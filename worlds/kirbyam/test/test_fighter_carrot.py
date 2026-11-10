"""The finite Fighter719 proof must not become global equipment or gate credit."""

import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from BaseClasses import CollectionState, ItemClassification

from .. import KirbyAmWorld, traversal_rules as rules
from ..traversal import SourcePolicy
from ..traversal_data import room_traversal_graph, room_traversal_targets, load_room_traversal
from .test_mini_traversal import make_world
from .test_traversal import policy
from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive

OWNER = 'REGION_CARROT_CASTLE/ROOM_5_07'
UPSTREAM = 'REGION_CARROT_CASTLE/ROOM_5_05'
EXIT = 'REGION_CARROT_CASTLE/ROOM_5_13__LOGIC__ENTRY_FROM_5_07'


def manifest():
    return json.loads((Path(__file__).resolve().parents[1]
                       / 'dev-docs/carrot-room7-fighter-acceptance.json').read_text())


def test_finite_source_and_equipment():
    graph = room_traversal_graph('bomb_719_room13', 'room5_fighter_entry')
    resolver = SourcePolicy(manifest()['source_policy'])
    assert resolver.grant('WADDLE_DOO', lambda _: True).guaranteed == frozenset({'Fighter'})
    owned = frozenset({'Fighter Ability'})
    target, = graph.required_targets
    result = graph.evaluate(resolver, owned, True)
    assert result.reaches(target) and not result.retry_assumptions
    assert any(p.equipped == 'Fighter' for p in result.positions if p.node == target)
    assert all(p.consumed == frozenset({'0x088D3BF4'}) for p in result.positions if p.node == target)
    assert all(p.equipped == 'Normal' for p in graph.starts)
    source, = graph.placements
    assert not source.renewable and not source.retry_evidence
    assert not replace(graph, placements=()).evaluate(resolver, owned, True).reaches(target)
    assert not graph.evaluate(resolver, frozenset(), True).reaches(target)
    assert graph.evaluate(resolver, frozenset(), False).reaches(target)
    assert not graph.evaluate(policy(), owned, True).reaches(target)
    assert not graph.evaluate(policy(2, pool=['Fighter', 'Beam']), owned, True).reaches(target)
    assert graph.access_region == UPSTREAM


@pytest.mark.parametrize('mode,pool,weight,applies,promotes', [
    (0, None, 0, True, False), (1, ['Fighter'], 0, True, True),
    (2, ['Fighter'], 0, True, True), (1, ['Beam'], 0, True, False),
    (2, ['Beam', 'Fighter'], 0, False, False), (2, ['Fighter'], 50, False, False),
    (2, ['Fighter'], 100, False, False), (1, ['Smash'], 0, False, False),
])
@pytest.mark.parametrize('statues', [False, True])
@pytest.mark.parametrize('gating', [False, True])
def test_source_scope_and_progression(mode, pool, weight, applies, promotes, statues, gating):
    resolver = policy(mode, pool=pool, weight=weight, statues=statues)
    row = next(r for r in room_traversal_targets('block') if r['id'] == 'bomb_719_room13')
    assert rules.target_applies(row, resolver) is applies
    world = SimpleNamespace(_enemy_copy_ability_policy=resolver.policy, _ability_gating_enabled=lambda: gating)
    assert rules.carrot_fighter_is_progression(world) is (promotes and gating)
    cabbage = next(r for r in room_traversal_targets('block') if r['id'] == 'bomb_517_chocolate')
    if pool == ['Fighter']:
        assert not rules.target_applies(cabbage, resolver)


def test_source_condition_cannot_spread_to_another_surface():
    from ..data import data
    rooms = deepcopy({name: {'traversal': region.traversal} for name, region in data.regions.items()})
    row = next(r for r in rooms[OWNER]['traversal']['targets'] if r['id'] == 'bomb_719_room13')
    row['exit'] = 'REGION_CARROT_CASTLE/ROOM_5_14'
    with pytest.raises(ValueError, match='reviewed Carrot entry'):
        load_room_traversal(rooms)


