"""Sanitized UFO517 scalar contracts; these tests do not rerun the emulator."""

from ..client import KirbyAmClient
from ..enemy_ability_data import ABILITY_NAME_TO_ID
from ..enemy_ability_runtime_patch import build_enemy_copy_runtime_patch_writes, build_enemy_source_runtime_config
from ..traversal import SourcePolicy
from .test_cabbage_ufo import ROOT, document


def test_native_assignment_source_target_and_setup():
    doc = document()
    raw = doc['source_policy']
    assert doc['generation_seed'] == 52 and raw['seed'] == 8531114801390986422
    assert raw['mode'] == 1 and raw['mapping_style'] == 'per_enemy_type'
    assert set(raw['allowed_abilities']) == set(ABILITY_NAME_TO_ID) - {'Normal', 'Master', 'Wait'}
    assert build_enemy_copy_runtime_patch_writes(raw)[0x3517FE] == 14
    assert int.from_bytes(build_enemy_source_runtime_config(raw)[4:8], 'little') & (1 << 18)
    assert SourcePolicy(raw).grant('WADDLE_DOO', lambda _: True).guaranteed == frozenset({'UFO'})
    assert doc['source'] == {'template': '0x088CA04C', 'native_type': 18, 'native_copy': 7,
                             'native_xy': [528, 264], 'finite': True, 'renewal': False, 'acquisition_frame': 1939}
    assert doc['target'] == {'capability': 'bomb_517_ufo_top_charge', 'graph': 'hub2_ufo_entry',
                             'location': 'MINOR_CHEST_SPRAY_PAINT_12', 'location_id': 3960511, 'room': 517,
                             'f1': [14, 7], 'f1_rect': [224, 112, 239, 127], 'linked_cells': 7,
                             'chest': 57, 'template': '0x088CA0B8'}
    setup = doc['setup']
    assert setup['predecessor'] == 591 and setup['initial_ability'] == 'Normal' and setup['helpers_room'] == 101
    assert setup['independent_hub2_access_assumed'] and setup['startup_fixture_only']
    assert setup['configuration_write_count'] == 8 and setup['configuration_frame'] == 1085
    assert setup['later_gameplay_writes'] == 0 and not setup['initial_state_restored']
    assert (setup['fresh_save_bytes'], setup['fresh_save_fill']) == (32768, 255)
    assert KirbyAmClient()._build_minor_chest_source_ptr_map()[0x8CA0B8] == 3960511


def test_endpoint_matrix_survives_and_collects_only_after_maximum_shot():
    doc = document()
    endpoints = [run for name, run in doc['runs'].items()
                 if name.startswith('qualified') and name.endswith(('positive', 'control'))]
    assert len(endpoints) == 8
    assert {(r['hp'], r['enemy_health'], r['positive']) for r in endpoints} == {
        (hp, enemy, positive) for hp in (1, 6) for enemy in (100, 500) for positive in (True, False)}
    assert len(doc['runs']) == 12
    for run in doc['runs'].values():
        assert run['first_frame'] == 1085
        assert (run['last_frame'], run['sample_count']) == ((2067, 983) if run['acquisition_only'] else (3403, 2319))
        assert run['hp_min'] == run['hp_max'] == run['hp']
        assert run['source_hp'] == run['enemy_health'] // 25
        assert (run['ingress_frame'], run['mouth_full_frame'], run['source_last_active_frame']) == (1109, 1850, 1850)
        assert not run['local_client']['server_submission']
        if not run['acquisition_only']:
            assert (run['acquisition_frame'], run['corridor_frame'], run['final_ability']) == (1939, 2016, 14)
        if run['positive']:
            assert (run['target_frame'], run['linked_complete_frame'], run['chest_frame']) == (2873, 2903, 3345)
            assert run['final_target'] == 0 and run['final_linked'] == [0] * 7
            assert run['final_chest'] and run['final_event_count'] == 1
            assert run['local_client']['messages'] == [{'cmd': 'LocationChecks', 'locations': [3960511]}]
        else:
            assert run['target_frame'] is run['linked_complete_frame'] is run['chest_frame'] is None
            assert run['final_target'] == 241 and run['final_linked'] == [242] * 7
            assert not run['final_chest'] and run['final_event_count'] == 0 and not run['local_client']['messages']
    assert doc['control'] == {'omitted_B_half_open': [2701, 2861], 'common_state_through': 2701,
                              'full_target_omission_controls': 4, 'full_lower_charge_controls': 2,
                              'no_permission_acquisition_only': True}


