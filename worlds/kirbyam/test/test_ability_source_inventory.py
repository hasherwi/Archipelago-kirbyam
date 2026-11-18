"""Physical inventory joins must not turn ownership or presence into equipment."""
from copy import deepcopy
import json
from pathlib import Path

import pytest

from ..ability_source_inventory import resolve_inventory_source, source_inventory
from ..traversal_data import compile_room_graph
from .test_traversal import policy

ROOT = Path(__file__).resolve().parents[1]
ROCK = 'room:401/template:0x088C5840'


def payload(node='pre'):
    return {
        'version': 1, 'status': 'reviewed',
        'nodes': [{'id': 'pre', 'native_room': 401}, {'id': 'post', 'native_room': 401}],
        'routes': [{'from': 'pre', 'to': 'post', 'capability': 'peg', 'evidence': 'test barrier'}],
        'sources': [{'node': node, 'inventory_id': ROCK, 'id': 'rock',
                     'acquisition_evidence': 'test acquisition limited to assigned compartment'}],
        'starts': ['pre'], 'required_targets': ['post'],
    }


def test_native_census_has_explicit_rooms_and_unique_placements():
    inventory = json.loads((ROOT / 'data/ability_source_inventory.json').read_text())
    assert [room['native_room'] for room in inventory['rooms']] == list(range(983))
    placements = source_inventory()
    references = [key for room in inventory['rooms'] for key in room['placements']]
    assert len(references) == len(set(references)) == 3476
    generated = {row['id'] for row in inventory['generated_statue_slots']}
    assert len(generated) == 2
    generated |= {row['id'] for row in inventory['spawner_outputs'] + inventory['encounter_sources']}
    assert set(references) | generated == set(placements)
    assert {key for room in inventory['rooms'] for key in room['encounter_sources']} == {
        row['id'] for row in inventory['encounter_sources']}
    assert any(not room['placements'] for room in inventory['rooms'])
    assert any(row['native_grant'] == 'Normal' and row['source_type'] == 'enemy'
               for row in placements.values())
    for row in inventory['encounter_calls'] + inventory['dynamic_grant_types']:
        assert row['logic'] == 'advanced'
    assert all(row['status'] == 'unresolved' for row in inventory['encounter_calls'])


def test_dedicated_boss_endurance_records_remain_in_census_but_not_adventure_logic():
    inventory = json.loads((ROOT / 'data/ability_source_inventory.json').read_text())
    excluded = {950, 951, 955, 956, 957, 969}
    assert {r['native_room'] for r in inventory['rooms'] if 'world_access' in r} == excluded
    for row in source_inventory().values():
        if row['native_room'] in excluded:
            assert row['world_access']['status'] == 'outside_adventure'
            with pytest.raises(ValueError, match='outside Adventure'):
                resolve_inventory_source({'inventory_id': row['id']}, row['native_room'],
                                         advanced=True, require_inventory=True)
        else:
            assert 'world_access' not in row
    # Copy Ability Room remains an Adventure source, unlike starting room950.
    statues = [r for r in source_inventory().values()
               if r['native_room'] == 970 and r['source_type'] == 'statue']
    assert statues
    for row in statues:
        assert resolve_inventory_source({'inventory_id': row['id']}, 970,
                                        require_inventory=True)['source_key'] == row['source_key']


def test_inventory_reference_checks_room_grant_and_unknowns():
    source = payload()['sources'][0]
    assert resolve_inventory_source(source, 401)['source_key'] == 'ROCKY'
    with pytest.raises(ValueError, match='another room'):
        resolve_inventory_source(source, 402)
    with pytest.raises(ValueError, match='grant mismatch'):
        resolve_inventory_source({**source, 'source_key': 'BONKERS'}, 401)
    with pytest.raises(ValueError, match='Unknown physical'):
        resolve_inventory_source({**source, 'inventory_id': 'missing'}, 401)


@pytest.mark.parametrize('gating', [False, True])
def test_native_presence_does_not_bootstrap_own_barrier(gating):
    graph = compile_room_graph(payload('post'), {})
    assert not graph.evaluate(policy(), frozenset({'Stone Ability'}), gating).reaches('post')
    without_source = payload()
    without_source['sources'] = []
    assert not compile_room_graph(without_source, {}).evaluate(
        policy(), frozenset({'Stone Ability'}), gating).reaches('post')


