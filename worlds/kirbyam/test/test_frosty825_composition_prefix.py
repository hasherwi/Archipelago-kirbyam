"""Resource-state evidence does not certify a conditional encounter branch."""
import json
from pathlib import Path

from ..ability_source_inventory import source_inventory
from ..traversal import SourcePolicy
from ..traversal_data import room_traversal_targets

ROOT = Path(__file__).resolve().parents[1]
LIFE = 'room:825/template:0x088CD3F0/encounter:56/src/mr_frosty.c:762/type:166'


def test_prefix_matches_native_placement_spawn_predicate_and_runtime_grant():
    record = json.loads((ROOT / 'dev-docs/frosty825-composition-prefix.json').read_text())
    assert record['inventory_id'] == LIFE
    assert record['status'] == 'prefix_resource_audit_only' and record['installed_world_route'] is False
    waddle = source_inventory()['room:825/template:0x088CD318']
    assert (waddle['spawn_conditions']['state_bank'], waddle['spawn_conditions']['bit_index'],
            waddle['spawn_conditions']['test']) == (0, 1, 'bit_clear')
    assert [c['health_percent'] for c in record['cases']] == [100, 500]
    for case in record['cases']:
        assert (case['first_frame'], case['last_frame'], case['audited_frames']) == (1085, 1729, 645)
        assert case['rooms'] == [825] and case['endpoint']['ability'] == 2
        assert case['boss']['hp'] == 30 * case['health_percent'] // 100
        assert case['waddle_bit_clear_in_all_four_slots'] and case['waddle_live_observations'] == 0
        assert {m['template'] for m in case['mechanisms_unchanged']} == {'0x88cd3cc', '0x88cd33c', '0x88cd360'}
        assert case['runtime_write_frames'] == [1085]
        assert SourcePolicy(case['policy']).grant('MR_FROSTY_ICE_CUBE', lambda _: True).guaranteed == {'Ice'}
    suffix = json.loads((ROOT / 'dev-docs/reconstructed-825-evidence-manifest.json').read_text())
    assert record['suffix_addendum_sha256'] == next(r['sha256'] for r in suffix['records']
        if r['identity'] == 'carried825/825-retained-ice-scope-addendum.json')


def test_native_candidate_alone_does_not_publish_world_access():
    source = source_inventory()[LIFE]
    assert source['native_contract']['attack_entry_guaranteed'] is False
    assert source['access']['status'] == 'unresolved'
    row = next(r for r in room_traversal_targets('block') if r['id'] == 'frozen_825_sound_effects')
    assert row['advanced_graphs'] == ['generated_ice', 'fire_entry']
    assert set(row['graphs']) == {'local', 'central_statues', 'peppermint290_statues', 'ufo_entry', 'generated_ice', 'fire_entry'}


def test_large_cube_controls_match_runtime_permission_and_preserve_ammunition():
    record = json.loads((ROOT / 'dev-docs/frosty825-large-cube-controls.json').read_text())
    native = source_inventory()[record['inventory_id']]
    assert native['source_key'] == record['source_key'] == 'MR_FROSTY_ICE_CUBE'
    assert record['status'] == 'conditional_acquisition_evidence'
    assert record['physical_prefix_equal_across_cases']
    expected = [2, 0, 7, 0, 2, 2, 2]
    for case, ability in zip(record['cases'], expected, strict=True):
        assert (case['first_frame'], case['last_frame'], case['audited_frames']) == (1085, 2021, 937)
        assert case['intake_type'] == 167 and case['intake_frames'] == [1933, 1944]
        assert case['original_parent_hp'] == 30 * case['enemy_health_percent'] // 100
        assert case['waddle_bit_clear_all_slots']
        assert case['final']['room'] == 825 and case['final']['ability'] == ability
        assert case['runtime_write_frames'] == ([] if case['policy']['mode'] == 0 else [1085])
        grant = SourcePolicy(case['policy']).grant(record['source_key'], lambda _: True)
        if ability in (2, 7):
            assert grant.guaranteed == {2: frozenset({'Ice'}), 7: frozenset({'Beam'})}[ability]
        elif case['gating']:
            assert case['omitted_permission'] is not None
        else:
            assert not grant.guaranteed
