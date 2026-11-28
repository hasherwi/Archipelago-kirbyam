"""Test physical check ownership independently of AP item delivery and goal completion."""
from copy import deepcopy

import pytest

from BaseClasses import CollectionState
from test.general import setup_multiworld

from .. import KirbyAmWorld
from ..data import LocationCategory, data, load_json_data, validate_check_placement
from ..rules import set_rules


@pytest.mark.parametrize("room_sanity,enabled", [(0, 140), (1, 395)])
def test_region_builder_materializes_only_enabled_checks_and_addressless_goals(room_sanity, enabled):
    mw = setup_multiworld(KirbyAmWorld, steps=("create_regions",), options={"room_sanity": room_sanity})
    rows = mw.get_locations(1)
    addressed = {loc.key: loc for loc in rows if loc.address is not None}
    assert len(addressed) == enabled == sum(loc.address is not None for loc in rows)
    for key, definition in data.locations.items():
        actual = addressed.get(key)
        if definition.category == LocationCategory.GOAL:
            goal = mw.get_location(definition.label, 1)
            assert actual is None and goal.address is None and goal.locked
            assert goal.parent_region.name == definition.parent_region
            assert goal.item.name == goal.name and goal.item.code is None
            assert goal.name not in KirbyAmWorld.location_name_to_id
        elif definition.category == LocationCategory.ROOM_SANITY and not room_sanity and "CoreLandmark" not in definition.tags:
            assert actual is None
        else:
            assert actual is not None and actual.address == definition.location_id


def test_first_visit_does_not_sweep_big_switch_but_reaching_its_press_does():
    mw = setup_multiworld(KirbyAmWorld, steps=("generate_early", "create_regions"), options={"room_sanity": 0})
    world = mw.worlds[1]
    set_rules(world)
    visit = mw.get_location("Moonlight Mansion - First Visit", 1)
    switch = mw.get_location("Rainbow Route East - Big Switch", 1)
    event = mw.get_location("Activate Big Switch - Rainbow Route East", 1)
    hub = data.items[data.item_key_to_id["HUB_CONNECTION_RAINBOW_ROUTE_EAST"]].label

    assert event.address is None and event.item.code is None and event.locked
    assert event.parent_region is switch.parent_region
    assert switch.item is None and switch.address == 3960411

    # Isolate the two ordinary AP graph facts from the full game's access route.
    # A visit enters the summary; the exact switch compartment is a distinct edge.
    menu = mw.get_region("Menu", 1)
    menu.connect(visit.parent_region, "Isolated first visit")
    menu.connect(switch.parent_region, "Isolated switch room").access_rule = (
        lambda state: state.has("Test room route", 1)
    )
    old_rule = switch.access_rule
    switch.access_rule = lambda state: old_rule(state) and state.has("Test switch side", 1)
    for names, reached in [((), False), (("Test room route",), False),
                           (("Test room route", "Test switch side"), True)]:
        state = CollectionState(mw)
        for name in names:
            state.collect(world.create_event(name), prevent_sweep=True)
        assert visit.can_reach(state)
        assert switch.can_reach(state) is reached
        state.sweep_for_advancements()
        assert state.has(event.name, 1) is reached
        assert not state.has(hub, 1)


@pytest.mark.parametrize("defect,match", [
    ("duplicate", "multiple owners"), ("wrong_side", "owner .* differs"),
    ("missing", "without an owner"), ("duplicate_event", "Duplicate or misplaced"),
])
def test_canonical_owner_rejects_bad_catalog_without_first_wins(defect, match):
    catalog = deepcopy(data)
    key = "VITALITY_CHEST_CANDY_CONSTELLATION"
    right = catalog.regions[catalog.locations[key].parent_region]
    wrong = catalog.regions["REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_2__LOGIC__ENTRY_FROM_9_01"]
    if defect in {"wrong_side", "missing"}:
        right.locations.remove(key)
    if defect == "wrong_side":
        wrong.locations.append(key)
    if defect == "duplicate":
        right.locations.append(key)
    if defect == "duplicate_event":
        right.events.extend(catalog.regions["REGION_CANDY_CONSTELLATION/ROOM_9_HUB"].events)
    with pytest.raises(ValueError, match=match):
        validate_check_placement(catalog)


