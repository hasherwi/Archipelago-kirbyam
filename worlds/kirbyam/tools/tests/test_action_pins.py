"""Action policy tests use strings only; no action or network execution."""
import importlib
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
check = importlib.import_module("check_action_pins").check


class ActionPinsTests(unittest.TestCase):
    def test_reviewed_commit(self) -> None:
        check("      - uses: actions/example@" + "a" * 40, {"actions/example": "a" * 40})

    def test_unreviewed_inputs(self) -> None:
        for reference in ("actions/example@v6", "actions/example@main", "./local", "docker://image:latest",
                          "unknown/action@" + "a" * 40, "actions/example@" + "b" * 40):
            with self.subTest(reference=reference), self.assertRaises(ValueError):
                check("        uses: " + reference, {"actions/example": "a" * 40})

    def test_yaml_forms_cannot_hide_mutable_references(self) -> None:
        for text in ('{"uses": "actions/example@main"}', "'uses': actions/example@v6",
                     'steps: [{uses: "actions/example@main"}]'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                check(text, {"actions/example": "a" * 40})

    def test_job_and_service_containers_require_review(self) -> None:
        for text in ("jobs: {test: {container: 'image:latest'}}",
                     "jobs: {test: {container: {image: 'image@sha256:abc'}}}",
                     "jobs: {test: {services: {db: {image: 'postgres:latest'}}}}"):
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, "container or service"):
                check(text, {})


if __name__ == "__main__":
    unittest.main()
