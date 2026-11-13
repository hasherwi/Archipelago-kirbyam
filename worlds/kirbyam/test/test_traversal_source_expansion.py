"""Exact source-expansion equivalence, not new native traversal acceptance."""

from dataclasses import replace
from itertools import product
import random

import pytest

from ..enemy_ability_data import ABILITY_NAME_TO_ID
from ..traversal import Node, Placement, Position, Route, SourcePolicy, TraversalGraph, reachable_positions
from ..traversal_data import graph_items, room_traversal_graph, room_traversal_targets
from .test_traversal import policy
from .traversal_reference import reachable_positions as reference_positions


ALL_PERMISSIONS = frozenset(f"{name} Ability" for name in ABILITY_NAME_TO_ID)
POLICIES = (
    (0, False, None, 0),
    (1, True, ["Stone", "Mini", "Crash", "Throw", "Ice", "Wheel"], 0),
    (2, False, ["Hammer", "Stone"], 0),
    (2, True, ["Hammer", "Stone"], 0),
    (2, True, ["Hammer", "Stone"], 50),
    (2, True, ["Hammer", "Stone"], 100),
    (2, True, ["Burning", "Mini", "Crash", "Throw", "Ice", "Wheel"], 0),
    (2, True, ["Burning", "Mini", "Crash", "Throw", "Ice", "Wheel"], 100),
)


@pytest.fixture(scope="module", params=POLICIES)
def resolver(request: pytest.FixtureRequest) -> SourcePolicy:
    mode, statues, pool, weight = request.param
    return policy(mode, statues=statues, pool=pool, weight=weight)  # type: ignore[no-untyped-call, no-any-return]


def assert_equivalent(graph: TraversalGraph, resolver: SourcePolicy, owned: frozenset[str],
                      gating: bool, retries: bool) -> None:
    expected = reference_positions(graph.nodes, graph.routes, graph.placements, graph.starts,
                                   resolver, owned, gating, retries)
    actual = reachable_positions(graph.nodes, graph.routes, graph.placements, graph.starts,
                                 resolver, owned, gating, retries)
    # Compare every equipped/uncertain outcome, opened and consumed identity,
    # and the complete retry qualification, not just target reachability.
    assert actual == expected


@pytest.mark.parametrize("gating,retries", tuple(product((False, True), repeat=2)))
def test_exhaustive_local_source_phases(resolver: SourcePolicy, gating: bool, retries: bool) -> None:
    equipment: tuple[str | frozenset[str], ...] = (
        "Normal", "Mini", "Stone", frozenset({"Normal", "Hammer", "Stone"}))
    starts = tuple(Position("source", ability, opened, consumed)
                   for ability, opened, consumed in product(
                       equipment, (frozenset(), frozenset({"gate"})),
                       (frozenset(), frozenset({"physical-source"}))))
    for source_key, renewable, locked, permitted in product(
            ("ROCKY", "STATUE:353900"), (False, True), (False, True), (False, True)):
        source = Placement("source", source_key, frozenset({"source-key"}) if locked else frozenset(),
                           "Synthetic safe retouch" if renewable else None, "physical-source", renewable)
        graph = TraversalGraph((Node("source", 1),), (), (source,), starts, frozenset({"source"}))
        owned = ALL_PERMISSIONS | {"source-key"} if permitted else frozenset()
        assert_equivalent(graph, resolver, owned, gating, retries)
        # Repeat with changed permissions and reversed starts: no result or phase
        # state may survive an evaluation or depend on the first held ability.
        assert_equivalent(replace(graph, starts=tuple(reversed(starts))), resolver,
                          ALL_PERMISSIONS - owned, gating, retries)


