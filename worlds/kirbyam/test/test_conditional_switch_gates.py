"""Only proved source-policy and entry-side subsets install bounded switch gates."""

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

OWNER = 'REGION_MUSTARD_MOUNTAIN/ROOM_4_15'
UPSTREAM = 'REGION_RAINBOW_ROUTE/ROOM_1_HUB_4'
EXIT = 'REGION_MUSTARD_MOUNTAIN/ROOM_4_16'


@pytest.mark.parametrize('mode,pool,weight,applies', [
    (0, None, 0, True), (1, ['Bomb'], 0, True), (1, ['Beam'], 0, False),
    (2, ['Bomb'], 0, True), (2, ['Bomb', 'Beam'], 0, False),
    (2, ['Bomb'], 50, False), (2, ['Bomb'], 100, False),
    (1, ['UFO'], 0, True), (2, ['UFO'], 0, True),
    (2, ['UFO'], 50, False), (2, ['Bomb', 'UFO'], 0, False),
    (1, ['Crash'], 0, True), (2, ['Crash'], 0, True),
    (2, ['Crash'], 50, False), (2, ['Crash'], 100, False),
    (2, ['Crash', 'Bomb'], 0, False),
    (1, ['Magic'], 0, True), (2, ['Magic'], 0, True),
    (2, ['Magic'], 50, False), (2, ['Magic'], 100, False),
    (2, ['Magic', 'Bomb'], 0, False),
])
@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('area_keys', [False, True])
@pytest.mark.parametrize('statues', [False, True])
@pytest.mark.parametrize('advanced', [False, True])
def test_mustard_conditional_policy_entry_and_permission_matrix(
        monkeypatch, mode, pool, weight, applies, gating, area_keys, statues, advanced):
    resolver = policy(mode, pool=pool, weight=weight, statues=statues)
    row = next(r for r in room_traversal_targets('switch') if r['id'] == 'switch_533_room16')
    monkeypatch.setattr(rules, 'extra_traversal_targets', lambda: (row,))
    assert rules.target_applies(row, resolver) is applies
    blocked_advanced = applies and pool in (["Crash"], ["Magic"]) and not advanced
    assert rules.static_extra_witness(resolver, advanced=advanced)  # Optional progression exit.
    target = SimpleNamespace(access_rule=lambda state: state.base_rule)
    dependencies = []
    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy=resolver.policy,
        _ability_gating_enabled=lambda: gating, _area_keys_enabled=lambda: area_keys,
        options=SimpleNamespace(advanced_logic=SimpleNamespace(value=int(advanced)), ability_randomization_statues=SimpleNamespace(value=statues),
                                accessibility=Accessibility(Accessibility.option_full)),
        multiworld=SimpleNamespace(
            get_entrance=lambda name, player: target,
            get_region=lambda name, player: name,
            register_indirect_condition=lambda region, entrance: dependencies.append(region),
        ),
        item_id_to_name=KirbyAmWorld.item_id_to_name,
    )
    rules.install_extra_traversal_rules(world)
    qualified = applies and not blocked_advanced
    ability = next(iter(resolver.grant('FOLEY', lambda _: True).guaranteed)) if applies else 'Bomb'
    owned = set()
    state = SimpleNamespace(base_rule=True, upstream=False)
    state.has = lambda item, player: item in owned
    # Generic owner access cannot bootstrap the Hub4 approach.
    state.can_reach_region = lambda name, player: name == OWNER or (name == UPSTREAM and state.upstream)
    assert not target.access_rule(state)
    owned.add(f'{ability} Ability')
    assert not target.access_rule(state)
    state.upstream = True
    assert target.access_rule(state) is qualified
    owned.clear()
    assert target.access_rule(state) is (qualified and not gating)
    state.base_rule = False
    assert not target.access_rule(state)
    assert dependencies == ([UPSTREAM] if applies else [])
    code = KirbyAmWorld.item_name_to_id[f'{ability} Ability']
    item = KirbyAmWorld.create_item_by_code(world, code)
    assert item.classification == (ItemClassification.useful if (ability in {"Crash", "Magic"} and not gating) or (ability in {"Crash", "Magic"} and not advanced)
                                   else ItemClassification.progression)


def test_mustard_graph_has_real_finite_source_and_no_equipped_start():
    graph = room_traversal_graph('switch_533_room16', 'hub4_entry')
    assert graph.access_region == UPSTREAM
    assert all(start.equipped == 'Normal' for start in graph.starts)
    source, = graph.placements
    assert (source.identity, source.source_key, source.renewable) == ('0x088C2714', 'FOLEY', False)
    assert not source.retry_evidence
    target, = graph.required_targets
    assert not graph.evaluate(policy(), frozenset(), True).reaches(target)
    assert graph.evaluate(policy(), frozenset({'Bomb Ability'}), True).reaches(target)
    assert not replace(graph, placements=()).evaluate(policy(), frozenset({'Bomb Ability'}), True).reaches(target)


@pytest.mark.parametrize('gating', [0, 1])
@pytest.mark.parametrize('area_keys', [0, 1])
@pytest.mark.parametrize('room_sanity', [0, 1])
def test_actual_world_wires_only_room16_edge_and_collects_bomb(gating, area_keys, room_sanity):
    world = make_world(0, gating, area_keys=area_keys, room_sanity=room_sanity)
    state = CollectionState(world.multiworld)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    target = world.multiworld.get_entrance(f'{OWNER} -> {EXIT}', 1)
    assert target.access_rule(state) is (not gating)
    item = world.create_item('Bomb Ability')
    state.collect(item, prevent_sweep=True)
    assert state.has('Bomb Ability', 1)  # Bomb is always progression, including gating off.
    assert target.access_rule(state)
    state.can_reach_region = lambda name, player: name == OWNER
    assert not target.access_rule(state)
    for destination in ('REGION_RAINBOW_ROUTE/ROOM_1_34', 'REGION_MUSTARD_MOUNTAIN/ROOM_4_17'):
        assert world.multiworld.get_entrance(f'{OWNER} -> {destination}', 1).access_rule(state)
    # No room-level rule or source-dependent RoomSanity gate is introduced.
    for location in world.multiworld.get_region(OWNER, 1).locations:
        assert location.access_rule(state)


