"""Separate ordinary170-to720 record must not imply a composed Yellow route."""

import hashlib
import json
from pathlib import Path

from ..data import data
from ..traversal_data import room_traversal_graph

DOCS = Path(__file__).parents[1] / 'dev-docs'
EVIDENCE = DOCS / 'carrot-yellow-ufo-upstream-runtime.json'


def evidence():
    return json.loads(EVIDENCE.read_text())


def test_upstream_boundaries_and_core_packet_are_preserved():
    e = evidence()
    boundary = e['model_boundary']
    assert boundary['native_rooms'] == [170, 719, 720]
    assert boundary['fixture_room'] == 170 and boundary['fixture_xy'] == [200, 80]
    assert not boundary['earlier170_access_proved'] and not boundary['continuous_yellow_composition_proved']
    assert not boundary['rule_changes']
    assert boundary['unchanged_core_access'] == room_traversal_graph('bomb_733_yellow', 'room14_entry').access_region
    assert boundary['unchanged_core_access'] == 'REGION_CARROT_CASTLE/ROOM_5_14'
    assert data.regions['REGION_CARROT_CASTLE/ROOM_5_07'].exit_requirements[boundary['unchanged_core_access']] == {
        'all': ['can_climb', 'can_break_block']}
    core = (DOCS / 'carrot-yellow-ufo-source-runtime.json').read_bytes()
    assert hashlib.sha256(core).hexdigest() == e['preserved_core_runtime_sha256']
    assert e['prior_packet_files_unchanged'] == 37
    assert e['source_policy'] == json.loads(core)['source_policy'] and e['production_seed'] == 8
    assert all(private not in EVIDENCE.read_text() for private in ('/home/', '/Users/', 'C:\\'))


def test_all_eight_observed_normal_no_hit_outcomes_and_directed_self_door():
    e = evidence()
    rows = e['accepted_cases']
    assert len(rows) == 8 and sum(r['samples'] for r in rows) == e['total_samples'] == 21064
    assert {(r['actual_hp'], r['enemy_health_percent'], r['scenario']) for r in rows} == {
        (hp, health, scenario) for hp in (1, 6) for health in (100, 500)
        for scenario in ('ingress', 'no-final-inhale')}
    for row in rows:
        positive = row['scenario'] == 'ingress'
        assert row['passed'] and row['no_hit'] and row['normal_entire_route']
        assert row['samples'] == 2633 and row['actual_hp'] == row['max_hp'] == row['final']['hp']
        assert (row['ai'], row['humans'], row['final']['ability']) == (0, 1, 0)
        assert row['final']['frame'] == 3717 and row['final']['room'] == (720 if positive else 719)
        assert [(t['frame'], t['room']) for t in row['transitions']] == (
            [(1085, 170), (1198, 719)] + ([(3646, 720)] if positive else []))
        assert row['directed_self_door'] == [{'frame': 2944, 'room': 719, 'x': 408.0, 'y': 136.99609375}]
        expected_changes = [{'frame': 1198, 'upper': 240, 'lower': 240}]
        if positive:
            expected_changes.append({'frame': 3329, 'upper': 240, 'lower': 0})
        assert row['top_barrier_changes'] == expected_changes
        assert row['checkerboard_before_self_door'] == [0] * 5
        assert row['checkerboard_after_self_door'] == [240] * 5
        assert row['final719_lower_f0'] == (0 if positive else 240)
        assert row['upper_f0_intact_throughout719'] and row['unused_734_bomb_intact_throughout719']
        assert row['configuration_writes'] == 8 and row['gameplay_ram_writes'] == row['state_restores'] == 0
        assert row['client_messages'] == [] and not row['server_submission']
        assert all(len(row[k]) == 64 and int(row[k], 16) >= 0
                   for k in ('result_sha256', 'trace_sha256', 'fixture_sha256'))


def test_only_final_inhale_changes_and_fixtures_keep_production_provenance():
    e = evidence()
    inputs = e['controller_inputs']
    assert inputs['columns'] == ['start', 'frames', 'keys'] and e['same_inputs_all_health_settings']
    assert [3322, 60, 2] in inputs['positive']
    assert inputs['no-final-inhale'] == [
        [start, frames, 0 if start == 3322 else keys] for start, frames, keys in inputs['positive']]
    assert all(start + frames == following[0] for (start, frames, _), following
               in zip(inputs['positive'], inputs['positive'][1:]))
    assert inputs['positive'][-1][0] + inputs['positive'][-1][1] == 3717
    assert len(e['fixtures']) == 4
    for fixture in e['fixtures']:
        assert fixture['startup_changed_bytes'] == 15
        matching = [r for r in e['accepted_cases'] if (r['actual_hp'], r['enemy_health_percent']) == (
            fixture['actual_hp'], fixture['enemy_health_percent'])]
        assert len(matching) == 2 and all(r['fixture_sha256'] == fixture['fixture_sha256'] for r in matching)
        assert all(len(fixture[k]) == 64 and int(fixture[k], 16) >= 0 for k in (
            'production_sha256', 'fixture_sha256', 'build_sha256', 'production_provenance_sha256'))
    config = e['configuration']
    assert config['frame'] == 1085 and config['count'] == 8
    assert config['writer'] == 'KirbyAmClient._sync_enemy_copy_ability_runtime_config'
    assert not any(config[k] for k in ('ability_gating', 'area_keys', 'helpers', 'server_submission'))
    assert len(e['provenance']['compact_result_sha256']) == 64
