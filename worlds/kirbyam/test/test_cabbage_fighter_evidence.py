"""Sanitized Fighter517 scalar contracts; these tests do not rerun an emulator."""

from ..client import KirbyAmClient
from ..enemy_ability_data import ABILITY_NAME_TO_ID
from ..enemy_ability_runtime_patch import build_enemy_copy_runtime_patch_writes, build_enemy_source_runtime_config
from ..traversal import SourcePolicy
from .test_cabbage_fighter import ROOT, document


def test_native_assignment_and_setup_contract():
    doc = document()
    raw = doc['source_policy']
    assert doc['generation_seed'] == 39 and raw['seed'] == 6282654274669279257
    assert raw['mode'] == 1 and raw['mapping_style'] == 'per_enemy_type'
    assert set(raw['allowed_abilities']) == set(ABILITY_NAME_TO_ID) - {'Normal', 'Master', 'Wait'}
    assert build_enemy_copy_runtime_patch_writes(raw)[0x3517FE] == 20
    assert int.from_bytes(build_enemy_source_runtime_config(raw)[4:8], 'little') & (1 << 18)
    assert SourcePolicy(raw).grant('WADDLE_DOO', lambda _: True).guaranteed == frozenset({'Fighter'})
    assert doc['source'] == {'template': '0x088CA04C', 'native_type': 18, 'native_copy': 7,
                             'native_xy': [528, 264], 'finite': True, 'renewal': False, 'acquisition_frame': 1939}
    assert doc['target'] == {'capability': 'bomb_517_fighter_first_combo', 'graph': 'hub2_fighter_entry',
                             'location': 'MINOR_CHEST_SPRAY_PAINT_12', 'location_id': 3960511, 'room': 517,
                             'f1': [14, 7], 'linked_cells': 7, 'chest': 57, 'template': '0x088CA0B8'}
    setup = doc['setup']
    assert setup['predecessor'] == 591 and setup['initial_ability'] == 'Normal' and setup['helpers_room'] == 101
    assert setup['independent_hub2_access_assumed'] and setup['startup_fixture_only']
    assert setup['configuration_write_count'] == 8 and setup['configuration_frame'] == 1085
    assert setup['later_gameplay_writes'] == 0 and not setup['initial_state_restored']
    assert (setup['fresh_save_bytes'], setup['fresh_save_fill']) == (32768, 255)
    assert KirbyAmClient()._build_minor_chest_source_ptr_map()[0x8CA0B8] == 3960511


def test_endpoints_and_actual_first_combo():
    doc = document()
    endpoints = [run for name, run in doc['runs'].items() if name.startswith('final')]
    assert len(endpoints) == 8
    assert {(r['hp'], r['enemy_health'], r['positive']) for r in endpoints} == {
        (hp, enemy, positive) for hp in (1, 6) for enemy in (100, 500) for positive in (True, False)}
    for run in endpoints:
        assert (run['first_frame'], run['last_frame'], run['sample_count']) == (1085, 4490, 3406)
        assert run['hp_min'] == run['hp_max'] == run['hp']
        assert run['source_hp'] == run['enemy_health'] // 25
        assert run['ingress_frame'] == 1109 and run['acquisition_frame'] == 1939
        assert run['corridor_frame'] == 2009 and run['final_ability'] == 20
        assert not run['acquisition_only'] and not run['local_client']['server_submission']
        if run['positive']:
            assert (run['target_frame'], run['linked_complete_frame'], run['chest_frame']) == (3328, 3358, 4252)
            assert run['final_target'] == 0 and run['final_linked'] == [0] * 7
            assert run['final_chest'] and run['final_event_count'] == 1
            assert run['local_client']['messages'] == [{'cmd': 'LocationChecks', 'locations': [3960511]}]
            attack = run['attack']
            assert int(attack['parent'], 16) == 0x02020EE0 and int(attack['task_fn'], 16) == 0x0807E821
            assert int(attack['mask'], 16) == 0xB1000043 and int(attack['flags'], 16) == 0xA0080100
            assert attack['scan_box'] == [0, -19, 60, 11] and attack['integer_rect'] == [185, 101, 245, 131]
            assert (attack['animation'], attack['header']) == (53, 1)  # Ordinary first combo, not the HP1 wave.
            assert (attack['x'], attack['y']) == (185.99609375, 120.99609375)
        else:
            assert run['target_frame'] is run['linked_complete_frame'] is run['chest_frame'] is None
            assert run['final_target'] == 241 and run['final_linked'] == [242] * 7
            assert not run['final_chest'] and run['final_event_count'] == 0 and not run['local_client']['messages']
    assert doc['control'] == {'omitted_B_half_open': [3326, 3327], 'common_state_through': 3326,
                              'full_target_omission_controls': 4, 'no_permission_acquisition_only': True}


def test_permission_is_not_equipment_and_negative_is_bounded():
    runs = [r for name, r in document()['runs'].items() if name.startswith('gated')]
    assert len(runs) == 2
    for run in runs:
        assert run['gate_mask'] == 67108470
        if run['acquisition_only']:
            assert run['permission_mask'] == run['final_ability'] == 0 and run['last_frame'] == 2067
            assert run['acquisition_frame'] is run['corridor_frame'] is None
            assert not run['final_chest'] and not run['local_client']['messages']
        else:
            assert run['permission_mask'] == 1 << 20 and run['last_frame'] == 4490
            assert run['acquisition_frame'] == 1939 and run['final_chest']


def test_provenance_and_limits_are_explicit():
    doc = document()
    assert doc['source_commit'] == '0db01bdd5c91bd971993e59dc92f38572a33c908'
    assert doc['source_tree'] == 'b9aa0f9b3a0898d0ccba1b253104dd960b6f1064'
    assert doc['native_commit'] == '7d969fbce14fdc838d2c1ea01389717fb96c3189'
    assert doc['independent_report_sha256'] == 'a87abe1a9658c92b06cbed2a5619bc3bf7ad5773ba56576f6de2d3d89101823a'
    for key in ('private_manifest_sha256', 'independent_report_sha256'):
        assert len(doc[key]) == 64 and int(doc[key], 16) > 0
    assert doc['combat']['independently_reviewed'] and not doc['combat']['non_source_combat_dependency']
    assert not doc['combat']['frozen_platform_or_payload_dependency']
    assert '0x1000' in doc['combat']['non_source_hp_reductions'] and len(doc['limits']) == 7
    for suffix in ('acceptance.json', 'source-witness.md'):
        text = (ROOT / 'dev-docs' / f'cabbage-fighter-{suffix}').read_text()
        assert all(private not in text for private in ('/home/', '/Users/', 'C:\\'))
