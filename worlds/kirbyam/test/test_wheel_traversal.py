"""The exact108 race uses obtainable equipment, never an unlock alone."""
from contextlib import ExitStack
from unittest.mock import patch

import pytest
from BaseClasses import CollectionState

from ..traversal import SourcePolicy
from ..wheel_traversal import (
    CENTRAL_REGION, HUB_SWITCH_LABELS, RACE_ENTRANCE, RESET_ASSUMPTION, wheel_graph,
)
from .test_mini_traversal import make_world


@pytest.mark.parametrize("mode", [0, 1, 2])
@pytest.mark.parametrize("statues", [0, 1])
@pytest.mark.parametrize("gating", [0, 1])
def test_all_mode_statue_fallback_uses_actual_assignment(mode, statues, gating):
    world = make_world(mode, gating, ability_randomization_statues=statues,
                       ability_randomization_no_ability_weight=100)
    policy = SourcePolicy(world._enemy_copy_ability_policy, bool(statues))
    graph = wheel_graph(True)
    items = frozenset({"Rainbow Route East - Hub Connection"})
    assert graph.evaluate(policy, items | {"Wheel Ability"}, gating,
                          allow_documented_retries=True).reaches("chest")
    assert graph.evaluate(policy, items, gating,
                          allow_documented_retries=True).reaches("chest") == (not gating)


def test_only_audited_return_resets_room_and_retains_wheel():
    graph = wheel_graph(False)
    resets = [route for route in graph.routes if route.resets_room_instance]
    assert len(resets) == 1
    rooms = {node.key: node.room for node in graph.nodes}
    assert (rooms[resets[0].source], rooms[resets[0].target]) == (110, 108)
    assert "unoccupied" in RESET_ASSUMPTION
    result = graph.evaluate(SourcePolicy({"mode": 0}), frozenset({"Wheel Ability"}), True)
    assert any(position.node == "chest" and position.equipped == "Wheel" for position in result.positions)


def test_970_requires_every_physical_switch_not_area_events_or_connection_items():
    world = make_world(2, True, ability_randomization_no_ability_weight=100)
    state = CollectionState(world.multiworld)
    for name in ("Wheel Ability", "Rainbow Route East - Hub Connection"):
        state.collect(world.create_item(name), prevent_sweep=True)
    target = world.multiworld.get_entrance(RACE_ENTRANCE, 1)
    switches = [world.multiworld.get_location(name, 1) for name in HUB_SWITCH_LABELS]
    with ExitStack() as stack:
        stack.enter_context(patch.object(
            state, "can_reach_region", side_effect=lambda name, player: name == CENTRAL_REGION,
        ))
        checks = [stack.enter_context(patch.object(location, "can_reach", return_value=True)) for location in switches]
        assert target.access_rule(state)
        for check in checks:
            check.return_value = False
            assert not target.access_rule(state)
            check.return_value = True
        state.remove(world.create_item("Wheel Ability"))
        assert not target.access_rule(state)


def test_normal_race_witnesses_are_not_wheel_gated():
    world = make_world(0, True)
    state = CollectionState(world.multiworld)
    assert not state.has("Wheel Ability", 1)
    # Candy16 Music Scores is a tested Normal route, unrelated to108's rule.
    from ..data import data
    location = world.multiworld.get_location(data.locations["MINOR_CHEST_MUSIC_NOTE_07"].label, 1)
    assert location.access_rule(state)


@pytest.mark.parametrize("mode", [0, 1, 2])
@pytest.mark.parametrize("statues", [0, 1])
@pytest.mark.parametrize("gating", [0, 1])
def test_wheel_and_mini_archive_accessibility(tmp_path, mode, statues, gating):
    from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive
    player = tmp_path / "player.yaml"
    player.write_text(
        "name: Traversal\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n"
        f"  ability_randomization_mode: {mode}\n  ability_randomization_statues: {statues}\n"
        f"  ability_gating: {gating}\n  ability_randomization_no_ability_weight: 100\n"
        "  room_sanity: 1\n", encoding="utf-8",
    )
    archive = generate_archive_from_fixture(player, tmp_path / "output", seed=1041 + mode * 4 + statues * 2 + gating)
    decoded = load_multidata_from_archive(archive)
    starts = decoded["precollected_items"][1]
    assert 3860108 in starts  # Stone remains.
    assert 3860104 not in starts and 3860123 not in starts
    pool = {entry[0] for entry in decoded["locations"][1].values()}
    assert (3860104 in pool) == bool(gating)
    assert (3860123 in pool) == bool(gating)


def test_all_indirect_source_regions_are_registered():
    from ..wheel_traversal import LOCAL_SOURCE_REGION
    world = make_world(0, True)
    entrance = world.multiworld.get_entrance(RACE_ENTRANCE, 1)
    expected = {world.multiworld.get_region(name, 1) for name in (LOCAL_SOURCE_REGION, CENTRAL_REGION)}
    expected.update(world.multiworld.get_location(name, 1).parent_region for name in HUB_SWITCH_LABELS)
    assert all(entrance in world.multiworld.indirect_connections.get(region, set()) for region in expected)
