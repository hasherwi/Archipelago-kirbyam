"""Separate dry Spark and underwater Sword witnesses for one exact Room9 exit."""

from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace

import pytest
from BaseClasses import CollectionState, ItemClassification
from Fill import distribute_items_restrictive
from test.general import setup_multiworld
from worlds.AutoWorld import call_all

from .support.source_policy import set_rule_test_policy
from .. import KirbyAmWorld, traversal_rules as rules
from ..enemy_ability_data import ABILITY_NAME_TO_ID, GATEABLE_ENEMY_COPY_ABILITIES
from ..traversal import Grant, Node, Position, Route, SourcePolicy, reachable_positions
from ..traversal_data import load_room_traversal, room_traversal_graph, room_traversal_targets
from .test_mini_traversal import make_world
from .test_traversal import policy

OWNER = 'REGION_RAINBOW_ROUTE/ROOM_1_08'
UPSTREAM = 'REGION_RAINBOW_ROUTE/ROOM_1_06_LOWER_MID'
EXIT = 'REGION_RAINBOW_ROUTE/ROOM_1_09'
TARGET = 'bomb_110_room9'
SWORD = 'bomb_110_room9_underwater_sword'
POLICIES = [
    (0, None, 0, True), (1, ['Spark'], 0, True), (1, ['Sword'], 0, True),
    (1, ['Beam'], 0, False), (2, ['Spark'], 0, True), (2, ['Sword'], 0, True),
    (2, ['Spark', 'Sword'], 0, False), (2, ['Sword', 'Beam'], 0, False),
    (2, ['Sword'], 50, False), (2, ['Sword'], 100, False), (2, None, 0, False),
]


def target_row():
    return next(row for row in room_traversal_targets('block') if row['id'] == TARGET)


@pytest.mark.parametrize('mode,pool,weight,applies', POLICIES)
@pytest.mark.parametrize('gating', [0, 1])
@pytest.mark.parametrize('statues', [0, 1])
def test_actual_world_policy_or_requires_only_the_available_permission(
        monkeypatch, mode, pool, weight, applies, gating, statues):
    resolver = policy(mode, pool=pool, weight=weight, statues=statues, minny=False)
    # Restricted policies isolate world wiring; real full-accessibility fill is
    # checked separately with unmodified broad production policies.
    set_rule_test_policy(monkeypatch, lambda *a, **kw: resolver.policy)
    world = make_world(mode, gating, accessibility='minimal', ability_randomization_statues=statues,
                       ability_randomization_no_ability_weight=weight)
    assert rules.target_applies(target_row(), resolver) is applies
    entrance = world.multiworld.get_entrance(f'{OWNER} -> {EXIT}', 1)
    state = CollectionState(world.multiworld)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    assert entrance.access_rule(state) is (not applies or not gating)
    for ability, source in (('Spark', 'SPARKY'), ('Sword', 'SWORD_KNIGHT')):
        item = world.create_item(f'{ability} Ability')
        state.collect(item, prevent_sweep=True)
        supported = resolver.grant(source, lambda _: True).guaranteed == frozenset({ability})
        assert entrance.access_rule(state) is (not applies or not gating or supported)
        state.remove(item)
    # Neither owner nor another Room6 compartment supplies the reviewed entry,
    # even with both permissions owned.
    for ability in ('Spark', 'Sword'):
        state.collect(world.create_item(f'{ability} Ability'), prevent_sweep=True)
    state.can_reach_region = lambda name, player: name in {OWNER, 'REGION_RAINBOW_ROUTE/ROOM_1_06_UPPER'}
    assert entrance.access_rule(state) is (not applies)
    spark_progression = gating and resolver.grant('SPARKY', lambda _: True).guaranteed == frozenset({'Spark'})
    assert world.create_item('Spark Ability').classification == (
        ItemClassification.progression if spark_progression else ItemClassification.useful)
    assert world.create_item('Sword Ability').classification == ItemClassification.progression
    assert 'Sword' in GATEABLE_ENEMY_COPY_ABILITIES


