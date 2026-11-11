"""Only proved source-policy and entry-side subsets install bounded bomb gates."""

from dataclasses import replace
from types import SimpleNamespace

import pytest
from BaseClasses import CollectionState, ItemClassification
from Options import Accessibility

from .. import KirbyAmWorld
from .. import traversal_rules as rules
from ..traversal_data import room_traversal_graph, room_traversal_targets
from .test_mini_traversal import make_world
from .test_traversal import policy

OWNER = 'REGION_RAINBOW_ROUTE/ROOM_1_08'
UPSTREAM = 'REGION_RAINBOW_ROUTE/ROOM_1_06_LOWER_MID'
EXIT = 'REGION_RAINBOW_ROUTE/ROOM_1_09'


@pytest.mark.parametrize('mode,pool,weight,applies', [
    (0, None, 0, True), (1, ['Spark'], 0, True), (1, ['Beam'], 0, False),
    (2, ['Spark'], 0, True), (2, ['Spark', 'Beam'], 0, False),
    (2, ['Spark'], 50, False), (2, ['Spark'], 100, False),
])
@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('area_keys', [False, True])
@pytest.mark.parametrize('statues', [False, True])
def test_rainbow_conditional_policy_entry_and_permission_matrix(
        monkeypatch, mode, pool, weight, applies, gating, area_keys, statues):
    resolver = policy(mode, pool=pool, weight=weight, statues=statues)
    row = next(r for r in room_traversal_targets('block') if r['id'] == 'bomb_110_room9')
    monkeypatch.setattr(rules, 'extra_traversal_targets', lambda: (row,))
    assert rules.target_applies(row, resolver) is applies
    assert rules.static_extra_witness(resolver)
    target = SimpleNamespace(access_rule=lambda state: state.base_rule)
    dependencies = []

    def absent_location(name, player):
        # This isolated Rainbow fixture has no Chocolate chest to promote Spark.
        raise KeyError(name)

    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy=resolver.policy,
        _ability_gating_enabled=lambda: gating, _area_keys_enabled=lambda: area_keys,
        options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=statues),
                                accessibility=Accessibility(Accessibility.option_full)),
        multiworld=SimpleNamespace(
            get_entrance=lambda name, player: target,
            get_region=lambda name, player: name,
            get_location=absent_location,
            register_indirect_condition=lambda region, entrance: dependencies.append(region),
        ),
        item_id_to_name=KirbyAmWorld.item_id_to_name,
    )
    rules.install_extra_traversal_rules(world)
    owned = set()
    state = SimpleNamespace(base_rule=True, upstream=False)
    state.has = lambda item, player: item in owned
    # Generic owner access cannot bootstrap the upper source path.
    state.can_reach_region = lambda name, player: name == OWNER or (name == UPSTREAM and state.upstream)
    assert target.access_rule(state) is (not applies)
    owned.add('Spark Ability')
    assert target.access_rule(state) is (not applies)
    state.upstream = True
    assert target.access_rule(state)
    owned.clear()
    assert target.access_rule(state) is (not applies or not gating)
    state.base_rule = False
    assert not target.access_rule(state)
    assert dependencies == ([UPSTREAM] if applies else [])
    code = KirbyAmWorld.item_name_to_id['Spark Ability']
    item = KirbyAmWorld.create_item_by_code(world, code)
    assert item.classification == (ItemClassification.progression if applies and gating else ItemClassification.useful)


def test_rainbow_graph_has_real_finite_source_and_no_equipped_start():
    graph = room_traversal_graph('bomb_110_room9', 'upper_entry')
    assert graph.access_region == UPSTREAM
    assert all(start.equipped == 'Normal' for start in graph.starts)
    source, = graph.placements
    assert (source.identity, source.source_key, source.renewable) == ('0x088B743C', 'SPARKY', False)
    assert not source.retry_evidence
    target, = graph.required_targets
    assert not graph.evaluate(policy(), frozenset(), True).reaches(target)
    assert graph.evaluate(policy(), frozenset({'Spark Ability'}), True).reaches(target)
    assert not replace(graph, placements=()).evaluate(policy(), frozenset({'Spark Ability'}), True).reaches(target)


