"""Native192 entry, finite mouth payloads and bounded Normal117 clearance."""
from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from ..traversal_data import room_traversal_graph, has_graph_access
from .test_traversal import policy
TARGET='mirra_117_carrot'
ACCESS='REGION_RAINBOW_ROUTE/ROOM_1_HUB_3'
PAYLOADS=frozenset({'0x088B9904','0x088B9874'})

@pytest.mark.parametrize('mode,pool,weight', [(0,None,0),(1,['Beam'],0),(2,['Spark','Beam'],0),(2,None,100)])
@pytest.mark.parametrize('gating',[False,True])
def test_normal_route_consumes_physical_payloads_without_copy_permission(mode,pool,weight,gating):
    graph=room_traversal_graph(TARGET,'normal_upper_entry')
    result=graph.evaluate(policy(mode,pool=pool,weight=weight),frozenset(),gating)
    assert all(result.reaches(n) for n in graph.required_targets)
    ends=[p for p in result.positions if p.node in graph.required_targets]
    assert ends and all(p.consumed >= PAYLOADS and p.equipped=='Normal' for p in ends)
    assert not result.retry_assumptions

@pytest.mark.parametrize('spent',sorted(PAYLOADS))
def test_spent_payload_cannot_be_manufactured(spent):
    graph=room_traversal_graph(TARGET,'normal_upper_entry')
    graph=replace(graph,starts=tuple(replace(p,consumed=frozenset({spent})) for p in graph.starts))
    assert not graph.evaluate(policy(0),frozenset(),False).reaches(next(iter(graph.required_targets)))

@pytest.mark.parametrize('change',[{'required_equipment':None},{'room_transition':True},{'opens':'opened'},{'uses_object':None}])
def test_finite_action_cannot_be_generalized(change):
    graph=room_traversal_graph(TARGET,'normal_upper_entry')
    graph=replace(graph,routes=(replace(graph.routes[0],**change),)+graph.routes[1:])
    with pytest.raises(ValueError):graph.evaluate(policy(0),frozenset(),False)

def test_access_is_independent_upper_room():
    graph=room_traversal_graph(TARGET,'normal_upper_entry')
    assert graph.access_region==ACCESS
    for allowed in (False,True):
        state=SimpleNamespace(can_reach_region=lambda name,player:allowed and name==ACCESS)
        assert has_graph_access(SimpleNamespace(player=1),state,graph)==allowed

def test_native_positive_control_and_deaths():
    record=json.loads((Path(__file__).resolve().parents[1]/'dev-docs/mirra117-normal-acceptance.json').read_text())
    assert len(record['positive'])==4 and len(record['controls'])==1 and len(record['failures'])==2
    for row in record['positive']:
        assert row['minimum_hp']==1 and row['abilities']==[0] and row['final']['room']==120
        assert [r['room'] for r in row['room_changes']]==[192,117,120]
        for address in ('0x88b9904','0x88b9874'):
            assert any(r['object'] and r['object']['hp']==0 and r['object']['state']=='0x809c48d' for r in row['objects'][address])
        assert any(r['object'] and r['object']['hp']==0 for r in row['objects']['0x88b9808'])
    for row in record['controls']:
        assert row['minimum_hp']==1 and row['final']['room']==117
        assert all(r['object']['hp']>0 for r in row['objects']['0x88b9808'] if r['object'])
    assert all(r['minimum_hp']==0 for r in record['failures'])

@pytest.mark.parametrize('keys',[False,True])
def test_installed_rule_preserves_key_and_needs_upper_access(monkeypatch,keys):
    from BaseClasses import CollectionState
    from .. import rules
    from .test_mini_traversal import make_world
    world=make_world(0,1,area_keys=int(keys))
    entrance=world.multiworld.get_entrance('REGION_RAINBOW_ROUTE/ROOM_1_24 -> REGION_CARROT_CASTLE/ROOM_5_02',1)
    state=CollectionState(world.multiworld)
    monkeypatch.setattr(rules,'_allow_pending_ability_gate',lambda *a:pytest.fail('pending fallback'))
    monkeypatch.setattr(state,'can_reach_region',lambda name,player:False)
    assert not entrance.access_rule(state)
    monkeypatch.setattr(state,'can_reach_region',lambda name,player:name==ACCESS)
    assert entrance.access_rule(state) is (not keys)
    if keys:
        state.collect(world.create_item(rules.AREA_KEY_LABEL_BY_AREA_ID[5]),prevent_sweep=True)
        assert entrance.access_rule(state)

@pytest.mark.parametrize('mutation',['access','inventory','identity','node'])
def test_original_payload_and_entry_contract_cannot_move(mutation):
    from copy import deepcopy
    from ..traversal_data import _validate_target,room_traversal_targets
    row=deepcopy(next(r for r in room_traversal_targets('block') if r['id']==TARGET))
    graph=row['graphs']['normal_upper_entry']
    if mutation=='access':graph['access']['region']='REGION_RAINBOW_ROUTE/ROOM_1_24'
    else:
        key={'inventory':'inventory_id','identity':'id','node':'node'}[mutation]
        graph['sources'][0][key]='other'
    with pytest.raises(ValueError):_validate_target(row)


def test_native_entry_region_join_is_hub3():
    rows=json.loads((Path(__file__).resolve().parents[1]/'dev-docs/native-room-wikirby-map.json').read_text())['rooms']
    assert ACCESS in next(row['ap_keys'] for row in rows if row['native_id']==192)
