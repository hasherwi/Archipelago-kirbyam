"""Bounded ordinary-mode Meta Knight route; inventory is permission, not equipment."""

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest
from BaseClasses import CollectionState, ItemClassification
from test.general import setup_multiworld

from .support.source_policy import set_rule_test_policy
from .. import KirbyAmWorld, traversal_rules as rules
from ..enemy_ability_data import ABILITY_NAME_TO_ID, GATEABLE_ENEMY_COPY_ABILITIES, STARTING_COPY_ABILITIES
from ..traversal import Node, Position, Route, SourcePolicy, compile_traversal_graph, reachable_positions
from ..traversal_data import _validate_target, room_traversal_graph, room_traversal_targets
from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive
from .test_conditional_switch_gates import OWNER, UPSTREAM, EXIT
from .test_mini_traversal import make_world
from .test_traversal import policy

TARGET = 'switch_533_room16'
CAPABILITY = 'switch_533_magic_meta_knight'
WITNESS = 'hub4_magic_entry'
PREFIX = TARGET + ':magic_'
EVIDENCE = Path(__file__).resolve().parents[1] / 'dev-docs/mustard-room15-magic-acceptance.json'
POLICIES = [
    (0, None, 0, False), (1, ['Magic'], 0, True), (1, ['Beam'], 0, False),
    (2, ['Magic'], 0, True), (2, ['Magic', 'Bomb'], 0, False),
    (2, ['Magic'], 50, False), (2, ['Magic'], 100, False),
]


def evidence():
    return json.loads(EVIDENCE.read_text(encoding='utf-8'))


def target_row():
    return next(row for row in room_traversal_targets('switch') if row['id'] == TARGET)


def magic_graph(area_keys=False):
    return room_traversal_graph(TARGET, WITNESS, area_keys)


def kernel(equipped, *, routes=None, nodes=None, opened=frozenset()):
    return reachable_positions(
        nodes or (Node('pre', 533), Node('post', 533)),
        routes or (Route('pre', 'post', CAPABILITY),), (),
        (Position('pre', equipped, opened),), policy(), frozenset({'Magic Ability'}), True,
    )


@pytest.mark.parametrize('ability', sorted(set(ABILITY_NAME_TO_ID) - {'Wait'}))
def test_exact_provider_consumes_actual_magic_not_permission(ability):
    result = kernel(ability)
    assert result.reaches('post') is (ability == 'Magic')
    assert all(p.equipped == 'Normal' and not p.opened for p in result.positions if p.node == 'post')


@pytest.mark.parametrize('equipped,passes', [
    (frozenset({'Magic'}), True), (frozenset({'Magic', 'Crash'}), False), (frozenset(), False),
])
def test_every_uncertain_equipment_outcome_must_qualify(equipped, passes):
    result = kernel(equipped)
    assert result.reaches('post') is passes
    assert all(p.equipment_outcomes == frozenset({'Normal'}) for p in result.positions if p.node == 'post')


def test_one_magic_cannot_activate_twice_or_use_unrelated_open_event():
    result = kernel('Magic', nodes=(Node('pre', 533), Node('post', 533), Node('end', 533)),
                    routes=(Route('pre', 'post', CAPABILITY), Route('post', 'end', CAPABILITY)))
    assert result.reaches('post') and not result.reaches('end')
    assert not kernel('Normal', opened=frozenset({'unrelated'})).reaches('post')
    assert all(p.equipped == 'Normal' for p in kernel('Magic', opened=frozenset({'unrelated'})).positions
               if p.node == 'post')


@pytest.mark.parametrize('mutation', ['source_room', 'target_room', 'swimming', 'persistent', 'empty_open'])
def test_kernel_and_compiler_reject_widened_attack(mutation):
    g = magic_graph()
    raw = deepcopy(target_row()['graphs'][WITNESS])
    attack = next(r for r in g.routes if r.capability)
    raw_attack = next(r for r in raw['routes'] if r.get('capability'))
    if mutation in {'source_room', 'target_room'}:
        key = attack.source if mutation == 'source_room' else attack.target
        g = replace(g, nodes=tuple(replace(n, room=534) if n.key == key else n for n in g.nodes))
        next(n for n in raw['nodes'] if n['id'] == key)['native_room'] = 534
    elif mutation == 'swimming':
        g = replace(g, routes=tuple(replace(r, water_state='swimming') if r == attack else r for r in g.routes))
        raw_attack['water_state'] = 'swimming'
    else:
        opens = 'persistent' if mutation == 'persistent' else ''
        g = replace(g, routes=tuple(replace(r, opens=opens) if r == attack else r for r in g.routes))
        raw_attack['opens'] = opens
    with pytest.raises(ValueError, match='native room|persistent'):
        compile_traversal_graph(raw)
    with pytest.raises(ValueError, match='native room|persistent'):
        g.evaluate(policy(1, pool=['Magic']), frozenset({'Magic Ability'}), True)


