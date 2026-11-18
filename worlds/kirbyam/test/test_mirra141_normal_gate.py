"""Bounded top-compartment Normal Mirra route; native artifacts are scalar contracts, not replays."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from ..traversal_data import room_traversal_graph, graph_items, has_graph_access
from .test_traversal import policy

OWNER = 'REGION_RAINBOW_ROUTE/ROOM_1_41__LOGIC__TOP_MUSTARD'
TARGET = 'mirra_141_top_mustard'


@pytest.mark.parametrize('mode,pool,weight', [
    (0, None, 0), (1, ['Beam'], 0), (2, ['Spark', 'Beam'], 0),
    (2, ['Spark'], 50), (2, ['Spark'], 100), (2, None, 0),
])
@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('keys', [False, True])
def test_normal_route_needs_no_permission_or_random_grant(mode, pool, weight, gating, keys):
    graph = room_traversal_graph(TARGET, 'normal_top_entry', keys)
    assert graph.access_region == OWNER
    assert not graph.placements and not graph_items(graph)
    assert graph.required_guaranteed_source is None
    result = graph.evaluate(policy(mode, pool=pool, weight=weight), frozenset(), gating)
    assert all(result.reaches(n) for n in graph.required_targets)
    assert not result.retry_assumptions
    assert all(not p.opened and not p.consumed for p in result.positions)


@pytest.mark.parametrize('changes', [
    {'required_equipment': None}, {'required_equipment': frozenset({'Normal', 'Cutter'})},
    {'opens': 'room-cleared'}, {'room_transition': True},
    {'items': frozenset({'Cutter Ability'})}, {'recover_dropped_ability': True},
    {'water_state': 'swimming'}, {'target': 'mirra_141_top_mustard:arrival'},
])
def test_bounded_normal_sequence_cannot_be_generalized(changes):
    from dataclasses import replace
    graph = room_traversal_graph(TARGET, 'normal_top_entry')
    graph = replace(graph, routes=(replace(graph.routes[0], **changes),))
    with pytest.raises(ValueError):
        graph.evaluate(policy(0), frozenset(), True)


def test_native_manifest_requires_actual_clearance_and_transition():
    record = json.loads((Path(__file__).resolve().parents[1] / 'dev-docs/mirra141-normal-acceptance.json').read_text())
    assert {r['case'] for r in record['positive']} == {'vanilla', '500-gated', 'shuffled', 'live-unowned'}
    for row in record['positive'] + record['controls']:
        assert row['minimum_hp'] == 1 and row['abilities'] == [0]
        assert row['initial']['room'] == 141 and row['initial']['x'] == 536
        assert row['initial']['ability_unlocks'] == row['final']['ability_unlocks'] == 0
        assert all(w['frame'] == 1085 and not w['guard_failed'] for w in row['runtime_writes'])
        assert len(row['private_evidence_sha256']) == len(row['runtime_sha256']) == 64
    for row in record['positive']:
        assert row['first_room545_frame'] and row['final']['room'] == 545
        assert any(x['mirra'] and x['mirra']['hp'] == 0 for x in row['mirra_landmarks'])
    control, = record['controls']
    assert control['final']['room'] == 141 and control['first_room545_frame'] is None
    assert all(x['mirra']['hp'] == 2 for x in control['mirra_landmarks'])


def test_top_access_is_independent():
    graph = room_traversal_graph(TARGET, 'normal_top_entry')
    world = SimpleNamespace(player=1)
    for accessible in (False, True):
        state = SimpleNamespace(can_reach_region=lambda name, player: accessible and name == OWNER and player == 1)
        assert has_graph_access(world, state, graph) == accessible


@pytest.mark.parametrize('keys', [False, True])
def test_installed_rule_preserves_destination_key(monkeypatch, keys):
    from BaseClasses import CollectionState
    from .. import rules
    from .test_mini_traversal import make_world
    world = make_world(0, 1, area_keys=int(keys))
    entrance = world.multiworld.get_entrance(OWNER + ' -> REGION_MUSTARD_MOUNTAIN/ROOM_4_07', 1)
    state = CollectionState(world.multiworld)
    monkeypatch.setattr(state, 'can_reach_region', lambda name, player: name == OWNER)
    monkeypatch.setattr(rules, '_allow_pending_ability_gate', lambda *a: pytest.fail('pending fallback'))
    assert entrance.access_rule(state) is (not keys)
    if keys:
        from ..rules import AREA_KEY_LABEL_BY_AREA_ID
        state.collect(world.create_item(AREA_KEY_LABEL_BY_AREA_ID[4]), prevent_sweep=True)
        assert entrance.access_rule(state)


@pytest.mark.parametrize('field,value', [('region', OWNER.replace('TOP_MUSTARD', 'EAST_MOONLIGHT')), ('exit', 'REGION_MOONLIGHT_MANSION/ROOM_2_16'), ('native_room', 117)])
def test_capability_cannot_be_reassigned_to_another_mirra(field, value):
    from copy import deepcopy
    from ..traversal_data import _validate_target, room_traversal_targets
    row = deepcopy(next(r for r in room_traversal_targets('block') if r['id'] == TARGET))
    row[field] = value
    with pytest.raises(ValueError, match='top Mustard exit'):
        _validate_target(row)
