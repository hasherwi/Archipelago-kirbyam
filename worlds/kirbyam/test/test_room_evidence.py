"""Bounds and semantics of the standalone ROM evidence decoder."""

import struct

import pytest

from ..tools import extract_room_evidence as evidence


def fixture_rom() -> bytearray:
    rom = bytearray(0x1000000)
    struct.pack_into("<I", rom, evidence.COMPLETION_TABLE, evidence.ROM_BASE + 0x100)
    struct.pack_into("<IB", rom, 0x100, evidence.ROM_BASE + 0x200, 1)
    struct.pack_into("<BB2xhh", rom, 0x200, 1, 8, 128, 120)
    struct.pack_into("<I", rom, evidence.SOLIDITY_TABLE, evidence.ROM_BASE + 0x300)
    struct.pack_into("<I", rom, 0x304, evidence.ROM_BASE + 0x400)
    struct.pack_into("<4BH2xHBB2x", rom, 0x400, 3, 254, 17, 11, 14, 734, 14, 5)
    return rom


def test_completion_chest_and_transition_are_separate_tables() -> None:
    room = evidence.extract_room(fixture_rom(), 0, {
        "test/room": {"room_sanity": {"included": True, "bit_index": 0}},
        "test/unused": {"locations": None},
    })
    assert room["ap_room_keys"] == ["test/room"]
    assert room["completion_entries"][0]["chest_position_pixels"] == [128, 120]
    assert room["transitions"][0]["destination_room"] == 734
    assert room["transitions"][0]["destination_spawn_tiles"] == [14, 5]
    assert room["transitions"][0]["source_tiles"] == [17, 11]


@pytest.mark.parametrize("room_id", [-1, evidence.ROOM_COUNT])
def test_rejects_invalid_room(room_id: int) -> None:
    with pytest.raises(ValueError, match="Invalid native room"):
        evidence.extract_room(b"", room_id, {})


def test_rejects_wrong_rom_before_parsing() -> None:
    with pytest.raises(ValueError, match="unmodified USA ROM"):
        evidence.build_evidence(fixture_rom(), [0], {})


@pytest.mark.parametrize("offset,value", [(0x400, 9), (0x404, 0)])
def test_rejects_unknown_or_nonadvancing_record(offset: int, value: int) -> None:
    rom = fixture_rom()
    rom[offset] = value
    with pytest.raises(ValueError, match="Unknown solidity record"):
        evidence.extract_room(rom, 0, {})


def test_rejects_non_rom_pointer() -> None:
    rom = fixture_rom()
    struct.pack_into("<I", rom, evidence.SOLIDITY_TABLE, 0x02000000)
    with pytest.raises(ValueError, match="Invalid ROM pointer"):
        evidence.extract_room(rom, 0, {})


def test_rejects_out_of_bounds_record() -> None:
    rom = fixture_rom()
    struct.pack_into("<I", rom, 0x304, evidence.ROM_BASE + len(rom) - 2)
    rom[-2] = 3
    with pytest.raises(ValueError, match="out of bounds"):
        evidence.extract_room(rom, 0, {})


def test_empty_completion_table_does_not_dereference_unused_pointer() -> None:
    rom = fixture_rom()
    struct.pack_into("<IB", rom, 0x100, 0, 0)
    room = evidence.extract_room(rom, 0, {})
    assert room["completion_entries"] == []
    assert len(room["transitions"]) == 1


def test_completion_door_is_not_an_outgoing_tile_transition() -> None:
    rom = fixture_rom()
    struct.pack_into("<BB2xHBB", rom, 0x200, 2, 8, 719, 6, 15)
    room = evidence.extract_room(rom, 0, {})
    assert room["completion_entries"][0]["destination_room"] == 719
    assert [t["destination_room"] for t in room["transitions"]] == [734]


def test_transition_flags_are_preserved_without_inventing_reachability() -> None:
    rom = fixture_rom()
    rom[0x40C] = 0x82
    assert evidence.extract_room(rom, 0, {})["transitions"][0]["transition_flags"] == 0x82


@pytest.mark.parametrize("kind,size", [(1, 0x12), (2, 0xE), (3, 0xE)])
def test_truncated_full_record_is_rejected(kind: int, size: int) -> None:
    rom = fixture_rom()
    offset = len(rom) - size + 1
    struct.pack_into("<I", rom, 0x304, evidence.ROM_BASE + offset)
    struct.pack_into("<4BH", rom, offset, kind, 254, 17, 11, size)
    with pytest.raises(ValueError, match="out of bounds"):
        evidence.extract_room(rom, 0, {})


def test_invalid_transition_destination_is_rejected() -> None:
    rom = fixture_rom()
    struct.pack_into("<H", rom, 0x408, evidence.ROOM_COUNT)
    with pytest.raises(ValueError, match="Invalid destination room"):
        evidence.extract_room(rom, 0, {})


def test_room_identity_uses_completion_index_not_object_list_index() -> None:
    rom = fixture_rom()
    struct.pack_into("<H", rom, evidence.ROOM_PROPS + 0x20, 7)
    room = evidence.extract_room(rom, 0, {
        "correct": {"room_sanity": {"included": True, "bit_index": 0}},
        "wrong": {"room_sanity": {"included": True, "bit_index": 7}},
    })
    assert room["object_list_idx"] == 7
    assert room["ap_room_keys"] == ["correct"]
