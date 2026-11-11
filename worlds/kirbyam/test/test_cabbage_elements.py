"""Exact finite Spark/Ice Chocolate alternatives; inventory is permission only."""

from dataclasses import replace

import pytest
from BaseClasses import CollectionState, ItemClassification

from .. import KirbyAmWorld, traversal_rules as rules
from ..data import data
from ..enemy_ability_data import GATEABLE_ENEMY_COPY_ABILITIES
from ..traversal import CAPABILITY_ABILITIES, ROOM_SCOPED_CAPABILITIES, Position, SourcePolicy
from ..traversal_data import room_traversal_graph
from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive
from .test_cabbage_parasol import CHEST, OWNER, TARGET, UPSTREAM, cabbage_row
from .test_mini_traversal import make_world
from .test_traversal import policy


@pytest.mark.parametrize('ability', ['Spark', 'Ice'])
@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('area_keys', [False, True])
def test_exact_finite_graph(ability, gating, area_keys):
    graph = room_traversal_graph(TARGET, f'hub2_{ability.lower()}_entry', area_keys)
    resolver = policy(1, pool=[ability])
    owned = frozenset({f'{ability} Ability'})
    assert graph.access_region == UPSTREAM
    assert graph.required_guaranteed_source == ('WADDLE_DOO', ability)
    assert all(start.equipped == 'Normal' for start in graph.starts)
    assert [(n.key.rsplit(':', 1)[-1], n.room) for n in graph.nodes] == [
        ('hub2', 591), ('arrival', 517), ('source', 517), ('chest', 517)]
    source, = graph.placements
    assert (source.identity, source.source_key, source.renewable, source.retry_evidence) == (
        '0x088CA04C', 'WADDLE_DOO', False, None)
    assert [r.resets_room_instance for r in graph.routes] == [True, False, False]
    assert all(not r.items and not r.opens and not r.recover_dropped_ability for r in graph.routes)
    assert graph.routes[-1].capability == TARGET
    assert graph.routes[-1].allowed_abilities == frozenset({ability})
    assert CAPABILITY_ABILITIES[TARGET] == frozenset({'Beam', 'Spark', 'Ice', 'Smash'})
    assert ROOM_SCOPED_CAPABILITIES[TARGET] == 517
    chest, = graph.required_targets
    result = graph.evaluate(resolver, owned, gating, allow_documented_retries=True)
    assert result.reaches(chest) and not result.retry_assumptions
    assert any(p.equipped == ability and source.identity in p.consumed
               for p in result.positions if p.node == chest)
    assert graph.evaluate(resolver, frozenset(), gating).reaches(chest) is (not gating)
    assert not replace(graph, placements=()).evaluate(resolver, owned, gating).reaches(chest)
    assert not replace(graph, placements=(replace(source, node=chest),)).evaluate(
        resolver, owned, gating).reaches(chest)
    spent = replace(graph, starts=(Position(source.node, 'Normal', consumed=frozenset({source.identity})),))
    assert not spent.evaluate(resolver, owned, gating).reaches(chest)
    for other in ('Beam', 'Smash', 'Spark', 'Ice', 'Fire', 'Missile', 'Parasol'):
        if other != ability:
            assert not graph.evaluate(policy(1, pool=[other]), owned, gating).positions


@pytest.mark.parametrize('ability', ['Spark', 'Ice'])
@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('mixed,weight', [(True, 0), (False, 50), (False, 100)])
def test_raw_guarantee_not_permission_filtered(ability, gating, mixed, weight):
    graph = room_traversal_graph(TARGET, f'hub2_{ability.lower()}_entry')
    pool = [ability, 'Missile'] if mixed else [ability]
    resolver = policy(2, pool=pool, weight=weight)
    assert not rules.target_applies(cabbage_row(), resolver)
    for owned in (frozenset(), frozenset({f'{ability} Ability'}),
                  frozenset({f'{ability} Ability', 'Missile Ability'})):
        assert not graph.evaluate(resolver, owned, gating, allow_documented_retries=True).positions


