"""Exact host-only Normal Green branch checks."""
from dataclasses import replace
from typing import Any

import pytest

from ..traversal_data import room_traversal_graph, graph_items
from .test_traversal import policy

TARGET = 'bomb_138_green'
CAPABILITY = 'bomb_138_green_normal_lower_slide'


@pytest.mark.parametrize('mode,pool,weight', [
    (0, None, 0), (1, ['Beam'], 0), (2, ['Spark', 'Beam'], 0),
    (2, ['Spark'], 50), (2, ['Spark'], 100), (2, None, 0),
])
@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('keys', [False, True])
def test_normal_suffix_has_no_source_or_permission_dependency(
    mode: int, pool: list[str] | None, weight: int, gating: bool, keys: bool,
) -> None:
    graph = room_traversal_graph(TARGET, 'upper_left_normal_slide', keys)
    assert graph.access_region == 'REGION_RAINBOW_ROUTE/ROOM_1_27_UPPER_LEFT'
    assert not graph.placements and not graph_items(graph)
    assert graph.required_guaranteed_source is None
    assert [r.resets_room_instance for r in graph.routes] == [True, False, False]
    result = graph.evaluate(policy(mode, pool=pool, weight=weight), frozenset(), gating)
    assert all(result.reaches(n) for n in graph.required_targets)
    assert not result.retry_assumptions
    assert all(not p.opened and not p.consumed for p in result.positions)


@pytest.mark.parametrize('mutation', [
    'capability', 'equipment', 'mixed', 'source', 'target', 'opens', 'items',
    'transition', 'recover', 'room', 'medium',
])
def test_normal_slide_cannot_be_generalized(mutation: str) -> None:
    graph = room_traversal_graph(TARGET, 'upper_left_normal_slide')
    route = graph.routes[-1]
    changes: dict[str, dict[str, Any]] = {
        'capability': {'capability': 'bomb_138_green'},
        'equipment': {'required_equipment': None},
        'mixed': {'required_equipment': frozenset({'Normal', 'Spark'})},
        'source': {'source': graph.routes[0].target},
        'target': {'target': graph.routes[0].target},
        'opens': {'opens': 'room-cleared'},
        'items': {'items': frozenset({'Spark Ability'})},
        'transition': {'room_transition': True},
        'recover': {'recover_dropped_ability': True},
        'medium': {'water_state': 'swimming'},
    }
    if mutation == 'room':
        graph = replace(graph, nodes=tuple(
            replace(node, room=999) if node.key == route.target else node for node in graph.nodes))
    else:
        graph = replace(graph, routes=graph.routes[:-1] + (replace(route, **changes[mutation]),))
    if mutation == 'capability':
        assert not graph.evaluate(policy(0), frozenset(), True).reaches(next(iter(graph.required_targets)))
    else:
        with pytest.raises(ValueError):
            graph.evaluate(policy(0), frozenset(), True)
