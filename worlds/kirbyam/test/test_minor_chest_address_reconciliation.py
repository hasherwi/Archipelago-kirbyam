from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "enumerate_minor_chests.py"
_spec = importlib.util.spec_from_file_location("enumerate_minor_chests", MODULE_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"Unable to load module spec from {MODULE_PATH}")
_enumerate_minor_chests = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_enumerate_minor_chests)


def test_resolve_amr_entry_rom_offset_prefers_direct_fragment_match() -> None:
    payload = bytes.fromhex("80ff02000006")
    object_template_addr = 0x200
    raw_addr = object_template_addr + _enumerate_minor_chests.AMR_OBJECT_TEMPLATE_FRAGMENT_OFFSET
    rom = bytearray(0x1000)
    rom[raw_addr:raw_addr + len(payload)] = payload

    resolved, mode = _enumerate_minor_chests.resolve_amr_entry_rom_offset(raw_addr, bytes(rom), payload)

    assert resolved == object_template_addr
    assert mode == "direct"


def test_resolve_amr_entry_rom_offset_uses_jp_to_us_shift() -> None:
    payload = bytes.fromhex("80ff02000006")
    object_template_addr = 0x300
    raw_addr = object_template_addr + _enumerate_minor_chests.AMR_OBJECT_TEMPLATE_FRAGMENT_OFFSET
    shifted_template_addr = object_template_addr + _enumerate_minor_chests.AMR_JP_TO_US_ROM_SHIFT
    shifted_payload_addr = shifted_template_addr + _enumerate_minor_chests.AMR_OBJECT_TEMPLATE_FRAGMENT_OFFSET
    rom = bytearray(shifted_payload_addr + len(payload) + 0x20)
    rom[shifted_payload_addr:shifted_payload_addr + len(payload)] = payload

    resolved, mode = _enumerate_minor_chests.resolve_amr_entry_rom_offset(raw_addr, bytes(rom), payload)

    assert resolved == shifted_template_addr
    assert mode == "jp_to_us_shift"


def test_resolve_amr_entry_rom_offset_rejects_template_base_payload_match() -> None:
    payload = bytes.fromhex("80ff02000006")
    template_base = 0x400
    fragment = template_base + _enumerate_minor_chests.AMR_OBJECT_TEMPLATE_FRAGMENT_OFFSET
    rom = bytearray(0x1000)
    rom[template_base:template_base + len(payload)] = payload

    with pytest.raises(ValueError, match="Unable to resolve AMR SmallChest address"):
        _enumerate_minor_chests.resolve_amr_entry_rom_offset(fragment, bytes(rom), payload)

    rom[template_base:template_base + len(payload)] = bytes(len(payload))
    rom[fragment:fragment + len(payload)] = payload
    resolved, _ = _enumerate_minor_chests.resolve_amr_entry_rom_offset(fragment, bytes(rom), payload)

    assert resolved == template_base


def test_parse_groomprops_uses_room_object_list_index_at_plus_20() -> None:
    room_entry = 7
    room_base = _enumerate_minor_chests.ROOM_PROPS_ROM_BASE + (
        room_entry * _enumerate_minor_chests.ROOM_PROPS_STRIDE
    )
    rom = bytearray(_enumerate_minor_chests.ROOM_PROPS_ROM_BASE + _enumerate_minor_chests.ROOM_PROPS_SIZE)
    rom[room_base + 0x20:room_base + 0x22] = (0x1234).to_bytes(2, "little")
    rom[room_base + 0x22:room_base + 0x24] = (0x5678).to_bytes(2, "little")
    rom[room_base + 0x24:room_base + 0x26] = (0x9ABC).to_bytes(2, "little")

    room = _enumerate_minor_chests.parse_groomprops(bytes(rom))[room_entry]

    assert room["object_list_idx"] == 0x1234
    assert room["doors_idx"] == 0x9ABC
    assert "object_list2_idx" not in room


def test_decode_amr_small_chest_fragment_uses_reward_byte_two_and_flag_byte_five() -> None:
    # Keep the adjacent unknown/auxiliary bytes nonzero to guard field offsets.
    fields = _enumerate_minor_chests.decode_amr_small_chest_fragment(bytes.fromhex("80ff02000152"))

    assert fields["reward_id"] == 2
    assert fields["unknown_object_field"] == 0
    assert fields["entry_aux_hi"] == 1
    assert fields["native_chest_flag_index"] == 0x52


