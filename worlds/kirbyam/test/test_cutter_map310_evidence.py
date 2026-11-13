"""Sanitized frozen Cutter evidence contracts. These tests do not replay a ROM."""

import pytest
import hashlib
import json
from pathlib import Path
from .test_beam538_evidence import historical_client_before_ice_start

from ..enemy_ability_data import ABILITY_NAME_TO_ID
from ..enemy_ability_runtime_patch import build_enemy_copy_runtime_patch_writes, build_enemy_source_runtime_config
from ..enemy_health_scaling import scale_hp_value
from ..traversal import CAPABILITY_ABILITIES, ROOM_SCOPED_CAPABILITIES, SourcePolicy
from .test_cutter_map310 import CAPABILITY, EVIDENCE, LOCATION, TARGET
from .test_yellow_ufo_upstream_evidence import lf_text_sha256


def evidence():
    return json.loads(EVIDENCE.read_text(encoding='utf-8'))


def test_source_runtime_policy_and_publication_boundaries():
    e = evidence()
    raw = e['source_policy']
    assert e['generation_seed'] == 2 and raw['seed'] == 16441167028314156635
    assert raw['mode'] == 1 and raw['mapping_style'] == 'per_enemy_type'
    assert set(raw['allowed_abilities']) == set(ABILITY_NAME_TO_ID) - {'Normal', 'Master', 'Wait'}
    assert SourcePolicy(raw).grant('TWISTER', lambda _: True).guaranteed == frozenset({'Cutter'})
    assert build_enemy_copy_runtime_patch_writes(raw)[0x3518EE] == 6
    assert int.from_bytes(build_enemy_source_runtime_config(raw)[4:8], 'little') & (1 << 28)
    assert e['source'] == {'template': '0x088B59B4', 'native_xy': [144, 280], 'finite': True,
                           'native_room': 534, 'normal_start_room': 590}
    assert e['target'] == {'id': TARGET, 'location': LOCATION, 'location_id': 3960205, 'chest': 39}
    assert CAPABILITY_ABILITIES[CAPABILITY] == frozenset({'Cutter'})
    assert ROOM_SCOPED_CAPABILITIES[CAPABILITY] == 310
    abilities = json.loads((EVIDENCE.parents[1] / 'data/abilities.json').read_text(encoding='utf-8'))
    assert abilities['Cutter'] == {'runtime_ability_id': 6, 'safe_to_gate': True}
    setup = e['setup']
    assert not any(setup[k] for k in ('full_route_gating', 'area_keys', 'gameplay_ram_writes',
                                      'runtime_rom_writes', 'state_restores', 'server_submission',
                                      'helper_parent_attacks_in310', 'helpers_inert'))
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
    for path in (EVIDENCE, EVIDENCE.with_name('mustard-map-cutter-source-witness.md')):
        assert all(private not in path.read_text(encoding='utf-8') for private in ('/home/', '/Users/', 'C:\\'))
    assert 'inputs' not in e  # Hash identity is not a published full controller replay.