@pytest.mark.parametrize('allowed', [[], ['Crash'], ['Magic', 'Crash']])
def test_provider_narrowing_cannot_widen_or_empty_magic(allowed):
    raw = deepcopy(target_row()['graphs'][WITNESS])
    next(r for r in raw['routes'] if r.get('capability'))['allowed_abilities'] = allowed
    with pytest.raises(ValueError, match='Allowed abilities'):
        compile_traversal_graph(raw)
    with pytest.raises(ValueError, match='Allowed abilities'):
        kernel('Magic', routes=(Route('pre', 'post', CAPABILITY, allowed_abilities=frozenset(allowed)),))


@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('area_keys', [False, True])
def test_finite_source_actual_carry_consumption_and_normal325(gating, area_keys):
    g = magic_graph(area_keys)
    rooms = {n.key: n.room for n in g.nodes}
    assert g.access_region == UPSTREAM and g.required_guaranteed_source == ('FOLEY', 'Magic')
    assert g.starts == (Position(PREFIX + 'hub4'),) and rooms[g.starts[0].node] == 590
    source, = g.placements
    assert (source.identity, source.source_key, source.renewable, source.retry_evidence) == (
        '0x088C2714', 'FOLEY', False, None)
    assert rooms[source.node] == 533
    assert [(rooms[r.source], rooms[r.target]) for r in g.routes if r.room_transition] == [
        (590, 534), (534, 533), (533, 325)]
    assert [r.capability for r in g.routes if r.capability] == [CAPABILITY]
    assert not any(r.opens or r.recover_dropped_ability for r in g.routes)
    assert [r.required_equipment for r in g.routes] == [
        frozenset({'Normal'}), frozenset({'Normal'}), frozenset({'Normal'}),
        frozenset({'Magic'}), None, frozenset({'Normal'}), frozenset({'Normal'})]
    resolver, owned = SourcePolicy(evidence()['source_policy']), frozenset({'Magic Ability'})
    target, = g.required_targets
    result = g.evaluate(resolver, owned, gating)
    assert result.reaches(target) and result.reaches(PREFIX + 'destination') and not result.retry_assumptions
    assert any(p.node == PREFIX + 'pose' and p.equipped == 'Magic' and source.identity in p.consumed
               for p in result.positions)
    for key in ('normal_crossing', 'door', 'destination'):
        terminals = [p for p in result.positions if p.node == PREFIX + key]
        assert terminals and all(p.equipped == 'Normal' and not p.opened for p in terminals)
        assert all(source.identity in p.consumed for p in terminals)
    assert g.evaluate(resolver, frozenset(), gating).reaches(target) is (not gating)
    assert not replace(g, placements=()).evaluate(resolver, owned, gating).reaches(target)
    cut = replace(g, routes=tuple(r for r in g.routes if r.target != source.node))
    assert not cut.evaluate(resolver, owned, gating).reaches(target)
    spent_start = (Position(source.node, 'Normal', consumed=frozenset({source.identity})),)
    assert not replace(g, starts=spent_start).evaluate(resolver, owned, gating).reaches(target)
    behind = replace(g, placements=(replace(source, node=target),))
    assert not behind.evaluate(resolver, owned, gating).reaches(target)
    loop = replace(g, routes=g.routes + (Route(PREFIX + 'normal_crossing', source.node),))
    spent_crossing = (Position(PREFIX + 'normal_crossing', 'Normal', consumed=frozenset({source.identity})),)
    after = replace(loop, starts=spent_crossing).evaluate(resolver, owned, gating)
    assert all(p.equipped == 'Normal' for p in after.positions)


@pytest.mark.parametrize('mode,pool,weight,applies', POLICIES)
@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('retries', [False, True])
def test_raw_source_guard_never_filters_mixed_pool_into_a_guarantee(mode, pool, weight, applies, gating, retries):
    resolver = policy(mode, pool=pool, weight=weight)
    for owned in (frozenset({'Magic Ability'}), frozenset(f'{name} Ability' for name in (pool or ['Magic']))):
        result = magic_graph().evaluate(resolver, owned, gating, allow_documented_retries=retries)
        assert result.reaches(PREFIX + 'door') is applies
        assert not result.retry_assumptions
        if not applies:
            assert not result.positions


