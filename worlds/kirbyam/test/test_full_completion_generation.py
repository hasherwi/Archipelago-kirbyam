"""Independent inventory, reachability and real generation checks for issue #204.

These checks establish the AP model and archive contract, not native gameplay.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, cast

import pytest

from BaseClasses import ItemClassification
from test.general import setup_multiworld

from .. import KirbyAmWorld
from ..completion import MANIFEST, PHYSICAL_KEYS, REQUIRED_ITEMS, ROOM_REGIONS
from ..data import LocationCategory, data, load_json_data
from ..options import Goal
from ..rules import set_rules
from ..vitality import VITALITY_ITEM_IDS
from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive
from .test_rules import _FakeState, _FakeWorld

GOAL_LABEL = "100% Game Completion"
HEALTH_PAIRS = [(low, high) for low in range(1, 11) for high in range(low, 11)]
REPRESENTATIVE_HEALTH = [(6, 6), (3, 5), (6, 10), (1, 10)]


def test_completion_inventory_matches_independent_native_and_ap_catalogs() -> None:
    native = cast(dict[str, Any], load_json_data("../dev-docs/native-room-wikirby-map.json"))
    # The native source table counts indices 8..279, while optional AP visits
    # also include Central Circle and omit the ten final-sequence rooms.
    rows = MANIFEST["rooms"]
    by_native = {row["native_id"]: row for row in native["rooms"]}
    assert len(rows) == len({row["native_room_id"] for row in rows}) == 272
    assert {row["doors_idx"] for row in rows} == set(range(8, 280))
    for row in rows:
        assert by_native[row["native_room_id"]]["completion_index"] == row["doors_idx"]
        for key in row["region_keys"]:
            assert key in data.regions
    aggregate = [row for row in rows if not row["region_keys"]]
    assert {row["native_room_id"] for row in aggregate} == {
        909, 910, 911, 912, 913, 914, 915, 916, 918, 919,
    }
    assert all(row["logic_requirement"] == "dark_mind_sequence" for row in aggregate)
    visits = {loc.bit_index for loc in data.locations.values() if loc.category == LocationCategory.ROOM_SANITY}
    assert visits == {0, *range(8, 270)}
    assert len(ROOM_REGIONS) == 262
    recovery = cast(dict[str, Any], load_json_data("chest_recovery.json"))["records"]
    assert len(recovery) == 84
    assert {row["flag"] for row in recovery} == set(MANIFEST["chest_flags"]) == set(range(84))
    chest_keys = {row["location_key"] for row in recovery if row["location_key"]}
    assert len(chest_keys) == 80
    switches_and_levers = {key for key, loc in data.locations.items()
                           if loc.category in (LocationCategory.HUB_SWITCH, LocationCategory.LEVER)}
    assert set(PHYSICAL_KEYS) == chest_keys | switches_and_levers
    assert len(PHYSICAL_KEYS) == 99
    assert len(REQUIRED_ITEMS) == 27
    assert [sum(tag in item.tags for item in REQUIRED_ITEMS)
            for tag in ("Shards", "Levers", "HubConnections")] == [8, 4, 15]
    sheet = data.locations["MINOR_CHEST_MUSIC_NOTE_06"]
    assert sheet.location_id == 3960519
    assert sheet.parent_region == "REGION_CARROT_CASTLE/ROOM_5_13__LOGIC__ENTRY_FROM_5_14"
    assert next(row for row in recovery if row["location_key"] == "MINOR_CHEST_MUSIC_NOTE_06")["flag"] == 81


class _CompletionState(_FakeState):
    def __init__(self) -> None:
        super().__init__(
            {item.label for item in REQUIRED_ITEMS} | {"Defeat Dark Meta Knight (Dimension Mirror)"},
            {data.locations[key].label for key in PHYSICAL_KEYS},
        )
        self.regions = {region for group in ROOM_REGIONS for region in group}

    def can_reach_region(self, name: str, _player: int) -> bool:
        return name in self.regions


def test_every_required_obligation_gates_goal_independently() -> None:
    world: Any = _FakeWorld(Goal.option_full_completion)
    set_rules(world)
    rule = world.multiworld.get_location(GOAL_LABEL, 1).access_rule
    state = _CompletionState()
    assert rule(state)
    assert not any("Vitality" in item.tags for item in REQUIRED_ITEMS)
    for label in tuple(state._owned):
        state._owned.remove(label)
        assert not rule(state), label
        state._owned.add(label)
    for label in tuple(state._reachable_locations):
        state._reachable_locations.remove(label)
        assert not rule(state), label
        state._reachable_locations.add(label)
    for group in ROOM_REGIONS:
        state.regions.difference_update(group)
        assert not rule(state), group
        state.regions.update(group)
    # Reaching maximum HP / collecting every upgrade cannot replace one chest.
    for item in data.items.values():
        if "Vitality" in item.tags:
            state._owned.add(item.label)
    state._reachable_locations.remove(data.locations["VITALITY_CHEST_CARROT_CASTLE"].label)
    assert not rule(state)


@pytest.mark.parametrize("minimum,maximum", HEALTH_PAIRS)
def test_all_55_health_ranges_generate_completable_graph_without_vitality(
    minimum: int, maximum: int,
) -> None:
    mw = setup_multiworld(KirbyAmWorld, seed=204, options={
        "goal": "full_completion", "minimum_health": minimum, "maximum_health": maximum,
        "room_sanity": (minimum + maximum) % 2, "shards": 2 * (maximum % 2),
    })
    goal = mw.get_location(GOAL_LABEL, 1)
    assert goal.address is None and goal.locked
    assert len(mw.itempool) == len(mw.get_unfilled_locations(1))
    counts = Counter(item.code for item in mw.itempool if item.code in VITALITY_ITEM_IDS)
    assert counts == Counter(VITALITY_ITEM_IDS[:maximum - minimum])
    # get_all_state excludes useful items from progression but still must reach
    # every mandatory physical check and all 262 modeled physical room sinks.
    state = mw.get_all_state()
    assert all(not state.has(item.label, 1) for item in data.items.values() if "Vitality" in item.tags)
    for key in PHYSICAL_KEYS:
        assert state.can_reach_location(data.locations[key].label, 1), key
    for group in ROOM_REGIONS:
        assert any(state.can_reach_region(region, 1) for region in group), group
    assert goal.can_reach(state)
    assert mw.completion_condition[1](state)
    assert all(item.classification & ItemClassification.progression for item in REQUIRED_ITEMS)


@pytest.mark.parametrize("minimum,maximum", REPRESENTATIVE_HEALTH)
@pytest.mark.parametrize("room_sanity", [False, True])
@pytest.mark.parametrize("shards", [0, 2])
def test_full_completion_real_archive_matrix(
    tmp_path: Path, minimum: int, maximum: int, room_sanity: bool, shards: int,
) -> None:
    player = tmp_path / "player.yaml"
    player.write_text(
        "name: FullCompletion\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n"
        f"  goal: full_completion\n  minimum_health: {minimum}\n  maximum_health: {maximum}\n"
        f"  room_sanity: {str(room_sanity).lower()}\n  shards: {shards}\n",
        encoding="utf-8",
    )
    archive = generate_archive_from_fixture(player, tmp_path / "output", seed=204 + minimum + shards)
    decoded = load_multidata_from_archive(archive)
    slot = decoded["slot_data"][1]
    assert slot["goal"] == 5 and slot["full_completion_version"] == 1
    assert (slot["minimum_health"], slot["maximum_health"]) == (minimum, maximum)
    placed = decoded["locations"][1]
    assert {data.locations[key].location_id for key in PHYSICAL_KEYS} <= set(placed)
    assert data.locations["GOAL_100_PERCENT"].location_id not in placed
    assert Counter(item[0] for item in placed.values() if item[0] in VITALITY_ITEM_IDS) == Counter(
        VITALITY_ITEM_IDS[:maximum - minimum]
    )


@pytest.mark.parametrize("minimum,maximum", REPRESENTATIVE_HEALTH)
def test_full_completion_archive_preserves_legitimate_precollects(
    tmp_path: Path, minimum: int, maximum: int,
) -> None:
    player = tmp_path / "player.yaml"
    # Plain start_inventory deliberately adds an extra legitimate upgrade even
    # for 6/6. It must neither remove its physical chest nor become a goal gate.
    label = next(item.label for item in data.items.values() if item.item_id == VITALITY_ITEM_IDS[0])
    player.write_text(
        "name: FullPrecollect\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n"
        f"  goal: full_completion\n  minimum_health: {minimum}\n  maximum_health: {maximum}\n"
        f"  start_inventory:\n    '{label}': 1\n  start_with_all_maps: true\n",
        encoding="utf-8",
    )
    archive = generate_archive_from_fixture(player, tmp_path / "output", seed=204)
    decoded = load_multidata_from_archive(archive)
    assert VITALITY_ITEM_IDS[0] in decoded["precollected_items"][1]
    assert {data.locations[key].location_id for key in PHYSICAL_KEYS} <= set(decoded["locations"][1])
    assert decoded["slot_data"][1]["goal"] == 5
