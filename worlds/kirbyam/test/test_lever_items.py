"""Contracts for AP-owned lever wall items (Issue #859)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from BaseClasses import ItemClassification

from ..data import data, load_json_data


_EXPECTED_LEVER_ITEMS = {
    "LEVER_WALL_MOONLIGHT_MANSION_2_11": (3860037, "Moonlight Mansion 2-11 - Lever Wall"),
    "LEVER_WALL_OLIVE_OCEAN_6_13": (3860038, "Olive Ocean 6-13 - Lever Wall"),
    "LEVER_WALL_CARROT_CASTLE_5_12": (3860039, "Carrot Castle 5-12 - Lever Wall"),
    "LEVER_WALL_RADISH_RUINS_8_12": (3860040, "Radish Ruins 8-12 - Lever Wall"),
}

_EXPECTED_LEVER_ROOMS = {
    "REGION_MOONLIGHT_MANSION/ROOM_2_11": 82,
    "REGION_OLIVE_OCEAN/ROOM_6_13": 202,
    "REGION_CARROT_CASTLE/ROOM_5_12": 254,
    "REGION_RADISH_RUINS/ROOM_8_12": 239,
}


def test_lever_wall_items_are_unique_progression_items() -> None:
    for item_key, (expected_id, expected_label) in _EXPECTED_LEVER_ITEMS.items():
        item_id = data.item_key_to_id[item_key]
        item = data.items[item_id]
        assert item_id == expected_id
        assert item.label == expected_label
        assert item.classification == ItemClassification.progression
        assert "Levers" in item.tags
        assert "Unique" in item.tags


def test_lever_room_doors_idx_contract_matches_room_data() -> None:
    rooms = cast(dict[str, Any], load_json_data("regions/rooms.json"))
    for room_key, expected_doors_idx in _EXPECTED_LEVER_ROOMS.items():
        room = rooms[room_key]
        room_sanity = room.get("room_sanity")
        locations = room.get("locations")
        if not isinstance(room_sanity, dict) and isinstance(locations, dict):
            room_sanity = locations.get("room_sanity")
        assert isinstance(room_sanity, dict)
        assert room_sanity["bit_index"] == expected_doors_idx


def test_payload_decouples_physical_lever_from_wall_unlock() -> None:
    world_dir = Path(__file__).resolve().parents[1]
    payload = (world_dir / "kirby_ap_payload" / "ap_payload.c").read_text(encoding="utf-8")

    assert "AP_LEVER_ACTIVATION_FLAGS" in payload
    assert "void ap_on_small_switch_effect(KirbySmallSwitchEffectFn native_effect)" in payload
    for doors_idx in _EXPECTED_LEVER_ROOMS.values():
        assert f"case {doors_idx}u:" in payload
    assert "AP_LEVER_ACTIVATION_FLAGS |= activation_bit" in payload
    assert "native_effect();" in payload

    assert "lever_wall_chest_ids[4] = {18u, 65u, 77u, 74u}" in payload
    assert "KIRBY_ITEM_ID_BASE_OFFSET + 37u" in payload
    assert "KIRBY_ITEM_ID_BASE_OFFSET + 40u" in payload