def test_ufo_graph_uses_real_source_and_top_charge_not_bomb_equivalence():
    graph = room_traversal_graph('switch_533_room16', 'hub4_ufo_entry')
    source, = graph.placements
    assert (source.identity, source.source_key, source.renewable) == ('0x088C2714', 'FOLEY', False)
    assert all(start.equipped == 'Normal' for start in graph.starts)
    target, = graph.required_targets
    resolver = policy(1, pool=['UFO'])
    assert not graph.evaluate(resolver, frozenset({'Bomb Ability'}), True).reaches(target)
    assert graph.evaluate(resolver, frozenset({'UFO Ability'}), True).reaches(target)
    assert not replace(graph, placements=()).evaluate(resolver, frozenset({'UFO Ability'}), True).reaches(target)
    assert not graph.evaluate(policy(), frozenset({'Bomb Ability', 'UFO Ability'}), True).reaches(target)
    assert [r.capability for r in graph.routes if r.capability] == ['switch_533_ufo_top_charge']


@pytest.mark.parametrize('accessibility', [Accessibility.option_full, Accessibility.option_minimal])
@pytest.mark.parametrize('room_sanity', [0, 1])
@pytest.mark.parametrize('gating', [0, 1])
@pytest.mark.parametrize('mode,pool,weight', [
    (1, ['Beam'], 0), (2, ['Bomb', 'Beam'], 0), (2, ['Bomb'], 50),
])
def test_unqualified_room16_exit_stays_closed_in_real_world(
        monkeypatch, accessibility, room_sanity, gating, mode, pool, weight):
    # Start with a normally built world; replace just the source policy to exercise
    # the installed production rule without unrelated randomized-source searches.
    world = make_world(0, gating, accessibility=accessibility, room_sanity=room_sanity)
    resolver = policy(mode, pool=pool, weight=weight)
    world._enemy_copy_ability_policy = resolver.policy
    row = next(r for r in room_traversal_targets('switch') if r['id'] == 'switch_533_room16')
    monkeypatch.setattr(rules, 'extra_traversal_targets', lambda: (row,))
    target = world.multiworld.get_entrance(f'{OWNER} -> {EXIT}', 1)
    target.access_rule = lambda state: True
    rules.install_extra_traversal_rules(world)
    state = CollectionState(world.multiworld)
    state.can_reach_region = lambda name, player: True
    for ability in ('Bomb', 'UFO', 'Crash', 'Magic'):
        state.collect(world.create_item(f'{ability} Ability'), prevent_sweep=True)
    assert not target.access_rule(state)  # Permission cannot manufacture equipment.
    bypass = world.multiworld.get_entrance(f'{OWNER} -> REGION_MUSTARD_MOUNTAIN/ROOM_4_17', 1)
    assert bypass.access_rule(state)
    assert world.multiworld.get_entrance(
        'REGION_MUSTARD_MOUNTAIN/ROOM_4_17 -> REGION_MUSTARD_MOUNTAIN/ROOM_4_18', 1
    ).access_rule(state)
    assert bool(world.multiworld.get_region(EXIT, 1).locations) is bool(room_sanity)


def test_room16_missing_source_policy_fails_closed(monkeypatch):
    row = next(r for r in room_traversal_targets('switch') if r['id'] == 'switch_533_room16')
    monkeypatch.setattr(rules, 'extra_traversal_targets', lambda: (row,))
    target = SimpleNamespace(access_rule=lambda state: True)
    world = SimpleNamespace(player=1, multiworld=SimpleNamespace(get_entrance=lambda *args: target))
    rules.install_extra_traversal_rules(world)
    assert not target.access_rule(SimpleNamespace())


@pytest.mark.parametrize('accessibility', [Accessibility.option_full, Accessibility.option_minimal])
def test_room16_enabled_check_is_rejected_by_final_output_guard(monkeypatch, accessibility):
    from ..check_accessibility import KirbyAmCheckAccessibilityError, validate_all_checks

    world = make_world(0, 1, accessibility=accessibility, room_sanity=1)
    world._enemy_copy_ability_policy = policy(1, pool=['Beam']).policy
    row = next(r for r in room_traversal_targets('switch') if r['id'] == 'switch_533_room16')
    monkeypatch.setattr(rules, 'extra_traversal_targets', lambda: (row,))
    target = world.multiworld.get_entrance(f'{OWNER} -> {EXIT}', 1)
    target.access_rule = lambda state: True
    rules.install_extra_traversal_rules(world)
    locations = world.multiworld.get_region(EXIT, 1).locations
    assert len(locations) == 1
    locations[0].place_locked_item(world.create_item('Bomb Ability'))
    # Isolate this enabled physical check; leave the actual production reachability
    # and final-output validator intact, without assuming all inventory is reachable.
    monkeypatch.setattr(world.multiworld, 'get_locations', lambda player=None: locations)
    with pytest.raises(KirbyAmCheckAccessibilityError, match='including with minimal accessibility'):
        validate_all_checks(world.multiworld, (1,))