def test_decode_amr_small_chest_fragment_rejects_wrong_width() -> None:
    with pytest.raises(ValueError, match="Expected 6-byte AMR fragment"):
        _enumerate_minor_chests.decode_amr_small_chest_fragment(b"short")


@pytest.mark.parametrize("reward_id", range(6))
def test_reward_ids_zero_through_five_are_ordinary_item_chests(reward_id: int) -> None:
    reward_path, is_ordinary_item_chest = _enumerate_minor_chests.classify_reward_profile(reward_id)

    assert reward_path == "ordinary_item_chest"
    assert is_ordinary_item_chest is True


@pytest.mark.parametrize(
    ("reward_id", "expected_path"),
    [
        (0x06, "vitality_chest"),
        (0x0A, "big_chest"),
        (0x13, "big_chest"),
        (0x14, "spray_paint_chest"),
        (0x21, "spray_paint_chest"),
        (0x28, "music_or_sound_chest"),
        (0x32, "music_or_sound_chest"),
        (0x63, "no_bonus_chest"),
        (0x07, "unclassified_chest_reward"),
    ],
)
def test_fixed_reward_ids_follow_native_chest_dispatch(reward_id: int, expected_path: str) -> None:
    reward_path, is_ordinary_item_chest = _enumerate_minor_chests.classify_reward_profile(reward_id)

    assert reward_path == expected_path
    assert is_ordinary_item_chest is False


def test_room_duplicate_summary_uses_unique_template_offsets() -> None:
    rooms = [
        {"entry_index": 1, "candidate_ap_room_keys": ["ROOM_A"], "rom_offset": "0x100"},
        {"entry_index": 2, "candidate_ap_room_keys": ["ROOM_A"], "rom_offset": "0x200"},
        {"entry_index": 3, "candidate_ap_room_keys": ["ROOM_B"], "rom_offset": "0x300"},
    ]

    summary = _enumerate_minor_chests.summarize_duplicate_room_sources(rooms)

    assert summary == [{
        "room_key": "ROOM_A",
        "chest_count": 2,
        "source_rom_offsets": ["0x100", "0x200"],
        "source_offsets_unique": True,
    }]


def test_checked_in_rom_manifest_matches_all_active_ordinary_chests() -> None:
    world_dir = MODULE_PATH.parents[1]
    manifest = json.loads((world_dir / "data" / "minor_chest_manifest.json").read_text(encoding="utf-8"))
    locations = json.loads((world_dir / "data" / "locations.json").read_text(encoding="utf-8"))

    ordinary_entries = [entry for entry in manifest["entries"] if entry["is_ordinary_item_chest"]]
    active_locations = [
        location for location in locations.values()
        if location.get("category") == "MINOR_CHEST" and location.get("source_rom_offset") is not None
        and "NativeRewardConsumable" in location.get("tags", [])
    ]

    assert manifest["metadata"]["rom_sha1"] == _enumerate_minor_chests.AUTHORIZED_USA_ROM_SHA1
    assert len(ordinary_entries) == 41
    assert len(active_locations) == 41
    assert {entry["rom_offset"] for entry in ordinary_entries} == {
        location["source_rom_offset"] for location in active_locations
    }
    assert tuple(sorted(entry["native_chest_flag_index"] for entry in ordinary_entries)) == (
        _enumerate_minor_chests.EXPECTED_CONSUMABLE_CHEST_FLAGS
    )
    assert all(len(entry["candidate_ap_room_keys"]) == 1 for entry in ordinary_entries)
    assert sorted(location["location_id"] for location in active_locations) == list(range(3960566, 3960607))


def test_native_small_chest_persistence_supports_flag_82() -> None:
    world_dir = MODULE_PATH.parents[1]
    payload = (world_dir / "kirby_ap_payload" / "ap_payload.c").read_text(encoding="utf-8")

    assert "if (chest_index >= 128u)" in payload
    assert "if (chest_index >= 80u)" not in payload
