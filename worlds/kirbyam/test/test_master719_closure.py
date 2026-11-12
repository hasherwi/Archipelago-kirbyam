"""Real CollectionState closure with production event, goals and719 OR rule.

Topology isolation is synthetic test setup, never a native acceptance claim.
No Generate, fill search, archive or emulator is used by this module.
"""

from argparse import Namespace
from dataclasses import dataclass
from collections.abc import Callable
from typing import cast

import pytest
from BaseClasses import CollectionState, Entrance, MultiWorld, Region
from Fill import FillError

from .. import KirbyAmWorld
from ..area_keys import dimension_mirror_entrance_names
from ..check_accessibility import KirbyAmCheckAccessibilityError, validate_all_checks
from ..locations import KirbyAmLocation
from ..master_source import CARROT_HUB, CARROT_KEY, CENTRAL_REGION, CENTRAL_RETURN_EVENT, RAINBOW_WEST_HUB
from ..rules import (
    _BOSS_DEFEAT_LOCATION_LABELS, _DMK_DIMENSION_MIRROR_EVENT, _GOAL_LOCATION_LABELS, _SHARD_ITEM_LABELS,
)
from ..traversal_data import graph_items, room_traversal_graph
from .. import traversal_rules
from .test_traversal import policy

OWNER = 'REGION_CARROT_CASTLE/ROOM_5_07'
LOWER = 'REGION_CARROT_CASTLE/ROOM_5_13__LOGIC__ENTRY_FROM_5_07'
EARLY_SOURCE = 'REGION_CARROT_CASTLE/ROOM_5_05'
DIMENSION = 'REGION_DIMENSION_MIRROR/MAIN'
CARRIERS = (RAINBOW_WEST_HUB, CARROT_HUB, CARROT_KEY)


@dataclass
class ClosureFixture:
    world: KirbyAmWorld
    target: Entrance
    event: KirbyAmLocation

    def sweep(self) -> CollectionState:
        state = CollectionState(self.world.multiworld)
        # Evaluate before inventory/events to exercise real region cache invalidation.
        self.target.can_reach(state)
        state.sweep_for_advancements()
        before = state.prog_items[1].copy()
        state.sweep_for_advancements()
        assert before == state.prog_items[1]
        return state


