"""Exact Normal110 admission in the independent, unoptimized fixed-point oracle."""
from collections.abc import Callable, Iterable
from dataclasses import replace
import hashlib
from pathlib import Path

import pytest

from ..traversal import (
    Node, Placement, Position, Route, SourcePolicy, TraversalGraph, TraversalResult, reachable_positions,
)
from .test_traversal import policy
from .test_traversal_source_expansion import ALL_PERMISSIONS, POLICIES
from .traversal_reference import reachable_positions as reference_positions

SPIT = 'bomb_110_upper_normal_spit'
SPRAY = 'bomb_110_room9_underwater_normal_spray'
KNIGHT = '0x088B74CC'
Solver = Callable[[Iterable[Node], Iterable[Route], Iterable[Placement], Iterable[Position],
                   SourcePolicy, frozenset[str], bool, bool], TraversalResult]


def payload_graph() -> TraversalGraph:
    return TraversalGraph(
        (Node('launch', 110), Node('after', 110)),
        (Route('launch', 'after', SPIT, uses_object=KNIGHT, required_equipment=frozenset({'Normal'})),),
        (Placement('launch', 'SWORD_KNIGHT', requirements=frozenset({'payload-access'}), identity=KNIGHT),),
        (Position('launch'),), frozenset({'after'}))


def evaluate(graph: TraversalGraph, resolver: SourcePolicy, owned: frozenset[str],
             gating: bool, retries: bool, solver: Solver) -> TraversalResult:
    return solver(graph.nodes, graph.routes, graph.placements, graph.starts, resolver, owned, gating, retries)


def test_unoptimized_reference_search_body_stays_byte_identical() -> None:
    source = Path(__file__).with_name('traversal_reference.py').read_bytes()
    tail = source.split(b'    queue = deque(starts)\n', 1)[1]
    assert hashlib.sha256(tail).hexdigest() == '44711c286fe14c4b02ce9aa9e9a0daf2ac677f60fd43c410ea98bc3ae9400510'


@pytest.mark.parametrize('spec', POLICIES)
@pytest.mark.parametrize('gating,retries', [(False, False), (False, True), (True, False), (True, True)])
@pytest.mark.parametrize('has_payload_access,spent', [(False, False), (True, False), (True, True)])
def test_exact_normal_payload_consumption_and_source_access(
    spec: tuple[int, bool, list[str] | None, int], gating: bool, retries: bool,
    has_payload_access: bool, spent: bool,
) -> None:
    mode, statues, pool, weight = spec
    resolver: SourcePolicy = policy(mode, statues=statues, pool=pool, weight=weight)
    graph = payload_graph()
    if spent:
        graph = replace(graph, starts=(Position('launch', consumed=frozenset({KNIGHT})),))
    owned = ALL_PERMISSIONS | ({'payload-access'} if has_payload_access else set())
    expected = evaluate(graph, resolver, owned, gating, retries, reference_positions)
    assert evaluate(graph, resolver, owned, gating, retries, reachable_positions) == expected
    after = {p for p in expected.positions if p.node == 'after'}
    assert after == ({Position('after', 'Normal', consumed=frozenset({KNIGHT}))}
                     if has_payload_access and not spent else set())
    assert not expected.retry_assumptions


@pytest.mark.parametrize('mutation', [
    'missing_object', 'missing_placement', 'wrong_identity', 'absent_identity', 'wrong_species', 'renewable',
    'wrong_compartment', 'unrelated_capability', 'missing_target', 'medium', 'source_room', 'target_room',
    'equipment', 'mixed_equipment', 'opens', 'transition',
])
def test_payload_malformed_actions_rejected_by_both_solvers(mutation: str) -> None:
    graph = payload_graph()
    route, = graph.routes
    source, = graph.placements
    if mutation == 'missing_object':
        route = replace(route, uses_object=None)
    elif mutation == 'missing_placement':
        graph = replace(graph, placements=())
    elif mutation == 'wrong_identity':
        route = replace(route, uses_object='another-enemy')
        graph = replace(graph, placements=(replace(source, identity='another-enemy'),))
    elif mutation == 'absent_identity':
        graph = replace(graph, placements=(replace(source, identity=None),))
    elif mutation == 'missing_target':
        route = replace(route, target='unreviewed-target')
    elif mutation == 'wrong_species':
        graph = replace(graph, placements=(replace(source, source_key='WADDLE_DEE'),))
    elif mutation == 'renewable':
        graph = replace(graph, placements=(replace(source, renewable=True, retry_evidence='invented refresh'),))
    elif mutation == 'wrong_compartment':
        graph = replace(graph, placements=(replace(source, node='after'),))
    elif mutation == 'unrelated_capability':
        route = replace(route, capability='ordinary_block_hit')
    else:
        graph, route = mutate_action(graph, route, mutation)
    graph = replace(graph, routes=(route,))
    for solver in (reference_positions, reachable_positions):
        with pytest.raises(ValueError):
            evaluate(graph, SourcePolicy({'mode': 0}), ALL_PERMISSIONS | {'payload-access'}, True, True, solver)


def mutate_action(graph: TraversalGraph, route: Route, mutation: str) -> tuple[TraversalGraph, Route]:
    if mutation == 'medium':
        route = replace(route, water_state='swimming' if route.water_state == 'dry' else 'dry')
    elif mutation in ('source_room', 'target_room'):
        key = route.source if mutation == 'source_room' else route.target
        graph = replace(graph, nodes=tuple(replace(n, room=503) if n.key == key else n for n in graph.nodes))
    elif mutation == 'equipment':
        route = replace(route, required_equipment=None)
    elif mutation == 'mixed_equipment':
        route = replace(route, required_equipment=frozenset({'Normal', 'Sword'}))
    elif mutation == 'opens':
        route = replace(route, opens='invented-persistence')
    elif mutation == 'transition':
        route = replace(route, room_transition=True)
    else:
        raise AssertionError(mutation)
    return graph, route


@pytest.mark.parametrize('mutation', [
    'medium', 'source_room', 'target_room', 'equipment', 'mixed_equipment', 'opens', 'transition', 'ammunition',
])
def test_distinct_spray_does_not_broaden_object_or_action_contract(mutation: str) -> None:
    graph = payload_graph()
    route = replace(graph.routes[0], capability=SPRAY, uses_object=None, water_state='swimming')
    if mutation == 'ammunition':
        route = replace(route, uses_object=KNIGHT)
    else:
        graph, route = mutate_action(graph, route, mutation)
    graph = replace(graph, routes=(route,))
    for solver in (reference_positions, reachable_positions):
        with pytest.raises(ValueError):
            evaluate(graph, SourcePolicy({'mode': 0}), ALL_PERMISSIONS | {'payload-access'}, True, True, solver)
