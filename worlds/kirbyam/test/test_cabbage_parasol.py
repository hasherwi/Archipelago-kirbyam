"""Finite Parasol carry and dry forward swing only for the Chocolate chest."""

import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from BaseClasses import CollectionState, ItemClassification

from .. import KirbyAmWorld, traversal_rules as rules
from ..data import data
from ..enemy_ability_data import GATEABLE_ENEMY_COPY_ABILITIES
from ..traversal import Position, SourcePolicy
from ..traversal_data import load_room_traversal, room_traversal_graph, room_traversal_targets
from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive
from .test_mini_traversal import make_world
from .test_traversal import policy

TARGET = 'bomb_517_chocolate'
OWNER = 'REGION_CABBAGE_CAVERN/ROOM_3_06'
UPSTREAM = 'REGION_CABBAGE_CAVERN/ROOM_3_HUB_2'
CHEST = 'MINOR_CHEST_SPRAY_PAINT_12'
EVIDENCE = Path(__file__).parents[1] / 'dev-docs/cabbage-parasol-acceptance.json'
POLICIES = [
    (0, None, 0, 'Beam'), (1, ['Beam'], 0, 'Beam'), (1, ['Smash'], 0, 'Smash'),
    (1, ['Missile'], 0, 'Missile'), (1, ['Parasol'], 0, 'Parasol'), (1, ['Fire'], 0, 'Fire'),
    (1, ['Spark'], 0, 'Spark'), (1, ['Ice'], 0, 'Ice'), (1, ['Sword'], 0, 'Sword'),
    (1, ['Fighter'], 0, 'Fighter'),
    (2, ['Parasol'], 0, 'Parasol'), (2, ['Parasol', 'Smash'], 0, None),
    (2, ['Parasol', 'Fire'], 0, None), (2, ['Parasol', 'Missile'], 0, None), (2, ['Parasol', 'Ice'], 0, None),
    (2, ['Parasol'], 50, None), (2, ['Parasol'], 100, None),
    (2, None, 0, None),
]


def cabbage_row():
    return next(row for row in room_traversal_targets('block') if row['id'] == TARGET)


@pytest.mark.parametrize('mode,pool,weight,ability', POLICIES)
@pytest.mark.parametrize('statues', [False, True])
def test_independent_nine_way_or_policy(mode, pool, weight, ability, statues):
    resolver = policy(mode, pool=pool, weight=weight, statues=statues)
    row = cabbage_row()
    assert rules.target_applies(row, resolver) is (ability is not None)
    if ability:
        results = [rules.graph_succeeds(g, resolver, frozenset({f'{ability} Ability'}), True, retries=False)
                   for g in rules.target_graphs(row, False)]
        assert results == [ability == name for name in
                           ('Beam', 'Smash', 'Fire', 'Missile', 'Parasol', 'Spark', 'Ice', 'Sword', 'Fighter')]
    # The same enemy key does not widen Carrot's independently reviewed alternatives.
    carrot = next(r for r in room_traversal_targets('block') if r['id'] == 'bomb_719_room13')
    if ability == 'Parasol':
        assert not rules.target_applies(carrot, resolver)


