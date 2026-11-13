"""Synthetic, ROM-free regressions for native object-stream room usage."""
import argparse
import importlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
usage = importlib.import_module("enrich_native_object_room_usage")


def record(type_id: int, size: int = 0x24, spawn_table: int = 1) -> bytes:
    data = bytearray(size)
    data[0] = spawn_table
    data[1] = size
    data[0x0C] = type_id
    return bytes(data)


def stream_rom(stream: bytes, header_count: int = 1) -> bytes:
    header = bytearray(0x10)
    header[:4] = (usage.ROM_BASE + 0x10).to_bytes(4, "little")
    header[0x0C] = header_count
    return bytes(header) + stream


class NativeObjectRoomUsageTests(unittest.TestCase):
    def test_header_type_count_does_not_truncate_records(self) -> None:
        for count in (0, 1, 255):
            with self.subTest(count=count):
                rom = stream_rom(record(7) * 3 + b"\0\0", count)
                self.assertEqual(usage.parse_object_types_for_list(rom, usage.ROM_BASE), [7, 7, 7])

    def test_variable_record_sizes_and_zero_terminator(self) -> None:
        rom = stream_rom(record(7, 0x18) + record(9, 0x30) + b"\0\0" + record(99))
        self.assertEqual(usage.parse_object_types_for_list(rom, usage.ROM_BASE), [7, 9])

    def test_other_spawn_tables_do_not_collide_with_table_one_ids(self) -> None:
        rom = stream_rom(record(7) + record(7, 0x18, 2) + record(9) + b"\0\0")
        self.assertEqual(usage.parse_object_types_for_list(rom, usage.ROM_BASE), [7, 9])

    def test_unknown_nonterminal_spawn_table_rejected(self) -> None:
        for spawn_table in (0, 3, 255):
            with self.subTest(spawn_table=spawn_table):
                rom = stream_rom(record(7) + record(7, spawn_table=spawn_table) + b"\0\0")
                with self.assertRaisesRegex(ValueError, "unknown spawn table"):
                    usage.parse_object_types_for_list(rom, usage.ROM_BASE)

    def test_other_spawn_table_records_are_still_validated(self) -> None:
        rom = stream_rom(record(7) + record(7, spawn_table=2)[:-1])
        with self.assertRaises(ValueError):
            usage.parse_object_types_for_list(rom, usage.ROM_BASE)

    def test_empty_stream_and_null_pointers(self) -> None:
        self.assertEqual(usage.parse_object_types_for_list(stream_rom(b"\0\0"), usage.ROM_BASE), [])
        self.assertEqual(usage.parse_object_types_for_list(bytes(0x10), usage.ROM_BASE), [])
        self.assertEqual(usage.parse_object_types_for_list(b"", 0), [])

    def test_malformed_or_truncated_stream_rejected_without_partial_result(self) -> None:
        for stream in (b"", b"\0", b"\1\1", b"\1\x0c" + bytes(10),
                       record(7)[:-1], record(7), record(7) + b"\1\x24"):
            with self.subTest(stream=stream):
                with self.assertRaises(ValueError):
                    usage.parse_object_types_for_list(stream_rom(stream), usage.ROM_BASE)

    def test_invalid_or_truncated_pointers_and_header_rejected(self) -> None:
        for rom, ptr in ((b"", usage.ROM_BASE), (bytes(15), usage.ROM_BASE),
                         (bytes(16), usage.ROM_BASE + 16), (bytes(16), 1)):
            with self.subTest(ptr=ptr, length=len(rom)):
                with self.assertRaises(ValueError):
                    usage.parse_object_types_for_list(rom, ptr)
        for ptr in (1, usage.ROM_BASE + 16):
            rom = ptr.to_bytes(4, "little") + bytes(12)
            with self.assertRaises(ValueError):
                usage.parse_object_types_for_list(rom, usage.ROM_BASE)

    def test_room_selection_and_no_background_or_unk22_duplicate_usage(self) -> None:
        # Three room records: separate background index, matching background index,
        # and an absent spawn list. The non-spawn fields must never add objects.
        room_props = bytearray(3 * 0x28)
        for i, (background, spawn) in enumerate(((1, 0), (0, 0), (0, 0xFFFF))):
            off = i * 0x28
            for field, value in ((0x1C, background), (0x20, spawn), (0x22, 0), (0x24, 4)):
                room_props[off + field:off + field + 2] = value.to_bytes(2, "little")
        pointer_table = ((usage.ROM_BASE + 0x80).to_bytes(4, "little")
                         + (1).to_bytes(4, "little"))  # invalid background-only union member
        header = bytearray(16)
        header[:4] = (usage.ROM_BASE + 0x90).to_bytes(4, "little")
        header[0x0C] = 1
        rom = bytes(room_props) + pointer_table + bytes(header) + record(7) * 2 + b"\0\0"
        with tempfile.TemporaryDirectory() as directory, patch.multiple(
            usage, ROOM_PROPS_ADDR=usage.ROM_BASE, ROOM_PROPS_SIZE=0x78,
            LEVEL_OBJ_LISTS_ADDR=usage.ROM_BASE + 0x78, LEVEL_OBJ_LISTS_COUNT=2,
        ):
            props = usage.parse_room_props(rom)
            self.assertEqual(props[0]["object_list2_idx"], 1)
            self.assertEqual(props[0]["object_list_idx"], 0)
            root = Path(directory)
            (root / "rom.bin").write_bytes(rom)
            (root / "mapping.json").write_text(json.dumps({"0x07": {"item_id": 7}}))
            (root / "rooms.json").write_text(json.dumps({
                "test_room": {"room_sanity": {"included": True, "bit_index": 4}},
            }))
            args = argparse.Namespace(rom=root / "rom.bin", mapping=root / "mapping.json",
                                      rooms=root / "rooms.json", output=root / "out.json", in_place=False)
            with patch.object(usage, "parse_args", return_value=args):
                usage.main()
            result = json.loads((root / "out.json").read_text())["0x07"]["room_usage"]
            self.assertEqual(result, {
                "total_count_all_rooms": 4,
                "rooms": [{"native_room_id": i, "count": 2, "ap_room_keys": ["test_room"]}
                          for i in (0, 1)],
            })


if __name__ == "__main__":
    unittest.main()
