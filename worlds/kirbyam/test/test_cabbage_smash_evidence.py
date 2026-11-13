"""Guard the retained native evidence contract; these tests do not replay a ROM."""

import json
from pathlib import Path

from ..client import KirbyAmClient
from ..data import data
from ..enemy_ability_data import ABILITY_NAME_TO_ID, ABILITY_SOURCES
from ..enemy_ability_runtime_patch import (
    build_enemy_copy_runtime_patch_writes, build_enemy_source_runtime_config,
)
from ..traversal import SourcePolicy

EVIDENCE = Path(__file__).parents[1] / 'dev-docs' / 'cabbage-smash-source-runtime.json'
POSITIVE_RUNS = ('accepted-source100-6hp', 'final100-1hp', 'final500-6hp', 'final500-1hp')
CONTROLS = ('control-attack-window', 'control-no-approach-attacks')


def test_production_policy_and_exact_source_target_contract():
    evidence = json.loads(EVIDENCE.read_text())
    raw = evidence['source_policy']
    assert evidence['normal_generation_seed'] == 173
    assert raw['seed'] == 2904965844187189627 and raw['mode'] == 1
    assert raw['mapping_style'] == 'per_enemy_type'
    assert raw['ability_randomization_no_ability_weight'] == 0
    assert raw['ability_randomization_minny'] is False
    assert all(raw[key] is True for key in (
        'ability_randomization_boss_spawns', 'ability_randomization_minibosses',
        'ability_randomization_passive_enemies'))
    assert set(raw['allowed_abilities']) == set(ABILITY_NAME_TO_ID) - {'Normal', 'Master', 'Wait'}
    assert len(raw['allowed_abilities']) == 25
    assert evidence['options']['ability_gating'] == evidence['options']['area_keys'] == 0
    source = evidence['source']
    assert (source['template'], source['type'], source['name'], source['original_xy']) == (
        '0x088CA04C', 18, 'WADDLE_DOO', [528, 264])
    doo = next(source for source in ABILITY_SOURCES if source.key == 'WADDLE_DOO')
    assert doo.addresses[0] == int(source['runtime_table_rom_offset'], 16) == 0x3517FE
    assert doo.default_ability_name == 'Beam'
    observed = [obj for point in evidence['runs'][POSITIVE_RUNS[0]]['checkpoints']
                for obj in point.get('source_objects', ())]
    assert len(observed) == 2
    assert all(int(obj['template'], 16) == 0x088CA04C and obj['type'] == 18
               and obj['native_current_copy_field'] == 7 for obj in observed)
    assert build_enemy_copy_runtime_patch_writes(raw)[0x3517FE] == source['table_value'] == 22
    assert SourcePolicy(raw).grant('WADDLE_DOO', lambda _: True).guaranteed == frozenset({'Smash'})
    bitmap = build_enemy_source_runtime_config(raw)
    assert int.from_bytes(bitmap[4:8], 'little') & (1 << source['source_bitmap_index'])
    assert source['source_bitmap_index'] == 18
    target = evidence['target']
    assert (target['key'], target['location_id'], target['chest_template'], target['chest_index']) == (
        'MINOR_CHEST_SPRAY_PAINT_12', 3960511, '0x088CA0B8', 57)
    assert data.locations[target['key']].location_id == target['location_id']
    assert KirbyAmClient()._build_minor_chest_source_ptr_map()[0x8CA0B8] == target['location_id']
    assert target['f1_tile'] == [14, 7]
    assert target['f2_tiles'] == [[15, 7], [15, 8], [16, 8], [17, 8], [15, 9], [16, 9], [17, 9]]
    assert evidence['arrival'] == {
        'startup_room': 591, 'destination_room': 517, 'controller_transition_frame': 1109,
        'settled_arrival_frame': 1158, 'settled_position': [696, 296.99609375]}
    offsets = [int(row['offset'], 16) for row in evidence['fixture_byte_diff_from_production_rom']]
    assert offsets == list(range(0x2D8CB8, 0x2D8CC0)) + [
        0x2D8CD1, 0x2D8CD5, 0x2D8CD9, 0x2D8CDD, 0x2D8CE1, 0x2D8CE5, 0x2D8CED]


