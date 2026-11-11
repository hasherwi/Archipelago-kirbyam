"""Only the complete, guaranteed-Twister UFO carry gates the native310 map."""

from dataclasses import replace
from types import SimpleNamespace

import pytest
from BaseClasses import CollectionState, ItemClassification
from Options import Accessibility

from .support.source_policy import set_rule_test_policy
from .. import traversal_rules as rules
from ..data import data
from ..traversal_data import room_traversal_graph, room_traversal_targets
from .test_mini_traversal import make_world
from .test_traversal import policy

TARGET = 'switch_310_mustard_map'
OWNER = 'REGION_MUSTARD_MOUNTAIN/ROOM_4_CHEST'
UPSTREAM = 'REGION_RAINBOW_ROUTE/ROOM_1_HUB_4'
SOURCE_ROOM = 'REGION_RAINBOW_ROUTE/ROOM_1_34'
LOCATION = 'MAJOR_CHEST_MUSTARD_MOUNTAIN'
POLICIES = [
    (0, None, 0, False),  # Native Twister is Tornado, not UFO.
    (1, ['UFO'], 0, True), (1, ['Bomb'], 0, False),
    (2, ['UFO'], 0, True), (2, ['UFO', 'Bomb'], 0, False),
    (2, ['UFO'], 50, False), (2, ['UFO'], 100, False),
]


def target_row():
    return next(row for row in room_traversal_targets('switch') if row['id'] == TARGET)


@pytest.mark.parametrize('mode,pool,weight,applies', POLICIES)
@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('area_keys', [False, True])
@pytest.mark.parametrize('statues', [False, True])
def test_map_conditional_policy_and_independent_entry_matrix(
        monkeypatch, mode, pool, weight, applies, gating, area_keys, statues):
    resolver = policy(mode, pool=pool, weight=weight, statues=statues, minny=False)
    row = target_row()
    monkeypatch.setattr(rules, 'extra_traversal_targets', lambda: (row,))
    assert rules.target_applies(row, resolver) is applies
    assert rules.static_extra_witness(resolver)

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
    state = SimpleNamespace(base_rule=True, has=lambda item, player: item in owned)
    # Reaching either the target room or the source room does not prove this approach.
    state.can_reach_region = lambda name, player: name in {OWNER, SOURCE_ROOM}
    assert target.access_rule(state) is (not applies)
    owned.add('UFO Ability')
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
def test_actual_world_wires_only_map_and_preserves_ufo_progression(
        monkeypatch, mode, pool, weight, applies, gating, area_keys, statues, room_sanity):
    resolver = policy(mode, pool=pool, weight=weight, statues=statues, minny=False)
    # A controlled production policy exercises the real generate/create/set-rules
    # lifecycle. Minimal accessibility keeps unrelated finite-source gates from
    # rejecting these deliberately restricted assignment pools.
    set_rule_test_policy(monkeypatch, lambda *args, **kwargs: resolver.policy)
    world = make_world(mode, gating, accessibility='minimal', area_keys=area_keys,
                       ability_randomization_statues=statues, room_sanity=room_sanity,
                       ability_randomization_no_ability_weight=weight)
    target = world.multiworld.get_location(data.locations[LOCATION].label, 1)
    assert target.parent_region.name == OWNER
    state = CollectionState(world.multiworld)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    incoming = world.multiworld.get_entrance(f'{SOURCE_ROOM} -> {OWNER}', 1)
    assert incoming.access_rule(state) is (not area_keys)
    state.collect(world.create_item('Mustard Mountain - Area Key'), prevent_sweep=True)
    assert incoming.access_rule(state)
    assert target.access_rule(state) is (not applies or not gating)
    item = world.create_item('UFO Ability')
    assert item.classification == ItemClassification.progression
    state.collect(item, prevent_sweep=True)
    assert state.has('UFO Ability', 1)
    assert target.access_rule(state)
    for accessible in (OWNER, SOURCE_ROOM):
        state.can_reach_region = lambda name, player, accessible=accessible: name == accessible
        assert target.access_rule(state) is (not applies)
        assert world.multiworld.get_entrance(f'{OWNER} -> {SOURCE_ROOM}', 1).access_rule(state)
        assert world.multiworld.get_entrance(f'{SOURCE_ROOM} -> {OWNER}', 1).access_rule(state)
        # RoomSanity is normalized into its own sink, never this chest rule.
        owner = world.multiworld.get_region(OWNER, 1)
        room_checks = [location for location in world.multiworld.get_locations(1)
                       if location.parent_region.name.startswith(OWNER) and location is not target]
        assert len(room_checks) == room_sanity
        assert all(location.access_rule(state) for location in room_checks)
        assert all(exit.access_rule(state) for exit in owner.exits)


@pytest.mark.parametrize('area_keys', [False, True])
@pytest.mark.parametrize('gating', [False, True])
def test_map_graph_requires_finite_source_and_carries_equipment(area_keys, gating):
    row = target_row()
    assert row['region'] == OWNER and row['location'] == LOCATION and not row.get('exit')
    graph = room_traversal_graph(TARGET, 'hub4_ufo_entry', area_keys)
    assert graph.access_region == UPSTREAM
    assert len(graph.starts) == 1 and graph.starts[0].equipped == 'Normal'
    native_rooms = {node.key: node.room for node in graph.nodes}
    assert native_rooms[graph.starts[0].node] == 590
    source, = graph.placements
    assert native_rooms[source.node] == 534
    assert (source.identity, source.source_key, source.renewable) == ('0x088B59B4', 'TWISTER', False)
    assert not source.retry_evidence
    assert [(native_rooms[route.source], native_rooms[route.target]) for route in graph.routes
            if route.room_transition] == [(590, 534), (534, 310)]
    assert [route.capability for route in graph.routes if route.capability] == ['switch_310_ufo_top_charge']
    assert all(route.opens is None for route in graph.routes)
    resolver = policy(1, pool=['UFO'], minny=False)
    owned = frozenset({'UFO Ability'})
    target, = graph.required_targets
    result = graph.evaluate(resolver, owned, gating)
    assert result.reaches(target)
    assert any(position.node == target and position.equipped == 'UFO' for position in result.positions)
    assert not result.retry_assumptions
    assert graph.evaluate(resolver, frozenset(), gating).reaches(target) is (not gating)
    assert not replace(graph, placements=()).evaluate(resolver, owned, gating).reaches(target)
    # Inventory cannot replace the acquisition leg, even with the real placement retained.
    without_acquisition = replace(graph, routes=tuple(route for route in graph.routes if route.target != source.node))
    assert not without_acquisition.evaluate(resolver, owned, gating).reaches(target)
    assert not graph.evaluate(policy(), owned, gating).reaches(target)
    bomb_result = graph.evaluate(policy(1, pool=['Bomb']), frozenset({'UFO Ability', 'Bomb Ability'}), gating)
    assert not bomb_result.reaches(target)


@pytest.mark.parametrize('pool,weight', [(['UFO', 'Bomb'], 0), (['UFO'], 50), (['UFO'], 100)])
@pytest.mark.parametrize('retries', [False, True])
def test_map_finite_random_source_has_no_retry_or_selected_outcome(pool, weight, retries):
    graph = room_traversal_graph(TARGET, 'hub4_ufo_entry')
    target, = graph.required_targets
    result = graph.evaluate(policy(2, pool=pool, weight=weight), frozenset({'UFO Ability', 'Bomb Ability'}),
                            True, allow_documented_retries=retries)
    assert not result.reaches(target)
    assert not result.retry_assumptions
