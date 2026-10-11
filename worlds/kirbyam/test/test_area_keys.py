"""Focused AP-world tests for Area Key catalog and generation behavior."""

from __future__ import annotations

import logging

import pytest

from BaseClasses import CollectionState, Item, ItemClassification, MultiWorld
from test.general import setup_multiworld, setup_solo_multiworld
from worlds.AutoWorld import call_all

from .. import KirbyAmWorld
from ..area_keys import (
    AREA_KEY_BITFIELD_MASK,
    AREA_KEY_LABEL_BY_AREA_ID,
    AREA_KEY_LABELS,
    EARLY_REACHABLE_CHECK_THRESHOLD,
    FALLBACK_STARTING_AREA_KEY_LABEL,
    area_key_bitfield_from_items,
    area_key_entrance_area_ids,
)
from ..data import data
from ..data import LocationCategory
from ..groups import ITEM_GROUPS


_PRE_GENERATE_BASIC_STEPS = (
    "generate_early",
    "create_regions",
    "create_items",
    "set_rules",
)


def _limit_reachable_checks(multiworld: MultiWorld, player: int, count: int) -> None:
    state = CollectionState(multiworld)
    numeric_locations = [
        location
        for location in multiworld.get_locations(player)
        if location.address is not None
    ]
    initially_reachable = [
        location
        for location in numeric_locations
        if location.can_reach(state)
    ]
    assert len(initially_reachable) >= count

    for location in numeric_locations:
        location.access_rule = lambda _state: False
    for location in initially_reachable[:count]:
        location.access_rule = lambda _state: True


def _owned_pool_items(multiworld: MultiWorld, player: int, label: str) -> list[Item]:
    return [
        item
        for item in multiworld.itempool
        if item.player == player and item.name == label
    ]


def test_area_key_catalog_uses_stable_contiguous_ids_and_progression_tags() -> None:
    area_keys = sorted(
        (item for item in data.items.values() if "AreaKeys" in item.tags),
        key=lambda item: item.item_id,
    )

    assert [item.item_id for item in area_keys] == list(range(3860041, 3860049))
    assert [item.label for item in area_keys] == list(AREA_KEY_LABELS)
    assert all(item.classification == ItemClassification.progression for item in area_keys)
    assert all("Unique" in item.tags for item in area_keys)
    assert ITEM_GROUPS["AreaKeys"] == set(AREA_KEY_LABELS)


def test_keyed_area_hubs_are_the_eight_always_on_core_landmarks() -> None:
    core_landmarks = sorted(
        (
            location
            for location in data.locations.values()
            if "CoreLandmark" in location.tags
        ),
        key=lambda location: location.location_id,
    )

    assert len(core_landmarks) == 8
    assert {location.category for location in core_landmarks} == {LocationCategory.ROOM_SANITY}
    assert {location.location_id for location in core_landmarks} == {
        3961070,
        3961094,
        3961119,
        3961126,
        3961163,
        3961188,
        3961221,
        3961256,
    }
    assert {location.bit_index for location in core_landmarks} == {
        80,
        104,
        141,
        169,
        189,
        211,
        240,
        253,
    }


def test_core_landmarks_fill_default_capacity_without_duplicating_room_sanity() -> None:
    off_world = setup_multiworld(
        KirbyAmWorld,
        steps=("generate_early", "create_regions", "create_items"),
        seed=40,
        options={"room_sanity": 0},
    )
    on_world = setup_multiworld(
        KirbyAmWorld,
        steps=("generate_early", "create_regions"),
        seed=41,
        options={"room_sanity": 1},
    )

    off_room_locations = [
        location
        for location in off_world.get_locations(1)
        if location.address is not None
        and location.name in {
            metadata.label
            for metadata in data.locations.values()
            if metadata.category == LocationCategory.ROOM_SANITY
        }
    ]
    on_room_locations = [
        location
        for location in on_world.get_locations(1)
        if location.address is not None
        and location.name in {
            metadata.label
            for metadata in data.locations.values()
            if metadata.category == LocationCategory.ROOM_SANITY
        }
    ]

    assert len(off_room_locations) == 8
    assert len(on_room_locations) == sum(
        location.category == LocationCategory.ROOM_SANITY
        for location in data.locations.values()
    )
    assert len({location.address for location in on_room_locations}) == len(on_room_locations)
    assert all(
        len(_owned_pool_items(off_world, 1, label)) == 1
        for label in AREA_KEY_LABELS
    )


def test_area_key_bits_are_destination_area_ids_2_through_9() -> None:
    items = [type("Item", (), {"name": label})() for label in AREA_KEY_LABELS]
    assert area_key_bitfield_from_items(items) == AREA_KEY_BITFIELD_MASK == 0x3FC

    moonlight = type("Item", (), {"name": AREA_KEY_LABEL_BY_AREA_ID[2]})()
    candy = type("Item", (), {"name": AREA_KEY_LABEL_BY_AREA_ID[9]})()
    assert area_key_bitfield_from_items([moonlight, candy]) == (1 << 2) | (1 << 9)


