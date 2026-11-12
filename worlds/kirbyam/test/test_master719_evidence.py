"""Sanitized Master719 evidence consumers, not ROM execution or generation."""
from copy import deepcopy
import hashlib
from inspect import signature
import json
from pathlib import Path
from typing import Any

import pytest

from ..data import data
from ..master_source import (
    CARROT_HUB, CARROT_KEY, CENTRAL_MASTER_IDENTITY, CENTRAL_MASTER_SOURCE,
    CENTRAL_REGION, CENTRAL_RETURN_EVENT, MASTER719_CAPABILITY, RAINBOW_WEST_HUB,
)
from ..peg_traversal import validate_peg_assignment
from ..tools.build_ranged_completion_status import build_status
from ..tools.build_ranged_target_coverage import build_coverage
from ..traversal import validated_assignment
from ..traversal_data import graph_items, room_traversal_graph, room_traversal_targets
from .test_traversal import policy

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'dev-docs/carrot-room7-master-acceptance.json'
WITNESS = EVIDENCE.with_name('carrot-room7-master-source-witness.md')
PERCENTAGES = [50, 100, 300, 450, 500]
HP_HISTORIES = [[1, -2, -5, -8], [2, -1, -4, -7], [6, 3, 0, -3], [9, 6, 3, 0], [10, 7, 4, 1]]


def evidence() -> dict[str, Any]:
    result: dict[str, Any] = json.loads(EVIDENCE.read_text(encoding='utf-8'))
    return result


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate_host(e: dict[str, Any]) -> None:
    h = e['host_contract']
    assert e['schema_version'] == 1 and e['status'] == 'accepted_bounded_source_carrier'
    assert e['pr_completion'] == 'partial'
    assert h['event'] == CENTRAL_RETURN_EVENT and h['event_address'] is h['event_item_code'] is None
    assert h['unique_shards_required'] == 8 and h['dimension_reachability_required'] is True
    assert h['dmk_sequence_required'] is h['central_access_required'] is True
    assert (h['source_key'], h['source_identity']) == (CENTRAL_MASTER_SOURCE, CENTRAL_MASTER_IDENTITY)
    assert (h['input_equipment'], h['output_equipment'], h['native_ability']) == ('Normal', 'Master', 26)
    assert h['master_permission_item'] is False and h['single_acquisition'] is h['forward_only'] is True
    assert h['carrier_rooms'] == [801, 192, 193, 170, 719]
    assert h['carrier_item_ids'] == [3860405, 3860406, 3860044]
    assert h['capability'] == MASTER719_CAPABILITY and h['target'] == 'bomb_719_room13'
    assert h['owner'] == 'REGION_CARROT_CASTLE/ROOM_5_07'
    assert h['destination'] == 'REGION_CARROT_CASTLE/ROOM_5_13__LOGIC__ENTRY_FROM_5_07'
    assert h['carrot_key_required_when_enabled'] is h['target_always_installed'] is True
    assert h['finite_doo_conditions_graph_local'] is h['placed_progression_guard_retained'] is True
    assert (h['targets'], h['witnesses'], h['conditional_policy_fallback_targets']) == (57, 145, 5)
    assert (h['policy_budget'], h['candidate_budget']) == (8192, 128)


def validate_setup(e: dict[str, Any]) -> None:
    s = e['setup']
    assert (s['ability_randomization_mode'], s['ordinary_ability_pool_size'], s['normal_weight']) == (2, 25, 100)
    assert s['included_statues'] is s['ability_gating'] is s['area_keys'] is True
    assert (s['minimum_health'], s['maximum_health']) == (1, 1)
    assert (s['allowed_mask'], s['gate_mask'], s['unlock_mask']) == ('0x03FFFFFE', '0x03FFFF7E', '0x80')
    assert not int(s['allowed_mask'], 16) & (1 << 26) and not int(s['gate_mask'], 16) & (1 << 26)
    assert s['generated_precollect_ids'] == [3860107, 3860041, 3860405, 3860406, 3860044]
    assert s['generated_production_patch'] is s['imported_genuine_historical_clear'] is True
    assert s['native_clear_value'] == 9999 and s['preexisting_hub_doors'] is True
    assert (s['local_client_writes'], s['successful_guards'], s['actual_acknowledged_sqlite_receipts']) == (33, 9, 5)
    assert s['ack_frames'] == [1351, 1352, 1353, 1354, 1355]
    assert s['key_sync_frame'] == 1350 < s['ack_frames'][0]
    assert (s['key_mask'], s['hub_mask'], s['configuration_frame']) == ('0x24', '0x60', 1517)
    assert s['rng_mailbox_initialization'] == {'address': '0x0203B078', 'value': 0}
    assert s['helpers_normal_in_room'] == 801
    for key in ('post_patch_rom_edits', 'state_restores', 'current_seed_earned_clear_proved',
                'missing_hub_denial_proved', 'additional_gameplay_state_injection', 'complete_watcher_run',
                'external_server_session', 'helper_source_carry_combat_credit', 'phone_input'):
        assert s[key] is False


