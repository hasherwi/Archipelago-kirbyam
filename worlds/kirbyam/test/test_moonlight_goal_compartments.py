"""Verified native 146/148 compartments, independent of any future Phone gate."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, cast

import pytest

from BaseClasses import CollectionState
from test.general import setup_multiworld

from .. import KirbyAmWorld
from ..data import data, load_json_data
from ..tools import enumerate_minor_chests as extractor

PREFIX = "REGION_MOONLIGHT_MANSION/ROOM_2_"
ROOM_18 = PREFIX + "18"
BOTTOM_RIGHT = ROOM_18 + "_BOTTOM_RIGHT"
GOAL_MAIN = PREFIX + "GOAL_2"
UPPER_LEFT = GOAL_MAIN + "_UPPER_LEFT"
CHALK = "MINOR_CHEST_SPRAY_PAINT_14"
MAIN_CHEST = "MINOR_CHEST_MOONLIGHT_MANSION_2_GOAL_2_OBJECT_01"
CENTRAL_CIRCLE = "REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE"


def test_chalk_identity_and_unique_upper_left_owner() -> None:
    chest = data.locations[CHALK]
    assert chest.location_id == 3960513
    assert chest.label == "Moonlight Mansion 2-GOAL-2 - Spray Paint #14 Chest"
    assert chest.source_rom_offset == 0x008BC114
    assert chest.parent_region == UPPER_LEFT
    assert [region.name for region in data.regions.values() if CHALK in region.locations] == [UPPER_LEFT]

    locations = cast(dict[str, Any], load_json_data("locations.json"))
    assert locations[CHALK]["parent_region"] == UPPER_LEFT
    assert locations[CHALK]["source_rom_offset"] == "0x008BC114"
    recovery = cast(dict[str, Any], load_json_data("chest_recovery.json"))
    records = [row for row in recovery["records"] if row["location_key"] == CHALK]
    assert len(records) == 1
    native = records[0]
    assert (native["source"], native["flag"], native["position"], native["rooms"]) == (
        "0x008BC114", 13, [112, 72], [148],
    )
    manifest = cast(dict[str, Any], load_json_data("minor_chest_manifest.json"))
    sources = [entry for entry in manifest["entries"] if entry["rom_offset"] == "0x008BC114"]
    assert len(sources) == 1
    source = sources[0]
    assert (source["native_reward_id"], source["native_chest_flag_index"], source["candidate_native_room_ids"]) == (
        33, 13, [148],
    )
    assert source["candidate_ap_room_keys"] == [chest.parent_region]
    assert source["room_sanity_ap_room_keys"] == [GOAL_MAIN]
    assert source["ap_room_mapping_evidence"] == (
        "dev-docs/phone-heave-ho-acceptance.md#qualified-retry-crossings-and-physical-collection"
    )
    summary = extractor.summarize_duplicate_room_sources(manifest["entries"])
    assert manifest["multi_chest_room_disambiguation"] == summary
    assert not any(row["room_key"] in {GOAL_MAIN, UPPER_LEFT} for row in summary)
    assert manifest["metadata"]["multi_chest_rooms_total"] == len(summary)
    assert manifest["metadata"]["multi_chest_rooms_exact_source_offsets_unique"] == sum(
        row["source_offsets_unique"] for row in summary
    )


@pytest.mark.parametrize("field,value", [
    ("native_reward_id", 32),
    ("native_chest_flag_index", 12),
    ("candidate_native_room_ids", [147]),
    ("candidate_doors_idx", [63]),
    ("candidate_ap_room_keys", [ROOM_18]),
])
def test_chalk_extractor_override_rejects_changed_identity(field: str, value: Any) -> None:
    manifest = cast(dict[str, Any], load_json_data("minor_chest_manifest.json"))
    source = deepcopy(next(entry for entry in manifest["entries"] if entry["rom_offset"] == "0x008BC114"))
    source["candidate_ap_room_keys"] = [GOAL_MAIN]
    source[field] = value
    rooms = cast(dict[str, Any], load_json_data("regions/rooms.json"))
    with pytest.raises(ValueError, match=f"identity mismatch: {field}="):
        extractor.apply_reviewed_chest_compartment(source, rooms)


@pytest.mark.parametrize("owners", [[], [GOAL_MAIN], [GOAL_MAIN, UPPER_LEFT]])
def test_chalk_extractor_override_requires_unique_reviewed_owner(owners: list[str]) -> None:
    manifest = cast(dict[str, Any], load_json_data("minor_chest_manifest.json"))
    source = deepcopy(next(entry for entry in manifest["entries"] if entry["rom_offset"] == "0x008BC114"))
    source["candidate_ap_room_keys"] = [GOAL_MAIN]
    rooms = {room: {"locations": {CHALK: None} if room in owners else {}}
             for room in (GOAL_MAIN, UPPER_LEFT)}
    with pytest.raises(ValueError, match="must uniquely own"):
        extractor.apply_reviewed_chest_compartment(source, rooms)


def test_manifest_regeneration_preserves_reviewed_compartment_and_other_sources(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Run the extractor on synthetic templates/room props, never private ROM bytes."""
    manifest = cast(dict[str, Any], load_json_data("minor_chest_manifest.json"))
    entries = manifest["entries"]
    rom = bytearray(extractor.ROOM_PROPS_ROM_BASE + extractor.ROOM_PROPS_SIZE)
    for entry in entries:
        fragment = bytes.fromhex(entry["amr_packed_item_hex"])
        offset = int(entry["rom_offset"], 16) + extractor.AMR_OBJECT_TEMPLATE_FRAGMENT_OFFSET
        rom[offset:offset + len(fragment)] = fragment
    for slot in manifest["slot_resolution_summary"]:
        for native_room in slot["candidate_native_room_ids"]:
            offset = extractor.ROOM_PROPS_ROM_BASE + native_room * extractor.ROOM_PROPS_STRIDE
            object_index = extractor.resolve_amr_room_slot_object_list_idx(slot["amr_room_slot"])
            object_offset = offset + extractor.ROOM_PROPS_OBJECT_LIST_IDX_OFFSET
            rom[object_offset:object_offset + 2] = object_index.to_bytes(2, "little")
            assert len(slot["candidate_doors_idx"]) == 1
            doors_offset = offset + extractor.ROOM_PROPS_DOORS_IDX_OFFSET
            rom[doors_offset:doors_offset + 2] = slot["candidate_doors_idx"][0].to_bytes(2, "little")

    rom_path = tmp_path / "synthetic-templates.gba"
    rom_path.write_bytes(rom)
    amr_path = tmp_path / "items.json"
    amr_path.write_text(json.dumps({"SmallChest": {
        "item": [entry["amr_packed_item"] for entry in entries],
        "address": [int(entry["raw_address"], 16) for entry in entries],
        "room": [entry["amr_room_slot"] for entry in entries],
    }}))
    output_path = tmp_path / "manifest.json"
    rooms_path = Path(__file__).resolve().parents[1] / "data" / "regions" / "rooms.json"
    # Only this synthetic fixture's digest is accepted in this isolated unit test.
    monkeypatch.setattr(extractor, "AUTHORIZED_USA_ROM_SHA1", hashlib.sha1(rom).hexdigest())
    monkeypatch.setattr(sys, "argv", [
        "enumerate_minor_chests", "--rom", str(rom_path), "--amr-items", str(amr_path),
        "--rooms", str(rooms_path), "--output", str(output_path),
    ])
    assert extractor.main() == 0
    generated = json.loads(output_path.read_text())
    # Synthetic surrounding template bytes deliberately have different hashes.
    # Every other source field, including each reviewed/coarse AP owner, matches.
    for expected, actual in zip(entries, generated["entries"], strict=True):
        assert {key: value for key, value in actual.items() if key != "rom_slice_sha256"} == {
            key: value for key, value in expected.items() if key != "rom_slice_sha256"
        }
    for field in ("multi_chest_room_disambiguation", "slot_resolution_summary", "reward_path_summary"):
        assert generated[field] == manifest[field]
    for field in ("multi_chest_rooms_total", "multi_chest_rooms_exact_source_offsets_unique"):
        assert generated["metadata"][field] == manifest["metadata"][field]