@pytest.mark.parametrize('witness,ability,source_key,identity', [
    ('upper_entry', 'Spark', 'SPARKY', '0x088B743C'),
    ('upper_entry_sword', 'Sword', 'SWORD_KNIGHT', '0x088B74CC'),
])
@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('area_keys', [False, True])
def test_both_alternatives_require_their_own_finite_physical_source(
        witness, ability, source_key, identity, gating, area_keys):
    graph = room_traversal_graph(TARGET, witness, area_keys)
    assert graph.access_region == UPSTREAM
    assert all(start.equipped == 'Normal' for start in graph.starts)
    source, = graph.placements
    assert (source.identity, source.source_key, source.renewable, source.retry_evidence) == (
        identity, source_key, False, None)
    assert all(route.opens is None and not route.recover_dropped_ability for route in graph.routes)
    target, = graph.required_targets
    owned = frozenset({f'{ability} Ability'})
    assert graph.evaluate(policy(), frozenset(), gating).reaches(target) is (not gating)
    assert graph.evaluate(policy(), owned, gating).reaches(target)
    assert not replace(graph, placements=()).evaluate(policy(), owned, gating).reaches(target)
    behind = replace(graph, placements=(replace(source, node=target),))
    assert not behind.evaluate(policy(), owned, gating).reaches(target)
    for unsupported in (policy(1, pool=['Beam']), policy(2, pool=['Spark', 'Sword']),
                        policy(2, pool=[ability], weight=50), policy(2, pool=[ability], weight=100)):
        # Grant pools are permission-filtered by the runtime. Own both supported
        # alternatives here so a mixed live pool stays genuinely uncertain.
        result = graph.evaluate(unsupported, owned | {"Spark Ability", "Sword Ability"}, gating,
                                allow_documented_retries=True)
        assert not result.reaches(target) and not result.retry_assumptions


@pytest.mark.parametrize('grant', [
    Grant(frozenset()), Grant(frozenset({'Normal'})), Grant(frozenset({'Unknown'})),
    Grant(frozenset({'Spark', 'Sword'}), randomized=True),
    Grant(frozenset({'Sword'}), randomized=True, can_fail=True),
])
def test_no_source_or_finite_uncertainty_is_not_an_or_guarantee(grant):
    assert not rules.target_applies(target_row(), SimpleNamespace(grant=lambda *args: grant))


@pytest.mark.parametrize('blocked,expected', [
    ({'SPARKY'}, [False, True]), ({'SWORD_KNIGHT'}, [True, False]),
    ({'SPARKY', 'SWORD_KNIGHT'}, [False, False]),
])
def test_blocked_source_policy_does_not_disable_the_independent_alternative(blocked, expected):
    native = policy()
    resolver = SimpleNamespace(grant=lambda key, permitted: (
        Grant(frozenset()) if key in blocked else native.grant(key, permitted)))
    assert rules.target_applies(target_row(), resolver) is any(expected)
    owned = frozenset({'Spark Ability', 'Sword Ability'})
    assert [rules.graph_succeeds(graph, resolver, owned, True, retries=True)
            for graph in rules.target_graphs(target_row(), False)] == expected


@pytest.mark.parametrize('ability', ABILITY_NAME_TO_ID)
def test_underwater_sword_is_not_dry_spark_or_a_global_provider(ability):
    result = reachable_positions(
        (Node('a', 110), Node('b', 110)),
        (Route('a', 'b', SWORD, water_state='swimming'),), (),
        (Position('a', ability),), policy())
    assert result.reaches('b') is (ability == 'Sword')


@pytest.mark.parametrize('capability,medium,source_room,target_room', [
    (SWORD, 'dry', 110, 110), (SWORD, 'swimming', 138, 110),
    (SWORD, 'swimming', 110, 138), (TARGET, 'swimming', 110, 110),
    (TARGET, 'dry', 138, 110), (TARGET, 'dry', 110, 138),
])
def test_target_medium_and_native_room_are_validated(capability, medium, source_room, target_room):
    with pytest.raises(ValueError, match='native room'):
        reachable_positions((Node('a', source_room), Node('b', target_room)),
                            (Route('a', 'b', capability, water_state=medium),), (),
                            (Position('a', 'Sword'),), policy())


def test_sword_carry_marks_media_and_retains_equipment_to_exact_exit():
    graph = room_traversal_graph(TARGET, 'upper_entry_sword')
    assert [route.water_state for route in graph.routes] == [
        'dry', 'dry', 'swimming', 'dry', 'swimming', 'swimming', 'dry', 'swimming']
    attacks = [route for route in graph.routes if route.capability]
    assert len(attacks) == 1 and attacks[0].capability == SWORD
    assert attacks[0].water_state == 'swimming'
    result = graph.evaluate(policy(), frozenset({'Sword Ability'}), True)
    assert any(position.node in graph.required_targets and position.equipped == 'Sword'
               for position in result.positions)
    spark = room_traversal_graph(TARGET, 'upper_entry')
    assert spark.routes[-1].capability == TARGET and spark.routes[-1].water_state == 'dry'


