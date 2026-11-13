"""Sanitized finite-source contracts, not emulator reruns or new native evidence."""

import json
from pathlib import Path

import pytest

from ..client import KirbyAmClient
from ..enemy_ability_data import ABILITY_NAME_TO_ID
from ..enemy_ability_runtime_patch import build_enemy_copy_runtime_patch_writes, build_enemy_source_runtime_config
from ..traversal import SourcePolicy
from ..traversal_data import room_traversal_targets


ROOT = Path(__file__).parents[1]


def evidence(ability):
    return json.loads((ROOT / 'dev-docs' / f'cabbage-{ability.lower()}-acceptance.json').read_text())


@pytest.mark.parametrize('ability,seed,grant', [
    ('Spark', 14282527318440564224, 15), ('Ice', 13204005821666718668, 2)])
def test_original_source_policy_and_exact_target_ownership(ability, seed, grant):
    doc = evidence(ability)
    policy = doc['source_policy']
    assert policy['seed'] == seed and policy['mode'] == 1 and policy['mapping_style'] == 'per_enemy_type'
    assert set(policy['allowed_abilities']) == set(ABILITY_NAME_TO_ID) - {'Normal', 'Master', 'Wait'}
    assert build_enemy_copy_runtime_patch_writes(policy)[0x3517FE] == grant
    assert int.from_bytes(build_enemy_source_runtime_config(policy)[4:8], 'little') & (1 << 18)
    assert SourcePolicy(policy).grant('WADDLE_DOO', lambda _: True).guaranteed == frozenset({ability})
    assert doc['source'] == {'template': '0x088CA04C', 'native_type': 18, 'native_copy': 7,
                             'native_xy': [528, 264], 'finite': True, 'renewal': False, 'acquisition_frame': 1939}
    target = doc['target']
    assert target == {'capability': 'bomb_517_chocolate', 'graph': f'hub2_{ability.lower()}_entry',
                      'location': 'MINOR_CHEST_SPRAY_PAINT_12', 'location_id': 3960511, 'room': 517,
                      'f1': [14, 7], 'linked_cells': 7, 'chest': 57, 'template': '0x088CA0B8'}
    owners = [(row['id'], key) for row in room_traversal_targets('block') for key in row['graphs']
              if key == target['graph']]
    assert owners == [('bomb_517_chocolate', target['graph'])]
    assert KirbyAmClient()._build_minor_chest_source_ptr_map()[0x8CA0B8] == 3960511
    setup = doc['setup']
    assert setup['independent_hub2_access_assumed'] and setup['startup_fixture_only']
    assert setup['predecessor'] == 591 and setup['initial_ability'] == 'Normal' and setup['helpers_room'] == 101
    assert setup['configuration_write_count'] == 8 and setup['configuration_frame'] == 1085
    assert setup['later_gameplay_writes'] == 0 and not setup['initial_state_restored']
    assert (setup['fresh_save_bytes'], setup['fresh_save_fill']) == (32768, 255)


@pytest.mark.parametrize('ability,end,corridor,chest,grant', [
    ('Spark', 4572, 2013, 4334, 15), ('Ice', 4490, 2016, 4252, 2)])
def test_endpoint_runs_and_separate_bounded_permission_controls(ability, end, corridor, chest, grant):
    doc = evidence(ability)
    endpoints = [r for name, r in doc['runs'].items() if name.startswith('final')]
    assert len(endpoints) == 8
    assert {(r['hp'], r['enemy_health'], r['positive']) for r in endpoints} == {
        (hp, enemy, positive) for hp in (1, 6) for enemy in (100, 500) for positive in (True, False)}
    for run in endpoints:
        assert (run['first_frame'], run['last_frame'], run['sample_count']) == (1085, end, end - 1084)
        assert run['hp_min'] == run['hp_max'] == run['hp']
        assert run['source_hp'] == run['enemy_health'] // 25
        assert run['ingress_frame'] == 1109 and run['acquisition_frame'] == 1939
        assert run['corridor_frame'] == corridor and run['final_ability'] == grant
        assert not run['acquisition_only'] and run['local_client']['server_submission'] is False
        if run['positive']:
            hit = 3510 if ability == 'Spark' else 3341 if run['hp'] == 1 else 3342
            assert (run['target_frame'], run['linked_complete_frame'], run['chest_frame']) == (hit, hit + 30, chest)
            assert run['final_target'] == 0 and run['final_linked'] == [0] * 7
            assert run['final_chest'] and run['final_event_count'] == 1
            assert run['local_client']['messages'] == [{'cmd': 'LocationChecks', 'locations': [3960511]}]
            attack = run['attack']
            assert int(attack['parent'], 16) == 0x02020EE0
            if ability == 'Spark':
                assert int(attack['task_fn'], 16) == 0x08074C1D and int(attack['mask'], 16) == 0xA0000403
                assert attack['scan_box'] == [-26, -22, 26, 30]
                assert attack['integer_rect'] == [175, 66, 227, 118]
            else:
                assert int(attack['task_fn'], 16) == 0x080737D9 and int(attack['mask'], 16) == 0xA0000203
                assert attack['scan_box'] == [-3, -3, 3, 3]
                assert attack['integer_rect'] == ([219, 116, 225, 122] if run['hp'] == 1 else [219, 114, 225, 120])
        else:
            assert run['target_frame'] is run['linked_complete_frame'] is run['chest_frame'] is None
            assert run['final_target'] == 241 and run['final_linked'] == [242] * 7
            assert not run['final_chest'] and run['final_event_count'] == 0 and not run['local_client']['messages']
    gate = [r for name, r in doc['runs'].items() if name.startswith('gated')]
    assert len(gate) == 2
    for run in gate:
        assert run['gate_mask'] == 67108470
        if run['acquisition_only']:
            assert run['permission_mask'] == run['final_ability'] == 0
            assert run['last_frame'] == (2007 if ability == 'Spark' else 2067)
            assert run['acquisition_frame'] is run['corridor_frame'] is None
        else:
            assert run['permission_mask'] == 1 << grant and run['last_frame'] == end
            assert run['acquisition_frame'] == 1939 and run['final_chest']
    start = 3504 if ability == 'Spark' else 3326
    assert doc['control'] == {'omitted_B_half_open': [start, start + 30], 'common_state_through': start,
                              'full_target_omission_controls': 4, 'no_permission_acquisition_only': True}


@pytest.mark.parametrize('ability', ['Spark', 'Ice'])
def test_provenance_and_limits_are_explicit(ability):
    doc = evidence(ability)
    assert doc['source_commit'] == '4725bd0a306fbc43008e0e31e7625d0365632ab1'
    expected = {'Spark': '67cdbd26b91d959b2624efc7945062196a0de2873686dc75ed3553fc0541ed64',
                'Ice': '50cfd9738415340b8c6fdce2c39527ce757003df385bb3cb7e5782afa8b87427'}
    assert doc['independent_report_sha256'] == expected[ability]
    assert doc['combat']['independently_reviewed'] and not doc['combat']['non_source_combat_dependency']
    if ability == 'Ice':
        assert doc['combat']['frozen_platform_or_payload_dependency'] is False
    assert '0x1000' in doc['combat']['non_source_hp_reductions']
    assert len(doc['limits']) == 7
    for suffix in ('acceptance.json', 'source-witness.md'):
        text = (ROOT / 'dev-docs' / f'cabbage-{ability.lower()}-{suffix}').read_text()
        assert all(private not in text for private in ('/home/', '/Users/', 'C:\\'))
