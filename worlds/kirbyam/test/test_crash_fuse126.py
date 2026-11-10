"""Finite Crash ignition is an alternative to, not a replacement for, fuse126."""

import json
import hashlib
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from BaseClasses import CollectionState, ItemClassification

from .. import traversal_rules as rules
from ..traversal import Position, Route, SourcePolicy
from ..traversal_data import has_graph_access, room_traversal_graph, room_traversal_targets
from .test_mini_traversal import make_world
from .test_traversal import policy
from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive

ROOT = Path(__file__).resolve().parents[1]
OWNER = 'REGION_RAINBOW_ROUTE/ROOM_1_32'
EXIT = 'REGION_RAINBOW_ROUTE/ROOM_1_33_LEFT'


def manifest():
    return json.loads((ROOT / 'dev-docs/rainbow-room32-crash-acceptance.json').read_text())


def graph():
    return room_traversal_graph('fuse_126', 'lower_entry_crash')


def test_consumption_equipment_and_finite_source():
    g = graph()
    resolver = SourcePolicy(manifest()['source_policy'])
    owned = frozenset({'Crash Ability'})
    target, = g.required_targets
    result = g.evaluate(resolver, owned, True)
    for node in (target, 'fuse_126:destination'):
        positions = [p for p in result.positions if p.node == node]
        assert positions and all(p.equipped == 'Normal' and not p.opened for p in positions)
    assert any(p.consumed == frozenset({'126:0x88b9554'})
               for p in result.positions if p.node == target)
    assert not result.retry_assumptions
    assert not g.evaluate(resolver, frozenset(), True).reaches(target)
    assert g.evaluate(resolver, frozenset(), False).reaches(target)
    assert not replace(g, placements=()).evaluate(resolver, owned, True).reaches(target)
    assert not g.evaluate(policy(), owned, True).reaches(target)
    spent = Position('fuse_126:source', 'Normal', consumed=frozenset({'126:0x88b9554'}))
    exhausted = replace(g, starts=(spent,))
    assert not exhausted.evaluate(resolver, owned, True).reaches(target)
    loop = replace(g, routes=g.routes + (Route(target, 'fuse_126:source'),),
                   starts=(Position(target, 'Normal', consumed=frozenset({'126:0x88b9554'})),))
    assert all(p.equipped == 'Normal' for p in loop.evaluate(resolver, owned, True).positions)


@pytest.mark.parametrize('mode,pool,weight,success', [
    (0, None, 0, False), (1, ['Crash'], 0, True), (1, ['Fire'], 0, False),
    (2, ['Crash'], 0, True), (2, ['Crash', 'Fire'], 0, False),
    (2, ['Crash'], 50, False), (2, ['Crash'], 100, False),
])
@pytest.mark.parametrize('statues', [False, True])
def test_source_policy_and_conditional_progression(mode, pool, weight, success, statues):
    resolver = policy(mode, pool=pool, weight=weight, statues=statues)
    g = graph()
    assert g.evaluate(resolver, frozenset({'Crash Ability', 'Fire Ability'}), True,
                      allow_documented_retries=True).reaches(next(iter(g.required_targets))) is success
    world = SimpleNamespace(_enemy_copy_ability_policy=resolver.policy, _ability_gating_enabled=lambda: True)
    assert rules.mustard_crash_is_progression(world) is success
    world._ability_gating_enabled = lambda: False
    assert not rules.mustard_crash_is_progression(world)


def test_same_target_and_prior_graphs_preserved():
    row = next(r for r in room_traversal_targets('fuse') if r['id'] == 'fuse_126')
    assert set(row['graphs']) == {
        'local', 'rainbow_hub194_statue', 'rainbow_hub592_burning', 'hub_statues', 'lower_entry_crash',
    }
    assert row['graphs']['local']['routes'][0]['allowed_abilities'] == [
        'Fire', 'Burning', 'Bomb', 'Laser', 'UFO', 'Master', 'Hammer']
    assert row['graphs']['local']['sources'][-1]['renewable']
    assert row['graphs']['local']['sources'][-1]['retry_evidence']
    old = deepcopy(row['graphs'])
    old.pop('lower_entry_crash')
    old['local']['routes'][0].pop('evidence')  # Only the stale timing sentence changed.
    assert hashlib.sha256(json.dumps(old, sort_keys=True).encode()).hexdigest() == (
        '5d51741a3c56f56f91d03161e68e47c6eeaeef310afdd81e25fde7491a4d1f87')
    rooms = json.loads((ROOT / 'data/regions/rooms.json').read_text())
    assert [k for k, v in rooms.items() if OWNER in v.get('exits', {})] == [
        'REGION_RAINBOW_ROUTE/ROOM_1_31']
    assert graph().access_region == OWNER
    assert next(n.room for n in graph().nodes if n.key == 'fuse_126:destination') == 570


