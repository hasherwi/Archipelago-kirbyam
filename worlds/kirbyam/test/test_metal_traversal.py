"""Ordinary-metal action witnesses reuse equipment and physical consumption.

Synthetic graphs test planner semantics, not native movement or room acceptance.
"""

from copy import deepcopy
from dataclasses import replace
from typing import Any

import pytest

from ..traversal import (
    CAPABILITY_ABILITIES, METAL_BREAKING_ABILITIES, Node, Placement, Position,
    Route, SourcePolicy, TraversalResult, compile_traversal_graph, reachable_positions,
)
from .test_traversal import policy


NODES = (Node("capture", 708), Node("ledge", 708), Node("beyond", 708), Node("outside", 707))
AMMO_ID = "one-grabbable-object"
AMMO = Placement("capture", "WADDLE_DEE", identity=AMMO_ID)
THROW = Route("capture", "beyond", "metal_throw", uses_object=AMMO.identity)


def throw_result(
    route: Route = THROW, sources: tuple[Placement, ...] = (AMMO,), ability: str = "Throw",
    consumed: frozenset[str] = frozenset(), owned: frozenset[str] = frozenset(),
    source_policy: SourcePolicy | None = None,
) -> TraversalResult:
    return reachable_positions(NODES, (route,), sources, (Position("capture", ability, consumed=consumed),),
                               source_policy or SourcePolicy({"mode": 0}), owned)


def test_eight_metal_breakers_distinguish_throw_from_direct_attacks() -> None:
    assert METAL_BREAKING_ABILITIES == {
        "Burning", "Hammer", "Stone", "Throw", "Missile", "UFO", "Smash", "Master"}
    assert CAPABILITY_ABILITIES["metal"] | CAPABILITY_ABILITIES["metal_throw"] == METAL_BREAKING_ABILITIES
    assert not CAPABILITY_ABILITIES["metal"] & CAPABILITY_ABILITIES["metal_throw"]
    assert not throw_result(replace(THROW, capability="metal", uses_object=None)).reaches("beyond")


def test_throw_consumes_object_without_inventing_movement_or_reverse_access() -> None:
    result = throw_result()
    assert Position("beyond", "Throw", consumed=frozenset({AMMO_ID})) in result.positions
    assert not result.reaches("ledge")
    reverse = reachable_positions(NODES, (THROW,), (AMMO,), (Position("beyond", "Throw"),), SourcePolicy({"mode": 0}))
    assert not reverse.reaches("capture")


def test_unlock_without_a_reachable_throw_source_is_not_equipment() -> None:
    assert not throw_result(ability="Normal", owned=frozenset({"Throw Ability"})).reaches("beyond")
    inaccessible_source = Placement("beyond", "PHAN_PHAN", identity="behind-metal")
    assert not throw_result(sources=(AMMO, inaccessible_source), ability="Normal",
                            owned=frozenset({"Throw Ability"})).reaches("beyond")


def test_swallowing_throw_source_and_throwing_same_object_are_mutually_exclusive() -> None:
    resolver = policy(1, pool=["Throw"])  # type: ignore[no-untyped-call]
    assert resolver.grant("WADDLE_DEE", lambda _: True).guaranteed == {"Throw"}
    assert not throw_result(ability="Normal", owned=frozenset({"Throw Ability"}),
                            source_policy=resolver).reaches("beyond")
    spare = replace(AMMO, identity="separate-copy-source")
    result = throw_result(sources=(AMMO, spare), ability="Normal", owned=frozenset({"Throw Ability"}),
                          source_policy=resolver)
    assert result.reaches("beyond")
    assert all({AMMO.identity, spare.identity} <= position.consumed
               for position in result.positions if position.node == "beyond")


def test_consumed_or_unavailable_ammunition_cannot_be_reused() -> None:
    assert not throw_result(consumed=frozenset({AMMO_ID})).reaches("beyond")
    locked = replace(AMMO, requirements=frozenset({"Defeat target miniboss"}))
    assert not throw_result(sources=(locked,)).reaches("beyond")
    assert throw_result(sources=(locked,), owned=locked.requirements).reaches("beyond")


def test_throw_cannot_start_from_swimming() -> None:
    assert not throw_result(replace(THROW, water_state="swimming")).reaches("beyond")