def test_actual_charge_release_scan_box_and_chain_parent():
    positives = [r for r in document()['runs'].values() if r['positive']]
    for run in positives:
        charge = run['charge']
        assert charge['hold_half_open'] == [2701, 2861]
        assert [(c['frame'], c['counter'], c['animation']) for c in charge['milestones']] == [
            (2715, 1, 21), (2752, 2, 22), (2813, 3, 23), (2861, 3, 23)]
        assert {c['state'] for c in charge['milestones']} == {'0x806d0f5'}
        assert (charge['release_frame'], charge['release_animation'], charge['release_state']) == (
            2862, 31, '0x806dbcd')
        assert charge['release_phase'] == list(range(1, 8)) and charge['end_of_frame_recoil'] == [0] * 7
        attack = run['attack']
        assert int(attack['parent'], 16) == 0x02020EE0 and int(attack['task_fn'], 16) == 0x08070581
        assert int(attack['mask'], 16) == 0x20001103 and int(attack['flags'], 16) == 0xA0084102
        assert int(attack['flags'], 16) & 0x80000100 == 0x80000100
        assert attack['scan_box'] == [-6, -4, 6, 4] and attack['integer_rect'] == [213, 118, 225, 126]
        assert attack['damage_box'] == [-16, -14, 13, 14] and attack['damage_box'] != attack['scan_box']
        assert attack['callbacks'] == ['0x0', '0x0', '0x0', '0x8084edd']
        assert (attack['anim_id'], attack['variant']) == (0x198, 0) and attack['chain_parent_matches']
        assert (attack['x'], attack['y']) == (219.99609375, 122.99609375)
        assert [p['frame'] for p in run['trajectory']] == list(range(2870, 2874))
        assert [p['x'] for p in run['trajectory']] == [201.99609375, 207.99609375, 213.99609375, 219.99609375]
        assert {p['y'] for p in run['trajectory']} == {122.99609375}
        assert run['trajectory'][0]['flags'] == '0xa0004100'
        assert [c['frame'] for c in run['carry']] == [2007, 2016, 2201, 2272, 2329, 2569, 2681, 2701]
        assert {c['ability'] for c in run['carry']} == {14}
        assert run['carry'][-1]['xy'] == [185.99609375, 120.99609375]
        assert all(d['template'] == '0x88ca04c' or (d['after'] == 1 and d['removal'])
                   for d in run['original_hp_transitions'])


def test_distinct_low_and_medium_shots_stop_at_wall():
    runs = document()['runs']
    for label, hold, counter, animation, spawn, callback, scan in [
        ('low', 30, 1, 0x199, 2735, '0x807c1a1', [-1, -1, 1, 1]),
        ('medium', 80, 2, 0x19A, 2788, '0x8084c21', [-6, -4, 6, 4]),
    ]:
        run = runs[f'qualified100-1hp-{label}']
        lower = run['lower_charge']
        assert not run['positive'] and not run['acquisition_only']
        assert (lower['hold_frames'], lower['counter'], lower['animation']) == (hold, counter, 20 + counter)
        assert lower['release_frame'] == 2701 + hold and lower['absent_frame'] == spawn + 2
        assert [s['frame'] for s in lower['shots']] == [spawn, spawn + 1]
        for shot in lower['shots']:
            assert shot['anim_id'] == animation and shot['scan_box'] == scan
            assert shot['callbacks'][2] == callback and not int(shot['flags'], 16) & 0x100
            assert shot['x'] + scan[2] < 224
        assert int(lower['shots'][-1]['flags'], 16) & 0x1000


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
            assert run['permission_mask'] == 1 << 14 and run['last_frame'] == 3403
            assert run['acquisition_frame'] == 1939 and run['final_chest']


def test_provenance_is_distinct_and_exploratory_failure_is_excluded():
    doc = document()
    assert doc['generation_local_commit'] == '3ebb8a2c8db87dc23a5de28c6a9fbd57a3061f07'
    assert doc['generation_public_tree_equivalent_commit'] == '0db01bdd5c91bd971993e59dc92f38572a33c908'
    assert doc['generation_tree'] == 'b9aa0f9b3a0898d0ccba1b253104dd960b6f1064'
    assert doc['integration_local_base'] == '10060925eaa7a4bcaf6e0e96f8f2f23a0b4a9345'
    assert doc['integration_public_tree_equivalent_base'] == '974a15d2cc30bd8a75f630e04ba8d0cf8ca44f0c'
    assert doc['integration_base_tree'] == '702046c2addbe5c90bd5968ea1c3443c17850be3'
    assert doc['native_commit'] == '7d969fbce14fdc838d2c1ea01389717fb96c3189'
    assert doc['private_manifest_sha256'] == '3071e0369137e672f5584189eb91bc8884bdc1a4d94bf81465174705696183b6'
    assert doc['independent_report_sha256'] == '1f73e8582eb15fc7617e4a50f34c84c1b000c87bbc4965bf1a5ed74858fe2acc'
    assert doc['combat']['independently_reviewed'] and not doc['combat']['non_source_combat_dependency']
    assert not doc['combat']['frozen_platform_or_payload_dependency'] and len(doc['limits']) == 9
    assert 'Died' in doc['excluded_diagnostics']['final100-1hp-control']
    assert all(name.startswith(('qualified', 'gated')) for name in doc['runs'])
    assert len(doc['builds']) == 5 and len(doc['input_sha256']) == 3
    for run in doc['runs'].values():
        assert set(run['hashes']) == {'states.json', 'commands.json', 'runtime.json', 'tile-deltas.json', 'client.json'}
        assert all(len(h) == 64 and int(h, 16) > 0 for h in run['hashes'].values())
    for build in doc['builds'].values():
        assert build['fixture_changed_bytes'] == 15
        assert all(len(h) == 64 and int(h, 16) > 0 for h in build['sha256'].values())
    for suffix in ('acceptance.json', 'source-witness.md'):
        text = (ROOT / 'dev-docs' / f'cabbage-ufo-{suffix}').read_text()
        assert all(private not in text for private in ('/home/', '/Users/', 'C:\\', 'copy_context', 'initial_save'))
