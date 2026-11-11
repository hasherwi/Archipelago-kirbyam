"""Finite Doo-to-UFO acquisition and maximum-charge large shot for Chocolate only."""

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest
from BaseClasses import CollectionState, ItemClassification

from .support.source_policy import set_rule_test_policy
from .. import KirbyAmWorld, traversal_rules as rules
from ..data import data
from ..traversal import (
    CAPABILITY_ABILITIES, CAPABILITY_CONSUMED_ABILITIES, Position, SourcePolicy, compile_traversal_graph,
)
from ..traversal_data import _validate_target, room_traversal_graph, room_traversal_targets
from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive
from .test_cabbage_parasol import CHEST, OWNER, TARGET, UPSTREAM, cabbage_row
from .test_mini_traversal import make_world
from .test_traversal import policy

ROOT = Path(__file__).parents[1]
EVIDENCE = ROOT / 'dev-docs/cabbage-ufo-acceptance.json'
CAPABILITY = 'bomb_517_ufo_top_charge'


def document():
    return json.loads(EVIDENCE.read_text())


@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('area_keys', [False, True])
def test_finite_source_and_own_capability(gating, area_keys):
    graph = room_traversal_graph(TARGET, 'hub2_ufo_entry', area_keys)
    resolver = SourcePolicy(document()['source_policy'])
    assert graph.access_region == UPSTREAM and graph.required_guaranteed_source == ('WADDLE_DOO', 'UFO')
    assert all(start.equipped == 'Normal' for start in graph.starts)
    assert [node.room for node in graph.nodes] == [591, 517, 517, 517]
    source, = graph.placements
    assert (source.identity, source.source_key, source.renewable, source.retry_evidence) == (
        '0x088CA04C', 'WADDLE_DOO', False, None)
    assert [route.resets_room_instance for route in graph.routes] == [True, False, False]
    assert all(not route.items and not route.opens and not route.recover_dropped_ability for route in graph.routes)
    assert graph.routes[-1].capability == CAPABILITY
    assert graph.routes[-1].allowed_abilities == CAPABILITY_ABILITIES[CAPABILITY] == frozenset({'UFO'})
    assert CAPABILITY not in CAPABILITY_CONSUMED_ABILITIES
    chest, = graph.required_targets
    owned = frozenset({'UFO Ability'})
    result = graph.evaluate(resolver, owned, gating, allow_documented_retries=True)
    assert result.reaches(chest) and not result.retry_assumptions
    assert any(p.equipped == 'UFO' and source.identity in p.consumed for p in result.positions if p.node == chest)
    assert graph.evaluate(resolver, frozenset(), gating).reaches(chest) is (not gating)
    assert not replace(graph, placements=()).evaluate(resolver, owned, gating).reaches(chest)
    assert not replace(graph, placements=(replace(source, node=chest),)).evaluate(
        resolver, owned, gating).reaches(chest)
    spent = replace(graph, starts=(Position(source.node, 'Normal', consumed=frozenset({source.identity})),))
    assert not spent.evaluate(resolver, owned, gating).reaches(chest)
    for ability in ('Beam', 'Smash', 'Fire', 'Missile', 'Parasol', 'Spark', 'Ice', 'Sword', 'Fighter'):
        assert not graph.evaluate(policy(1, pool=[ability]), owned, gating).positions


@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('pool,weight', [(['UFO', 'Beam'], 0), (['UFO'], 50), (['UFO'], 100), (None, 0)])
def test_uncertain_raw_policy_is_not_narrowed_by_permission(gating, pool, weight):
    resolver = policy(2, pool=pool, weight=weight)
    assert not rules.target_applies(cabbage_row(), resolver)
    graph = room_traversal_graph(TARGET, 'hub2_ufo_entry')
    for owned in (frozenset(), frozenset({'UFO Ability'}), frozenset({'UFO Ability', 'Beam Ability'})):
        assert not graph.evaluate(resolver, owned, gating, allow_documented_retries=True).positions


