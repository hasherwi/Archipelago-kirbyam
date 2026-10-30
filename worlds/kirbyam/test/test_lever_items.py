"""Contracts for AP-owned lever wall items (Issue #859)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from BaseClasses import ItemClassification

from ..data import data, load_json_data


_EXPECTED_LEVER_ITEMS = {
    "LEVER_WALL_MOONLIGHT_MANSION_2_11": (3860037, "Moonlight Mansion 2-11 - Lever Wall"),
    "LEVER_WALL_OLIVE_OCEAN_6_13": (3860038, "Olive Ocean 6-13 - Lever Wall"),
    "LEVER_WALL_CARROT_CASTLE_5_12": (3860039, "Carrot Castle 5-05 - Lever Wall"),
    "LEVER_WALL_RADISH_RUINS_8_12": (3860040, "Radish Ruins 8-12 - Lever Wall"),
}

_EXPECTED_LEVER_ROOMS = {
    "REGION_MOONLIGHT_MANSION/ROOM_2_11": 82,
    "REGION_OLIVE_OCEAN/ROOM_6_13": 202,
    "REGION_CARROT_CASTLE/ROOM_5_05": 252,
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
    assert "ap_lever_bit_for_obj(chest_obj_ptr)" in payload
    assert "AP_LEVER_ACTIVATION_FLAGS |= lever_bit" in payload
    assert "void ap_on_initialize_chest(void *chest)" in payload
    assert "void ap_on_chest_popup_room_counter" in payload
    assert "native_effect();" in payload

    assert "lever_wall_chest_ids[4] = {18u, 65u, 77u, 74u}" in payload
    assert "KIRBY_ITEM_ID_BASE_OFFSET + 37u" in payload
    assert "KIRBY_ITEM_ID_BASE_OFFSET + 40u" in payload


def test_carrot_lever_matches_native_room_and_preserves_identity() -> None:
    import json

    fixture_path = Path(__file__).parent / "data" / "carrot-lever-native.json"
    evidence = json.loads(fixture_path.read_text(encoding="utf-8"))
    room_key = "REGION_CARROT_CASTLE/ROOM_5_05"
    assert evidence["room"]["native_room_id"] == evidence["carrot_lever"]["native_room_id"] == 170
    assert room_key in evidence["room"]["ap_room_keys"]
    assert evidence["room"]["doors_idx"] == evidence["carrot_lever"]["object_list_idx"] == 252
    assert evidence["carrot_lever"] == {
        "source": "0x008D2E68", "native_room_id": 170, "object_list_idx": 252,
        "flag": 77, "reward": 99, "type": 129,
    }
    location_key = "LEVER_CARROT_CASTLE_5_12"  # Preserve the legacy internal key.
    location = data.locations[location_key]
    assert (location.location_id, location.bit_index) == (3960417, 2)
    assert location.label == "Carrot Castle 5-05 - Lever"
    assert location.parent_region == room_key
    assert [key for key, region in data.regions.items() if location_key in region.locations] == [room_key]
    assert data.item_key_to_id["LEVER_WALL_CARROT_CASTLE_5_12"] == 3860039


def test_generated_carrot_lever_check_and_event_belong_only_to_room_five() -> None:
    from test.general import setup_solo_multiworld
    from .. import KirbyAmWorld

    multiworld = setup_solo_multiworld(KirbyAmWorld, steps=("generate_early", "create_regions"), seed=972)
    check = multiworld.get_location("Carrot Castle 5-05 - Lever", 1)
    event = multiworld.get_location("Activate Lever - Carrot Castle 5-05", 1)
    assert check.address == 3960417
    assert check.parent_region is multiworld.get_region("REGION_CARROT_CASTLE/ROOM_5_05", 1)
    assert event.parent_region is check.parent_region
    assert event.address is None and event.locked
    assert event.item is not None and event.item.name == event.name
    old_room = multiworld.get_region("REGION_CARROT_CASTLE/ROOM_5_12", 1)
    assert all("Lever" not in location.name for location in old_room.locations)
    assert len([location for location in multiworld.get_locations(1) if location.address == 3960417]) == 1


def test_generated_carrot_wall_still_requires_received_wall_item() -> None:
    from BaseClasses import CollectionState
    from test.general import setup_solo_multiworld
    from .. import KirbyAmWorld

    multiworld = setup_solo_multiworld(KirbyAmWorld, seed=972)
    room = multiworld.get_region("REGION_CARROT_CASTLE/ROOM_5_05", 1)
    wall_exit = next(exit for exit in room.exits if exit.connected_region is not None
                     and exit.connected_region.name == "REGION_CARROT_CASTLE/ROOM_5_06")
    state = CollectionState(multiworld)
    assert not wall_exit.access_rule(state)
    world = multiworld.worlds[1]
    event_item = multiworld.get_location("Activate Lever - Carrot Castle 5-05", 1).item
    assert event_item is not None
    state.collect(event_item, prevent_sweep=True)
    assert not wall_exit.access_rule(state)
    state.collect(world.create_item("Carrot Castle 5-05 - Lever Wall"), prevent_sweep=True)
    assert wall_exit.access_rule(state)


def test_carrot_lever_move_preserves_current_room_topology() -> None:
    rooms = cast(dict[str, Any], load_json_data("regions/rooms.json"))
    assert rooms["REGION_CARROT_CASTLE/ROOM_5_05"]["exits"] == {
        "REGION_CARROT_CASTLE/ROOM_5_HUB": None,
        "REGION_CARROT_CASTLE/ROOM_5_06": "cc_lever",
        "REGION_CARROT_CASTLE/ROOM_5_07": None,
    }
    old_room = rooms["REGION_CARROT_CASTLE/ROOM_5_12"]
    assert old_room["exits"] == {
        "REGION_CARROT_CASTLE/ROOM_5_BOSS": None,
        "REGION_CARROT_CASTLE/ROOM_5_13": None,
    }
    assert old_room["logical_exit_overrides"] == {
        "REGION_CARROT_CASTLE/ROOM_5_13": "ENTRY_FROM_5_12",
    }
