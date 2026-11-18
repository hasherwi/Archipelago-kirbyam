"""Independent right-side access and source-free Normal811 clearance."""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from ..traversal_data import room_traversal_graph,has_graph_access,room_traversal_targets,_validate_target
from .test_traversal import policy
TARGET='mirra_811_olive'
ACCESS='REGION_OLIVE_OCEAN/ROOM_6_11'
ROOT=Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('mode,pool,weight',[(0,None,0),(1,['Beam'],0),(2,None,0),(2,None,100)])
@pytest.mark.parametrize('gating',[False,True])
def test_normal_right_route_needs_no_random_grant(mode,pool,weight,gating):
    graph=room_traversal_graph(TARGET,'normal_right_entry')
    assert not graph.placements
    result=graph.evaluate(policy(mode,pool=pool,weight=weight),frozenset(),gating)
    assert all(result.reaches(n) for n in graph.required_targets)
    assert all(p.equipped=='Normal' and not p.consumed for p in result.positions)
    assert not result.retry_assumptions

@pytest.mark.parametrize('change',[{'required_equipment':None},{'water_state':'swimming'},{'opens':'opened'},{'room_transition':True}])
def test_dry_puff_cannot_be_generalized(change):
    graph=room_traversal_graph(TARGET,'normal_right_entry')
    graph=replace(graph,routes=(replace(graph.routes[0],**change),))
    with pytest.raises(ValueError):graph.evaluate(policy(0),frozenset(),False)

def test_right_access_not_western_room_membership():
    graph=room_traversal_graph(TARGET,'normal_right_entry')
    assert graph.access_region==ACCESS
    for allowed in (False,True):
        state=SimpleNamespace(can_reach_region=lambda name,player:allowed and name==ACCESS)
        assert has_graph_access(SimpleNamespace(player=1),state,graph)==allowed
    rows=json.loads((ROOT/'dev-docs/native-room-wikirby-map.json').read_text())['rooms']
    assert ACCESS in next(row['ap_keys'] for row in rows if row['native_id']==829)
    target=deepcopy(next(row for row in room_traversal_targets('block') if row['id']==TARGET))
    target['graphs']['normal_right_entry']['access']['region']='REGION_OLIVE_OCEAN/ROOM_6_10'
    with pytest.raises(ValueError):_validate_target(target)

def test_native_join_and_failed_puff():
    record=json.loads((ROOT/'dev-docs/mirra811-normal-acceptance.json').read_text())
    assert len(record['positive'])==4 and len(record['controls'])==1
    for row in record['positive']+record['controls']:
        assert row['minimum_hp']==1 and row['abilities']==[0]
        assert row['initial']['room']==829 and row['joined_arrival']['room']==811
    for row in record['positive']:
        assert [r['room'] for r in row['room_changes']]==[829,811,551]
        assert any(r['object'] and r['object']['hp']==0 for r in row['objects']['0x88cc730'])
    for row in record['controls']:
        assert row['final']['room']==811
        assert all(r['object']['hp']>0 for r in row['objects']['0x88cc730'] if r['object'])

def test_installed_rule_does_not_call_pending_ability_gate(monkeypatch):
    from BaseClasses import CollectionState
    from .. import rules
    from .test_mini_traversal import make_world
    world=make_world(0,1,area_keys=0)
    entrance=world.multiworld.get_entrance('REGION_OLIVE_OCEAN/ROOM_6_10 -> REGION_OLIVE_OCEAN/ROOM_6_15',1)
    state=CollectionState(world.multiworld)
    monkeypatch.setattr(rules,'_allow_pending_ability_gate',lambda *a:pytest.fail('pending fallback'))
    monkeypatch.setattr(state,'can_reach_region',lambda name,player:False)
    assert not entrance.access_rule(state)
    monkeypatch.setattr(state,'can_reach_region',lambda name,player:name==ACCESS)
    assert entrance.access_rule(state)