def test_physical_grant_preserves_permission_and_random_failure():
    graph = compile_room_graph(payload(), {})
    assert not graph.evaluate(policy(), frozenset(), True).reaches('post')
    assert graph.evaluate(policy(), frozenset({'Stone Ability'}), True).reaches('post')
    assert graph.evaluate(policy(), frozenset(), False).reaches('post')
    assert not graph.evaluate(policy(2, pool=['Fire']), frozenset(), False).reaches('post')
    assert not graph.evaluate(policy(2, pool=['Stone'], weight=100), frozenset(), False).reaches('post')
    assert not graph.evaluate(policy(2, pool=['Stone'], weight=50), frozenset(), False).reaches('post')


def test_encounter_type_requires_advanced_graph_even_without_inventory_reference():
    graph = payload()
    graph['sources'] = [{'node': 'pre', 'source_key': 'BOMBAR_BOMB',
                         'acquisition_evidence': 'test encounter prerequisite', 'items': ['Encounter started']}]
    with pytest.raises(ValueError, match='Advanced Logic'):
        compile_room_graph(graph, {})
    compiled = compile_room_graph(graph, {}, advanced=True)
    assert compiled.placements[0].requirements == frozenset({'Encounter started'})
    assert not compiled.evaluate(policy(), frozenset(), False).reaches('post')


def test_join_does_not_mutate_witness_or_invent_renewability():
    original = payload()
    snapshot = deepcopy(original)
    graph = compile_room_graph(original, {})
    assert original == snapshot
    assert not graph.placements[0].renewable
    assert graph.placements[0].identity == 'rock'


def test_same_physical_source_cannot_be_consumed_under_two_identities():
    graph = payload()
    graph['sources'].append({**graph['sources'][0], 'id': 'second-rock'})
    with pytest.raises(ValueError, match='multiple consumption identities'):
        compile_room_graph(graph, {})


def test_reviewed_legacy_identity_joins_without_changing_consumption_contract():
    source = {'id': '0x088C5840', 'source_key': 'ROCKY', 'node': 'pre',
              'acquisition_evidence': 'existing reviewed acquisition'}
    assert resolve_inventory_source(source, 401) == source
    with pytest.raises(ValueError, match='grant mismatch'):
        resolve_inventory_source({**source, 'source_key': 'BONKERS'}, 401)


def test_legacy_binding_cannot_be_evaded_by_changing_its_room():
    source = {'id': '0x088C5840', 'source_key': 'ROCKY', 'node': 'pre',
              'acquisition_evidence': 'existing reviewed acquisition'}
    with pytest.raises(ValueError, match='another room'):
        resolve_inventory_source(source, 402)


def test_normally_empty_enemy_uses_actual_live_random_runtime_eligibility():
    record = next(row for row in source_inventory().values() if row['source_key'] == 'WADDLE_DEE')
    graph = payload()
    for node in graph['nodes']:
        node['native_room'] = record['native_room']
    graph['sources'][0]['inventory_id'] = record['id']
    compiled = compile_room_graph(graph, {})
    assert not compiled.evaluate(policy(), frozenset(), False).reaches('post')
    assert compiled.evaluate(policy(2, pool=['Stone']), frozenset(), False).reaches('post')
    assert not compiled.evaluate(policy(2, pool=['Stone'], weight=100), frozenset(), False).reaches('post')


def test_absent_consumption_identity_defaults_to_physical_placement():
    graph = payload()
    graph['sources'][0]['id'] = None
    compiled = compile_room_graph(graph, {})
    assert compiled.placements[0].identity == ROCK


def test_distinct_physical_sources_cannot_alias_consumption():
    graph = payload()
    graph['sources'].append({**graph['sources'][0],
                             'inventory_id': 'room:401/template:0x088C5864'})
    with pytest.raises(ValueError, match='share one consumption identity'):
        compile_room_graph(graph, {})


def test_native_random_statues_have_physical_slots_but_no_guaranteed_selection():
    inventory = json.loads((ROOT / 'data/ability_source_inventory.json').read_text())
    slots = inventory['generated_statue_slots']
    assert len(slots) == 2
    assert slots[0]['id'] != slots[1]['id']
    for slot in slots:
        assert slot['native_room'] == 951
        assert len(slot['possible_source_keys']) == len(set(slot['possible_source_keys'])) == 19
        with pytest.raises(ValueError, match='generation_evidence'):
            resolve_inventory_source({'inventory_id': slot['id']}, 951)


def test_encounter_generated_ordinary_enemy_is_still_advanced_only():
    inventory = json.loads((ROOT / 'data/ability_source_inventory.json').read_text())
    minny = next(call for call in inventory['encounter_calls']
                 if call.get('source_key') == 'MINNY')
    assert minny['controller_type'] == 0x3D  # Boxy's generated Minny, not a static Minny.
    assert minny['logic'] == 'advanced'
    assert minny['status'] == 'unresolved'