def validate_native(e: dict[str, Any]) -> None:
    m = e['continuous_milestones']
    assert m == {
        'normal_stand_contact_pending26': 1532, 'master_equipped_occupancy1': 1554,
        'actual192': 1873, 'key_attempt192_to193': 2268, 'actual193': 2294, 'actual170': 2488, 'actual719': 3087,
        'big_dee_hit_frames': [4155, 4161, 4167], 'collision_bit4': 4173, 'bounce': 4174, 'left_escape': 4184,
        'safe_left_pose': 4209, 'charge_begin': 4409, 'f1_mutation': 4449, 'all15_f2_clear': 4485,
        'actual734_lower': 4657, 'alive_hp1_master_endpoint': 4736,
    }
    a = e['final_action']
    assert (a['hold_b_frames'], a['f1_cell'], a['f1_before'], a['f1_after']) == (30, [1, 14], 241, 255)
    assert (a['f2_count'], a['f2_before'], a['f2_after']) == (15, 242, 0)
    assert a['launch_xy'] == [86, 232.99609375] and a['lower734_xy'] == [200, 216.99609375]
    assert a['wave_xy_at_f1'] == [37.5, 224.99609375] and a['wave_bounds'] == [-8, -12, 8, 12]
    assert a['wave_counter'] == 5 and a['wave_human_owned'] is a['chain_parent_is_actual_wave'] is True
    assert a['wave_objectbase_size'] == 0x78
    assert a['stable_object_addresses_required'] is a['extended_observer_bytes_are_wave_ai'] is False
    assert e['accepted_continuous_trace_count'] == 2 * len(e['health_profiles']) == 10
    assert [p['enemy_health_percent'] for p in e['health_profiles']] == PERCENTAGES
    assert [p['big_dee_hp'] for p in e['health_profiles']] == HP_HISTORIES
    for p in e['health_profiles']:
        assert (p['actual_player_hp'], p['trace_frames'], p['master_retained_from'], p['lower734_arrival']) == (
            1, 4736, 1554, 4657)
        assert p['cold_repeat'] is True and p['positive_trace_sha256'] == p['repeat_trace_sha256']