@pytest.mark.parametrize('ability', ['Spark', 'Ice'])
@pytest.mark.parametrize('mode', [1, 2])
def test_excluded_original_source_cannot_supply_assignment(ability, mode):
    resolver = policy(mode, pool=[ability])
    resolver.writes.pop(0x3517FE, None)
    bitmap = bytearray(resolver.source_config)
    bitmap[4:8] = (int.from_bytes(bitmap[4:8], 'little') & ~(1 << 18)).to_bytes(4, 'little')
    resolver.source_config = bytes(bitmap)
    assert resolver.grant('WADDLE_DOO', lambda _: True).guaranteed == frozenset({'Beam'})
    graph = room_traversal_graph(TARGET, f'hub2_{ability.lower()}_entry')
    assert not graph.evaluate(resolver, frozenset({f'{ability} Ability'}), True).positions


@pytest.mark.parametrize('ability', ['Spark', 'Ice'])
@pytest.mark.parametrize('gating', [0, 1])
@pytest.mark.parametrize('area_keys', [0, 1])
@pytest.mark.parametrize('statues', [0, 1])
@pytest.mark.parametrize('room_sanity', [0, 1])
@pytest.mark.parametrize('minor_chests', [False, True])
def test_actual_world_scope(monkeypatch, ability, gating, area_keys, statues, room_sanity, minor_chests):
    # Start with shuffled assignments, then isolate Doo so prior promotion reasons are absent.
    raw = natural_policy(ability)
    monkeypatch.setattr(KirbyAmWorld, 'ENABLE_MINOR_CHESTS', minor_chests)
    monkeypatch.setattr('worlds.kirbyam.build_enemy_copy_ability_policy', lambda *args, **kwargs: raw)
    world = make_world(1, gating, accessibility='minimal', area_keys=area_keys,
                       ability_randomization_statues=statues, room_sanity=room_sanity)
    state = CollectionState(world.multiworld)
    item = world.create_item(f'{ability} Ability')
    assert ability in GATEABLE_ENEMY_COPY_ABILITIES
    assert item.classification == (ItemClassification.progression if gating and minor_chests
                                   else ItemClassification.useful)
    assert rules.cabbage_element_is_progression(world, ability) is bool(gating and minor_chests)
    if minor_chests:
        chest = world.multiworld.get_location(data.locations[CHEST].label, 1)
        assert chest.address == 3960511 and chest.parent_region.name == OWNER
        state.can_reach_region = lambda name, player: name == OWNER
        assert not chest.access_rule(state)
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
    area = world.multiworld.get_entrance(
        'REGION_RAINBOW_ROUTE/ROOM_1_13_LOWER -> REGION_CABBAGE_CAVERN/ROOM_3_04', 1)
    assert area.access_rule(state) is (not area_keys)
    state.collect(world.create_item('Cabbage Cavern - Area Key'), prevent_sweep=True)
    assert area.access_rule(state)


def natural_policy(ability):
    from ..enemy_ability_data import ABILITY_NAME_TO_ID
    raw = policy(1, pool=sorted(set(ABILITY_NAME_TO_ID) - {'Normal', 'Master', 'Wait'}), minny=False).policy
    raw['seed'] = {'Spark': 14282527318440564224, 'Ice': 13204005821666718668}[ability]
    resolver = SourcePolicy(raw)
    assert resolver.grant('WADDLE_DOO', lambda _: True).guaranteed == frozenset({ability})
    assert resolver.grant('SPARKY', lambda _: True).guaranteed != frozenset({'Spark'})
    assert resolver.grant('MR_FROSTY', lambda _: True).guaranteed != frozenset({'Ice'})
    return raw


