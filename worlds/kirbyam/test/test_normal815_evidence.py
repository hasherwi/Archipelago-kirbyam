"""Bounded reviewed Normal 815 contracts, not emulator or upstream replay tests."""

import json
from pathlib import Path

import pytest
from BaseClasses import CollectionState
from test.general import setup_multiworld

from .. import KirbyAmWorld
from ..data import data, load_json_data

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'dev-docs/olive-normal815-acceptance.json'
OWNER = 'REGION_OLIVE_OCEAN/ROOM_6_CHEST_1'
KEY = 'VITALITY_CHEST_OLIVE_OCEAN'


def evidence():
    return json.loads(EVIDENCE.read_text(encoding='utf-8'))


def test_exact_vitality_ownership_preserves_ordinary_rule_and_other_surfaces():
    assert evidence()['target'] == {
        'owner': OWNER, 'location_key': KEY, 'location_id': 3960301,
        'native_room': 815, 'chest_template': '0x088CCC90', 'requirement': 'can_break_block',
    }
    assert data.locations[KEY].parent_region == OWNER
    assert data.locations[KEY].location_id == 3960301
    room = load_json_data('regions/rooms.json')[OWNER]
    assert room['locations'][KEY] == 'can_break_block'
    assert room['locations']['room_sanity'] == {'included': True, 'location_id': 3961152, 'bit_index': 200}
    assert room['exits'] == {'REGION_OLIVE_OCEAN/ROOM_6_16': {'any': ['can_break_block', 'can_swim']}}
    assert 'traversal' not in room


@pytest.mark.parametrize('ability_gating', [0, 1])
@pytest.mark.parametrize('ability_randomization_mode', [0, 1, 2])
def test_local_rule_does_not_require_copy_item_or_health(ability_gating, ability_randomization_mode):
    mw = setup_multiworld(KirbyAmWorld, seed=815, options={
        'ability_gating': ability_gating, 'ability_randomization_mode': ability_randomization_mode,
        'minimum_health': 1, 'maximum_health': 1,
    })
    # This tests only the local AP predicate, not arrival reachability or a new native replay.
    assert mw.get_location(data.locations[KEY].label, 1).access_rule(CollectionState(mw))


def test_four_cases_and_one_bit_control_are_bounded():
    e = evidence()
    assert {(c['actual_hp'], c['enemy_health_multiplier']) for c in e['matrix']} == {
        (1, 100), (1, 500), (6, 100), (6, 500),
    }
    for c in e['matrix'] + [e['control']]:
        assert (c['sample_start'], c['sample_end'], c['sample_count']) == (1085, 3945, 2861)
        assert c['normal_every_sample'] and c['helpers_remain_101'] and c['damage_taken'] == 0
        assert c['blipper_hp_observed'] == [1, 2 if c['enemy_health_multiplier'] == 100 else 10]
    for c in e['matrix']:
        assert c['local_client_messages'] == [{'cmd': 'LocationChecks', 'locations': [3960301]}]
        assert (c['vitality_register'], c['event_counter']) == (2, 1)
    c = e['control']
    assert (c['actual_hp'], c['enemy_health_multiplier']) == (6, 100)
    assert (c['difference_frame'], c['identical_state_prefix_through']) == (3525, 3525)
    assert (c['success_keys'], c['control_keys'], c['omitted_key_bit']) == (18, 16, 2)
    assert not c['lower_gate_crossing'] and c['local_client_messages'] == []
    assert (c['vitality_register'], c['event_counter']) == (0, 0)