def validate_health(e: dict[str, Any]) -> None:
    h = e['health_equivalence']
    assert h['public_percent_range'] == [50, 500]
    assert (h['vanilla_big_dee_hp'], h['damage_per_contact'], h['contacts']) == (2, 3, 3)
    assert h['unexecuted_initial_hp'] == [3, 4, 5, 7, 8]
    assert h['other_encountered_enemy_types'] == [8, 13, 18, 52, 12]
    for key in ('first_hit_exact_zero_natively_executed', 'other_combat_hp_changes_observed',
                'all_percentages_natively_executed', 'arbitrary_rng_phase_safety_proved',
                'full_observer_equality_required', 'human_contact_pointer_is_timestamp'):
        assert h[key] is False
    assert [(c['percent_range'], c['initial_hp_range'], c['first_nonpositive_hit'], c['executed_percentages'])
            for c in h['classes']] == [
                ([50, 174], [1, 3], 1, [50, 100]), ([175, 324], [4, 6], 2, [300]),
                ([325, 474], [7, 9], 3, [450]), ([475, 500], [10, 10], None, [500]),
    ]
    # Exhaust the arithmetic bins, not native runs or inferred RNG histories.
    for percent in range(50, 501):
        classes = [c for c in h['classes'] if c['percent_range'][0] <= percent <= c['percent_range'][1]]
        assert len(classes) == 1
        hp = max(1, (2 * percent + 50) // 100)
        c = classes[0]
        assert c['initial_hp_range'][0] <= hp <= c['initial_hp_range'][1]
        assert next((hit for hit in (1, 2, 3) if hp - 3 * hit <= 0), None) == c['first_nonpositive_hit']


def validate_controls(e: dict[str, Any]) -> None:
    o = e['omission']
    assert (o['enemy_health_percent'], o['changed_input_times'], o['identical_recorded_prefix_through']) == (
        100, [4409, 4438], 4409)
    assert (o['endpoint_frame'], o['final_room']) == (4736, 719)
    assert o['alive_hp1_master'] is o['f1_and_all15_f2_sealed'] is True
    assert o['new_50_300_450_500_counterfactuals'] is False
    assert o['reuse_scope'] == 'unchanged final charged-wave mechanism only'
    assert [r['stop_frame'] for r in e['preserved_nonpasses']] == [3698, 3789, 1553]
    assert e['controller_correction'] == {
        'departure_frames_earlier': 80, 'landing_pause_before': 70, 'landing_pause_after': 40,
        'common_escape': 'Left25 then Left19', 'new_retiming_in_health_profiles': False,
    }
    k = e['supplemental_qualification']['missing_carrot_key']
    assert k['same_controller_not_identical_state'] is True and k['first_recorded_physical_divergence'] == 1897
    assert (k['attempt_frame'], k['positive_method_allowed_reason'], k['negative_method_allowed_reason']) == (
        2268, [5, 1, 3], [5, 0, 2])
    assert (k['negative_key_mask'], k['negative_endpoint'], k['negative_room']) == ('0x04', 2362, 192)
    m = e['supplemental_qualification']['mode1']
    assert m['scope'] == 'source only' and m['included_statues'] is True
    assert (m['ordinary_statue_assignments_checked'], m['master_stand_bytes_unchanged']) == (19, 36)
    assert (m['beam_statue_original'], m['beam_statue_shuffled']) == (7, 10)
    assert (m['contact_frame'], m['equip_frame'], m['endpoint_frame']) == (1532, 1554, 1585)
    assert m['carrier_proved'] is m['all_ordinary_fallbacks_absent'] is False


def validate_record(e: dict[str, Any]) -> None:
    for validator in (validate_host, validate_setup, validate_native, validate_health, validate_controls):
        validator(e)


def test_reviewed_scalar_contract() -> None:
    validate_record(evidence())


@pytest.mark.parametrize('path,value', [
    (('pr_completion',), 'complete'), (('host_contract', 'event_address'), 1),
    (('host_contract', 'unique_shards_required'), 7), (('host_contract', 'dimension_reachability_required'), False),
    (('host_contract', 'dmk_sequence_required'), False), (('host_contract', 'central_access_required'), False),
    (('host_contract', 'master_permission_item'), True), (('host_contract', 'forward_only'), False),
    (('host_contract', 'destination'), 'REGION_CARROT_CASTLE/ROOM_5_13'),
    (('host_contract', 'conditional_policy_fallback_targets'), 0), (('host_contract', 'policy_budget'), 100000),
    (('setup', 'imported_genuine_historical_clear'), False), (('setup', 'current_seed_earned_clear_proved'), True),
    (('setup', 'missing_hub_denial_proved'), True), (('setup', 'actual_acknowledged_sqlite_receipts'), 0),
    (('setup', 'rng_mailbox_initialization'), None), (('setup', 'key_sync_frame'), 1355),
    (('setup', 'helper_source_carry_combat_credit'), True), (('setup', 'external_server_session'), True),
    (('final_action', 'chain_parent_is_actual_wave'), False), (('final_action', 'wave_objectbase_size'), 160),
    (('final_action', 'stable_object_addresses_required'), True),
    (('final_action', 'extended_observer_bytes_are_wave_ai'), True),
    (('health_equivalence', 'all_percentages_natively_executed'), True),
    (('health_equivalence', 'first_hit_exact_zero_natively_executed'), True),
    (('health_equivalence', 'human_contact_pointer_is_timestamp'), True),
    (('omission', 'new_50_300_450_500_counterfactuals'), True),
    (('supplemental_qualification', 'mode1', 'carrier_proved'), True),
    (('supplemental_qualification', 'missing_carrot_key', 'same_controller_not_identical_state'), False),
])
def test_evidence_rejects_scope_expansion(path: tuple[str, ...], value: Any) -> None:
    e = deepcopy(evidence())
    target: Any = e
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(AssertionError):
        validate_record(e)


@pytest.mark.parametrize('keys', [False, True])
def test_evidence_binds_current_graph_and_exact_owned_items(keys: bool) -> None:
    h = evidence()['host_contract']
    target = next(row for row in room_traversal_targets('block') if row['id'] == h['target'])
    assert target['region'] == h['owner'] and target['exit'] == h['destination']
    assert set(target['graphs']) == set(h['graphs'])
    assert 'requires_guaranteed_source' not in target and 'requires_any_guaranteed_source' not in target
    graph = room_traversal_graph(h['target'], h['graph'], keys)
    assert graph.access_region == CENTRAL_REGION and graph.starts[0].equipped == h['input_equipment']
    assert len(graph.placements) == 1 and not graph.placements[0].renewable
    assert graph.placements[0].source_key == h['source_key']
    assert graph.placements[0].identity == h['source_identity']
    assert graph.placements[0].requirements == {h['event']}
    assert list(dict.fromkeys(node.room for node in graph.nodes)) == h['carrier_rooms']
    owned = frozenset({CENTRAL_RETURN_EVENT, RAINBOW_WEST_HUB, CARROT_HUB} | ({CARROT_KEY} if keys else set()))
    assert graph_items(graph) == owned
    for label, item_id in zip((RAINBOW_WEST_HUB, CARROT_HUB, CARROT_KEY), h['carrier_item_ids']):
        assert next(item for item in data.items.values() if item.label == label).item_id == item_id
    assert 'Master Ability' not in {item.label for item in data.items.values()}
    assert graph.evaluate(policy(2, weight=100), owned, True).reaches('bomb_719_master:left_door')
    for missing in owned:
        assert not graph.evaluate(policy(2, weight=100), owned - {missing}, True).reaches('bomb_719_master:left_door')
    for name, ability in zip(h['graphs'][:4], ('Beam', 'Fighter', 'Sword', 'Fire')):
        assert target['graphs'][name]['requires_guaranteed_source'] == {'source_key': 'WADDLE_DOO', 'ability': ability}


def test_current_counts_and_historical_404_record_are_distinct() -> None:
    h = evidence()['host_contract']
    status = build_status()
    coverage = build_coverage()
    assert status['completion'] == 'partial' and not status['declaration_errors']
    assert status['counts']['witnesses'] == 146 and h['witnesses'] == 145
    assert len(coverage['installed_targets']) == h['targets'] == 57
    from .support.green138_history import before_green138
    historical = [{**row, 'target': before_green138(row['target'])}
                  for row in coverage['installed_targets']]
    assert digest(historical) == '76c369a269387b9e3812400689c2da0e9ab02a68476624e71817e9a6b48c8933'
    scope = json.loads((ROOT / 'dev-docs/ranged-completion-scope.json').read_text(encoding='utf-8'))
    assert len(scope['policy_fallback_targets']) == 4 and h['conditional_policy_fallback_targets'] == 5
    old = json.loads((ROOT / 'dev-docs/candy-normal404-acceptance.json').read_text(encoding='utf-8'))
    assert old['host_contract']['counts']['witnesses'] == 144
    assert digest(old) == 'dcc7aef5d96dd145428601050a8d5f495364e1f5d83c4a71f0aba4f9a3530ec9'
    old_witness = (ROOT / 'dev-docs/candy-normal404-source-witness.md').read_text(encoding='utf-8')
    assert hashlib.sha256(old_witness.encode()).hexdigest() == (
        'cf7cb9c78205b57505c46b72801eae46783d9b8f0773ed8d1b0161db5d56dbce')
    assert signature(validate_peg_assignment).parameters['max_attempts'].default == h['policy_budget']
    assert signature(validated_assignment).parameters['max_attempts'].default == h['candidate_budget']


def test_generation_accounting_is_prior_checks_not_new_archives_or_aggregate() -> None:
    g = evidence()['prior_real_generation']
    assert g['source_commit'] == evidence()['provenance']['host_contract_commit']
    assert (g['excluded_regressions_passed'], g['goal_audit_cases'], g['total_checks']) == (46, 8, 54)
    assert (g['accepted_archives'], g['correct_minimal_refusals']) == (6, 2)
    assert g['accepted_goal_values'] == [0, 1, 2, 4] and g['refusal_unique_shards'] == [2, 7]
    assert g['full_aggregate'] is g['rerun_by_evidence_integration'] is False


def test_provenance_integrity_privacy_and_line_endings() -> None:
    e = evidence()
    assert digest(e) == 'edd46edf136e41a93416d90680483d5d2708b84920275625e956296f0ee10e03'
    witness = WITNESS.read_text(encoding='utf-8')
    assert hashlib.sha256(witness.encode()).hexdigest() == (
        '565ff71ec114376a1e40e0d7a9054f9f1c56f971f58db9be5ee703ae92f5586c')
    p = e['provenance']
    assert p['native_execution_ap_commit'] == '94c4e638c9de9793e589f3253379a1f5e4009118'
    assert p['host_contract_commit'] == '46a92b051394ef482ef3aff1f0222da992f7ff05'
    assert p['native_source_commit'] == '7d969fbce14fdc838d2c1ea01389717fb96c3189'
    hashes = [p['historical_clear_battery_sha256'], e['omission']['trace_sha256']]
    for group in ('native_source_sha256', 'private_review_sha256', 'private_packet_sha256'):
        hashes.extend(p[group].values())
    for row in e['health_profiles']:
        hashes.extend(row[key] for key in ('positive_trace_sha256', 'repeat_trace_sha256', 'production_rom_sha256'))
    hashes.extend(row['trace_sha256'] for row in e['preserved_nonpasses'])
    hashes.extend(row[key] for row in e['supplemental_qualification'].values()
                  for key in ('trace_sha256', 'negative_trace_sha256') if key in row)
    assert all(len(h) == 64 and int(h, 16) >= 0 for h in hashes)
    for text in (json.dumps(e), witness):
        assert all(private not in text for private in ('/home/', '/Users/', 'C:\\', 'D:\\', 'identity-private'))
    assert not any(key in e for key in ('inputs', 'frames', 'replay', 'savestate', 'memory', 'identity'))
    assert set(e['excluded_credit']) == {
        'return or retouch', 'drop or recovery', 'generic Master ability provider', '720', 'upper734',
        'other exits', 'chests or Secret Notes', 'reward or location reporting', 'helper ability or combat', 'Phone',
        'external server or full watcher', 'reset or reconnect persistence', 'native BizHawk portability',
        'every seed or RNG phase',
    }


@pytest.mark.parametrize('mutation', ['survivor_killed', 'repeat_mismatch', 'class_gap', 'wrong_sign_branch'])
def test_health_records_reject_false_equivalence(mutation: str) -> None:
    e = evidence()
    if mutation == 'survivor_killed':
        e['health_profiles'][-1]['big_dee_hp'][-1] = 0
    elif mutation == 'repeat_mismatch':
        e['health_profiles'][0]['repeat_trace_sha256'] = '0' * 64
    elif mutation == 'class_gap':
        e['health_equivalence']['classes'][1]['percent_range'][0] = 176
    else:
        e['health_equivalence']['classes'][2]['first_nonpositive_hit'] = 2
    with pytest.raises(AssertionError):
        validate_record(e)


def test_evidence_integrity_survives_actual_crlf_files(tmp_path: Path) -> None:
    for original in (EVIDENCE, WITNESS):
        copied = tmp_path / original.name
        copied.write_bytes(original.read_text(encoding='utf-8').replace('\n', '\r\n').encode())
        assert b'\r\n' in copied.read_bytes()
        assert copied.read_text(encoding='utf-8') == original.read_text(encoding='utf-8')
    assert digest(json.loads((tmp_path / EVIDENCE.name).read_text())) == digest(evidence())