@pytest.mark.parametrize('ability', ['Spark', 'Ice'])
@pytest.mark.parametrize('gating,minor_chests,count', [
    (1, True, 0), (1, True, 1), (1, True, 3), (0, True, 1), (1, False, 3),
])
def test_natural_full_pool_fill_and_main_start_order(tmp_path, monkeypatch, ability, gating, minor_chests, count):
    import Main

    generated, before, after = [], [], []
    main, create_regions = Main.main, KirbyAmWorld.create_regions
    name = f'{ability} Ability'

    def capture_regions(world):
        before.append(world.multiworld.state.count(name, world.player))
        create_regions(world)
        after.append(world.multiworld.state.count(name, world.player))

    def capture_main(*args, **kwargs):
        multiworld = main(*args, **kwargs)
        generated.append(multiworld)
        return multiworld

    monkeypatch.setattr(KirbyAmWorld, 'ENABLE_MINOR_CHESTS', minor_chests)
    monkeypatch.setattr(KirbyAmWorld, 'create_regions', capture_regions)
    monkeypatch.setattr(Main, 'main', capture_main)
    player = tmp_path / 'player.yaml'
    player.write_text(
        'name: CabbageElement\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n'
        '  ability_randomization_mode: 1\n  ability_randomization_no_ability_weight: 0\n'
        f'  ability_gating: {gating}\n  start_inventory:\n    {name}: {count}\n'
        f'  room_sanity: {int(not minor_chests)}\n'
        '  minimum_health: 1\n  maximum_health: 1\n  accessibility: full\n', encoding='utf-8')
    archive = generate_archive_from_fixture(player, tmp_path / 'out', seed={'Spark': 22, 'Ice': 149}[ability])
    decoded = load_multidata_from_archive(archive)
    raw = decoded['slot_data'][1]['enemy_copy_ability_policy']
    assert len(raw['allowed_abilities']) == 25
    assert raw['seed'] == natural_policy(ability)['seed']
    assert SourcePolicy(raw).grant('WADDLE_DOO', lambda _: True).guaranteed == frozenset({ability})
    multiworld, = generated
    assert not multiworld.get_unfilled_locations()
    assert multiworld.can_beat_game() and multiworld.fulfills_accessibility()
    expected = count if gating and minor_chests else 0
    assert before == [0] and after == [expected]
    starting = [item for item in multiworld.precollected_items[1] if item.name == name]
    assert len(starting) == count
    assert all(item.classification == (ItemClassification.progression if gating and minor_chests
                                       else ItemClassification.useful) for item in starting)
    state = CollectionState(multiworld)
    assert state.count(name, 1) == expected
    if minor_chests:
        chest = multiworld.get_location(data.locations[CHEST].label, 1)
        assert decoded['locations'][1][3960511]
        state.can_reach_region = lambda name, player: name == OWNER
        assert not chest.access_rule(state)
        state.can_reach_region = lambda name, player: name == UPSTREAM
        assert chest.access_rule(state) is (bool(count) or not gating)
        for item in starting:
            state.remove(item)
        assert not state.has(name, 1)
        assert chest.access_rule(state) is (not gating)


@pytest.mark.parametrize('ability', ['Spark', 'Ice'])
@pytest.mark.parametrize('mode,gating,area_keys', [(1, 1, 0), (1, 0, 1), (2, 1, 1)])
def test_singleton_generated_policy_with_optional_sources_off(tmp_path, monkeypatch, ability, mode, gating, area_keys):
    import Main
    from ..ability_randomization import build_enemy_copy_ability_policy

    def singleton(*args, **kwargs):
        return build_enemy_copy_ability_policy(*args, **kwargs, whitelist=[ability])

    generated = []
    main = Main.main

    def capture(*args, **kwargs):
        multiworld = main(*args, **kwargs)
        generated.append(multiworld)
        return multiworld

    monkeypatch.setattr('worlds.kirbyam.build_enemy_copy_ability_policy', singleton)
    monkeypatch.setattr(Main, 'main', capture)
    player = tmp_path / 'player.yaml'
    player.write_text(
        'name: SingletonElement\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n'
        f'  ability_randomization_mode: {mode}\n  ability_gating: {gating}\n  area_keys: {area_keys}\n'
        '  ability_randomization_statues: 0\n  ability_randomization_minibosses: 0\n'
        '  ability_randomization_boss_spawns: 0\n  ability_randomization_minny: 0\n'
        '  ability_randomization_passive_enemies: 0\n  ability_randomization_no_ability_weight: 0\n'
        '  minimum_health: 1\n  maximum_health: 1\n  enemy_health_multiplier: 500\n'
        '  room_sanity: 1\n  accessibility: full\n', encoding='utf-8')
    archive = generate_archive_from_fixture(player, tmp_path / 'out', seed=22 if ability == 'Spark' else 149)
    raw = load_multidata_from_archive(archive)['slot_data'][1]['enemy_copy_ability_policy']
    assert list(raw['allowed_abilities']) == [ability]
    assert SourcePolicy(raw).grant('WADDLE_DOO', lambda _: True).guaranteed == frozenset({ability})
    multiworld, = generated
    assert not multiworld.get_unfilled_locations()
    assert multiworld.can_beat_game() and multiworld.fulfills_accessibility()
    state = CollectionState(multiworld)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    chest = multiworld.get_location(data.locations[CHEST].label, 1)
    assert chest.access_rule(state) is (not gating)
    state.collect(multiworld.worlds[1].create_item(f'{ability} Ability'), prevent_sweep=True)
    assert chest.access_rule(state)


