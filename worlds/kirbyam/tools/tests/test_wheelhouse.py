"""Offline negative fixtures: never download or install fixture code."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from verify_wheelhouse import verify  # noqa: E402


class WheelhouseTests(unittest.TestCase):
    def test_complete_inventory_and_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            wheels = root / "wheels"
            wheels.mkdir()
            wheel = wheels / "fixture.whl"
            wheel.write_bytes(b"reviewed fixture")
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({wheel.name: hashlib.sha256(wheel.read_bytes()).hexdigest()}))
            verify(wheels, manifest)
            wheel.write_bytes(b"altered fixture")
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                verify(wheels, manifest)
            wheel.unlink()
            with self.assertRaisesRegex(ValueError, "missing or unexpected"):
                verify(wheels, manifest)
            wheel.write_bytes(b"reviewed fixture")
            (wheels / "unresolved-dependency.whl").write_bytes(b"unexpected")
            with self.assertRaisesRegex(ValueError, "missing or unexpected"):
                verify(wheels, manifest)

    def test_missing_integrity_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manifest = root / "manifest.json"
            manifest.write_text("{}")
            with self.assertRaisesRegex(ValueError, "wheel basenames"):
                verify(root, manifest)


if __name__ == "__main__":
    unittest.main()
