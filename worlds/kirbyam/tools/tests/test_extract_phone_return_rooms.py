"""Test extraction with synthetic table contents, not game bytes."""
import struct

import pytest

from worlds.kirbyam.tools.extract_phone_return_rooms import (
    ENCOUNTER_ROOM_TABLE, L_RETURN_FLAG, PRIORITY_FLAGS_OFFSET, ROOM_PROPS, ROOM_RECORD_SIZE,
    _room_flags, build_evidence,
)


def _fixture():
    rom = bytearray(ROOM_PROPS + 3 * ROOM_RECORD_SIZE)
    # Encounter slots 1 and 12 both refer to the first synthetic room.
    encounters = [100] * 16
    encounters[1] = encounters[9] = 1
    struct.pack_into("<16H", rom, ENCOUNTER_ROOM_TABLE, *encounters)
    for room, flags in ((1, L_RETURN_FLAG | 0x10), (2, 0x10)):
        struct.pack_into("<H", rom, ROOM_PROPS + room * ROOM_RECORD_SIZE + PRIORITY_FLAGS_OFFSET, flags)
    catalog = {"rooms": [{"native_id": 1, "ap_keys": ["LOWER", "UPPER"]},
                         {"native_id": 2, "ap_keys": ["ELSEWHERE"]}]}
    return rom, catalog


def test_static_flag_and_session_slots_stay_separate():
    rom, catalog = _fixture()
    assert _room_flags(rom, catalog) == [
        {"native_room": 1, "ap_compartments": ["LOWER", "UPPER"],
         "room_allows_phone_return": True, "encounter_session_slots": [1, 12]},
        {"native_room": 2, "ap_compartments": ["ELSEWHERE"],
         "room_allows_phone_return": False, "encounter_session_slots": []},
    ]


def test_catalog_cannot_mistake_a_sentinel_for_an_enabled_room():
    rom, catalog = _fixture()
    struct.pack_into("<H", rom, ROOM_PROPS + ROOM_RECORD_SIZE + PRIORITY_FLAGS_OFFSET, 0xFFFF)
    with pytest.raises(ValueError, match="unused native room"):
        _room_flags(rom, catalog)


def test_production_extractor_refuses_unverified_game_files():
    rom, catalog = _fixture()
    with pytest.raises(ValueError, match="unmodified USA ROM"):
        build_evidence(bytes(rom), catalog)
