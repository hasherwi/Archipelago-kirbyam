"""Public controller evidence retains complete input spans and negative controls."""
import json
from pathlib import Path

ROOT = Path(__file__).parents[1] / 'dev-docs'


def load(name):
    return json.loads((ROOT / name).read_text())


def assert_inputs(run):
    frame = 0
    for row in run['inputs']:
        assert row['start'] == frame
        assert row['frames'] >= 0 and not row['keys'] & 768  # No Phone/shoulder input.
        frame += row['frames']
    assert not run['helpers_in_route'] and run['state_restores'] == 0
    assert all(w['frame'] == 1085 and not w['guard_failed'] for w in run['runtime_writes'])
    for key in ('rom_sha256', 'bridge_sha256', 'inputs_sha256', 'trace_sha256'):
        assert len(run[key]) == 64
    return frame


def test_explicit_timer_has_matched_native_control_without_equipment():
    record = load('room16-normal-timer-acceptance.json')
    positive, control = record['runs']
    assert positive['inputs'] == control['inputs']
    assert record['patch'] == {'rom_offset': '0x008C2708', 'native_value': 0, 'patched_value': 600}
    for run in (positive, control):
        assert_inputs(run)
        assert run['ability_ids'] == [0] and run['hp_min'] == run['hp_max'] == 6
        assert len(run['runtime_writes']) == 8
        assert next(w for w in run['runtime_writes'] if w['address'] == '0x203b064')['value'] == '02000000'
    assert positive['events']['entered325']['frame'] == 4698
    assert 'entered325' not in control['events']
    assert positive['rom_sha256'] != control['rom_sha256']


def test_fire_source_precedes_contact_crossing_and_chest_in_repeated_runs():
    record = load('olive-sound-effects-fire-acceptance.json')
    runs = {r['id']: r for r in record['runs']}
    for name in ('fire-repeat-0', 'fire-repeat-37', 'fire-repeat-211', 'fire-client-positive'):
        run = runs[name]
        end = assert_inputs(run)
        e = run['events']
        assert e['entry831']['frame'] < e['entry825']['frame'] < e['fire_acquired']['frame']
        assert e['fire_acquired']['frame'] < e['switch825']['frame'] < e['chest66']['frame'] < end
        assert e['switch825']['ability'] == e['chest66']['ability'] == 1
        assert not run['runtime_writes']
    control = runs['fire-no-target-attack']
    assert_inputs(control)
    assert 'switch825' not in control['events'] and 'chest66' not in control['events']
    assert record['client_control']['client_messages'] == []
    expected = [{'cmd': 'LocationChecks', 'locations': [3960523]}]
    assert runs['fire-client-positive']['client_messages'] == expected
    shuffled = record['shuffled_confirmation']
    assert shuffled['client_messages'] == expected and shuffled['policy']['mode'] == 1
    assert len(shuffled['runtime_writes']) == 8 and not shuffled['helpers_in_route']
    assert all(p['parent'] == '0x2020ee0' and p['mask'] == '0xa0000103'
               for sample in record['contact_attack_samples'] for p in sample['packets'])


def test_generation_profiles_keep_full_validation_and_match_rom_tokens():
    record = load('room16-fire-generation.json')
    rows = record['profiles']
    assert len(rows) == 16 and all(r['status'] == 'passed' and r['verified_slot_policy'] for r in rows)
    for row in rows:
        assert row['options']['accessibility'] == 'full'
        assert row['verified_timer_token'] == (600 if row['options']['ability_randomization_mode'] == 2 else 0)
    live = [r for r in rows if r['options']['ability_randomization_mode'] == 2]
    assert {(r['options']['room_sanity'], r['options']['goal'], r['options']['ability_gating']) for r in live} == {
        (rooms, goal, gating) for rooms in (0, 1) for goal in ('dark_mind', 'full_completion') for gating in (0, 1)}