def generated_graph(seed: int) -> tuple[TraversalGraph, frozenset[str]]:
    """Small finite graphs with phase revisits, finite ammo and room boundaries."""
    rng = random.Random(seed)
    nodes = (Node("a", 1), Node("b", 1), Node("c", 2))
    sources = (
        Placement("a", "WADDLE_DEE", identity="ammo"),
        Placement("a", rng.choice(("ROCKY", "MINNY", "STATUE:353900")),
                  frozenset({"source-key"}) if rng.choice((False, True)) else frozenset(),
                  "Synthetic safe retouch" if seed & 1 else None, "provider", bool(seed & 1)),
        Placement("b", rng.choice(("WHEELIE", "STATUE:353902")), identity="second-provider"),
    )
    preserves, resets = ((False, False), (True, False), (False, True))[seed % 3]
    routes = (
        Route("a", "b", "peg", "gate"),
        Route("b", "a", required_equipment=frozenset({"Normal", "Stone"})),
        Route("a", "b", "metal_throw", uses_object="ammo"),
        Route("a", "b", "frozen_enemy_hit", uses_object="ammo"),
        Route("a", "b", "fuse"),  # Crash consumption must remain per Position.
        Route("a", "b", "mini_corridor", recover_dropped_ability=True),
        Route("a", "b", "underwater_block_hit", water_state="swimming"),
        Route("b", "c", items=frozenset({"route-key"}),
              preserves_room_instance=preserves, resets_room_instance=resets),
        Route("c", "a", preserves_room_instance=preserves, resets_room_instance=resets),
    )
    abilities: tuple[str | frozenset[str], ...] = (
        "Normal", "Mini", "Crash", "Throw", "Ice", "Stone", frozenset({"Stone", "Hammer"}))
    starts = tuple(Position(rng.choice(("a", "b", "c")), rng.choice(abilities),
                            frozenset({"gate"}) if rng.choice((False, True)) else frozenset(),
                            frozenset({"ammo"}) if rng.choice((False, True)) else frozenset())
                   for _ in range(3))
    owned = frozenset(name for name in sorted(ALL_PERMISSIONS | {"source-key", "route-key"})
                      if rng.choice((False, True)))
    return TraversalGraph(nodes, routes, sources, starts, frozenset({"b", "c"})), owned


@pytest.mark.parametrize("gating,retries", tuple(product((False, True), repeat=2)))
def test_generated_paths_match_reference(resolver: SourcePolicy, gating: bool, retries: bool) -> None:
    for seed in range(32):
        graph, owned = generated_graph(seed)
        assert_equivalent(graph, resolver, owned, gating, retries)


def catalog_graphs() -> tuple[tuple[str, str], ...]:
    return tuple((row["id"], witness)
                 for kind in ("mini", "peg", "wheel", "fuse", "rope", "block", "switch", "reinforced", "metal")
                 for row in room_traversal_targets(kind) for witness in row["graphs"])


@pytest.mark.parametrize("target,witness", catalog_graphs())
def test_reviewed_graphs_match_reference(target: str, witness: str, resolver: SourcePolicy) -> None:
    for area_keys, gating, retries in product((False, True), repeat=3):
        graph = room_traversal_graph(target, witness, area_keys)
        assert_equivalent(graph, resolver, graph_items(graph) | ALL_PERMISSIONS, gating, retries)


@pytest.mark.parametrize("retries", [False, True])
def test_full_live_pool_707_matches_reference(retries: bool) -> None:
    resolver = policy(2, statues=True)  # type: ignore[no-untyped-call]
    graph = room_traversal_graph("metal_707_to_712", "central_statues", True)
    owned = graph_items(graph) | ALL_PERMISSIONS
    assert_equivalent(graph, resolver, owned, True, retries)
    result = graph.evaluate(resolver, owned, True, allow_documented_retries=retries)
    assert len(result.positions) == (452 if retries else 36)
    assert result.reaches("metal_707:712_door") is retries
    assert bool(result.retry_assumptions) is retries


def test_source_phase_preserves_opened_and_consumed_identities() -> None:
    source = Placement("source", "WHEELIE", identity="finite-wheelie")
    starts = tuple(Position("source", "Normal", opened, consumed)
                   for consumed, opened in product(
                       (frozenset({"finite-wheelie"}), frozenset()),
                       (frozenset(), frozenset({"gate"}))))
    graph = TraversalGraph((Node("source", 1),), (), (source,), starts, frozenset({"source"}))
    resolver = SourcePolicy({"mode": 0})
    assert_equivalent(graph, resolver, ALL_PERMISSIONS, True, False)
    result = graph.evaluate(resolver, ALL_PERMISSIONS, True)
    for opened in (frozenset(), frozenset({"gate"})):
        assert Position("source", "Wheel", opened, frozenset({"finite-wheelie"})) in result.positions
    spent_only = replace(graph, starts=starts[:2]).evaluate(resolver, ALL_PERMISSIONS, True)
    assert all(position.equipped == "Normal" for position in spent_only.positions)
