"""Sanitized frozen v4 metadata contracts, not a native-ROM replay."""

import hashlib
import json
from pathlib import Path

from ..enemy_ability_data import ABILITY_NAME_TO_ID
from ..enemy_ability_runtime_patch import build_enemy_copy_runtime_patch_writes, build_enemy_source_runtime_config
from ..traversal import (
    CAPABILITY_ABILITIES, CAPABILITY_CONSUMED_ABILITIES,
    ROOM_SCOPED_ATTACK_WATER_STATES, ROOM_SCOPED_CAPABILITIES, SourcePolicy,
)
from .test_magic_switch import CAPABILITY, EVIDENCE, TARGET, evidence


def test_exact_full_pool_source_config_and_scoped_capability():
    e = evidence()
    raw = e['source_policy']
    assert e['packet_version'] == 4 and e['generation_seed'] == 12
    assert raw['seed'] == 16990593358183723736 and raw['mode'] == 1
    assert raw['mapping_style'] == 'per_enemy_type' and raw['ability_randomization_no_ability_weight'] == 0
    assert set(raw['allowed_abilities']) == set(ABILITY_NAME_TO_ID) - {'Normal', 'Master', 'Wait'}
    assert SourcePolicy(raw).grant('FOLEY', lambda _: True).guaranteed == frozenset({'Magic'})
    assert build_enemy_copy_runtime_patch_writes(raw)[0x35197E] == 21
    config = build_enemy_source_runtime_config(raw)
    assert int.from_bytes(config[8:12], 'little') & (1 << 2)  # Native Foley index 34.
    source = e['source']
    assert (source['template'], source['native_room'], source['native_xy'], source['native_type']) == (
        '0x088C2714', 533, [224, 64], 34)
    assert source['finite'] and source['normal_start_room'] == 590 and source['acquisition_frame'] == 4377
    target = e['target']
    assert target['id'] == TARGET and target['native_room'] == 533 and target['destination_room'] == 325
    assert (target['switch_template'], target['gate_template'], target['linked_slot'], target['parameter']) == (
        '0x088C26F0', '0x088C26CC', 1, 0)
    assert CAPABILITY_ABILITIES[CAPABILITY] == CAPABILITY_CONSUMED_ABILITIES[CAPABILITY] == frozenset({'Magic'})
    assert ROOM_SCOPED_CAPABILITIES[CAPABILITY] == 533 and ROOM_SCOPED_ATTACK_WATER_STATES[CAPABILITY] == 'dry'
    assert [key for key, values in CAPABILITY_ABILITIES.items() if 'Magic' in values] == [CAPABILITY]
    abilities = json.loads((Path(__file__).resolve().parents[1] / 'data/abilities.json').read_text())
    assert abilities['Magic'] == {'runtime_ability_id': 21, 'safe_to_gate': True}


def test_native_options_startup_write_fence_and_private_artifact_boundary():
    e = evidence()
    setup = e['setup']
    assert setup['ability_gating'] == setup['area_keys'] == 0
    assert setup['startup_room_position_fixture_only'] and not setup['full_new_game_to_hub4']
    assert setup['fresh_blank_battery_bytes'] == 32768 and setup['helpers_room'] == 101
    assert not setup['helpers_contribute_to533'] and setup['write_fence_closes_before_movement']
    assert not any(setup[k] for k in ('gameplay_ram_writes', 'runtime_rom_writes', 'state_restores'))
    writes = setup['client_config_writes']
    assert len(writes) == 8
    assert all(w['frame'] == 1085 and w['size'] == 4 and not w['guard_failed']
               and w['origin'] == 'KirbyAmClient._sync_enemy_copy_ability_runtime_config' for w in writes)
    raw = e['source_policy']
    expected = {0x0203B064: 1, 0x0203B068: raw['seed'] & 0xFFFFFFFF, 0x0203B06C: raw['seed'] >> 32,
                0x0203B070: 0, 0x0203B074: sum(1 << ABILITY_NAME_TO_ID[n] for n in raw['allowed_abilities']),
                0x0203B0B0: 0, 0x0203B0B4: 0, 0x0203B078: 0}
    assert {int(w['address'], 16): int.from_bytes(bytes.fromhex(w['value']), 'little') for w in writes} == expected
    assert len(setup['fixture_byte_differences']) == 15
    for diff in setup['fixture_byte_differences']:
        address = int(diff['offset'], 16)
        assert 0x2D8CB8 <= address < 0x2D8CC0 or 0x2D8CD0 <= address < 0x2D8CF0
    for path in (EVIDENCE, EVIDENCE.with_name('mustard-room15-magic-source-witness.md')):
        assert all(private not in path.read_text(encoding='utf-8') for private in ('/home/', '/Users/', 'C:\\'))
    hashes = list(e['private_artifact_sha256'].values()) + list(e['accepted_code_sha256'].values())
    hashes += [digest for build in e['production_hashes'].values() for digest in build.values()]
    hashes += [value for case in e['cases'] for key, value in case.items() if key.endswith('_sha256')]
    assert all(len(digest) == 64 and int(digest, 16) >= 0 for digest in hashes)
    assert 'exact private file bytes' in e['raw_hash_format']
    assert e['private_artifact_sha256']['roulette-calculation.json'] == hashlib.sha256(
        (json.dumps(e['selection']['source_recurrence'], indent=2) + '\n').encode()).hexdigest()


