"""Validate retained acceptance metadata, without replaying private ROM artifacts."""

import json
from pathlib import Path

from ..traversal import SourcePolicy

EVIDENCE = Path(__file__).parents[1] / 'dev-docs' / 'rainbow-route-8-sword-runtime.json'


def test_source_entry_and_attached_underwater_target_are_exact():
    evidence = json.loads(EVIDENCE.read_text())
    source = evidence['source']
    assert (source['template_rom_offset'], source['spawn_table'], source['type'], source['source_key']) == (
        '0x008B74CC', 1, '0x1A', 'SWORD_KNIGHT')
    assert source['native_position'] == [120, 216] and source['copy_field'] == 18
    assert source['acquisition_frame'] == 1359
    assert SourcePolicy({'mode': 0}).grant('SWORD_KNIGHT', lambda _: True).guaranteed == {'Sword'}
    entry = evidence['entry']
    assert (entry['source_native_room'], entry['destination_native_room']) == (108, 110)
    assert entry['source_ap_region'] == 'REGION_RAINBOW_ROUTE/ROOM_1_06_LOWER_MID'
    assert entry['door_record_rom_offset'] == '0x0087847A'
    assert entry['trigger_tile'] == [34, 18] and entry['spawn_tile'] == [7, 8]
    assert entry['decoded_arrival'] == [104, 120.99609375]
    assert 'not replayed' in entry['scope']
    target = evidence['target']
    assert (target['room'], target['tile'], target['native_destination']) == (110, [13, 57], 554)
    assert (target['collision_before'], target['collision_after'], target['intervening_solid_column']) == (
        '0xF1', '0x00', 12)
    assert (target['kirby_state'], target['weapon_animation'], target['weapon_variant']) == ('0x69', '0x6F', 1)
    assert target['medium'] == 'underwater'
    assert target['first_hit_bounds'] == [0, -26, 25, -3]
    assert target['integer_scan_columns'] == [11, 13] and target['integer_scan_rows'] == [56, 57]


def test_five_no_hit_runs_and_three_matched_controls_keep_discrete_health_scope():
    evidence = json.loads(EVIDENCE.read_text())
    assert evidence['tested_enemy_health_values'] == [50, 100, 500]
    assert {(r['options']['minimum_health'], r['options']['enemy_health_multiplier'])
            for r in evidence['runs']} == {(1, 50), (1, 100), (1, 500), (6, 100), (6, 500)}
    controls = []
    for run in evidence['runs']:
        options = run['options']
        assert options['ability_randomization_mode'] == options['ability_gating'] == options['area_keys'] == 0
        assert run['hp_min'] == run['hp_max'] == options['minimum_health'] == options['maximum_health']
        assert run['frames'] == 3467 and run['hp_samples'] == 2383
        hit = run['target_hit']
        assert hit['frame'] == (2889 if options['enemy_health_multiplier'] == 500 else 2886)
        assert (hit['room'], hit['water'], hit['ability'], hit['animation']) == (110, True, 18, 0x69)
        assert hit['targets']['13,57'] == 0 and hit['targets']['12,50'] == 0xF1
        weapon = run['registered_weapon_at_hit']
        assert weapon['parent'] == '0x2020ee0' and weapon['animation'] == '0x6f' and weapon['variant'] == 1
        assert weapon['bounds'] == weapon['sprite_box'] == [0, -26, 25, -3]
        assert weapon['damage_box'] == [0, 0, 0, 0]
        transitions = run['water_transitions']
        crossed = next(point for point in transitions if point['room'] == 554)
        assert crossed['frame'] == 3388 and crossed['ability'] == 18
        assert transitions[-1]['water'] is False and transitions[-1]['frame'] == 3398
        control = run['matched_control']
        if options['minimum_health'] == 1:
            controls.append(control)
            assert control['prefix_identical_through_frame'] == 2882
            assert control['hp_min'] == 1 and control['frames'] == 3467
            assert control['final']['room'] == 110 and control['final']['ability'] == 18
            assert control['final']['targets']['13,57'] == 0xF1
        else:
            assert control is None
    assert len(controls) == 3
    difference = evidence['replay']['control_difference']
    assert difference['positive'] == {'start': 2882, 'frames': 30, 'keys': 2}
    assert difference['control'] == {'start': 2882, 'frames': 30, 'keys': 0}


def test_only_eight_guarded_configuration_writes_precede_movement():
    evidence = json.loads(EVIDENCE.read_text())
    assert evidence['replay']['gameplay_ram_writes'] == evidence['replay']['state_restores'] == 0
    expected = {
        0x0203B064: 0, 0x0203B068: 0, 0x0203B06C: 0, 0x0203B070: 55,
        0x0203B074: 0x03FFFFFE, 0x0203B0B0: 0, 0x0203B0B4: 0, 0x0203B078: 0,
    }
    for run in evidence['runs']:
        writes = run['configuration_writes']
        assert len(writes) == 8
        assert {int(w['address'], 16): int.from_bytes(bytes.fromhex(w['value']), 'little')
                for w in writes} == expected
        assert all(w['frame'] == 1085 and w['size'] == 4 and w['guard_failed'] is False
                   and w['origin'] == 'KirbyAmClient._sync_enemy_copy_ability_runtime_config' for w in writes)
        offsets = [int(row['offset'], 16) for row in run['fixture_byte_diff']]
        assert offsets == list(range(0x2D8CB8, 0x2D8CC0)) + [
            0x2D8CD1, 0x2D8CD5, 0x2D8CD9, 0x2D8CDD, 0x2D8CE1, 0x2D8CE5, 0x2D8CED]
    old, = [r for r in evidence['runs'] if r['options']['enemy_health_multiplier'] == 100
            and r['options']['minimum_health'] == 1]
    assert old['build_commit'] == '8dbf941f30f88f8d0f151e2a556d31ca19aa6ac5'
    assert all(r['build_commit'] == 'b98feba7d5b771919ab8f0ad642c11570e3c6427'
               for r in evidence['runs'] if r is not old)