@pytest.mark.parametrize('gating', [0, 1])
@pytest.mark.parametrize('area_keys', [0, 1])
@pytest.mark.parametrize('room_sanity', [0, 1])
def test_actual_world_binding(monkeypatch, gating, area_keys, room_sanity):
    from .. import KirbyAmWorld
    generate = KirbyAmWorld.generate_early

    def generated_policy(world):
        generate(world)
        world._enemy_copy_ability_policy = manifest()['source_policy']

    monkeypatch.setattr(KirbyAmWorld, 'generate_early', generated_policy)
    world = make_world(1, gating, area_keys=area_keys, room_sanity=room_sanity)
    state = CollectionState(world.multiworld)
    state.can_reach_region = lambda name, player: name == OWNER
    target = world.multiworld.get_entrance(f'{OWNER} -> {EXIT}', 1)
    assert target.access_rule(state) is (not gating)
    item = world.create_item('Crash Ability')
    assert item.classification == (ItemClassification.progression if gating else ItemClassification.useful)
    state.collect(item, prevent_sweep=True)
    assert target.access_rule(state)
    if gating:
        state.remove(item)
        assert not target.access_rule(state)
        state.collect(item, prevent_sweep=True)
    state.can_reach_region = lambda name, player: name == 'REGION_RAINBOW_ROUTE/ROOM_1_31'
    assert not has_graph_access(world, state, graph())
    if gating:
        assert not target.access_rule(state)
    assert all(location.access_rule(state) for location in world.multiworld.get_region(OWNER, 1).locations)


@pytest.mark.parametrize('gating,area_keys,health', [(1, 0, 100), (1, 1, 500), (0, 0, 100)])
def test_normal_pool_seed19_one_hp_full_fill(tmp_path, gating, area_keys, health):
    player = tmp_path / 'player.yaml'
    player.write_text('name: Crash126\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n'
                      '  ability_randomization_mode: 1\n  minimum_health: 1\n  maximum_health: 1\n'
                      f'  ability_gating: {gating}\n  area_keys: {area_keys}\n'
                      f'  enemy_health_multiplier: {health}\n', encoding='utf-8')
    archive = generate_archive_from_fixture(player, tmp_path / 'out', seed=19)
    raw = load_multidata_from_archive(archive)['slot_data'][1]['enemy_copy_ability_policy']
    assert len(raw['allowed_abilities']) == 25
    assert SourcePolicy(raw).grant('HOT_HEAD', lambda _: True).guaranteed == frozenset({'Crash'})


def test_raw_mixed_pool_cannot_become_a_guarantee_through_inventory_filtering():
    g = graph()
    resolver = policy(2, pool=['Crash', 'Fire'])
    for owned in (frozenset({'Crash Ability'}), frozenset({'Crash Ability', 'Fire Ability'})):
        for gating in (False, True):
            assert not g.evaluate(resolver, owned, gating, allow_documented_retries=True).positions
    # This guard belongs only to the new alternative, not the existing fuse target.
    assert not room_traversal_graph('fuse_126', 'local').required_guaranteed_source
    assert room_traversal_graph('fuse_126', 'local').evaluate(
        policy(), frozenset({'Fire Ability'}), True).reaches('target')


@pytest.mark.parametrize('condition', [
    {}, [], {'source_key': 'FOLEY', 'ability': 'Crash'},
    {'source_key': 'HOT_HEAD', 'ability': 'Normal'},
    {'source_key': 'HOT_HEAD', 'ability': ['Crash']},
    {'source_key': 'HOT_HEAD', 'ability': 'Crash', 'retry': True},
])
def test_guaranteed_source_guard_rejects_malformed_or_detached_condition(condition):
    from ..traversal import compile_traversal_graph
    row = next(r for r in room_traversal_targets('fuse') if r['id'] == 'fuse_126')
    payload = deepcopy(row['graphs']['lower_entry_crash'])
    payload['requires_guaranteed_source'] = condition
    with pytest.raises(ValueError, match='guaranteed-source'):
        compile_traversal_graph(payload)


def test_mixed_nonprovider_target_stays_closed_after_permission_collection(monkeypatch):
    from .. import KirbyAmWorld
    generate = KirbyAmWorld.generate_early
    resolver = policy(2, pool=['Crash', 'Sword'])

    def generated_policy(world):
        generate(world)
        world._enemy_copy_ability_policy = resolver.policy

    monkeypatch.setattr(KirbyAmWorld, 'generate_early', generated_policy)
    world = make_world(2, 1, accessibility='minimal')
    state = CollectionState(world.multiworld)
    state.can_reach_region = lambda name, player: name == OWNER
    target = world.multiworld.get_entrance(f'{OWNER} -> {EXIT}', 1)
    for name in ('Crash Ability', 'Sword Ability'):
        state.collect(world.create_item(name), prevent_sweep=True)
        assert not target.access_rule(state)
        owned = frozenset(n for n in ('Crash Ability', 'Sword Ability') if state.has(n, 1))
        assert not graph().evaluate(resolver, owned, True, allow_documented_retries=True).positions