@pytest.mark.parametrize('gating', [0, 1])
@pytest.mark.parametrize('area_keys', [0, 1])
@pytest.mark.parametrize('room_sanity,minor_chests', [(0, False), (1, True)])
@pytest.mark.parametrize('statues', [0, 1])
def test_actual_world_binding_and_collect_remove(monkeypatch, gating, area_keys, room_sanity, minor_chests, statues):
    generate = KirbyAmWorld.generate_early

    def generate_policy(world):
        generate(world)
        world._enemy_copy_ability_policy = manifest()['source_policy']

    monkeypatch.setattr(KirbyAmWorld, 'generate_early', generate_policy)
    monkeypatch.setattr(KirbyAmWorld, 'ENABLE_MINOR_CHESTS', minor_chests)
    world = make_world(1, gating, area_keys=area_keys, room_sanity=room_sanity,
                       ability_randomization_statues=statues, accessibility=2)
    state = CollectionState(world.multiworld)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    target = world.multiworld.get_entrance(f'{OWNER} -> {EXIT}', 1)
    assert target.access_rule(state) is (not gating)
    item = world.create_item('Fighter Ability')
    assert item.classification == (ItemClassification.progression if gating else ItemClassification.useful)
    state.collect(item, prevent_sweep=True)
    assert target.access_rule(state)
    if gating:
        assert state.has('Fighter Ability', 1)
        state.remove(item)
        assert not target.access_rule(state)
    state.can_reach_region = lambda name, player: name == OWNER
    assert not target.access_rule(state)
    for room in ('ROOM_5_08', 'ROOM_5_14'):
        assert world.multiworld.get_entrance(f'{OWNER} -> REGION_CARROT_CASTLE/{room}', 1).access_rule(state)
    assert all(loc.access_rule(state) for loc in world.multiworld.get_region(OWNER, 1).locations)
    other = world.multiworld.get_region('REGION_CARROT_CASTLE/ROOM_5_14', 1)
    notes, = [edge for edge in other.exits if 'ROOM_5_13' in edge.name]
    assert notes.connected_region.name != EXIT and notes.access_rule(state)


def test_native_acceptance_endpoints_and_controls():
    runs = manifest()['runs']
    assert len(runs) == 8
    assert {(r['hp'], r['enemy_health_percent'], r['positive']) for r in runs} == {
        (hp, health, positive) for hp in (1, 6) for health in (100, 500) for positive in (True, False)}
    for run in runs:
        assert run['real_entry_frame'] == 1188 and run['acquisition_frame'] == 1420
        assert run['per_frame']['hp_min'] == run['final']['hp'] == run['hp']
        assert run['final']['ability'] == 20
        assert run['final']['room'] == (734 if run['positive'] else 719)
        assert run['state_restores'] == run['phone_inputs'] == 0


@pytest.mark.parametrize('gating,area_keys,health', [(1, 0, 100), (1, 1, 500), (0, 0, 100)])
def test_full_pool_seed39_one_hp_fill(tmp_path, gating, area_keys, health):
    player = tmp_path / 'player.yaml'
    player.write_text('name: Crash533Proof\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n'
                      '  ability_randomization_mode: 1\n  ability_randomization_no_ability_weight: 0\n'
                      '  minimum_health: 1\n  maximum_health: 1\n'
                      f'  ability_gating: {gating}\n  area_keys: {area_keys}\n'
                      f'  enemy_health_multiplier: {health}\n', encoding='utf-8')
    archive = generate_archive_from_fixture(player, tmp_path / 'out', seed=39)
    raw = load_multidata_from_archive(archive)['slot_data'][1]['enemy_copy_ability_policy']
    assert len(raw['allowed_abilities']) == 25
    assert SourcePolicy(raw).grant('WADDLE_DOO', lambda _: True).guaranteed == frozenset({'Fighter'})