@pytest.mark.parametrize('mode', [1, 2])
def test_excluded_source_retains_native_beam(mode):
    resolver = policy(mode, pool=['UFO'])
    resolver.writes.pop(0x3517FE, None)
    bitmap = bytearray(resolver.source_config)
    bitmap[4:8] = (int.from_bytes(bitmap[4:8], 'little') & ~(1 << 18)).to_bytes(4, 'little')
    resolver.source_config = bytes(bitmap)
    assert resolver.grant('WADDLE_DOO', lambda _: True).guaranteed == frozenset({'Beam'})
    assert not room_traversal_graph(TARGET, 'hub2_ufo_entry').evaluate(
        resolver, frozenset({'UFO Ability'}), True).positions


@pytest.mark.parametrize('gating', [0, 1])
@pytest.mark.parametrize('area_keys', [0, 1])
@pytest.mark.parametrize('statues', [0, 1])
@pytest.mark.parametrize('room_sanity', [0, 1])
@pytest.mark.parametrize('minor_chests', [False, True])
def test_actual_world_scope_and_existing_progression(
        monkeypatch, gating, area_keys, statues, room_sanity, minor_chests):
    raw = document()['source_policy']
    monkeypatch.setattr(KirbyAmWorld, 'ENABLE_MINOR_CHESTS', minor_chests)
    set_rule_test_policy(monkeypatch, lambda *args, **kwargs: raw)
    world = make_world(1, gating, accessibility='minimal', area_keys=area_keys,
                       ability_randomization_statues=statues, room_sanity=room_sanity)
    state = CollectionState(world.multiworld)
    item = world.create_item('UFO Ability')
    # UFO already has an independent progression classification; no new factory reason is needed.
    assert item.classification == ItemClassification.progression
    if minor_chests:
        chest = world.multiworld.get_location(data.locations[CHEST].label, 1)
        assert chest.address == 3960511 and chest.parent_region.name == OWNER
        state.can_reach_region = lambda name, player: name == OWNER
        state.collect(item, prevent_sweep=True)
        assert not chest.access_rule(state)
        state.remove(item)
        state.can_reach_region = lambda name, player: name == UPSTREAM
        assert chest.access_rule(state) is (not gating)
        state.collect(world.create_item('Missile Ability'), prevent_sweep=True)
        assert chest.access_rule(state) is (not gating)
        state.collect(item, prevent_sweep=True)
        assert chest.access_rule(state)
        state.remove(item)
        assert chest.access_rule(state) is (not gating)
    else:
        with pytest.raises(KeyError):
            world.multiworld.get_location(data.locations[CHEST].label, 1)
    state.can_reach_region = lambda name, player: name == OWNER
    owner = world.multiworld.get_region(OWNER, 1)
    assert all(exit.access_rule(state) for exit in owner.exits)
    room_checks = [loc for loc in owner.locations if loc.address != 3960511]
    assert len(room_checks) == room_sanity and all(loc.access_rule(state) for loc in room_checks)
    entrance = world.multiworld.get_entrance(
        'REGION_RAINBOW_ROUTE/ROOM_1_13_LOWER -> REGION_CABBAGE_CAVERN/ROOM_3_04', 1)
    assert entrance.access_rule(state) is (not area_keys)
    state.collect(world.create_item('Cabbage Cavern - Area Key'), prevent_sweep=True)
    assert entrance.access_rule(state)