def fixture(  # noqa: C901 - one explicit isolated-world dependency matrix
            *, goal: int = 1, shards: int = 2, accessibility: str = 'minimal', source_mode: int = 2,
            statues: bool = False, early: str | None = None, cycle: str | None = None,
            missing_shard: bool = False, duplicate_shard: bool = False, dimension: bool = True,
            dmk: bool = True, central: bool = True, keys: bool = True, players: int = 1) -> ClosureFixture:
    """Keep production rules/vanilla placements; replace unrelated topology only.

    Vanilla shards come from create_items' real locked boss locations. Shuffled
    shards are explicitly placed in isolated checks. No event is hand-collected.
    """
    mw = MultiWorld(players)
    for player in mw.player_ids:
        mw.game[player] = KirbyAmWorld.game
    mw.player_name = {player: f'Master closure {player}' for player in mw.player_ids}
    mw.set_seed(1052719)
    args = Namespace()
    overrides = {'goal': goal, 'shards': shards, 'accessibility': accessibility,
                 'ability_randomization_mode': 2, 'ability_randomization_statues': False,
                 'ability_randomization_no_ability_weight': 100, 'area_keys': keys,
                 'required_area_bosses': 1}
    for name, cls in KirbyAmWorld.options_dataclass.type_hints.items():
        setattr(args, name, {player: cls.from_any(overrides.get(name, cls.default)) for player in mw.player_ids})
    mw.set_options(args)
    for player in mw.player_ids[1:]:
        mw.regions.append(Region("Menu", player, mw))
        mw.completion_condition[player] = lambda state: True
    world = mw.worlds[1]
    assert isinstance(world, KirbyAmWorld)
    mw.state = CollectionState(mw)
    world.generate_early()
    # Synthetic branch controls without bounded assignment-search or generation.
    resolver = policy(1, pool=[early]) if early else policy(source_mode, statues=statues, weight=100, pool=['Ice'])
    world._enemy_copy_ability_policy = resolver.policy
    world.options.ability_randomization_statues.value = int(statues)
    world.create_regions()
    world.create_items()
    world.set_rules()
    target = mw.get_entrance(f'{OWNER} -> {LOWER}', 1)
    target_rule = target.access_rule
    dimension_rule = mw.get_entrance(dimension_mirror_entrance_names()[0], 1).access_rule
    event = mw.get_location(CENTRAL_RETURN_EVENT, 1)
    assert isinstance(event, KirbyAmLocation) and event.item is not None
    assert event.address is None and event.item.code is None and event.locked
    assert CENTRAL_RETURN_EVENT not in _GOAL_LOCATION_LABELS.values()
    keep = set(_BOSS_DEFEAT_LOCATION_LABELS) | set(_GOAL_LOCATION_LABELS.values()) | {
        CENTRAL_RETURN_EVENT, _DMK_DIMENSION_MIRROR_EVENT}
    for region in mw.regions:
        for entrance in region.exits:
            entrance.access_rule = lambda state: False
        region.locations = [location for location in region.locations if location.name in keep]
    target.access_rule = target_rule
    mw.itempool.clear()
    # No automatic permission, hub, key, shard or modeled event starts.
    mw.precollected_items[1].clear()
    menu = mw.get_region('Menu', 1)
    owner = mw.get_region(OWNER, 1)
    lower = mw.get_region(LOWER, 1)
    connected = set()

    def connect(region: Region, rule: Callable[[CollectionState], bool] | None = None) -> None:
        if region.name not in connected:
            menu.connect(region, f'Isolated -> {region.name}', rule=rule)
            connected.add(region.name)

    if central:
        connect(mw.get_region(CENTRAL_REGION, 1))
    connect(owner)
    if early:
        connect(mw.get_region(EARLY_SOURCE, 1))
    connect(mw.get_region(DIMENSION, 1), lambda state: dimension and dimension_rule(state))
    mw.get_location(_DMK_DIMENSION_MIRROR_EVENT, 1).access_rule = lambda state: dmk
    # Goal location parent access is independent of clear availability.
    for name in _GOAL_LOCATION_LABELS.values():
        region = cast(Region, mw.get_location(name, 1).parent_region)
        if region.name not in {DIMENSION, CENTRAL_REGION}:
            connect(region)

    def put(name: str, item: str, region: Region = menu) -> KirbyAmLocation:
        location = KirbyAmLocation(1, name, 9000000 + len(mw.get_locations()), region)
        region.locations.append(location)
        location.place_locked_item(world.create_item(item))
        return location

    for i, label in enumerate(_BOSS_DEFEAT_LOCATION_LABELS):
        boss = mw.get_location(label, 1)
        boss_region = boss.parent_region
        assert boss_region is not None
        if shards == 0:
            assert boss.item is not None and boss.item.name == _SHARD_ITEM_LABELS[i] and boss.locked
        else:
            boss.place_locked_item(world.create_filler())
        # Every boss except the last is an independent early synthetic ingress.
        if i != 7 or cycle not in {'shard', 'precursor'}:
            connect(boss_region)
        elif cycle == 'shard':
            lower.connect(boss_region, 'Target -> last vanilla boss')
        else:
            connect(boss_region, lambda state: state.has('Moonlight Mansion - Area Key', 1))
        if shards == 0 and i == 7 and missing_shard:
            boss.access_rule = lambda state: False
    if shards == 2:
        for i, label in enumerate(_SHARD_ITEM_LABELS):
            if i == 7 and missing_shard:
                if duplicate_shard:
                    put('Duplicate shard', _SHARD_ITEM_LABELS[0])
                continue
            loc = put(f'Independent shard {i}', label, lower if i == 7 and cycle == 'shard' else menu)
            if i == 7 and cycle == 'precursor':
                loc.access_rule = lambda state: state.has('Moonlight Mansion - Area Key', 1)
    if cycle == 'precursor':
        put('Upstream precursor behind target', 'Moonlight Mansion - Area Key', lower)
    for carrier in CARRIERS:
        if carrier == CARROT_KEY and not keys:
            continue
        put(f'Carrier {carrier}', carrier, lower if cycle == carrier else menu)
    if early and early != 'Beam':
        put('Early ability permission', f'{early} Ability')
    put('Lower target check', '1 Up', lower)
    return ClosureFixture(world, target, event)


@pytest.mark.parametrize('goal', [0, 1, 2, 4])
@pytest.mark.parametrize('accessibility', ['full', 'minimal'])
@pytest.mark.parametrize('shards', [0, 2])
def test_independent_eight_shards_enable_only_after_real_event_sweep(
    goal: int, accessibility: str, shards: int,
) -> None:
    f = fixture(goal=goal, shards=shards, accessibility=accessibility)
    state = f.sweep()
    assert state.has(CENTRAL_RETURN_EVENT, 1) and f.target.can_reach(state)
    assert f.world.multiworld.can_beat_game()
    assert f.world.multiworld.fulfills_accessibility()
    validate_all_checks(f.world.multiworld, [1])


