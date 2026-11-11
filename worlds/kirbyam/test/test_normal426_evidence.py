"""Reviewed Normal 426 scalar contracts, not emulator replays or upstream proofs."""

import json
from pathlib import Path

import pytest
from BaseClasses import CollectionState
from test.general import setup_multiworld

from .. import KirbyAmWorld
from ..data import data, load_json_data

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'dev-docs/candy-normal426-acceptance.json'
OWNER = 'REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_3'
KEY = 'MAJOR_CHEST_CANDY_CONSTELLATION'


def evidence():
    return json.loads(EVIDENCE.read_text(encoding='utf-8'))


def test_exact_map_ownership_preserves_null_rule_and_separate_surfaces():
    assert evidence()['target'] == {
        'owner': OWNER, 'location_key': KEY, 'location_id': 3960208,
        'native_room': 426, 'chest_template': '0x088C87FC', 'requirement': None,
    }
    assert data.locations[KEY].parent_region == OWNER
    assert data.locations[KEY].location_id == 3960208
    assert load_json_data('locations.json')[KEY]['bit_index'] == 9
    room = load_json_data('regions/rooms.json')[OWNER]
    assert room['locations'][KEY] is None
    assert room['exits'] == {'REGION_CANDY_CONSTELLATION/ROOM_9_GOAL_2': None}
    assert room['locations']['room_sanity'] == {'included': True, 'location_id': 3961254, 'bit_index': 167}
    assert 'traversal' not in room


@pytest.mark.parametrize('ability_gating', [0, 1])
@pytest.mark.parametrize('ability_randomization_mode', [0, 1, 2])
def test_local_map_rule_needs_no_copy_item_or_health_gate(ability_gating, ability_randomization_mode):
    mw = setup_multiworld(KirbyAmWorld, seed=426, options={
        'ability_gating': ability_gating, 'ability_randomization_mode': ability_randomization_mode,
        'minimum_health': 1, 'maximum_health': 1,
    })
    # Local rule only, not proof of reaching the parent region or a gated native replay.
    assert mw.get_location(data.locations[KEY].label, 1).access_rule(CollectionState(mw))


def test_three_bounded_cases_keep_exact_target_client_and_health():
    e = evidence()
    assert {(c['actual_hp'], c['enemy_health_multiplier']) for c in e['matrix']} == {(1, 100), (1, 500), (6, 100)}
    for c in e['matrix'] + [e['control']]:
        assert (c['sample_start'], c['sample_end'], c['sample_count']) == (1085, 4154, 3070)
        assert c['sample_count'] == c['sample_end'] - c['sample_start'] + 1
        assert c['normal_every_sample'] and c['damage_taken'] == 0 and not c['helpers_in_426']
    for c in e['matrix']:
        assert c['local_client_messages'] == [{'cmd': 'LocationChecks', 'locations': [3960208]}]
        assert c['transport_flag'] == '0x200'
    control = e['control']
    assert (control['actual_hp'], control['enemy_health_multiplier']) == (6, 100)
    assert (control['difference_frame'], control['identical_state_prefix_through']) == (2782, 2782)
    assert (control['success_keys'], control['control_keys'], control['omitted_key_bit']) == (17, 16, 1)
    assert control['maximum_x_in_426'] == 250.375
    assert control['local_client_messages'] == [] and control['transport_flag'] == '0x0'
    assert not any(control[k] for k in (
        'first_complete_crossing', 'middle_switch_active', 'lower_switch_active', 'physical_chest_event',
    ))


def test_retained_contact_timing_and_loaded_only_latches():
    e = evidence()
    assert e['boundary'] == {
        'room': 419, 'stored_xy': [1184, 256], 'observed_xy': [1176, 248.99609375],
        'frame': 1085, 'up_frame': 1086, 'next_room': 426, 'transition_frame': 1098,
        'next_xy': [72, 56.99609375],
    }
    m = e['mechanism']
    assert m['first_switch_active_intervals'] == [[2009, 2020], [2194, 2205], [2635, 2704], [2723, 2764]]
    assert [m[k] for k in ('jump_frame', 'first_complete_crossing_frame', 'middle_switch_frame',
                           'lower_switch_frame', 'final_complete_crossing_frame', 'physical_chest_frame')] == [
        2782, 2807, 2820, 3218, 3788, 3976,
    ]
    assert m['first_crossing_gate_bounds'] == [-8, -32, 8, -20]
    assert m['final_crossing_gate_bounds'] == [-8, -32, 8, -28]
    assert m['latch_flag'] == '0x4' and m['latch_scope'] == 'While the room remains loaded only.'
    assert m['switch_template_modes'] == {'5': '0x8004', '6': '0x0004'}
    assert m['f1_tile'] == [25, 3] and m['f1_action'] == 'Ordinary down+B slide before the chest.'
    assert m['equipment'] == 'Normal' and m['local_enemies'] == 0 and not m['copy_ability_required']
    assert load_json_data('abilities.json')['Normal'] == {
        'runtime_ability_id': 0, 'safe_to_gate': False, 'enemy_copy_allowed': False,
    }
    assert 'Normal Ability' not in {item.label for item in data.items.values()}


def test_clean_setup_and_explicit_evidence_limits():
    e = evidence()
    assert e['setup'] == {
        'startup_only_fixture_byte_differences': 17, 'client_configuration_writes': 8,
        'configuration_frame': 1085, 'blank_battery_boot': True, 'gameplay_writes': False,
        'runtime_rom_writes': False, 'state_restores': False, 'helpers_in_route': False,
        'server_transmission': False, 'ability_gating': 0, 'area_keys': 0,
        'enemy_copy_mode': 1, 'allowed_ability_count': 25, 'seed': 2,
    }
    limits = ' '.join(e['limitations'])
    for boundary in ('not arbitrary 419', 'not boot frame 0', 'No 426 to 420', 'RoomSanity',
                     'No room-reset', 'No 6 HP / 500%', 'no health restriction', 'fresh emulator replay'):
        assert boundary in limits


def test_private_provenance_is_pinned_without_raw_payloads():
    e = evidence()
    assert e['production_source_commit'] == 'd04d4d0bec97f116a95d318e9a0d21518b615b72'
    assert e['integration_base'] == 'a1c2cffee0fdb0ae49872cd6b86dbab99b53b5d9'
    assert e['native_source_commit'] == '7d969fbce14fdc838d2c1ea01389717fb96c3189'
    assert e['private_artifact_sha256']['manifest.json'] == (
        'd7d6980a0ed6db81a6e75cfddb01618f4e596c7af3bd425f7c00d2083240bc37')
    hashes = list(e['private_artifact_sha256'].values())
    for c in e['matrix'] + [e['control']]:
        hashes.extend(c[k] for k in ('input_sha256', 'states_sha256', 'result_sha256'))
    assert all(len(h) == 64 and int(h, 16) >= 0 for h in hashes)
    for path in (EVIDENCE, EVIDENCE.with_name('candy-normal426-source-witness.md')):
        text = path.read_text(encoding='utf-8')
        assert all(private not in text for private in ('/home/', '/Users/', 'C:\\', 'D:\\'))
    assert not any(key in e for key in ('inputs', 'frames', 'replay', 'savestate'))