@pytest.mark.parametrize('gating', [0, 1])
@pytest.mark.parametrize('area_keys', [0, 1])
@pytest.mark.parametrize('room_sanity', [0, 1])
def test_actual_world_wires_only_room9_edge_and_collects_spark(gating, area_keys, room_sanity):
    world = make_world(0, gating, area_keys=area_keys, room_sanity=room_sanity)
    state = CollectionState(world.multiworld)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    target = world.multiworld.get_entrance(f'{OWNER} -> {EXIT}', 1)
    assert target.access_rule(state) is (not gating)
    item = world.create_item('Spark Ability')
    state.collect(item, prevent_sweep=True)
    assert state.has('Spark Ability', 1) is bool(gating)
    assert target.access_rule(state)
    state.can_reach_region = lambda name, player: name == OWNER
    assert not target.access_rule(state)
    for destination in (UPSTREAM, 'REGION_RAINBOW_ROUTE/ROOM_1_12'):
        assert world.multiworld.get_entrance(f'{OWNER} -> {destination}', 1).access_rule(state)
    # No room-level rule or source-dependent RoomSanity gate is introduced.
    for location in world.multiworld.get_region(OWNER, 1).locations:
        assert location.access_rule(state)


@pytest.mark.parametrize('mode,pool,weight,applies', [
    (0, None, 0, True), (1, ['Beam'], 0, True), (1, ['Spark'], 0, True), (1, ['Ice'], 0, True),
    (1, ['Sword'], 0, True), (2, ['Sword'], 0, True),
    (2, ['Beam'], 0, True), (2, ['Beam', 'Spark'], 0, False),
    (2, ['Beam'], 50, False), (2, ['Beam'], 100, False),
])
@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('enabled', [False, True])
@pytest.mark.parametrize('area_keys', [False, True])
@pytest.mark.parametrize('statues', [False, True])
def test_cabbage_conditional_policy_category_and_entry_matrix(
        monkeypatch, mode, pool, weight, applies, gating, enabled, area_keys, statues):
    resolver = policy(mode, pool=pool, weight=weight, statues=statues)
    row = next(r for r in room_traversal_targets('block') if r['id'] == 'bomb_517_chocolate')
    monkeypatch.setattr(rules, 'extra_traversal_targets', lambda: (row,))
    assert rules.target_applies(row, resolver) is applies
    assert rules.static_extra_witness(resolver)
    target = SimpleNamespace(access_rule=lambda state: state.base_rule)

    def get_location(name, player):
        if not enabled:
            raise KeyError('disabled chest category')
        return target

    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy=resolver.policy,
        _ability_gating_enabled=lambda: gating, _area_keys_enabled=lambda: area_keys,
        options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=statues),
                                accessibility=Accessibility(Accessibility.option_full)),
        multiworld=SimpleNamespace(get_location=get_location),
        item_id_to_name=KirbyAmWorld.item_id_to_name,
    )
    rules.install_extra_traversal_rules(world)
    owned = set()
    state = SimpleNamespace(base_rule=True, upstream=False, has=lambda item, player: item in owned)
    state.can_reach_region = lambda name, player: name == 'REGION_CABBAGE_CAVERN/ROOM_3_06' or (
        name == 'REGION_CABBAGE_CAVERN/ROOM_3_HUB_2' and state.upstream)
    assert target.access_rule(state) is (not (applies and enabled))
    state.upstream = True
    assignment = resolver.grant('WADDLE_DOO', lambda _: True).guaranteed
    needs_permission = enabled and applies and gating and bool(assignment & {'Spark', 'Ice', 'Sword'})
    assert target.access_rule(state) is (not needs_permission)
    if needs_permission:
        # The independent entry is necessary but not a substitute for permission.
        owned.add('Missile Ability')
        assert not target.access_rule(state)
        ability, = assignment
        owned.add(f'{ability} Ability')
        assert target.access_rule(state)
    state.base_rule = False
    assert not target.access_rule(state)
    item = KirbyAmWorld.create_item_by_code(world, KirbyAmWorld.item_name_to_id['Beam Ability'])
    assert item.classification == ItemClassification.useful


def test_cabbage_complete_carry_does_not_inherit_other_target_providers():
    graph = room_traversal_graph('bomb_517_chocolate', 'hub2_entry')
    assert graph.access_region == 'REGION_CABBAGE_CAVERN/ROOM_3_HUB_2'
    assert all(start.equipped == 'Normal' for start in graph.starts)
    source, = graph.placements
    assert (source.identity, source.source_key, source.renewable) == ('0x088CA04C', 'WADDLE_DOO', False)
    assert graph.routes[-1].allowed_abilities == frozenset({'Beam'})
    target, = graph.required_targets
    assert graph.evaluate(policy(), frozenset(), True).reaches(target)
    for ability in ('Spark', 'Ice', 'Smash'):
        assert not graph.evaluate(policy(1, pool=[ability]), frozenset({f'{ability} Ability'}), True).reaches(target)
    assert not replace(graph, placements=()).evaluate(policy(), frozenset({'Beam Ability'}), True).reaches(target)