@pytest.mark.parametrize('goal', [0, 1, 2, 4])
@pytest.mark.parametrize('duplicate', [False, True])
def test_missing_or_duplicate_unique_shard_ignores_goal_shortcuts(goal: int, duplicate: bool) -> None:
    f = fixture(goal=goal, missing_shard=True, duplicate_shard=duplicate)
    state = f.sweep()
    assert not state.has(CENTRAL_RETURN_EVENT, 1)
    assert not f.target.can_reach(state)
    if goal != 0:
        assert state.has(_GOAL_LOCATION_LABELS[goal], 1)
        assert f.world.multiworld.can_beat_game()
    # Even arbitrary objective items cannot replace the missing unique shard.
    for label in _GOAL_LOCATION_LABELS.values():
        state.collect(f.world.create_event(label), prevent_sweep=True)
    state.sweep_for_advancements()
    assert not state.has(CENTRAL_RETURN_EVENT, 1)


@pytest.mark.parametrize('missing', ['dimension', 'dmk', 'central'])
def test_dimension_dmk_and_parent_central_are_separate_requirements(missing: str) -> None:
    f = fixture(dimension=missing != 'dimension', dmk=missing != 'dmk', central=missing != 'central')
    state = f.sweep()
    assert all(state.has(shard, 1) for shard in _SHARD_ITEM_LABELS)
    assert not state.has(CENTRAL_RETURN_EVENT, 1) and not f.target.can_reach(state)
    if missing == 'dimension':
        state.collect(f.world.create_event(_DMK_DIMENSION_MIRROR_EVENT), prevent_sweep=True)
        state.sweep_for_advancements()
        assert not state.has(CENTRAL_RETURN_EVENT, 1)


@pytest.mark.parametrize('shards', [0, 2])
@pytest.mark.parametrize('cycle', ['shard', 'precursor', *CARRIERS])
def test_last_shard_precursor_and_each_carrier_cannot_self_unlock(shards: int, cycle: str | None) -> None:
    f = fixture(shards=shards, cycle=cycle)
    state = f.sweep()
    assert not f.target.can_reach(state)
    assert state.has(CENTRAL_RETURN_EVENT, 1) == (cycle in CARRIERS)
    assert not state.has(cycle if cycle in CARRIERS else _SHARD_ITEM_LABELS[-1], 1)
    # A fresh counterpart has the exact same prerequisites independently placed.
    independent = fixture(shards=shards)
    assert independent.target.can_reach(independent.sweep())


@pytest.mark.parametrize('shards', [0, 2])
@pytest.mark.parametrize('early', ['Beam', 'Fighter', 'Sword', 'Fire'])
def test_independent_reviewed_early_alternative_breaks_last_shard_cycle(shards: int, early: str) -> None:
    f = fixture(shards=shards, cycle='shard', early=early)
    state = CollectionState(f.world.multiworld)
    # Sweep only independent early items. Neither the last shard nor the new event is available yet.
    state.sweep_for_advancements(locations=[loc for loc in f.world.multiworld.get_locations()
                                            if loc.name == 'Early ability permission'])
    assert not state.has(CENTRAL_RETURN_EVENT, 1)
    assert f.target.can_reach(state)
    state.sweep_for_advancements()
    assert state.has(_SHARD_ITEM_LABELS[-1], 1) and state.has(CENTRAL_RETURN_EVENT, 1)
    denied = fixture(shards=shards, cycle='shard')
    assert not denied.target.can_reach(denied.sweep())


@pytest.mark.parametrize('goal', [0, 1, 2, 4])
@pytest.mark.parametrize('accessibility', ['full', 'minimal'])
@pytest.mark.parametrize('shards', [0, 2])
def test_minimal_goal_semantics_do_not_disable_final_placed_check_guard(
    goal: int, accessibility: str, shards: int,
) -> None:
    f = fixture(goal=goal, shards=shards, accessibility=accessibility, cycle='shard')
    state = f.sweep()
    assert not state.has(CENTRAL_RETURN_EVENT, 1)
    assert f.world.multiworld.can_beat_game() == (goal != 0)
    if accessibility == 'minimal' and goal != 0:
        assert f.world.multiworld.fulfills_accessibility()
    else:
        with pytest.raises(FillError):
            f.world.multiworld.fulfills_accessibility()
    # Existing final guard is intentionally stronger than AP minimal semantics.
    with pytest.raises(KirbyAmCheckAccessibilityError, match='Generation stopped before'):
        validate_all_checks(f.world.multiworld, [1])


