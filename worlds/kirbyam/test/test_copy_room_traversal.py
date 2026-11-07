"""The new access item supplies a source, never equipment or a route bypass."""
from copy import deepcopy
import random
from unittest.mock import patch

import pytest
from BaseClasses import CollectionState

from ..ability_randomization import build_enemy_copy_ability_policy
from ..traversal import Grant, SourcePolicy
from ..traversal_data import graph_items, room_traversal_graph
from ..wheel_traversal import RACE_ENTRANCE
from .test_mini_traversal import make_world

CASES = [('wheel_108_chest', 'chest', 'Wheel'), ('peg_149_35_18', 'target', 'Smash')]
ITEM = 'Copy Ability Room Access'
ROOM = 'REGION_COPY_ABILITY_ROOM/MAIN'


@pytest.mark.parametrize('target_id,target,ability', CASES)
@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('area_keys', [False, True])
def test_fixed_copy_sources_require_access_and_each_carry_item(target_id, target, ability, gating, area_keys):
    graph = room_traversal_graph(target_id, 'statues', area_keys)
    policy = SourcePolicy({'mode': 0})
    owned = graph_items(graph) | {ability + ' Ability'}
    assert graph.evaluate(policy, owned, gating).reaches(target)
    assert not graph.evaluate(policy, owned - {ITEM}, gating).reaches(target)
    for item in graph_items(graph):
        assert not graph.evaluate(policy, owned - {item}, gating).reaches(target), item
    assert graph.evaluate(policy, owned - {ability + ' Ability'}, gating).reaches(target) is (not gating)
    assert not graph.evaluate(policy, frozenset({ITEM}), True).reaches(target)
    assert not graph.evaluate(policy, frozenset({ability + ' Ability'}), True).reaches(target)
    assert not graph.requires_all_hub_switches


@pytest.mark.parametrize('target_id,target,ability', CASES)
@pytest.mark.parametrize('mode', [1, 2])
def test_copy_room_does_not_rewrite_bad_actual_statue_grants(target_id, target, ability, mode):
    raw = build_enemy_copy_ability_policy(random.Random(73), mode, True, True,
                                          whitelist=('Stone',), no_ability_weight=100)
    before = deepcopy(raw)
    policy = SourcePolicy(raw, True)
    graph = room_traversal_graph(target_id, 'statues', True)
    owned = graph_items(graph) | {ability + ' Ability'}
    assert not graph.evaluate(policy, owned, True, allow_documented_retries=True).reaches(target)
    assert raw == before


@pytest.mark.parametrize('target_id,target,ability', CASES)
@pytest.mark.parametrize('accessibility', ['full', 'minimal'])
def test_installed_copy_sources_need_independent_access_permission_and_actual_grant(
    target_id, target, ability, accessibility,
):
    world = make_world(2, True, accessibility=accessibility, ability_randomization_statues=False,
                       ability_randomization_no_ability_weight=100)
    state = CollectionState(world.multiworld)
    graph = room_traversal_graph(target_id, 'statues', True)
    for name in graph_items(graph) | {ability + ' Ability'}:
        state.collect(world.create_item(name), prevent_sweep=True)
    rule_target = (world.multiworld.get_entrance(RACE_ENTRANCE, 1) if target == 'chest' else
                   world.multiworld.get_location('Moonlight Mansion 2-20 - Small Chest', 1))
    with patch.object(state, 'can_reach_region', return_value=False):
        assert not rule_target.access_rule(state)
    with patch.object(state, 'can_reach_region', side_effect=lambda region, player: region == ROOM):
        assert rule_target.access_rule(state)
        state.remove(world.create_item(ability + ' Ability'))
        assert not rule_target.access_rule(state)
        state.collect(world.create_item(ability + ' Ability'), prevent_sweep=True)
        with patch.object(SourcePolicy, 'grant', return_value=Grant(frozenset())):
            assert not rule_target.access_rule(state)
        state.remove(world.create_item(ITEM))
        # Even an incorrectly optimistic region cache cannot manufacture acquisition.
        assert not rule_target.access_rule(state)
