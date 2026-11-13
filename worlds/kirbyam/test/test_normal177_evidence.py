"""Reviewed Normal 177 scalar contracts, not emulator replays or upstream proofs."""

import json
from pathlib import Path

import pytest
from BaseClasses import CollectionState
from test.general import setup_multiworld

from .. import KirbyAmWorld
from ..data import data, load_json_data

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'dev-docs/rainbow-normal177-acceptance.json'
OWNER = 'REGION_RAINBOW_ROUTE/ROOM_1_GOAL_3'
KEY = 'MINOR_CHEST_RAINBOW_ROUTE_1_GOAL_3'


def evidence():
    return json.loads(EVIDENCE.read_text(encoding='utf-8'))


def test_exact_chest_ownership_preserves_null_rule_and_separate_exit():
    target = evidence()['target']
    assert target == {
        'owner': OWNER, 'location_key': KEY, 'location_id': 3960568,
        'native_room': 177, 'chest_template': '0x088BB0BC', 'requirement': None,
    }
    assert data.locations[KEY].parent_region == OWNER
    assert data.locations[KEY].location_id == 3960568
    assert load_json_data('locations.json')[KEY]['source_rom_offset'] == '0x008BB0BC'
    room = load_json_data('regions/rooms.json')[OWNER]
    assert room['locations'][KEY] is None
    assert room['exits'] == {'REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE': 'can_break_block'}
    assert room['locations']['room_sanity']['location_id'] == 3961047
    assert 'traversal' not in room


@pytest.mark.parametrize('ability_gating', [0, 1])
@pytest.mark.parametrize('ability_randomization_mode', [0, 1, 2])
def test_local_access_rule_needs_no_copy_item_or_health_gate(ability_gating, ability_randomization_mode):
    mw = setup_multiworld(KirbyAmWorld, seed=177, options={
        'ability_gating': ability_gating, 'ability_randomization_mode': ability_randomization_mode,
        'minimum_health': 1, 'maximum_health': 1,
    })
    chest = mw.get_location(data.locations[KEY].label, 1)
    # Only the location rule: parent-region reachability is deliberately not claimed.
    assert chest.access_rule(CollectionState(mw))


def test_four_original_ungated_recipes_and_matched_prefix_controls():
    e = evidence()
    assert e['boundary'] == {
        'room': 178, 'frame': 1085, 'xy': [1432, 136.99609375],
        'next_room': 177, 'transition_frame': 2635, 'next_xy': [712, 56.99609375],
    }
    rows = e['matrix']
    assert {(c['actual_hp'], c['enemy_health_multiplier']) for c in rows} == {
        (1, 100), (6, 100), (1, 500), (6, 500),
    }
    assert [(c['capture_frame'], c['shot_frame'], c['physical_chest_frame'], c['final_frame']) for c in rows] == [
        (10935, 11452, 11935, 12074), (14243, 14761, 15244, 15383),
        (32509, 32973, 33456, 33595), (31876, 32345, 32828, 32967),
    ]
    for c in rows:
        assert c['ability_gating'] == c['damage_taken'] == 0 and c['normal_every_frame']
        assert c['sample_count'] == c['final_frame'] - 1085 + 1
        assert c['local_client_locations'] == [3960568]
        assert c['source_templates'] == ['0x88baf78', '0x88baf9c' if (
            c['actual_hp'], c['enemy_health_multiplier']) == (1, 500) else '0x88bafc0']
        control = c['control']
        assert control == {
            'omitted_key_bit': 2, 'difference_frame': c['shot_frame'], 'stop_frame': c['shot_frame'] + 81,
            'final_x': 182, 'retained_mouth': 109, 'switch_slot2': 0,
            'chest_event_counter': 0, 'local_client_locations': [],
        }
        assert control['stop_frame'] < c['physical_chest_frame'] < c['final_frame']


def test_gated_no_items_supplement_is_separate_and_bounded():
    s = evidence()['gated_supplement']
    assert (s['actual_hp'], s['enemy_health_multiplier'], s['ability_gating']) == (1, 500, 1)
    assert s['items_received'] == [] and s['unlock_mask'] == 0
    assert s['gateable_mask'] == '0x03FFFE76'
    assert s['normal_every_frame'] and s['damage_taken'] == 0
    assert s['sample_count'] == 32924 and s['final_frame'] == 34008
    assert s['source_templates'] == ['0x88baf78', '0x88baf9c']
    assert s['capture_frame'] == 32917 and s['retained_mouth'] == 0x40
    assert [s[k] for k in ('shot_frame', 'gate_contact_frame', 'switch_contact_frame',
                           'switch_set_frame', 'physical_chest_frame')] == [33386, 33389, 33399, 33400, 33869]
    assert s['local_client_locations'] == [3960568]
    assert s['control'] == {
        'omitted_key_bit': 2, 'difference_frame': 33386, 'stop_frame': 33467,
        'sample_count': 32383, 'final_x': 182, 'retained_mouth': 64,
        'switch_slot2': 0, 'chest_event_counter': 0, 'local_client_locations': [],
    }


def test_object_contact_exception_is_not_generic_equipment_or_terrain_power():
    e = evidence()
    assert e['mechanism'] == {
        'equipment': 'Normal', 'same_pass_original_flamers': 2, 'star_damage': 25,
        'switch_slot': 2, 'dynamic_object_contact_bypass': True,
        'terrain_piercing': False, 'copy_ability_required': False,
    }
    assert e['setup'] == {
        'startup_only_fixture_byte_differences': 15, 'client_configuration_writes': 8,
        'blank_battery_boot': True, 'gameplay_writes': False, 'runtime_rom_writes': False,
        'state_restores': False, 'helpers_in_route': False, 'server_transmission': False,
    }
    assert load_json_data('abilities.json')['Normal'] == {
        'runtime_ability_id': 0, 'safe_to_gate': False, 'enemy_copy_allowed': False,
    }
    assert 'Normal Ability' not in {item.label for item in data.items.values()}
    assert any('No upstream 138' in limit for limit in e['limitations'])
    assert any('no health restriction' in limit for limit in e['limitations'])


def test_private_provenance_is_pinned_without_raw_payloads():
    e = evidence()
    assert e['production_source_commit'] == '6948ac7295d3b3e8e1eaf08506338592d707254e'
    assert e['integration_base'] == 'd04d4d0bec97f116a95d318e9a0d21518b615b72'
    assert e['native_source_commit'] == '7d969fbce14fdc838d2c1ea01389717fb96c3189'
    assert e['private_artifact_sha256']['acceptance-index-v1.json'] == (
        '87cb83bf16e5a274725637693856e5e54eadd3b9c16dc635de58496c0db8dba0')
    assert e['gated_supplement']['private_artifact_sha256']['acceptance-index-v2.json'] == (
        '61accc0642281f01c44ed92c5db6c18ece4261658ef13c1a2a47d0a04f6b25da')
    for hashes in (e['private_artifact_sha256'], e['gated_supplement']['private_artifact_sha256']):
        assert all(len(h) == 64 and int(h, 16) >= 0 for h in hashes.values())
    for path in (EVIDENCE, EVIDENCE.with_name('rainbow-normal177-source-witness.md')):
        text = path.read_text(encoding='utf-8')
        assert all(private not in text for private in ('/home/', '/Users/', 'C:\\', 'D:\\'))
    assert not any(key in e for key in ('inputs', 'frames', 'replay', 'savestate'))
