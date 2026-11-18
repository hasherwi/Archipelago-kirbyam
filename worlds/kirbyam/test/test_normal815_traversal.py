"""Bind only the reviewed local815 recipe after independent room access."""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

import pytest

from ..traversal_data import _validate_target, room_traversal_graph, room_traversal_targets
from .test_traversal import policy

ROOT = Path(__file__).resolve().parents[1]
OWNER = 'REGION_OLIVE_OCEAN/ROOM_6_CHEST_1'
TARGET = 'normal_815_vitality'


@pytest.mark.parametrize('mode,pool,weight', [(0,None,0),(1,['Sleep'],0),(2,None,0),(2,None,100)])
@pytest.mark.parametrize('gating', [False, True])
def test_intrinsic_recipe_does_not_need_ability_permission_or_retry(mode, pool, weight, gating):
    graph = room_traversal_graph(TARGET, 'normal_arrival')
    result = graph.evaluate(policy(mode, pool=pool, weight=weight), frozenset(), gating)
    assert result.reaches(TARGET + ':chest')
    assert not graph.placements and not result.retry_assumptions
    assert all(p.equipped == 'Normal' and not p.consumed and not p.opened for p in result.positions)


@pytest.mark.parametrize('change', ['access', 'source', 'location', 'room'])
def test_binding_cannot_move_to_another_access_or_target(change):
    row = deepcopy(next(r for r in room_traversal_targets('block') if r['id'] == TARGET))
    graph = row['graphs']['normal_arrival']
    if change == 'access': graph['access']['region'] = 'REGION_OLIVE_OCEAN/ROOM_6_15'
    if change == 'source': graph['sources'] = [{'id': 'invented'}]
    if change == 'location': row['location'] = 'MINOR_CHEST_OLIVE_OCEAN_6_16'
    if change == 'room': graph['nodes'][0]['native_room'] = 553
    with pytest.raises(ValueError): _validate_target(row)


@pytest.mark.parametrize('change', [{'opens': 'gate'}, {'uses_object': '0x088CCCFC'},
                                    {'required_equipment': frozenset({'Cutter'})}])
def test_recipe_is_not_a_latch_consumed_block_or_copy_attack(change):
    graph = room_traversal_graph(TARGET, 'normal_arrival')
    graph = replace(graph, routes=(replace(graph.routes[0], **change),))
    with pytest.raises(ValueError): graph.evaluate(policy(0), frozenset(), False)


def test_arrival_binding_preserves_the_only_existing_ap_entrance_and_other_surfaces():
    rooms = json.loads((ROOT / 'data/regions/rooms.json').read_text())
    incoming = [(key, room['exits'][OWNER]) for key, room in rooms.items() if OWNER in room.get('exits', {})]
    assert incoming == [('REGION_OLIVE_OCEAN/ROOM_6_15', 'can_fly')]
    room = rooms[OWNER]
    assert room['exits'] == {'REGION_OLIVE_OCEAN/ROOM_6_16': {'any': ['can_break_block', 'can_swim']}}
    assert room['locations']['room_sanity']['location_id'] == 3961152


def test_current_native_variants_and_no_puff_control_preserve_resource_distinctions():
    evidence = json.loads((ROOT / 'dev-docs/normal815-current-acceptance.json').read_text())
    assert len(evidence['cases']) == 5
    assert evidence['comparison'] == {'identical_observations_through_frame': 3525,
                                      'omitted_input_bit': 2, 'input_start_frame': 3525}
    for row in evidence['cases']:
        assert row['minimum_hp'] == 1 and row['abilities'] == [0]
        assert row['helper_rooms'] == [[101, 101, 101]] and row['rooms'] == [551, 815]
        assert row['endpoint']['frame'] == 3945 and row['endpoint']['room'] == 815
        assert row['observed_human_intakes'] == 0
        assert row['block']['inventory_id'] == 'room:815/template:0x088CCCFC'
        assert row['block']['first']['x'] == 184 and row['block']['last']['x'] == 182.75
        assert row['client_messages'] == ([{'cmd': 'LocationChecks', 'locations': [3960301]}] if row['positive'] else [])
        assert row['vitality_bits'] == (2 if row['positive'] else 0)
        assert row['event_counter'] == int(row['positive'])
        for write in row['provenance']['runtime_writes']:
            assert write['frame'] == 1085 and not write['guard_failed']
