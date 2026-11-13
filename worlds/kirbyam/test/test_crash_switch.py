"""Bounded camera-valid Crash533 witness; inventory is permission, not equipment."""

import json
from dataclasses import replace
from pathlib import Path

import pytest
from BaseClasses import CollectionState, ItemClassification

from .. import traversal_rules as rules
from ..traversal import Node, Position, Route, SourcePolicy, compile_traversal_graph, reachable_positions
from ..traversal_data import room_traversal_graph, room_traversal_targets
from .test_conditional_switch_gates import OWNER, UPSTREAM, EXIT
from .test_mini_traversal import make_world
from .test_traversal import policy
from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive

CAPABILITY = 'switch_533_crash_viewport'
ROOT = Path(__file__).resolve().parents[1]


def manifest():
    return json.loads((ROOT / 'dev-docs/mustard-room15-crash-acceptance.json').read_text())


def graph():
    return room_traversal_graph('switch_533_room16', 'hub4_crash_entry')


def test_finite_source_consumption_and_actual_normal_destination():
    g = graph()
    resolver = SourcePolicy(manifest()['source_policy'])
    assert resolver.grant('FOLEY', lambda _: True).guaranteed == frozenset({'Crash'})
    owned = frozenset({'Crash Ability'})
    target, = g.required_targets
    result = g.evaluate(resolver, owned, True)
    terminal = [p for p in result.positions if p.node == target]
    assert terminal and all(p.equipped == 'Normal' and not p.opened for p in terminal)
    assert all(p.consumed == frozenset({'0x088C2714'}) for p in terminal)
    assert result.reaches('switch_533_room16:destination')
    assert all(p.equipped == 'Normal' for p in result.positions
               if p.node == 'switch_533_room16:destination')
    assert next(n.room for n in g.nodes if n.key == 'switch_533_room16:destination') == 325
    assert all(p.equipped == 'Normal' for p in g.starts)
    assert not any(r.opens for r in g.routes)
    assert not result.retry_assumptions
    assert not g.evaluate(resolver, frozenset(), True).reaches(target)
    assert g.evaluate(resolver, frozenset(), False).reaches(target)
    assert not replace(g, placements=()).evaluate(resolver, owned, True).reaches(target)
    assert not g.evaluate(policy(), owned, True).reaches(target)  # Native Foley is Bomb.
    # Even an artificial local return cannot replenish the finite source.
    source = g.placements[0].node
    crossing = 'switch_533_room16:normal_crossing'
    loop = replace(g, routes=g.routes + (Route(crossing, source),),
                   starts=(Position(crossing, 'Normal', consumed=frozenset({'0x088C2714'})),))
    after = loop.evaluate(resolver, owned, True)
    assert all(p.equipped == 'Normal' for p in after.positions)
    dropped = replace(g, starts=(Position(source, 'Normal', consumed=frozenset({'0x088C2714'})),))
    assert not dropped.evaluate(resolver, owned, True).reaches(target)


@pytest.mark.parametrize('room,medium,opens', [
    (534, 'dry', None), (533, 'swimming', None), (533, 'dry', 'persistent'),
])
def test_capability_refuses_wrong_room_water_or_persistent_credit(room, medium, opens):
    with pytest.raises(ValueError):
        reachable_positions([Node('a', room), Node('b', room)],
                            [Route('a', 'b', CAPABILITY, opens=opens, water_state=medium)],
                            (), [Position('a', 'Crash')], policy())


def test_compiler_rejects_persistent_credit():
    row = next(r for r in room_traversal_targets('switch') if r['id'] == 'switch_533_room16')
    payload = json.loads(json.dumps(row['graphs']['hub4_crash_entry']))
    next(r for r in payload['routes'] if r.get('capability'))['opens'] = 'switch'
    with pytest.raises(ValueError, match='persistent'):
        compile_traversal_graph(payload)


