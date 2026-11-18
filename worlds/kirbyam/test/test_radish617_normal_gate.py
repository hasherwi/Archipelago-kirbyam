"""Bounded Normal map route; native artifacts are scalar contracts, not replays."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from ..data import load_json_data
from ..traversal_data import room_traversal_graph, graph_items, has_graph_access
from .test_traversal import policy

OWNER = 'REGION_RADISH_RUINS/ROOM_8_CHEST_2'
TARGET = 'bomb_617_radish_map'


@pytest.mark.parametrize('mode,pool,weight', [
    (0, None, 0), (1, ['Beam'], 0), (2, ['Spark', 'Beam'], 0),
    (2, ['Spark'], 50), (2, ['Spark'], 100), (2, None, 0),
])
@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('keys', [False, True])
def test_normal_route_needs_no_permission_or_random_grant(mode, pool, weight, gating, keys):
    graph = room_traversal_graph(TARGET, 'normal_entry', keys)
    assert graph.access_region == OWNER
    assert not graph.placements and not graph_items(graph)
    assert graph.required_guaranteed_source is None
    result = graph.evaluate(policy(mode, pool=pool, weight=weight), frozenset(), gating)
    assert all(result.reaches(n) for n in graph.required_targets)
    assert not result.retry_assumptions
    assert all(not p.opened and not p.consumed for p in result.positions)


def test_location_rule_keeps_independent_access():
    room = load_json_data('regions/rooms.json')[OWNER]
    assert room['locations']['MAJOR_CHEST_RADISH_RUINS'] is None
    target, = room['traversal']['targets']
    assert target['location'] == 'MAJOR_CHEST_RADISH_RUINS'
    graph = room_traversal_graph(TARGET, 'normal_entry')
    world = SimpleNamespace(player=1)
    for accessible in (False, True):
        state = SimpleNamespace(can_reach_region=lambda name, player: accessible and name == OWNER and player == 1)
        assert has_graph_access(world, state, graph) == accessible


def test_native_positive_and_omission_contracts():
    e = json.loads((Path(__file__).resolve().parents[1] / 'dev-docs/radish617-normal-acceptance.json').read_text())
    assert {(r['hp'], r['gated']) for r in e['positive']} == {(1, False), (1, True), (6, False), (6, True)}
    for r in e['positive']:
        assert r['minimum_hp'] == r['hp']
        assert r['abilities'] == [0] and r['helper_rooms'] == [[101, 101, 101]]
        assert r['final']['ability_unlocks'] == 0 and r['final']['room'] == 617
        assert r['final_flags'] == dict(native_chest73=True, major_check8=True, native_map8=False, upper_bomb=0, lower_bomb=0)
        assert r['captured_client_messages'] == [{'cmd': 'LocationChecks', 'locations': [3960207]}]
    assert {r['omission'] for r in e['controls']} == {'upper_puff', 'lower_slide'}
    for r in e['controls']:
        assert not r['final_flags']['native_chest73'] and not r['final_flags']['major_check8']
        assert not r['captured_client_messages']
    for r in e['positive'] + e['controls']:
        assert not r['runtime_writes']
        assert len(r['private_evidence_sha256']) == len(r['runtime_sha256']) == 64


@pytest.mark.parametrize('changes', [
    {'required_equipment': None}, {'required_equipment': frozenset({'Normal', 'Cutter'})},
    {'opens': 'room-cleared'}, {'room_transition': True},
    {'items': frozenset({'Cutter Ability'})}, {'recover_dropped_ability': True},
    {'water_state': 'swimming'}, {'target': 'bomb_617_radish_map:arrival'},
])
def test_bounded_normal_sequence_cannot_be_generalized(changes):
    from dataclasses import replace
    graph = room_traversal_graph(TARGET, 'normal_entry')
    graph = replace(graph, routes=(replace(graph.routes[0], **changes),))
    with pytest.raises(ValueError):
        graph.evaluate(policy(0), frozenset(), True)
