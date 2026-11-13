"""Goal 2 retains finite Frosty/Waddle and guarded permanent Ice alternatives."""

from types import SimpleNamespace
from typing import Any, cast

import pytest

from BaseClasses import ItemClassification

from .. import KirbyAmWorld
from .. import traversal_rules as rules
from ..traversal_data import room_traversal_graph, room_traversal_targets
from .test_traversal import policy

CASES = [
    (0, True, None, 0, True),
    (1, False, ['Fire'], 0, True),
    (2, False, ['Fire'], 100, True),
    (1, True, ['Ice'], 0, True),
    (1, True, ['Fire'], 0, False),
    (2, True, ['Ice'], 0, True),
    (2, True, ['Ice', 'Fire'], 0, False),
    (2, True, ['Ice'], 50, False),
    (2, True, ['Ice'], 100, False),
]


def target_row() -> dict[str, Any]:
    return next(row for row in room_traversal_targets('block') if row['id'] == 'frozen_825_sound_effects')


@pytest.mark.parametrize('mode,minibosses,pool,weight,formerly_guaranteed', CASES)
@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('enabled', [False, True])
def test_unconditional_binding_and_lifecycle(
    mode: int,
    minibosses: bool,
    pool: list[str] | None,
    weight: int,
    formerly_guaranteed: bool,
    gating: bool,
    enabled: bool,
) -> None:
    resolver = policy(mode, minibosses=minibosses, pool=pool, weight=weight)
    assert rules.target_applies(target_row(), resolver)
    # Before create_regions: classification must never consult a location cache.
    world = SimpleNamespace(_ability_gating_enabled=lambda: gating, ENABLE_MINOR_CHESTS=enabled,
                            item_id_to_name=KirbyAmWorld.item_id_to_name,
                            multiworld=SimpleNamespace(), player=1)
    assert rules.goal2_ice_is_progression(world) is (enabled and gating)
    item = KirbyAmWorld.create_item_by_code(cast(KirbyAmWorld, world), KirbyAmWorld.item_name_to_id['Ice Ability'])
    assert item.classification == (ItemClassification.progression if enabled and gating
                                   else ItemClassification.useful)


@pytest.mark.parametrize('mode', [0, 1, 2])
@pytest.mark.parametrize('witness', ['central_statues', 'peppermint290_statues'])
def test_permanent_ice_uses_guarded_network_and_finite_waddle(mode: int, witness: str) -> None:
    from ..traversal_data import graph_items
    graph = room_traversal_graph('frozen_825_sound_effects', witness, True)
    owned = graph_items(graph) | {'Ice Ability'}
    target, = graph.required_targets
    resolver = policy(mode, pool=['Fire'], weight=100)
    assert graph.evaluate(resolver, owned, True, allow_documented_retries=True).reaches(target)
    assert not graph.evaluate(resolver, owned-{'Ice Ability'}, True,
                              allow_documented_retries=True).reaches(target)
    assert not graph.evaluate(resolver, frozenset({'Ice Ability'}), True,
                              allow_documented_retries=True).reaches(target)
    assert not any(p.source_key == 'MR_FROSTY' for p in graph.placements)
    waddle, = [p for p in graph.placements if p.source_key == 'WADDLE_DEE']
    assert not waddle.renewable
    assert all(r.opens is None for r in graph.routes)


def test_frosty_graph_is_finite_and_has_no_prebattle_copy_or_refresh() -> None:
    graph = room_traversal_graph('frozen_825_sound_effects', 'local')
    assert all(position.equipped == 'Normal' for position in graph.starts)
    assert {source.source_key for source in graph.placements} == {'MR_FROSTY', 'WADDLE_DEE'}
    assert all(not source.renewable for source in graph.placements)
    assert all(source.node not in {position.node for position in graph.starts} for source in graph.placements)
    assert all(route.opens is None for route in graph.routes)
    target, = graph.required_targets
    assert not graph.evaluate(policy(), frozenset(), True).reaches(target)
    assert graph.evaluate(policy(), frozenset({'Ice Ability'}), True).reaches(target)


