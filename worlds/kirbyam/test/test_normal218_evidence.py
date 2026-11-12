"""Bounded scalar/source contracts for Normal 218, not emulator replays."""

import json
import math
import struct
from pathlib import Path
from typing import Any, cast

import pytest
from BaseClasses import CollectionState
from test.general import setup_multiworld

from .. import KirbyAmWorld
from ..data import data, load_json_data
from ..tools.build_ranged_completion_status import build_status

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'dev-docs/peppermint-normal218-acceptance.json'
PREFIX = 'REGION_PEPPERMINT_PALACE/ROOM_7_'


def evidence() -> dict[str, Any]:
    decoded: object = json.loads(EVIDENCE.read_text(encoding='utf-8'))
    assert isinstance(decoded, dict), 'Evidence must be a JSON object'
    return cast(dict[str, Any], decoded)


def test_exact_mapping_and_unchanged_ownership() -> None:
    e = evidence()
    mapping = json.loads((ROOT / 'dev-docs/native-room-wikirby-map.json').read_text())
    for native, room in ((221, '22'), (218, '23'), (200, '24')):
        assert e['host']['mapping'][str(native)] == PREFIX + room
        assert next(r for r in mapping['rooms'] if r['native_id'] == native)['ap_keys'] == [PREFIX + room]
    decoded_rooms = load_json_data('regions/rooms.json')
    assert isinstance(decoded_rooms, dict)
    rooms = decoded_rooms
    for room, successor, location_id, bit in (
        ('22', '23', 3961195, 111), ('23', '24', 3961193, 109), ('24', 'BOSS', 3961171, 85),
    ):
        assert rooms[PREFIX + room]['exits'][PREFIX + successor] is None
        assert rooms[PREFIX + room]['locations']['room_sanity'] == {
            'included': True, 'location_id': location_id, 'bit_index': bit,
        }
    assert rooms[PREFIX + '23'] == {
        'locations': {'room_sanity': {'included': True, 'location_id': 3961193, 'bit_index': 109}},
        'exits': {PREFIX + '24': None},
    }
    target = rooms[PREFIX + '22']['traversal']['targets'][0]
    assert (target['id'], target['native_room'], target['exit'], target['location']) == (
        'peg_221_41_12', 221, None, 'MINOR_CHEST_SPRAY_PAINT_01')
    assert rooms[PREFIX + '22']['locations']['MINOR_CHEST_SPRAY_PAINT_01'] is None
    assert not e['host']['new_target'] and not e['host']['source_policy_binding']


@pytest.mark.parametrize('mode', [0, 1, 2])
@pytest.mark.parametrize('gating', [0, 1])
def test_local_null_exits_do_not_require_copy(mode: int, gating: int) -> None:
    mw = setup_multiworld(KirbyAmWorld, seed=218, options={
        'ability_randomization_mode': mode, 'ability_gating': gating,
        'area_keys': 1, 'minimum_health': 1, 'maximum_health': 1,
    })
    # Only the local predicate: this does not prove upstream reachability or native profile coverage.
    for source, destination in (('22', '23'), ('23', '24')):
        region = mw.get_region(PREFIX + source, 1)
        edge = next(edge for edge in region.exits
                    if edge.connected_region is not None and edge.connected_region.name == PREFIX + destination)
        assert edge.access_rule(CollectionState(mw))
    decoded_abilities = load_json_data('abilities.json')
    assert isinstance(decoded_abilities, dict)
    abilities = decoded_abilities
    assert abilities['Normal']['safe_to_gate'] is False
    assert 'Normal Ability' not in {item.label for item in data.items.values()}