@pytest.mark.parametrize('gating', [0, 1])
@pytest.mark.parametrize('area_keys', [0, 1])
@pytest.mark.parametrize('health', [100, 500])
@pytest.mark.parametrize('count', [0, 1, 3])
def test_full_seed52_fill_and_start_inventory(tmp_path, monkeypatch, gating, area_keys, health, count):
    import Main

    generated = []
    main = Main.main

    def capture(*args, **kwargs):
        multiworld = main(*args, **kwargs)
        generated.append(multiworld)
        return multiworld

    monkeypatch.setattr(Main, 'main', capture)
    player = tmp_path / 'player.yaml'
    player.write_text(
        'name: UFO517\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n'
        '  ability_randomization_mode: 1\n  ability_randomization_no_ability_weight: 0\n'
        f'  ability_gating: {gating}\n  area_keys: {area_keys}\n  enemy_health_multiplier: {health}\n'
        '  minimum_health: 1\n  maximum_health: 1\n  accessibility: full\n'
        + (f'  start_inventory:\n    UFO Ability: {count}\n' if count else ''), encoding='utf-8')
    archive = generate_archive_from_fixture(player, tmp_path / 'out', seed=52)
    decoded = load_multidata_from_archive(archive)
    raw = decoded['slot_data'][1]['enemy_copy_ability_policy']
    assert {**raw, 'allowed_abilities': list(raw['allowed_abilities'])} == document()['source_policy']
    assert SourcePolicy(raw).grant('WADDLE_DOO', lambda _: True).guaranteed == frozenset({'UFO'})
    assert decoded['locations'][1][3960511]
    assert decoded['precollected_items'][1].count(3860114) == count
    multiworld, = generated
    assert not multiworld.get_unfilled_locations()
    assert multiworld.can_beat_game() and multiworld.fulfills_accessibility()
    world = multiworld.worlds[1]
    assert all(item.classification == ItemClassification.progression
               for item in multiworld.precollected_items[1] if item.name == 'UFO Ability')
    assert multiworld.state.count('UFO Ability', 1) == count
    assert CollectionState(multiworld).count('UFO Ability', 1) == count
    state = CollectionState(multiworld)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    chest = multiworld.get_location(data.locations[CHEST].label, 1)
    assert chest.access_rule(state) is (not gating or bool(count))
    state.collect(world.create_item('UFO Ability'), prevent_sweep=True)
    assert chest.access_rule(state)


def test_prior_catalog_and_graphs_unchanged():
    doc = document()
    rooms = json.loads((ROOT / 'data/regions/rooms.json').read_text())
    row = rooms[OWNER]['traversal']['targets'][0]

    def digest(value):
        return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

    assert len(doc['prior_graphs_sha256']) == 9
    for name, expected in doc['prior_graphs_sha256'].items():
        assert digest(row['graphs'][name]) == expected
    stripped = deepcopy(rooms)
    target = stripped[OWNER]['traversal']['targets'][0]
    target['graphs'].pop('hub2_ufo_entry')
    target['requires_guaranteed_source']['abilities'].remove('UFO')
    # Whole-catalog hash in native evidence is historical after the main merge.
    # Preserve this exact historical target; the union catalog guards other targets.
    assert digest(target) == '771bf115d82bba1ea3eefa281675049d2354f4d384df9b95bebcaf04e8272cdf'
    owners = [(row['id'], name) for row in room_traversal_targets('block') for name, graph in row['graphs'].items()
              if any(route.get('capability') == CAPABILITY for route in graph['routes'])]
    assert owners == [(TARGET, 'hub2_ufo_entry')]


@pytest.mark.parametrize('mode,pool,weight,accepted', [
    (0, None, 0, False), (1, ['UFO'], 0, True), (1, ['Sleep'], 0, False),
    (2, ['UFO'], 0, True), (2, ['UFO', 'Beam'], 0, False),
    (2, ['UFO', 'Fighter'], 0, False), (2, ['UFO'], 50, False),
    (2, ['UFO'], 100, False), (2, None, 0, False),
])
@pytest.mark.parametrize('gating', [False, True])
def test_raw_singleton_only_and_ten_separate_or_graphs(mode, pool, weight, accepted, gating):
    resolver = policy(mode, pool=pool, weight=weight)
    row = cabbage_row()
    names = ('Beam', 'Smash', 'Fire', 'Missile', 'Parasol', 'Spark', 'Ice', 'Sword', 'Fighter', 'UFO')
    assert row['requires_guaranteed_source'] == {'source_key': 'WADDLE_DOO', 'abilities': list(names)}
    assert len(row['graphs']) == 10
    owned = frozenset(f'{name} Ability' for name in names)
    graph = room_traversal_graph(TARGET, 'hub2_ufo_entry')
    chest, = graph.required_targets
    assert graph.evaluate(resolver, owned, gating, allow_documented_retries=True).reaches(chest) is accepted
    if accepted:
        results = [rules.graph_succeeds(g, resolver, owned, gating, retries=False)
                   for g in rules.target_graphs(row, False)]
        assert results == [False] * 9 + [True]
        carrot = next(r for r in room_traversal_targets('block') if r['id'] == 'bomb_719_room13')
        assert not rules.target_applies(carrot, resolver)


