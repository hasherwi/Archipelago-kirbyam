"""Real world wiring and archive generation for the reviewed Mini corridors."""

from argparse import Namespace

import pytest
from BaseClasses import CollectionState, MultiWorld

from .. import KirbyAmWorld
from ..enemy_ability_data import STARTING_COPY_ABILITIES, starting_copy_abilities
from ..mini_traversal import mini_routes
from ..traversal import SourcePolicy
from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive


def make_world(mode, gating, **extra_options):
    multiworld = MultiWorld(1)
    multiworld.game[1] = KirbyAmWorld.game
    multiworld.player_name = {1: "Mini traversal"}
    multiworld.set_seed(773)
    args = Namespace()
    overrides = {"ability_randomization_mode": mode, "ability_gating": gating, **extra_options}
    for name, option in KirbyAmWorld.options_dataclass.type_hints.items():
        setattr(args, name, {1: option.from_any(overrides.get(name, option.default))})
    multiworld.set_options(args)
    world = multiworld.worlds[1]
    multiworld.state = CollectionState(multiworld)
    world.generate_early()
    world.create_regions()
    world.set_rules()
    return world


@pytest.mark.parametrize("mode", [0, 1, 2])
@pytest.mark.parametrize("gating", [0, 1])
def test_all_reviewed_branches_and_bypasses(mode, gating):
    world = make_world(mode, gating)
    state = CollectionState(world.multiworld)
    assert not state.has("Mini Ability", 1)
    assert state.has("Stone Ability", 1) and not state.has("Wheel Ability", 1)
    for row, graph in mini_routes():
        if row["exit"]:
            target = world.multiworld.get_entrance(f"{row['region']} -> {row['exit']}", 1)
        else:
            from ..data import data
            target = world.multiworld.get_location(data.locations[row["location"]].label, 1)
        assert target.access_rule(state) == (not gating), row["id"]
        state.collect(world.create_item("Mini Ability"), prevent_sweep=True)
        assert target.access_rule(state), row["id"]
        state.remove(world.create_item("Mini Ability"))
        # No room-wide gate: normal route remains independently available.
        result = graph.evaluate(SourcePolicy(world._enemy_copy_ability_policy), frozenset(), True)
        assert result.reaches(row["id"] + ":bypass")
        assert not result.reaches(row["id"] + ":target")


def test_only_minny_option_removed():
    options = KirbyAmWorld.options_dataclass.type_hints
    assert "ability_randomization_minny" not in options
    assert {"ability_randomization_mode", "ability_randomization_statues", "ability_gating",
            "ability_randomization_minibosses", "ability_randomization_boss_spawns"} <= options.keys()


def test_mini_and_wheel_removed_in_all_modes_without_changing_stone():
    assert starting_copy_abilities(0) == starting_copy_abilities(1)
    assert set(starting_copy_abilities(0)) == set(STARTING_COPY_ABILITIES) - {"Mini", "Wheel"}
    assert starting_copy_abilities(2) == starting_copy_abilities(0)


@pytest.mark.parametrize("mode,gating", [(0, 1), (1, 1), (1, 0), (2, 1)])
def test_full_generation_accessibility_and_slot_contract(tmp_path, mode, gating):
    player = tmp_path / "player.yaml"
    player.write_text(
        "name: Mini\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n"
        f"  ability_randomization_mode: {mode}\n  ability_gating: {gating}\n"
        "  ability_randomization_minny: 1\n",  # Old YAML must not re-enable source randomization.
        encoding="utf-8",
    )
    archive = generate_archive_from_fixture(player, tmp_path / "out", seed=773)
    decoded = load_multidata_from_archive(archive)
    slot = decoded["slot_data"][1]
    assert "ability_randomization_minny" not in slot
    assert slot["enemy_copy_ability_policy"]["ability_randomization_minny"] is False
    assert (3860123 in decoded["precollected_items"][1]) is False
    assert 3860108 in decoded["precollected_items"][1]  # Stone is never removed.
    assert (3860123 in [item[0] for item in decoded["locations"][1].values()]) == bool(gating)


