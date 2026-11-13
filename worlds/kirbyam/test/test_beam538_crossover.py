"""Optional native538 left exit: a new edge must fail closed, never inherit access."""

from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace

import pytest
from BaseClasses import CollectionState, ItemClassification
from Options import Accessibility

from .support.source_policy import set_rule_test_policy
from .. import KirbyAmWorld, traversal_rules as rules
from ..area_keys import area_key_entrance_area_ids
from ..data import data
from ..enemy_ability_data import GATEABLE_ENEMY_COPY_ABILITIES
from ..traversal import Position, SourcePolicy, compile_traversal_graph
from ..traversal_data import _validate_target, graph_items, room_traversal_graph, room_traversal_targets
from .test_mini_traversal import make_world
from .test_traversal import policy

TARGET = 'bomb_538_beam_left_exit'
CAPABILITY = 'bomb_538_beam_left_crossover'
OWNER = 'REGION_RAINBOW_ROUTE/ROOM_1_36_VERTICAL'
HORIZONTAL = 'REGION_RAINBOW_ROUTE/ROOM_1_36_HORIZONTAL'
DESTINATION = 'REGION_RAINBOW_ROUTE/ROOM_1_39'
UPSTREAM = 'REGION_MUSTARD_MOUNTAIN/ROOM_4_06'
SOURCE_ROOM = 'REGION_RAINBOW_ROUTE/ROOM_1_37'
RIGHT539 = 'REGION_MUSTARD_MOUNTAIN/ROOM_4_01'
EDGE = f'{OWNER} -> {DESTINATION}'
POLICIES = [
    (0, None, 0, True), (1, ['Beam'], 0, True), (1, ['Sword'], 0, False),
    (2, ['Beam'], 0, True), (2, ['Beam', 'Sword'], 0, False),
    (2, ['Beam'], 50, False), (2, ['Beam'], 100, False), (2, ['Sleep'], 0, False),
]


def target_row():
    return next(row for row in room_traversal_targets('block') if row['id'] == TARGET)


def beam_graph(area_keys=False):
    return room_traversal_graph(TARGET, 'normal544_beam_entry', area_keys)


@pytest.mark.parametrize('mode,pool,weight,supported', POLICIES)
@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('area_keys', [False, True])
@pytest.mark.parametrize('statues', [False, True])
def test_always_installed_optional_source_rule(monkeypatch, mode, pool, weight, supported, gating, area_keys, statues):
    resolver = policy(mode, pool=pool, weight=weight, statues=statues, minny=False)
    row = target_row()
    monkeypatch.setattr(rules, 'extra_traversal_targets', lambda: (row,))
    assert rules.target_applies(row, resolver)  # Unsupported policies are NOT skipped.
    assert rules.static_extra_witness(resolver)  # Optional route must not reject this assignment.
    target, indirect = SimpleNamespace(access_rule=lambda state: state.base_rule), []
    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy=resolver.policy,
        _ability_gating_enabled=lambda: gating, _area_keys_enabled=lambda: area_keys,
        options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=statues),
                                accessibility=Accessibility(Accessibility.option_full)),
        multiworld=SimpleNamespace(get_entrance=lambda name, player: target if name == EDGE else None,
                                   get_region=lambda name, player: name,
                                   register_indirect_condition=lambda region, edge: indirect.append((region, edge))),
    )
    rules.install_extra_traversal_rules(world)
    assert indirect == [(UPSTREAM, target)]
    accessible, owned = set(), set()
    state = SimpleNamespace(base_rule=True, has=lambda item, player: item in owned,
                            can_reach_region=lambda name, player: name in accessible)
    for invalid in (OWNER, HORIZONTAL, SOURCE_ROOM, DESTINATION, 'REGION_RAINBOW_ROUTE/ROOM_1_40'):
        accessible.add(invalid)
    assert not target.access_rule(state)
    owned.update(f'{name} Ability' for name in GATEABLE_ENEMY_COPY_ABILITIES)
    owned.add('Beam Ability')
    assert not target.access_rule(state)  # Every permission still does not supply independent544 access.
    accessible.add(UPSTREAM)
    assert target.access_rule(state) is supported
    owned.clear()
    assert target.access_rule(state) is supported  # Beam is not gateable.
    state.base_rule = False
    assert not target.access_rule(state)