def test_positive_and_omission_scopes_preserve_earlier_switch_activity():
    e = evidence()
    cases = e['cases']
    assert len(cases) == len({c['case'] for c in cases}) == 43
    positives = [c for c in cases if c['positive']]
    prefixes = [c for c in cases if c['clean_prefix']]
    negatives = [c for c in cases if not c['positive'] and not c['clean_prefix']]
    assert (len(positives), len(negatives), len(prefixes)) == (30, 9, 4)
    assert e['coverage']['fresh_full_positives'] == len(positives)
    assert e['coverage']['full_damaged_omission_controls'] == len(negatives)
    assert e['coverage']['damage_free_prefix_omission_controls'] == len(prefixes)
    assert len({c['enemy_health_percent'] for c in cases}) == 28
    assert {(c['starting_hp'], c['enemy_health_percent']) for c in positives if c['starting_hp'] == 6} == {
        (6, 100), (6, 500)}
    for c in cases:
        assert c['acquisition_frame'] == 1320 and c['arrival_frame'] == 2344
        assert c['configuration_write_count'] == 8 and c['first_hp_frame'] == 1085
        assert c['hp_sample_count'] == c['final']['frame'] - 1085 + 1
        assert not c['native_map_ownership']
        assert not any(c[k] for k in ('gameplay_ram_writes', 'runtime_rom_writes', 'state_restores',
                                      'server_transmission', 'poll_memory_writes'))
        assert c['switch_contact_frames']  # Earlier setup effects survive the final-shot omission.
        assert all(len(digest) == 64 and int(digest, 16) >= 0 for digest in c['sha256'].values())
        if c['positive']:
            assert c['hp_min'] == c['hp_max'] == c['starting_hp']
            assert c['final']['ability'] == 6 and c['final']['frame'] == 3880
            assert c['final_phase_contact_frames'] == [3519, 3520]
            expected_crossing = 3578 if c['enemy_health_percent'] <= 224 else (
                3579 if c['enemy_health_percent'] <= 424 else 3580)
            assert c['crossing_frame'] == expected_crossing
            assert c['chest39'] and c['mustard_map_check']
            assert c['client_messages'] == [{'cmd': 'LocationChecks', 'locations': [3960205]}]
            assert len(c['knight_hp_changes']) == 1
            assert c['identity']['input_file_sha256'] == e['private_artifact_sha256']['primary/robust-inputs.json']
        else:
            assert not c['final_phase_contact_frames'] and c['crossing_frame'] is None
            assert not c['chest39'] and not c['mustard_map_check'] and not c['client_messages']
            if c['clean_prefix']:
                assert c['hp_min'] == c['hp_max'] == c['starting_hp']
                assert c['final']['frame'] == 3533 and c['final']['ability'] == 6
            else:
                assert c['hp_min'] < c['starting_hp'] and c['final']['frame'] == 3880


def test_contact_is_before_terrain_not_rebound_or_persistent_gate():
    e = evidence()
    t, collision, order = e['trajectory'], e['collision_order'], e['ordering']
    assert t['creation_frame'] == 3472 and t['pre_movement_player_release'] == [369.29296875, 72.99609375]
    assert t['steered_movements'] == 31 and t['first_contact_movement'] == 48
    assert t['terrain_centers_verified_clear'] == 48 and t['first_contact_frame'] == 3519
    assert t['first_contact_center'] == [311.72265625, 128.046875]
    assert 'inclusive Y-edge' in t['boundary']
    assert int(collision['player_parent'], 16) == 0x02020EE0
    assert int(collision['normal_cutter_callback'], 16) == 0x08079265
    assert int(collision['generic_task'], 16) == 0x08070581
    assert int(collision['category'], 16) == 0x20002003 and collision['damage'] == 4
    assert int(collision['next_frame_flags'], 16) & 0x1000
    assert collision['next_frame_frozen_center'] == t['first_contact_center']
    assert collision['removed_frame'] == 3521
    assert order['hypothetical_first_terrain_without_prior_object_contact']['update'] == 50
    assert 'not wall penetration' in order['limit']
    assert e['native_outcome']['slot1_high_frames'] == [3520, 3531]
    assert e['native_outcome']['chest39_frame'] == 3783


def test_all_28_hp_pair_representatives_are_native_cases_not_interpolation():
    e = evidence()
    intervals = e['health_intervals']
    assert len(intervals) == e['coverage']['source_derived_chip_knight_hp_pairs'] == 28
    assert e['coverage']['native_tested_hp_pairs'] == 28 and e['coverage']['native_untested_hp_pairs'] == 0
    assert {(p['chip_hp'], p['knight_hp']) for p in intervals} == {
        (scale_hp_value(2, h), scale_hp_value(4, h)) for h in range(50, 501)}
    cases = {c['case']: c for c in e['cases'] if c['positive']}
    for interval in intervals:
        low, high = interval['first_percent'], interval['last_percent']
        assert all((scale_hp_value(2, h), scale_hp_value(4, h)) == (
            interval['chip_hp'], interval['knight_hp']) for h in range(low, high + 1))
        representative, = [c for c in interval['fresh_positive_cases'] if c['starting_hp'] == 1]
        actual = cases[representative['case']]
        assert actual['enemy_health_percent'] == representative['health_percent']
        assert actual['chip_hp_changes'][0][1] == interval['chip_hp']
        assert actual['knight_hp_changes'][0][1] == interval['knight_hp']
        assert interval['chip_four_damage_hits_to_kill'] == (interval['chip_hp'] + 3) // 4
    assert any('global-RNG' in limit for limit in e['limitations'])


