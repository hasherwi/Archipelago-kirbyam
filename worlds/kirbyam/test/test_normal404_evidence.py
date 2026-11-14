"""Frozen Normal404 scalar contracts and host predicates, not native replays."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from BaseClasses import CollectionState
from test.general import setup_multiworld

from .. import KirbyAmWorld
from ..area_keys import area_key_entrance_area_ids
from ..data import data
from ..tools.build_ranged_completion_status import build_status
from ..tools.build_ranged_target_coverage import build_coverage

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'dev-docs/candy-normal404-acceptance.json'
PREFIX = 'REGION_CANDY_CONSTELLATION/'
ROOM = PREFIX + 'ROOM_9_01'
PARENT = PREFIX + 'ROOM_9_CHEST_2'
OWNER = PARENT + '__LOGIC__ENTRY_FROM_9_01'
OTHER = PARENT + '__LOGIC__ENTRY_FROM_9_09'
SINK = PARENT + '__ROOM_CHECK'
KEY = 'MINOR_CHEST_SPRAY_PAINT_06'
ADMISSIONS = {
    'REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE_UPPER_PLATFORMS': PREFIX + 'ROOM_9_HUB',
    'REGION_MOONLIGHT_MANSION/ROOM_2_WARP': PREFIX + 'ROOM_9_04',
    'REGION_MUSTARD_MOUNTAIN/ROOM_4_WARP': PREFIX + 'ROOM_9_06',
    'REGION_PEPPERMINT_PALACE/ROOM_7_WARP': ROOM,
}


def evidence() -> dict[str, Any]:
    result: dict[str, Any] = json.loads(EVIDENCE.read_text(encoding='utf-8'))
    return result


def digest(value: Any) -> str:
    # Semantic JSON hashes survive platform checkout line-ending conversion.
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate_record(e: dict[str, Any]) -> None:
    """Fail closed on evidence overclaims, not on untested native approaches."""
    assert e['target'] == {
        'owner': OWNER, 'location_key': KEY, 'location_id': 3960505,
        'native_room': 403, 'chest_template': '0x088C5EA0', 'requirement': None,
    }
    assert e['boundary'] == {
        'accepted_ingress': 427, 'stored_xy': [696, 80], 'observed_xy': [680, 72.99609375],
        'frame': 1085, 'next_room': 404, 'transition_frame': 1097,
        'next_xy': [40, 136.99609375], 'unaccepted_ingresses': [407, 230],
    }
    assert e['setup'] == {
        'startup_only_fixture_byte_differences': 16, 'client_configuration_writes': 8,
        'configuration_frame': 1085, 'startup_write_mode': 'harness-fenced', 'protocol_guard_requests': 0,
        'blank_battery_boot': True, 'gameplay_writes': False, 'runtime_rom_writes': False,
        'state_restores': False, 'server_transmission': False, 'ability_randomization_mode': 0,
        'ability_gating': 0, 'area_keys': 0, 'seed': 404, 'global_ai': 0, 'num_humans': 1,
    }
    m = e['mechanism']
    assert (m['equipment'], m['copy_ability_required'], m['helper_participation'], m['source_acquisition']) == (
        'Normal', False, False, False)
    assert [m[k] for k in ('lower_f1', 'support', 'upper_f1', 'door_tile')] == [
        [27, 6], [27, 5], [27, 4], [20, 4]]
    assert (m['door_record'], m['door_destination_room'], m['door_spawn_tiles']) == ('0x088940BC', 403, [7, 9])
    assert (m['switch_template'], m['switch_xy'], m['gate_template'], m['gate_xy']) == (
        '0x088C600C', [440, 64], '0x088C6030', [360, 80])
    assert (m['switch_flags'], m['room_state_slot'], m['release_counter_parameter']) == (0, 0, 0)
    assert m['release_countdown_frames'] == [1911, 1912] and m['gate_fully_closed_frame'] == 1991
    assert (m['puff_parent'], m['puff_category'], m['puff_damage']) == ('0x02020EE0', '0x20000042', 2)
    assert m['stored_pointer_is_not_continuous_contact'] is True
    assert 'destruction-flag 0x1000' in m['active_doo_only'] and 'non-combat despawn' in m['active_doo_only']
    assert len(e['matrix']) == 3
    assert {(r['positive']['actual_hp'], r['positive']['enemy_health_multiplier']) for r in e['matrix']} == {
        (6, 100), (1, 100), (1, 500)}
    for row in e['matrix']:
        p, r, c = (row[k] for k in ('positive', 'repeat', 'control'))
        assert row['cold_repeat_all_sampled_states_identical'] is True
        assert row['identical_prefix_through'] == 1869
        assert row['omission_input'] == {'frame': 1869, 'positive_keys': 2, 'control_keys': 0}
        assert p['input_sha256'] == r['input_sha256'] and p['states_sha256'] == r['states_sha256']
        for run in (p, r, c):
            assert (run['actual_hp'], run['enemy_health_multiplier']) == (p['actual_hp'], p['enemy_health_multiplier'])
            assert (run['sample_start'], run['sample_end'], run['sample_count']) == (1085, 2277, 1193)
            assert run['sample_count'] == run['sample_end'] - run['sample_start'] + 1
            assert run['normal_every_sample'] is True and run['damage_taken'] == run['copy_events'] == 0
            assert run['helpers_only_room'] == 101 and run['helper_participation'] is False
            assert run['active_doo_hp'] == (4 if run['enemy_health_multiplier'] == 100 else 20)
        for run in (p, r):
            assert run['local_client_messages'] == [{'cmd': 'LocationChecks', 'locations': [3960505]}]
            assert (run['event_counter'], run['event_source']) == (1, '0x088C5EA0')
            assert run['milestones'] == {
                'entry404': 1097, 'lower_f1': 1872, 'support': 1878, 'upper_f1': 1884,
                'switch_press': 1903, 'revealed_door': 1926,
                'fully_past_gate': 1982 if run['actual_hp'] == 6 else 1978,
                'entry403': 2008, 'chest_animation': 2189,
            }
            assert run['contact_windows'] == {
                'integer_rectangle_overlap': [1902, 1909], 'current_contact_bit_0x100': [1903, 1910],
                'slot0_high': [1903, 1912], 'opening_callback': [1904, 1946], 'closing_callback': [1948, 1990],
            }
        assert c['local_client_messages'] == [] and (c['event_counter'], c['event_source']) == (0, '0x00000000')
        assert c['final_room'] == 404 and c['causal_cells_intact'] is True and c['gate_remains_closed'] is True
    assert e['controller_correction'] == {
        'changed_input_frames': list(range(1882, 1890)), 'before_keys': 80, 'after_keys': 64,
        'same_100_500_human_trajectory': True,
    }
    failed = e['excluded_literal_6hp_controller_at_1hp']
    assert (failed['case'], failed['first_death_frame'], failed['accepted']) == ('positive100-1hp', 1905, False)
    physical = e['physical_outcome']
    assert [physical[k] for k in ('group', 'previous_classification', 'classification')] == [
        '404:27,4', 'unbound_timed_check_route', 'qualified_normal427_to_paint6_route']
    assert physical['trigger_cells'] == [[27, 4], [27, 6]] and physical['observed_initial_trigger'] == [27, 6]
    fields = ('newly_evidenced_outcomes', 'independent_trigger_recipes', 'groups',
              'historical_prior_unadjudicated_cells', 'role_reconciled_or_narrowed_cells',
              'unresolved_role_cells', 'unresolved_role_groups', 'previously_narrowed_cells_in_this_group')
    assert [physical[k] for k in fields] == [1, 1, 304, 395, 43, 352, 249, 2]


def test_frozen_evidence_contract() -> None:
    validate_record(evidence())


@pytest.mark.parametrize('path,value', [
    (('target', 'owner'), OTHER), (('target', 'location_id'), 3960300),
    (('target', 'chest_template'), '0x088C600C'), (('target', 'requirement'), 'Beam Ability'),
    (('boundary', 'accepted_ingress'), 407), (('boundary', 'unaccepted_ingresses'), []),
    (('mechanism', 'room_state_slot'), 1), (('mechanism', 'helper_participation'), True),
    (('mechanism', 'equipment'), 'Beam'), (('setup', 'protocol_guard_requests'), 8),
    (('setup', 'server_transmission'), True), (('matrix', 0, 'positive', 'sample_count'), 1192),
    (('matrix', 0, 'positive', 'contact_windows', 'integer_rectangle_overlap'), [1903, 1912]),
    (('matrix', 1, 'control', 'local_client_messages'), [{'cmd': 'LocationChecks', 'locations': [3960505]}]),
    (('matrix', 1, 'identical_prefix_through'), 1868), (('matrix', 2, 'positive', 'actual_hp'), 6),
    (('excluded_literal_6hp_controller_at_1hp', 'accepted'), True),
    (('controller_correction', 'changed_input_frames'), [1882]),
    (('physical_outcome', 'unresolved_role_cells'), 350),
    (('physical_outcome', 'independent_trigger_recipes'), 2),
])
def test_evidence_mutations_cannot_broaden_acceptance(path: tuple[str | int, ...], value: Any) -> None:
    mutated = deepcopy(evidence())
    target: Any = mutated
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(AssertionError):
        validate_record(mutated)


def test_exact_ownership_null_edge_and_terminal_sink() -> None:
    room = data.regions[ROOM]
    assert set(room.exits) == {PREFIX + 'ROOM_9_02', PREFIX + 'ROOM_9_07', OWNER}
    assert not room.exit_requirements and not room.traversal
    assert data.locations[KEY].parent_region == OWNER
    assert data.locations[KEY].location_id == 3960505
    assert data.locations[KEY].source_rom_offset == 0x008C5EA0
    assert [r.name for r in data.regions.values() if KEY in r.locations] == [OWNER]
    assert data.locations['VITALITY_CHEST_CANDY_CONSTELLATION'].parent_region == OTHER
    assert set(data.regions[PREFIX + 'ROOM_9_09'].exits) == {OTHER, PREFIX + 'ROOM_9_08'}
    for owner, entry in ((OWNER, ROOM), (OTHER, PREFIX + 'ROOM_9_09')):
        assert set(data.regions[owner].exits) == {entry, SINK}
        assert not data.regions[owner].exit_requirements
        assert PARENT not in data.regions[owner].exits
    assert data.regions[SINK].exits == [] and data.regions[SINK].locations == ['ROOM_SANITY_9_CHEST_2']
    assert not data.regions[PARENT].locations
    abilities = json.loads((ROOT / 'data/abilities.json').read_text(encoding='utf-8'))
    assert abilities['Normal']['safe_to_gate'] is False
    assert 'Normal Ability' not in {item.label for item in data.items.values()}


@pytest.mark.parametrize('ability_gating', [0, 1])
@pytest.mark.parametrize('ability_randomization_mode', [0, 1, 2])
@pytest.mark.parametrize('area_keys', [0, 1])
def test_host_local_predicates_and_existing_candy_admissions(
    ability_gating: int, ability_randomization_mode: int, area_keys: int,
) -> None:
    # Local AP predicates only: these checks do not replay native settings or prove upstream access.
    mw = setup_multiworld(KirbyAmWorld, seed=404, steps=('generate_early', 'create_regions', 'set_rules'), options={
        'ability_gating': ability_gating, 'ability_randomization_mode': ability_randomization_mode,
        'area_keys': area_keys, 'minimum_health': 1, 'maximum_health': 1,
    })
    state = CollectionState(mw)
    assert mw.get_entrance(f'{ROOM} -> {OWNER}', 1).access_rule(state)
    assert mw.get_location(data.locations[KEY].label, 1).access_rule(state)
    world = mw.worlds[1]
    key_item = world.create_item('Candy Constellation - Area Key')
    hub_item = world.create_item('Candy Constellation - Hub Connection')
    key_state, hub_state, both = (CollectionState(mw) for _ in range(3))
    key_state.collect(key_item, prevent_sweep=True)
    hub_state.collect(hub_item, prevent_sweep=True)
    both.collect(key_item, prevent_sweep=True)
    both.collect(hub_item, prevent_sweep=True)
    assert {name for name, area in area_key_entrance_area_ids().items() if area == 9} == {
        f'{source} -> {dest}' for source, dest in ADMISSIONS.items()}
    for source, dest in ADMISSIONS.items():
        rule = mw.get_entrance(f'{source} -> {dest}', 1).access_rule
        is_hub = dest.endswith('ROOM_9_HUB')
        assert rule(state) is (not area_keys and not is_hub)
        assert rule(key_state) is (not is_hub)
        assert rule(hub_state) is (not area_keys)
        assert rule(both)


def test_current_host_structure_preserves_404_and_tracks_master719_and_green138_additions() -> None:
    coverage = build_coverage()
    status = build_status()
    contract = evidence()['host_contract']
    # Frozen404 native provenance remains 144; Master719 and Green138 each add exactly one graph.
    assert contract['counts']['witnesses'] == 144
    assert status['counts'] == {**contract['counts'], 'witnesses': 146,
                                'locations': 400, 'surfaces': 1107,
                                'regions': 386, 'mapped_native_definitions': 354}
    assert (len(data.regions), len(data.locations), len(coverage['surfaces']),
            len(coverage['installed_targets']), status['counts']['witnesses']) == (386, 400, 1107, 57, 146)
    # Project only the pinned feature surfaces, retaining the frozen native record.
    from .support.main_sync_history import main_surfaces
    assert digest(main_surfaces(coverage['surfaces'])) == contract['normalized_surface_sha256']
    # Strictly project Green off the unchanged Master-era catalog pin; keep frozen404 evidence.
    from .support.green138_history import before_green138
    historical = [{**row, 'target': before_green138(row['target'])}
                  for row in coverage['installed_targets']]
    assert digest(historical) == '76c369a269387b9e3812400689c2da0e9ab02a68476624e71817e9a6b48c8933'
    carrot = next(row['target'] for row in coverage['installed_targets']
                  if row['target']['id'] == 'bomb_719_room13')
    assert len(carrot['graphs']) == 5 and 'central_master' in carrot['graphs']
    assert 'requires_guaranteed_source' not in carrot and 'requires_any_guaranteed_source' not in carrot
    assert status['completion'] == 'partial' and not status['declaration_errors']
    scope = json.loads((ROOT / 'dev-docs/ranged-completion-scope.json').read_text(encoding='utf-8'))
    assert set(scope['policy_fallback_targets']) == {
        'bomb_517_chocolate', 'bomb_733_yellow',
        'switch_533_room16', 'switch_310_mustard_map',
    }
    for key in (ROOM, PREFIX + 'ROOM_9_02', PREFIX + 'ROOM_9_07', OWNER):
        assert not data.regions[key].traversal


def test_inventory_changes_are_404_assessment_only() -> None:
    inventory = json.loads((ROOT / 'dev-docs/small-switch-inventory.json').read_text(encoding='utf-8'))
    room = next(r for r in inventory['rooms'] if r['native_id'] == 404)
    assert room['assessment']['classification'] == 'reviewed_normal_puff_falling_switch'
    assert room['assessment']['evidence'] == EVIDENCE.name
    del room['assessment']
    assert digest(inventory) == '3ede15632071ad080abdbf1dbe1b83cef1669e9a3d4f0775362ee5b2d0659981'


def test_public_evidence_integrity_provenance_and_privacy() -> None:
    e = evidence()
    assert digest(e) == 'dcc7aef5d96dd145428601050a8d5f495364e1f5d83c4a71f0aba4f9a3530ec9'
    witness = EVIDENCE.with_name('candy-normal404-source-witness.md').read_text(encoding='utf-8')
    assert hashlib.sha256(witness.encode()).hexdigest() == (
        'cf7cb9c78205b57505c46b72801eae46783d9b8f0773ed8d1b0161db5d56dbce'
    )
    assert e['production_source_commit'] == '94c4e638c9de9793e589f3253379a1f5e4009118'
    assert e['production_source_tree'] == 'ef9cec4cd62afb06f14e23cce89ac0941eab19e0'
    assert e['native_source_commit'] == '7d969fbce14fdc838d2c1ea01389717fb96c3189'
    hashes = list(e['private_artifact_sha256'].values())
    for row in e['matrix']:
        hashes.extend(row[k] for k in ('production_sha256', 'fixture_sha256', 'generated_slot_sha256'))
        for kind in ('positive', 'repeat', 'control'):
            hashes.extend(row[kind][k] for k in ('input_sha256', 'states_sha256', 'result_sha256'))
    assert all(len(h) == 64 and int(h, 16) >= 0 for h in hashes)
    for text in (json.dumps(e), witness):
        assert all(private not in text for private in ('/home/', '/Users/', 'C:\\', 'D:\\'))
    assert not any(key in e for key in ('inputs', 'frames', 'replay', 'savestate', 'memory'))
    # Historical native limitations stay frozen; current fallback counts are checked above.
    limits = ' '.join(e['limitations'])
    for boundary in ('407', '230', 'No 6 HP / 500%', 'not server acknowledgement',
                     'not native replay evidence', 'Six conditional-source fallbacks', 'not a fresh emulator replay'):
        assert boundary in limits
