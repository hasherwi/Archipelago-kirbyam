"""Sanitized immutable Cupid packet contracts; these tests do not replay a ROM."""

import hashlib
import json
from pathlib import Path

from ..enemy_ability_data import ABILITY_NAME_TO_ID
from ..enemy_ability_runtime_patch import build_enemy_copy_runtime_patch_writes, build_enemy_source_runtime_config
from ..enemy_health_scaling import scale_hp_value
from ..traversal import CAPABILITY_ABILITIES, ROOM_SCOPED_CAPABILITIES, SourcePolicy
from .test_cupid_map310 import CAPABILITY, EVIDENCE, LOCATION, TARGET
from .test_yellow_ufo_upstream_evidence import lf_text_sha256


def evidence():
    return json.loads(EVIDENCE.read_text(encoding='utf-8'))


def test_exact_source_policy_native_configuration_and_publication_boundary():
    e = evidence()
    assert e['generation_seed'] == 63 and e['source_policy']['seed'] == 7582041893722069666
    raw = e['source_policy']
    assert raw['mode'] == 1 and raw['mapping_style'] == 'per_enemy_type'
    assert set(raw['allowed_abilities']) == set(ABILITY_NAME_TO_ID) - {'Normal', 'Master', 'Wait'}
    assert SourcePolicy(raw).grant('TWISTER', lambda _: True).guaranteed == frozenset({'Cupid'})
    assert build_enemy_copy_runtime_patch_writes(raw)[0x3518EE] == 19
    assert int.from_bytes(build_enemy_source_runtime_config(raw)[4:8], 'little') & (1 << 28)
    source = e['source']
    assert source['template'] == '0x088B59B4' and source['native_xy'] == [144, 280]
    assert source['finite'] and source['native_room'] == 534 and source['normal_start_room'] == 590
    assert (e['target']['id'], e['target']['location'], e['target']['location_id']) == (TARGET, LOCATION, 3960205)
    assert CAPABILITY_ABILITIES[CAPABILITY] == frozenset({'Cupid'}) and ROOM_SCOPED_CAPABILITIES[CAPABILITY] == 310
    setup = e['setup']
    assert not any(setup[k] for k in (
        'full_route_gating', 'area_keys', 'gameplay_ram_writes', 'runtime_rom_writes',
        'state_restores', 'server_submission', 'helper_parent_attacks_in310', 'helpers_inert'))
    assert setup['helpers_room'] == 101 and setup['normal_entry_fixture_only']
    assert len(setup['fixture_byte_differences']) == 15
    writes = setup['client_config_writes']
    assert len(writes) == 8
    assert all(w['frame'] == 1085 and w['size'] == 4 and not w['guard_failed']
               and w['origin'] == 'KirbyAmClient._sync_enemy_copy_ability_runtime_config' for w in writes)
    seed = raw['seed']
    expected = {0x0203B064: 1, 0x0203B068: seed & 0xFFFFFFFF, 0x0203B06C: seed >> 32,
                0x0203B070: 0, 0x0203B074: sum(1 << ABILITY_NAME_TO_ID[n] for n in raw['allowed_abilities']),
                0x0203B0B0: 0, 0x0203B0B4: 0, 0x0203B078: 0}
    assert {int(w['address'], 16): int.from_bytes(bytes.fromhex(w['value']), 'little') for w in writes} == expected
    for path in (EVIDENCE, EVIDENCE.with_name('mustard-map-cupid-source-witness.md')):
        assert all(private not in path.read_text(encoding='utf-8') for private in ('/home/', '/Users/', 'C:\\'))