ENTRY_EVIDENCE = EVIDENCE.with_name('rainbow-route-8-sword-entry-runtime.json')


def test_actual_entry_supplement_preserves_original_production_and_scope():
    original = json.loads(EVIDENCE.read_text())
    supplement = json.loads(ENTRY_EVIDENCE.read_text())
    assert supplement['original_acceptance_sha256'] == original['source_packet_sha256']
    assert supplement['source_packet_sha256'] == 'c32f298c8cae021c3075b334e91da1cee4cf32ff4a36c1391d306045416a53fd'
    assert len(original['runs']) == 5 and original['replay']['first_554_frame'] == 3388
    reused, = [run for run in original['runs'] if run['options']['minimum_health'] == 1
               and run['options']['enemy_health_multiplier'] == 100]
    assert supplement['production_sha256'] == reused['production_sha256']
    assert supplement['build']['repo_commit'] == reused['build_commit']
    assert supplement['options'] == supplement['build']['options'] == reused['options']
    assert supplement['options']['enemy_health_multiplier'] == 100
    assert supplement['options']['minimum_health'] == supplement['options']['maximum_health'] == 1
    offsets = [int(row['offset'], 16) for row in supplement['build']['fixture_byte_diff']]
    assert offsets == list(range(0x2D8CB8, 0x2D8CC0)) + [
        0x2D8CD1, 0x2D8CD2, 0x2D8CD5, 0x2D8CD6, 0x2D8CD9,
        0x2D8CDD, 0x2D8CE1, 0x2D8CE5, 0x2D8CED]
    assert '/home/' not in ENTRY_EVIDENCE.read_text()


def test_actual_entry_source_underwater_hit_and_completed_exit():
    evidence = json.loads(ENTRY_EVIDENCE.read_text())
    entry = evidence['entry']
    assert entry['ap_compartment'] == 'REGION_RAINBOW_ROUTE/ROOM_1_06_LOWER_MID'
    assert entry['door_rom_offset'] == '0x0087847A'
    assert entry['trigger_tile'] == [34, 18] and entry['spawn_tile'] == [7, 8]
    startup = entry['startup_pose']
    assert (startup['frame'], startup['room'], startup['x'], startup['y'], startup['water']) == (
        1085, 108, 504, 277, False)
    press = entry['door_press']
    assert (press['frame'], press['room'], press['animation']) == (1207, 108, 42)
    first = entry['first110']
    assert (first['frame'], first['room'], first['x'], first['y'], first['ability']) == (
        1218, 110, 104, 120.99609375, 0)
    observed = entry['settled_source_observation']
    assert observed['frame'] == 1238
    source, = observed['template_observations']
    assert (source['template'], source['type'], source['copy'], source['hp']) == ('0x88b74cc', 26, 18, 4)
    assert (evidence['acquisition']['frame'], evidence['acquisition']['ability']) == (1512, 18)
    hit = evidence['target_hit']
    assert (hit['frame'], hit['room'], hit['water'], hit['animation']) == (3039, 110, True, 0x69)
    assert hit['targets']['13,57'] == 0 and hit['targets']['12,50'] == 0xF1
    weapon = evidence['registered_weapon_at_hit']
    assert (weapon['parent'], weapon['animation'], weapon['variant']) == ('0x2020ee0', '0x6f', 1)
    assert weapon['bounds'] == [0, -26, 25, -3]
    assert (evidence['first554']['frame'], evidence['first554']['room']) == (3541, 554)
    final = evidence['final']
    assert (final['frame'], final['room'], final['ability'], final['hp']) == (3620, 554, 18, 1)
    assert evidence['water_transitions'][-1]['frame'] == 3551 and final['water'] is False


def test_supplement_control_and_configuration_only_writes():
    original = json.loads(EVIDENCE.read_text())
    evidence = json.loads(ENTRY_EVIDENCE.read_text())
    assert evidence['configuration_writes'] == original['runs'][0]['configuration_writes']
    assert len(evidence['configuration_writes']) == 8
    assert evidence['gameplay_ram_writes'] == evidence['state_restores'] == 0
    assert evidence['hp_min'] == evidence['hp_max'] == 1
    assert evidence['hp_samples'] == evidence['frames'] - 1085 + 1 == 2536
    control = evidence['control']
    assert control['identical_prefix_through'] == 3035
    assert control['difference'] == (
        'Only frame3035 30-frame B target attack is omitted; all other controller inputs identical.')
    assert control['target_sealed_all_native110_frames'] is control['never554'] is True
    final = control['final']
    assert (final['frame'], final['room'], final['ability'], final['hp']) == (3620, 110, 18, 1)
    assert final['targets']['13,57'] == 0xF1