@pytest.mark.parametrize('raw', [None, [], 'missing'])
def test_missing_policy_also_closes_new_edge(monkeypatch, raw):
    monkeypatch.setattr(rules, 'extra_traversal_targets', lambda: (target_row(),))
    target = SimpleNamespace(access_rule=lambda state: True)
    world = SimpleNamespace(player=1, _enemy_copy_ability_policy=raw,
                            multiworld=SimpleNamespace(get_entrance=lambda name, player: target))
    rules.install_extra_traversal_rules(world)
    assert not target.access_rule(object())


@pytest.mark.parametrize('mode,pool,weight,supported', POLICIES)
@pytest.mark.parametrize('gating,area_keys,disabled,statues', [
    (0, 0, False, 0), (1, 1, False, 1), (1, 0, True, 1), (0, 1, True, 0)])
def test_actual_normalized_edge_preserves_corridors_checks_keys_and_classification(
        monkeypatch, mode, pool, weight, supported, gating, area_keys, disabled, statues):
    resolver = policy(mode, pool=pool, weight=weight, statues=statues, minny=False)
    set_rule_test_policy(monkeypatch, lambda *a, **k: resolver.policy)
    monkeypatch.setattr(KirbyAmWorld, 'ENABLE_MINOR_CHESTS', not disabled)
    world = make_world(mode, gating, accessibility='minimal', area_keys=area_keys,
                       ability_randomization_statues=statues, room_sanity=int(not disabled),
                       ability_randomization_no_ability_weight=weight)
    mw = world.multiworld
    target = mw.get_entrance(EDGE, 1)
    assert target.parent_region.name == OWNER and target.connected_region.name == DESTINATION
    assert EDGE not in area_key_entrance_area_ids()  # Native537 is Rainbow39, not Mustard/native539.
    state = CollectionState(mw)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    assert target.access_rule(state) is supported
    beam = world.create_item('Beam Ability')
    assert beam.classification == ItemClassification.useful
    state.collect(beam, prevent_sweep=True)
    assert target.access_rule(state) is supported
    state.remove(beam)
    assert target.access_rule(state) is supported
    assert HORIZONTAL not in data.regions[OWNER].exits and RIGHT539 not in data.regions[OWNER].exits
    assert OWNER not in data.regions[HORIZONTAL].exits and OWNER not in data.regions[DESTINATION].exits
    for destination in ('REGION_RAINBOW_ROUTE/ROOM_1_35', SOURCE_ROOM):
        assert mw.get_entrance(f'{OWNER} -> {destination}', 1).access_rule(state)
    assert mw.get_entrance(f'{DESTINATION} -> {HORIZONTAL}', 1).access_rule(state)
    assert mw.get_entrance(f'{HORIZONTAL} -> {DESTINATION}', 1).access_rule(state)
    right = mw.get_entrance(f'{HORIZONTAL} -> {RIGHT539}', 1)
    assert right.access_rule(state) is (not area_keys)
    state.collect(world.create_item('Mustard Mountain - Area Key'), prevent_sweep=True)
    assert right.access_rule(state)
    checks = [loc for loc in mw.get_locations(1) if loc.address == 3961006]
    assert len(checks) == int(not disabled)
    assert all(loc.parent_region.name == OWNER and loc.access_rule(state) for loc in checks)
    assert not mw.get_region(HORIZONTAL, 1).locations