def test_fresh_positive_full_control_and_clean_prefix_results_are_distinct():
    e = evidence()
    cases = e['cases']
    assert e['case_counts'] == {'ungated': 47, 'positive': 34, 'full_control': 9, 'clean_prefix': 4,
                                'gated_acquisition': 2, 'health_pairs': 28, 'distinct_percentages': 32}
    assert len(cases) == len({c['name'] for c in cases}) == 47
    # Fresh deterministic runs may have identical trace bytes at nearby health settings.
    assert len({c['enemy_health_percent'] for c in cases}) == 32
    assert sum(c['positive'] for c in cases) == 34 and sum(c['clean_prefix'] for c in cases) == 4
    endpoints = [c for c in cases if c['name'].startswith(('robust-', 'clean-prefix-'))]
    assert len(endpoints) == 12
    assert {(c['hp'], c['enemy_health_percent']) for c in endpoints} == {(hp, h) for hp in (1, 6) for h in (100, 500)}
    for c in cases:
        assert c['source_acquisition_frame'] == 1320 and c['entry310_frame'] == 2368
        assert not c['final_collection']['native_map_ownership']
        assert c['configuration_write_count'] == 8
        assert not any(c[k] for k in (
            'gameplay_ram_writes', 'runtime_rom_writes', 'state_restores', 'server_transmission'))
        assert all(len(h) == 64 and int(h, 16) >= 0 for h in c['hashes'].values())
        if c['positive']:
            assert c['hp_min'] == c['hp_max'] == c['hp'] and c['first_damage_frame'] is None
            assert c['final_ability'] == 19 and c['final_frame'] == 3549
            assert c['switch_contact_frame'] == 2968 and c['slot1_high_frames'] == [2969, 2980]
            assert c['crossing_frame'] == 3045 and c['chest_frame'] == 3452
            assert c['final_collection']['chest39'] and c['final_collection']['mustard_map_check']
            assert c['client_locations'] == [{'cmd': 'LocationChecks', 'locations': [3960205]}]
            assert c['identity']['input_file_sha256'] == e['private_artifact_sha256']['robust-inputs.json']
        else:
            assert all(c[k] is None for k in (
                'switch_contact_frame', 'slot1_high_frames', 'crossing_frame', 'chest_frame'))
            assert not c['client_locations'] and not any(c['final_collection'].values())
            if c['clean_prefix']:
                assert c['hp_min'] == c['hp_max'] == c['hp'] and c['first_damage_frame'] is None
                assert c['final_frame'] == 3000 and c['final_ability'] == 19
            else:
                assert c['first_damage_frame'] > 3000 and c['hp_min'] < c['hp']
                assert c['final_frame'] == 3549  # Full controls are not clean prefixes.


def test_exact_q0_player_arrow_timing_and_eight_arrow_repair():
    e = evidence()
    t = e['native_timing']
    assert t['release'] == {'frame': 2896, 'x': 425.99609375, 'player_after_update_y': 85.16796875, 'charge': 0}
    assert t['arrow_pre_movement_y'] == 85.10546875
    first = t['first_arrow_update']
    arrow, switch = t['first_switch_contact']['arrow'], t['first_switch_contact']['switch']
    assert int(arrow['parent'], 16) == 0x02020EE0 and int(arrow['fn'], 16) == 0x08081EB1
    assert arrow['room'] == switch['room'] == 310 and arrow['damage'] == 3 and arrow['counter'] == 73
    assert arrow['collision_pointer'] == switch['address'] and switch['collision_pointer'] == arrow['object']
    assert [arrow['x'], arrow['y'], arrow['vx'], arrow['vy']] == [301.0859375, 134.4375, -201, -1037]
    assert [first['x'], first['y'], first['vx'], first['vy'], first['counter']] == [417.5234375, 82.40625, -633, 691, 1]
    assert t['slot1_high_frames'] == [2969, 2980] and t['gate_open_frame'] == 2970
    assert (t['crossing']['frame'], t['crossing']['x'], t['crossing']['y']) == (3045, 455.296875, 136.99609375)
    inputs = e['inputs']
    assert inputs['post_crossing_weak_arrows'] == 8
    shots = [start for start, frames, keys in inputs['positive'] if 3048 <= start < 3272 and keys & 2]
    assert shots == [3048, 3076, 3104, 3132, 3160, 3188, 3216, 3244]
    assert inputs['omission'] == [[s, f, k & ~2 if s == 2881 else k] for s, f, k in inputs['positive']]
    assert [2881, 1, 66] in inputs['positive']
    diagnostic = e['failed_two_arrow_diagnostic']
    assert (diagnostic['enemy_health_percent'], diagnostic['knight_hp'], diagnostic['knight_hp_after_two_hits'],
            diagnostic['first_damage_frame']) == (163, 7, 1, 3126)
    fixed = next(c for c in e['cases'] if c['name'] == 'threshold-163-1hp-positive')
    assert any(h['frame'] == 3123 and h['hp'] == -2 for h in fixed['knight_hp_changes'])
    high = next(c for c in e['cases'] if c['name'] == 'robust-500-1hp-positive')
    assert [h['hp'] for h in high['chip_hp_changes'][:2]] == [10, 7]
    assert all(h['hp'] > 0 for h in high['chip_hp_changes'])
    assert all(h['hp'] == 20 for h in high['knight_hp_changes'])


