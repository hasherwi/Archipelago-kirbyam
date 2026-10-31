"""Read-only authorization fixtures; no API calls, credentials or release writes."""
import importlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / ".github/scripts"))
authorize = importlib.import_module("kirbyam_publish_policy").authorize


class PublishPolicyTests(unittest.TestCase):
    def test_event_ref_and_approved_history(self) -> None:
        context = {"GITHUB_REPOSITORY": "hasherwi/Archipelago-kirbyam", "GITHUB_EVENT_NAME": "push",
                   "GITHUB_REF_PROTECTED": "true", "GITHUB_REF": "refs/tags/kirbyam-v0.5.0",
                   "GITHUB_SHA": "a" * 40, "release_enabled": "true"}
        authorize(context, True)
        for key, value in (("GITHUB_EVENT_NAME", "pull_request"), ("GITHUB_EVENT_NAME", "workflow_dispatch"),
                           ("GITHUB_REF", "refs/heads/main"), ("GITHUB_REF", "refs/heads/arbitrary"),
                           ("GITHUB_REF", "refs/tags/kirbyam-vbad"), ("GITHUB_REF_PROTECTED", "false"),
                           ("GITHUB_REPOSITORY", "attacker/fork"), ("GITHUB_SHA", "--help")):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                authorize({**context, key: value}, True)
        with self.assertRaisesRegex(ValueError, "approved main"):
            authorize(context, False)
        # A build flag cannot grant or revoke authority; approved platform context does.
        authorize({**context, "release_enabled": "false"}, True)

    def test_workflow_boundary_is_wired(self) -> None:
        root = Path(__file__).resolve().parents[4]
        text = (root / ".github/workflows/kirbyam-apworld.yml").read_text()
        publisher = text.split("  release-apworld:", 1)[1]
        self.assertIn("github.event_name == 'push'", publisher)
        self.assertIn("github.ref_protected == true", publisher)
        self.assertIn("environment: kirbyam-release", publisher)
        self.assertNotIn("needs.build-apworld.outputs", publisher)
        self.assertNotIn("pull-requests: write", publisher)
        self.assertIn("ref: main", publisher)
        self.assertIn("persist-credentials: false", publisher)
        self.assertIn("python .github/scripts/kirbyam_publish_policy.py", publisher)


if __name__ == "__main__":
    unittest.main()
