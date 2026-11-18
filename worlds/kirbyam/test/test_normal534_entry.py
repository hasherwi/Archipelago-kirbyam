"""Bounded Normal prefix does not borrow the later Sir Kibble grant."""
from copy import deepcopy
import json
from pathlib import Path
import pytest
from ..traversal_data import room_traversal_graph, room_traversal_targets, _validate_target
from .test_traversal import policy

TARGET = 'normal_534_mustard_entry'
ACCESS = 'REGION_RAINBOW_ROUTE/ROOM_1_HUB_4'
ROOT = Path(__file__).resolve().parents[1]

@pytest.mark.parametrize('mode,pool,weight', [(0,None,0),(1,['Sleep'],0),(2,None,0),(2,None,100)])
@pytest.mark.parametrize('gating', [False,True])
def test_prefix_needs_no_owned_or_obtainable_copy(mode,pool,weight,gating):
    graph = room_traversal_graph(TARGET,'normal_hub4_entry')
    result = graph.evaluate(policy(mode,pool=pool,weight=weight),frozenset(),gating)
    assert all(result.reaches(n) for n in graph.required_targets)
    assert len(graph.placements)==2 and not result.retry_assumptions
    ends=[p for p in result.positions if p.node in graph.required_targets]
    assert ends and all(p.equipped == 'Normal' and p.consumed >= {'0x088B59B4','0x088B596C'} for p in ends)

@pytest.mark.parametrize('change', ['access','equipment','endpoint','source'])
def test_prefix_cannot_be_generalized(change):
    row = deepcopy(next(r for r in room_traversal_targets('block') if r['id']==TARGET))
    graph = row['graphs']['normal_hub4_entry']
    if change=='access': graph['access']['region']='REGION_RAINBOW_ROUTE/ROOM_1_34'
    if change=='equipment': graph['routes'][1]['required_equipment']=['Cutter']
    if change=='endpoint': row['exit']='REGION_MUSTARD_MOUNTAIN/ROOM_4_15'
    if change=='source': graph['sources']=[{'id':'invented'}]
    with pytest.raises(ValueError): _validate_target(row)

def test_prefix_packet_provenance_and_bounds():
    prefixes = json.loads((ROOT/'dev-docs/normal534-entry-prefix.json').read_text())['cases']
    original = json.loads((ROOT/'dev-docs/mustard-map-kibble-acceptance.json').read_text())
    cases = {c['case']:c for c in original['positive']+original['controls']}
    assert len(prefixes)==len(cases)==71
    for row in prefixes:
        case=cases[row['case']]
        assert row['private_evidence_sha256']==case['private_evidence_sha256']
        assert row['rooms']==[590,534,310]
        assert row['endpoint']=={'frame':2520,'room':310,'x':56.0,'y':136.99609375,'hp':case['hp'],'ability':0}
        if case.get('cutter_acquired_frame') is not None:
            assert case['cutter_acquired_frame']>2520

def test_installed_entrance_requires_independent_access(monkeypatch):
    from BaseClasses import CollectionState
    from .. import rules
    from .test_mini_traversal import make_world
    world=make_world(0,1,area_keys=0)
    entrance=world.multiworld.get_entrance('REGION_RAINBOW_ROUTE/ROOM_1_34 -> REGION_MUSTARD_MOUNTAIN/ROOM_4_CHEST',1)
    state=CollectionState(world.multiworld)
    monkeypatch.setattr(rules,'_allow_pending_ability_gate',lambda *a:pytest.fail('pending fallback'))
    monkeypatch.setattr(state,'can_reach_region',lambda name,player:False)
    assert not entrance.access_rule(state)
    monkeypatch.setattr(state,'can_reach_region',lambda name,player:name==ACCESS)
    assert entrance.access_rule(state)

def test_destination_key_and_other_room34_exits_remain(monkeypatch):
    from BaseClasses import CollectionState
    from ..area_keys import AREA_KEY_LABEL_BY_AREA_ID
    from .test_mini_traversal import make_world
    world=make_world(0,1,area_keys=1)
    state=CollectionState(world.multiworld)
    monkeypatch.setattr(state,'can_reach_region',lambda name,player:name==ACCESS)
    entrance=world.multiworld.get_entrance('REGION_RAINBOW_ROUTE/ROOM_1_34 -> REGION_MUSTARD_MOUNTAIN/ROOM_4_CHEST',1)
    assert not entrance.access_rule(state)
    state.collect(world.create_item(AREA_KEY_LABEL_BY_AREA_ID[4]),prevent_sweep=True)
    assert entrance.access_rule(state)
    rooms=json.loads((ROOT/'data/regions/rooms.json').read_text())
    exits=rooms['REGION_RAINBOW_ROUTE/ROOM_1_34']['exits']
    assert all(value=='can_break_block' for key,value in exits.items()
               if key not in {'REGION_MUSTARD_MOUNTAIN/ROOM_4_CHEST','REGION_MUSTARD_MOUNTAIN/ROOM_4_15'})