def test_health_pair_representatives_cover_hp_formula_not_other_enemy_or_rng_states():
    e = evidence()
    pairs = e['health_pairs']
    assert len(pairs) == 28
    assert {(p['chip_hp'], p['knight_hp']) for p in pairs} == {
        (scale_hp_value(2, health), scale_hp_value(4, health)) for health in range(50, 501)}
    positives = [c for c in e['cases'] if c['positive']]
    for p in pairs:
        low, high = p['health_percent_interval']
        assert all((scale_hp_value(2, h), scale_hp_value(4, h)) == (p['chip_hp'], p['knight_hp'])
                   for h in range(low, high + 1))
        run, = [c for c in positives if c['hp'] == 1 and c['enemy_health_percent'] == p['representative']]
        assert run['chip_hp_changes'][0]['hp'] == p['chip_hp']
        assert run['knight_hp_changes'][0]['hp'] == p['knight_hp']
        assert p['chip_weak_hits_to_defeat'] == (p['chip_hp'] + 2) // 3
        assert p['knight_weak_hits_to_defeat'] == (p['knight_hp'] + 2) // 3
    assert any('global RNG' in limitation for limitation in e['limitations'])


def test_separate_gated_acquisition_boundary_is_not_a_full_route():
    e = evidence()
    gated = e['gating_acquisition']
    assert 'acquisition boundary only' in gated['scope'] and 'no broader' in gated['scope']
    assert gated['main_ungated_manifest_sha256'] == e['private_artifact_sha256']['acceptance.json']
    received, withheld = gated['cases']
    assert [c['permission'] for c in gated['cases']] == ['received', 'withheld']
    assert received['initial_items_received'] == [[3860119, 0, 1, 1]] and withheld['initial_items_received'] == []
    assert received['runtime_unlocked_mask'] == 1 << 19 and withheld['runtime_unlocked_mask'] == 0
    assert received['acquired_cupid_frame'] == 1320 and withheld['acquired_cupid_frame'] is None
    assert (received['final_ability'], withheld['final_ability']) == (19, 0)
    for case in gated['cases']:
        assert case['runtime_gate_mask'] & (1 << 19) and case['source_table_byte'] == 19
        assert case['hp_min'] == case['hp_max'] == 1 and case['frame'] == 1335
        assert not any(case[k] for k in ('native_equipment_writes', 'gameplay_ram_writes', 'state_restores'))


def test_tracked_source_hash_uses_lf_but_private_hashes_remain_raw():
    e = evidence()
    raw = (Path(__file__).resolve().parents[1] / 'client.py').read_bytes()
    assert e['tracked_client_hash_format'] == 'UTF-8 text with LF line endings (Git blob content)'
    assert e['tracked_client_sha256'] == lf_text_sha256(raw)
    lf = raw.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
    assert lf_text_sha256(lf.replace(b'\n', b'\r\n')) == hashlib.sha256(lf).hexdigest()
    assert lf_text_sha256(raw + b' ') != e['tracked_client_sha256']
    assert e['private_artifact_sha256']['acceptance.json'] == (
        'c4d1218cf61a7a58dde5a93eb147b51f5963b0bddc4fc559bd5b20358e2fce55')
    assert e['private_artifact_sha256']['gating-acceptance.json'] == (
        '3cd7be9a38d349c6aca905af303b44a7f866671e06f2020c9e28756e7ad2f8fc')