@pytest.mark.parametrize("mode", [0, 1, 2])
@pytest.mark.parametrize("gating", [False, True])
@pytest.mark.parametrize("right_entry", [False, True])
@pytest.mark.parametrize("room_sanity", [False, True])
def test_mustard_5_arrivals_preserve_normal_chest_alternative(mode, gating, right_entry, room_sanity):
    from ..data import LocationCategory, data

    world = make_world(mode, gating, room_sanity=room_sanity)
    mw = world.multiworld
    base = "REGION_MUSTARD_MOUNTAIN/ROOM_4_05"
    right = base + "__LOGIC__RIGHT_ENTRY"
    lower = "REGION_MUSTARD_MOUNTAIN/ROOM_4_06"
    upper = "REGION_MUSTARD_MOUNTAIN/ROOM_4_09"
    left_region, right_region = (mw.get_region(name, 1) for name in (base, right))
    # Isolate the two native arrivals. A trip through the rest of the world must
    # not supply the independent right-side entry in the left-only negative case.
    for region in (left_region, right_region):
        for entrance in region.entrances:
            if entrance.parent_region.name not in (base, right):
                entrance.access_rule = lambda state: False
    menu = mw.get_region("Menu", 1)
    for exit_ in menu.exits:
        exit_.access_rule = lambda state: False
    menu.connect(right_region if right_entry else left_region)
    state = CollectionState(mw)
    for name in world.item_name_to_id:
        if name != "Mini Ability":
            state.collect(world.create_item(name), prevent_sweep=True)
    chest = mw.get_location(data.locations["MINOR_CHEST_MUSTARD_MOUNTAIN_4_05"].label, 1)
    assert chest.parent_region is right_region
    assert chest.can_reach(state) == (right_entry or not gating)
    for region in (left_region, right_region):
        if region.can_reach(state):
            assert mw.get_entrance(f"{region.name} -> {upper}", 1).can_reach(state)
            assert mw.get_entrance(f"{region.name} -> {lower}", 1).can_reach(state) == (not gating)
    room_checks = [data.locations[key] for key in data.regions[base + "__ROOM_CHECK"].locations
                   if data.locations[key].category == LocationCategory.ROOM_SANITY]
    assert len(room_checks) == 1
    if room_sanity:
        assert mw.get_location(room_checks[0].label, 1).can_reach(state)
    state.collect(world.create_item("Mini Ability"), prevent_sweep=True)
    assert chest.can_reach(state)
    assert all(mw.get_entrance(f"{name} -> {lower}", 1).can_reach(state) for name in (base, right))


def test_mustard_5_native_entries_and_local_sources_are_not_merged():
    from ..data import data
    from ..traversal_data import room_traversal_graph

    base = "REGION_MUSTARD_MOUNTAIN/ROOM_4_05"
    right = base + "__LOGIC__RIGHT_ENTRY"
    assert base in data.regions["REGION_MUSTARD_MOUNTAIN/ROOM_4_04"].exits
    assert right in data.regions["REGION_MUSTARD_MOUNTAIN/ROOM_4_08"].exits
    assert base not in data.regions["REGION_MUSTARD_MOUNTAIN/ROOM_4_08"].exits
    for target, source in (("mini_321_lower", "minny_088c4db4"),
                           ("mini_321_cross_to_right", "minny_088c4db4"),
                           ("mini_321_right_lower", "minny_088c4dd8")):
        assert {p.identity for p in room_traversal_graph(target, "local").placements} == {source}


