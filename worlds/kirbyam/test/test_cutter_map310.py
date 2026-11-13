"""Bounded finite-Twister Cutter route; owned permission is never equipment."""

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from BaseClasses import CollectionState, ItemClassification
from Options import Accessibility
from test.general import setup_multiworld

from .support.source_policy import set_rule_test_policy
from .. import KirbyAmWorld, traversal_rules as rules
from ..data import data
from ..enemy_ability_data import GATEABLE_ENEMY_COPY_ABILITIES
from ..traversal import CAPABILITY_CONSUMED_ABILITIES, Position, SourcePolicy, compile_traversal_graph
from ..traversal_data import _validate_target, room_traversal_graph, room_traversal_targets
from .test_mini_traversal import make_world
from .test_traversal import policy

TARGET = 'switch_310_mustard_map'
OWNER = 'REGION_MUSTARD_MOUNTAIN/ROOM_4_CHEST'
UPSTREAM = 'REGION_RAINBOW_ROUTE/ROOM_1_HUB_4'
SOURCE_ROOM = 'REGION_RAINBOW_ROUTE/ROOM_1_34'
LOCATION = 'MAJOR_CHEST_MUSTARD_MOUNTAIN'
CAPABILITY = 'switch_310_cutter_five_roof_returns'
EVIDENCE = Path(__file__).resolve().parents[1] / 'dev-docs/mustard-map-cutter-acceptance.json'
POLICIES = [
    (0, None, 0, False), (1, ['Cutter'], 0, True), (1, ['Bomb'], 0, False),
    (2, ['Cutter'], 0, True), (2, ['Cutter', 'Bomb'], 0, False),
    (2, ['Cutter'], 50, False), (2, ['Cutter'], 100, False),
]


def target_row():
    return next(row for row in room_traversal_targets('switch') if row['id'] == TARGET)


def cutter_graph(area_keys=False):
    return room_traversal_graph(TARGET, 'hub4_cutter_entry', area_keys)


@pytest.mark.parametrize('mode,pool,weight,applies', POLICIES)
@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('area_keys', [False, True])
@pytest.mark.parametrize('statues', [False, True])
def test_conditional_policy_preserves_base_rule_and_independent_entry(
        monkeypatch, mode, pool, weight, applies, gating, area_keys, statues):
    resolver = policy(mode, pool=pool, weight=weight, statues=statues, minny=False)
    row = target_row()
    monkeypatch.setattr(rules, 'extra_traversal_targets', lambda: (row,))
    assert rules.target_applies(row, resolver) is applies
    assert rules.static_extra_witness(resolver, advanced=True)

    def original_rule(state):
        return state.base_rule
    target = SimpleNamespace(access_rule=original_rule)
    looked_up = []

    def get_location(name, player):
        looked_up.append((name, player))
        return target

    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy=resolver.policy,
        _ability_gating_enabled=lambda: gating, _area_keys_enabled=lambda: area_keys,
        options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=statues),
                                accessibility=Accessibility(Accessibility.option_full)),
        multiworld=SimpleNamespace(get_location=get_location),
    )
    rules.install_extra_traversal_rules(world)
    assert looked_up == ([(data.locations[LOCATION].label, 1)] if applies else [])
    if not applies:
        assert target.access_rule is original_rule
    owned = set()
    state = SimpleNamespace(base_rule=True, has=lambda item, player: item in owned,
                            can_reach_region=lambda name, player: name in {OWNER, SOURCE_ROOM})
    assert target.access_rule(state) is (not applies)
    owned.add('Cutter Ability')
    assert target.access_rule(state) is (not applies)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    assert target.access_rule(state)
    owned.clear()
    assert target.access_rule(state) is (not applies or not gating)
    state.base_rule = False
    assert not target.access_rule(state)