def test_only_accepted_cases_and_preserved_attempts() -> None:
    e = evidence()
    assert [(c['cumulative_attempt'], c['options']['ability_randomization_mode'],
             c['options']['enemy_health_multiplier'], c['final_room']) for c in e['cases']] == [
        (7, 0, 500, 200), (8, 0, 500, 200), (9, 0, 500, 218), (12, 1, 50, 200), (13, 1, 50, 200),
    ]
    for case in e['cases']:
        assert case['actual_hp'] == 1 and case['normal'] and case['damage_taken'] == 0
        assert not case['copy_request'] and case['ownership'] == 128
        assert case['options']['minimum_health'] == case['options']['maximum_health'] == 1
        shuffled = case['cumulative_attempt'] in (12, 13)
        assert case['precollected_item_ids'] == ([3860107, 3860041] if shuffled else [3860107])
        assert case['options']['ability_gating'] == (1 if shuffled else 0)
        assert case['options']['area_keys'] == (1 if shuffled else 0)
        assert case['area_key_bits'] == (4 if shuffled else 0)
    assert e['accounting']['consumed_attempts'] == 14
    assert e['accounting']['failed_cumulative_attempts'] == [1, 5, 6, 10, 11, 14]
    assert e['accounting']['unrun_and_not_credited'] == [15, 16]
    assert e['exact_repeat'] == {
        'all_states_equal': True, 'all_inputs_equal': True, 'snapshot_count': 1121,
        'input_record_count': 1114, 'post_setup_single_frame_commands': 1103,
    }
    assert e['cases'][0]['states_sha256'] == e['cases'][1]['states_sha256']
    assert e['cases'][0]['input_sha256'] == e['cases'][1]['input_sha256']
    assert e['cases'][3]['states_sha256'] == e['cases'][4]['states_sha256']
    assert e['cases'][3]['input_sha256'] == e['cases'][4]['input_sha256']
    assert e['shuffled_exact_repeat'] == e['exact_repeat']
    failed = e['failed_live_profile']
    assert (failed['cumulative_attempt'], failed['failure_frame'], failed['final_room']) == (14, 1119, 218)
    assert failed['options'] == {
        'ability_randomization_mode': 2, 'ability_gating': 1, 'area_keys': 1,
        'enemy_health_multiplier': 100, 'minimum_health': 6, 'maximum_health': 10,
    }
    assert failed['actual_hp'] == failed['actual_current_max_hp'] == 6
    assert failed['exact_projected_prefix_end'] == 1118
    assert failed['observed_state_duplicate_of_previous_except_frame']
    failure_claims = ('arrival_200', 'route_accepted', 'retry_occurred', 'specific_cause_established')
    assert not any(failed[k] for k in failure_claims)


def test_contact_chain_exit_and_untouched_peg() -> None:
    e = evidence()
    m, b = e['mechanism'], e['boundary']
    assert (b['source_door_tile'], b['arrival_218_frame'], b['arrival_218_xy']) == (
        [1, 2], 1113, [232, 40.99609375])
    assert (b['arrival_200_frame'], b['arrival_200_xy']) == (2188, [648, 136.99609375])
    assert (m['puff_spawn_frame'], m['puff_contact_frame'], m['mutations_complete_frame']) == (2109, 2114, 2168)
    assert m['chain_parent_is_human_puff'] and m['puff_callback'] == '0x08072E41'
    assert m['peg_tile'] == [9, 33] and m['peg_value'] == 246
    changes = e['mutations']
    assert len(changes) == len({tuple(c['tile']) for c in changes}) == 13
    assert [c['tile'] for c in changes if c['after'] == 29] == [[x, 1] for x in range(2, 9)]
    assert next(c for c in changes if c['tile'] == [5, 4]) == {
        'frame': 2168, 'tile': [5, 4], 'before': 243, 'after': 255,
    }
    assert not m['f3_is_solid'] and m['f3_attributes'] == 65
    assert e['attribution']['regular_enemy_types'] == [0, 55]
    assert e['attribution']['destroyed_endpoints_included'] and e['attribution']['symmetric_observed_bounds']
    assert e['attribution']['audit_status'] == 'historical; not the corrected contact-box audit'
    assert not e['attribution']['disappeared_previous_endpoints_included']
    assert not e['attribution']['body_enemy_pairs_included']
    assert e['attribution']['positive_attack_enemy_pairs'] == 202
    assert e['attribution']['remote_attack_human_pairs'] == 517
    assert not e['attribution']['helper_ai_zero_is_absence']