def test_moved_block_contact_and_intrinsic_puff_are_not_payload_or_latch():
    m = evidence()['mechanism']
    assert m['silver_block_template'] == '0x088CCCFC' and not m['block_consumed_or_spat']
    assert [m[k] for k in ('block_x_before', 'block_x_2336', 'block_x_2388')] == [184, 183.75, 182.75]
    assert m['block_contact_rect'] == [175, 127, 189, 143]
    assert m['switch_contact_rect'] == [161, 135, 175, 143]
    assert m['inclusive_integer_contact_x'] == 175
    assert m['maintained_lower_switch_from'] == 2388 and m['upper_gate_crossing_frame'] == 2562
    assert (m['final_puff_input_frame'], m['puff_spawn_frame']) == (3525, 3526)
    assert m['puff_damage_bounds'] == [-5, -5, 5, 5]
    assert m['upper_switch_active_interval'] == [3535, 3546] and m['upper_switch_release_frame'] == 3547
    assert m['lower_gate_crossing_frame'] == 3600 and m['lower_gate_crossing_bounds'] == [-8, -32, 8, -16]
    assert (m['beyond_lower_gate_frame'], m['slide_frame'], m['physical_chest_frame']) == (3610, 3666, 3807)
    assert not m['gate_latch'] and not m['underwater_553_exit_used']
    assert load_json_data('abilities.json')['Normal']['safe_to_gate'] is False
    assert 'Normal Ability' not in {item.label for item in data.items.values()}


def test_clean_setup_boundary_and_review_limits():
    e = evidence()
    assert e['boundary'] == {
        'room': 551, 'stored_xy': [1168, 288], 'next_room': 815,
        'transition_frame': 1288, 'next_xy': [72, 136.99609375],
    }
    assert e['setup'] == {
        'startup_only_fixture_byte_differences': 17, 'client_configuration_writes': 8,
        'configuration_frame': 1085, 'blank_battery_boot': True, 'gameplay_writes': False,
        'runtime_rom_writes': False, 'state_restores': False, 'server_transmission': False,
        'ability_gating': 0, 'area_keys': 0, 'enemy_copy_mode': 1, 'allowed_ability_count': 25,
        'seed': 2, 'no_ability_weight': 0,
    }
    limits = ' '.join(e['limitations'])
    for boundary in ('not arbitrary 551', 'new-game', 'No generic Normal', 'RoomSanity',
                     'fresh emulator replay', 'collision-map tile', 'not boot frame 0', 'No health restriction'):
        assert boundary in limits
    inventory = json.loads((ROOT / 'dev-docs/small-switch-inventory.json').read_text())
    room = next(r for r in inventory['rooms'] if r['native_id'] == 815)
    assert room['assessment']['classification'] == 'reviewed_normal_moved_block_and_puff'
    assert room['assessment']['evidence'] == EVIDENCE.name


def test_sanitized_provenance_pins_recorded_evidence():
    e = evidence()
    assert e['production_source_commit'] == 'a1c2cffee0fdb0ae49872cd6b86dbab99b53b5d9'
    assert e['integration_base'] == '7a417dc96ef8902401aa32533f6ea6b85ce28a9f'
    assert e['native_source_commit'] == '7d969fbce14fdc838d2c1ea01389717fb96c3189'
    assert e['private_artifact_sha256']['summary.json'] == (
        '6cb783bfa46da133ab1eb69cb70e1f87fd373c73102f2baddb8f6f2cb799481b')
    assert e['private_artifact_sha256']['review-report.md'] == (
        '7bd2fc8fd24a21a23c4a5694cb89bc7c1bfa904408d651b70eff9ba6daa55bc2')
    hashes = list(e['private_artifact_sha256'].values())
    for c in e['matrix'] + [e['control']]:
        hashes.extend(c[k] for k in ('input_sha256', 'states_sha256', 'result_sha256'))
    assert all(len(h) == 64 and int(h, 16) >= 0 for h in hashes)
    for path in (EVIDENCE, EVIDENCE.with_name('olive-normal815-source-witness.md')):
        text = path.read_text(encoding='utf-8')
        assert all(private not in text for private in ('/home/', '/Users/', 'C:\\', 'D:\\'))
    assert not any(key in e for key in ('inputs', 'frames', 'replay', 'savestate'))