@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('area_keys', [False, True])
def test_finite_source_permission_and_actual_equipment(gating, area_keys):
    graph = room_traversal_graph(TARGET, 'hub2_parasol_entry', area_keys)
    resolver = SourcePolicy(json.loads(EVIDENCE.read_text())['source_policy'])
    assert graph.access_region == UPSTREAM
    assert graph.required_guaranteed_source == ('WADDLE_DOO', 'Parasol')
    assert all(start.equipped == 'Normal' for start in graph.starts)
    assert [(n.key.rsplit(':', 1)[-1], n.room) for n in graph.nodes] == [
        ('hub2', 591), ('arrival', 517), ('source', 517), ('chest', 517)]
    source, = graph.placements
    assert (source.identity, source.source_key, source.renewable, source.retry_evidence) == (
        '0x088CA04C', 'WADDLE_DOO', False, None)
    assert [r.resets_room_instance for r in graph.routes] == [True, False, False]
    assert all(not r.items and not r.opens and not r.recover_dropped_ability for r in graph.routes)
    assert graph.routes[-1].capability == 'bomb_517_parasol_swing'
    assert graph.routes[-1].allowed_abilities == frozenset({'Parasol'})
    chest, = graph.required_targets
    owned = frozenset({'Parasol Ability'})
    result = graph.evaluate(resolver, owned, gating, allow_documented_retries=True)
    assert result.reaches(chest) and not result.retry_assumptions
    arrivals = [p for p in result.positions if p.node == chest]
    assert any(p.equipped == 'Parasol' for p in arrivals)
    assert all(p.equipped in {'Parasol', 'Normal'} and source.identity in p.consumed for p in arrivals)
    assert graph.evaluate(resolver, frozenset(), gating).reaches(chest) is (not gating)
    assert not replace(graph, placements=()).evaluate(resolver, owned, gating).reaches(chest)
    assert not replace(graph, placements=(replace(source, node=chest),)).evaluate(
        resolver, owned, gating).reaches(chest)
    spent = replace(graph, starts=(Position(source.node, 'Normal', consumed=frozenset({source.identity})),))
    assert not spent.evaluate(resolver, owned, gating).reaches(chest)
    for ability in ('Beam', 'Smash', 'Spark', 'Ice', 'Fire', 'Missile'):
        assert not graph.evaluate(policy(1, pool=[ability]), owned, gating).reaches(chest)


@pytest.mark.parametrize('pool,weight', [
    (['Parasol', 'Smash'], 0), (['Parasol', 'Ice'], 0), (['Parasol', 'Fire'], 0),
    (['Parasol', 'Missile'], 0), (['Parasol'], 50), (['Parasol'], 100), (None, 0),
])
@pytest.mark.parametrize('owned', [
    frozenset(), frozenset({'Parasol Ability'}),
    frozenset({'Parasol Ability', 'Smash Ability', 'Ice Ability', 'Fire Ability', 'Missile Ability'}),
])
@pytest.mark.parametrize('gating', [False, True])
def test_raw_policy_guard_prevents_permission_narrowing(pool, weight, owned, gating):
    graph = room_traversal_graph(TARGET, 'hub2_parasol_entry')
    resolver = policy(2, pool=pool, weight=weight)
    assert not graph.evaluate(resolver, owned, gating, allow_documented_retries=True).positions


@pytest.mark.parametrize('update', [
    {'id': 'bomb_719_room13'}, {'kind': 'switch'}, {'native_room': 719},
    {'region': 'REGION_CARROT_CASTLE/ROOM_5_07'}, {'location': 'MINOR_CHEST_MUSIC_NOTE_10'},
    {'requires_guaranteed_source': {'source_key': 'HOT_HEAD', 'abilities': ['Beam', 'Smash', 'Parasol']}},
    {'requires_guaranteed_source': {'source_key': 'WADDLE_DOO', 'abilities': ['Parasol']}},
    {'requires_guaranteed_source': {'source_key': 'WADDLE_DOO', 'abilities': ['Beam', 'Smash', 'Parasol', 'Ice']}},
])
def test_target_condition_cannot_spread(update):
    row = deepcopy(cabbage_row())
    row.update(update)
    region = row.pop('region')
    with pytest.raises(ValueError, match='applicability'):
        load_room_traversal({region: {'traversal': {'version': 1, 'targets': [row]}}})