def test_omission_common_window_and_separate_qualified_suffix() -> None:
    c = evidence()['omission']
    assert (c['matched_prefix_through'], c['common_window_end'], c['only_common_input_difference_frame']) == (
        2108, 2188, 2109)
    assert (c['success_keys'], c['omission_keys']) == (2, 0)
    assert not c['scheduled_up_position_qualified'] and c['scheduled_up_frame'] == 2177
    assert c['scheduled_up_preinput_x'] < 80
    assert c['settled_xy'] == [85.72265625, 72.99609375]
    assert c['settled_velocity'] == [0, 0] and c['settled_state'] == '0x080488E1'
    assert (c['separate_suffix_neutral_frames'], c['qualified_fresh_up_frame'], c['post_up_neutral_frames']) == (
        8, 2197, 40)
    assert c['end_frame'] == 2237 and c['target_cells_unchanged'] == 13 and c['peg_value'] == 246
    assert c['final_room'] == 218 and not c['arrival_200']
    assert not c['entire_control_one_bit_only'] and not c['directional_rescue']


def test_no_copy_source_field_distinction_and_current_counts() -> None:
    e = evidence()
    c = e['copy_field']
    assert (c['shuffled_doo_generated_assignment'], c['doo_live_native_value']) == (21, 7)
    assert c['template'] == '0x088C1708' and c['subtypes'] == [0, 0] and not c['copy_request_occurred']
    assert c['state_callbacks'] == ['0x080B6B69', '0x080B6CD9', '0x080B7361']
    assert c['layout_provenance'] == {
        'source_type': 'ObjectTemplate', 'subtype1_offset': 14, 'true_subtype2_offset': 16,
        'legacy_subtype2_label_offset': 15, 'legacy_field_source_name': 'unkF',
        'verified_values_at_offsets_14_15_16': [0, 0, 0], 'observed_template_count': 14,
        'verified_rom_count': 6, 'verification': 'immutable production and fixture bytes',
        'historical_trace_relabelled': False, 'generalized_to_other_templates': False,
    }
    assert e['independent_sha256']['layout-and-fresh-witness-review.md'] == (
        '1161b47ac401b9f0190bafcd19183a91b71f43214d41ec3a6ca2940163eb1713')
    scope = json.loads((ROOT / 'dev-docs/ranged-completion-scope.json').read_text())
    assert len(scope['policy_fallback_targets']) == e['host']['policy_fallback_count'] == 4
    assert (e['host']['target_count'], e['host']['witness_count']) == (57, 146)
    counts = build_status()['counts']
    assert counts['witnesses'] == e['host']['witness_count']
    assert len(data.regions) == 382
    ledger = (ROOT / 'dev-docs/ranged-coverage-ledger.md').read_text()
    assert 'the four current target-wide source-policy fallbacks' in ledger
    assert 'definitions (146 witnesses)' in ledger
    assert 'the five current target-wide' not in ledger


def test_sanitized_provenance_and_limits() -> None:
    e = evidence()
    assert e['integration_base'] == '15a1761391925cf343e155e512b09ab667e2401c'
    assert e['native_source_commit'] == '7d969fbce14fdc838d2c1ea01389717fb96c3189'
    assert e['independent_sha256']['positive12-acceptance.md'] == (
        'ffac9c5a6b214a052111478191114de1e9f92ddbf5c946f7fe9c80b79fa0da6e')
    assert e['independent_sha256']['218-host-scope-review.md'] == (
        'ea88d85224979874986d17f0dd05b27269985f5e18bb0e890dde01efd4758e16')
    hashes = list(e['independent_sha256'].values())
    hashes.extend(e['private_manifest_sha256'].values())
    hashes.extend(e['source_sha256'].values())
    for case in e['cases']:
        hashes.extend(case[key] for key in ('input_sha256', 'states_sha256', 'result_sha256', 'fixture_sha256'))
    assert all(len(h) == 64 and int(h, 16) >= 0 for h in hashes)
    assert e['setup']['startup_only_fixture_byte_differences'] == 15
    assert e['setup']['pre_sync_distinct_from_post_sync']
    for key in ('gameplay_ram_writes', 'runtime_rom_writes', 'state_restores'):
        assert e['setup'][key] == 0
    for path in (EVIDENCE, EVIDENCE.with_name('peppermint-normal218-source-witness.md')):
        text = path.read_text(encoding='utf-8')
        assert all(private not in text for private in ('/home/', '/Users/', 'C:\\', 'D:\\'))
    assert not any(key in e for key in ('inputs', 'frames', 'replay', 'savestate'))
    assert '217/225' in ' '.join(e['limitations'])