def test_native_return_door_targets_room_18_bottom_right_only() -> None:
    rooms = cast(dict[str, Any], load_json_data("regions/rooms.json"))
    assert rooms[UPPER_LEFT] == {
        "locations": {CHALK: None},
        "exits": {BOTTOM_RIGHT: None},
    }
    assert data.regions[UPPER_LEFT].exits == [BOTTOM_RIGHT]
    assert not data.regions[UPPER_LEFT].exit_requirements
    assert not data.regions[UPPER_LEFT].location_requirements
    # The native return spawns at (13, 9), inside the bottom-right compartment.
    # It must not bypass the existing internal flight requirement to room 18.
    assert rooms[BOTTOM_RIGHT] == {
        "locations": {},
        "exits": {ROOM_18: "can_fly", UPPER_LEFT: None},
    }
    assert data.regions[BOTTOM_RIGHT].exit_requirements == {ROOM_18: "can_fly"}


def test_other_moonlight_checks_and_exits_are_unchanged() -> None:
    rooms = cast(dict[str, Any], load_json_data("regions/rooms.json"))
    assert rooms[GOAL_MAIN] == {
        "locations": {
            "room_sanity": {"included": True, "location_id": 3961055, "bit_index": 64},
            MAIN_CHEST: None,
        },
        "exits": {CENTRAL_CIRCLE: {"all": ["can_fly", "can_break_floating_block"]}},
    }
    assert data.locations[MAIN_CHEST].parent_region == GOAL_MAIN
    assert data.locations[MAIN_CHEST].source_rom_offset == 0x008BC018
    assert rooms[GOAL_MAIN + "_UPPER_RIGHT"] == {
        "locations": {}, "exits": {PREFIX + "20": None},
    }
    assert rooms[GOAL_MAIN + "_BOTTOM_RIGHT"] == {
        "locations": {}, "exits": {GOAL_MAIN: None},
    }
    assert rooms[ROOM_18] == {
        "locations": {
            "room_sanity": {"included": True, "location_id": 3961053, "bit_index": 62},
        },
        "exits": {
            ROOM_18 + "_UPPER_LEFT": "can_climb",
            PREFIX + "17": None,
            PREFIX + "19": None,
            BOTTOM_RIGHT: None,
        },
    }
    assert rooms[ROOM_18 + "_UPPER_LEFT"] == {
        "locations": {}, "exits": {PREFIX + "16": None, ROOM_18: None},
    }


