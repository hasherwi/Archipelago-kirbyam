"""Offline orchestration fixtures: no credentials, API requests or release mutations."""
import importlib
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
r = importlib.import_module('release_readiness')
SHA = 'a' * 40
TAG = 'kirbyam-v1.0.0-rc1'
RUN = dict(conclusion='success', id=42, run_attempt=1, event='push', head_sha=SHA, head_branch=TAG,
           path=r.artifacts.WORKFLOW, repository={'full_name': r.REPO})
JOB = dict(name='release-apworld', status='completed', conclusion='success')


class ReadinessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.evidence = dict(repository=r.REPO, tag=TAG, source=SHA)
        for setting in r.SETTINGS:
            self.evidence[setting] = dict(status='verified', owner='maintainer',
                                          checked_at='2026-11-04T00:00:00Z', evidence='inspection reference')
        self.evidence_file = self.directory / 'owner.json'
        self.evidence_file.write_text(json.dumps(self.evidence))
        self.args = SimpleNamespace(tag=TAG, source=SHA, run_id=42,
                                    owner_evidence=self.evidence_file, preflight=False, public=False)
        self.release = dict(tag_name=TAG, draft=True, immutable=False, html_url='release',
                            assets=[dict(name=n, digest='sha256:x') for n in r.artifacts.ASSETS])

    def responses(self, release=None, jobs=None, pending=None, run=None):
        release = release if release is not None else self.release
        return [{'object': {'type': 'commit', 'sha': SHA}}, release, run or RUN,
                {'total_count': len(jobs) if jobs is not None else 1, 'jobs': jobs if jobs is not None else [JOB]}, pending or [], release]

    def test_normal_staging_and_public_verification(self):
        for public in (False, True):
            with self.subTest(public=public):
                self.args.public = public
                self.release.update(draft=not public, immutable=public)
                report = {}
                with patch.object(r, 'source_check'), patch.object(r, 'api', side_effect=self.responses()), \
                     patch.object(r, 'verify_download') as verify:
                    self.assertTrue(r.inspect(self.args, report))
                self.assertEqual(report['status'], 'published-and-verified' if public else 'staged-and-verified')
                self.assertEqual(verify.call_args.args[-1], public)

    def test_preflight_does_not_need_or_create_remote_objects(self):
        self.args.preflight = True
        with patch.object(r, 'source_check') as source, patch.object(r, 'api') as api:
            report = {}
            self.assertTrue(r.inspect(self.args, report))
            source.assert_called_once_with(TAG, SHA)
            api.assert_not_called()
            self.assertEqual(report['status'], 'preflight complete')

    def test_owner_missing_unreadable_and_unsubstantiated(self):
        for value, expected in (({'status': 'missing'}, 'missing'), ({}, 'unreadable'),
                                ({'status': 'verified'}, 'unreadable')):
            self.evidence['protected_tag'] = value
            self.assertEqual(r.prerequisites(self.evidence, TAG, SHA)['protected_tag'], expected)
            self.evidence_file.write_text(json.dumps(self.evidence))
            with patch.object(r, 'source_check'), patch.object(r, 'api') as api:
                self.assertFalse(r.inspect(self.args, {}))
                api.assert_not_called()
        with self.assertRaises(ValueError):
            r.prerequisites(self.evidence, TAG, 'b' * 40)

    def test_failure_states_never_verify_assets(self):
        cases = [([dict(JOB, conclusion='skipped')], [], RUN, 'publisher skipped'),
                 ([dict(JOB, status='waiting', conclusion=None)], [{}], RUN, 'awaiting approval'),
                 ([dict(JOB, conclusion='failure')], [], RUN, 'staging failed'),
                 ([dict(JOB, conclusion='cancelled')], [], RUN, 'staging failed'),
                 ([], [], RUN, 'staging pending'),
                 ([JOB], [], dict(RUN, event='workflow_dispatch'), 'build-only success'),
                 ([JOB], [], dict(RUN, head_sha='b' * 40), 'build-only success')]
        for jobs, pending, run, status in cases:
            with self.subTest(status=status), patch.object(r, 'source_check'), \
                 patch.object(r, 'api', side_effect=self.responses(jobs=jobs, pending=pending, run=run)), \
                 patch.object(r, 'verify_download') as verify:
                report = {}
                self.assertFalse(r.inspect(self.args, report))
                self.assertEqual(report['status'], status)
                verify.assert_not_called()

    def test_missing_draft_wrong_tag_and_published_release_stop(self):
        for responses in ([{'object': {'type': 'commit', 'sha': 'b' * 40}}],
                          [{'object': {'type': 'commit', 'sha': SHA}}, ValueError('draft missing')],
                          self.responses(release=dict(self.release, draft=False))):
            with patch.object(r, 'source_check'), patch.object(r, 'api', side_effect=responses), \
                 patch.object(r, 'verify_download') as verify, self.assertRaises(ValueError):
                r.inspect(self.args, {})
            verify.assert_not_called()

    def test_concurrent_release_change_stops(self):
        responses = self.responses()
        responses[-1] = dict(self.release, draft=False)
        with patch.object(r, 'source_check'), patch.object(r, 'api', side_effect=responses), \
             patch.object(r, 'verify_download'), self.assertRaisesRegex(ValueError, 'changed'):
            r.inspect(self.args, {})

    def test_verification_download_counts_do_not_block_readiness(self):
        for public in (False, True):
            with self.subTest(public=public):
                self.args.public = public
                self.release.update(draft=not public, immutable=public)
                responses = self.responses()
                responses[-1] = dict(self.release, assets=[
                    dict(asset, download_count=1) for asset in self.release['assets']])
                with patch.object(r, 'source_check'), patch.object(r, 'api', side_effect=responses), \
                     patch.object(r, 'verify_download'):
                    self.assertTrue(r.inspect(self.args, {}))

    def test_asset_changes_still_block_readiness(self):
        for field, value in (('id', 999), ('digest', 'sha256:changed'), ('name', 'other.apworld')):
            with self.subTest(field=field):
                responses = self.responses()
                assets = [dict(asset, download_count=1) for asset in self.release['assets']]
                assets[0][field] = value
                responses[-1] = dict(self.release, assets=assets)
                with patch.object(r, 'source_check'), patch.object(r, 'api', side_effect=responses), \
                     patch.object(r, 'verify_download'), self.assertRaisesRegex(ValueError, 'changed'):
                    r.inspect(self.args, {})

    def test_actual_download_verification_and_retry_constraints(self):
        # Exercise real #983 receipt/digest checks; only network/signature subprocess is mocked.
        (self.directory / 'owner.json').unlink()
        (self.directory / r.artifacts.ASSETS[0]).write_bytes(b'fixture APWorld')
        context = dict(GITHUB_REPOSITORY=r.REPO, GITHUB_SHA=SHA, GITHUB_REF='refs/tags/' + TAG,
                       GITHUB_EVENT_NAME='push', GITHUB_RUN_ID='42', GITHUB_RUN_ATTEMPT='1')
        (self.directory / r.artifacts.ASSETS[1]).write_text(json.dumps(r.artifacts.receipt(self.directory, context)))
        (self.directory / r.artifacts.ASSETS[2]).write_bytes(b'fixture bundle')
        self.release['assets'] = [dict(name=n, digest='sha256:' + r.artifacts.digest(self.directory / n))
                                  for n in r.artifacts.ASSETS]
        with patch.object(r, 'command') as command:
            r.verify_download(self.directory, self.release, TAG, SHA, RUN)
            self.assertEqual(command.call_count, 3)
            self.assertIn('--source-digest', command.call_args.args)
            with self.assertRaisesRegex(ValueError, 'identity'):
                r.verify_download(self.directory, self.release, TAG, SHA, dict(RUN, run_attempt=2))
            (self.directory / r.artifacts.ASSETS[2]).write_bytes(b'new attestation bundle')
            with self.assertRaisesRegex(ValueError, 'differs'):
                r.verify_download(self.directory, self.release, TAG, SHA, RUN)
        for assets in (self.release['assets'][:1], self.release['assets'] + [dict(name='game.gba')]):
            with self.assertRaisesRegex(ValueError, 'exactly'):
                r.verify_download(self.directory, dict(self.release, assets=assets), TAG, SHA, RUN)

    def test_public_downloads_are_unauthenticated_and_signatures_required(self):
        (self.directory / 'owner.json').unlink()
        payloads = {r.artifacts.ASSETS[0]: b'fixture APWorld', r.artifacts.ASSETS[2]: b'bundle'}
        (self.directory / r.artifacts.ASSETS[0]).write_bytes(payloads[r.artifacts.ASSETS[0]])
        context = dict(GITHUB_REPOSITORY=r.REPO, GITHUB_SHA=SHA, GITHUB_REF='refs/tags/' + TAG,
                       GITHUB_EVENT_NAME='push', GITHUB_RUN_ID='42', GITHUB_RUN_ATTEMPT='1')
        payloads[r.artifacts.ASSETS[1]] = json.dumps(r.artifacts.receipt(self.directory, context)).encode()
        import hashlib
        self.release['assets'] = [dict(name=n, digest='sha256:' + hashlib.sha256(payloads[n]).hexdigest(),
            browser_download_url=f'https://github.com/{r.REPO}/releases/download/{TAG}/{n}')
            for n in r.artifacts.ASSETS]
        def download(url, timeout):
            self.assertIsInstance(url, str)  # no authenticated Request/header object
            return io.BytesIO(payloads[url.rsplit('/', 1)[1]])
        with patch.object(r.urllib.request, 'urlopen', side_effect=download) as fetch, \
             patch.object(r, 'command') as command:
            r.verify_download(self.directory, self.release, TAG, SHA, RUN, public=True)
            self.assertEqual(fetch.call_count, 3)
            self.assertEqual(command.call_count, 2)
        with patch.object(r, 'command', side_effect=[None, ValueError('invalid signature')]), \
             self.assertRaisesRegex(ValueError, 'signature'):
            r.verify_download(self.directory, self.release, TAG, SHA, RUN)

    def test_source_validation_reuses_metadata_and_ancestry(self):
        with patch.object(r.subprocess, 'run') as git, \
             patch.object(r, 'command', side_effect=[json.dumps({'world_version': '1.0.0'}), '## v1.0.0-rc1\nNotes']):
            r.source_check(TAG, SHA)
            self.assertIn('--is-ancestor', git.call_args.args[0])
        with self.assertRaises(ValueError):
            r.source_check(TAG, '--help')
        with patch.object(r.subprocess, 'run'), \
             patch.object(r, 'command', return_value=json.dumps({'world_version': '0.5.0'})), \
             self.assertRaisesRegex(ValueError, 'manifest'):
            r.source_check(TAG, SHA)


if __name__ == '__main__':
    unittest.main()
