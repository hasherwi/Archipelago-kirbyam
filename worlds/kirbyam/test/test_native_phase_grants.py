"""Native attack phases are alternatives, not convenient finite source grants."""
import json
from pathlib import Path
import pytest
from ..ability_source_inventory import source_inventory,resolve_inventory_source
from ..traversal import Node,Placement,Position,Route,reachable_positions
from ..traversal_data import compile_room_graph
from .test_traversal import policy
from .traversal_reference import reachable_positions as reference


def yellow():
    return next(r for r in source_inventory().values() if r['source_key']=='GOLEM'
                and r.get('type_id')==32 and r.get('subtype1')==0)


def graph_source(**extra):
    r=yellow()
    return {'version':1,'status':'reviewed','nodes':[{'id':n,'native_room':r['native_room']} for n in ('pre','post')],
            'starts':['pre'],'required_targets':['post'],
            'sources':[{'id':'golem','inventory_id':r['id'],'node':'pre','acquisition_evidence':'isolated test approach',**extra}],
            'routes':[{'from':'pre','to':'post','capability':'peg','evidence':'isolated Stone-only obstacle','allowed_abilities':['Stone']}]}

@pytest.mark.parametrize('gating',[False,True])
def test_unknown_native_phase_cannot_guarantee_stone(gating):
    graph=compile_room_graph(graph_source(),{},require_inventory=True)
    assert graph.placements[0].native_grants==('Stone','Wheel')
    for owned in (frozenset({'Stone Ability'}),frozenset({'Stone Ability','Wheel Ability'})):
        assert not graph.evaluate(policy(0),owned,gating).reaches('post')
    grant=policy(0).grant('GOLEM',lambda n:n=='Stone',('Stone','Wheel'))
    assert grant.abilities==frozenset({'Stone'}) and grant.can_fail and not grant.guaranteed


def test_phase_narrowing_requires_evidence_and_real_native_option():
    with pytest.raises(ValueError,match='phase selection'):
        compile_room_graph(graph_source(native_grants=['Stone']),{},require_inventory=True)
    with pytest.raises(ValueError,match='state contract'):
        compile_room_graph(graph_source(native_grants=['Hammer'],native_grant_evidence='not a native Golem phase'),{},require_inventory=True)
    graph=compile_room_graph(graph_source(native_grants=['Stone'],native_grant_evidence='isolated reviewed Stone-state acquisition'),{},require_inventory=True)
    assert graph.evaluate(policy(0),frozenset({'Stone Ability'}),True).reaches('post')
    assert not graph.evaluate(policy(0),frozenset(),True).reaches('post')

@pytest.mark.parametrize('mode',[1,2])
def test_runtime_randomization_overrides_native_phase_options(mode):
    graph=compile_room_graph(graph_source(),{},require_inventory=True)
    assert graph.evaluate(policy(mode,pool=['Stone']),frozenset({'Stone Ability'}),True).reaches('post')
    assert not graph.evaluate(policy(mode,pool=['Wheel']),frozenset({'Stone Ability','Wheel Ability'}),True).reaches('post')
    assert not graph.evaluate(policy(mode,pool=['Stone']),frozenset(),True).reaches('post')


def test_live_mixed_and_no_ability_outcomes_remain_uncertain():
    graph=compile_room_graph(graph_source(),{},require_inventory=True)
    owned=frozenset({'Stone Ability','Wheel Ability'})
    for weight in (0,50,100):
        assert not graph.evaluate(policy(2,pool=['Stone','Wheel'],weight=weight),owned,True).reaches('post')
    # Native phase alternatives cannot become live rerolls through retry opt-in.
    graph=compile_room_graph(graph_source(renewable=True,renewable_evidence='isolated reset',retry_evidence='isolated repeat contact'),{},require_inventory=True)
    result=graph.evaluate(policy(0),owned,True,True)
    assert not result.reaches('post') and not result.retry_assumptions


def test_grant_cache_does_not_transfer_a_phase_between_physical_sources():
    nodes=[Node(n,1) for n in ('a','b','stone','wheel')]
    sources=[Placement('a','GOLEM',identity='a',native_grants=('Stone',)),Placement('b','GOLEM',identity='b',native_grants=('Wheel',))]
    routes=[Route('a','stone','peg'),Route('b','wheel',required_equipment=frozenset({'Wheel'}))]
    starts=[Position('a'),Position('b')]
    result=reachable_positions(nodes,routes,sources,starts,policy(0),gating=False)
    assert result.reaches('stone') and result.reaches('wheel')
    assert result.positions==reference(nodes,routes,sources,starts,policy(0),gating=False).positions


def test_inventory_records_native_variants_without_certifying_phase_access():
    records=[r for r in source_inventory().values() if r['source_key']=='GOLEM']
    assert len(records)==22
    for r in records:
        contract=r['native_grant_states']
        assert contract['source_sha256']=='8399d5f2bad9211e186e7c9a2374ca09de65867d10a8cc35ec28c4ecaac0ed31'
        assert contract['phase_acquisition'].startswith('unresolved')
        subtype=contract['subtype1']
        expected={31:{'Stone'},32:{'Stone','Wheel'},33:{'Stone','Fighter'}}[r['type_id']]
        if subtype is None or subtype&127:expected={'Stone','Wheel','Fighter'}
        assert set(contract['options'])==expected
    ordinary=next(r for r in source_inventory().values() if r['source_key']=='ROCKY')
    with pytest.raises(ValueError,match='no native phase'):
        resolve_inventory_source({'inventory_id':ordinary['id'],'native_grants':['Wheel']},ordinary['native_room'])


