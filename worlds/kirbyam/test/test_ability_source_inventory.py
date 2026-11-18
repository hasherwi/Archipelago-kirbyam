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
    assert set(references) | generated == set(placements)
    assert any(not room['placements'] for room in inventory['rooms'])
    assert any(row['native_grant'] == 'Normal' and row['source_type'] == 'enemy'
               for row in placements.values())
    for row in inventory['encounter_calls'] + inventory['dynamic_grant_types']:
        assert row['logic'] == 'advanced'
    assert all(row['status'] == 'unresolved' for row in inventory['encounter_calls'])


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
        with pytest.raises(ValueError, match='Unresolved physical ability grant'):
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
        assert row['id'] not in source_inventory()
        with pytest.raises(ValueError, match='Unknown physical'):
            resolve_inventory_source({'inventory_id': row['id']}, row['native_room'], advanced=True)


def test_generated_boss_phases_retain_candidate_roots_without_becoming_sources():
    inventory = json.loads((ROOT / 'data/ability_source_inventory.json').read_text())
    for typ in (0x4C, 0x4D):
        calls = [call for call in inventory['encounter_calls'] if call['controller_type'] == typ]
        assert calls
        assert all(call['candidate_root_encounters'] and call['controller_parent_calls'] for call in calls)
        assert all(call['logic'] == 'advanced' and call['status'] == 'unresolved' for call in calls)
