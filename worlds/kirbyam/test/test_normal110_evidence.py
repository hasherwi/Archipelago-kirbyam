"""Frozen Normal110 scalar contracts; not emulator replays or approval of publication."""
import json
from pathlib import Path

import pytest

from ..data import load_json_data
from ..traversal import CAPABILITY_ABILITIES, ROOM_SCOPED_ATTACK_WATER_STATES
from ..traversal_data import room_traversal_targets
from .support.normal110_history import before_normal110

ROOT = Path(__file__).parents[1]
EVIDENCE = ROOT / 'dev-docs/rainbow-normal110-acceptance.json'


def evidence():
    return json.loads(EVIDENCE.read_text())


def test_exact_payload_entry_action_and_continuation():
    e = evidence()
    assert e['production_commit'] == '714a06f8794076e3261062344dfad8f3810d6898'
    assert e['production_tree'] == '49a999340b61aa144c3e77118c8ee3ec7c9a41c7'
    assert e['native_commit'] == '7d969fbce14fdc838d2c1ea01389717fb96c3189'
    assert e['independent_entry'] == 'REGION_RAINBOW_ROUTE/ROOM_1_06_LOWER_MID'
    assert e['entry_door_rom_offset'] == '0x0087847A'
    assert e['entry_door_record'] == '03ff22120e00ffff6e00070800ff'
    assert '503' in e['excluded_entrance']
    assert e['payload'] == {
        'source_key': 'SWORD_KNIGHT', 'identity': '0x088B74CC', 'type': 26,
        'xy': [120, 215.99609375], 'capture_frame': 1443, 'spit_frame': 1580,
        'upper_targets': [[14, 21], [11, 26]], 'pending_is_not_equipment': True,
        'finite': True, 'renewable': False, 'swallowed': False,
    }
    assert load_json_data('abilities.json')['Normal'] == {
        'runtime_ability_id': 0, 'safe_to_gate': False, 'enemy_copy_allowed': False}
    for name, medium in [('bomb_110_upper_normal_spit', 'dry'),
                         ('bomb_110_room9_underwater_normal_spray', 'swimming')]:
        assert CAPABILITY_ABILITIES[name] == {'Normal'}
        assert ROOM_SCOPED_ATTACK_WATER_STATES[name] == medium


@pytest.mark.parametrize('index', range(18))
def test_frozen_runtime_scalar_row(index):
    r = evidence()['runs'][index]
    assert r['hp_min'] == r['hp_max'] == r['options']['minimum_health'] == r['options']['maximum_health']
    assert (r['hp_samples'], r['frames']) == (2488, 3572)
    assert r['all_equipped_normal'] and r['no_swallow_or_copy_animation']
    assert not r['gameplay_ram_writes'] and not r['state_restores']
    assert r['entry'] == {'frame': 1218, 'room': 110, 'x': 104.0, 'y': 120.99609375, 'ability': 0}
    assert r['all110_selective_12_50_sealed']
    assert r['final']['ability'] == r['final']['mouth_ability'] == 0
    assert r['final']['hp'] == r['hp_min'] and r['final']['ability_unlocks'] == '0x0'
    assert len(r['configuration_writes']) == 8 + r['options']['area_keys']
    assert all(w['frame'] == 1085 and not w['guard_failed'] for w in r['configuration_writes'])
    for write in r['configuration_writes']:
        assert write['origin'] == ('KirbyAmClient._sync_area_key_runtime_config'
                                   if write['address'] == '0x203b0c0'
                                   else 'KirbyAmClient._sync_enemy_copy_ability_runtime_config')
    assert r['final']['area_keys'] == ('0x4' if r['options']['area_keys'] else '0x0')
    if r['control']:
        assert r['matched_prefix_through2785'] and r['hit'] is None and r['first554_frame'] is None
        assert r['hit_effects'] == [] and r['final']['room'] == 110
    else:
        assert r['hit'] == {'frame': 2788, 'room': 110, 'x': 174.09375, 'y': 926.73046875,
                            'water': True, 'ability': 0, 'animation': 66}
        assert r['first554_frame'] == 3493 and r['final']['room'] == 554 and not r['final']['water']
        effect, = r['hit_effects']
        assert (effect['parent'], effect['category'], effect['animation'], effect['variant']) == (
            '0x2020ee0', '0x30000043', '0x2e', 0)
        assert effect['bounds'] == [-8, -12, 12, 10]
        assert effect['damage_box'] == [-8, -12, 10, 11]
        assert [effect['x'], effect['y']] == [197.2734375, 926.73046875]
    assert all(len(h) == 64 and int(h, 16) >= 0 for h in r['artifact_sha256'].values())