@pytest.mark.parametrize('kind,subtype,options', [
    (0, 3, ('Parasol', 'Normal')),
    (0, 4, ('Parasol',)),
    (18, 1, ('Parasol', 'Beam')),
])
def test_attached_parasol_parent_grants_keep_the_actual_native_alternatives(kind, subtype, options):
    records = [r for r in source_inventory().values()
               if r.get('type_id') == kind and r.get('subtype1') == subtype]
    assert len(records) == {(0, 3): 2, (0, 4): 20, (18, 1): 4}[kind, subtype]
    for record in records:
        resolved = resolve_inventory_source({'inventory_id': record['id']}, record['native_room'])
        assert tuple(resolved['native_grants']) == options
        vanilla = policy(0).grant(record['source_key'], lambda _: True, options)
        assert vanilla.guaranteed == (frozenset({'Parasol'}) if options == ('Parasol',) else frozenset())
        owned_parasol = policy(0).grant(record['source_key'], lambda n: n == 'Parasol', options)
        assert owned_parasol.can_fail == (len(options) > 1)
        for mode in (1, 2):
            randomized = policy(mode, pool=['Stone']).grant(record['source_key'], lambda _: True, options)
            assert randomized.guaranteed == frozenset({'Stone'})


def test_native_wheel_observation_does_not_promote_failed_phase_variants():
    evidence = json.loads((Path(__file__).parents[1] / 'dev-docs/generated-king-golem710-phase-observations.json').read_text())
    assert evidence['status'] == 'mechanics_observations_not_safe_route'
    cases = evidence['cases']
    assert len(cases) == 8
    wheel = cases['king-golem710-wheel-phase-onehp']
    assert wheel['minimum_hp'] == wheel['final']['hp'] == 1
    assert wheel['final']['ability'] == 4 and wheel['final']['frame'] == 3895
    assert wheel['equipment_transitions'][0]['frame'] == 3887
    intake = wheel['intakes'][0]
    assert intake['last_observed_source']['native_ability'] == 4
    assert intake['source']['type_id'] == 32
    assert intake['source']['parent'] == '0x2000054'
    assert intake['source']['state'] == '0x809c48d'
    fighter = cases['king-golem710-fighter-filter-sixhp']
    assert any(row['source']['native_ability'] == 20 for row in fighter['phase_observations'])
    assert not any(row['ability'] == 20 for row in fighter['equipment_transitions'])
    assert fighter['final']['hp'] == 0
    for suffix in ('shuffled', 'unowned', 'live', 'health500'):
        failed = cases['king-golem710-wheel-phase-' + suffix]
        assert failed['final']['hp'] == 0 and not failed['equipment_transitions']
    for case in cases.values():
        assert case['initial']['ability'] == 0
        assert case['configured_start'] == [710, 16, 288]
        assert all(len(case[key]) == 64 for key in ('private_trace_sha256', 'runtime_sha256',
                                                   'fixture_rom_sha256', 'script_sha256', 'bridge_sha256'))


@pytest.mark.parametrize('mode', [1, 2])
def test_excluding_passive_enemies_retains_native_attached_parasol(mode):
    import random
    from ..ability_randomization import build_enemy_copy_ability_policy
    from ..traversal import SourcePolicy
    raw = build_enemy_copy_ability_policy(random.Random(427), mode, True, True, True,
                                         include_passive_enemies=False, whitelist=['Stone'])
    resolver = SourcePolicy(raw)
    grant = resolver.grant('WADDLE_DEE', lambda _: True, ('Parasol',))
    assert grant.guaranteed == frozenset({'Parasol'}) and not grant.randomized
    mixed = resolver.grant('WADDLE_DEE', lambda _: True, ('Parasol', 'Normal'))
    assert not mixed.guaranteed and mixed.can_fail and not mixed.randomized
    # Waddle Doo's table grant is non-Normal, so its eligible runtime assignment still wins.
    assert resolver.grant('WADDLE_DOO', lambda _: True, ('Parasol', 'Beam')).guaranteed == frozenset({'Stone'})


def test_fighter_followup_preserves_failed_control_and_exact_intake_lineage():
    root = Path(__file__).parents[1] / 'dev-docs'
    evidence = json.loads((root / 'generated-king-golem710-fighter-acceptance.json').read_text())
    historical = json.loads((root / 'generated-king-golem710-phase-observations.json').read_text())
    control = evidence['cases']['king-golem710-fighter-filter-sixhp']
    positive = evidence['cases']['king-golem710-fighter-filter-swallow']
    assert control == historical['cases']['king-golem710-fighter-filter-sixhp']
    assert evidence['comparison'] == {
        'identical_observations_through_frame': 5800, 'first_different_input_frame': 5801,
        'control_keys': 2, 'positive_keys': 128, 'same_fixture_rom': True}
    assert positive['fixture_rom_sha256'] == control['fixture_rom_sha256']
    assert positive['configured_hp'] == 6 and positive['minimum_hp'] == 1
    assert positive['final']['frame'] == 5836 and positive['final']['ability'] == 20
    assert positive['final']['hp'] == 1 and positive['final']['room'] == 710
    assert positive['health_percent'] == 100 and positive['policy']['mode'] == 0
    intake = next(row for row in positive['intakes'] if row['frame'] == 5798)
    assert intake['source']['type_id'] == 33
    assert intake['source']['parent'] == '0x2000054'
    assert intake['source']['native_ability'] == intake['last_observed_source']['native_ability'] == 20
    assert intake['source']['state'] == '0x809c48d'
    assert positive['equipment_transitions'][-1]['ability'] == 20
    assert control['final']['hp'] == 0
    assert not any(row['ability'] == 20 for row in control['equipment_transitions'])
    assert not positive['runtime_writes']
    for key in ('private_trace_sha256', 'runtime_sha256', 'fixture_rom_sha256', 'script_sha256', 'bridge_sha256'):
        assert len(positive[key]) == 64