def test_all_44_cases_preserve_endpoint_layout_and_control_limits():
    e = evidence()
    coverage, cases = e['coverage'], e['cases']
    assert len(cases) == len({c['name'] for c in cases}) == coverage['native_cases'] == 44
    endpoints = [c for c in cases if c['name'].startswith('final-v4-')]
    waits = [c for c in cases if c['name'].startswith('v4-layout-delay')]
    assert len(endpoints) == coverage['endpoint_control_cases'] == 12
    assert len(waits) == coverage['ordinary_wait_positives'] == 32
    assert {(c['health'], c['hp'], c['control']) for c in endpoints} == {
        (health, hp, control) for health in (100, 500) for hp in (1, 6)
        for control in ('positive', 'no-cast', 'conversion')}
    assert {c['layout'] for c in endpoints if c['control'] == 'positive'} == {coverage['endpoint_layout']} == {3}
    assert {c['layout'] for c in waits} == {0, 1, 2, 3, 4}
    assert all(c['health'] == 100 and c['hp'] == 1 and c['control'] == 'positive' for c in waits)
    assert not coverage['all_health_layout_combinations_tested'] and not coverage['alternate_mode_native_tested']
    assert sum(c['control'] == 'positive' for c in cases) == coverage['positive_cases'] == 36
    for control, field in [('no-cast', 'no_cast_controls'), ('conversion', 'conversion_controls')]:
        assert sum(c['control'] == control for c in cases) == coverage[field] == 4
    for case in cases:
        assert case['hp_min'] == case['hp_max'] == case['hp']
        assert case['first_hp_frame'] == 1085 and case['hp_samples'] == case['final_frame'] - 1084
        assert case['source_hp'] == (2 if case['health'] == 100 else 10)
        assert case['configuration_write_count'] == 8
        assert not any(case[k] for k in ('gameplay_ram_writes', 'runtime_rom_writes', 'state_restores'))
        if case['control'] == 'positive':
            assert case['final_room'] == 325 and case['final_ability'] == 0
            assert case['cue']['frame'] < case['outcome_frame'] < case['meta_creation'] < case['first_contact']
            assert case['first_contact'] == case['third_contact']
            assert case['third_contact'] < case['normal_frame'] < case['cross_frame'] < case['arrival_frame']
            assert 886 <= case['after_press_icon_angle'] <= 1013
        elif case['control'] == 'no-cast':
            assert case['final_room'] == 533 and case['final_ability'] == 21
            assert case['input_differences'] == [[4474, 2, 0]]
        else:
            assert case['final_room'] == 533 and case['final_ability'] == 0
            assert case['input_differences'] == [[4534, 1, 0], [4541, 0, 1]]


def test_exact_cast_contact_consumption_and_normal_gate_crossing():
    e = evidence()
    assert e['pose'] == {'xy': [170.21875, 135.80859375], 'settled_camera': [50.21875, 55.80859375],
                         'carry_start_xy': [245.51953125, 72.99609375], 'carry_left_frames': 70}
    frames = e['baseline_frames']
    assert [frames[k] for k in ('entry534', 'entry533', 'live_source', 'acquisition', 'cast_input')] == [
        1157, 2697, 4162, 4377, 4474]
    assert [frames[k] for k in ('visual_cue_and_A', 'outcome_meta_knight', 'effect_creation',
                                'first_and_third_sweep_contact', 'consumed_to_normal', 'normal_crossing',
                                'arrival325', 'settled')] == [4534, 4660, 4723, 4862, 4894, 4941, 5221, 5269]
    assert frames['gate_starts_opening'] == 4864
    assert frames['gate_fully_open'] == 4907 and frames['gate_starts_closing'] == 4908
    assert frames['gate_starts_closing'] < frames['normal_crossing'] < frames['gate_closed'] == 4951
    effect = e['effect']
    assert effect['task'] == '0x08083B05' and effect['parent'] == effect['kirby2'] == '0x02020EE0'
    assert effect['local_player'] == 0 and effect['room'] == 533
    assert effect['category_includes'] == '0x2000' and effect['category_excludes'] == '0x8000'
    assert effect['contact_counter'] == 140 and effect['contact_center_x'] == 306.21875
    assert effect['switch_contact_flag'] == '0x40000'


def test_visible_selection_source_recurrence_is_not_alternate_mode_native_acceptance():
    selection = evidence()['selection']
    assert selection['decision_inputs'] == ['rendered_pixels']
    assert set(selection['diagnostic_only']) == {'layout', 'angle', 'RNG', 'outcome', 'ability'}
    assert set(selection['ordinary_layout_selector']) == set(selection['native_accepted_layouts']) == {0, 1, 2, 3, 4}
    assert selection['alternate_layout_selector'] == [5, 6, 7, 5]
    assert selection['source_only_layouts'] == [5, 6, 7]
    assert '320 neutral' in selection['fixed_recovery'] and '120 Up+Left' in selection['fixed_recovery']
    calculation = selection['source_recurrence']

    def stop(angle):
        speed = 320
        for _ in range(250):
            angle = (angle + (speed >> 4)) % 1024
            speed = max(16, speed - 4)
            if speed == 16 and angle % 128 == 0:
                return ((768 - angle) // 128) % 8
        raise AssertionError('Source recurrence did not settle')

    assert [a for a in range(1024) if stop(a) == 0] == list(range(886, 1014))
    assert len(calculation['layouts']) == 8
    for index, layout in enumerate(calculation['layouts']):
        candidates = [n for n in range(1, 101) if layout[stop(20 * n % 1024)] == 4]
        assert candidates
        assert calculation['all_layout_candidates'][index] == {'layout': index, 'stop_updates': candidates}
    assert any('source recurrence only' in limit for limit in evidence()['limitations'])