@pytest.mark.parametrize('gating', [0, 1])
@pytest.mark.parametrize('area_keys', [0, 1])
@pytest.mark.parametrize('statues', [0, 1])
@pytest.mark.parametrize('room_sanity', [0, 1])
@pytest.mark.parametrize('minor_chests', [False, True])
def test_actual_world_binds_only_chest_and_preserves_progression(
        monkeypatch, gating, area_keys, statues, room_sanity, minor_chests):
    raw = json.loads(EVIDENCE.read_text())['source_policy']
    monkeypatch.setattr(KirbyAmWorld, 'ENABLE_MINOR_CHESTS', minor_chests)
    monkeypatch.setattr('worlds.kirbyam.build_enemy_copy_ability_policy', lambda *args, **kwargs: raw)
    world = make_world(1, gating, accessibility='minimal', area_keys=area_keys,
                       ability_randomization_statues=statues, room_sanity=room_sanity,
                       ability_randomization_no_ability_weight=0)
    state = CollectionState(world.multiworld)
    state.can_reach_region = lambda name, player: name == OWNER
    item = world.create_item('Parasol Ability')
    assert 'Parasol' in GATEABLE_ENEMY_COPY_ABILITIES
    assert item.classification == (ItemClassification.progression if gating and minor_chests
                                   else ItemClassification.useful)
    if minor_chests:
        chest = world.multiworld.get_location(data.locations[CHEST].label, 1)
        assert chest.address == 3960511 and chest.parent_region.name == OWNER
        assert not chest.access_rule(state)
        state.collect(item, prevent_sweep=True)
        assert not chest.access_rule(state)  # Permission does not supply Hub2 access.
        state.remove(item)
        state.can_reach_region = lambda name, player: name == UPSTREAM
        assert chest.access_rule(state) is (not gating)
        for wrong in ('Beam Ability', 'Smash Ability', 'Fire Ability', 'Missile Ability'):
            state.collect(world.create_item(wrong), prevent_sweep=True)
        assert chest.access_rule(state) is (not gating)
        state.collect(item, prevent_sweep=True)
        assert state.has('Parasol Ability', 1) is bool(gating)
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
    assert len(room_checks) == room_sanity
    assert all(loc.access_rule(state) for loc in room_checks)
    area = world.multiworld.get_entrance(
        'REGION_RAINBOW_ROUTE/ROOM_1_13_LOWER -> REGION_CABBAGE_CAVERN/ROOM_3_04', 1)
    assert area.access_rule(state) is (not area_keys)
    state.collect(world.create_item('Cabbage Cavern - Area Key'), prevent_sweep=True)
    assert area.access_rule(state)


@pytest.mark.parametrize('mode,pool,weight,ability', POLICIES)
@pytest.mark.parametrize('gating', [0, 1])
def test_actual_world_uncertain_policies_keep_prior_rule(monkeypatch, mode, pool, weight, ability, gating):
    resolver = policy(mode, pool=pool, weight=weight, minny=False)
    monkeypatch.setattr('worlds.kirbyam.build_enemy_copy_ability_policy', lambda *args, **kwargs: resolver.policy)
    world = make_world(mode, gating, accessibility='minimal', ability_randomization_no_ability_weight=weight)
    chest = world.multiworld.get_location(data.locations[CHEST].label, 1)
    assert world.create_item('Parasol Ability').classification == (
        ItemClassification.progression if gating and ability == 'Parasol' else ItemClassification.useful)
    state = CollectionState(world.multiworld)
    state.can_reach_region = lambda name, player: name == OWNER
    assert chest.access_rule(state) is (ability is None)
    for name in ('Beam', 'Smash', 'Fire', 'Missile', 'Parasol', 'Spark', 'Ice', 'Sword', 'Fighter'):
        state.collect(world.create_item(f'{name} Ability'), prevent_sweep=True)
    assert chest.access_rule(state) is (ability is None)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    assert chest.access_rule(state)
    state.remove(world.create_item('Parasol Ability'))
    assert chest.access_rule(state) is (not (ability == 'Parasol' and gating))