@pytest.mark.parametrize('mode,statues', [(0, False), (1, False), (1, True), (2, False), (2, True)])
@pytest.mark.parametrize('cycle', [None, 'shard'])
def test_ordinary_source_policy_does_not_change_clear_fixed_point(mode: int, statues: bool, cycle: str | None) -> None:
    f = fixture(source_mode=mode, statues=statues, cycle=cycle)
    state = f.sweep()
    assert state.has(CENTRAL_RETURN_EVENT, 1) == (cycle is None)
    assert f.target.can_reach(state) == (cycle is None)


def test_hypothetical_source_feasibility_never_populates_actual_collection_state() -> None:
    graph = room_traversal_graph('bomb_719_room13', 'central_master', True)
    assert traversal_rules.graph_succeeds(graph, policy(2, weight=100), graph_items(graph), True, retries=False)
    f = fixture(cycle='shard')
    assert not f.target.can_reach(f.sweep())
    assert not f.world.multiworld.state.has(CENTRAL_RETURN_EVENT, 1)


def test_add_rule_preserves_existing_blocker_and_event_is_not_automatic() -> None:
    f = fixture()
    from worlds.generic.Rules import add_rule
    add_rule(f.target, lambda state: False)
    state = f.sweep()
    assert state.has(CENTRAL_RETURN_EVENT, 1) and not f.target.can_reach(state)


def test_missing_declared_event_fails_loudly() -> None:
    from ..rules import install_central_return_rule

    f = fixture()
    parent = f.event.parent_region
    assert parent is not None
    parent.locations.remove(f.event)
    with pytest.raises(KeyError):
        install_central_return_rule(f.world)


def test_enabled_key_inventory_does_not_leak_between_players() -> None:
    f = fixture(cycle=CARROT_KEY, players=2)
    mw = f.world.multiworld
    remote = mw.get_region('Menu', 2)
    location = KirbyAmLocation(2, 'Other player key', 9000100, remote)
    remote.locations.append(location)
    location.place_locked_item(mw.worlds[2].create_item(CARROT_KEY))
    state = f.sweep()
    assert state.has(CARROT_KEY, 2) and not state.has(CARROT_KEY, 1)
    assert state.has(CENTRAL_RETURN_EVENT, 1) and not f.target.can_reach(state)


@pytest.mark.parametrize('independent_delivery', [False, True])
def test_remote_carrier_delivery_closes_only_without_cross_player_cycle(independent_delivery: bool) -> None:
    f = fixture(cycle=CARROT_KEY, players=2)
    mw = f.world.multiworld
    remote = mw.get_region('Menu', 2)
    delivery = KirbyAmLocation(2, 'Remote Carrot key delivery', 9000100, remote)
    remote.locations.append(delivery)
    delivery.place_locked_item(f.world.create_item(CARROT_KEY))
    delivery.access_rule = lambda state: independent_delivery or state.has('Moonlight Mansion - Area Key', 2)
    lower = mw.get_region(LOWER, 1)
    precursor = KirbyAmLocation(1, 'Remote precursor behind target', 9000101, lower)
    lower.locations.append(precursor)
    precursor.place_locked_item(mw.worlds[2].create_item('Moonlight Mansion - Area Key'))
    state = f.sweep()
    assert state.has(CENTRAL_RETURN_EVENT, 1)
    assert f.target.can_reach(state) == independent_delivery
    assert state.has(CARROT_KEY, 1) == independent_delivery
    assert state.has('Moonlight Mansion - Area Key', 2) == independent_delivery


def test_actual_collection_never_inherits_hypothetical_all_inventory_event() -> None:
    f = fixture(cycle='shard')
    mw = f.world.multiworld
    # Same items, deliberately also visible to the diagnostic all-item pool.
    # This is exactly why the final guard must start from fresh placed progression.
    mw.itempool.extend(item for location in mw.get_filled_locations()
                       if (item := location.item) is not None and item.code is not None)
    hypothetical = mw.get_all_state()
    assert hypothetical.has(CENTRAL_RETURN_EVENT, 1) and f.target.can_reach(hypothetical)
    real = f.sweep()
    assert not real.has(CENTRAL_RETURN_EVENT, 1) and not f.target.can_reach(real)
    with pytest.raises(KirbyAmCheckAccessibilityError, match='unreachable from placed progression'):
        validate_all_checks(mw, [1])