def test_production_graph_rejects_uncatalogued_source_instead_of_inventing_presence():
    graph = payload()
    graph['sources'][0].pop('inventory_id')
    graph['sources'][0]['source_key'] = 'ROCKY'
    with pytest.raises(ValueError, match='requires a physical inventory reference'):
        compile_room_graph(graph, {}, require_inventory=True)
    assert compile_room_graph(payload(), {}, require_inventory=True).placements[0].source_key == 'ROCKY'


def test_spawner_prototypes_are_censused_without_becoming_acquisition_witnesses():
    inventory = json.loads((ROOT / 'data/ability_source_inventory.json').read_text())
    outputs = inventory['spawner_outputs']
    parents = {row['id'] for row in inventory['placements'] if row['source_type'] == 'object_spawner'}
    assert len(outputs) == len(parents) == 37
    assert {row['parent_placement'] for row in outputs} == parents
    assert sum(row['source_type'] == 'miniboss' for row in outputs) == 6
    candidates = {key for call in inventory['encounter_calls'] for key in call['candidate_encounters']}
    assert {row['id'] for row in outputs if row['source_type'] == 'miniboss'} <= candidates
    for row in outputs:
        assert row['configured_child_capacity'] == 1
        assert not row['reclaims_destroyed_slots']
        assert row['status'] == 'unresolved'
        assert row['id'] in source_inventory()
        with pytest.raises(ValueError, match='generation_evidence|Unresolved physical ability grant'):
            resolve_inventory_source({'inventory_id': row['id']}, row['native_room'], advanced=True)


def test_spawner_counter_dependencies_remain_conditional_and_room_local():
    inventory = json.loads((ROOT / 'data/ability_source_inventory.json').read_text())
    records = {row['id']: row for row in inventory['placements'] + inventory['spawner_outputs']}
    for output in inventory['spawner_outputs']:
        conditions = output['spawn_conditions']
        assert conditions['counter_access_certified'] is False
        contributors = [records[key] for key in conditions['candidate_counter_contributors']]
        assert contributors
        assert all(row['native_room'] == output['native_room'] for row in contributors)
        assert all(any(event['bank'] == conditions['room_counter_bank']
                       for event in row['conditional_room_counter_events']) for row in contributors)
    # Room526 outputs depend on Boxy, not mere room access or any enemy defeat.
    room526 = [row for row in inventory['spawner_outputs'] if row['native_room'] == 526]
    assert len(room526) == 4
    assert all(row['logic'] == 'advanced' for row in room526)
    for row in room526:
        with pytest.raises(ValueError, match='Advanced Logic'):
            resolve_inventory_source({'inventory_id': row['id']}, 526)
    assert all({records[key]['native_name'] for key in row['spawn_conditions']['candidate_counter_contributors']}
               == {'OBJ_BOXY'} for row in room526)
    # A generated Boss Endurance boss can feed the next counter threshold;
    # these conditional chains do not admit the room into Adventure logic.
    endurance = [row for row in inventory['spawner_outputs'] if row['native_room'] == 955]
    assert any(any(key.endswith('/spawner-output') for key in row['spawn_conditions']['candidate_counter_contributors'])
               for row in endurance)
    assert all(row['world_access']['status'] == 'outside_adventure' for row in endurance)


def test_generated_boss_phases_retain_candidate_roots_without_becoming_sources():
    inventory = json.loads((ROOT / 'data/ability_source_inventory.json').read_text())
    for typ in (0x4C, 0x4D):
        calls = [call for call in inventory['encounter_calls'] if call['controller_type'] == typ]
        assert calls
        assert all(call['candidate_root_encounters'] and call['controller_parent_calls'] for call in calls)
        assert all(call['logic'] == 'advanced' and call['status'] == 'unresolved' for call in calls)


@pytest.mark.parametrize('kind', ['spawner_outputs', 'encounter_sources'])
def test_generated_candidates_require_explicit_generation_and_lifetime_witness(kind):
    inventory = json.loads((ROOT / 'data/ability_source_inventory.json').read_text())
    record = next(r for r in inventory[kind] if r['source_key'] is not None)
    source = {'inventory_id': record['id'], 'acquisition_evidence': 'fixture'}
    for field in ('generation_evidence', 'lifetime_evidence'):
        with pytest.raises(ValueError, match=field):
            resolve_inventory_source(source, record['native_room'], advanced=True)
        source[field] = 'reviewed fixture'
    resolved = resolve_inventory_source(source, record['native_room'], advanced=True)
    assert resolved['lifetime'] == record['id']
    if record['logic'] == 'advanced':
        with pytest.raises(ValueError, match='Advanced Logic'):
            resolve_inventory_source(source, record['native_room'])
    with pytest.raises(ValueError, match='lifetime mismatch'):
        resolve_inventory_source({**source, 'lifetime': 'another encounter'},
                                 record['native_room'], advanced=True)