@pytest.mark.parametrize("room_sanity", [0, 1])
@pytest.mark.parametrize("ability_gating", [0, 1])
@pytest.mark.parametrize("ability_randomization_mode", [0, 1, 2])
def test_built_regions_and_slot_data_keep_correct_compartments(
    room_sanity: int, ability_gating: int, ability_randomization_mode: int,
) -> None:
    multiworld = setup_multiworld(KirbyAmWorld, seed=1086, options={
        "room_sanity": room_sanity,
        "ability_gating": ability_gating,
        "ability_randomization_mode": ability_randomization_mode,
    })
    upper_left = multiworld.get_region(UPPER_LEFT, 1)
    main = multiworld.get_region(GOAL_MAIN, 1)
    chalk = multiworld.get_location(data.locations[CHALK].label, 1)
    assert chalk.parent_region is upper_left
    assert chalk.address == 3960513
    assert sum(location.address == chalk.address for location in multiworld.get_locations(1)) == 1
    assert multiworld.get_location(data.locations[MAIN_CHEST].label, 1).parent_region is main
    assert {location.address for location in main.locations} == (
        {data.locations[MAIN_CHEST].location_id, 3961055} if room_sanity
        else {data.locations[MAIN_CHEST].location_id}
    )
    door = multiworld.get_entrance(f"{UPPER_LEFT} -> {BOTTOM_RIGHT}", 1)
    assert door.connected_region is multiworld.get_region(BOTTOM_RIGHT, 1)
    assert door.access_rule(CollectionState(multiworld))
    assert {exit.connected_region.name for exit in upper_left.exits if exit.connected_region} == {
        BOTTOM_RIGHT, "REGION_MOONLIGHT_MANSION/MAIN",
    }
    with pytest.raises(KeyError):
        multiworld.get_entrance(f"{UPPER_LEFT} -> {ROOM_18}", 1)
    slot_rooms = cast(dict[str, Any], multiworld.worlds[1].fill_slot_data()["rooms"])
    assert slot_rooms[UPPER_LEFT]["exits"] == [BOTTOM_RIGHT]


def test_return_reachability_does_not_skip_internal_room_18_edge() -> None:
    multiworld = setup_multiworld(KirbyAmWorld, seed=1086, options={"room_sanity": 1})
    # Isolate a start in the actual upper-left compartment. This checks graph
    # wiring, not whether the Heave-Ho block or a Phone route is traversable.
    multiworld.get_entrance("Start Game", 1).access_rule = lambda state: False
    multiworld.get_region("Menu", 1).connect(multiworld.get_region(UPPER_LEFT, 1), "Test Upper-Left Entry")
    internal = multiworld.get_entrance(f"{BOTTOM_RIGHT} -> {ROOM_18}", 1)
    existing_rule = internal.access_rule
    internal.access_rule = lambda state: False
    state = CollectionState(multiworld)

    assert multiworld.get_location(data.locations[CHALK].label, 1).can_reach(state)
    assert multiworld.get_region(BOTTOM_RIGHT, 1).can_reach(state)
    assert not multiworld.get_region(ROOM_18, 1).can_reach(state)
    assert not multiworld.get_region(GOAL_MAIN, 1).can_reach(state)
    assert not multiworld.get_location(data.locations[MAIN_CHEST].label, 1).can_reach(state)

    # Preserve the existing solo-compatible policy, with no new Phone item gate.
    internal.access_rule = existing_rule
    assert multiworld.get_region(ROOM_18, 1).can_reach(CollectionState(multiworld))