@pytest.mark.parametrize('gating,area_keys,health', [(0, 0, 100), (1, 0, 100), (0, 1, 500), (1, 1, 500)])
def test_full_seed29_fill_uses_actual_policy_and_progression(tmp_path, monkeypatch, gating, area_keys, health):
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
        'name: Parasol517\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n'
        '  ability_randomization_mode: 1\n  ability_randomization_no_ability_weight: 0\n'
        f'  ability_gating: {gating}\n  area_keys: {area_keys}\n  enemy_health_multiplier: {health}\n'
        '  minimum_health: 1\n  maximum_health: 1\n  accessibility: full\n', encoding='utf-8')
    archive = generate_archive_from_fixture(player, tmp_path / 'out', seed=29)
    decoded = load_multidata_from_archive(archive)
    raw = decoded['slot_data'][1]['enemy_copy_ability_policy']
    assert {**raw, 'allowed_abilities': list(raw['allowed_abilities'])} == (
        json.loads(EVIDENCE.read_text())['source_policy'])
    assert SourcePolicy(raw).grant('WADDLE_DOO', lambda _: True).guaranteed == frozenset({'Parasol'})
    assert decoded['locations'][1][3960511]
    multiworld, = generated
    assert not multiworld.get_unfilled_locations()
    assert multiworld.can_beat_game() and multiworld.fulfills_accessibility()
    world = multiworld.worlds[1]
    state = CollectionState(multiworld)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    chest = multiworld.get_location(data.locations[CHEST].label, 1)
    assert chest.access_rule(state) is (not gating)
    state.collect(world.create_item('Parasol Ability'), prevent_sweep=True)
    assert chest.access_rule(state)


@pytest.mark.parametrize('gating,minor_chests,count', [
    (1, True, 1), (1, True, 3), (0, True, 1), (1, False, 1), (1, False, 3),
])
def test_full_seed29_start_inventory_is_reconciled_after_regions(
        tmp_path, monkeypatch, gating, minor_chests, count):
    import Main

    generated, region_states = [], []
    main, create_regions = Main.main, KirbyAmWorld.create_regions

    def capture_regions(world):
        create_regions(world)
        region_states.append(world.multiworld.state.count('Parasol Ability', world.player))

    def capture_main(*args, **kwargs):
        multiworld = main(*args, **kwargs)
        generated.append(multiworld)
        return multiworld

    monkeypatch.setattr(KirbyAmWorld, 'ENABLE_MINOR_CHESTS', minor_chests)
    monkeypatch.setattr(KirbyAmWorld, 'create_regions', capture_regions)
    monkeypatch.setattr(Main, 'main', capture_main)
    player = tmp_path / 'player.yaml'
    player.write_text(
        'name: Starting Parasol\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n'
        '  ability_randomization_mode: 1\n  ability_randomization_no_ability_weight: 0\n'
        f'  ability_gating: {gating}\n  start_inventory:\n    Parasol Ability: {count}\n'
        f'  room_sanity: {int(not minor_chests)}\n'  # Supply slots when minor chests are disabled.
        '  minimum_health: 1\n  maximum_health: 1\n  accessibility: full\n', encoding='utf-8')
    archive = generate_archive_from_fixture(player, tmp_path / 'out', seed=29)
    decoded = load_multidata_from_archive(archive)
    raw = decoded['slot_data'][1]['enemy_copy_ability_policy']
    assert SourcePolicy(raw).grant('WADDLE_DOO', lambda _: True).guaranteed == frozenset({'Parasol'})
    assert decoded['precollected_items'][1].count(3860105) == count
    multiworld, = generated
    assert not multiworld.get_unfilled_locations()
    assert multiworld.can_beat_game() and multiworld.fulfills_accessibility()
    expected_count = count if gating and minor_chests else 0
    assert region_states == [expected_count]  # Existing state repaired once, before fill.
    starting = [item for item in multiworld.precollected_items[1] if item.name == 'Parasol Ability']
    assert len(starting) == count
    assert all(item.classification == (ItemClassification.progression if expected_count else ItemClassification.useful)
               for item in starting)
    state = CollectionState(multiworld)
    assert state.count('Parasol Ability', 1) == expected_count  # Fresh states see the same permissions.
    if not minor_chests:
        with pytest.raises(KeyError):
            multiworld.get_location(data.locations[CHEST].label, 1)
        return
    chest = multiworld.get_location(data.locations[CHEST].label, 1)
    state.can_reach_region = lambda name, player: name == OWNER
    assert not chest.access_rule(state)  # Starting permission still does not equip or supply Hub2.
    state.can_reach_region = lambda name, player: name == UPSTREAM
    assert chest.access_rule(state)
    for item in starting:
        state.remove(item)
    assert not state.has('Parasol Ability', 1)
    assert chest.access_rule(state) is (not gating)