def test_directed_area_key_contract_contains_main_and_room_edges_only_into_areas_2_to_9() -> None:
    gated = area_key_entrance_area_ids()
    assert gated["REGION_RAINBOW_ROUTE/MAIN -> REGION_MOONLIGHT_MANSION/MAIN"] == 2
    assert any("/ROOM_" in entrance_name for entrance_name in gated)
    assert all(area_id in range(2, 10) for area_id in gated.values())
    assert "REGION_MOONLIGHT_MANSION/MAIN -> REGION_RAINBOW_ROUTE/MAIN" not in gated
    assert "REGION_RAINBOW_ROUTE/MAIN -> REGION_DIMENSION_MIRROR/MAIN" not in gated


def test_generate_basic_precollects_moonlight_below_viability_threshold(
    caplog: pytest.LogCaptureFixture,
) -> None:
    multiworld = setup_solo_multiworld(
        KirbyAmWorld,
        steps=_PRE_GENERATE_BASIC_STEPS,
        seed=42,
    )
    world = multiworld.worlds[1]
    _limit_reachable_checks(multiworld, 1, EARLY_REACHABLE_CHECK_THRESHOLD - 1)
    state_without_key = CollectionState(multiworld)
    fourth_reachable_location = next(
        location
        for location in multiworld.get_locations(1)
        if location.address is not None and not location.can_reach(state_without_key)
        and location.parent_region is not None
        and location.parent_region.can_reach(state_without_key)
    )
    fourth_reachable_location.access_rule = (
        lambda state: state.has(FALLBACK_STARTING_AREA_KEY_LABEL, 1)
    )

    original_pool_size = len(multiworld.itempool)
    assert len(_owned_pool_items(multiworld, 1, FALLBACK_STARTING_AREA_KEY_LABEL)) == 1

    with caplog.at_level(logging.INFO):
        world.generate_basic()

    assert len(multiworld.itempool) == original_pool_size
    assert _owned_pool_items(multiworld, 1, FALLBACK_STARTING_AREA_KEY_LABEL) == []
    assert [
        item.name
        for item in multiworld.precollected_items[1]
        if item.name == FALLBACK_STARTING_AREA_KEY_LABEL
    ] == [FALLBACK_STARTING_AREA_KEY_LABEL]
    assert "precollected Moonlight Mansion - Area Key" in caplog.text
    assert world._early_reachable_check_count == EARLY_REACHABLE_CHECK_THRESHOLD - 1
    state_with_key = CollectionState(multiworld)
    assert sum(
        location.address is not None and location.can_reach(state_with_key)
        for location in multiworld.get_locations(1)
    ) == EARLY_REACHABLE_CHECK_THRESHOLD


def test_generate_basic_does_not_precollect_at_viability_threshold() -> None:
    multiworld = setup_solo_multiworld(
        KirbyAmWorld,
        steps=_PRE_GENERATE_BASIC_STEPS,
        seed=43,
    )
    world = multiworld.worlds[1]
    _limit_reachable_checks(multiworld, 1, EARLY_REACHABLE_CHECK_THRESHOLD)

    original_pool_size = len(multiworld.itempool)
    world.generate_basic()

    assert len(multiworld.itempool) == original_pool_size
    assert len(_owned_pool_items(multiworld, 1, FALLBACK_STARTING_AREA_KEY_LABEL)) == 1
    assert not any(
        item.name == FALLBACK_STARTING_AREA_KEY_LABEL
        for item in multiworld.precollected_items[1]
    )


def test_generate_basic_does_not_duplicate_an_existing_starting_moonlight_key() -> None:
    multiworld = setup_solo_multiworld(
        KirbyAmWorld,
        steps=_PRE_GENERATE_BASIC_STEPS,
        seed=46,
    )
    world = multiworld.worlds[1]
    _limit_reachable_checks(multiworld, 1, EARLY_REACHABLE_CHECK_THRESHOLD - 1)
    multiworld.push_precollected(world.create_item(FALLBACK_STARTING_AREA_KEY_LABEL))

    original_pool_size = len(multiworld.itempool)
    original_pool_key_count = len(
        _owned_pool_items(multiworld, 1, FALLBACK_STARTING_AREA_KEY_LABEL)
    )
    world.generate_basic()

    assert len(multiworld.itempool) == original_pool_size
    assert len(_owned_pool_items(multiworld, 1, FALLBACK_STARTING_AREA_KEY_LABEL)) == original_pool_key_count
    assert [
        item.name
        for item in multiworld.precollected_items[1]
        if item.name == FALLBACK_STARTING_AREA_KEY_LABEL
    ] == [FALLBACK_STARTING_AREA_KEY_LABEL]


