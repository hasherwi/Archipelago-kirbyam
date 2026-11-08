"""Read-only research inventory invariants; no ROM or gameplay behavior assumed."""
import json
import struct
from pathlib import Path

import pytest

from ..tools.scan_metal_tiles import build_inventory, decompress_rl, pointer, records, unpack

ROOT = Path(__file__).resolve().parents[1]


def test_inventory_covers_all_native_slots_and_wiki_positive_rooms() -> None:
    inventory = json.loads((ROOT / "docs/metal-tile-inventory.json").read_text())
    mapping = json.loads((ROOT / "dev-docs/native-room-wikirby-map.json").read_text())
    review = json.loads((ROOT / "dev-docs/metal-block-wikirby-review.json").read_text())
    valid, unused = inventory["valid_room_ids"], inventory["unused_slots"]
    assert len(valid) == len(set(valid)) == 286
    assert len(unused) == len(set(unused)) == 697
    assert not set(valid) & set(unused)
    assert set(valid) | set(unused) == set(range(983))
    assert set(valid) == {row["native_id"] for row in mapping["rooms"]}
    assert inventory["errors"] == []
    by_class = {
        tile: {r["room"] for r in inventory["rooms"] if any(t["tile"] == tile for t in r["tiles"])}
        for tile in ("0xf5", "0xf6", "0xf7")
    }
    assert [len(by_class[t]) for t in by_class] == [33, 13, 25]
    assert len(by_class["0xf5"] | by_class["0xf7"]) == 51
    assert len(review["rooms"]) == 51
    assert {r["native_room_id"] for r in review["rooms"]} == by_class["0xf5"] | by_class["0xf7"]
    assert [sum(t["tile"] == tile for r in inventory["rooms"] for t in r["tiles"])
            for tile in by_class] == [358, 14, 331]
    for room in inventory["rooms"]:
        assert room["room"] in valid
        positions = [(t["x"], t["y"]) for t in room["tiles"]]
        assert len(positions) == len(set(positions))
        assert all(0 <= x < room["width"] and 0 <= y < room["height"] for x, y in positions)
        assert all(r["replacement"] not in (0xF5, 0xF6, 0xF7) for r in room["records"])
        tile_keys = {(t["x"], t["y"], int(t["tile"], 16)) for t in room["tiles"]}
        record_keys = {(r["x"], r["y"], r["attribute"]) for r in room["records"]}
        assert tile_keys == record_keys


def test_rl_literal_and_repeat_runs() -> None:
    payload = struct.pack("<I", (6 << 8) | 0x30) + bytes([2, 1, 2, 3, 128, 7])
    assert decompress_rl(payload, 0, 6) == bytes([1, 2, 3, 7, 7, 7])


@pytest.mark.parametrize("payload,expected", [
    (struct.pack("<I", (3 << 8) | 0x10), 3),
    (struct.pack("<I", (3 << 8) | 0x30), 4),
    (struct.pack("<I", 0x30), 0),
    (struct.pack("<I", (2 << 8) | 0x30) + bytes([128, 7]), 2),
    (struct.pack("<I", (3 << 8) | 0x30) + bytes([2, 1]), 3),
])
def test_rl_rejects_wrong_header_size_overrun_and_truncation(payload: bytes, expected: int) -> None:
    with pytest.raises(ValueError):
        decompress_rl(payload, 0, expected)


@pytest.mark.parametrize("offset", [-1, 1, 5])
def test_unpack_rejects_out_of_bounds(offset: int) -> None:
    with pytest.raises(ValueError):
        unpack(bytes(4), "<I", offset)


def test_pointer_rejects_non_rom_address() -> None:
    with pytest.raises(ValueError):
        pointer(bytes(4), 0)


def test_solidity_records_validate_lengths_and_terminator() -> None:
    entry = struct.pack("<4BH", 1, 0xF5, 2, 3, 18) + bytes(12)
    assert records(entry + b"\x00", 0) == [dict(offset=0, kind=1, attribute=0xF5, x=2, y=3)]
    with pytest.raises(ValueError):
        records(entry, 0)
    with pytest.raises(ValueError):
        records(struct.pack("<4BH", 1, 0xF5, 2, 3, 14) + bytes(12), 0)


def test_inventory_rejects_wrong_rom_before_reading_tables() -> None:
    with pytest.raises(ValueError, match="unmodified USA ROM"):
        build_inventory(b"not a ROM")