@pytest.mark.parametrize('identity', ['0x088B59B4','0x088B596C'])
def test_consumed_payload_after_arrival_cannot_be_reused(identity):
    from dataclasses import replace
    from ..traversal import Position
    graph=room_traversal_graph(TARGET,'normal_hub4_entry')
    graph=replace(graph, starts=(Position(TARGET+':rainbow34', consumed=frozenset({identity})),))
    result=graph.evaluate(policy(0),frozenset(),False)
    assert not any(result.reaches(n) for n in graph.required_targets)

@pytest.mark.parametrize('index', [1,2])
def test_payload_action_cannot_be_replaced_with_permission(index):
    from dataclasses import replace
    graph=room_traversal_graph(TARGET,'normal_hub4_entry')
    routes=list(graph.routes)
    routes[index]=replace(routes[index],uses_object=None)
    graph=replace(graph,routes=tuple(routes))
    with pytest.raises(ValueError): graph.evaluate(policy(0),frozenset({'Tornado Ability'}),False)

def test_native_payload_intake_and_omission_controls():
    evidence=json.loads((ROOT/'dev-docs/normal534-payload-acceptance.json').read_text())
    assert len(evidence['cases'])==6
    for row in evidence['cases']:
        assert row['abilities']==[0] and row['helper_rooms']==[[101,101,101]]
        assert all(w['frame']==1085 and not w['guard_failed'] for w in row['provenance']['runtime_writes'])
        if row['positive']:
            assert row['minimum_hp']==1 and row['endpoint']['room']==310
            assert [p['template'] for p in row['payloads']]==['0x88b59b4','0x88b596c']
            assert [p['intake']['frame'] for p in row['payloads']]==[1282,1390]
            assert all(p['intake']['contact']=='0x2020ee0' and p['intake']['state']=='0x809c48d' for p in row['payloads'])
        else:
            assert row['minimum_hp']==0 and row['endpoint']['room']==534

@pytest.mark.parametrize('mode,pool,weight', [(0,None,0),(1,['Sleep'],0),(2,None,0),(2,None,100)])
@pytest.mark.parametrize('gating', [False,True])
def test_room15_prefix_reuses_finite_payloads_without_copy_grant(mode,pool,weight,gating):
    graph=room_traversal_graph('normal_534_room15_entry','normal_hub4_entry')
    result=graph.evaluate(policy(mode,pool=pool,weight=weight),frozenset(),gating)
    ends=[p for p in result.positions if p.node in graph.required_targets]
    assert ends and all(p.equipped=='Normal' and p.consumed >= {'0x088B59B4','0x088B596C'} for p in ends)
    assert {n.room for n in graph.nodes if n.key in graph.required_targets}=={533}
    assert not result.retry_assumptions

def test_room15_native_prefix_and_destination_key(monkeypatch):
    from BaseClasses import CollectionState
    from ..area_keys import AREA_KEY_LABEL_BY_AREA_ID
    from .test_mini_traversal import make_world
    evidence=json.loads((ROOT/'dev-docs/normal534-room15-acceptance.json').read_text())
    assert len(evidence['cases'])==6
    for row in evidence['cases']:
        assert row['abilities']==[0] and row['helper_rooms']==[[101,101,101]]
        if row['positive']:
            assert row['minimum_hp']==1 and row['endpoint']=={'frame':2705,'room':533,'x':616.0,'y':264.99609375,'hp':1,'ability':0}
            assert [p['intake']['frame'] for p in row['payloads']]==[1282,1390]
        else:
            assert row['minimum_hp']==0 and row['endpoint']['room']==590
    world=make_world(0,1,area_keys=1)
    state=CollectionState(world.multiworld)
    monkeypatch.setattr(state,'can_reach_region',lambda name,player:name==ACCESS)
    entrance=world.multiworld.get_entrance('REGION_RAINBOW_ROUTE/ROOM_1_34 -> REGION_MUSTARD_MOUNTAIN/ROOM_4_15',1)
    assert not entrance.access_rule(state)
    state.collect(world.create_item(AREA_KEY_LABEL_BY_AREA_ID[4]),prevent_sweep=True)
    assert entrance.access_rule(state)