# Source-decoder regression helpers only. These do not replay the private native traces.
_Box = tuple[float, float, float, float]


def _source_box(record: dict[str, Any], contact: bool) -> _Box:
    left, top, right, bottom = record['damage_box' if contact else 'bounds']
    if contact:
        assert right >= 0 and bottom >= 0, 'Only nonnegative observed half extents are qualified'
        right, bottom = left + 2 * right, top + 2 * bottom
    x, y = record['x'], record['y']
    if contact:
        x, y = math.floor(x), math.floor(y)
    return x + min(left, -right), y + min(top, bottom), x + max(right, -left), y + max(top, bottom)


def _box_hull(a: _Box, b: _Box) -> _Box:
    return min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])


def _attack_box(record: dict[str, Any]) -> _Box:
    return _box_hull(_source_box(record, False), _source_box(record, True))


def _box_identity(record: dict[str, Any]) -> tuple[object, ...]:
    return record['task'], record['address'], record.get('template'), record.get('parent')


def _retained_endpoints(current: list[dict[str, Any]], previous: list[dict[str, Any]]) -> list[dict[str, Any]]:
    current_ids = {_box_identity(record) for record in current}
    return current + [record for record in previous if _box_identity(record) not in current_ids]


def _swept_attack_box(record: dict[str, Any], previous: list[dict[str, Any]]) -> _Box:
    current = _attack_box(record)
    prior = next((old for old in previous if _box_identity(old) == _box_identity(record)), None)
    return _box_hull(current, _attack_box(prior)) if prior is not None else current


def _observed_overlap(a: _Box, b: _Box) -> bool:
    return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]


def test_corrected_audit_is_separate_from_historical_attribution() -> None:
    e = evidence()
    old, corrected = e['attribution'], e['corrected_contact_box_audit']
    assert (old['positive_attack_enemy_pairs'], old['omission_attack_enemy_pairs'],
            old['remote_attack_human_pairs']) == (202, 166, 517)
    assert old['audit_status'] == 'historical; not the corrected contact-box audit'
    assert old['contact_box_interpretation'] == 'legacy direct edge offsets, not decoded half extents'
    assert old['corrected_supplement'] == 'corrected_contact_box_audit'
    assert corrected['schema_version'] == 1 and not corrected['historical_attribution_values_reinterpreted']
    assert corrected['source_commit'] == e['native_source_commit']
    provenance = corrected['provenance']
    assert provenance['supplement_manifest_sha256'] == (
        'cf510aa35558af44c7595fb19f6bc3073d92032d939317a406c4cf6a46b90ea0')
    assert provenance['report_sha256'] == '6cba857536b915940febcc2c5634259629fdb488830e7cefeda7bf17b126a19c'
    assert provenance['audit_result_sha256'] == '3216b79a5523e45ea1c96c9090e764840df8050b611fffa00abb488f15085ebb'
    assert provenance['audit_code_sha256'] == '9a12cfa6944092f3e4738e123a01cc6782500563616ad3dcc4a8fecb5875e7b6'
    assert provenance['source_sha256'] == {
        'katam/include/data.h': '02ca9bb101debdcc792e46cd00f413c660c866bd35758f81ff0a1d86d1440df1',
        'katam/include/object.h': '5ed2e44f4329b09b2acc1d9e20d9259d8c54d70dc6b8afc0431f60f1bca7aa38',
        'katam/include/kirby.h': '9874d9fae39c5af9c0c94b2abca2b7937b2af6f2e61232ebd662ccff6bc49f62',
        'katam/src/kirby.c': '041be2e8ff2c61026179d8c840b4680c9daa7308ecb76e0567c911d60efbf722',
        'katam/asm/code_08032E98.s': 'e06b6dd2bcac9a2aef40cc1452f431cd689b9e63c03674c13524a2f439f6a30a',
    }
    for source in ('katam/src/kirby.c', 'katam/asm/code_08032E98.s'):
        assert provenance['source_sha256'][source] == e['source_sha256'][source]
    assert corrected['limits'] == {
        'new_native_trials': 0, 'raw_fields_modified': False, 'profile_projection': False,
        'within_frame_omniscience': False, 'helper_inactivity_proved': False, 'live6_route_success': False,
        'host_rules_changed': False, 'broader_seed_rng_ingress_or_boss_claim': False,
    }


