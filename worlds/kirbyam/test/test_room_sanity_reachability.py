"""Singleton physical-room checks must not connect logical compartments (#945)."""
from collections import Counter

import pytest
from BaseClasses import CollectionState, MultiWorld, Region

from .. import KirbyAmWorld
from ..data import LocationCategory, data, load_json_data
from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive


SPLITS = {name: list(row["logical_subregions"])
          for name, row in load_json_data("regions/rooms.json").items()
          if row.get("logical_subregions")}
ENTRY_CASES = [(parent, source) for parent, entries in SPLITS.items()
               for source in [parent, *(f"{parent}__LOGIC__{key}" for key in entries)]]


@pytest.mark.parametrize("parent,entry", ENTRY_CASES)
def test_each_compartment_reaches_one_physical_check_without_traversal(parent, entry):
    check_name = f"{parent}__ROOM_CHECK"
    names = [parent, *(f"{parent}__LOGIC__{key}" for key in SPLITS[parent]), check_name]
    mw = MultiWorld(1)
    mw.worlds[1] = KirbyAmWorld(mw, 1)
    regions = {name: Region(name, 1, mw) for name in ["Menu", *names]}
    mw.regions.extend(regions.values())
    for name in names:
        definition = data.regions[name]
        for destination in definition.exits:
            if destination in regions:
                regions[name].connect(regions[destination])
        for key in definition.locations:
            location = data.locations[key]
            if location.category == LocationCategory.ROOM_SANITY:
                regions[name].add_locations({location.label: location.location_id})
    regions["Menu"].connect(regions[entry])
    state = CollectionState(mw)
    checks = list(mw.get_locations(1))
    assert len(checks) == 1
    assert checks[0].can_reach(state)
    assert checks[0].parent_region.name == check_name
    assert not regions[check_name].exits
    assert {name for name in names if regions[name].can_reach(state)} == {entry, check_name}


def test_physical_room_location_ids_and_bits_stay_unique():
    locations = [loc for loc in data.locations.values() if loc.category == LocationCategory.ROOM_SANITY]
    assert len(locations) == 263
    assert len({loc.location_id for loc in locations}) == 263
    assert len({loc.bit_index for loc in locations}) == 263
    owners = Counter(key for region in data.regions.values() for key in region.locations)
    assert all(owners[loc.name] == 1 for loc in locations)


def test_moonlight_lower_ingress_preserves_directed_native_route():
    rooms = load_json_data("regions/rooms.json")
    prefix = "REGION_MOONLIGHT_MANSION/ROOM_"
    # Native 702: spawn (4, 12), open chute x=5..6 down to lower y=17.
    assert rooms[prefix + "2_05"]["exits"][prefix + "2_05_LOWER"] is None
    assert rooms[prefix + "2_05_LOWER"]["exits"][prefix + "2_06"] == "can_fly"
    # Native 702 (43,17) -> 744 (2,3); 744 (3,58) -> 745 (7,3).
    assert prefix + "2_GOAL_1" in rooms[prefix + "2_06"]["exits"]
    assert prefix + "2_06" not in rooms[prefix + "2_GOAL_1"]["exits"]
    assert prefix + "2_GOAL_1" not in rooms["REGION_RAINBOW_ROUTE/ROOM_1_HUB_3"]["exits"]


@pytest.mark.parametrize("goal", range(3))
@pytest.mark.parametrize("room_sanity", range(2))
@pytest.mark.parametrize("shards", [0, 2])
@pytest.mark.parametrize("gating", range(2))
def test_room_sanity_archive_accessibility_across_goals_and_options(tmp_path, goal, room_sanity, shards, gating):
    scenario = goal * 8 + room_sanity * 4 + shards + gating
    minimum, maximum = [(1, 1), (1, 10), (6, 10)][scenario % 3]
    player = tmp_path / "player.yaml"
    player.write_text(
        "name: Room Check\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n"
        f"  goal: {goal}\n  configured_area_boss: {scenario % 8}\n"
        f"  shards: {shards}\n  room_sanity: {room_sanity}\n  ability_gating: {gating}\n"
        f"  minimum_health: {minimum}\n  maximum_health: {maximum}\n"
        f"  start_with_all_maps: {scenario % 2}\n", encoding="utf-8",
    )
    archive = generate_archive_from_fixture(player, tmp_path / "output", seed=945 + scenario)
    decoded = load_multidata_from_archive(archive)
    actual = set(decoded["locations"][1])
    expected = {loc.location_id for loc in data.locations.values()
                if loc.category == LocationCategory.ROOM_SANITY}
    assert actual & expected == (expected if room_sanity else set())
    assert decoded["slot_data"][1]["room_sanity"] == room_sanity


def test_issue_945_original_generation_seed(tmp_path):
    player = tmp_path / "player.yaml"
    player.write_text(
        "name: Room Baseline\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n"
        "  room_sanity: 1\n  shards: 2\n  goal: 1\n  ability_gating: 0\n",
        encoding="utf-8",
    )
    generate_archive_from_fixture(player, tmp_path / "output", seed=935)