def test_separate_gating_pair_and_immutable_verifier_correction():
    e = evidence()
    gated = e['gating_acquisition']
    assert 'acquisition boundary only' in gated['scope'] and 'not a full' in gated['scope']
    received, withheld = gated['records']
    assert [c['permission'] for c in gated['records']] == ['received', 'withheld']
    assert received['initial_items_received'] == [[3860106, 0, 1, 1]]
    assert withheld['initial_items_received'] == []
    assert (received['runtime_unlocked_mask'], withheld['runtime_unlocked_mask']) == (64, 0)
    assert (received['final_ability'], withheld['final_ability']) == (6, 0)
    for c in gated['records']:
        assert c['runtime_gate_mask'] & (1 << 6) and c['source_table_byte'] == 6
        assert c['frame'] == 1335 and c['hp_min'] == c['hp_max'] == 1
        assert not any(c[k] for k in ('native_equipment_writes', 'gameplay_ram_writes', 'state_restores'))
    pair, = gated['config_write_difference']
    assert all(int(c['address'], 16) == 0x0203B0B4 for c in pair)
    correction = e['gating_verifier_correction']
    assert correction['original_manifest_sha256'] == e['private_artifact_sha256']['primary/gating-acceptance.json']
    assert correction['corrected_verifier_sha256'] == (
        e['private_artifact_sha256']['supplement/verify_original_gating.py'])
    assert 'tuple pairs' in correction['problem'] and 'No original artifact changed' in correction['correction']


def test_tracked_source_uses_lf_but_frozen_packet_hashes_remain_raw():
    e = evidence()
    raw = (Path(__file__).resolve().parents[1] / 'client.py').read_bytes()
    assert e['tracked_client_hash_format'] == 'UTF-8 text with LF line endings (Git blob content)'
    assert e['tracked_client_sha256'] == 'b32450357cfbd9486ce71ad1c5dfd9000e5b0aca770422722e62a235408251f9'
    # Preserve e's historical client identity; current client comes from main.
    union = json.loads((Path(__file__).parents[1] / 'dev-docs/main-ranged-union-catalog.json').read_text())
    expected = union['adopted_main_source_sha256']['client.py']
    assert lf_text_sha256(historical_client_before_ice_start(raw, expected)) == expected
    lf = raw.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
    assert lf_text_sha256(lf.replace(b'\n', b'\r\n')) == hashlib.sha256(lf).hexdigest()
    with pytest.raises(AssertionError):
        historical_client_before_ice_start(raw + b' ', expected)
    assert lf_text_sha256(historical_client_before_ice_start(lf.replace(b'\n', b'\r\n'), expected)) == expected
    assert e['private_artifact_sha256']['primary/packet-manifest.json'] == (
        '2a5babe84f2595c3ecf8433979e8128a0443bcd21ca9f5f4dee4c8008f28f3eb')
    assert e['private_artifact_sha256']['primary/acceptance.json'] == (
        '1f29ae4a41d535f64e4ddb98e12f8197b23af6120daed5d67167b64d643ebaaf')
    assert e['private_artifact_sha256']['supplement/packet-manifest.json'] == (
        '4319bdb9fcf18666f430b40912b7cddc6d28fffa4878a568953368349bed7bc2')
    assert e['private_artifact_sha256']['supplement/sweep-acceptance.json'] == (
        '84f6e44d1205da266dc1c4a2a011abe6be6ff7953de97f8e32598726f2f982cc')
    assert e['production_source_commit'] == '99b5ab8292cf3f9d2f55798034a08d38a8e04c03'
    assert e['integration_base_commit'] == '6948ac7295d3b3e8e1eaf08506338592d707254e'