@pytest.mark.parametrize('mode,pool,weight,applies', POLICIES)
@pytest.mark.parametrize('gating', [0, 1])
@pytest.mark.parametrize('area_keys', [0, 1])
@pytest.mark.parametrize('statues', [0, 1])
@pytest.mark.parametrize('room_sanity', [0, 1])
@pytest.mark.parametrize('maps', [0, 1])
def test_actual_world_only_map_and_unchanged_cutter_classification(
        monkeypatch, mode, pool, weight, applies, gating, area_keys, statues, room_sanity, maps):
    resolver = policy(mode, pool=pool, weight=weight, statues=statues, minny=False)
    set_rule_test_policy(monkeypatch, lambda *args, **kwargs: resolver.policy)
    world = make_world(mode, gating, accessibility='minimal', area_keys=area_keys,
                       ability_randomization_statues=statues, room_sanity=room_sanity,
                       ability_randomization_no_ability_weight=weight, start_with_all_maps=maps)
    target = world.multiworld.get_location(data.locations[LOCATION].label, 1)
    assert target.parent_region.name == OWNER
    state = CollectionState(world.multiworld)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    incoming = world.multiworld.get_entrance(f'{SOURCE_ROOM} -> {OWNER}', 1)
    assert incoming.access_rule(state) is (not area_keys)
    state.collect(world.create_item('Mustard Mountain - Area Key'), prevent_sweep=True)
    assert incoming.access_rule(state)
    assert target.access_rule(state) is (not applies or not gating)
    item = world.create_item('Cutter Ability')
    assert item.classification == ItemClassification.progression
    state.collect(item, prevent_sweep=True)
    assert state.has('Cutter Ability', 1) and target.access_rule(state)
    state.remove(item)
    assert target.access_rule(state) is (not applies or not gating)
    state.collect(item, prevent_sweep=True)
    for accessible in (OWNER, SOURCE_ROOM):
        state.can_reach_region = lambda name, player, accessible=accessible: name == accessible
        assert target.access_rule(state) is (not applies)
        assert world.multiworld.get_entrance(f'{OWNER} -> {SOURCE_ROOM}', 1).access_rule(state)
        assert incoming.access_rule(state)
        owner = world.multiworld.get_region(OWNER, 1)
        other_checks = [location for location in world.multiworld.get_locations(1)
                        if location.parent_region.name.startswith(OWNER) and location is not target]
        assert len(other_checks) == room_sanity
        assert all(location.access_rule(state) for location in other_checks)
        assert all(exit.access_rule(state) for exit in owner.exits)


@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('area_keys', [False, True])
def test_finite_source_actual_carry_retained_cutter_and_no_persistent_credit(gating, area_keys):
    graph = cutter_graph(area_keys)
    assert graph.access_region == UPSTREAM
    assert graph.required_guaranteed_source == ('TWISTER', 'Cutter')
    assert len(graph.starts) == 1 and graph.starts[0].equipped == 'Normal'
    rooms = {node.key: node.room for node in graph.nodes}
    assert rooms[graph.starts[0].node] == 590
    source, = graph.placements
    assert rooms[source.node] == 534
    assert (source.identity, source.source_key, source.renewable) == ('0x088B59B4', 'TWISTER', False)
    assert not source.retry_evidence
    assert [(rooms[r.source], rooms[r.target]) for r in graph.routes if r.room_transition] == [(590, 534), (534, 310)]
    assert [r.capability for r in graph.routes if r.capability] == [CAPABILITY]
    assert all(r.opens is None for r in graph.routes)
    assert CAPABILITY not in CAPABILITY_CONSUMED_ABILITIES
    resolver, owned = policy(1, pool=['Cutter']), frozenset({'Cutter Ability'})
    target, = graph.required_targets
    result = graph.evaluate(resolver, owned, gating)
    assert result.reaches(target) and not result.retry_assumptions
    assert any(p.node == source.node and p.equipped == 'Cutter' and source.identity in p.consumed
               for p in result.positions)
    assert any(p.node == target and p.equipped == 'Cutter' and not p.opened for p in result.positions)
    assert graph.evaluate(resolver, frozenset(), gating).reaches(target) is (not gating)
    assert not replace(graph, placements=()).evaluate(resolver, owned, gating).reaches(target)
    cut = replace(graph, routes=tuple(r for r in graph.routes if r.target != source.node))
    assert not cut.evaluate(resolver, owned, gating).reaches(target)
    spent = replace(graph, starts=(Position(source.node, 'Normal', consumed=frozenset({source.identity})),))
    assert not spent.evaluate(resolver, owned, gating).reaches(target)
    assert graph.routes[2].required_equipment == graph.routes[-1].required_equipment == frozenset({'Cutter'})
    for wrong in ('UFO', 'Crash', 'Bomb', 'Laser'):
        assert not graph.evaluate(policy(1, pool=[wrong]), owned | {f'{wrong} Ability'}, gating).positions


@pytest.mark.parametrize('pool,weight', [
    (['Cutter', 'UFO'], 0), (['Cutter', 'Crash'], 0), (['Cutter'], 50), (['Cutter'], 100)])
@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('retries', [False, True])
def test_raw_mixed_source_cannot_become_guaranteed_by_inventory_filter(pool, weight, gating, retries):
    for owned in (frozenset({'Cutter Ability'}), frozenset(f'{a} Ability' for a in pool)):
        result = cutter_graph().evaluate(policy(2, pool=pool, weight=weight), owned, gating,
                                         allow_documented_retries=retries)
        assert not result.positions and not result.retry_assumptions