@pytest.mark.parametrize('mode,pool,weight,applies', POLICIES)
@pytest.mark.parametrize('gating', [0, 1])
@pytest.mark.parametrize('area_keys', [0, 1])
@pytest.mark.parametrize('statues', [0, 1])
@pytest.mark.parametrize('room_sanity', [0, 1])
def test_actual_world_source_permission_options_and_unrelated_exits(
        monkeypatch, mode, pool, weight, applies, gating, area_keys, statues, room_sanity):
    resolver = policy(mode, pool=pool, weight=weight, statues=statues, minny=False)
    set_rule_test_policy(monkeypatch, lambda *args, **kwargs: resolver.policy)
    world = make_world(mode, gating, accessibility='minimal', area_keys=area_keys,
                       ability_randomization_statues=statues, room_sanity=room_sanity,
                       ability_randomization_no_ability_weight=weight)
    state = CollectionState(world.multiworld)
    target = world.multiworld.get_entrance(f'{OWNER} -> {EXIT}', 1)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    # Native Foley is Bomb; Magic must not replace that original permission.
    native_bomb = mode == 0
    assert target.access_rule(state) is (not gating or not (applies or native_bomb))
    item = world.create_item('Magic Ability')
    assert item.classification == (ItemClassification.progression if gating and applies else ItemClassification.useful)
    state.collect(item, prevent_sweep=True)
    assert state.has('Magic Ability', 1) is bool(gating and applies)
    assert target.access_rule(state) is (not gating or not native_bomb)
    state.remove(item)
    assert target.access_rule(state) is (not gating or not (applies or native_bomb))
    state.collect(item, prevent_sweep=True)
    for accessible in (OWNER, 'REGION_RAINBOW_ROUTE/ROOM_1_34'):
        state.can_reach_region = lambda name, player, accessible=accessible: name == accessible
        assert target.access_rule(state) is (not (applies or native_bomb))
        for destination in ('REGION_RAINBOW_ROUTE/ROOM_1_34', 'REGION_MUSTARD_MOUNTAIN/ROOM_4_17'):
            assert world.multiworld.get_entrance(f'{OWNER} -> {destination}', 1).access_rule(state)
        assert all(location.access_rule(state) for location in world.multiworld.get_region(OWNER, 1).locations)
    if applies or native_bomb:
        assert target in world.multiworld.indirect_connections[world.multiworld.get_region(UPSTREAM, 1)]


def test_four_or_alternatives_preserve_graphs_and_exact_target():
    row = target_row()
    assert list(row['graphs']) == ['hub4_entry', 'hub4_ufo_entry', 'hub4_crash_entry', WITNESS]
    for key, digest in evidence()['preserved_graph_sha256'].items():
        assert hashlib.sha256(json.dumps(row['graphs'][key], sort_keys=True).encode()).hexdigest() == digest
    for ability in ('Bomb', 'UFO', 'Crash', 'Magic'):
        resolver = policy(1, pool=[ability])
        assert rules.target_applies(row, resolver)
        assert rules.static_extra_witness(resolver)
        assert [rules.graph_succeeds(g, resolver, frozenset({f'{ability} Ability'}), True, retries=True)
                for g in rules.target_graphs(row, False)] == [ability == a for a in ('Bomb', 'UFO', 'Crash', 'Magic')]
    for key, wrong in [('id', 'switch_other'), ('kind', 'block'), ('native_room', 310),
                       ('region', UPSTREAM), ('exit', 'REGION_MUSTARD_MOUNTAIN/ROOM_4_17')]:
        altered = deepcopy(row)
        altered[key] = wrong
        with pytest.raises(ValueError, match='reviewed Room16 exit'):
            _validate_target(altered)
    owners = [(r['id'], key) for r in room_traversal_targets('switch') for key, g in r['graphs'].items()
              if any(route.get('capability') == CAPABILITY for route in g['routes'])]
    assert owners == [(TARGET, WITNESS)]
    assert 'Magic' in GATEABLE_ENEMY_COPY_ABILITIES and 'Magic' not in STARTING_COPY_ABILITIES


@pytest.mark.parametrize('scenario', [
    'enabled', 'gating_off', 'absent', 'wrong_source', 'mixed', 'failable', 'no_policy'])
