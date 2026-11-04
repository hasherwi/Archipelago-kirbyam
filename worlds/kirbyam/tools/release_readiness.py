"""Read-only release readiness; never creates tags, uploads, or publishes."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import urllib.request

import release_artifacts as artifacts

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kirbyam_release_metadata as metadata

REPO = artifacts.REPOSITORY
SETTINGS = ('protected_main', 'protected_tag', 'release_environment', 'immutable_releases')


def command(*args):
    return subprocess.check_output(args, text=True).strip()


def api(path):
    return json.loads(command('gh', 'api', f'repos/{REPO}/{path}'))


def source_check(tag, sha):
    if not re.fullmatch('[0-9a-f]{40}', sha):
        raise ValueError('source must be a full lowercase reviewed commit SHA')
    release = metadata.build_release_metadata('refs/tags/' + tag)
    if not release.release_enabled:
        raise ValueError('expected a Kirby release tag')
    subprocess.run(['git', 'merge-base', '--is-ancestor', sha, 'origin/main'], check=True)
    manifest = json.loads(command('git', 'show', f'{sha}:worlds/kirbyam/archipelago.json'))
    if manifest.get('world_version') != release.manifest_version:
        raise ValueError('tagged manifest version must already match release')
    with tempfile.TemporaryDirectory() as tmp:
        notes = Path(tmp) / 'changelog.md'
        notes.write_text(command('git', 'show', f'{sha}:worlds/kirbyam/CHANGELOG.md'))
        metadata.check_changelog_has_version(notes, release.version)


def prerequisites(evidence, tag, sha):
    """Owner inspection records are evidence, not an automatic settings audit."""
    if (evidence.get('repository'), evidence.get('tag'), evidence.get('source')) != (REPO, tag, sha):
        raise ValueError('owner evidence must name this repository, tag and source')
    result = {}
    for name in SETTINGS:
        item = evidence.get(name, {})
        status = item.get('status', 'unreadable')
        if status not in ('verified', 'missing', 'unreadable'):
            raise ValueError(f'invalid prerequisite status: {name}')
        if status == 'verified' and not all(item.get(k) for k in ('owner', 'checked_at', 'evidence')):
            status = 'unreadable'
        result[name] = status
    return result


def classify(run, jobs, pending, tag, sha):
    if (run.get('event'), run.get('head_sha'), run.get('head_branch'), run.get('path')) != (
            'push', sha, tag, artifacts.WORKFLOW):
        return ('build-only success' if run.get('conclusion') == 'success' else 'build-only'), 'Select the exact tag-push run, not a branch or manual build.'
    publisher = next((j for j in jobs if j['name'] == 'release-apworld'), None)
    if publisher and publisher.get('conclusion') == 'skipped':
        return 'publisher skipped', 'Inspect tag protection and build result; a skipped writer staged nothing.'
    if pending:
        return 'awaiting approval', 'Required environment reviewer must inspect source and build before approval.'
    if not publisher or publisher.get('status') != 'completed':
        return 'staging pending', 'Wait for the exact run; inspect missing jobs or interrupted attempts.'
    if publisher.get('conclusion') != 'success':
        return 'staging failed', 'Preserve existing assets and inspect the failed attempt before recovery.'
    return 'verification required', 'Download and verify every asset before publication.'


def verify_download(directory, release, tag, sha, run, public=False):
    names = [a['name'] for a in release['assets']]
    if sorted(names) != sorted(artifacts.ASSETS):
        raise ValueError('release must contain exactly the three allowlisted assets')
    if public:
        for asset in release['assets']:
            # Public verification deliberately sends no authorization header.
            expected = f'https://github.com/{REPO}/releases/download/{tag}/{asset["name"]}'
            if asset['browser_download_url'] != expected:
                raise ValueError('unexpected public asset URL')
            with urllib.request.urlopen(expected, timeout=60) as response:
                (directory / asset['name']).write_bytes(response.read())
    else:
        command('gh', 'release', 'download', tag, '--repo', REPO, '--dir', str(directory),
                '--pattern', artifacts.ASSETS[0], '--pattern', artifacts.ASSETS[1],
                '--pattern', artifacts.ASSETS[2])
    # Reuse #983 digest/allowlist policy without granting published mutation rights.
    artifacts.plan(directory, {'isDraft': True, 'assets': release['assets']})
    context = {'GITHUB_REPOSITORY': REPO, 'GITHUB_SHA': sha, 'GITHUB_REF': f'refs/tags/{tag}',
               'GITHUB_EVENT_NAME': 'push', 'GITHUB_RUN_ID': str(run['id']),
               'GITHUB_RUN_ATTEMPT': str(run['run_attempt'])}
    artifacts.verify(directory, context)
    for name in artifacts.ASSETS[:2]:
        command('gh', 'attestation', 'verify', str(directory / name), '--repo', REPO,
                '--bundle', str(directory / artifacts.ASSETS[2]), '--signer-workflow',
                f'{REPO}/{artifacts.WORKFLOW}', '--source-digest', sha,
                '--source-ref', f'refs/tags/{tag}', '--deny-self-hosted-runners')


def inspect(args, report):
    source_check(args.tag, args.source)
    report['prerequisites'] = prerequisites(json.loads(args.owner_evidence.read_text()), args.tag, args.source)
    missing = [key for key, value in report['prerequisites'].items() if value != 'verified']
    report['missing_prerequisites'] = missing
    if missing:
        report.update(status='blocked', action='Owner must inspect and resolve missing/unreadable settings; see runbook.')
        return False
    if args.preflight:
        report.update(status='preflight complete', action='Create/inspect the draft, then push the exact tag using the runbook. This is not release readiness.')
        return True
    # Get ref identity from GitHub rather than trusting a local tag or release target_commitish.
    ref = api(f'git/ref/tags/{args.tag}')['object']
    while ref['type'] == 'tag':
        ref = api(f'git/tags/{ref["sha"]}')['object']
    if ref['type'] != 'commit' or ref['sha'] != args.source:
        raise ValueError('remote tag does not resolve to reviewed source; do not move it')
    release = api(f'releases/tags/{args.tag}')
    if release['tag_name'] != args.tag:
        raise ValueError('release tag mismatch')
    report['release_url'] = release['html_url']
    report['missing_assets'] = sorted(set(artifacts.ASSETS) - {a['name'] for a in release['assets']})
    if not release['draft'] and not args.public:
        raise ValueError('release already published; preserve evidence and use public verification/recovery')
    if args.public and (release['draft'] or release.get('immutable') is not True):
        raise ValueError('public verification requires a published immutable release')
    run = api(f'actions/runs/{args.run_id}')
    if run.get('repository', {}).get('full_name') != REPO or run['id'] != args.run_id:
        raise ValueError('unexpected run repository or identity')
    report['run_attempt'] = run['run_attempt']
    jobs = api(f'actions/runs/{args.run_id}/attempts/{run["run_attempt"]}/jobs?per_page=100')
    if jobs['total_count'] > len(jobs['jobs']):
        raise ValueError('incomplete jobs response; inspect run manually')
    pending = api(f'actions/runs/{args.run_id}/pending_deployments')
    status, action = classify(run, jobs['jobs'], pending, args.tag, args.source)
    report.update(status=status, action=action)
    if status != 'verification required':
        return False
    with tempfile.TemporaryDirectory() as tmp:
        verify_download(Path(tmp), release, args.tag, args.source, run, args.public)
    # Detect concurrent state/asset changes; this is not an atomic publication lock.
    if api(f'releases/tags/{args.tag}') != release:
        raise ValueError('release changed during verification; inspect and repeat')
    report.update(status='published-and-verified' if args.public else 'staged-and-verified',
                  action='Record evidence; publication still requires separate authorization.' if not args.public
                  else 'Record public verification evidence.', missing_assets=[])
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--run-id', type=int)
    parser.add_argument('--preflight', action='store_true', help='Check source and owner prerequisites before draft/tag creation')
    parser.add_argument('--owner-evidence', required=True, type=Path)
    parser.add_argument('--public', action='store_true', help='Verify unauthenticated public downloads after publication')
    args = parser.parse_args()
    if not args.preflight and args.run_id is None:
        parser.error('--run-id is required unless --preflight is selected')
    if args.preflight and args.public:
        parser.error('--preflight and --public cannot be combined')
    report = dict(tag=args.tag, source=args.source, run_url=f'https://github.com/{REPO}/actions/runs/{args.run_id}' if args.run_id else None,
                  release_url=f'https://github.com/{REPO}/releases/tag/{args.tag}',
                  status='blocked', missing_assets=list(artifacts.ASSETS),
                  action='Resolve the error using the release runbook; do not publish.')
    try:
        ready = inspect(args, report)
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        report.update(status='blocked', error=str(error))
        ready = False
    print(json.dumps(report, indent=2))
    return 0 if ready else 1


if __name__ == '__main__':
    raise SystemExit(main())