@pytest.mark.parametrize('condition', [
    None, {}, [], 'SPARKY',
    [{'source_key': 'SPARKY', 'ability': 'Spark'}],
    [{'source_key': 'SPARKY', 'ability': 'Sword'}, {'source_key': 'SWORD_KNIGHT', 'ability': 'Spark'}],
    [{'source_key': 'SPARKY', 'ability': 'Spark'}, {'source_key': 'UNKNOWN', 'ability': 'Sword'}],
    [{'source_key': 'SPARKY', 'ability': 'Spark'}, {'source_key': 'SWORD_KNIGHT', 'abilities': ['Sword']}],
])
def test_malformed_or_conditions_are_rejected(condition):
    row = deepcopy(target_row())
    row['requires_any_guaranteed_source'] = condition
    with pytest.raises(ValueError, match='guaranteed-source alternatives'):
        load_room_traversal({OWNER: {'traversal': {'version': 1, 'targets': [row]}}})


@pytest.mark.parametrize('update', [
    {'id': 'other'}, {'kind': 'switch'}, {'native_room': 138},
    {'exit': UPSTREAM}, {'region': 'REGION_RAINBOW_ROUTE/ROOM_1_28'},
    {'requires_guaranteed_source': None},
    {'requires_guaranteed_source': {'source_key': 'SPARKY', 'ability': 'Spark'}},
])
def test_source_or_is_target_specific_and_exclusive_with_legacy_condition(update):
    row = deepcopy(target_row())
    row.update(update)
    owner = row.pop('region')
    with pytest.raises(ValueError, match='guaranteed-source alternatives|mutually exclusive'):
        load_room_traversal({owner: {'traversal': {'version': 1, 'targets': [row]}}})


@pytest.mark.parametrize('gating', [0, 1])
@pytest.mark.parametrize('area_keys', [0, 1])
@pytest.mark.parametrize('room_sanity', [0, 1])
def test_actual_world_either_permission_opens_only_the_same_room9_exit(gating, area_keys, room_sanity):
    world = make_world(0, gating, area_keys=area_keys, room_sanity=room_sanity)
    state = CollectionState(world.multiworld)
    target = world.multiworld.get_entrance(f'{OWNER} -> {EXIT}', 1)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    for ability in ('Spark', 'Sword'):
        assert target.access_rule(state) is (not gating)
        item = world.create_item(f'{ability} Ability')
        state.collect(item, prevent_sweep=True)
        assert target.access_rule(state)  # OR, never a second add_rule AND.
        state.can_reach_region = lambda name, player: name == OWNER
        assert not target.access_rule(state)
        state.remove(item)
        state.can_reach_region = lambda name, player: name == UPSTREAM
    for destination in (UPSTREAM, 'REGION_RAINBOW_ROUTE/ROOM_1_12'):
        assert world.multiworld.get_entrance(f'{OWNER} -> {destination}', 1).access_rule(state)
    for location in world.multiworld.get_region(OWNER, 1).locations:
        assert location.access_rule(state)
    area = world.multiworld.get_entrance(
        'REGION_RAINBOW_ROUTE/ROOM_1_13_LOWER -> REGION_CABBAGE_CAVERN/ROOM_3_04', 1)
    assert area.access_rule(state) is (not area_keys)
    state.collect(world.create_item('Cabbage Cavern - Area Key'), prevent_sweep=True)
    assert area.access_rule(state)


@pytest.mark.parametrize('mode,seed,gating,area_keys,statues', [
    (0, 110, 0, 0, 0), (0, 110, 1, 1, 1),
    (1, 30, 0, 0, 0), (1, 30, 1, 1, 0),
    (1, 17, 0, 0, 1), (1, 17, 1, 1, 1),
])
def test_real_fill_full_accessibility_at_one_hp(mode, seed, gating, area_keys, statues):
    multiworld = setup_multiworld(KirbyAmWorld, seed=seed, options={
        'ability_randomization_mode': mode, 'ability_gating': gating, 'area_keys': area_keys,
        'ability_randomization_statues': statues, 'minimum_health': 1, 'maximum_health': 1,
        'accessibility': 'full',
    })
    world = multiworld.worlds[1]
    resolver = SourcePolicy(world._enemy_copy_ability_policy, bool(statues))
    assert rules.target_applies(target_row(), resolver)
    assert resolver.grant('SWORD_KNIGHT', lambda _: True).guaranteed == frozenset({'Sword'})
    assert len(resolver.policy['allowed_abilities']) == 25
    if mode == 1:
        assert resolver.grant('SPARKY', lambda _: True).guaranteed != frozenset({'Spark'})
    distribute_items_restrictive(multiworld)
    call_all(multiworld, 'post_fill')
    assert not multiworld.get_unfilled_locations()
    assert multiworld.can_beat_game()
    assert multiworld.fulfills_accessibility()