@pytest.mark.parametrize("route,sources,message", [
    (replace(THROW, uses_object=None), (AMMO,), "physical target"),
    (THROW, (), "physical source"),
    (THROW, (replace(AMMO, node="ledge"),), "launch compartment"),
    (THROW, (replace(AMMO, renewable=True),), "one-use physical"),
    (replace(THROW, opens="metal"), (AMMO,), "persistent opens"),
    (replace(THROW, target="outside"), (AMMO,), "native room"),
    (replace(THROW, room_transition=True), (AMMO,), "native room"),
])
def test_throw_rejects_unreviewed_object_transport(route: Route, sources: tuple[Placement, ...], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        throw_result(route, sources)


@pytest.fixture
def metal_graph() -> dict[str, Any]:
    return {
        "version": 1, "status": "reviewed",
        "nodes": [{"id": "before", "native_room": 205}, {"id": "after", "native_room": 205}],
        "routes": [{"from": "before", "to": "after", "capability": "metal", "allowed_abilities": ["Hammer"],
                    "evidence": "Synthetic schema fixture, not a source-backed room witness",
                    "metal_evidence": {"Hammer": "Isolated floor test; this synthetic graph proves no source path"}}],
        "starts": ["before"], "required_targets": ["after"],
    }


@pytest.mark.parametrize("allowed", [None, [], ["Hammer", "Hammer"], [True], [{}], "Hammer"])
def test_compiled_metal_requires_explicit_unique_providers(metal_graph: dict[str, Any], allowed: Any) -> None:
    metal_graph["routes"][0]["allowed_abilities"] = allowed
    with pytest.raises(ValueError, match="explicit unique"):
        compile_traversal_graph(metal_graph)


@pytest.mark.parametrize("evidence", [None, "Hammer works", {}, {"Hammer": ""}, {"Hammer": True},
                                      {"Stone": "unmatched"}, {"Hammer": "proof", "Stone": "extra"}])
def test_each_metal_provider_requires_its_own_move_and_geometry_record(
    metal_graph: dict[str, Any], evidence: Any,
) -> None:
    metal_graph["routes"][0]["metal_evidence"] = evidence
    with pytest.raises(ValueError, match="every allowed ability"):
        compile_traversal_graph(metal_graph)


def test_compilation_does_not_turn_isolated_attack_evidence_into_equipment(metal_graph: dict[str, Any]) -> None:
    original = deepcopy(metal_graph)
    graph = compile_traversal_graph(metal_graph)
    assert not graph.evaluate(SourcePolicy({"mode": 0}), frozenset({"Hammer Ability"}), True).reaches("after")
    assert metal_graph == original


def test_throw_cannot_be_smuggled_into_direct_metal_provider_set(metal_graph: dict[str, Any]) -> None:
    metal_graph["routes"][0].update(allowed_abilities=["Throw"], metal_evidence={"Throw": "Claim without ammunition"})
    with pytest.raises(ValueError, match="narrow"):
        compile_traversal_graph(metal_graph)


def test_metal_evidence_cannot_certify_an_environmental_action(metal_graph: dict[str, Any]) -> None:
    metal_graph["routes"][0]["capability"] = "peg"
    with pytest.raises(ValueError, match="ordinary-metal capability"):
        compile_traversal_graph(metal_graph)


@pytest.mark.parametrize("evidence", [None, "", " ", True, 1])
def test_compiled_throw_requires_capture_trajectory_evidence(metal_graph: dict[str, Any], evidence: Any) -> None:
    metal_graph["routes"][0].update(capability="metal_throw", allowed_abilities=["Throw"], uses_object="ammo",
                                    throw_evidence=evidence, metal_evidence={"Throw": "Synthetic contact proof"})
    with pytest.raises(ValueError, match="capture/throw evidence"):
        compile_traversal_graph(metal_graph)


def test_compiled_throw_preserves_physical_identity_and_source_policy(metal_graph: dict[str, Any]) -> None:
    metal_graph["sources"] = [{"id": "ammo", "node": "before", "source_key": "WADDLE_DEE",
                               "acquisition_evidence": "Synthetic shared capture and swallowing position"}]
    metal_graph["routes"][0].update(capability="metal_throw", allowed_abilities=["Throw"], uses_object="ammo",
                                    throw_evidence="Synthetic capture/throw from one fixed position",
                                    metal_evidence={"Throw": "Synthetic trajectory to exact metal barrier"})
    graph = compile_traversal_graph(metal_graph)
    assert graph.routes[0].uses_object == graph.placements[0].identity == "ammo"
    resolver = policy(1, pool=["Throw"])  # type: ignore[no-untyped-call]
    assert not graph.evaluate(resolver, frozenset({"Throw Ability"}), True).reaches("after")


def test_metal_target_kind_uses_shared_catalog_and_installer(metal_graph: dict[str, Any]) -> None:
    from ..traversal_data import load_room_traversal
    owner = "REGION_PEPPERMINT_PALACE/ROOM_7_07"
    target = {"id": "test-metal", "kind": "metal", "native_room": 205,
              "exit": "REGION_PEPPERMINT_PALACE/ROOM_7_CHEST", "graphs": {"local": metal_graph}}
    rows, _, _ = load_room_traversal({owner: {"traversal": {"version": 1, "targets": [target]}}})
    assert rows[0]["kind"] == "metal"
    assert rows[0]["region"] == owner


def test_direct_metal_sequence_must_not_skip_a_room_transition() -> None:
    with pytest.raises(ValueError, match="native room"):
        throw_result(Route("capture", "outside", "metal"), ability="Hammer")


def test_throw_cannot_use_a_statue_as_ammunition() -> None:
    with pytest.raises(ValueError, match="not a statue"):
        throw_result(sources=(replace(AMMO, source_key="STATUE:3538FC"),))


def test_partial_metal_applicability_uses_actual_source_output_not_ability_inventory() -> None:
    from ..traversal_rules import target_applies
    target = {"requires_guaranteed_source": {"source_key": "MASTER_HAND", "ability": "Smash"}}
    assert target_applies(target, SourcePolicy({"mode": 0}))
    assert target_applies(target, policy(1, pool=["Smash"]))  # type: ignore[no-untyped-call]
    assert not target_applies(target, policy(1, pool=["Burning"]))  # type: ignore[no-untyped-call]
    assert not target_applies(target, policy(2, pool=["Smash", "Burning"]))  # type: ignore[no-untyped-call]
    assert not target_applies(target, policy(2, pool=["Smash"], weight=1))  # type: ignore[no-untyped-call]
    assert target_applies(target, policy(2, pool=["Burning"], minibosses=False))  # type: ignore[no-untyped-call]


@pytest.mark.parametrize("condition", [
    None, {}, {"source_key": "UNKNOWN", "ability": "Smash"},
    {"source_key": "MASTER_HAND", "ability": "Normal"},
    {"source_key": "MASTER_HAND", "ability": "Unknown"},
    {"source_key": ["MASTER_HAND"], "ability": "Smash"},
    {"source_key": "MASTER_HAND", "ability": ["Smash"]},
    {"source_key": "MASTER_HAND", "ability": "Smash", "guaranteed": True},
])
def test_source_applicability_schema_rejects_unreviewable_conditions(condition: Any) -> None:
    from ..traversal_data import _validate_source_condition
    with pytest.raises(ValueError, match="guaranteed-source"):
        _validate_source_condition(condition)


@pytest.mark.parametrize("source,ability", [("MR_FROSTY", "Ice"), ("MASTER_HAND", "Smash")])
def test_source_applicability_schema_is_reusable_not_per_boss_code(source: str, ability: str) -> None:
    from ..traversal_data import _validate_source_condition
    _validate_source_condition({"source_key": source, "ability": ability})


@pytest.mark.parametrize("source_key", ["GLUNK", "JACK", "SQUISHY"])
def test_throw_rejects_explicitly_ineligible_enemy_registry_entries(source_key: str) -> None:
    from ..enemy_ability_data import ABILITY_SOURCES
    source = next(source for source in ABILITY_SOURCES if source.key == source_key)
    assert not source.can_be_swallowed
    with pytest.raises(ValueError, match="ineligible source"):
        throw_result(sources=(replace(AMMO, source_key=source_key),))


@pytest.mark.parametrize("reload", [False, True])
def test_direct_metal_opening_is_lost_on_exit_and_cannot_bootstrap_reentry(reload: bool) -> None:
    attack = Route("capture", "beyond", "metal", opens="local-f5", allowed_abilities=frozenset({"Hammer"}))
    routes = (attack, Route("beyond", "outside", resets_room_instance=reload), Route("outside", "capture"))
    resolver = SourcePolicy({"mode": 0})
    result = reachable_positions(NODES, routes, (), (Position("capture", "Hammer"),), resolver)
    assert Position("beyond", "Hammer", opened=frozenset({"local-f5"})) in result.positions
    outside_normal = [position for position in result.positions if position.node == "outside"
                      and position.equipped == "Normal"]
    assert outside_normal
    assert all(not position.opened for position in result.positions if position.node == "outside")
    reentry = reachable_positions(NODES, routes, (), outside_normal, resolver)
    assert reentry.reaches("capture")
    assert not reentry.reaches("beyond")


def test_direct_metal_destruction_credit_is_only_local_to_the_current_room_instance() -> None:
    attack = Route("capture", "beyond", "metal", opens="local-f5", allowed_abilities=frozenset({"Hammer"}))
    routes = (attack, Route("beyond", "capture"))
    result = reachable_positions(NODES, routes, (), (Position("capture", "Hammer"),), SourcePolicy({"mode": 0}))
    cleared_normal = Position("capture", "Normal", opened=frozenset({"local-f5"}))
    assert cleared_normal in result.positions
    same_visit = reachable_positions(NODES, (attack,), (), (cleared_normal,), SourcePolicy({"mode": 0}))
    assert same_visit.reaches("beyond")