def test_corrected_audit_keeps_each_raw_case_and_pair_category() -> None:
    e = evidence()
    cases = e['corrected_contact_box_audit']['cases']
    assert len(cases) == len(e['cases']) == 5
    assert [case['cumulative_attempt'] for case in cases] == [7, 8, 9, 12, 13]
    for case, accepted in zip(cases, e['cases']):
        assert case['name'] == accepted['name'] and case['cumulative_attempt'] == accepted['cumulative_attempt']
        assert case['raw_states_sha256'] == accepted['states_sha256']
        omission = case['cumulative_attempt'] == 9
        expected = {'body_enemy': 3104 if omission else 3004,
                    'human_attack_enemy': 182 if omission else 220, 'remote_attack_human': 538}
        assert case['pair_observations'] == expected
        assert case['total_pair_observations'] == sum(expected.values()) == (3824 if omission else 3762)
        assert case['sample_count'] == (1153 if omission else 1104)
        assert (case['first_frame'], case['last_frame']) == (1085, 2237 if omission else 2188)
        assert case['observed_overlaps'] == 0
    assert [case['raw_states_bytes'] for case in cases] == [11388527, 11388527, 11757417, 11422472, 11422472]


def test_corrected_layout_and_scope_contract() -> None:
    corrected = evidence()['corrected_contact_box_audit']
    assert corrected['layout'] == {
        'source_type': 'ObjectBase', 'contact_offsets': [56, 57, 58, 59],
        'contact_encoding': ['left', 'top', 'half_width', 'half_height'],
        'contact_right': 'left + 2 * half_width', 'contact_bottom': 'top + 2 * half_height',
        'source_extent_storage': 'abs(edge_difference) >> 1; odd extents truncate',
        'terrain_offsets': [60, 61, 62, 63], 'terrain_encoding': ['left', 'top', 'right', 'bottom'],
    }
    assert corrected['method'] == {
        'contact_positions': 'floor fixed-point coordinates to integer pixels',
        'terrain_positions': 'retain fractional pixel coordinates',
        'horizontal_orientations': 'union original and mirrored intervals',
        'mirrored_contact_left': '-left - 2 * half_width', 'vertical_orientation': 'source top/bottom; not mirrored',
        'body_enemy_boxes': 'decoded contact boxes only',
        'attack_comparison_boxes': 'union terrain bounds and decoded contact boxes',
        'endpoint_policy': 'current and previous same-identity hulls; retain destroyed and disappeared endpoints',
        'identity_fields': ['task', 'address', 'template', 'parent'], 'regular_enemy_type_range': [0, 55],
        'room_matching_required': True, 'chain_propagation_excluded': '0x0800E27D',
        'effect_objects_and_untyped_tasks_boxed': False, 'boundary_touch_counts_as_overlap': True,
        'count_unit': 'eligible frame-by-frame pair observations, not unique actors or native trials',
    }