def test_reconciliation_does_not_recollect_already_progression_parasol(monkeypatch):
    from test.general import setup_multiworld

    raw = json.loads(EVIDENCE.read_text())['source_policy']
    monkeypatch.setattr('worlds.kirbyam.build_enemy_copy_ability_policy', lambda *args, **kwargs: raw)
    multiworld = setup_multiworld(KirbyAmWorld, steps=('generate_early',), seed=29, options={
        'ability_randomization_mode': 1, 'ability_gating': 1, 'accessibility': 'minimal',
    })
    world = multiworld.worlds[1]
    ready = world.create_item('Parasol Ability')
    ready.classification = ItemClassification.progression
    multiworld.push_precollected(ready)
    for _ in range(2):
        early = world.create_item('Parasol Ability')
        assert early.classification == ItemClassification.useful
        multiworld.push_precollected(early)
    assert multiworld.state.count('Parasol Ability', 1) == 1
    world.create_regions()
    assert multiworld.state.count('Parasol Ability', 1) == 3
    assert CollectionState(multiworld).count('Parasol Ability', 1) == 3


def test_promotion_requires_actual_chest_and_source_policy():
    raw = json.loads(EVIDENCE.read_text())['source_policy']
    world = SimpleNamespace(player=1, _enemy_copy_ability_policy=raw, _ability_gating_enabled=lambda: True,
                            multiworld=SimpleNamespace(get_location=lambda *args: object()))
    assert rules.cabbage_parasol_is_progression(world)

    def absent(*args):
        raise KeyError('disabled')

    world.multiworld.get_location = absent
    assert not rules.cabbage_parasol_is_progression(world)
    world._enemy_copy_ability_policy = None
    assert not rules.cabbage_parasol_is_progression(world)


@pytest.mark.parametrize('mode', [1, 2])
def test_source_table_and_bitmap_eligibility_cannot_be_invented(mode):
    resolver = policy(mode, pool=['Parasol'])
    graph = room_traversal_graph(TARGET, 'hub2_parasol_entry')
    assert graph.evaluate(resolver, frozenset({'Parasol Ability'}), True).reaches(TARGET + ':chest')
    # Excluded source categories retain their native grant, never an inferred
    # assignment from another enemy. Exercise the actual runtime-derived inputs.
    resolver.writes.pop(0x3517FE, None)
    bitmap = bytearray(resolver.source_config)
    bitmap[4:8] = (int.from_bytes(bitmap[4:8], 'little') & ~(1 << 18)).to_bytes(4, 'little')
    resolver.source_config = bytes(bitmap)
    assert resolver.grant('WADDLE_DOO', lambda _: True).guaranteed == frozenset({'Beam'})
    assert not graph.evaluate(resolver, frozenset({'Parasol Ability'}), True).positions


@pytest.mark.parametrize('pool,weight', [(['Parasol', 'Missile'], 0), (['Parasol'], 50), (['Parasol'], 100)])
def test_uncertain_sources_do_not_promote_pre_region_start_inventory(monkeypatch, pool, weight):
    from test.general import setup_multiworld

    raw = policy(2, pool=pool, weight=weight).policy
    monkeypatch.setattr('worlds.kirbyam.build_enemy_copy_ability_policy', lambda *args, **kwargs: raw)
    multiworld = setup_multiworld(KirbyAmWorld, steps=('generate_early',), seed=29, options={
        'ability_randomization_mode': 2, 'ability_gating': 1, 'accessibility': 'minimal',
        'ability_randomization_no_ability_weight': weight,
    })
    world = multiworld.worlds[1]
    item = world.create_item('Parasol Ability')
    multiworld.push_precollected(item)
    world.create_regions()
    assert item.classification == ItemClassification.useful
    assert not multiworld.state.has(item.name, 1) and not CollectionState(multiworld).has(item.name, 1)
