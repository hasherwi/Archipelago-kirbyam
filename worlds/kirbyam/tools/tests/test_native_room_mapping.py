"""Offline negative checks for native-room documentation coverage."""
import copy
import importlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
mapping = importlib.import_module("check_native_room_mapping")


class NativeRoomMappingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = json.loads(mapping.DATA.read_text())
        self.rooms = json.loads((mapping.ROOT / "data/regions/rooms.json").read_text())

    def test_checked_inventory_and_table(self) -> None:
        mapping.validate(self.data, self.rooms)
        self.assertIn(mapping.render(self.data), mapping.DOC.read_text())

    def test_missing_slot_is_rejected(self) -> None:
        self.data["unused_ranges"][0][0] += 1
        with self.assertRaisesRegex(ValueError, "incomplete"):
            mapping.validate(self.data, self.rooms)

    def test_duplicate_record_is_rejected(self) -> None:
        self.data["rooms"].append(copy.deepcopy(self.data["rooms"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            mapping.validate(self.data, self.rooms)

    def test_wrong_completion_join_is_rejected(self) -> None:
        self.data["rooms"][0]["completion_index"] = 4
        with self.assertRaisesRegex(ValueError, "completion-index join"):
            mapping.validate(self.data, self.rooms)

    def test_unknown_key_is_rejected(self) -> None:
        self.data["rooms"][0]["ap_keys"].append("invented")
        with self.assertRaisesRegex(ValueError, "unknown AP key"):
            mapping.validate(self.data, self.rooms)

    def test_missing_generated_alias_is_rejected(self) -> None:
        row = next(row for row in self.data["rooms"]
                   if any("__LOGIC__" in key for key in row["ap_keys"]))
        row["ap_keys"] = [key for key in row["ap_keys"] if "__LOGIC__" not in key]
        with self.assertRaisesRegex(ValueError, "incomplete"):
            mapping.validate(self.data, self.rooms)

    def test_wrong_rom_is_rejected_before_parsing(self) -> None:
        with self.assertRaisesRegex(ValueError, "unmodified USA ROM"):
            mapping.validate(self.data, self.rooms, b"synthetic invalid fixture")


if __name__ == "__main__":
    unittest.main()