@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('area_keys', [False, True])
def test_finite_normal_ingress_and_carried_beam_are_required(gating, area_keys):
    graph = beam_graph(area_keys)
    assert graph.access_region == UPSTREAM
    assert graph.required_guaranteed_source == ('WADDLE_DOO', 'Beam')
    source, = graph.placements
    assert (source.identity, source.source_key, source.renewable) == ('0x088B6138', 'WADDLE_DOO', False)
    assert not source.retry_evidence and not graph_items(graph)
    rooms = {node.key: node.room for node in graph.nodes}
    assert graph.starts == (Position(TARGET + ':upper544'),)
    assert [(rooms[r.source], rooms[r.target]) for r in graph.routes if r.room_transition] == [
        (544, 543), (543, 542), (542, 538)]
    assert [r.capability for r in graph.routes if r.capability] == [CAPABILITY]
    assert graph.routes[-2].target == graph.routes[-1].source  # Separate Scarfy handling and ledge attack.
    assert all(r.required_equipment == frozenset({'Normal'}) for r in graph.routes[:5])
    assert all(r.required_equipment == frozenset({'Beam'}) for r in graph.routes[5:])
    assert all(r.opens is None for r in graph.routes)
    resolver, target = SourcePolicy({'mode': 0}), next(iter(graph.required_targets))
    result = graph.evaluate(resolver, frozenset(), gating)
    assert result.reaches(target) and not result.retry_assumptions
    assert any(p.node == source.node and p.equipped == 'Beam' and source.identity in p.consumed
               for p in result.positions)
    assert any(p.node == target and p.equipped == 'Beam' and not p.opened for p in result.positions)
    owned = frozenset({'Beam Ability'})
    assert not replace(graph, placements=()).evaluate(resolver, owned, gating).reaches(target)
    for route in graph.routes:
        cut = replace(graph, routes=tuple(r for r in graph.routes if r != route))
        assert not cut.evaluate(resolver, owned, gating).reaches(target)
    spent = replace(graph, starts=(Position(source.node, consumed=frozenset({source.identity})),))
    assert not spent.evaluate(resolver, owned, gating).reaches(target)
    for node in graph.nodes[6:]:
        if node.key not in graph.required_targets:
            assert not replace(graph, starts=(Position(node.key),)).evaluate(
                resolver, owned, gating).reaches(target)


@pytest.mark.parametrize('pool,weight', [(['Beam'], 0), (['Beam', 'Sword'], 0), (['Beam'], 50)])
def test_raw_source_certainty_and_inventory_monotonicity(pool, weight):
    graph, resolver = beam_graph(), policy(2, pool=pool, weight=weight)
    inventories = [frozenset(), frozenset({'Beam Ability'}), frozenset({'Beam Ability', 'Sword Ability'}),
                   frozenset(f'{a} Ability' for a in GATEABLE_ENEMY_COPY_ABILITIES)]
    for retries in (False, True):
        results = [graph.evaluate(resolver, owned, True, retries).reaches(next(iter(graph.required_targets)))
                   for owned in inventories]
        assert results == sorted(results)
        assert results == ([True] * 4 if pool == ['Beam'] and not weight else [False] * 4)


@pytest.mark.parametrize('mutation', ['swimming', 'wrong_room'])
def test_compiler_and_kernel_keep_attack_room_and_medium(mutation):
    raw = deepcopy(target_row()['graphs']['normal544_beam_entry'])
    graph = beam_graph()
    if mutation == 'swimming':
        raw['routes'][-1]['water_state'] = 'swimming'
        graph = replace(graph, routes=(*graph.routes[:-1], replace(graph.routes[-1], water_state='swimming')))
    else:
        for node in raw['nodes']:
            if node['native_room'] == 538:
                node['native_room'] = 542
        graph = replace(graph, nodes=tuple(replace(n, room=542) if n.room == 538 else n for n in graph.nodes))
    with pytest.raises(ValueError, match='native room and dry'):
        compile_traversal_graph(raw)
    with pytest.raises(ValueError, match='native room and dry'):
        graph.evaluate(policy(), frozenset(), True)


@pytest.mark.parametrize('update', [
    {'requires_guaranteed_source': {'source_key': 'WADDLE_DOO', 'ability': 'Beam'}},
    {'requires_any_guaranteed_source': []}, {'required_for_generation': True}, {'new_connection': 'yes'},
    {'exit': None},
])
def test_new_connection_schema_forbids_permissive_applicability(update):
    row = deepcopy(target_row())
    row.update(update)
    with pytest.raises(ValueError, match='new_connection|New optional connections'):
        _validate_target(row)


