"""Offline byte/identity/state fixtures; no privileged API or signing calls."""
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
artifacts = importlib.import_module("release_artifacts")


class ReleaseArtifactTests(unittest.TestCase):
    def test_receipt_requires_exact_bytes_and_identity(self) -> None:
        context = {"GITHUB_REPOSITORY": artifacts.REPOSITORY, "GITHUB_SHA": "a" * 40,
                   "GITHUB_REF": "refs/tags/kirbyam-v0.5.0", "GITHUB_EVENT_NAME": "push",
                   "GITHUB_RUN_ID": "123", "GITHUB_RUN_ATTEMPT": "1"}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / artifacts.ASSETS[0]).write_bytes(b"synthetic apworld fixture")
            record = artifacts.receipt(root, context)
            manifest = root / artifacts.ASSETS[1]
            manifest.write_text(json.dumps(record))
            artifacts.verify(root, context)
            for key in ("source", "workflow", "repository", "ref", "event", "run_id", "sha256"):
                manifest.write_text(json.dumps({**record, key: "wrong"}))
                with self.subTest(key=key), self.assertRaises(ValueError):
                    artifacts.verify(root, context)
            manifest.write_text(json.dumps(record))
            (root / artifacts.ASSETS[0]).write_bytes(b"altered")
            with self.assertRaises(ValueError):
                artifacts.verify(root, context)
            manifest.unlink()
            with self.assertRaises(FileNotFoundError):
                artifacts.verify(root, context)

    def test_draft_retry_and_published_release_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in artifacts.ASSETS:
                (root / name).write_bytes(b"fixture")
            self.assertEqual(artifacts.plan(root, {"isDraft": True, "assets": []}), list(artifacts.ASSETS))
            existing = [{"name": name, "digest": "sha256:" + artifacts.digest(root / name)}
                        for name in artifacts.ASSETS]
            self.assertEqual(artifacts.plan(root, {"isDraft": True, "assets": existing}), [])
            state: dict[str, Any]
            for state in ({"isDraft": False, "assets": []}, {"assets": []},
                          {"isDraft": True, "assets": [{"name": "full.gba", "digest": "sha256:bad"}]},
                          {"isDraft": True, "assets": [{"name": artifacts.ASSETS[0]}]},
                          {"isDraft": True, "assets": [{"name": artifacts.ASSETS[0], "digest": "sha256:bad"}]}):
                with self.subTest(state=state), self.assertRaises(ValueError):
                    artifacts.plan(root, state)
            (root / "full.gba").write_bytes(b"synthetic forbidden fixture")
            with self.assertRaises(ValueError):
                artifacts.plan(root, {"isDraft": True, "assets": []})

    def test_no_destructive_upload_commands(self) -> None:
        root = Path(__file__).resolve().parents[4]
        workflow = (root / ".github/workflows/kirbyam-apworld.yml").read_text()
        for forbidden in ("--clobber", "delete-asset", "gh release create", "gh release edit"):
            self.assertNotIn(forbidden, workflow)
        self.assertIn("--source-digest", workflow)
        self.assertIn("--signer-workflow", workflow)
        self.assertIn("release_artifacts.py plan", workflow)


if __name__ == "__main__":
    unittest.main()
