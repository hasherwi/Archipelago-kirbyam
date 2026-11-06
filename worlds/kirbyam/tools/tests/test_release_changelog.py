"""Release-note regression coverage without project imports, ROMs or network access."""
import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / '.github/scripts'))
sys.path.insert(0, str(ROOT / 'worlds/kirbyam/tools'))
m = importlib.import_module('kirbyam_release_metadata')
p = importlib.import_module('kirbyam_publish_policy')
r = importlib.import_module('release_readiness')


class ReleaseChangelogTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.directory = Path(tmp.name)
        self.notes = self.directory / 'CHANGELOG.md'

    def test_selection_and_section_boundaries(self):
        base = '## v0.5.0\n\n### Improvements\n- Base notes.\n'
        rc = '## v0.5.0-rc2\n- RC2 notes.\n'
        for source, version, expected in (
            (base, '0.5.0-rc2', base), (base, '0.5.0', base),
            (base + rc, '0.5.0-rc2', rc), (rc + base, '0.5.0-rc2', rc),
            (rc + base, '0.5.0', base),
        ):
            with self.subTest(version=version, source=source):
                self.notes.write_text('## Unreleased\n- Future.\n' + source + '## v0.4.0\n- Older.\n')
                before = self.notes.read_bytes()
                m.check_changelog_has_version(self.notes, version)
                self.assertEqual(m.extract_changelog_section(self.notes, version), expected)
                self.assertEqual(self.notes.read_bytes(), before)

    def test_missing_wrong_and_duplicate_sections_fail_closed(self):
        for source, version in (
            ('## Unreleased\n- Notes.\n', '0.5.0-rc2'),
            ('## v0.5.0-rc1\n- Notes.\n', '0.5.0-rc2'),
            ('## v0.5.1\n- Notes.\n', '0.5.0-rc2'),
            ('## v0.5.0-rc2\n- Notes.\n', '0.5.0'),
            ('## v0.5.0\n- Notes.\n', '0.5.0-rc0'),
            ('## v0.5.0\n- Notes.\n', '0.5.0-beta1'),
            ('## v0.5.0\n## v0.5.0\n', '0.5.0-rc2'),
            ('## v0.5.0-rc2\n## v0.5.0-rc2\n## v0.5.0\n', '0.5.0-rc2'),
        ):
            self.notes.write_text(source)
            for check in (m.check_changelog_has_version, m.extract_changelog_section):
                with self.subTest(source=source, version=version, check=check.__name__), self.assertRaises(ValueError):
                    check(self.notes, version)

    def test_build_cli_rc2_and_final_preserve_identity_and_source(self):
        for version in ('0.5.0-rc2', '0.5.0'):
            self.notes.write_text('## v0.5.0\n- Shared notes.\n')
            manifest = self.directory / 'archipelago.json'
            manifest.write_text('{"world_version": "0.5.0"}')
            output = self.directory / 'output'
            output.write_text('')
            extracted = self.directory / 'notes'
            before = (self.notes.read_bytes(), manifest.read_bytes())
            argv = ['metadata', '--github-ref', 'refs/tags/kirbyam-v' + version,
                    '--changelog', str(self.notes), '--world-manifest', str(manifest),
                    '--github-output', str(output), '--release-notes', str(extracted)]
            with patch.object(sys, 'argv', argv):
                self.assertEqual(m.main(), 0)
            self.assertEqual(extracted.read_text(), self.notes.read_text())
            self.assertEqual(before, (self.notes.read_bytes(), manifest.read_bytes()))
            fields = dict(line.split('=', 1) for line in output.read_text().splitlines())
            self.assertEqual(fields['release_tag'], 'kirbyam-v' + version)
            self.assertEqual(fields['version'], version)
            self.assertEqual(fields['manifest_version'], '0.5.0')
            self.assertEqual(fields['prerelease'], str('-rc' in version).lower())

    def test_trusted_publisher_and_readiness_use_tagged_source(self):
        sha = 'a' * 40
        source = '## v0.5.0\n- Tagged source notes.\n'
        for version in ('0.5.0-rc2', '0.5.0'):
            tag = 'kirbyam-v' + version
            context = dict(GITHUB_REPOSITORY=r.REPO, GITHUB_EVENT_NAME='push',
                           GITHUB_REF_PROTECTED='true', GITHUB_REF='refs/tags/' + tag,
                           GITHUB_SHA=sha, GITHUB_OUTPUT=str(self.directory / 'output'))
            def read_source(args, **kwargs):
                self.assertEqual(list(args[:2]), ['git', 'show'])
                self.assertTrue(args[2].startswith(sha + ':'))
                return json.dumps({'world_version': '0.5.0'}) if args[2].endswith('.json') else source
            old = Path.cwd()
            try:
                os.chdir(self.directory)
                with patch.dict(os.environ, context), patch.object(p.subprocess, 'run') as ancestry, \
                     patch.object(p.subprocess, 'check_output', side_effect=read_source):
                    p.main()
                    ancestry.assert_called_once_with(['git', 'merge-base', '--is-ancestor', sha, 'HEAD'], check=True)
                self.assertEqual(Path('release_notes.md').read_text(), source)
                with patch.object(r.subprocess, 'run') as ancestry, \
                     patch.object(r.subprocess, 'check_output', side_effect=read_source):
                    r.source_check(tag, sha)
                    ancestry.assert_called_once_with(['git', 'merge-base', '--is-ancestor', sha, 'origin/main'], check=True)
            finally:
                os.chdir(old)


if __name__ == '__main__':
    unittest.main()