def test_mustard_cross_side_metadata_records_sufficient_recovery_witness():
    from ..traversal_data import room_traversal_graph, room_traversal_targets

    target = "mini_321_cross_to_right"
    row = next(row for row in room_traversal_targets("mini") if row["id"] == target)
    payload = row["graphs"]["local"]
    route = next(route for route in payload["routes"] if route.get("capability") == "mini_corridor")
    assert route["recover_dropped_ability"] is True
    assert "y425->393->361->313" in route["evidence"]
    assert "raw23/type0xA3" in route["evidence"]
    assert "inhale-and-spit the Flamer rightward while Normal" in route["evidence"]
    graph = room_traversal_graph(target, "local")
    recovery, = [route for route in graph.routes if route.recover_dropped_ability]
    assert (recovery.source, recovery.target) == (target + ":source", target + ":target")
    assert not recovery.room_transition and not recovery.resets_room_instance
    source, = graph.placements
    assert (source.identity, source.source_key) == ("minny_088c4db4", "MINNY")
    assert not source.renewable and source.retry_evidence is None
    assert all(position.equipped == "Normal" for position in graph.starts)


@pytest.mark.parametrize("gating", [False, True])
def test_mustard_cross_side_recovery_still_needs_local_minny_and_permission(gating):
    from dataclasses import replace
    from .test_traversal import policy
    from ..traversal_data import room_traversal_graph

    target = "mini_321_cross_to_right:target"
    graph = room_traversal_graph("mini_321_cross_to_right", "local")
    resolver = policy(2, minny=False, weight=100)
    owned = frozenset({"Mini Ability"})
    assert graph.evaluate(resolver, owned, gating).reaches(target)
    assert graph.evaluate(resolver, frozenset(), gating).reaches(target) is (not gating)
    assert not replace(graph, placements=()).evaluate(resolver, owned, gating).reaches(target)
    # The cleared Flamer is not the initial Mini source or a manufactured star.
    source, = graph.placements
    ordinary_source = replace(source, source_key="FLAMER")
    assert not replace(graph, placements=(ordinary_source,)).evaluate(resolver, owned, gating).reaches(target)


@pytest.mark.parametrize("recovery", ["absent", "wrong_ability", "uncertain", "can_fail"])
def test_mustard_cross_side_requires_supported_guaranteed_recovery(monkeypatch, recovery):
    from ..traversal import Grant
    from ..traversal_data import room_traversal_graph
    from .test_traversal import policy

    graph = room_traversal_graph("mini_321_cross_to_right", "local")
    resolver = policy(2, minny=False, weight=100)
    outcomes = {
        "absent": Grant(frozenset()),
        "wrong_ability": Grant(frozenset({"Stone"})),
        "uncertain": Grant(frozenset({"Mini", "Stone"}), randomized=True),
        "can_fail": Grant(frozenset({"Mini"}), can_fail=True),
    }
    monkeypatch.setattr(resolver, "dropped_star_grant", lambda *args: outcomes[recovery])
    result = graph.evaluate(resolver, frozenset({"Mini Ability"}), True, allow_documented_retries=True)
    assert not result.reaches("mini_321_cross_to_right:target")
    assert result.reaches("mini_321_cross_to_right:bypass")


def test_installed_mustard_cross_side_recovery_does_not_gate_ordinary_upper_exit():
    from unittest.mock import patch
    from ..traversal import Grant

    world = make_world(2, True, ability_randomization_no_ability_weight=100)
    state = CollectionState(world.multiworld)
    state.collect(world.create_item("Mini Ability"), prevent_sweep=True)
    base = "REGION_MUSTARD_MOUNTAIN/ROOM_4_05"
    cross = world.multiworld.get_entrance(base + " -> " + base + "__LOGIC__RIGHT_ENTRY", 1)
    upper = world.multiworld.get_entrance(base + " -> REGION_MUSTARD_MOUNTAIN/ROOM_4_09", 1)
    assert cross.access_rule(state)
    with patch.object(SourcePolicy, "dropped_star_grant", return_value=Grant(frozenset())):
        assert not cross.access_rule(state)
        assert upper.access_rule(state)
