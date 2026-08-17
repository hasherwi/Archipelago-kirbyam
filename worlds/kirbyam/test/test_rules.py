"""Tests for Kirby AM world rule wiring."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest

from .. import KirbyAmWorld
from ..options import ConfiguredAreaBoss, Goal
from ..rules import (
    ABILITY_GATE_RULES,
    evaluate_room_logic_requirement,
    get_stake_breaking_abilities,
    get_stake_gated_transition_entrance_names,
    set_rules,
)


@dataclass
class _FakeOptions:
    goal_value: int
    configured_area_boss_value: int = 7

    @property
    def goal(self):
        class _GoalValue:
            def __init__(self, value: int):
                self.value = value

        return _GoalValue(self.goal_value)

    @property
    def configured_area_boss(self):
        class _ConfiguredAreaBossValue:
            def __init__(self, value: int):
                self.value = value

        return _ConfiguredAreaBossValue(self.configured_area_boss_value)


class _FakeEntrance:
    def __init__(self, name: str, player: int) -> None:
        self.name = name
        self.player = player


class _FakeLocation:
    def __init__(self, name: str, player: int) -> None:
        self.name = name
        self.player = player
        self.access_rule = lambda _state: True  # set_rule writes here


class _FakeMultiWorld:
    def __init__(self) -> None:
        self.completion_condition: dict[int, object] = {}
        self.entrances: dict[tuple[str, int], _FakeEntrance] = {}
        self.locations: dict[tuple[str, int], _FakeLocation] = {}

    def get_entrance(self, name: str, player: int):
        key = (name, player)
        if key not in self.entrances:
            self.entrances[key] = _FakeEntrance(name, player)
        return self.entrances[key]

    def get_location(self, name: str, player: int):
        key = (name, player)
        if key not in self.locations:
            self.locations[key] = _FakeLocation(name, player)
        return self.locations[key]


class _FakeState:
    def __init__(self, owned: set[str] | None = None, reachable_locations: set[str] | None = None) -> None:
        self._owned = owned or set()
        self._reachable_locations = reachable_locations or set()

    def has(self, name: str, _player: int) -> bool:
        return name in self._owned

    def has_from_list_unique(self, names: list[str], _player: int, amount: int) -> bool:
        return len(set(names).intersection(self._owned)) >= amount

    def can_reach_location(self, location_name: str, _player: int) -> bool:
        return location_name in self._reachable_locations


class _FakeWorld:
    def __init__(self, goal_value: int, player: int = 1) -> None:
        self.player = player
        self.options = _FakeOptions(goal_value)
        self.multiworld = _FakeMultiWorld()


def _get_completion_fn(world: _FakeWorld):
    completion_fn = world.multiworld.completion_condition[world.player]
    assert callable(completion_fn)
    return completion_fn


def test_dark_mind_goal_requires_dark_mind_event() -> None:
    world = _FakeWorld(Goal.option_dark_mind)
    set_rules(world)

    completion_fn = _get_completion_fn(world)
    assert not completion_fn(_FakeState())
    assert completion_fn(_FakeState({"Defeat Dark Mind"}))


def test_goal_configured_legacy_name_aliases_to_consolidated_area_boss_mode() -> None:
    assert Goal.from_text("defeat_area_boss").value == Goal.option_defeat_area_boss
    assert Goal.from_text("defeat_configured_area_boss").value == Goal.option_defeat_area_boss


def test_removed_hidden_random_goal_requires_explicit_two_option_replacement() -> None:
    with pytest.raises(KeyError):
        Goal.from_text("defeat_random_hidden_area_boss")


@pytest.mark.parametrize(
    ("option_value", "expected_key"),
    [
        (ConfiguredAreaBoss.option_king_golem, "BOSS_DEFEAT_2"),
        (ConfiguredAreaBoss.option_moley, "BOSS_DEFEAT_6"),
        (ConfiguredAreaBoss.option_kracko, "BOSS_DEFEAT_1"),
        (ConfiguredAreaBoss.option_mega_titan, "BOSS_DEFEAT_7"),
        (ConfiguredAreaBoss.option_gobbler, "BOSS_DEFEAT_4"),
        (ConfiguredAreaBoss.option_wiz, "BOSS_DEFEAT_5"),
        (ConfiguredAreaBoss.option_dark_meta_knight, "BOSS_DEFEAT_8"),
        (ConfiguredAreaBoss.option_master_hand_crazy_hand_pair, "BOSS_DEFEAT_3"),
    ],
)
def test_every_configured_area_boss_maps_to_its_actual_area_defeat_key(
    option_value: int,
    expected_key: str,
) -> None:
    world = KirbyAmWorld.__new__(KirbyAmWorld)
    world.options = SimpleNamespace(configured_area_boss=SimpleNamespace(value=option_value))

    assert KirbyAmWorld._get_resolved_configured_area_boss_goal_key(world) == expected_key


def test_configured_area_boss_framework_random_resolves_to_concrete_boss() -> None:
    # Archipelago reserves the literal `random` for Choice and resolves it during
    # option parsing. The world therefore receives an ordinary concrete boss ID.
    with patch("Options.random.choice", return_value=ConfiguredAreaBoss.option_wiz):
        resolved_option = ConfiguredAreaBoss.from_text("random")

    assert resolved_option.value == ConfiguredAreaBoss.option_wiz

    world = KirbyAmWorld.__new__(KirbyAmWorld)
    world.options = SimpleNamespace(configured_area_boss=resolved_option)
    assert KirbyAmWorld._get_resolved_configured_area_boss_goal_key(world) == "BOSS_DEFEAT_5"


def test_any_area_boss_goal_requires_goal_event_and_event_reaches_after_any_boss() -> None:
    world = _FakeWorld(Goal.option_defeat_any_area_boss)
    set_rules(world)

    completion_fn = _get_completion_fn(world)
    assert not completion_fn(_FakeState())
    assert completion_fn(_FakeState({"Defeat Any Area Boss"}))

    goal_location = world.multiworld.get_location("Defeat Any Area Boss", world.player)
    assert not goal_location.access_rule(_FakeState())
    assert goal_location.access_rule(
        _FakeState(reachable_locations={"Olive Ocean - Boss Defeat"})
    )


def test_area_boss_goal_requires_goal_event_and_selected_boss_access() -> None:
    world = _FakeWorld(Goal.option_defeat_area_boss)
    world._resolved_configured_area_boss_goal_key = "BOSS_DEFEAT_3"
    set_rules(world)

    completion_fn = _get_completion_fn(world)
    assert not completion_fn(_FakeState())
    assert completion_fn(_FakeState({"Defeat Area Boss"}))

    goal_location = world.multiworld.get_location("Defeat Area Boss", world.player)
    assert not goal_location.access_rule(
        _FakeState(reachable_locations={"Mustard Mountain - Boss Defeat"})
    )
    assert goal_location.access_rule(
        _FakeState(reachable_locations={"Candy Constellation - Boss Defeat"})
    )


def test_current_area_goal_events_are_materialized_in_rainbow_route() -> None:
    from ..data import load_json_data

    regions = load_json_data("regions/areas.json")
    rainbow_locations = regions["REGION_RAINBOW_ROUTE/MAIN"]["locations"]

    assert "GOAL_ANY_AREA_BOSS" in rainbow_locations
    assert "GOAL_CONFIGURED_AREA_BOSS" in rainbow_locations
    assert "GOAL_HIDDEN_AREA_BOSS" not in rainbow_locations


def test_unknown_goal_value_defaults_to_dark_mind_completion() -> None:
    world = _FakeWorld(99)
    set_rules(world)

    completion_fn = _get_completion_fn(world)
    assert not completion_fn(_FakeState())
    assert completion_fn(_FakeState({"Defeat Dark Mind"}))


def test_set_rules_applies_shard_gate_to_dimension_mirror_and_goal_events() -> None:
    world = _FakeWorld(Goal.option_dark_mind)

    with patch("worlds.kirbyam.rules.set_rule") as mock_set_rule:
        set_rules(world)

    applied_names = [call.args[0].name for call in mock_set_rule.call_args_list]
    assert "REGION_RAINBOW_ROUTE/MAIN -> REGION_DIMENSION_MIRROR/MAIN" in applied_names
    assert "Defeat Dark Mind" in applied_names


def test_area_topology_routes_start_through_rainbow_route_anchor() -> None:
    from ..data import load_json_data

    regions = load_json_data("regions/areas.json")

    assert regions["REGION_GAME_START"]["exits"] == ["REGION_RAINBOW_ROUTE/MAIN"]

    # Rainbow Route is the hub; connects to all areas that have a hub mirror in
    # the room-level transition data. Olive Ocean and Radish Ruins have no hub
    # mirror to Rainbow Route (they are reached via adjacent areas instead).
    assert set(regions["REGION_RAINBOW_ROUTE/MAIN"]["exits"]) == {
        "REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE",
        "REGION_MUSTARD_MOUNTAIN/MAIN",
        "REGION_MOONLIGHT_MANSION/MAIN",
        "REGION_CANDY_CONSTELLATION/MAIN",
        "REGION_PEPPERMINT_PALACE/MAIN",
        "REGION_CABBAGE_CAVERN/MAIN",
        "REGION_CARROT_CASTLE/MAIN",
        "REGION_DIMENSION_MIRROR/MAIN",
    }

    # Areas connected to Rainbow Route via hub mirror exit back to it.
    for region_name in {
        "REGION_MUSTARD_MOUNTAIN/MAIN",
        "REGION_MOONLIGHT_MANSION/MAIN",
        "REGION_CANDY_CONSTELLATION/MAIN",
        "REGION_PEPPERMINT_PALACE/MAIN",
        "REGION_CABBAGE_CAVERN/MAIN",
        "REGION_CARROT_CASTLE/MAIN",
    }:
        assert "REGION_RAINBOW_ROUTE/MAIN" in regions[region_name]["exits"]

    # Areas reachable only via cross-area mirrors have no direct Rainbow Route exit.
    assert "REGION_RAINBOW_ROUTE/MAIN" not in regions["REGION_OLIVE_OCEAN/MAIN"]["exits"]
    assert "REGION_RAINBOW_ROUTE/MAIN" not in regions["REGION_RADISH_RUINS/MAIN"]["exits"]

    # Cross-area mirror connections derived from rooms.json transitions data.
    assert set(regions["REGION_CABBAGE_CAVERN/MAIN"]["exits"]) >= {
        "REGION_OLIVE_OCEAN/MAIN", "REGION_RADISH_RUINS/MAIN",
    }
    assert "REGION_OLIVE_OCEAN/MAIN" in regions["REGION_MOONLIGHT_MANSION/MAIN"]["exits"]
    assert set(regions["REGION_OLIVE_OCEAN/MAIN"]["exits"]) >= {
        "REGION_CABBAGE_CAVERN/MAIN", "REGION_MOONLIGHT_MANSION/MAIN",
    }
    assert set(regions["REGION_CARROT_CASTLE/MAIN"]["exits"]) >= {
        "REGION_PEPPERMINT_PALACE/MAIN", "REGION_RADISH_RUINS/MAIN",
    }
    assert set(regions["REGION_PEPPERMINT_PALACE/MAIN"]["exits"]) >= {"REGION_CARROT_CASTLE/MAIN"}
    assert set(regions["REGION_RADISH_RUINS/MAIN"]["exits"]) >= {
        "REGION_CABBAGE_CAVERN/MAIN", "REGION_CARROT_CASTLE/MAIN",
    }


def test_room_subareas_pure_topology_with_all_rooms() -> None:
    from ..data import load_json_data, normalize_region_exits

    room_regions = load_json_data("regions/rooms.json")

    assert len(room_regions) == 313

    def room_sanity_metadata(region: dict[str, Any]) -> dict[str, Any]:
        direct = region.get("room_sanity")
        if isinstance(direct, dict):
            return direct
        locations = region.get("locations")
        if isinstance(locations, dict):
            nested = locations.get("room_sanity")
            if isinstance(nested, dict):
                return nested
        return {}

    included_room_sanity = [
        room_sanity_metadata(region).get("included", False)
        for region in room_regions.values()
    ]
    assert sum(1 for included in included_room_sanity if included) == 263

    included_room_sanity_ids = [
        room_sanity_metadata(region)["location_id"]
        for region in room_regions.values()
        if room_sanity_metadata(region).get("included", False)
    ]
    included_room_sanity_bits = [
        room_sanity_metadata(region)["bit_index"]
        for region in room_regions.values()
        if room_sanity_metadata(region).get("included", False)
    ]
    assert len(included_room_sanity_ids) == len(set(included_room_sanity_ids))
    assert len(included_room_sanity_bits) == len(set(included_room_sanity_bits))

    expected_warp_room_sanity = {
        "REGION_RAINBOW_ROUTE/ROOM_1_WARP",
        "REGION_MOONLIGHT_MANSION/ROOM_2_WARP",
        "REGION_MUSTARD_MOUNTAIN/ROOM_4_WARP",
        "REGION_CARROT_CASTLE/ROOM_5_WARP",
        "REGION_PEPPERMINT_PALACE/ROOM_7_WARP",
        "REGION_CANDY_CONSTELLATION/ROOM_9_WARP",
    }
    for region_key in expected_warp_room_sanity:
        room_meta = room_sanity_metadata(room_regions[region_key])
        assert room_meta["included"] is True
        assert isinstance(room_meta["location_id"], int)
        assert isinstance(room_meta["bit_index"], int)

    # Both legacy lists and compact requirement maps normalize to stable
    # adjacency, and every destination resolves to a declared room or area.
    areas = load_json_data("regions/areas.json")
    declared_regions = set(room_regions) | set(areas)
    for room_name, room_def in room_regions.items():
        exits, requirements = normalize_region_exits(room_name, room_def)
        assert set(requirements) <= set(exits)
        assert set(exits) <= declared_regions


def test_room_locations_are_derived_from_locations_json() -> None:
    from ..data import LocationCategory, data

    canonical_room_locations: dict[str, list[str]] = {}
    for loc_key, loc in data.locations.items():
        if loc.category == LocationCategory.ROOM_SANITY:
            continue
        canonical_room_locations.setdefault(loc.parent_region, []).append(loc_key)

    for room_key, expected_locations in canonical_room_locations.items():
        if not room_key.startswith("REGION_") or "/ROOM_" not in room_key or "__LOGIC__" in room_key:
            continue
        actual_locations = [
            loc_key
            for loc_key in data.regions[room_key].locations
            if data.locations[loc_key].category != LocationCategory.ROOM_SANITY
        ]
        assert sorted(actual_locations) == sorted(expected_locations), (
            f"Room {room_key} locations must be derived from locations.json parent_region metadata"
        )


def test_room_subareas_preserve_two_way_and_one_way_transitions() -> None:
    from ..data import load_json_data, normalize_region_exits

    room_regions = load_json_data("regions/rooms.json")

    def exits(room_name: str) -> list[str]:
        return normalize_region_exits(room_name, room_regions[room_name])[0]

    middle = "REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE_MIDDLE_PLATFORMS"
    assert middle in exits("REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE")
    assert "REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE" in exits(middle)

    assert "REGION_RAINBOW_ROUTE/ROOM_1_39" in exits("REGION_RAINBOW_ROUTE/ROOM_1_38")
    assert "REGION_RAINBOW_ROUTE/ROOM_1_38" not in exits("REGION_RAINBOW_ROUTE/ROOM_1_39")


def test_room_reachability_from_start() -> None:
    from ..rules import _reachable_rooms_from

    reachable = _reachable_rooms_from("REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE")

    assert len(reachable) == 287
    assert "REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE" in reachable
    assert "REGION_MOONLIGHT_MANSION/ROOM_2_11_AFTER_LEVER" in reachable
    assert "REGION_CANDY_CONSTELLATION/ROOM_9_20" in reachable


def test_room_sanity_binding_optional() -> None:
    from ..data import load_json_data
    from ..rules import _bind_room_sanity_locations

    room_regions = load_json_data("regions/rooms.json")

    central_locations_before = room_regions["REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE"]["locations"].copy()

    _bind_room_sanity_locations(room_regions, enable_room_sanity=False)
    assert (
        room_regions["REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE"].get("locations", [])
        == central_locations_before
    )

    _bind_room_sanity_locations(room_regions, enable_room_sanity=True)
    assert "ROOM_SANITY_1_CENTRAL_CIRCLE" in room_regions["REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE"]["locations"]
    assert "ROOM_SANITY_1_WARP" in room_regions["REGION_RAINBOW_ROUTE/ROOM_1_WARP"]["locations"]
    assert "ROOM_SANITY_2_WARP" in room_regions["REGION_MOONLIGHT_MANSION/ROOM_2_WARP"]["locations"]
    assert "ROOM_SANITY_4_WARP" in room_regions["REGION_MUSTARD_MOUNTAIN/ROOM_4_WARP"]["locations"]
    assert "ROOM_SANITY_5_WARP" in room_regions["REGION_CARROT_CASTLE/ROOM_5_WARP"]["locations"]
    assert "ROOM_SANITY_7_WARP" in room_regions["REGION_PEPPERMINT_PALACE/ROOM_7_WARP"]["locations"]
    assert "ROOM_SANITY_9_WARP" in room_regions["REGION_CANDY_CONSTELLATION/ROOM_9_WARP"]["locations"]
    assert "ROOM_SANITY_10_01" not in room_regions["REGION_DIMENSION_MIRROR/ROOM_10_01"].get("locations", [])
    assert "ROOM_SANITY_0_01" not in room_regions["REGION_TUTORIAL/ROOM_0_01"].get("locations", [])


ALL_SHARDS = {
    "Mustard Mountain - Mirror Shard",
    "Moonlight Mansion - Mirror Shard",
    "Candy Constellation - Mirror Shard",
    "Olive Ocean - Mirror Shard",
    "Peppermint Palace - Mirror Shard",
    "Cabbage Cavern - Mirror Shard",
    "Carrot Castle - Mirror Shard",
    "Radish Ruins - Mirror Shard",
}
_DMK_EVENT = "Defeat Dark Meta Knight (Dimension Mirror)"


def test_defeat_dark_mind_requires_dmk_event() -> None:
    """Defeat Dark Mind goal location must be blocked without the DMK event."""
    world = _FakeWorld(Goal.option_dark_mind)
    set_rules(world)

    dm_location = world.multiworld.get_location("Defeat Dark Mind", world.player)
    assert callable(dm_location.access_rule)

    # All shards but no DMK event: blocked.
    assert not dm_location.access_rule(_FakeState(ALL_SHARDS))

    # All shards + DMK event: accessible.
    assert dm_location.access_rule(_FakeState(ALL_SHARDS | {_DMK_EVENT}))


def test_defeat_dark_mind_blocked_without_shards() -> None:
    """Defeat Dark Mind goal location requires all 8 shards even with DMK event."""
    world = _FakeWorld(Goal.option_dark_mind)
    set_rules(world)

    dm_location = world.multiworld.get_location("Defeat Dark Mind", world.player)
    assert callable(dm_location.access_rule)

    # DMK event with partial shards: blocked.
    partial_shards = set(list(ALL_SHARDS)[:7])
    assert not dm_location.access_rule(_FakeState(partial_shards | {_DMK_EVENT}))

    # No shards and no DMK: blocked.
    assert not dm_location.access_rule(_FakeState({_DMK_EVENT}))


def test_dmk_event_present_in_dimension_mirror_region() -> None:
    """areas.json must declare the Defeat Dark Meta Knight (Dimension Mirror) event."""
    from ..data import load_json_data

    regions = load_json_data("regions/areas.json")
    dim_region = regions.get("REGION_DIMENSION_MIRROR/MAIN", {})
    assert dim_region, "REGION_DIMENSION_MIRROR/MAIN must exist in areas.json"
    events = dim_region.get("events", [])
    assert _DMK_EVENT in events, (
        f"{_DMK_EVENT!r} event must be declared in REGION_DIMENSION_MIRROR/MAIN events in areas.json"
    )


def test_ability_gate_helpers_default_true_without_ability_items() -> None:
    state = _FakeState()

    for gate_name, gate_rule in ABILITY_GATE_RULES.items():
        assert gate_rule(state, 1), f"{gate_name} should default to True until ability items exist"


def test_compact_room_requirements_enforce_lever_wall_items_and_compose() -> None:
    requirement = {"all": ["can_fly", "can_break_block", "mm_lever"]}

    assert not evaluate_room_logic_requirement(requirement, _FakeState(), 1)
    assert evaluate_room_logic_requirement(
        requirement,
        _FakeState({"Moonlight Mansion 2-11 - Lever Wall"}),
        1,
    )


def test_room_exit_requirements_are_room_local_only() -> None:
    from ..data import load_json_data, normalize_region_exits

    rooms = load_json_data("regions/rooms.json")
    areas = load_json_data("regions/areas.json")

    for room_name, room_def in rooms.items():
        exits, requirements = normalize_region_exits(room_name, room_def)
        assert set(requirements) <= set(exits)

    for area_name, area_def in areas.items():
        assert "exit_requirements" not in area_def, (
            f"Area {area_name} should not have room-level requirements"
        )


def test_logical_exit_overrides_reference_declared_exits() -> None:
    from ..data import load_json_data, normalize_region_exits

    rooms = load_json_data("regions/rooms.json")

    for room_name, room_def in rooms.items():
        exits, _requirements = normalize_region_exits(room_name, room_def)
        exit_set = set(exits)

        logical_exit_overrides = room_def.get("logical_exit_overrides", {})
        if logical_exit_overrides is None:
            logical_exit_overrides = {}
        assert isinstance(logical_exit_overrides, dict), (
            f"Room {room_name} logical_exit_overrides must be a dict when present"
        )

        missing = sorted(str(destination) for destination in logical_exit_overrides if destination not in exit_set)
        assert not missing, (
            f"Room {room_name} logical_exit_overrides includes destinations missing from exits: {missing}"
        )


def test_legacy_split_rooms_define_logical_subregion_metadata() -> None:
    from ..data import load_json_data

    rooms = load_json_data("regions/rooms.json")

    room_9_chest_1 = rooms["REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_1"]
    room_9_chest_2 = rooms["REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_2"]
    assert "locations" not in room_9_chest_1
    assert room_9_chest_2["logical_subregions"]["ENTRY_FROM_9_01"]["exits"] == [
        "REGION_CANDY_CONSTELLATION/ROOM_9_01"
    ]
    assert room_9_chest_2["logical_subregions"]["ENTRY_FROM_9_09"]["exits"] == [
        "REGION_CANDY_CONSTELLATION/ROOM_9_09"
    ]
    assert "locations" not in room_9_chest_2["logical_subregions"]["ENTRY_FROM_9_01"]
    assert "locations" not in room_9_chest_2["logical_subregions"]["ENTRY_FROM_9_09"]
    assert rooms["REGION_CANDY_CONSTELLATION/ROOM_9_01"]["logical_exit_overrides"] == {
        "REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_2": "ENTRY_FROM_9_01"
    }
    assert rooms["REGION_CANDY_CONSTELLATION/ROOM_9_09"]["logical_exit_overrides"] == {
        "REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_2": "ENTRY_FROM_9_09"
    }

    room_8_07 = rooms["REGION_RADISH_RUINS/ROOM_8_07"]
    assert room_8_07["logical_subregions"]["ENTRY_FROM_8_GOAL_1"]["exits"] == [
        "REGION_RADISH_RUINS/ROOM_8_GOAL_1"
    ]
    assert set(room_8_07["logical_subregions"]["ENTRY_FROM_8_18_OR_8_21_OR_8_23"]["exits"]) == {
        "REGION_RADISH_RUINS/ROOM_8_18",
        "REGION_RADISH_RUINS/ROOM_8_21",
        "REGION_RADISH_RUINS/ROOM_8_23",
    }
    assert "logical_exit_overrides" not in rooms["REGION_RADISH_RUINS/ROOM_8_GOAL_1"]

    room_8_09 = rooms["REGION_RADISH_RUINS/ROOM_8_09"]
    assert room_8_09["logical_subregions"]["ENTRY_FROM_8_03"]["exits"] == [
        "REGION_RADISH_RUINS/ROOM_8_04"
    ]
    assert room_8_09["logical_subregions"]["ENTRY_FROM_8_04"]["exits"] == [
        "REGION_RADISH_RUINS/ROOM_8_03"
    ]
    assert rooms["REGION_RADISH_RUINS/ROOM_8_03"]["logical_exit_overrides"] == {
        "REGION_RADISH_RUINS/ROOM_8_09": "ENTRY_FROM_8_03"
    }
    assert rooms["REGION_RADISH_RUINS/ROOM_8_04"]["logical_exit_overrides"] == {
        "REGION_RADISH_RUINS/ROOM_8_09": "ENTRY_FROM_8_04"
    }

    room_5_13 = rooms["REGION_CARROT_CASTLE/ROOM_5_13"]
    assert room_5_13["logical_subregions"]["ENTRY_FROM_5_12"]["exits"] == [
        "REGION_CARROT_CASTLE/ROOM_5_12"
    ]
    assert set(room_5_13["logical_subregions"]["ENTRY_FROM_5_18_OR_5_WARP"]["exits"]) == {
        "REGION_CARROT_CASTLE/ROOM_5_18",
        "REGION_CARROT_CASTLE/ROOM_5_WARP",
    }
    assert rooms["REGION_CARROT_CASTLE/ROOM_5_12"]["logical_exit_overrides"] == {
        "REGION_CARROT_CASTLE/ROOM_5_13": "ENTRY_FROM_5_12"
    }
    assert rooms["REGION_CARROT_CASTLE/ROOM_5_18"]["logical_exit_overrides"] == {
        "REGION_CARROT_CASTLE/ROOM_5_13": "ENTRY_FROM_5_18_OR_5_WARP"
    }
    assert rooms["REGION_CARROT_CASTLE/ROOM_5_WARP"]["logical_exit_overrides"] == {
        "REGION_CARROT_CASTLE/ROOM_5_13": "ENTRY_FROM_5_18_OR_5_WARP"
    }

    room_6_05 = rooms["REGION_OLIVE_OCEAN/ROOM_6_05"]
    assert set(room_6_05["logical_subregions"]["ENTRY_FROM_6_04_OR_6_06"]["exits"]) == {
        "REGION_OLIVE_OCEAN/ROOM_6_04",
        "REGION_OLIVE_OCEAN/ROOM_6_06",
    }
    assert "locations" not in room_6_05["logical_subregions"]["ENTRY_FROM_6_04_OR_6_06"]
    assert room_6_05["logical_subregions"]["ENTRY_FROM_6_23"]["exits"] == [
        "REGION_OLIVE_OCEAN/ROOM_6_23"
    ]
    assert rooms["REGION_OLIVE_OCEAN/ROOM_6_04"]["logical_exit_overrides"] == {
        "REGION_OLIVE_OCEAN/ROOM_6_05": "ENTRY_FROM_6_04_OR_6_06"
    }
    assert rooms["REGION_OLIVE_OCEAN/ROOM_6_06"]["logical_exit_overrides"] == {
        "REGION_OLIVE_OCEAN/ROOM_6_05": "ENTRY_FROM_6_04_OR_6_06"
    }
    assert rooms["REGION_OLIVE_OCEAN/ROOM_6_23"]["logical_exit_overrides"] == {
        "REGION_OLIVE_OCEAN/ROOM_6_05": "ENTRY_FROM_6_23"
    }


def test_area_two_split_rooms_are_first_class_regions() -> None:
    from ..data import data as kirby_data

    assert kirby_data.regions["REGION_MOONLIGHT_MANSION/ROOM_2_05"].exits[-1] == (
        "REGION_MOONLIGHT_MANSION/ROOM_2_07_LOWER"
    )
    assert kirby_data.regions["REGION_MOONLIGHT_MANSION/ROOM_2_07_LOWER"].exits == [
        "REGION_MOONLIGHT_MANSION/ROOM_2_05"
    ]
    assert "REGION_MOONLIGHT_MANSION/ROOM_2_12_LEFT" in (
        kirby_data.regions["REGION_RAINBOW_ROUTE/ROOM_1_08"].exits
    )
    assert kirby_data.regions["REGION_MOONLIGHT_MANSION/ROOM_2_11"].exit_requirements[
        "REGION_MOONLIGHT_MANSION/ROOM_2_11_AFTER_LEVER"
    ] == {"all": ["can_climb", "can_fly", "can_break_block", "mm_lever"]}


def test_logical_exit_overrides_route_to_synthetic_subregions() -> None:
    from ..data import data as kirby_data

    room_9_chest_2_from_9_01 = "REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_2__LOGIC__ENTRY_FROM_9_01"
    room_9_chest_2_from_9_09 = "REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_2__LOGIC__ENTRY_FROM_9_09"
    room_8_07_from_goal_1 = "REGION_RADISH_RUINS/ROOM_8_07__LOGIC__ENTRY_FROM_8_GOAL_1"
    room_8_07_from_8_18_8_21_8_23 = "REGION_RADISH_RUINS/ROOM_8_07__LOGIC__ENTRY_FROM_8_18_OR_8_21_OR_8_23"
    room_8_09_from_8_03 = "REGION_RADISH_RUINS/ROOM_8_09__LOGIC__ENTRY_FROM_8_03"
    room_8_09_from_8_04 = "REGION_RADISH_RUINS/ROOM_8_09__LOGIC__ENTRY_FROM_8_04"
    room_5_13_from_5_12 = "REGION_CARROT_CASTLE/ROOM_5_13__LOGIC__ENTRY_FROM_5_12"
    room_5_13_from_5_18_or_5_warp = "REGION_CARROT_CASTLE/ROOM_5_13__LOGIC__ENTRY_FROM_5_18_OR_5_WARP"
    room_6_05_from_6_04_or_6_06 = "REGION_OLIVE_OCEAN/ROOM_6_05__LOGIC__ENTRY_FROM_6_04_OR_6_06"
    room_6_05_from_6_23 = "REGION_OLIVE_OCEAN/ROOM_6_05__LOGIC__ENTRY_FROM_6_23"

    assert room_9_chest_2_from_9_01 in kirby_data.regions["REGION_CANDY_CONSTELLATION/ROOM_9_01"].exits
    assert room_9_chest_2_from_9_09 in kirby_data.regions["REGION_CANDY_CONSTELLATION/ROOM_9_09"].exits
    assert "REGION_RADISH_RUINS/ROOM_8_07" in kirby_data.regions["REGION_RADISH_RUINS/ROOM_8_GOAL_1"].exits
    assert "REGION_RADISH_RUINS/ROOM_8_07" in kirby_data.regions["REGION_RADISH_RUINS/ROOM_8_18"].exits
    assert "REGION_RADISH_RUINS/ROOM_8_07" in kirby_data.regions["REGION_RADISH_RUINS/ROOM_8_21"].exits
    assert "REGION_RADISH_RUINS/ROOM_8_07" in kirby_data.regions["REGION_RADISH_RUINS/ROOM_8_23"].exits
    assert room_8_09_from_8_03 in kirby_data.regions["REGION_RADISH_RUINS/ROOM_8_03"].exits
    assert room_8_09_from_8_04 in kirby_data.regions["REGION_RADISH_RUINS/ROOM_8_04"].exits
    assert room_5_13_from_5_12 in kirby_data.regions["REGION_CARROT_CASTLE/ROOM_5_12"].exits
    assert room_5_13_from_5_18_or_5_warp in kirby_data.regions["REGION_CARROT_CASTLE/ROOM_5_18"].exits
    assert room_5_13_from_5_18_or_5_warp in kirby_data.regions["REGION_CARROT_CASTLE/ROOM_5_WARP"].exits
    assert room_6_05_from_6_04_or_6_06 in kirby_data.regions["REGION_OLIVE_OCEAN/ROOM_6_04"].exits
    assert room_6_05_from_6_04_or_6_06 in kirby_data.regions["REGION_OLIVE_OCEAN/ROOM_6_06"].exits
    assert room_6_05_from_6_23 in kirby_data.regions["REGION_OLIVE_OCEAN/ROOM_6_23"].exits

    assert kirby_data.regions[room_9_chest_2_from_9_01].exits == ["REGION_CANDY_CONSTELLATION/ROOM_9_01"]
    assert kirby_data.regions[room_9_chest_2_from_9_09].exits == ["REGION_CANDY_CONSTELLATION/ROOM_9_09"]
    assert kirby_data.regions["REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_1"].locations == [
        "SOUND_PLAYER_CHEST",
        "ROOM_SANITY_9_CHEST_1",
    ]
    assert kirby_data.regions[room_9_chest_2_from_9_09].locations == ["VITALITY_CHEST_CANDY_CONSTELLATION"]
    assert kirby_data.regions[room_8_07_from_goal_1].exits == ["REGION_RADISH_RUINS/ROOM_8_GOAL_1"]
    assert set(kirby_data.regions[room_8_07_from_8_18_8_21_8_23].exits) == {
        "REGION_RADISH_RUINS/ROOM_8_18",
        "REGION_RADISH_RUINS/ROOM_8_21",
        "REGION_RADISH_RUINS/ROOM_8_23",
    }
    assert kirby_data.regions[room_8_09_from_8_03].exits == ["REGION_RADISH_RUINS/ROOM_8_04"]
    assert kirby_data.regions[room_8_09_from_8_04].exits == ["REGION_RADISH_RUINS/ROOM_8_03"]
    assert kirby_data.regions[room_5_13_from_5_12].exits == ["REGION_CARROT_CASTLE/ROOM_5_12"]
    assert set(kirby_data.regions[room_5_13_from_5_18_or_5_warp].exits) == {
        "REGION_CARROT_CASTLE/ROOM_5_18",
        "REGION_CARROT_CASTLE/ROOM_5_WARP",
    }
    assert set(kirby_data.regions[room_6_05_from_6_04_or_6_06].exits) == {
        "REGION_OLIVE_OCEAN/ROOM_6_04",
        "REGION_OLIVE_OCEAN/ROOM_6_06",
    }
    assert kirby_data.regions["REGION_OLIVE_OCEAN/ROOM_6_05"].locations == ["ROOM_SANITY_6_05"]
    assert kirby_data.regions[room_6_05_from_6_04_or_6_06].locations == []
    assert kirby_data.regions[room_6_05_from_6_23].exits == ["REGION_OLIVE_OCEAN/ROOM_6_23"]


def test_stake_breaking_abilities_are_shared_and_expected() -> None:
    abilities = get_stake_breaking_abilities()

    assert abilities == tuple(sorted(abilities))
    assert set(abilities) >= {"Hammer", "Master", "Smash", "Stone"}
    assert len(abilities) == len(set(abilities))


def test_stake_gated_transitions_include_candy_one_way_gate() -> None:
    stake_entrances = set(get_stake_gated_transition_entrance_names())

    assert "REGION_CANDY_CONSTELLATION/ROOM_9_06 -> REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_1" in stake_entrances
    assert "REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_1 -> REGION_CANDY_CONSTELLATION/ROOM_9_06" not in stake_entrances


def test_stake_gated_transitions_cover_cross_region_stake_rooms() -> None:
    stake_entrances = set(get_stake_gated_transition_entrance_names())

    assert "REGION_OLIVE_OCEAN/ROOM_6_15 -> REGION_OLIVE_OCEAN/ROOM_6_CHEST_2" in stake_entrances
    assert "REGION_RAINBOW_ROUTE/ROOM_1_HUB_3 -> REGION_MOONLIGHT_MANSION/ROOM_2_GOAL_1" in stake_entrances
    assert "REGION_CANDY_CONSTELLATION/ROOM_9_HUB -> REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_3" in stake_entrances


def test_stake_gated_transitions_come_from_room_exit_requirements() -> None:
    from ..data import load_json_data, normalize_region_exits

    rooms_payload = load_json_data("regions/rooms.json")
    rooms = rooms_payload if isinstance(rooms_payload, dict) else {}
    annotated: set[str] = set()
    for source_room, room_data in rooms.items():
        if not isinstance(source_room, str) or not isinstance(room_data, dict):
            continue
        _exits, requirements = normalize_region_exits(source_room, room_data)
        for destination_room, requirement in requirements.items():
            if requirement == "CanPoundPegs":
                annotated.add(f"{source_room} -> {destination_room}")

    assert annotated
    assert set(get_stake_gated_transition_entrance_names()) == annotated


def test_stake_gated_transitions_ignore_non_stake_non_exit_mismatch_warning() -> None:
    rooms_payload = {
        "REGION_TEST/ROOM_A": {
            "exits": ["REGION_TEST/ROOM_B"],
            "transitions": [
                {
                    "destination_room": "REGION_TEST/ROOM_MISSING",
                    "ability_gate": "CanCutRopes",
                },
                {
                    "destination_room": "REGION_TEST/ROOM_MISSING",
                    "ability_gate": "CanPoundPegs",
                },
            ],
        }
    }

    with patch("worlds.kirbyam.rules.load_json_data", return_value=rooms_payload), \
         patch("worlds.kirbyam.rules.logger.warning") as warning_log:
        assert get_stake_gated_transition_entrance_names() == ()
        warning_log.assert_called_once_with(
            "Stake transition override references non-exit edge: %s -> %s",
            "REGION_TEST/ROOM_A",
            "REGION_TEST/ROOM_MISSING",
        )


def test_stake_gated_transitions_rejects_invalid_exit_shapes() -> None:
    import pytest

    rooms_payload = {
        "REGION_TEST/ROOM_A": {
            "exits": None,
            "transitions": [
                {
                    "destination_room": "REGION_TEST/ROOM_B",
                    "ability_gate": "CanPoundPegs",
                }
            ],
        }
    }

    with patch("worlds.kirbyam.rules.load_json_data", return_value=rooms_payload), \
         pytest.raises(TypeError, match="exits must be a list or object"):
        get_stake_gated_transition_entrance_names()


def test_lever_rooms_define_four_lever_events() -> None:
    from ..data import load_json_data

    rooms = load_json_data("regions/rooms.json")

    assert "Activate Lever - Moonlight Mansion 2-11" in rooms["REGION_MOONLIGHT_MANSION/ROOM_2_11"]["events"]
    assert "Activate Lever - Carrot Castle 5-12" in rooms["REGION_CARROT_CASTLE/ROOM_5_12"]["events"]
    assert "Activate Lever - Olive Ocean 6-13" in rooms["REGION_OLIVE_OCEAN/ROOM_6_13"]["events"]
    assert "Activate Lever - Radish Ruins 8-12" in rooms["REGION_RADISH_RUINS/ROOM_8_12"]["events"]


def test_hub_switch_locations_have_matching_big_switch_events() -> None:
    from ..data import load_json_data

    areas = load_json_data("regions/areas.json")
    locations = load_json_data("locations.json")

    expected_events_by_hub_switch = {
        "HUB_SWITCH_MUSTARD": "Activate Big Switch - Mustard Mountain",
        "HUB_SWITCH_MOONLIGHT": "Activate Big Switch - Moonlight Mansion",
        "HUB_SWITCH_CANDY": "Activate Big Switch - Candy Constellation",
        "HUB_SWITCH_OLIVE": "Activate Big Switch - Olive Ocean",
        "HUB_SWITCH_PEPPERMINT_EAST": "Activate Big Switch - Peppermint Palace East",
        "HUB_SWITCH_PEPPERMINT_WEST": "Activate Big Switch - Peppermint Palace West",
        "HUB_SWITCH_CABBAGE_CAVERN_CENTER": "Activate Big Switch - Cabbage Cavern Center",
        "HUB_SWITCH_CABBAGE_CAVERN_EAST": "Activate Big Switch - Cabbage Cavern East",
        "HUB_SWITCH_CABBAGE_CAVERN_WEST": "Activate Big Switch - Cabbage Cavern West",
        "HUB_SWITCH_CARROT": "Activate Big Switch - Carrot Castle",
        "HUB_SWITCH_RADISH": "Activate Big Switch - Radish Ruins",
        "HUB_SWITCH_RAINBOW_ROUTE_EAST": "Activate Big Switch - Rainbow Route East",
        "HUB_SWITCH_RAINBOW_ROUTE_NORTH": "Activate Big Switch - Rainbow Route North",
        "HUB_SWITCH_RAINBOW_ROUTE_SOUTH": "Activate Big Switch - Rainbow Route South",
        "HUB_SWITCH_RAINBOW_ROUTE_WEST": "Activate Big Switch - Rainbow Route West",
    }

    found_events: set[str] = set()
    for hub_switch_key, expected_event in expected_events_by_hub_switch.items():
        loc_meta = locations.get(hub_switch_key)
        assert isinstance(loc_meta, dict), f"Missing location metadata for {hub_switch_key}"
        parent_region = str(loc_meta.get("parent_region", ""))
        assert "/" in parent_region, f"Invalid parent region for {hub_switch_key}: {parent_region}"

        area_region = parent_region.split("/", 1)[0] + "/MAIN"
        area_data = areas.get(area_region)
        assert isinstance(area_data, dict), f"Missing area region {area_region} for {hub_switch_key}"

        events = area_data.get("events", [])
        assert isinstance(events, list), f"Invalid events list for area {area_region}"
        event_set = {event for event in events if isinstance(event, str)}

        assert expected_event in event_set
        found_events.add(expected_event)

    assert found_events == set(expected_events_by_hub_switch.values())


def test_lever_locations_have_matching_lever_events() -> None:
    from ..data import load_json_data

    rooms = load_json_data("regions/rooms.json")
    locations = load_json_data("locations.json")

    expected_events_by_lever_location = {
        "LEVER_MOONLIGHT_MANSION_2_11": "Activate Lever - Moonlight Mansion 2-11",
        "LEVER_CARROT_CASTLE_5_12": "Activate Lever - Carrot Castle 5-12",
        "LEVER_OLIVE_OCEAN_6_13": "Activate Lever - Olive Ocean 6-13",
        "LEVER_RADISH_RUINS_8_12": "Activate Lever - Radish Ruins 8-12",
    }

    for lever_key, expected_event in expected_events_by_lever_location.items():
        location_meta = locations.get(lever_key)
        assert isinstance(location_meta, dict), f"Missing location metadata for {lever_key}"

        parent_region = str(location_meta.get("parent_region", ""))
        assert parent_region in rooms, f"Missing room region for {lever_key}: {parent_region}"
        room_data = rooms[parent_region]
        assert isinstance(room_data, dict), f"Invalid room payload for {parent_region}"

        events = room_data.get("events", [])
        assert isinstance(events, list), f"Invalid events list for room {parent_region}"
        event_set = {event for event in events if isinstance(event, str)}

        assert expected_event in event_set
