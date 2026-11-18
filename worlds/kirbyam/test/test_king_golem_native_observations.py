"""Bind the damaged-boss acquisition lineage without granting world access."""
import json
from pathlib import Path

from ..ability_source_inventory import source_inventory


def test_half_health_generation_and_single_child_acquisition_controls():
    evidence = json.loads((Path(__file__).resolve().parents[1]
        / 'dev-docs/generated-king-golem710-native-observations.json').read_text())
    assert evidence['status'] == 'mechanics_only_not_route'
    source = source_inventory()[evidence['acquired_inventory_id']]
    assert source['logic'] == 'advanced' and source['access']['status'] == 'unresolved'
    assert source['parent_placement'] == evidence['controller_inventory_id']
    assert source['type_id'] == 31 and source['native_grant'] == 'Stone'
    cases = evidence['cases']
    control = cases['full_health_control']
    assert control['abilities'] == [0] and control['first_golem'] is None
    assert control['controller_health_changes'] == [{'frame': 1086, 'hp': 60}]
    for key, expected in [('vanilla', 8), ('shuffled_owned', 2), ('shuffled_unowned', 0),
                          ('live_singleton', 2), ('live_no_ability', 0)]:
        case = cases[key]
        assert case['initial']['ability'] == 0 and case['initial']['hp'] == 6
        assert case['initial']['room'] == case['final']['room'] == 710
        assert case['minimum_hp'] == 3
        assert case['controller_health_changes'][-1] == {'frame': 3503, 'hp': 30}
        assert case['first_golem']['frame'] == 3515
        assert case['first_golem_intake']['frame'] == 3562
        child = next(a for a in case['first_golem_intake']['actors'] if a['type_id'] == 31)
        boss = next(a for a in case['first_golem_intake']['actors'] if a['type_id'] == 70)
        assert child['parent'] == boss['object']
        assert child['hp'] == 0 and child['state'] == '0x809c48d'
        assert child['native_ability'] == 8  # Native state reset; runtime policy resolves actual swallow.
        assert boss['hp'] == 30
        endpoint = case['matched_endpoint']
        assert endpoint['frame'] == 3645 and endpoint['ability'] == expected
        assert endpoint['hp'] == 3
        if expected:
            assert case['first_grant']['frame'] == 3637
            assert case['first_grant']['ability'] == expected
        else:
            assert case['first_grant'] is None and case['abilities'] == [0]
        for field in ('private_trace_sha256', 'runtime_sha256', 'fixture_rom_sha256', 'bridge_sha256'):
            assert len(case[field]) == 64
        assert all(not w['guard_failed'] and w['origin'] ==
                   'KirbyAmClient._sync_enemy_copy_ability_runtime_config' for w in case['runtime_writes'])
    assert not cases['vanilla']['runtime_writes']
    assert cases['shuffled_owned']['runtime_writes']
