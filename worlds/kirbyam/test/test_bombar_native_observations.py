"""Distinguish local activation/intake observations from accepted carry routes."""
import json
from pathlib import Path


def test_activation_control_and_damaged_acquisition_remain_non_routes():
    record = json.loads((Path(__file__).resolve().parents[1]
                         / 'dev-docs/generated-bombar232-native-observations.json').read_text())
    assert record['status'] == 'mechanics_only_not_route'
    control, active = record['control'], record['activated']
    assert control['first_activated_frame'] is None
    assert control['minimum_hp'] == 6 and control['abilities'] == [0]
    assert active['first_activated_frame'] is not None
    assert active['minimum_hp'] == 3 and active['abilities'] == [0, 5, 25]
    for row in (control, active):
        assert row['initial']['ability'] == 0 and row['initial']['hp'] == 6
        assert row['initial']['room'] == row['final']['room'] == 232
        assert not row['runtime_writes']
        assert len(row['private_trace_sha256']) == len(row['runtime_sha256']) == 64
    landmarks = {r['frame']: r for r in active['landmarks']}
    missiles = [a for a in landmarks[2212]['actors'] if a['type_id'] == 179]
    assert len(missiles) == 2 and all(a['native_ability'] == 25 for a in missiles)
    assert all(a['state'] == '0x809c48d' for a in missiles)
    assert landmarks[2304]['ability'] == 5  # Paired intake is not an individual source grant.
    assert landmarks[2666]['ability'] == 25
    assert all(a['hp'] > 0 for r in active['landmarks'] for a in r['actors'] if a['type_id'] == 63)

    failed = record['failed_one_hp']
    assert failed['minimum_hp'] == 0 and failed['abilities'] == [0]
    assert next(r['frame'] for r in failed['equipment_health_changes'] if r['hp'] == 0) == 1672