def test_camera_scope_is_one_explicit_graph_not_global_switch_credit():
    rows = room_traversal_targets('switch')
    owners = [(r['id'], key) for r in rows for key, g in r['graphs'].items()
              if any(route.get('capability') == CAPABILITY for route in g['routes'])]
    assert owners == [('switch_533_room16', 'hub4_crash_entry')]
    row = next(r for r in rows if r['id'] == 'switch_533_room16')
    assert set(row['graphs']) == {'hub4_entry', 'hub4_ufo_entry', 'hub4_crash_entry', 'hub4_magic_entry'}
    assert rules.static_extra_witness(SourcePolicy(manifest()['source_policy']))
    evidence = manifest()
    x0, y0, x1, y1 = evidence['positive_pose']['viewport']
    sx0, sy0, sx1, sy1 = evidence['positive_pose']['switch_bounds']
    assert x0 < sx1 and x1 > sx0 and y0 < sy1 and y1 > sy0
    assert evidence['offscreen_pose']['viewport_x'][1] < sx0
    for run in evidence['runs'].values():
        assert run['hp_min'] == run['hp_max'] == run['actual_hp']
        assert run['gameplay_ram_writes'] == run['runtime_rom_writes'] == run['state_restores'] == 0
        if run['switch_activated']:
            assert run['final']['room'] == 325 and run['final']['ability'] == 0
        else:
            assert run['actual_hp'] == 1 and run['final']['room'] == 533


@pytest.mark.parametrize('gating', [0, 1])
@pytest.mark.parametrize('area_keys', [0, 1])
@pytest.mark.parametrize('room_sanity', [0, 1])
def test_real_world_binding_collection_and_unrelated_exits(monkeypatch, gating, area_keys, room_sanity):
    from .. import KirbyAmWorld
    generate = KirbyAmWorld.generate_early

    def generated_policy(world):
        generate(world)
        world._enemy_copy_ability_policy = manifest()['source_policy']

    monkeypatch.setattr(KirbyAmWorld, 'generate_early', generated_policy)
    world = make_world(1, gating, area_keys=area_keys, room_sanity=room_sanity)
    state = CollectionState(world.multiworld)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    target = world.multiworld.get_entrance(f'{OWNER} -> {EXIT}', 1)
    assert target.access_rule(state) is (not gating)
    item = world.create_item('Crash Ability')
    assert item.classification == (ItemClassification.progression if gating else ItemClassification.useful)
    state.collect(item, prevent_sweep=True)
    assert target.access_rule(state)
    if gating:
        assert state.has('Crash Ability', 1)
        state.remove(item)
        assert not target.access_rule(state)
    state.can_reach_region = lambda name, player: name == OWNER
    assert not target.access_rule(state)
    for destination in ('REGION_RAINBOW_ROUTE/ROOM_1_34', 'REGION_MUSTARD_MOUNTAIN/ROOM_4_17'):
        assert world.multiworld.get_entrance(f'{OWNER} -> {destination}', 1).access_rule(state)
    assert all(location.access_rule(state) for location in world.multiworld.get_region(OWNER, 1).locations)


@pytest.mark.parametrize('mode,pool,weight,progression', [
    (0, None, 0, False), (1, ['Crash'], 0, True), (1, ['Bomb'], 0, False),
    (2, ['Crash'], 0, True), (2, ['Crash', 'Bomb'], 0, False),
    (2, ['Crash'], 50, False), (2, ['Crash'], 100, False),
])
def test_conditional_promotion_matches_source_gate(mode, pool, weight, progression):
    from types import SimpleNamespace
    resolver = policy(mode, pool=pool, weight=weight)
    world = SimpleNamespace(_enemy_copy_ability_policy=resolver.policy, _ability_gating_enabled=lambda: True)
    assert rules.mustard_crash_is_progression(world) is progression
    world._ability_gating_enabled = lambda: False
    assert not rules.mustard_crash_is_progression(world)


@pytest.mark.parametrize('gating,area_keys,health', [(1, 0, 100), (1, 1, 500), (0, 0, 100)])
def test_normal_pool_seed29_one_hp_full_fill(tmp_path, gating, area_keys, health):
    player = tmp_path / 'player.yaml'
    player.write_text('name: Crash\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n'
                      '  ability_randomization_mode: 1\n  minimum_health: 1\n  maximum_health: 1\n'
                      f'  ability_gating: {gating}\n  area_keys: {area_keys}\n'
                      f'  enemy_health_multiplier: {health}\n', encoding='utf-8')
    archive = generate_archive_from_fixture(player, tmp_path / 'out', seed=29)
    decoded = load_multidata_from_archive(archive)
    raw = decoded['slot_data'][1]['enemy_copy_ability_policy']
    assert len(raw['allowed_abilities']) == 25
    assert SourcePolicy(raw).grant('FOLEY', lambda _: True).guaranteed == frozenset({'Crash'})