def test_contact_half_extent_bytes_are_not_terrain_edges() -> None:
    raw = bytearray(0x40)
    struct.pack_into('4b', raw, 0x38, -10, 6, 11, 3)
    struct.pack_into('4b', raw, 0x3C, -4, -3, 5, 7)
    layout = evidence()['corrected_contact_box_audit']['layout']
    record = {'x': 10.75, 'y': 20.75,
              'damage_box': struct.unpack_from('4b', raw, layout['contact_offsets'][0]),
              'bounds': struct.unpack_from('4b', raw, layout['terrain_offsets'][0])}
    assert _source_box(record, True) == (-2, 26, 22, 32)
    assert _source_box(record, False) == (5.75, 17.75, 15.75, 27.75)
    assert _attack_box(record) == (-2, 17.75, 22, 32)


@pytest.mark.parametrize(('xy', 'stored', 'expected'), [
    ((10.75, 20.75), (-4, -2, 4, 4), (6, 18, 14, 26)),
    ((10.75, 20.75), (-10, 6, 11, 3), (-2, 26, 22, 32)),
    ((-0.25, -0.25), (-4, -2, 4, 4), (-5, -3, 3, 5)),
    ((0.0, 0.0), (2, 3, 3, 2), (-8, 3, 8, 7)),
    ((0.0, 0.0), (0, 0, 0, 0), (0, 0, 0, 0)),
])
def test_contact_floor_half_extents_and_horizontal_mirror(
    xy: tuple[float, float], stored: tuple[int, int, int, int], expected: _Box,
) -> None:
    assert _source_box({'x': xy[0], 'y': xy[1], 'damage_box': stored}, True) == expected


def test_odd_source_extents_truncate_before_decoding() -> None:
    left, top, right, bottom = -3, -5, 4, 6
    stored = (left, top, abs(right - left) >> 1, abs(bottom - top) >> 1)
    assert stored == (-3, -5, 3, 5)
    assert _source_box({'x': 0, 'y': 0, 'damage_box': stored}, True) == (-3, -5, 3, 5)
    with pytest.raises(AssertionError, match='nonnegative'):
        _source_box({'x': 0, 'y': 0, 'damage_box': (-3, -5, -1, 5)}, True)


def test_body_contact_is_distinct_from_attack_terrain_union() -> None:
    human = {'x': 0, 'y': 0, 'damage_box': (-1, -1, 1, 1), 'bounds': (-10, -10, 10, 10)}
    enemy = {'x': 5, 'y': 0, 'damage_box': (-1, -1, 1, 1), 'bounds': (-1, -1, 1, 1)}
    assert not _observed_overlap(_source_box(human, True), _source_box(enemy, True))
    assert _observed_overlap(_attack_box(human), _attack_box(enemy))
    assert _observed_overlap((-1, -1, 1, 1), (1, -1, 3, 1)), 'Boundary contact is not separation'


def test_destroyed_disappeared_and_reused_identity_endpoints_are_retained() -> None:
    old = {'task': 't', 'address': 'a', 'template': 'source', 'parent': 'human', 'flags': 0,
           'x': 0, 'y': 0, 'damage_box': (-1, -1, 1, 1), 'bounds': (-1, -1, 1, 1)}
    destroyed = dict(old, x=10, flags=0x1000)
    assert _retained_endpoints([destroyed], [old]) == [destroyed]
    assert _swept_attack_box(destroyed, [old]) == (-1, -1, 11, 1)
    assert _retained_endpoints([], [destroyed]) == [destroyed]
    assert _swept_attack_box(destroyed, [destroyed]) == (9, -1, 11, 1)
    for field in ('task', 'address', 'template', 'parent'):
        replacement = dict(destroyed, **{field: 'new-identity'})
        assert _retained_endpoints([replacement], [old]) == [replacement, old]
        assert _swept_attack_box(replacement, [old]) == (9, -1, 11, 1)