@pytest.mark.parametrize('ability', ['Spark', 'Ice'])
def test_reconciliation_does_not_double_collect_progression(monkeypatch, ability):
    from test.general import setup_multiworld

    raw = natural_policy(ability)
    monkeypatch.setattr('worlds.kirbyam.build_enemy_copy_ability_policy', lambda *args, **kwargs: raw)
    multiworld = setup_multiworld(KirbyAmWorld, steps=('generate_early',), seed=22, options={
        'ability_randomization_mode': 1, 'ability_gating': 1, 'accessibility': 'minimal',
    })
    world = multiworld.worlds[1]
    name = f'{ability} Ability'
    ready = world.create_item(name)
    ready.classification = ItemClassification.progression
    multiworld.push_precollected(ready)
    for _ in range(2):
        early = world.create_item(name)
        assert early.classification == ItemClassification.useful
        multiworld.push_precollected(early)
    assert multiworld.state.count(name, 1) == 1
    world.create_regions()
    assert multiworld.state.count(name, 1) == CollectionState(multiworld).count(name, 1) == 3


@pytest.mark.parametrize('ability', ['Spark', 'Ice'])
@pytest.mark.parametrize('pool,weight', [(['Spark', 'Ice'], 0), (['Spark'], 50), (['Ice'], 100)])
def test_uncertain_policy_keeps_fallback_and_does_not_promote(monkeypatch, ability, pool, weight):
    raw = policy(2, pool=pool, weight=weight).policy
    monkeypatch.setattr('worlds.kirbyam.build_enemy_copy_ability_policy', lambda *args, **kwargs: raw)
    world = make_world(2, 1, accessibility='minimal', ability_randomization_no_ability_weight=weight)
    item = world.create_item(f'{ability} Ability')
    assert item.classification == ItemClassification.useful
    assert not rules.cabbage_element_is_progression(world, ability)
    state = CollectionState(world.multiworld)
    state.can_reach_region = lambda name, player: name == OWNER
    assert world.multiworld.get_location(data.locations[CHEST].label, 1).access_rule(state)


@pytest.mark.parametrize('ability', ['Spark', 'Ice'])
def test_prior_independent_promotion_reason_is_preserved(monkeypatch, ability):
    # Singleton policies retain the earlier guaranteed Sparky/Frosty reason even without Chocolate.
    raw = policy(1, pool=[ability]).policy
    monkeypatch.setattr('worlds.kirbyam.build_enemy_copy_ability_policy', lambda *args, **kwargs: raw)
    world = make_world(1, 1, accessibility='minimal')
    get_location = world.multiworld.get_location

    def without_chocolate(name, player):
        if name == data.locations[CHEST].label:
            raise KeyError(name)
        return get_location(name, player)

    monkeypatch.setattr(world.multiworld, 'get_location', without_chocolate)
    assert not rules.cabbage_element_is_progression(world, ability)
    assert world.create_item(f'{ability} Ability').classification == ItemClassification.progression


@pytest.mark.parametrize('ability', ['Spark', 'Ice'])
@pytest.mark.parametrize('weight', [0, 50, 100])
def test_uncertain_early_duplicates_stay_useful(monkeypatch, ability, weight):
    from test.general import setup_multiworld

    raw = policy(2, pool=['Spark', 'Ice'] if weight == 0 else [ability], weight=weight).policy
    monkeypatch.setattr('worlds.kirbyam.build_enemy_copy_ability_policy', lambda *args, **kwargs: raw)
    multiworld = setup_multiworld(KirbyAmWorld, steps=('generate_early',), seed=22, options={
        'ability_randomization_mode': 2, 'ability_gating': 1, 'accessibility': 'minimal',
        'ability_randomization_no_ability_weight': weight,
    })
    world = multiworld.worlds[1]
    items = [world.create_item(f'{ability} Ability') for _ in range(3)]
    for item in items:
        multiworld.push_precollected(item)
    world.create_regions()
    assert all(item.classification == ItemClassification.useful for item in items)
    assert multiworld.state.count(items[0].name, 1) == CollectionState(multiworld).count(items[0].name, 1) == 0