def test_unsupported_final_assignment_does_not_reuse_prior_ice_decision() -> None:
    row = target_row()
    assert rules.target_applies(row, policy(1, pool=['Ice']))
    assert rules.target_applies(row, policy(1, pool=['Fire']))


@pytest.mark.parametrize('mode,gating,enabled,expected_progression', [
    (0, True, True, True),
    (0, False, True, False),
    (2, True, True, True),
    (0, True, False, False),
])
def test_real_world_item_pool_and_installed_chest(
    monkeypatch: pytest.MonkeyPatch, mode: int, gating: bool, enabled: bool, expected_progression: bool
) -> None:
    from BaseClasses import CollectionState
    from ..data import data
    from .test_mini_traversal import make_world

    monkeypatch.setattr(KirbyAmWorld, 'ENABLE_MINOR_CHESTS', enabled)
    world = make_world(mode, gating, accessibility='minimal', ability_randomization_no_ability_weight=100,
                       room_sanity=not enabled)
    world.create_items()
    assert not any(item.name == 'Ice Ability' for item in world.multiworld.itempool)
    ice_items = [item for item in world.multiworld.precollected_items[1] if item.name == 'Ice Ability']
    assert len(ice_items) == 1
    assert any(item.classification & ItemClassification.progression for item in ice_items) is expected_progression
    label = data.locations['MINOR_CHEST_MUSIC_NOTE_10'].label
    if not enabled:
        with pytest.raises(KeyError):
            world.multiworld.get_location(label, 1)
        return
    target = world.multiworld.get_location(label, 1)
    state = CollectionState(world.multiworld)
    state.remove(ice_items[0])  # Test the route without the guaranteed permission.
    assert target.access_rule(state) is (not expected_progression)
    if expected_progression:
        state.collect(ice_items[0], prevent_sweep=True)
        if mode == 0:
            assert target.access_rule(state)


def test_main_order_explicit_ice_three_before_regions() -> None:
    from argparse import Namespace
    from BaseClasses import CollectionState, MultiWorld
    multiworld = MultiWorld(1)
    multiworld.game[1] = KirbyAmWorld.game
    multiworld.player_name = {1: 'Ice lifecycle'}
    multiworld.set_seed(773)
    args = Namespace()
    overrides = {'ability_randomization_mode': 2, 'ability_gating': True,
                 'start_inventory': {'Ice Ability': 3}, 'accessibility': 'minimal'}
    for name, option in KirbyAmWorld.options_dataclass.type_hints.items():
        setattr(args, name, {1: option.from_any(overrides.get(name, option.default))})
    multiworld.set_options(args)
    world = multiworld.worlds[1]
    multiworld.state = CollectionState(multiworld)
    world.generate_early()
    # Main applies explicit inventory here, before create_regions.
    for item_name, count in world.options.start_inventory.value.items():
        for _ in range(count):
            multiworld.push_precollected(multiworld.create_item(item_name, 1))
    items = [item for item in multiworld.precollected_items[1] if item.name == 'Ice Ability']
    assert len(items) == 3
    assert all(item.classification & ItemClassification.progression for item in items)
    assert multiworld.state.count('Ice Ability', 1) == 3
    world.create_regions()
    world.set_rules()
    assert multiworld.state.count('Ice Ability', 1) == 3


@pytest.mark.parametrize('witness', ['central_statues', 'peppermint290_statues'])
def test_no_fallback_when_randomized_statues_cannot_supply_ice(witness: str) -> None:
    from ..traversal_data import graph_items, has_graph_access
    graph = room_traversal_graph('frozen_825_sound_effects', witness, True)
    owned = graph_items(graph) | {'Ice Ability'}
    target, = graph.required_targets
    assert not graph.evaluate(policy(2, statues=True, pool=['Fire']), owned, True,
                              allow_documented_retries=True).reaches(target)
    # Native statue touches ignore the enemy Normal weighting.
    assert graph.evaluate(policy(2, statues=True, pool=['Ice'], weight=100), owned, True,
                          allow_documented_retries=True).reaches(target)
    # Permission and all keys do not substitute for the independent source region.
    state = SimpleNamespace(can_reach_region=lambda region, player: False)
    assert not has_graph_access(SimpleNamespace(player=1), state, graph)
    assert graph.access_region is not None
