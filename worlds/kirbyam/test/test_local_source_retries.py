"""Documented local source retries are conditional, not finite lucky-draw proofs."""

import random
from unittest.mock import patch

import pytest
from BaseClasses import CollectionState

from ..ability_randomization import build_enemy_copy_ability_policy
from ..data import data
from ..traversal import SourcePolicy
from ..traversal_data import room_traversal_graph, room_traversal_targets
from ..wheel_traversal import LOCAL_SOURCE_REGION, RACE_ENTRANCE
from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive
from .test_mini_traversal import make_world


CASES = [
    ('wheel_108_chest', 'chest', '0x088B765C', 'WHEELIE', 'Wheel Ability'),
    ('peg_149_35_18', 'target', '0x088BC434', 'GIANT_ROCKY', 'Hammer Ability'),
]


def live_policy(weight):
    raw = build_enemy_copy_ability_policy(
        random.Random(427), 2, True, True, whitelist=('Wheel', 'Hammer'),
        include_passive_enemies=True, no_ability_weight=weight,
    )
    return SourcePolicy(raw, include_statues=False)


@pytest.mark.parametrize('target_id,target,identity,source_key,permission', CASES)
@pytest.mark.parametrize('weight', [0, 55, 99, 100])
def test_local_live_sources_require_positive_support_and_explicit_retry(
    target_id, target, identity, source_key, permission, weight,
):
    graph = room_traversal_graph(target_id, 'local')
    source = next(p for p in graph.placements if p.identity == identity)
    assert source.source_key == source_key
    assert source.renewable and source.retry_evidence
    assert graph.unavailable_reason is None
    assert all(node.room != 970 for node in graph.nodes)
    policy = live_policy(weight)
    owned = frozenset({'Wheel Ability', 'Hammer Ability'})
    finite = graph.evaluate(policy, owned, True)
    assert not finite.reaches(target)
    assert not finite.retry_assumptions
    conditional = graph.evaluate(policy, owned, True, allow_documented_retries=True)
    assert conditional.reaches(target) == (weight < 100)
    assert bool(conditional.retry_assumptions) == (weight < 100)
    missing_permission = graph.evaluate(policy, owned - {permission}, True, allow_documented_retries=True)
    assert not missing_permission.reaches(target)
    ungated = graph.evaluate(policy, frozenset(), False, allow_documented_retries=True)
    assert ungated.reaches(target) == (weight < 100)


def test_installed_local_peg_rule_can_retry_without_remote_access():
    world = make_world(2, True, ability_randomization_statues=False, ability_randomization_no_ability_weight=55)
    state = CollectionState(world.multiworld)
    row = next(row for row in room_traversal_targets('peg') if row['id'] == 'peg_149_35_18')
    location = world.multiworld.get_location(data.locations[row['location']].label, 1)
    # Starting Stone permission is sufficient only because the physical Giant
    # Rocky is independently present and its audited repeat route is available.
    assert state.has('Stone Ability', 1)
    with patch.object(state, 'can_reach_region', return_value=False):
        assert location.access_rule(state)
        with patch.object(SourcePolicy, 'grant', return_value=live_policy(100).grant('GIANT_ROCKY', lambda _: True)):
            assert not location.access_rule(state)


def test_installed_wheel_rule_requires_its_independent_source_region_and_permission():
    world = make_world(2, True, ability_randomization_statues=False, ability_randomization_no_ability_weight=55)
    state = CollectionState(world.multiworld)
    target = world.multiworld.get_entrance(RACE_ENTRANCE, 1)
    with patch.object(state, 'can_reach_region', return_value=False):
        state.collect(world.create_item('Wheel Ability'), prevent_sweep=True)
        assert not target.access_rule(state)
    with patch.object(state, 'can_reach_region', side_effect=lambda region, player: region == LOCAL_SOURCE_REGION):
        assert target.access_rule(state)
        state.remove(world.create_item('Wheel Ability'))
        assert not target.access_rule(state)


@pytest.mark.parametrize('weight', [0, 55])
@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('area_keys', [False, True])
def test_live_fixed_statue_local_retry_archive(tmp_path, weight, gating, area_keys):
    player = tmp_path / 'player.yaml'
    player.write_text(
        'name: Local retry\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n'
        '  ability_randomization_mode: 2\n  ability_randomization_statues: 0\n'
        f'  ability_randomization_no_ability_weight: {weight}\n'
        f'  ability_gating: {int(gating)}\n  area_keys: {int(area_keys)}\n'
        '  room_sanity: 1\n', encoding='utf-8',
    )
    archive = generate_archive_from_fixture(
        player, tmp_path / 'output', seed=8100 + weight + int(gating) * 2 + int(area_keys),
    )
    decoded = load_multidata_from_archive(archive)
    assert decoded['locations'][1]
    starts = decoded['precollected_items'][1]
    assert 3860108 in starts  # Stone retains starting permission.
    assert 3860104 not in starts  # Wheel remains a findable permission, never starting equipment.
    pool = {entry[0] for entry in decoded['locations'][1].values()}
    assert (3860104 in pool) == gating
