"""Bounded Foley acquisition, camera respawn and frozen-projectile timed exit."""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

import pytest
from BaseClasses import CollectionState, ItemClassification

from .. import traversal_rules as rules
from ..traversal import Position, SourcePolicy, compile_traversal_graph
from ..traversal_data import room_traversal_graph, room_traversal_targets
from .support.source_policy import set_rule_test_policy
from .test_conditional_switch_gates import OWNER, UPSTREAM, EXIT
from .test_mini_traversal import make_world
from .test_traversal import policy

TARGET = 'switch_533_room16'
WITNESS = 'hub4_ice_entry'
PREFIX = TARGET + ':ice_'
PROJECTILE = '0x088C2714:camera_respawn1'


def target_row():
    return next(row for row in room_traversal_targets('switch') if row['id'] == TARGET)


@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('keys', [False, True])
def test_finite_acquisition_then_distinct_respawn_projectile(gating, keys):
    graph = room_traversal_graph(TARGET, WITNESS, keys)
    resolver = policy(1, pool=['Ice'])
    owned = frozenset({'Ice Ability'})
    result = graph.evaluate(resolver, owned, gating)
    assert result.reaches(PREFIX + 'door') and result.reaches(PREFIX + 'destination')
    assert all(p.equipped == 'Normal' for p in graph.starts)
    assert graph.access_region == UPSTREAM
    assert [(s.identity, s.source_key, s.renewable) for s in graph.placements] == [
        ('0x088C2714', 'FOLEY', False), (PROJECTILE, 'FOLEY', False)]
    assert all(not s.retry_evidence for s in graph.placements)
    before_exit = [p for p in result.positions if p.node == PREFIX + 'door' and p.equipped == 'Ice']
    assert before_exit and all(p.consumed == frozenset({'0x088C2714', PROJECTILE}) for p in before_exit)
    assert all(not p.opened for p in result.positions)
    assert graph.evaluate(resolver, frozenset(), gating).reaches(PREFIX + 'door') is (not gating)
    # The first consumed source cannot also be the frozen projectile.
    invalid = deepcopy(target_row()['graphs'][WITNESS])
    invalid['sources'][1]['id'] = '0x088C2714'
    invalid['routes'][4]['uses_object'] = '0x088C2714'
    with pytest.raises(ValueError, match='Conflicting physical source'):
        compile_traversal_graph(invalid)
    # Consuming the respawn for another ability removes the projectile.
    spent = replace(graph, starts=(Position(PREFIX + 'pose', 'Ice', consumed=frozenset({PROJECTILE})),))
    assert not spent.evaluate(resolver, owned, gating).reaches(PREFIX + 'door')


@pytest.mark.parametrize('mode,pool,weight,qualifies', [
    (0, None, 0, False), (1, ['Ice'], 0, True), (1, ['Beam'], 0, False),
    (2, ['Ice'], 0, True), (2, ['Ice', 'Bomb'], 0, False),
    (2, ['Ice'], 50, False), (2, ['Ice'], 100, False),
])
@pytest.mark.parametrize('advanced', [0, 1])
@pytest.mark.parametrize('gating', [0, 1])
def test_source_permission_and_entry_required_at_both_logic_levels(monkeypatch, mode, pool, weight, qualifies, advanced, gating):
    raw = policy(mode, pool=pool, weight=weight).policy
    set_rule_test_policy(monkeypatch, lambda: raw)
    world = make_world(mode, gating, advanced_logic=advanced)
    state = CollectionState(world.multiworld)
    while state.has('Ice Ability', 1):
        state.remove(world.create_item('Ice Ability'))
    state.can_reach_region = lambda name, player: name == OWNER
    state.collect(world.create_item('Ice Ability'), prevent_sweep=True)
    edge = world.multiworld.get_entrance(f'{OWNER} -> {EXIT}', 1)
    assert not edge.access_rule(state)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    # Native Bomb remains its independent ordinary alternative.
    expected = bool(qualifies)
    assert edge.access_rule(state) is (expected or (mode == 0 and not gating))
    assert rules.mustard_ice_is_progression(world) is bool(qualifies and gating)
    graph = room_traversal_graph(TARGET, WITNESS)
    assert graph.evaluate(SourcePolicy(raw), frozenset({'Ice Ability'}), bool(gating),
                          allow_documented_retries=True).reaches(PREFIX + 'door') is qualifies
    if mode != 0:
        state.remove(world.create_item('Ice Ability'))
        assert edge.access_rule(state) is bool(expected and not gating)


