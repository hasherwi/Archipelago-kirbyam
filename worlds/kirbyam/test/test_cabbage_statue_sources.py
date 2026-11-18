"""Reviewed hub statues supply physical equipment before the Chocolate carry."""
from dataclasses import replace
from types import SimpleNamespace

import pytest

from ..traversal import SourcePolicy
from ..traversal_data import room_traversal_graph, room_traversal_targets
from ..traversal_rules import cabbage_source_is_progression, target_applies
from .test_traversal import policy

TARGET = 'bomb_517_chocolate'
WITNESS = 'hub2_statues_entry'
PROVIDERS = ('Beam', 'Smash', 'Fire', 'Missile', 'Parasol', 'Spark', 'Ice', 'Sword', 'Fighter', 'UFO')


def graph():
    return room_traversal_graph(TARGET, WITNESS)


def row():
    return next(r for r in room_traversal_targets('block') if r['id'] == TARGET)


@pytest.mark.parametrize('ability', PROVIDERS)
@pytest.mark.parametrize('gating', [False, True])
def test_statue_assignment_uses_each_existing_complete_carry(ability, gating):
    p = SourcePolicy(policy(1, pool=[ability]).policy, include_statues=True)
    g = graph()
    assert g.access_region == 'REGION_CABBAGE_CAVERN/ROOM_3_HUB_2'
    assert {s.source_key for s in g.placements} == {'STATUE:353906', 'STATUE:353901'}
    assert all(s.renewable for s in g.placements)
    assert target_applies(row(), p)
    goal, = g.required_targets
    assert g.evaluate(p, frozenset({ability + ' Ability'}), gating).reaches(goal)
    if gating and ability != 'Beam':
        assert not g.evaluate(p, frozenset(), True).reaches(goal)


def test_native_statues_do_not_inherit_enemy_randomness_or_failure_weight():
    p = policy(2, pool=['Mini'], weight=100)
    g = graph()
    goal, = g.required_targets
    assert not p.grant('WADDLE_DOO', lambda _: True).abilities
    assert target_applies(row(), p)
    assert g.evaluate(p, frozenset({'Spark Ability'}), True).reaches(goal)
    assert g.evaluate(p, frozenset({'Fighter Ability'}), True).reaches(goal)
    assert not g.evaluate(p, frozenset(), True).reaches(goal)


@pytest.mark.parametrize('mutation', ['absent', 'behind_goal', 'lost'])
def test_permission_without_physical_acquisition_or_carry_does_not_suffice(mutation):
    g = graph()
    goal, = g.required_targets
    if mutation == 'absent':
        g = replace(g, placements=())
    elif mutation == 'behind_goal':
        g = replace(g, placements=tuple(replace(s, node=goal) for s in g.placements))
    else:
        g = replace(g, routes=tuple(replace(r, loses_equipment=True) if r.room_transition else r
                                   for r in g.routes))
    assert not g.evaluate(policy(0), frozenset({'Spark Ability', 'Fighter Ability'}), True).reaches(goal)


def test_wrong_randomized_statues_do_not_manufacture_supported_equipment():
    p = SourcePolicy(policy(1, pool=['Sleep']).policy, include_statues=True)
    g = graph()
    goal, = g.required_targets
    assert not g.evaluate(p, frozenset({'Spark Ability', 'Fighter Ability', 'Sleep Ability'}), False).reaches(goal)
    assert not target_applies(row(), p)  # This unsupported policy remains explicitly unresolved.


@pytest.mark.parametrize('enabled', [False, True])
def test_classification_uses_native_statues_before_region_creation(enabled):
    world = SimpleNamespace(_enemy_copy_ability_policy=policy(2, pool=['Mini'], weight=100).policy,
                            _ability_gating_enabled=lambda: True, ENABLE_MINOR_CHESTS=enabled,
                            options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=0)))
    assert cabbage_source_is_progression(world, 'Spark') is enabled
    assert cabbage_source_is_progression(world, 'Fighter') is enabled
    assert not cabbage_source_is_progression(world, 'Missile')


def test_live_statue_permission_filter_is_not_a_bounded_guarantee():
    p = policy(2, statues=True, pool=['Beam', 'Sword'])
    g = graph()
    goal, = g.required_targets
    # Runtime filters unavailable permissions, but later unlocks expand this
    # pool. Bounded logic must not rely on a temporarily singleton draw.
    assert p.grant('STATUE:353906', lambda a: a == 'Beam').guaranteed == frozenset({'Beam'})
    assert not g.evaluate(p, frozenset(), True).reaches(goal)
    assert not g.evaluate(p, frozenset({'Sword Ability'}), True).reaches(goal)
    assert g.evaluate(p, frozenset(), True, allow_documented_retries=True).reaches(goal)


@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('ability', ['Spark', 'Fighter'])
def test_installed_statue_route_requires_independent_access(monkeypatch, gating, ability):
    from BaseClasses import CollectionState, ItemClassification
    from .. import KirbyAmWorld
    from ..data import data
    from .support.source_policy import set_rule_test_policy
    from .test_mini_traversal import make_world
    from .test_cabbage_parasol import CHEST, OWNER, UPSTREAM

    # Every randomized enemy has no grant; native statues remain physical sources.
    raw = policy(2, pool=['Mini'], weight=100).policy
    monkeypatch.setattr(KirbyAmWorld, 'ENABLE_MINOR_CHESTS', True)
    set_rule_test_policy(monkeypatch, lambda *args, **kwargs: raw)
    world = make_world(2, int(gating), accessibility='minimal', ability_randomization_statues=0)
    state = CollectionState(world.multiworld)
    for name in ('Spark Ability', 'Fighter Ability'):
        while state.has(name, world.player):
            state.remove(world.create_item(name))
    item = world.create_item(ability + ' Ability')
    if gating:
        assert item.classification == ItemClassification.progression
    chest = world.multiworld.get_location(data.locations[CHEST].label, world.player)
    state.can_reach_region = lambda name, player: name == OWNER
    state.collect(item, prevent_sweep=True)
    assert not chest.access_rule(state)
    state.remove(item)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    assert chest.access_rule(state) is (not gating)
    state.collect(item, prevent_sweep=True)
    assert chest.access_rule(state)