@pytest.mark.parametrize('mutation', ['swimming', 'source_room', 'target_room'])
def test_compiler_and_kernel_preserve_scoped_dry_attack(mutation):
    raw = deepcopy(cabbage_row()['graphs']['hub2_ufo_entry'])
    graph = room_traversal_graph(TARGET, 'hub2_ufo_entry')
    if mutation == 'swimming':
        raw['routes'][-1]['water_state'] = 'swimming'
        graph = replace(graph, routes=(*graph.routes[:-1], replace(graph.routes[-1], water_state='swimming')))
    else:
        key = graph.routes[-1].source if mutation == 'source_room' else graph.routes[-1].target
        for node in raw['nodes']:
            if node['id'] == key:
                node['native_room'] = 733
        graph = replace(graph, nodes=tuple(replace(n, room=733) if n.key == key else n for n in graph.nodes))
    with pytest.raises(ValueError, match='native room and dry'):
        compile_traversal_graph(raw)
    with pytest.raises(ValueError, match='native room and dry'):
        graph.evaluate(SourcePolicy(document()['source_policy']), frozenset({'UFO Ability'}), True)


@pytest.mark.parametrize('update', [
    {'id': 'bomb_733_yellow'}, {'kind': 'switch'}, {'native_room': 733},
    {'region': 'REGION_CARROT_CASTLE/ROOM_5_16'}, {'location': 'MINOR_CHEST_SPRAY_PAINT_02'},
    {'requires_guaranteed_source': {'source_key': 'SPARKY', 'ability': 'UFO'}},
    {'requires_guaranteed_source': {'source_key': 'WADDLE_DOO', 'abilities': ['UFO']}},
    {'requires_guaranteed_source': {'source_key': 'WADDLE_DOO', 'abilities': ['Beam', 'UFO']}},
])
def test_target_whitelist_cannot_leak_to_another_target_or_subset(update):
    row = deepcopy(cabbage_row())
    row.update(update)
    with pytest.raises(ValueError, match='source applicability|applicability condition'):
        _validate_target(row)


@pytest.mark.parametrize('independent', [False, True])
@pytest.mark.parametrize('permission', [False, True])
def test_real_collection_state_requires_independent_hub2(monkeypatch, independent, permission):
    set_rule_test_policy(monkeypatch, lambda *args, **kwargs: document()['source_policy'])
    world = make_world(1, 1, accessibility='minimal', area_keys=0)
    mw = world.multiworld
    for region in mw.get_regions(1):
        for exit_ in region.exits:
            exit_.access_rule = lambda state: False
    menu = mw.get_region('Menu', 1)
    menu.connect(mw.get_region(OWNER, 1), 'test direct Chocolate owner')
    if independent:
        menu.connect(mw.get_region(UPSTREAM, 1), 'test independent Hub2')
    state = CollectionState(mw)
    if permission:
        state.collect(world.create_item('UFO Ability'), prevent_sweep=True)
    assert state.can_reach_region(OWNER, 1)
    assert state.can_reach_region(UPSTREAM, 1) is independent
    assert mw.get_location(data.locations[CHEST].label, 1).can_reach(state) is (independent and permission)


def test_normal_ingress_and_actual_ufo_equipment_have_no_shortcut():
    graph = room_traversal_graph(TARGET, 'hub2_ufo_entry')
    resolver = SourcePolicy(document()['source_policy'])
    source, = graph.placements
    chest, = graph.required_targets
    assert [r.required_equipment for r in graph.routes] == [
        frozenset({'Normal'}), frozenset({'Normal'}), frozenset({'UFO'})]
    for route in graph.routes:
        cut = replace(graph, routes=tuple(r for r in graph.routes if r != route))
        assert not cut.evaluate(resolver, frozenset({'UFO Ability'}), True).reaches(chest)
    for ability in ('Normal', 'Beam', 'Fighter', 'Sword'):
        isolated = replace(graph, placements=(), starts=(Position(source.node, ability),))
        assert not isolated.evaluate(resolver, frozenset({'UFO Ability'}), True).reaches(chest)