@pytest.mark.parametrize('independent', [False, True])
def test_collection_state_cannot_bootstrap544_from_new_connection(independent):
    world = make_world(0, 0, area_keys=0)
    mw = world.multiworld
    # Actual graph traversal, no can_reach_region mock. Isolate the new connection
    # and deliberately add its strongest possible circular dependency.
    for region in mw.get_regions(1):
        for exit_ in region.exits:
            if exit_.name != EDGE:
                exit_.access_rule = lambda state: False
    menu = mw.get_region('Menu', 1)
    menu.connect(mw.get_region(OWNER, 1), 'test initial vertical')
    mw.get_region(DESTINATION, 1).connect(mw.get_region(UPSTREAM, 1), 'test circular544')
    if independent:
        menu.connect(mw.get_region(UPSTREAM, 1), 'test independent544')
    state = CollectionState(mw)
    assert state.can_reach_region(OWNER, 1)
    assert state.can_reach_region(UPSTREAM, 1) is independent
    assert state.can_reach_region(DESTINATION, 1) is independent


@pytest.mark.parametrize('mode,gating,area_keys,disabled', [(0, 1, 0, False), (1, 1, 1, False), (2, 0, 1, True)])
def test_full_generation_accessibility_with_optional_supported_or_unsupported_source(
        tmp_path, monkeypatch, mode, gating, area_keys, disabled):
    import Main
    from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive
    generated, main = [], Main.main

    def capture(*args, **kwargs):
        mw = main(*args, **kwargs)
        generated.append(mw)
        return mw

    monkeypatch.setattr(Main, 'main', capture)
    monkeypatch.setattr(KirbyAmWorld, 'ENABLE_MINOR_CHESTS', not disabled)
    player = tmp_path / 'player.yaml'
    player.write_text('name: Beam538\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n'
                      f'  ability_randomization_mode: {mode}\n  ability_gating: {gating}\n'
                      f'  area_keys: {area_keys}\n  room_sanity: {int(not disabled)}\n'
                      '  minimum_health: 1\n  maximum_health: 1\n  accessibility: full\n', encoding='utf-8')
    archive = generate_archive_from_fixture(player, tmp_path / 'out', seed=538)
    raw = load_multidata_from_archive(archive)['slot_data'][1]['enemy_copy_ability_policy']
    mw, = generated
    assert not mw.get_unfilled_locations()
    assert mw.can_beat_game() and mw.fulfills_accessibility()
    state = CollectionState(mw)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    supported = SourcePolicy(raw).grant('WADDLE_DOO', lambda _: True).guaranteed == frozenset({'Beam'})
    assert mw.get_entrance(EDGE, 1).access_rule(state) is supported
    if mode == 0:
        assert supported
    elif mode == 2:
        assert not supported


def test_real_upstream_mini_permission_and_mustard_key_remain_required():
    world = make_world(0, 1, area_keys=1)
    mw = world.multiworld
    state = CollectionState(mw)
    for item in data.items.values():
        if item.label not in {'Mini Ability', 'Mustard Mountain - Area Key'}:
            state.collect(world.create_item(item.label), prevent_sweep=True)
    target = mw.get_entrance(EDGE, 1)
    assert not state.can_reach_region(UPSTREAM, 1) and not target.access_rule(state)
    key = world.create_item('Mustard Mountain - Area Key')
    state.collect(key, prevent_sweep=True)
    assert not state.can_reach_region(UPSTREAM, 1) and not target.access_rule(state)
    mini = world.create_item('Mini Ability')
    state.collect(mini, prevent_sweep=True)
    assert state.can_reach_region(UPSTREAM, 1) and target.access_rule(state)
    state.remove(key)
    assert not state.can_reach_region(UPSTREAM, 1) and not target.access_rule(state)
    state.collect(key, prevent_sweep=True)
    state.remove(mini)
    assert not state.can_reach_region(UPSTREAM, 1) and not target.access_rule(state)