def test_ice_in_normal_graphs_and_other_ice_classification_retained():
    row = target_row()
    assert row['advanced_graphs'] == ['hub4_crash_entry', 'hub4_magic_entry']
    assert WITNESS not in row['advanced_graphs']
    assert WITNESS in [g for g in row['graphs'] if g not in row['advanced_graphs']]
    assert len(rules.target_graphs(row, False, advanced=True)) == 5
    assert len(rules.target_graphs(row, False, advanced=False)) == 3
    world = make_world(0, 1, advanced_logic=0)
    assert not rules.mustard_ice_is_progression(world)
    assert rules.goal2_ice_is_progression(world)
    assert world.create_item('Ice Ability').classification == ItemClassification.progression


@pytest.mark.parametrize('gating,advanced,rooms,count,keys', [
    (1, 1, 1, 0, 0), (1, 1, 1, 2, 1), (0, 1, 1, 0, 0),
    (1, 0, 1, 1, 0), (0, 0, 1, 0, 0), (1, 0, 0, 1, 0),
    (1, 0, 1, 0, 1), (1, 0, 1, 2, 1),
])
def test_full_pool_seed43_archive_at_both_logic_levels(tmp_path, gating, advanced, rooms, count, keys):
    from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive
    player = tmp_path / 'player.yaml'
    player.write_text('name: Ice533Proof\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n'
                      '  ability_randomization_mode: 1\n  ability_randomization_no_ability_weight: 0\n'
                      '  minimum_health: 1\n  maximum_health: 1\n  accessibility: full\n'
                      f'  advanced_logic: {advanced}\n  ability_gating: {gating}\n'
                      f'  area_keys: {keys}\n  room_sanity: {rooms}\n'
                      f'  start_inventory:\n    Ice Ability: {count}\n', encoding='utf-8')
    out = tmp_path / 'out'
    archive = generate_archive_from_fixture(player, out, seed=43)
    decoded = load_multidata_from_archive(archive)
    raw = decoded['slot_data'][1]['enemy_copy_ability_policy']
    assert len(raw['allowed_abilities']) == 25
    assert SourcePolicy(raw).grant('FOLEY', lambda _: True).guaranteed == frozenset({'Ice'})
    assert decoded['precollected_items'][1].count(3860102) == count


def test_native_acceptance_has_paired_complete_crossings_and_controls():
    record = json.loads((Path(__file__).parents[1] / 'dev-docs/mustard-room15-ice-acceptance.json').read_text())
    assert record['target'] == TARGET and record['production_seed'] == 43
    assert record['policy_seed'] == 4777282310011543242
    runs = record['runs']
    assert {(r['enemy_health_percent'], r['player_hp'], r['control']) for r in runs} == {
        (health, hp, control) for health in (100, 500) for hp in (1, 6)
        for control in ('positive', 'no-freeze')}
    assert len(runs) == 8
    for run in runs:
        assert run['hp_min'] == run['hp_max'] == run['player_hp']
        assert run['hp_sample_count'] == 4110
        assert run['gameplay_ram_writes'] == run['runtime_rom_writes'] == run['state_restores'] == 0
        assert len(run['config_writes']) == 8
        build = run['build']
        assert build['seed'] == 43 and build['source_table_byte'] == 2
        assert SourcePolicy(build['policy']).grant('FOLEY', lambda _: True).guaranteed == frozenset({'Ice'})
        assert build['options']['advanced_logic'] == 1
        for difference in build['fixture_byte_diff']:
            offset = int(difference['offset'], 16)
            assert 0x2D8CB8 <= offset < 0x2D8CC0 or 0x2D8CD0 <= offset < 0x2D8CF0
        events = run['events']
        if run['control'] == 'positive':
            assert run['final_room'] == 325
            assert events['switch_contact']['contact'] == events['first_frozen']['state']['address']
            assert events['respawned_foley']['frame'] < events['first_frozen']['frame'] < events['switch_contact']['frame']
        else:
            assert run['final_room'] == 533
            assert 'first_frozen' not in events and 'switch_contact' not in events
        for digest in [*build['sha256'].values(), *run['sha256'].values()]:
            assert len(digest) == 64 and set(digest) <= set('0123456789abcdef')