@pytest.mark.parametrize('mode,pool,weight,applies', [
    (0, None, 0, True), (1, ['Beam'], 0, True), (1, ['Spark'], 0, False),
    (2, ['Beam'], 0, True), (2, ['Beam', 'Spark'], 0, False),
    (2, ['Beam'], 50, False), (2, ['Beam'], 100, False),
])
@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('area_keys', [False, True])
@pytest.mark.parametrize('statues', [False, True])
def test_carrot_conditional_policy_entry_matrix(
        monkeypatch, mode, pool, weight, applies, gating, area_keys, statues):
    resolver = policy(mode, pool=pool, weight=weight, statues=statues)
    row = next(r for r in room_traversal_targets('block') if r['id'] == 'bomb_719_room13')
    monkeypatch.setattr(rules, 'extra_traversal_targets', lambda: (row,))
    assert rules.target_applies(row, resolver) is applies
    assert rules.static_extra_witness(resolver)
    target = SimpleNamespace(access_rule=lambda state: state.base_rule)
    looked_up = []
    dependencies = []

    def get_entrance(name, player):
        looked_up.append(name)
        return target

    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy=resolver.policy,
        _ability_gating_enabled=lambda: gating, _area_keys_enabled=lambda: area_keys,
        options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=statues),
                                accessibility=Accessibility(Accessibility.option_full)),
        multiworld=SimpleNamespace(
            get_entrance=get_entrance, get_region=lambda name, player: name,
            register_indirect_condition=lambda region, entrance: dependencies.append(region)),
    )
    rules.install_extra_traversal_rules(world)
    state = SimpleNamespace(base_rule=True, upstream=False, has=lambda item, player: False)
    state.can_reach_region = lambda name, player: name == 'REGION_CARROT_CASTLE/ROOM_5_07' or (
        name == 'REGION_CARROT_CASTLE/ROOM_5_05' and state.upstream)
    assert target.access_rule(state) is (not applies)
    state.upstream = True
    assert target.access_rule(state)
    state.base_rule = False
    assert not target.access_rule(state)
    assert looked_up == ([
        'REGION_CARROT_CASTLE/ROOM_5_07 -> REGION_CARROT_CASTLE/ROOM_5_13__LOGIC__ENTRY_FROM_5_07'
    ] if applies else [])
    assert dependencies == (['REGION_CARROT_CASTLE/ROOM_5_05'] if applies else [])


@pytest.mark.parametrize('room_sanity', [0, 1])
@pytest.mark.parametrize('minor_chests', [False, True])
def test_carrot_actual_logical_entrance_keeps_other_exits_and_notes_separate(monkeypatch, room_sanity, minor_chests):
    monkeypatch.setattr(KirbyAmWorld, 'ENABLE_MINOR_CHESTS', minor_chests)
    world = make_world(0, 1, room_sanity=room_sanity)
    state = CollectionState(world.multiworld)
    base = 'REGION_CARROT_CASTLE/ROOM_5_07'
    lower = 'REGION_CARROT_CASTLE/ROOM_5_13__LOGIC__ENTRY_FROM_5_07'
    target = world.multiworld.get_entrance(f'{base} -> {lower}', 1)
    state.can_reach_region = lambda name, player: name == base
    assert not target.access_rule(state)
    state.can_reach_region = lambda name, player: name == 'REGION_CARROT_CASTLE/ROOM_5_05'
    assert target.access_rule(state)
    for destination in ('ROOM_5_08', 'ROOM_5_14'):
        assert world.multiworld.get_entrance(f'{base} -> REGION_CARROT_CASTLE/{destination}', 1).access_rule(state)
    for location in world.multiworld.get_region(base, 1).locations:
        assert location.access_rule(state)
    # The other incoming Room14 compartment is not this Beam-gated entrance.
    room14 = world.multiworld.get_region('REGION_CARROT_CASTLE/ROOM_5_14', 1)
    notes_routes = [e for e in room14.exits if 'ROOM_5_13' in e.name]
    assert len(notes_routes) == 1 and notes_routes[0].connected_region.name != lower
    assert notes_routes[0].access_rule(state)


def test_carrot_source_is_lower_native_instance_not_inventory_or_upper_doo():
    graph = room_traversal_graph('bomb_719_room13', 'room5_entry')
    source, = graph.placements
    assert source.identity == '0x088D3BF4' and source.source_key == 'WADDLE_DOO'
    assert not source.renewable and not source.retry_evidence
    assert all(start.equipped == 'Normal' for start in graph.starts)
    target, = graph.required_targets
    assert graph.evaluate(policy(), frozenset(), True).reaches(target)
    assert not replace(graph, placements=()).evaluate(policy(), frozenset({'Beam Ability'}), True).reaches(target)
