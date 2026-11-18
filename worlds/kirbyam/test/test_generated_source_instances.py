"""Finite generated occurrences are separate from a reusable native prototype."""
from copy import deepcopy

import pytest

from ..ability_source_inventory import resolve_inventory_source
from ..traversal_data import compile_room_graph
from .test_traversal import policy

PROTOTYPE = 'room:710/template:0x088BD2B0/encounter:70/src/king_golem.c:439/type:31'


def life(name):
    return PROTOTYPE + '/instance:' + name


def payload(activate_second=True):
    return {
        'version': 1, 'status': 'reviewed',
        'nodes': [{'id': key, 'native_room': 710} for key in ('arrival', 'first', 'second', 'goal')],
        'sources': [{'node': key, 'inventory_id': PROTOTYPE, 'generation_instance': key,
                     'instance_evidence': 'fixture: separately observed finite occurrence',
                     'generation_evidence': 'fixture: branch and controller prerequisites',
                     'lifetime_evidence': 'fixture: this occurrence only',
                     'acquisition_evidence': 'fixture: source contact compartment'} for key in ('first', 'second')],
        'routes': [
            {'from': 'arrival', 'to': 'first', 'activates_lifetimes': [life('first')],
             'activation_evidence': 'fixture first event', 'evidence': 'fixture approach'},
            {'from': 'first', 'to': 'second', 'required_equipment': ['Stone'],
             'loses_equipment': True, 'loss_evidence': 'fixture equipment loss',
             'ends_lifetimes': [life('first')], 'lifetime_evidence': 'fixture first output ends',
             'activates_lifetimes': [life('second')] if activate_second else [],
             'activation_evidence': 'fixture second event', 'evidence': 'fixture later phase'},
            {'from': 'second', 'to': 'goal', 'required_equipment': ['Stone'], 'evidence': 'fixture observation'}],
        'starts': ['arrival'], 'required_targets': ['goal'],
    }


@pytest.mark.parametrize('activate_second', [False, True])
def test_second_finite_occurrence_requires_its_own_activation_without_room_reset(activate_second):
    graph = compile_room_graph(payload(activate_second), {}, advanced=True, require_inventory=True)
    assert {s.identity for s in graph.placements} == {life('first'), life('second')}
    assert all(not s.renewable for s in graph.placements)
    assert graph.evaluate(policy(), frozenset(), gating=False).reaches('goal') is activate_second


def test_one_occurrence_cannot_be_duplicated_under_another_consumption_identity():
    data = payload()
    duplicate = deepcopy(data['sources'][0])
    duplicate['id'] = 'another-name-for-first'
    data['sources'].append(duplicate)
    with pytest.raises(ValueError, match='multiple consumption identities'):
        compile_room_graph(data, {}, advanced=True)


def test_distinct_occurrences_cannot_share_consumption_identity():
    data = payload()
    for source in data['sources']:
        source['id'] = 'same-identity'
    with pytest.raises(ValueError, match='cannot share one consumption identity'):
        compile_room_graph(data, {}, advanced=True)


def test_prototype_cannot_mix_unqualified_and_explicit_occurrences():
    data = payload()
    data['sources'][0].pop('generation_instance')
    with pytest.raises(ValueError, match='cannot mix implicit and explicit'):
        compile_room_graph(data, {}, advanced=True)


@pytest.mark.parametrize('identity', ['', None, [], '../first', 'first/second'])
def test_instance_identity_is_explicit_and_well_formed(identity):
    data = payload()
    data['sources'][0]['generation_instance'] = identity
    with pytest.raises(ValueError, match='simple nonempty identity'):
        compile_room_graph(data, {}, advanced=True)


def test_instance_evidence_and_advanced_logic_are_required():
    data = payload()
    data['sources'][0].pop('instance_evidence')
    with pytest.raises(ValueError, match='instance_evidence'):
        compile_room_graph(data, {}, advanced=True)
    with pytest.raises(ValueError, match='Advanced Logic'):
        compile_room_graph(payload(), {})


def test_ordinary_placement_cannot_manufacture_extra_instances():
    with pytest.raises(ValueError, match='Only a generated prototype'):
        resolve_inventory_source({'inventory_id': 'room:401/template:0x088C5840',
                                  'generation_instance': 'extra', 'instance_evidence': 'invented'}, 401)
    with pytest.raises(ValueError, match='physical inventory reference'):
        resolve_inventory_source({'source_key': 'GOLEM', 'generation_instance': 'extra',
                                  'instance_evidence': 'invented'}, 710)


def test_single_output_non_reclaiming_spawner_cannot_multiply_instances():
    with pytest.raises(ValueError, match='Non-reclaiming spawner'):
        resolve_inventory_source({
            'inventory_id': 'room:121/template:0x088D2898/spawner-output',
            'generation_instance': 'extra', 'instance_evidence': 'invented',
        }, 121, advanced=True)


def test_random_statue_slot_cannot_multiply_its_fixed_native_selection():
    with pytest.raises(ValueError, match='Only encounter output prototypes'):
        resolve_inventory_source({
            'inventory_id': 'room:951/template:0x088D5BF8/statue-slot:0',
            'generation_instance': 'reroll', 'instance_evidence': 'invented',
        }, 951, advanced=True)