@pytest.mark.parametrize('mutation', ['swimming', 'wrong_room', 'persistent'])
def test_kernel_and_compiler_reject_widened_attack(mutation):
    graph = cutter_graph()
    route = next(r for r in graph.routes if r.capability)
    raw = deepcopy(target_row()['graphs']['hub4_cutter_entry'])
    raw_route = next(r for r in raw['routes'] if r.get('capability'))
    if mutation == 'swimming':
        raw_route['water_state'] = 'swimming'
        graph = replace(graph, routes=tuple(replace(r, water_state='swimming') if r == route else r
                                            for r in graph.routes))
    elif mutation == 'wrong_room':
        for node in raw['nodes']:
            if node['native_room'] == 310:
                node['native_room'] = 533
        graph = replace(graph, nodes=tuple(replace(n, room=533) if n.room == 310 else n for n in graph.nodes))
    else:
        raw_route['opens'] = 'retained_return'
        graph = replace(graph, routes=tuple(replace(r, opens='retained_return') if r == route else r
                                            for r in graph.routes))
    with pytest.raises(ValueError, match='native room|persistent'):
        compile_traversal_graph(raw)
    with pytest.raises(ValueError, match='native room|persistent'):
        graph.evaluate(policy(1, pool=['Cutter']), frozenset({'Cutter Ability'}), True)


def test_four_or_alternatives_exact_target_and_preserved_prior_graphs():
    row = target_row()
    assert set(row['graphs']) == {'hub4_ufo_entry', 'hub4_crash_entry', 'hub4_cupid_entry', 'hub4_cutter_entry'}
    assert row['requires_guaranteed_source'] == {
        'source_key': 'TWISTER', 'abilities': ['UFO', 'Crash', 'Cupid', 'Cutter']}
    expected = json.loads(EVIDENCE.read_text(encoding='utf-8'))['preserved_graph_sha256']
    assert set(expected) == {'hub4_ufo_entry', 'hub4_crash_entry', 'hub4_cupid_entry'}
    for key, digest in expected.items():
        assert hashlib.sha256(json.dumps(row['graphs'][key], sort_keys=True).encode()).hexdigest() == digest
    for ability in ('UFO', 'Crash', 'Cupid', 'Cutter'):
        resolver = policy(1, pool=[ability])
        assert rules.target_applies(row, resolver)
        assert [rules.graph_succeeds(g, resolver, frozenset({f'{ability} Ability'}), True, retries=True)
                for g in rules.target_graphs(row, False, advanced=True)] == [
                    ability == 'UFO', ability == 'Crash', ability == 'Cupid', ability == 'Cutter']
    for key, wrong in [('id', 'switch_other'), ('native_room', 533), ('kind', 'block'),
                       ('region', SOURCE_ROOM), ('location', 'MAJOR_CHEST_RAINBOW_ROUTE')]:
        altered = deepcopy(row)
        altered[key] = wrong
        with pytest.raises(ValueError, match='reviewed chest target'):
            _validate_target(altered)
    owners = [(r['id'], key) for r in room_traversal_targets('switch') for key, g in r['graphs'].items()
              if any(route.get('capability') == CAPABILITY for route in g['routes'])]
    assert owners == [(TARGET, 'hub4_cutter_entry')]


@pytest.mark.parametrize('scenario', ['enabled', 'gating_off', 'absent', 'wrong_source'])
def test_unconditional_start_inventory_is_already_owned_before_regions(monkeypatch, scenario):
    from .. import regions
    raw = json.loads(EVIDENCE.read_text(encoding='utf-8'))['source_policy']
    if scenario == 'wrong_source':
        raw = policy(1, pool=['Bomb']).policy
    set_rule_test_policy(monkeypatch, lambda *args, **kwargs: raw)
    multiworld = setup_multiworld(KirbyAmWorld, steps=('generate_early',), seed=2, options={
        'ability_randomization_mode': 1, 'ability_gating': int(scenario != 'gating_off'), 'accessibility': 'minimal'})
    world = multiworld.worlds[1]
    assert 'Cutter' in GATEABLE_ENEMY_COPY_ABILITIES
    if scenario == 'absent':
        create_regions = regions.create_regions

        def without_target(current_world):
            result = create_regions(current_world)
            target = current_world.multiworld.get_location(data.locations[LOCATION].label, current_world.player)
            target.parent_region.locations.remove(target)
            return result

        monkeypatch.setattr(regions, 'create_regions', without_target)
    starting = [world.create_item('Cutter Ability') for _ in range(3)]
    for item in starting:
        assert item.classification == ItemClassification.progression
        multiworld.push_precollected(item)
    assert multiworld.state.count('Cutter Ability', 1) == 3
    world.create_regions()
    assert multiworld.state.count('Cutter Ability', 1) == CollectionState(multiworld).count('Cutter Ability', 1) == 3
    for item in starting:
        multiworld.state.remove(item)
    assert not multiworld.state.has('Cutter Ability', 1)