def test_starting_inventory_reconciles_only_enabled_raw_source_once(monkeypatch, scenario):
    from .. import regions
    raw = evidence()['source_policy']
    if scenario in {'wrong_source', 'mixed', 'failable'}:
        raw = policy(2, pool=['Magic', 'Bomb'] if scenario == 'mixed' else
                     ['Beam'] if scenario == 'wrong_source' else ['Magic'],
                     weight=50 if scenario == 'failable' else 0).policy
    set_rule_test_policy(monkeypatch, lambda *args, **kwargs: raw)
    multiworld = setup_multiworld(KirbyAmWorld, steps=('generate_early',), seed=12, options={
        'ability_randomization_mode': 1, 'ability_gating': int(scenario != 'gating_off'), 'accessibility': 'minimal'})
    world = multiworld.worlds[1]
    if scenario == 'no_policy':
        world._enemy_copy_ability_policy = None
    if scenario == 'absent':
        create_regions = regions.create_regions

        def without_target(current_world):
            result = create_regions(current_world)
            target = next(e for e in result[OWNER].exits if e.name == f'{OWNER} -> {EXIT}')
            result[OWNER].exits.remove(target)
            return result

        monkeypatch.setattr(regions, 'create_regions', without_target)
    early = [world.create_item('Magic Ability') for _ in range(2)]
    assert all(i.classification == ItemClassification.useful for i in early)
    for item in early:
        multiworld.push_precollected(item)
    ready = world.create_item('Magic Ability')
    ready.classification = ItemClassification.progression
    multiworld.push_precollected(ready)
    unrelated = world.create_item('Sleep Ability')
    multiworld.push_precollected(unrelated)
    assert multiworld.state.count('Magic Ability', 1) == 1
    world.create_regions()
    expected = 3 if scenario == 'enabled' else 1
    assert multiworld.state.count('Magic Ability', 1) == expected
    assert CollectionState(multiworld).count('Magic Ability', 1) == expected
    assert all(item.advancement is (scenario == 'enabled') for item in early)
    assert ready.advancement and not unrelated.advancement
    for item in (*early, ready):
        multiworld.state.remove(item)
    assert not multiworld.state.has('Magic Ability', 1)


@pytest.mark.parametrize('gating,area_keys,health,room_sanity,count', [
    (1, 0, 100, 0, 0), (1, 1, 500, 1, 1), (1, 0, 100, 1, 3), (0, 1, 500, 0, 3)])
def test_normal_full_pool_seed12_fill_start_inventory_and_accessibility(
        tmp_path, monkeypatch, gating, area_keys, health, room_sanity, count):
    import Main
    generated, before, after = [], [], []
    main, create_regions = Main.main, KirbyAmWorld.create_regions

    def capture_regions(world):
        before.append(world.multiworld.state.count('Magic Ability', world.player))
        create_regions(world)
        after.append(world.multiworld.state.count('Magic Ability', world.player))

    def capture_main(*args, **kwargs):
        multiworld = main(*args, **kwargs)
        generated.append(multiworld)
        return multiworld

    monkeypatch.setattr(KirbyAmWorld, 'create_regions', capture_regions)
    monkeypatch.setattr(Main, 'main', capture_main)
    player = tmp_path / 'player.yaml'
    player.write_text('name: Magic533\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n'
                      '  ability_randomization_mode: 1\n  ability_randomization_no_ability_weight: 0\n'
                      '  minimum_health: 1\n  maximum_health: 1\n'
                      f'  ability_gating: {gating}\n  area_keys: {area_keys}\n'
                      f'  enemy_health_multiplier: {health}\n  room_sanity: {room_sanity}\n'
                      f'  start_inventory:\n    Magic Ability: {count}\n  accessibility: full\n', encoding='utf-8')
    archive = generate_archive_from_fixture(player, tmp_path / 'out', seed=12)
    decoded = load_multidata_from_archive(archive)
    raw = decoded['slot_data'][1]['enemy_copy_ability_policy']
    assert json.loads(json.dumps(raw)) == evidence()['source_policy']
    assert SourcePolicy(raw).grant('FOLEY', lambda _: True).guaranteed == frozenset({'Magic'})
    assert decoded['precollected_items'][1].count(3860121) == count
    assert before == [0] and after == [count if gating else 0]
    multiworld, = generated
    assert not multiworld.get_unfilled_locations()
    assert multiworld.can_beat_game() and multiworld.fulfills_accessibility()
    state = CollectionState(multiworld)
    assert state.count('Magic Ability', 1) == (count if gating else 0)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    target = multiworld.get_entrance(f'{OWNER} -> {EXIT}', 1)
    assert target.access_rule(state) is (bool(count) or not gating)
    starting = [i for i in multiworld.precollected_items[1] if i.name == 'Magic Ability']
    assert len(starting) == count
    assert all(i.classification == (ItemClassification.progression if gating else ItemClassification.useful)
               for i in starting)
    for item in starting:
        state.remove(item)
    assert not state.has('Magic Ability', 1) and target.access_rule(state) is (not gating)