def test_health_partition_copy_pending_and_exclusions_are_explicit():
    e = evidence()
    assert (e['cold_runs'], e['positive_runs'], e['matched_controls']) == (18, 12, 6)
    assert e['cold_repeat100_every_sample_equal']
    assert 'Not a normal globalAI300 replay' in e['startup_helper_qualification']
    assert e['provenance_correction']['address'] == '0x203b0c0'
    positives = [r for r in e['runs'] if not r['control']]
    assert {(r['options']['minimum_health'], r['options']['enemy_health_multiplier']) for r in positives} == {
        (1, 50), (1, 100), (1, 124), (1, 125), (1, 500), (6, 100), (6, 500)}
    assert {(r['options']['ability_randomization_mode'], r['options']['ability_gating']) for r in positives} == {
        (0, 0), (1, 0), (1, 1), (2, 0), (2, 1)}
    obstacle = e['optional_obstacle']
    assert obstacle['identity'] == '0x088B7484' and obstacle['spit_direction'] == 'left'
    assert obstacle['death_percent_range'] == [50, 124] and obstacle['survives_percent_range'] == [125, 500]
    assert not obstacle['independent_copy_source']
    assert {(t['frame'], t['mouth_ability']) for r in positives for t in r['mouth_transitions']
            if t['frame'] == 1443} == {(1443, 0), (1443, 6), (1443, 8), (1443, 18)}
    for r in positives:
        assert all(t['mouth_ability'] == 0 for t in r['mouth_transitions'] if t['frame'] in (1580, 1814))
        assert r['copy_event_max'] == (2 if r['options']['ability_randomization_mode'] == 2 else 0)
    assert any('original500 Waddle swallow' in limit for limit in e['limitations'])
    assert any('not451' in limit for limit in e['limitations'])


def test_public_packet_is_compact_and_old_target_physics_are_retained():
    e = evidence()
    assert e['private_packet_sha256']['final-manifest.json'] == (
        '5cccc724d14c485dfc0eb3925db1cbe8996057ffcfdc029a0c16a2767501097e')
    for path in (EVIDENCE, EVIDENCE.with_name('rainbow-normal110-source-witness.md')):
        assert all(value not in path.read_text() for value in ('/home/', '/Users/', 'C:\\', 'D:\\'))
    assert not any(key in e for key in ('inputs', 'per-frame', 'savestate', 'raw_memory'))
    row = next(r for r in room_traversal_targets('block') if r['id'] == 'bomb_110_room9')
    before = before_normal110(row)
    assert set(before['graphs']) == {'upper_entry', 'upper_entry_sword'}
    assert before['requires_any_guaranteed_source'] == [
        {'source_key': 'SPARKY', 'ability': 'Spark'}, {'source_key': 'SWORD_KNIGHT', 'ability': 'Sword'}]


def test_accepted_helper_supplement_keeps_fixture_and_attribution_limits():
    e = evidence()
    assert e['review_status'] == 'independently_accepted_bounded_native_evidence'
    assert e['independent_review_sha256'] == {
        'final-review.md': 'c1e91c1b6238e1dfb3baa4eb98d8c90fd8882df7b8c3cd0bde74dd04bd1f36b8',
        'final-review-data.json': '3a595004a2e9bc4afcdd198427e77cc5f0b365adb3677b2acb16b6b1eb78d59f',
        'helper-supplement-review.md': '852c721a2e581da4c7ab302bd6187a8ba4ee133fef209cd37c89c3cff3bf6da0',
        'helper-supplement-review-data.json': '1bb9dbcec17f296ecc498dc68e4780345cbaa2d114d5e71761a29f5e50e4605c',
        'review-manifest.json': '28cd3b98846404162e63d38c3759425395479443d0948ee3c0b5de43e475d3c0',
    }
    s = e['helper_supplement']
    assert s['manifest_sha256'] == '9919d805dc4909f381e91738e4b09cbad07075bc585bd85967cc98ed950b59f5'
    assert s['samples'] == 2488 and s['human_samples_equal_frozen500']
    assert s['ai_state'] == s['gameplay_ram_writes'] == s['ai_state_writes'] == s['state_restores'] == 0
    assert (s['target_hit_frame'], s['first554_frame'], s['target_effect_parent']) == (2788, 3493, '0x02020EE0')
    assert s['original_artifacts_unchanged'] == 96 and s['original_private_dependencies_unchanged'] == 7
    assert s['first100_artifacts_unchanged']
    assert [(a['index'], a['rooms'], a['abilities']) for a in s['actors']] == [
        (0, [108, 110, 554], [0]), (1, [101], [0, 19]), (2, [101], [0]), (3, [101], [0])]
    assert all(a['live_task_samples'] == 2488 and a['distinct_positions'] > 1 for a in s['actors'])
    assert 'eligibility, not callback execution' in s['task_qualification']
    assert s['registry_correction'] == {
        'nonzero_kind1_frames': list(range(1218, 1227)), 'entries_per_nonzero_sample': 3,
        'entry_room': 108, 'entry_parent': '0x0', 'kind2_attack_count_always_zero': True,
    }
    assert 'do not prove attack absence' in s['registry_qualification']
    assert 'not a complete live-attack census' in s['registry_qualification']
