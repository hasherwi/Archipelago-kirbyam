"""Only guaranteed physical Frosty Ice grants enable the partial Goal 2 repair."""

from types import SimpleNamespace

import pytest

from BaseClasses import ItemClassification
from Options import Accessibility

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


def target_row():
    return next(row for row in room_traversal_targets('block') if row['id'] == 'frozen_825_sound_effects')


@pytest.mark.parametrize('mode,minibosses,pool,weight,applies', CASES)
@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('enabled', [False, True])
@pytest.mark.parametrize('minimal', [False, True])
def test_conditional_binding_matrix(monkeypatch, mode, minibosses, pool, weight, applies,
                                    gating, enabled, minimal):
    resolver = policy(mode, minibosses=minibosses, pool=pool, weight=weight)
    row = target_row()
    monkeypatch.setattr(rules, 'extra_traversal_targets', lambda: (row,))
    assert rules.target_applies(row, resolver) is applies
    # Unsupported policies are not rejected by source assignment validation.
    assert rules.static_extra_witness(resolver)

    def original_rule(state):
        return state.base_rule
    target = SimpleNamespace(access_rule=original_rule)

    def get_location(name, player):
        if not enabled:
            raise KeyError('disabled category')
        return target

    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy=resolver.policy,
        _ability_gating_enabled=lambda: gating, _area_keys_enabled=lambda: False,
        options=SimpleNamespace(
            ability_randomization_statues=SimpleNamespace(value=False),
            accessibility=Accessibility(Accessibility.option_minimal if minimal else Accessibility.option_full),
        ),
        multiworld=SimpleNamespace(get_location=get_location),
    )
    assert rules.goal2_ice_is_progression(world) is (applies and enabled and gating)
    rules.install_extra_traversal_rules(world)
    if not applies or not enabled:
        assert target.access_rule is original_rule
    owned = set()
    state = SimpleNamespace(base_rule=True, has=lambda item, player: item in owned,
                            can_reach_region=lambda name, player: False)
    assert target.access_rule(state) is (not (applies and enabled and gating))
    owned.add('Ice Ability')
    assert target.access_rule(state)
    state.base_rule = False
    assert not target.access_rule(state)

    # Exercise the actual item factory, not only the predicate.
    world.item_id_to_name = KirbyAmWorld.item_id_to_name
    code = KirbyAmWorld.item_name_to_id['Ice Ability']
    item = KirbyAmWorld.create_item_by_code(world, code)
    expected = ItemClassification.progression if applies and enabled and gating else ItemClassification.useful
    assert item.classification == expected


def test_frosty_graph_is_finite_and_has_no_prebattle_copy_or_refresh():
    graph = room_traversal_graph('frozen_825_sound_effects', 'local')
    assert all(position.equipped == 'Normal' for position in graph.starts)
    assert {source.source_key for source in graph.placements} == {'MR_FROSTY', 'WADDLE_DEE'}
    assert all(not source.renewable for source in graph.placements)
    assert all(source.node not in {position.node for position in graph.starts} for source in graph.placements)
    assert all(route.opens is None for route in graph.routes)
    target, = graph.required_targets
    assert not graph.evaluate(policy(), frozenset(), True).reaches(target)
    assert graph.evaluate(policy(), frozenset({'Ice Ability'}), True).reaches(target)


def test_unsupported_final_assignment_does_not_reuse_prior_ice_decision():
    row = target_row()
    assert rules.target_applies(row, policy(1, pool=['Ice']))
    assert not rules.target_applies(row, policy(1, pool=['Fire']))


@pytest.mark.parametrize('mode,gating,enabled,expected_progression', [
    (0, True, True, True),
    (0, False, True, False),
    (2, True, True, False),
    (0, True, False, False),
])
def test_real_world_item_pool_and_installed_chest(monkeypatch, mode, gating, enabled, expected_progression):
    from BaseClasses import CollectionState
    from ..data import data
    from .test_mini_traversal import make_world

    monkeypatch.setattr(KirbyAmWorld, 'ENABLE_MINOR_CHESTS', enabled)
    world = make_world(mode, gating, accessibility='minimal', ability_randomization_no_ability_weight=100,
                       room_sanity=not enabled)
    world.create_items()
    ice_items = [item for item in world.multiworld.itempool if item.name == 'Ice Ability']
    assert len(ice_items) == int(gating)
    assert any(item.classification & ItemClassification.progression for item in ice_items) is expected_progression
    label = data.locations['MINOR_CHEST_MUSIC_NOTE_10'].label
    if not enabled:
        with pytest.raises(KeyError):
            world.multiworld.get_location(label, 1)
        return
    target = world.multiworld.get_location(label, 1)
    state = CollectionState(world.multiworld)
    assert target.access_rule(state) is (not expected_progression)
    if expected_progression:
        state.collect(ice_items[0], prevent_sweep=True)
        assert target.access_rule(state)
