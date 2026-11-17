"""All physical Goal Games are independent item checks, with exit-route rules."""
import json
from pathlib import Path

import pytest

from test.general import setup_multiworld
from .. import KirbyAmWorld
from ..data import LocationCategory, data
from ..groups import LOCATION_GROUPS

GOALS = [loc for loc in data.locations.values() if loc.category == LocationCategory.GOAL_GAME]
CENTRAL = 'REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE'


def test_goal_catalog_exactly_sixteen_unique_completions():
    assert len(GOALS) == 16
    assert {loc.bit_index for loc in GOALS} == set(range(16))
    assert {loc.location_id for loc in GOALS} == set(range(3960700, 3960716))
    assert len({loc.parent_region for loc in GOALS}) == 16
    assert LOCATION_GROUPS['Goal Games'] == {loc.label for loc in GOALS}
    assert not any('CARROT' in loc.parent_region or 'DIMENSION' in loc.parent_region for loc in GOALS)
    ids = [loc.location_id for loc in data.locations.values()]
    assert len(ids) == len(set(ids))
    for loc in GOALS:
        region = data.regions[loc.parent_region]
        assert region.location_requirements.get(loc.name) == region.exit_requirements.get(CENTRAL)
        assert loc.name in region.locations
        assert loc.category != LocationCategory.GOAL


def test_exact_native_doors_are_distinct_from_visit_indices():
    rows = json.loads((Path(__file__).parents[1] / 'data/goal_game_doors.json').read_text())['goals']
    assert [row['source_room'] for row in rows] == [557, 176, 177, 745, 148, 531, 547, 326,
                                                 135, 825, 214, 224, 622, 526, 413, 420]
    doors = [door for row in rows for door in row['doors']]
    assert len(doors) == len({door['rom_offset'] for door in doors}) == 33
    assert {door['destination_room'] for door in doors} == {980, 981, 982}
    for row in rows:
        assert data.locations[row['location_key']].bit_index == row['bit_index']
        assert len({door['destination_room'] for door in row['doors']}) == 1


@pytest.mark.parametrize('room_sanity', [0, 1])
@pytest.mark.parametrize('shards', ['vanilla', 'completely_random'])
@pytest.mark.parametrize('ability_gating,area_keys,health', [(0, 0, 6), (1, 1, 10)])
def test_default_checks_reachable_and_pool_balanced(room_sanity, shards, ability_gating, area_keys, health):
    multiworld = setup_multiworld(KirbyAmWorld, seed=1000, options={
        'room_sanity': room_sanity, 'shards': shards, 'ability_gating': ability_gating,
        'area_keys': area_keys, 'maximum_health': health})
    locations = multiworld.get_locations(1)
    goals = [loc for loc in locations if loc.address in {g.location_id for g in GOALS}]
    assert len(goals) == 16
    assert all(loc.item is None for loc in goals)
    assert len(multiworld.itempool) == len([loc for loc in locations if loc.address is not None and not loc.locked])
    state = multiworld.get_all_state(False)
    assert all(loc.can_reach(state) for loc in goals)


@pytest.mark.parametrize('seed,room_sanity,shards', [(1000, 0, 'vanilla'), (1001, 1, 'completely_random')])
def test_full_fill_preserves_goal_check_accessibility(seed, room_sanity, shards):
    from Fill import distribute_items_restrictive
    multiworld = setup_multiworld(KirbyAmWorld, seed=seed,
        options={'room_sanity': room_sanity, 'shards': shards})
    distribute_items_restrictive(multiworld)
    assert all(location.item is not None for location in multiworld.get_locations())
    assert multiworld.can_beat_game()
    assert multiworld.fulfills_accessibility()
    for goal in GOALS:
        assert multiworld.get_location(goal.label, 1).item is not None
