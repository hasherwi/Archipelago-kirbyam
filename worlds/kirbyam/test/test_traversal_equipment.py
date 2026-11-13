"""Carry guards constrain raw equipment without granting attacks or equipment."""

from dataclasses import replace

import pytest

from ..traversal import Node, Position, Route, SourcePolicy, compile_traversal_graph, reachable_positions


def evaluate(equipped, required, *, water_state='dry', opened=frozenset()):
    return reachable_positions(
        (Node('a', 730), Node('b', 730)),
        (Route('a', 'b', required_equipment=required, water_state=water_state),), (),
        (Position('a', equipped, opened),), SourcePolicy({'mode': 0}), frozenset({'UFO Ability'}), False,
    )


@pytest.mark.parametrize('water_state', ['dry', 'swimming'])
@pytest.mark.parametrize('equipped,passes', [
    ('Normal', False), ('UFO', True), ('Spark', False),
    (frozenset({'UFO', 'Spark'}), False), (frozenset({'UFO'}), True), (frozenset(), False),
])
def test_every_equipment_outcome_must_qualify_without_water_attack_substitution(water_state, equipped, passes):
    assert evaluate(equipped, frozenset({'UFO'}), water_state=water_state).reaches('b') is passes


def test_normal_guard_requires_drop_without_recovery_or_inventory_equipment():
    result = evaluate('UFO', frozenset({'Normal'}), water_state='swimming')
    assert {p.equipped for p in result.positions if p.node == 'b'} == {'Normal'}
    assert not evaluate('Normal', frozenset({'UFO'})).reaches('b')


@pytest.mark.parametrize('required', [frozenset(), frozenset({'Unknown'}), 'UFO', ['UFO'], True])
def test_direct_kernel_rejects_malformed_equipment(required):
    with pytest.raises(ValueError, match='Required equipment'):
        evaluate('UFO', required)


@pytest.mark.parametrize('required', [None, [], ['UFO', 'UFO'], ['Wait'], ['Unknown'], 'UFO', True, [1], [['UFO']]])
def test_compiler_rejects_malformed_equipment(required):
    payload = {
        'version': 1, 'status': 'reviewed', 'starts': ['a'], 'required_targets': ['b'],
        'nodes': [{'id': 'a', 'native_room': 730}, {'id': 'b', 'native_room': 730}],
        'routes': [{'from': 'a', 'to': 'b', 'required_equipment': required, 'evidence': 'Test carry evidence'}],
    }
    with pytest.raises(ValueError, match='Required equipment'):
        compile_traversal_graph(payload)


def test_opened_attack_does_not_bypass_independent_equipment_guard():
    route = Route('a', 'b', 'peg', opens='opened', required_equipment=frozenset({'UFO'}))
    nodes = (Node('a', 730), Node('b', 730))
    starts = (Position('a', 'Normal', frozenset({'opened'})),)
    assert not reachable_positions(nodes, (route,), (), starts, SourcePolicy({'mode': 0})).reaches('b')
    assert reachable_positions(nodes, (replace(route, required_equipment=None),), (), starts,
                               SourcePolicy({'mode': 0})).reaches('b')
