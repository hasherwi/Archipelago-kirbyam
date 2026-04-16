"""Logic rules for Kirby & The Amazing Mirror.

This implementation is intentionally minimal while the world data model and
client/ROM integration are still in flux.

Current rules:
    - Access to Rainbow Route's connected area graph starts from REGION_GAME_START,
            which now only feeds the Rainbow Route hub.
    - Access to the Dimension Mirror region from Rainbow Route requires collecting
            all 8 Mirror Shards (implemented as 8 progression items).
        - Within the Dimension Mirror:
            * Defeat Dark Meta Knight (Dimension Mirror) is an event available once
                the region is entered (no additional items required beyond the shards gate).
            * Defeat Dark Mind goal location requires: all 8 shards + DMK event.
        - Completion conditions:
            * Dark Mind: collect Defeat Dark Mind.

NOTE: Dark Mind is modeled as an explicit AP goal location.
The client reports this goal location from native AI-state signals and sends
CLIENT_GOAL after server acknowledgement of the selected goal location check.
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from BaseClasses import CollectionState
from worlds.generic.Rules import forbid_items_for_player, set_rule

from .area_keys import (
    AREA_KEY_LABEL_BY_AREA_ID,
    gated_area_main_entrance_area_ids,
    gated_room_entrance_area_ids,
)
from .data import LocationCategory, data
from .generation_logging import logger
from .groups import resolve_item_group
from .options import Goal

if TYPE_CHECKING:
    from . import KirbyAmWorld


_SHARD_ITEM_LABELS = [
    "Mustard Mountain - Mirror Shard",
    "Moonlight Mansion - Mirror Shard",
    "Candy Constellation - Mirror Shard",
    "Olive Ocean - Mirror Shard",
    "Peppermint Palace - Mirror Shard",
    "Cabbage Cavern - Mirror Shard",
    "Carrot Castle - Mirror Shard",
    "Radish Ruins - Mirror Shard",
]

_GOAL_LOCATION_LABELS = {
    Goal.option_dark_mind: "Defeat Dark Mind",
}

_DMK_DIMENSION_MIRROR_EVENT = "Defeat Dark Meta Knight (Dimension Mirror)"
_ABILITY_GATE_STATUS_VALUES = frozenset({"confirmed", "semantic_candidate", "unconfirmed"})

_HUB_SWITCH_LOCATION_LABELS = [
    "Peppermint Palace West - Big Switch",
    "Rainbow Route East - Big Switch",
    "Rainbow Route South - Big Switch",
    "Cabbage Cavern Center - Big Switch",
    "Rainbow Route West - Big Switch",
    "Carrot Castle - Big Switch",
    "Rainbow Route North - Big Switch",
    "Mustard Mountain - Big Switch",
    "Cabbage Cavern West - Big Switch",
    "Radish Ruins - Big Switch",
    "Moonlight Mansion - Big Switch",
    "Peppermint Palace East - Big Switch",
    "Cabbage Cavern East - Big Switch",
    "Olive Ocean - Big Switch",
    "Candy Constellation - Big Switch",
]

# Hub mirrors that become available only after the corresponding big switch has
# been pressed in that area. Gate return direction only to avoid progression
# deadlocks in the current graph topology.
_BIG_SWITCH_GATED_HUB_TRANSITIONS = {
    "REGION_MOONLIGHT_MANSION/ROOM_2_GOAL_1 -> REGION_RAINBOW_ROUTE/ROOM_1_HUB_3": "Moonlight Mansion - Big Switch",
    "REGION_CABBAGE_CAVERN/ROOM_3_HUB_3 -> REGION_RAINBOW_ROUTE/ROOM_1_HUB_3": "Cabbage Cavern Center - Big Switch",
    "REGION_CANDY_CONSTELLATION/ROOM_9_HUB -> REGION_RAINBOW_ROUTE/ROOM_1_HUB_3": "Candy Constellation - Big Switch",
    "REGION_PEPPERMINT_PALACE/ROOM_7_15 -> REGION_RAINBOW_ROUTE/ROOM_1_HUB_3": "Peppermint Palace East - Big Switch",
}

_LEVER_EVENTS_BY_TRANSITION = {
    "REGION_MOONLIGHT_MANSION/ROOM_2_11 -> REGION_MOONLIGHT_MANSION/ROOM_2_06": "EVENT_LEVER_MOONLIGHT_ROOM_11",
    "REGION_OLIVE_OCEAN/ROOM_6_13 -> REGION_OLIVE_OCEAN/ROOM_6_14": "EVENT_LEVER_OLIVE_OCEAN_ROOM_13",
    "REGION_CARROT_CASTLE/ROOM_5_05 -> REGION_CARROT_CASTLE/ROOM_5_02": "EVENT_LEVER_CARROT_CASTLE_ROOM_5",
    "REGION_RADISH_RUINS/ROOM_8_12 -> REGION_RADISH_RUINS/ROOM_8_15": "EVENT_LEVER_RADISH_RUINS_ROOM_12",
}

# These gates intentionally default to True until ability items/statues become
# part of the item pool. The names match the planned logic categories from #37.
_ABILITY_GATE_PLACEHOLDER_SOURCES = {
    "CanCutRopes": frozenset({"Cutter", "Sword", "Cupid", "Smash", "Master"}),
    "CanBreakBlocks": frozenset({"Hammer", "Stone", "Throw", "Burning", "Missile", "UFO", "Smash", "Master"}),
    "CanUseMini": frozenset({"Mini"}),
    "CanLightFuses": frozenset({"Fire", "Burning", "Bomb", "Laser", "UFO", "Master"}),
    "CanPoundPegs": frozenset({"Hammer", "Stone", "Smash", "Master"}),
}


def _has_all_shards(state: CollectionState, player: int) -> bool:
    return state.has_from_list_unique(_SHARD_ITEM_LABELS, player, len(_SHARD_ITEM_LABELS))


def _allow_pending_ability_gate(_state: CollectionState, _player: int, _gate_name: str) -> bool:
    return True


def _has_area_key(state: CollectionState, player: int, area_id: int) -> bool:
    area_key_label = AREA_KEY_LABEL_BY_AREA_ID.get(area_id)
    if area_key_label is None:
        return True
    return state.has(area_key_label, player)


def _has_checked_location(state: CollectionState, player: int, location_label: str) -> bool:
    return state.can_reach_location(location_label, player)


def _all_big_switches_pressed(state: CollectionState, player: int) -> bool:
    return all(_has_checked_location(state, player, label) for label in _HUB_SWITCH_LOCATION_LABELS)


def can_cut_ropes(state: CollectionState, player: int) -> bool:
    return _allow_pending_ability_gate(state, player, "CanCutRopes")


def can_break_blocks(state: CollectionState, player: int) -> bool:
    return _allow_pending_ability_gate(state, player, "CanBreakBlocks")


def can_use_mini(state: CollectionState, player: int) -> bool:
    return _allow_pending_ability_gate(state, player, "CanUseMini")


def can_light_fuses(state: CollectionState, player: int) -> bool:
    return _allow_pending_ability_gate(state, player, "CanLightFuses")


def can_pound_pegs(state: CollectionState, player: int) -> bool:
    return _allow_pending_ability_gate(state, player, "CanPoundPegs")


CanCutRopes = can_cut_ropes
CanBreakBlocks = can_break_blocks
CanUseMini = can_use_mini
CanLightFuses = can_light_fuses
CanPoundPegs = can_pound_pegs


ABILITY_GATE_RULES = {
    "CanCutRopes": can_cut_ropes,
    "CanBreakBlocks": can_break_blocks,
    "CanUseMini": can_use_mini,
    "CanLightFuses": can_light_fuses,
    "CanPoundPegs": can_pound_pegs,
}


def get_region_ability_gate_annotations() -> dict[str, dict[str, dict[str, object]]]:
    annotations: dict[str, dict[str, dict[str, object]]] = {}
    for region_name, region_data in data.regions.items():
        if region_data.ability_gates:
            annotations[region_name] = region_data.ability_gates
    return annotations


def set_rules(world: KirbyAmWorld) -> None:
    shard_gate_rule = lambda state: _has_all_shards(state, world.player)

    item_name_groups = getattr(world, "item_name_groups", {})
    shard_items = resolve_item_group(item_name_groups, "Shards", default=_SHARD_ITEM_LABELS)
    get_locations = getattr(world.multiworld, "get_locations", None)
    if callable(get_locations):
        for location in get_locations(world.player):
            key = getattr(location, "key", None)
            if key is None:
                continue
            loc_meta = data.locations.get(key)
            if loc_meta is None or loc_meta.category != LocationCategory.BOSS_DEFEAT:
                continue
            forbid_items_for_player(location, shard_items, world.player)

    # Completion condition
    goal_label = _GOAL_LOCATION_LABELS.get(world.options.goal.value, "Defeat Dark Mind")
    if world.options.goal.value not in _GOAL_LOCATION_LABELS:
        logger.warning(
            "[P%s] Unknown goal value %s; defaulting to %s",
            world.player,
            world.options.goal.value,
            goal_label,
        )
    else:
        logger.debug("[P%s] Goal mode %s: require %s", world.player, world.options.goal.value, goal_label)
    world.multiworld.completion_condition[world.player] = (
        lambda state, required_goal=goal_label: state.has(required_goal, world.player)
    )

    # Region gating: require all shards for every graph entrance into
    # REGION_DIMENSION_MIRROR/MAIN (area graph and room graph).
    dimension_mirror_gate_entrances = sorted(
        f"{region_name} -> {exit_name}"
        for region_name, region_data in data.regions.items()
        for exit_name in region_data.exits
        if exit_name == "REGION_DIMENSION_MIRROR/MAIN"
    )
    for entrance_name in dimension_mirror_gate_entrances:
        try:
            entrance = world.multiworld.get_entrance(entrance_name, world.player)
            set_rule(entrance, shard_gate_rule)
        except KeyError:
            logger.debug(
                "[P%s] Entrance %r not found; skipping Dimension Mirror shard gate",
                world.player,
                entrance_name,
            )

    # Defense in depth: the DMK event location itself also requires all shards.
    # This guarantees sphereing cannot place DMK before shard completion even if
    # any entrance gate regresses.
    try:
        dmk_location = world.multiworld.get_location(_DMK_DIMENSION_MIRROR_EVENT, world.player)
        set_rule(dmk_location, shard_gate_rule)
    except KeyError:
        logger.warning(
            "[P%s] DMK event location %s not found; shard requirement not applied to DMK event",
            world.player,
            _DMK_DIMENSION_MIRROR_EVENT,
        )

    for gated_entrance_name, area_id in gated_area_main_entrance_area_ids().items():
        try:
            entrance = world.multiworld.get_entrance(gated_entrance_name, world.player)
            set_rule(
                entrance,
                lambda state, required_area_id=area_id: _has_area_key(state, world.player, required_area_id),
            )
        except KeyError:
            logger.debug(
                "[P%s] Entrance %r not found; skipping Area Key gate for area %s",
                world.player,
                gated_entrance_name,
                area_id,
            )

    room_gated_entrances = gated_room_entrance_area_ids()
    for gated_entrance_name, area_id in room_gated_entrances.items():
        try:
            entrance = world.multiworld.get_entrance(gated_entrance_name, world.player)
            set_rule(
                entrance,
                lambda state, required_area_id=area_id: _has_area_key(state, world.player, required_area_id),
            )
        except KeyError:
            logger.debug(
                "[P%s] Entrance %r not found; skipping room-level Area Key gate for area %s",
                world.player,
                gated_entrance_name,
                area_id,
            )

    for gated_entrance_name, switch_location_label in _BIG_SWITCH_GATED_HUB_TRANSITIONS.items():
        try:
            entrance = world.multiworld.get_entrance(gated_entrance_name, world.player)
            # If this hub mirror is also gate in room_gated_entrances, combine the rules
            # to require BOTH the Area Key and the big switch.
            if gated_entrance_name in room_gated_entrances:
                required_area_id = room_gated_entrances[gated_entrance_name]
                set_rule(
                    entrance,
                    lambda state, required_area_id=required_area_id, required_switch=switch_location_label: (
                        _has_area_key(state, world.player, required_area_id)
                        and _has_checked_location(state, world.player, required_switch)
                    ),
                )
            else:
                # Hub mirror not in room gates - just require big switch
                set_rule(
                    entrance,
                    lambda state, required_switch=switch_location_label: _has_checked_location(
                        state,
                        world.player,
                        required_switch,
                    ),
                )
        except KeyError:
            logger.debug(
                "[P%s] Entrance %r not found; skipping big-switch gate %s",
                world.player,
                gated_entrance_name,
                switch_location_label,
            )

    # Copy Ability Room unlocks only when all big switches are pressed.
    copy_ability_gate_entrances = sorted(
        f"{region_name} -> {exit_name}"
        for region_name, region_data in data.regions.items()
        for exit_name in region_data.exits
        if region_name == "REGION_RAINBOW_ROUTE/ROOM_1_HUB_4"
        or exit_name == "REGION_RAINBOW_ROUTE/ROOM_1_HUB_4"
    )
    for entrance_name in copy_ability_gate_entrances:
        try:
            entrance = world.multiworld.get_entrance(entrance_name, world.player)
            set_rule(
                entrance,
                lambda state: _all_big_switches_pressed(state, world.player),
            )
        except KeyError:
            logger.debug(
                "[P%s] Entrance %r not found; skipping Copy Ability Room all-switch gate",
                world.player,
                entrance_name,
            )

    for gated_entrance_name, lever_event_name in _LEVER_EVENTS_BY_TRANSITION.items():
        try:
            entrance = world.multiworld.get_entrance(gated_entrance_name, world.player)
            set_rule(
                entrance,
                lambda state, required_event=lever_event_name: state.has(required_event, world.player),
            )
        except KeyError:
            logger.debug(
                "[P%s] Entrance %r not found; skipping lever gate %s",
                world.player,
                gated_entrance_name,
                lever_event_name,
            )

    for goal_location_name in _GOAL_LOCATION_LABELS.values():
        try:
            goal_location = world.multiworld.get_location(goal_location_name, world.player)
            # Require both all shards and the DMK event for the final goal.
            set_rule(
                goal_location,
                lambda state: _has_all_shards(state, world.player)
                and state.has(_DMK_DIMENSION_MIRROR_EVENT, world.player),
            )
        except KeyError:
            logger.warning(
                "[P%s] Goal location %s not found; Dark Meta Knight requirement not applied to this goal",
                world.player,
                goal_location_name,
            )


# ============================================================================
# Room Graph Reachability Queries
# ============================================================================
# rooms.json defines room connectivity and may include non-room-sanity locations
# (for example, boss/chest ownership). Room-sanity binding remains optional.
# These functions allow querying which rooms are reachable from which other rooms.
# The location binding (room-sanity checks) is separate and optional.


def _get_room_graph() -> dict[str, dict]:
    """Load room topology data used for reachability queries."""
    from .data import load_json_data
    return load_json_data("regions/rooms.json")


def _reachable_rooms_from(
    start_region: str,
    graph: dict[str, dict] | None = None,
) -> set[str]:
    """
    BFS to find all rooms reachable from a given start region.
    
    Args:
        start_region: The starting room region name (e.g., "REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE").
        graph: The room graph dict. If None, loads from data.
    
    Returns:
        Set of all reachable room region names.
    """
    if graph is None:
        graph = _get_room_graph()
    
    visited = set()
    queued = {start_region}
    queue = deque([start_region])
    
    while queue:
        current = queue.popleft()
        if current in visited:
            continue
        if current not in graph:
            continue
        
        visited.add(current)
        for next_room in graph[current].get("exits", []):
            if next_room not in visited and next_room not in queued:
                queue.append(next_room)
                queued.add(next_room)
    
    return visited


def _bind_room_sanity_locations(
    world_regions: dict,
    enable_room_sanity: bool = True,
) -> None:
    """
    Optionally bind room-sanity locations to room regions.
    
    Room topology may include non-room-sanity locations; this function selectively
    attaches ROOM_SANITY_* locations to their corresponding room regions.
    
    Args:
        world_regions: The regions dict loaded from data files.
        enable_room_sanity: If True, load and bind room-sanity locations to rooms.
    """
    if not enable_room_sanity:
        return
    
    from .data import load_json_data
    import re
    
    room_regions_topology = load_json_data("regions/rooms.json")

    # Bind each room_sanity-enabled room region to its ROOM_SANITY_* location key.
    for region_name, region_def in room_regions_topology.items():
        if not isinstance(region_def, dict):
            continue
        room_meta = region_def.get("room_sanity")
        if not isinstance(room_meta, dict) or not bool(room_meta.get("included", False)):
            continue

        match = re.match(r"REGION_[A-Z_]+/ROOM_(\d+)_([A-Z0-9_]+)$", region_name)
        if not match:
            continue

        area_code = int(match.group(1))
        room_code = match.group(2)
        location_name = f"ROOM_SANITY_{area_code}_{room_code}"

        if region_name in world_regions:
            if "locations" not in world_regions[region_name]:
                world_regions[region_name]["locations"] = []
            if location_name not in world_regions[region_name]["locations"]:
                world_regions[region_name]["locations"].append(location_name)