def test_goal_game_and_chalk_are_different_moonlight_compartments():
    goal_game = data.locations["GOAL_GAME_2_GOAL_2"]
    chalk = data.locations["MINOR_CHEST_SPRAY_PAINT_14"]
    assert goal_game.parent_region != chalk.parent_region
    assert goal_game.bit_index == 4 and chalk.source_rom_offset
    audit = load_json_data("goal_game_doors.json")
    room = next(row for row in audit["goals"] if row["location_key"] == goal_game.name)
    assert room["source_room"] == 148 and room["bit_index"] == 4


@pytest.mark.parametrize("room_sanity", [0, 1])
def test_chalk_compartment_counts_as_native_visit_without_other_compartment_access(room_sanity):
    mw = setup_multiworld(KirbyAmWorld, steps=("create_regions",), options={"room_sanity": room_sanity})
    room_key = "REGION_MOONLIGHT_MANSION/ROOM_2_GOAL_2"
    chalk_room = mw.get_region(f"{room_key}_UPPER_LEFT", 1)
    assert chalk_room.name == data.locations["MINOR_CHEST_SPRAY_PAINT_14"].parent_region
    menu = mw.get_region("Menu", 1)
    for exit_ in menu.exits:
        exit_.access_rule = lambda _: False
    for exit_ in chalk_room.exits:
        if exit_.connected_region.name != f"{room_key}__ROOM_CHECK":
            exit_.access_rule = lambda _: False
    menu.connect(chalk_room, "Isolated native arrival on Chalk side")
    state = CollectionState(mw)
    assert state.can_reach_region(chalk_room.name, 1)
    assert not state.can_reach_region(room_key, 1)
    from ..completion import ROOM_REGIONS

    assert (f"{room_key}__ROOM_CHECK",) in ROOM_REGIONS
    assert state.can_reach_region(f"{room_key}__ROOM_CHECK", 1)
    assert not state.can_reach_location(data.locations["GOAL_GAME_2_GOAL_2"].label, 1)
    visit = data.locations["ROOM_SANITY_2_GOAL_2"]
    if room_sanity:
        assert state.can_reach_location(visit.label, 1)
    else:
        assert visit.label not in {loc.name for loc in mw.get_locations(1)}


def test_full_placement_audit_matches_exact_native_sources_and_important_compartments():
    from ..tools.audit_check_placement import audit

    report = audit()
    assert len(report["locations"]) == 401
    assert len(report["addressless_region_events"]) == 21
    by_key = {row["key"]: row for row in report["locations"]}
    assert by_key["MAJOR_CHEST_WORLD_MAP"]["native_room"] == 805
    assert by_key["MINOR_CHEST_SPRAY_PAINT_14"]["native_object"] == "0x008BC114"
    assert by_key["VITALITY_CHEST_CANDY_CONSTELLATION"]["owner"].endswith("__ENTRY_FROM_9_09")
    assert by_key["MINOR_CHEST_SPRAY_PAINT_06"]["owner"].endswith("__ENTRY_FROM_9_01")
    assert by_key["MAJOR_CHEST_PEPPERMINT_PALACE"]["owner"].endswith("__LOWER_MAP")
    assert by_key["BOSS_DEFEAT_3"]["encounter_slot"] == 3
    assert by_key["GOAL_HIDDEN_AREA_BOSS"]["role"] == "legacy_goal_event"


def test_inactive_minor_chests_leave_other_checks_unchanged(monkeypatch):
    monkeypatch.setattr(KirbyAmWorld, "ENABLE_MINOR_CHESTS", False)
    mw = setup_multiworld(KirbyAmWorld, steps=("create_regions",), options={"room_sanity": 1})
    checks = {loc.key for loc in mw.get_locations(1) if loc.address is not None}
    assert checks == {key for key, loc in data.locations.items()
                      if loc.category not in {LocationCategory.GOAL, LocationCategory.MINOR_CHEST}}
    assert len(checks) == 330
