"""Environmental clearance is a directed Normal sequence, not a metal ability."""

from copy import deepcopy
from dataclasses import replace
from typing import Any

import pytest

from ..enemy_ability_data import ABILITY_NAME_TO_ID
from ..traversal import (
    CAPABILITY_ABILITIES, Node, Position, Route, SourcePolicy, TraversalResult,
    compile_traversal_graph, reachable_positions,
)


NODES = (Node("right_approach", 102), Node("cleared_corridor", 102), Node("outside", 103))
PULL = Route("right_approach", "cleared_corridor", "heave_ho_pull")


def evaluate(route: Route = PULL, ability: str = "Normal") -> TraversalResult:
    return reachable_positions(NODES, (route,), (), (Position("right_approach", ability),),
                               SourcePolicy({"mode": 0}))


@pytest.mark.parametrize("ability", list(ABILITY_NAME_TO_ID))
def test_pulling_uses_normal_suction_not_a_copy_ability(ability: str) -> None:
    result = evaluate(ability=ability)
    assert result.reaches("cleared_corridor")
    assert {position.equipped for position in result.positions if position.node == "cleared_corridor"} == {"Normal"}
    # Carrying a metal-breaking ability does not silently preserve it through suction.
    assert CAPABILITY_ABILITIES["heave_ho_pull"] == {"Normal"}
    assert not CAPABILITY_ABILITIES["heave_ho_pull"] & CAPABILITY_ABILITIES["metal"]


def test_inaccessible_approach_cannot_be_replaced_by_ability_inventory() -> None:
    result = reachable_positions(NODES, (PULL,), (), (Position("outside"),),
                                 SourcePolicy({"mode": 0}),
                                 frozenset(f"{ability} Ability" for ability in ABILITY_NAME_TO_ID))
    assert not result.reaches("right_approach")
    assert not result.reaches("cleared_corridor")


def test_pulling_does_not_invent_a_reverse_route() -> None:
    result = reachable_positions(NODES, (PULL,), (), (Position("cleared_corridor"),),
                                 SourcePolicy({"mode": 0}))
    assert not result.reaches("right_approach")


@pytest.mark.parametrize("route,message", [
    (replace(PULL, water_state="swimming"), "dry Normal suction"),
    (replace(PULL, target="outside"), "local mechanism"),
    (replace(PULL, room_transition=True), "local mechanism"),
    (replace(PULL, opens="clear"), "persistent opens"),
    (replace(PULL, allowed_abilities=frozenset({"Hammer"})), "narrow"),
])
def test_unreviewed_mechanism_variants_fail_closed(route: Route, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        evaluate(route)


@pytest.fixture
def mechanism_graph() -> dict[str, Any]:
    return {
        "version": 1,
        "status": "reviewed",
        "nodes": [{"id": "right", "native_room": 102}, {"id": "left", "native_room": 102}],
        "routes": [{"from": "right", "to": "left", "capability": "heave_ho_pull",
                    "evidence": "Synthetic compiler fixture, not room acceptance",
                    "heave_ho_evidence": "Reviewed object identity, right-hand suction and disposal shaft"}],
        "starts": ["right"],
        "required_targets": ["left"],
    }


@pytest.mark.parametrize("evidence", [None, "", " ", True, 1])
def test_compiler_requires_mechanism_specific_evidence(mechanism_graph: dict[str, Any], evidence: Any) -> None:
    mechanism_graph["routes"][0]["heave_ho_evidence"] = evidence
    with pytest.raises(ValueError, match="object, approach and disposal"):
        compile_traversal_graph(mechanism_graph)


def test_compiler_preserves_local_normal_mechanism_without_source_or_unlock(mechanism_graph: dict[str, Any]) -> None:
    original = deepcopy(mechanism_graph)
    graph = compile_traversal_graph(mechanism_graph)
    assert graph.evaluate(SourcePolicy({"mode": 0}), frozenset(), True).reaches("left")
    assert not graph.placements
    assert not graph.routes[0].items
    assert mechanism_graph == original


def test_mechanism_evidence_cannot_certify_an_ordinary_metal_attack(mechanism_graph: dict[str, Any]) -> None:
    mechanism_graph["routes"][0]["capability"] = "metal"
    with pytest.raises(ValueError, match="local pulling mechanism"):
        compile_traversal_graph(mechanism_graph)


def test_olive_ocean_existing_mini_witness_does_not_require_reinforced_disposal() -> None:
    from ..traversal_data import room_traversal_graph
    graph = room_traversal_graph("mini_134_ocean_spray", "local")
    assert not any(route.capability in {"metal", "heave_ho_pull"} for route in graph.routes)
    assert all(route.opens is None for route in graph.routes)
    assert any(route.capability == "mini_corridor" and route.recover_dropped_ability for route in graph.routes)
    assert graph.evaluate(SourcePolicy({"mode": 0}), frozenset({"Mini Ability"}), True).reaches(
        "mini_134_ocean_spray:target")
    assert not graph.evaluate(SourcePolicy({"mode": 0}), frozenset(), True).reaches(
        "mini_134_ocean_spray:target")


def test_only_reviewed_radish_target_is_registered_not_every_environment_tile_room() -> None:
    from ..data import data
    from ..traversal_data import room_traversal_graph, room_traversal_targets
    from ..traversal_rules import extra_traversal_targets
    rows = room_traversal_targets("reinforced")
    assert [(row["id"], row["native_room"], row["location"]) for row in rows] == [
        ("reinforced_102_battle_notes", 102, "MINOR_CHEST_MUSIC_NOTE_04")]
    assert rows[0] in extra_traversal_targets()
    graph = room_traversal_graph(rows[0]["id"], "local")
    assert [route.capability for route in graph.routes] == [None, "heave_ho_pull", None]
    assert not graph.placements
    assert all(node.room == 102 for node in graph.nodes)
    assert not any(route.items or route.opens for route in graph.routes)
    owner = data.regions[rows[0]["region"]]
    assert owner.exit_requirements.get("REGION_RADISH_RUINS/ROOM_8_23") is None


@pytest.mark.parametrize("mode", [0, 1, 2])
@pytest.mark.parametrize("gating", [False, True])
def test_radish_environmental_target_needs_no_unlock_or_randomized_source(mode: int, gating: bool) -> None:
    from ..traversal_data import room_traversal_graph
    graph = room_traversal_graph("reinforced_102_battle_notes", "local")
    policy = SourcePolicy({"mode": mode, "allowed_abilities": ["Normal"],
                           "ability_randomization_no_ability_weight": 100})
    result = graph.evaluate(policy, frozenset(), gating)
    assert result.reaches("reinforced_102_battle_notes:target")
    assert not result.retry_assumptions


@pytest.mark.parametrize("mode", [0, 1, 2])
@pytest.mark.parametrize("gating", [0, 1])
def test_installed_radish_rule_needs_parent_access_but_no_ability_items(mode: int, gating: int) -> None:
    from BaseClasses import CollectionState
    from ..data import data
    from .test_mini_traversal import make_world
    world = make_world(mode, gating)  # type: ignore[no-untyped-call]
    state = CollectionState(world.multiworld)
    target = world.multiworld.get_location(data.locations["MINOR_CHEST_MUSIC_NOTE_04"].label, 1)
    assert target.access_rule(state)
    assert not target.can_reach(state)  # The local witness does not grant access to Radish Ruins.
    exit_ = world.multiworld.get_entrance("REGION_RADISH_RUINS/ROOM_8_22 -> REGION_RADISH_RUINS/ROOM_8_23", 1)
    assert exit_.access_rule(state)