@pytest.mark.parametrize('effect,evidence,value', [
    ('loses_equipment', 'loss_evidence', True),
    ('ends_lifetimes', 'lifetime_evidence', ['encounter']),
    ('revives_lifetimes', 'revival_evidence', ['encounter']),
    ('activates_lifetimes', 'activation_evidence', ['encounter']),
])
def test_serialized_lifetime_effect_requires_evidence(effect, evidence, value):
    graph = payload()
    graph['sources'][0]['lifetime'] = 'encounter'
    graph['routes'][0][effect] = value
    with pytest.raises(ValueError, match=evidence):
        compile_room_graph(graph, {})
    graph['routes'][0][evidence] = 'fixture witness'
    if effect == 'revives_lifetimes':
        graph['routes'][0].update(room_instance='reset', room_transition=True, reset_evidence='fixture reset')
    compiled = compile_room_graph(graph, {})
    assert getattr(compiled.routes[0], effect) == (value if isinstance(value, bool) else frozenset(value))



def test_native_non_reclaiming_spawner_cannot_supply_unlimited_random_retries():
    inventory = json.loads((ROOT / 'data/ability_source_inventory.json').read_text())
    for record in inventory['spawner_outputs']:
        if record['source_key'] is None:
            continue
        source = {'inventory_id': record['id'], 'generation_evidence': 'fixture activation',
                  'lifetime_evidence': 'fixture encounter', 'renewable': True,
                  'renewable_evidence': 'unsupported retry claim', 'retry_evidence': 'retry'}
        with pytest.raises(ValueError, match='Finite non-reclaiming spawner'):
            resolve_inventory_source(source, record['native_room'], advanced=True)
        source.update(renewable=False)
        source.pop('retry_evidence')
        assert not resolve_inventory_source(source, record['native_room'], advanced=True)['renewable']


def test_room_reset_cannot_override_session_or_world_spawn_bits():
    persistent = [row for row in source_inventory().values()
                  if row.get('source_key') and row.get('spawn_conditions', {}).get('state_bank') in (1, 2)]
    assert len(persistent) == 10
    assert {row['source_key'] for row in persistent} == {'COOKIN', 'JACK'}
    for row in persistent:
        source = {'inventory_id': row['id']}
        assert resolve_inventory_source(source, row['native_room'])['room_reset_respawns'] is False
        with pytest.raises(ValueError, match='room-reset contract mismatch'):
            resolve_inventory_source(dict(source, room_reset_respawns=True), row['native_room'])
    assert resolve_inventory_source({'inventory_id': ROCK}, 401).get('room_reset_respawns', True) is True


def test_compiled_cookin_retains_consumption_across_same_room_reset():
    from dataclasses import replace
    from ..traversal import Position
    record = source_inventory()['room:133/template:0x088CBAB0']
    identity = record['id']
    graph = compile_room_graph({
        'version': 1, 'status': 'reviewed',
        'nodes': [{'id': key, 'native_room': 133} for key in ('pre', 'contact', 'goal')],
        'sources': [{'id': identity, 'inventory_id': identity, 'node': 'contact',
                     'acquisition_evidence': 'isolated physical acquisition fixture'}],
        'routes': [{'from': 'pre', 'to': 'contact', 'room_transition': True,
                    'room_instance': 'reset', 'reset_evidence': 'isolated new room slot',
                    'evidence': 'isolated return'},
                   {'from': 'contact', 'to': 'goal', 'required_equipment': ['Cook'],
                    'evidence': 'isolated equipment observation'}],
        'starts': ['pre'], 'required_targets': ['goal'],
    }, {}, require_inventory=True)
    assert graph.placements[0].room_reset_respawns is False
    initial = Position('pre', consumed=frozenset({identity}))
    spent = replace(graph, starts=(initial,))
    assert not spent.evaluate(policy(), frozenset(), gating=False).reaches('goal')
    carried = replace(graph, starts=(replace(initial, equipped='Cook'),))
    assert carried.evaluate(policy(), frozenset(), gating=False).reaches('goal')