@pytest.mark.parametrize('gating,area_keys,health,maps,count', [
    (1, 0, 100, 0, 0), (1, 1, 500, 1, 1), (1, 0, 163, 0, 3), (0, 0, 100, 1, 1)])
def test_normal_full_pool_seed2_fill_start_inventory_and_accessibility(
        tmp_path, monkeypatch, gating, area_keys, health, maps, count):
    import Main
    from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive
    generated, before_regions, after_regions = [], [], []
    main, create_regions = Main.main, KirbyAmWorld.create_regions

    def capture_regions(world):
        before_regions.append(world.multiworld.state.count('Cutter Ability', world.player))
        create_regions(world)
        after_regions.append(world.multiworld.state.count('Cutter Ability', world.player))

    def capture_main(*args, **kwargs):
        multiworld = main(*args, **kwargs)
        generated.append(multiworld)
        return multiworld

    monkeypatch.setattr(KirbyAmWorld, 'create_regions', capture_regions)
    monkeypatch.setattr(Main, 'main', capture_main)
    player = tmp_path / 'player.yaml'
    player.write_text('name: Cutter310\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n'
                      '  ability_randomization_mode: 1\n  ability_randomization_no_ability_weight: 0\n'
                      '  minimum_health: 1\n  maximum_health: 1\n'
                      f'  ability_gating: {gating}\n  area_keys: {area_keys}\n'
                      f'  enemy_health_multiplier: {health}\n  start_with_all_maps: {maps}\n'
                      f'  start_inventory:\n    Cutter Ability: {count}\n  accessibility: full\n', encoding='utf-8')
    archive = generate_archive_from_fixture(player, tmp_path / 'out', seed=2)
    decoded = load_multidata_from_archive(archive)
    raw = decoded['slot_data'][1]['enemy_copy_ability_policy']
    assert len(raw['allowed_abilities']) == 25
    assert SourcePolicy(raw).grant('TWISTER', lambda _: True).guaranteed == frozenset({'Cutter'})
    assert raw['seed'] == 16441167028314156635
    assert decoded['precollected_items'][1].count(3860106) == count
    assert before_regions == after_regions == [count]
    multiworld, = generated
    assert not multiworld.get_unfilled_locations()
    assert multiworld.can_beat_game() and multiworld.fulfills_accessibility()
    state = CollectionState(multiworld)
    assert state.count('Cutter Ability', 1) == count
    state.can_reach_region = lambda name, player: name == UPSTREAM
    target = multiworld.get_location(data.locations[LOCATION].label, 1)
    assert target.access_rule(state) is (bool(count) or not gating)
    starting = [i for i in multiworld.precollected_items[1] if i.name == 'Cutter Ability']
    for item in starting:
        state.remove(item)
    assert not state.has('Cutter Ability', 1)
    assert target.access_rule(state) is (not gating)


@pytest.mark.parametrize('pool,weight', [(['Cutter'], 0), (['Cutter', 'Cupid'], 0), (['Cutter'], 50)])
def test_permission_growth_is_monotone_and_never_filters_raw_source_certainty(pool, weight):
    graph, resolver = cutter_graph(), policy(2, pool=pool, weight=weight)
    inventories = [frozenset(), frozenset({'Cutter Ability'}),
                   frozenset({'Cutter Ability', 'Cupid Ability'}),
                   frozenset(f'{a} Ability' for a in GATEABLE_ENEMY_COPY_ABILITIES)]
    results = [graph.evaluate(resolver, owned, True).reaches(next(iter(graph.required_targets)))
               for owned in inventories]
    assert results == sorted(results)
    assert results == ([False, True, True, True] if pool == ['Cutter'] and not weight else [False] * 4)


def test_other_equipment_cannot_execute_exact_return_sequence():
    from ..traversal import Node, Route, reachable_positions
    nodes = (Node('arrival', 310), Node('crossed', 310))
    route = Route('arrival', 'crossed', CAPABILITY)
    for ability in ('Normal', 'Cupid', 'UFO', 'Crash', 'Cutter'):
        result = reachable_positions(nodes, (route,), (), (Position('arrival', ability),), policy(0))
        assert result.reaches('crossed') is (ability == 'Cutter')