def test_exact_client_configuration_writes_and_no_gameplay_injection():
    evidence = json.loads(EVIDENCE.read_text())
    raw = evidence['source_policy']
    seed = raw['seed']
    expected = {
        0x0203B064: 1, 0x0203B068: seed & 0xFFFFFFFF, 0x0203B06C: seed >> 32,
        0x0203B070: 0,
        0x0203B074: sum(1 << ABILITY_NAME_TO_ID[name] for name in raw['allowed_abilities']),
        0x0203B0B0: 0, 0x0203B0B4: 0, 0x0203B078: 0,
    }
    assert set(evidence['runs']) == set(POSITIVE_RUNS + CONTROLS)
    for run in evidence['runs'].values():
        assert run['state_restores'] == run['gameplay_ram_writes'] == 0
        writes = run['runtime_config_writes']
        assert len(writes) == 8
        assert {int(write['address'], 16): int.from_bytes(bytes.fromhex(write['value']), 'little')
                for write in writes} == expected
        assert all(write['frame'] == 1085 and write['size'] == 4 and write['guard_failed'] is False
                   and write['origin'] == 'KirbyAmClient._sync_enemy_copy_ability_runtime_config'
                   for write in writes)
        assert run['sample_count'] == run['frames'] - 1085 + 1
        assert run['minimum_hp'] == run['player_hp']
        assert all(point['hp'] == run['player_hp'] for point in run['checkpoints'])
        assert all(point['ability'] == 22 for point in run['checkpoints'] if point['frame'] >= 2007)
        assert all(point['ability_gate'] == point['ability_unlocks'] == 0 for point in run['checkpoints'])


def test_four_successes_and_two_matched_negatives_keep_distinct_attribution():
    evidence = json.loads(EVIDENCE.read_text())
    positives = [evidence['runs'][name] for name in POSITIVE_RUNS]
    assert {(run['player_hp'], run['enemy_health_percent']) for run in positives} == {
        (1, 100), (6, 100), (1, 500), (6, 500)}
    assert len({run['input_sha256'] for run in positives}) == 1
    assert len({run['rom_sha256'] for run in positives}) == 4
    for run in positives:
        assert run['frames'] == 4900 and run['event_counter'] == 1
        assert int(run['event_ring'][0], 16) == 0x088CA0B8
        assert run['client_messages'] == [{'cmd': 'LocationChecks', 'locations': [3960511]}]
        changes = {point['frame']: point for point in run['changes']}
        assert changes[1939]['ability'] == 22 and changes[1939]['target_f1'] == 0xF1
        assert all(point['ability'] == 22 for point in run['changes'] if point['frame'] >= 1939)
        assert changes[3129]['target_f1'] == 0 and changes[3129]['animation'] == 107
        assert changes[3129]['y'] == 111.37109375  # Rising Final Cutter, not landing wave.
        assert changes[4421]['chest57'] and changes[4421]['minor_event_counter'] == 1
        points = {point['frame']: point for point in run['checkpoints']}
        assert points[3119]['linked_f2'] == [0xF2] * 7
        assert points[3179]['linked_f2'] == [0] * 7  # Subsequent clear, not simultaneous at3129.
        assert points[4900]['chest57'] and points[4900]['spray11'] is False
    for name, frames, starts in (
        ('control-attack-window', 3179, [3119]),
        ('control-no-approach-attacks', 4900, [3119, 3179, 3220]),
    ):
        run = evidence['runs'][name]
        assert (run['frames'], run['player_hp'], run['enemy_health_percent']) == (frames, 6, 100)
        assert run['rom_sha256'] == positives[0]['rom_sha256']
        assert run['event_counter'] == 0 and run['client_messages'] == []
        assert all(int(pointer, 16) == 0 for pointer in run['event_ring'])
        final = run['checkpoints'][-1]
        assert final['target_f1'] == 0xF1 and final['linked_f2'] == [0xF2] * 7
        assert final['chest57'] is False and final['spray11'] is False
        differences = run['input_differences']
        assert [delta['positive']['start'] for delta in differences] == starts
        for delta in differences:
            assert delta['positive'] in evidence['positive_inputs']
            assert delta['control'] == {**delta['positive'], 'keys': delta['positive']['keys'] & ~2}