def test_existing_non_moonlight_key_uses_real_state_reachability_to_avoid_fallback() -> None:
    multiworld = setup_solo_multiworld(
        KirbyAmWorld,
        steps=_PRE_GENERATE_BASIC_STEPS,
        seed=47,
    )
    world = multiworld.worlds[1]
    initially_reachable = [
        location
        for location in multiworld.get_locations(1)
        if location.address is not None and location.can_reach(CollectionState(multiworld))
    ]
    assert len(initially_reachable) >= EARLY_REACHABLE_CHECK_THRESHOLD
    for location in multiworld.get_locations(1):
        if location.address is not None:
            location.access_rule = lambda _state: False
    cabbage_key = AREA_KEY_LABEL_BY_AREA_ID[3]

    def requires_cabbage_key(state: CollectionState, key: str = cabbage_key) -> bool:
        return state.has(key, 1)

    for location in initially_reachable[:EARLY_REACHABLE_CHECK_THRESHOLD]:
        location.access_rule = requires_cabbage_key
    multiworld.push_precollected(world.create_item(cabbage_key))

    world.generate_basic()

    assert world._early_reachable_check_count == EARLY_REACHABLE_CHECK_THRESHOLD
    assert not any(
        item.name == FALLBACK_STARTING_AREA_KEY_LABEL
        for item in multiworld.precollected_items[1]
    )


def test_generate_basic_fallback_is_isolated_per_player() -> None:
    multiworld = setup_multiworld(
        [KirbyAmWorld, KirbyAmWorld],
        steps=_PRE_GENERATE_BASIC_STEPS,
        seed=44,
    )
    _limit_reachable_checks(multiworld, 1, EARLY_REACHABLE_CHECK_THRESHOLD - 1)
    _limit_reachable_checks(multiworld, 2, EARLY_REACHABLE_CHECK_THRESHOLD)

    call_all(multiworld, "generate_basic")

    assert len(_owned_pool_items(multiworld, 1, FALLBACK_STARTING_AREA_KEY_LABEL)) == 0
    assert len(_owned_pool_items(multiworld, 2, FALLBACK_STARTING_AREA_KEY_LABEL)) == 1
    assert area_key_bitfield_from_items(multiworld.precollected_items[1]) == (1 << 2)
    assert area_key_bitfield_from_items(multiworld.precollected_items[2]) == 0


def test_two_player_restrictive_fill_keeps_every_area_key_out_of_its_own_lock() -> None:
    from Fill import distribute_items_restrictive

    multiworld = setup_multiworld(
        [KirbyAmWorld, KirbyAmWorld],
        seed=50,
    )
    distribute_items_restrictive(multiworld)

    assert multiworld.can_beat_game(CollectionState(multiworld))
    area_key_locations = [
        location
        for location in multiworld.get_filled_locations()
        if location.item is not None and location.item.name in AREA_KEY_LABELS
    ]
    assert len(area_key_locations) == 16
    assert any(
        location.item is not None and location.player != location.item.player
        for location in area_key_locations
    )

    filled_locations = multiworld.get_filled_locations()
    for area_key_location in area_key_locations:
        area_key_item = area_key_location.item
        assert area_key_item is not None
        state_without_this_key = CollectionState(multiworld)
        for other_location in filled_locations:
            other_item = other_location.item
            if other_item is not None and other_item is not area_key_item:
                state_without_this_key.collect(other_item, True)
        state_without_this_key.sweep_for_advancements()
        assert area_key_location.can_reach(state_without_this_key), (
            f"{area_key_location.item} self-locked at {area_key_location}"
        )


def test_slot_data_encodes_only_this_players_precollected_area_keys() -> None:
    multiworld = setup_multiworld(
        [KirbyAmWorld, KirbyAmWorld],
        steps=_PRE_GENERATE_BASIC_STEPS,
        seed=45,
    )
    world_one = multiworld.worlds[1]
    world_two = multiworld.worlds[2]
    multiworld.push_precollected(world_one.create_item(AREA_KEY_LABEL_BY_AREA_ID[2]))
    multiworld.push_precollected(world_two.create_item(AREA_KEY_LABEL_BY_AREA_ID[9]))

    assert world_one.fill_slot_data()["starting_area_key_bitfield"] == (1 << 2)
    assert world_two.fill_slot_data()["starting_area_key_bitfield"] == (1 << 9)
    assert world_one.fill_slot_data()["core_landmark_location_ids"] == [
        3961070,
        3961094,
        3961119,
        3961126,
        3961163,
        3961188,
        3961221,
        3961256,
    ]
