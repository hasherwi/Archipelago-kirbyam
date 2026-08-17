# mypy: ignore-errors
# TODO(typing): retain strict checks in CI while this rules module transitions
# from dynamic rule construction helpers to precise static types.

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
            * Defeat Any Area Boss: collect Defeat Any Area Boss.

NOTE: Dark Mind is modeled as an explicit AP goal location.
The client reports this goal location from native AI-state signals and sends
CLIENT_GOAL after server acknowledgement of the selected goal location check.
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING

from BaseClasses import CollectionState
from worlds.generic.Rules import forbid_items_for_player, set_rule

from .data import LocationCategory, data, load_json_data, normalize_region_exits
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
    Goal.option_defeat_any_area_boss: "Defeat Any Area Boss",
    Goal.option_defeat_configured_area_boss: "Defeat Configured Area Boss",
    Goal.option_defeat_random_hidden_area_boss: "Defeat a Hidden Area Boss",
}
_DARK_MIND_GOAL_LABEL = _GOAL_LOCATION_LABELS[Goal.option_dark_mind]
_ANY_AREA_BOSS_GOAL_LABEL = _GOAL_LOCATION_LABELS[Goal.option_defeat_any_area_boss]
_CONFIGURED_AREA_BOSS_GOAL_LABEL = _GOAL_LOCATION_LABELS[Goal.option_defeat_configured_area_boss]
_HIDDEN_RANDOM_AREA_BOSS_GOAL_LABEL = _GOAL_LOCATION_LABELS[Goal.option_defeat_random_hidden_area_boss]

_BOSS_DEFEAT_LOCATION_LABELS = [
    "Mustard Mountain - Boss Defeat",
    "Moonlight Mansion - Boss Defeat",
    "Candy Constellation - Boss Defeat",
    "Olive Ocean - Boss Defeat",
    "Peppermint Palace - Boss Defeat",
    "Cabbage Cavern - Boss Defeat",
    "Carrot Castle - Boss Defeat",
    "Radish Ruins - Boss Defeat",
]

_DMK_DIMENSION_MIRROR_EVENT = "Defeat Dark Meta Knight (Dimension Mirror)"
_ABILITY_GATE_STATUS_VALUES = frozenset({"confirmed", "semantic_candidate", "unconfirmed"})

# These gates intentionally default to True until ability items/statues become
# part of the item pool. The names match the planned logic categories from #37.
_ABILITY_GATE_PLACEHOLDER_SOURCES = {
    "CanCutRopes": frozenset({"Cutter", "Sword", "Cupid", "Smash", "Master"}),
    "CanBreakBlocks": frozenset({"Hammer", "Stone", "Throw", "Burning", "Missile", "UFO", "Smash", "Master"}),
    "CanUseMini": frozenset({"Mini"}),
    "CanLightFuses": frozenset({"Fire", "Burning", "Bomb", "Laser", "UFO", "Master"}),
    "CanPoundPegs": frozenset({"Hammer", "Stone", "Smash", "Master"}),
}

_STAKE_TRANSITION_GATE_NAME = "CanPoundPegs"
_MOONLIGHT_MANSION_LEVER_EVENT = "Activate Lever - Moonlight Mansion 2-11"
_PENDING_ROOM_ABILITY_REQUIREMENTS = frozenset({
    "can_break_block",
    "can_break_floating_block",
    "can_break_metal",
    "can_break_metal_throw",
    "can_climb",
    "can_fly",
    "can_swim",
})


def _has_all_shards(state: CollectionState, player: int) -> bool:
    return state.has_from_list_unique(_SHARD_ITEM_LABELS, player, len(_SHARD_ITEM_LABELS))


def _allow_pending_ability_gate(_state: CollectionState, _player: int, _gate_name: str) -> bool:
    return True


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


def evaluate_room_logic_requirement(requirement, state: CollectionState, player: int) -> bool:
    """Evaluate the compact condition values used by room exits and locations.

    Ability-related tokens intentionally retain the existing permissive behavior
    until their item-specific predicates are finalized. Event requirements are
    enforced now because their progression items already exist.
    """
    if requirement is None:
        return True
    if isinstance(requirement, str):
        if requirement == "mm_lever":
            return state.has(_MOONLIGHT_MANSION_LEVER_EVENT, player)
        if requirement == _STAKE_TRANSITION_GATE_NAME:
            return can_pound_pegs(state, player)
        if requirement == "can_break_block":
            return can_break_blocks(state, player)
        if requirement in _PENDING_ROOM_ABILITY_REQUIREMENTS:
            return _allow_pending_ability_gate(state, player, requirement)
        raise ValueError(f"Unknown KirbyAM room logic requirement token: {requirement!r}")
    if isinstance(requirement, dict) and len(requirement) == 1:
        operator, operands = next(iter(requirement.items()))
        if isinstance(operands, list):
            if operator == "all":
                return all(evaluate_room_logic_requirement(item, state, player) for item in operands)
            if operator == "any":
                return any(evaluate_room_logic_requirement(item, state, player) for item in operands)
    raise TypeError(f"Invalid KirbyAM room logic requirement: {requirement!r}")


def _requirement_contains_token(requirement, token: str) -> bool:
    if requirement == token:
        return True
    if isinstance(requirement, dict):
        return any(
            _requirement_contains_token(operand, token)
            for operands in requirement.values()
            if isinstance(operands, list)
            for operand in operands
        )
    return False


def get_stake_breaking_abilities() -> tuple[str, ...]:
    """Return the reusable hammer peg/stake ability group in deterministic order."""
    return tuple(sorted(_ABILITY_GATE_PLACEHOLDER_SOURCES[_STAKE_TRANSITION_GATE_NAME]))


def get_stake_gated_transition_entrance_names() -> tuple[str, ...]:
    """Return directional entrance names that require the shared stake gate.

    Source of truth is regions/rooms.json path-level exit requirements. Legacy
    transition annotations remain supported during the data migration.
    """
    rooms_payload = load_json_data("regions/rooms.json")
    rooms = rooms_payload if isinstance(rooms_payload, dict) else {}

    entrance_names: set[str] = set()
    for source_room, room_data in rooms.items():
        if not isinstance(source_room, str) or not isinstance(room_data, dict):
            continue
        exits, requirements = normalize_region_exits(source_room, room_data)
        transitions = room_data.get("transitions", [])
        exit_set = {room for room in exits if isinstance(room, str)}
        for destination_room, requirement in requirements.items():
            if _requirement_contains_token(requirement, _STAKE_TRANSITION_GATE_NAME):
                entrance_names.add(f"{source_room} -> {destination_room}")

        if not isinstance(transitions, list):
            continue
        for transition in transitions:
            if not isinstance(transition, dict):
                continue
            destination_room = transition.get("destination_room")
            ability_gate = transition.get("ability_gate")
            if not isinstance(destination_room, str):
                continue
            if ability_gate != _STAKE_TRANSITION_GATE_NAME:
                continue
            if destination_room not in exit_set:
                logger.warning(
                    "Stake transition override references non-exit edge: %s -> %s",
                    source_room,
                    destination_room,
                )
                continue
            entrance_names.add(f"{source_room} -> {destination_room}")

    return tuple(sorted(entrance_names))


def set_rules(world: KirbyAmWorld) -> None:  # noqa: C901
    def shard_gate_rule(state):
        return _has_all_shards(state, world.player)

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
    goal_value = world.options.goal.value
    goal_label = _GOAL_LOCATION_LABELS.get(goal_value, "Defeat Dark Mind")

    if goal_value not in _GOAL_LOCATION_LABELS:
        logger.warning(
            "[P%s] Unknown goal value %s; defaulting to %s",
            world.player,
            goal_value,
            goal_label,
        )
    else:
        logger.debug("[P%s] Goal mode %s: require %s", world.player, goal_value, goal_label)

    if goal_value == Goal.option_defeat_configured_area_boss:
        configured_goal_key = getattr(world, "_resolved_configured_area_boss_goal_key", None)
        configured_goal = data.locations.get(configured_goal_key) if isinstance(configured_goal_key, str) else None
        if configured_goal is None or not isinstance(configured_goal.label, str):
            raise ValueError(
                f"[P{world.player}] Configured area-boss goal target was not resolved for goal mode {goal_value}"
            )
        logger.debug(
            "[P%s] Configured area boss goal mode requires %s (%s)",
            world.player,
            configured_goal.label,
            configured_goal_key,
        )
        world.multiworld.completion_condition[world.player] = (
            lambda state, required_goal=configured_goal.label: state.can_reach_location(required_goal, world.player)
        )
    elif goal_value == Goal.option_defeat_random_hidden_area_boss:
        hidden_goal_key = getattr(world, "_resolved_hidden_area_boss_goal_key", None)
        hidden_goal = data.locations.get(hidden_goal_key) if isinstance(hidden_goal_key, str) else None
        if hidden_goal is None or not isinstance(hidden_goal.label, str):
            logger.warning(
                "[P%s] Hidden area-boss goal target was not resolved; defaulting completion to %s",
                world.player,
                _DARK_MIND_GOAL_LABEL,
            )
            world.multiworld.completion_condition[world.player] = (
                lambda state, required_goal=_DARK_MIND_GOAL_LABEL: state.has(required_goal, world.player)
            )
        else:
            world.multiworld.completion_condition[world.player] = (
                lambda state, required_goal=hidden_goal.label: state.can_reach_location(required_goal, world.player)
            )
    else:
        world.multiworld.completion_condition[world.player] = (
            lambda state, required_goal=goal_label: state.has(required_goal, world.player)
        )

    # Region gating: the name is generated by regions.create_regions()
    entrance_name = "REGION_RAINBOW_ROUTE/MAIN -> REGION_DIMENSION_MIRROR/MAIN"
    try:
        entrance = world.multiworld.get_entrance(entrance_name, world.player)
        set_rule(entrance, shard_gate_rule)
    except KeyError:
        # If the entrance doesn't exist yet (during early iteration), don't block generation.
        logger.debug(
            "[P%s] Entrance %r not found; skipping Dimension Mirror shard gate",
            world.player,
            entrance_name,
        )

    # Apply compact room-edge and location requirements after region creation.
    applied_room_requirements = 0
    for source_name, region_data in data.regions.items():
        for destination_name, requirement in region_data.exit_requirements.items():
            requirement_entrance_name = f"{source_name} -> {destination_name}"
            try:
                requirement_entrance = world.multiworld.get_entrance(
                    requirement_entrance_name,
                    world.player,
                )
                set_rule(
                    requirement_entrance,
                    lambda state, required=requirement: evaluate_room_logic_requirement(
                        required,
                        state,
                        world.player,
                    ),
                )
                applied_room_requirements += 1
            except KeyError:
                logger.debug(
                    "[P%s] Required room entrance %r not found; skipping",
                    world.player,
                    requirement_entrance_name,
                )

        for location_key, requirement in region_data.location_requirements.items():
            location_data = data.locations[location_key]
            try:
                required_location = world.multiworld.get_location(location_data.label, world.player)
                set_rule(
                    required_location,
                    lambda state, required=requirement: evaluate_room_logic_requirement(
                        required,
                        state,
                        world.player,
                    ),
                )
                applied_room_requirements += 1
            except KeyError:
                logger.debug(
                    "[P%s] Required room location %r not found; skipping",
                    world.player,
                    location_data.label,
                )

    logger.debug(
        "[P%s] Applied %s compact room logic requirement(s)",
        world.player,
        applied_room_requirements,
    )

    # Shared stake-gate model (hammer peg) for directional room transitions.
    def stake_gate_rule(state):
        return can_pound_pegs(state, world.player)
    stake_entrance_names = get_stake_gated_transition_entrance_names()
    applied_stake_gates = 0
    for stake_entrance_name in stake_entrance_names:
        try:
            stake_entrance = world.multiworld.get_entrance(stake_entrance_name, world.player)
            set_rule(stake_entrance, stake_gate_rule)
            applied_stake_gates += 1
        except KeyError:
            logger.debug(
                "[P%s] Stake-gated entrance %r not found; skipping",
                world.player,
                stake_entrance_name,
            )

    logger.debug(
        "[P%s] Applied %s stake-gated transition rule(s) using abilities: %s",
        world.player,
        applied_stake_gates,
        ", ".join(get_stake_breaking_abilities()),
    )

    for goal_location_name in _GOAL_LOCATION_LABELS.values():
        try:
            goal_location = world.multiworld.get_location(goal_location_name, world.player)

            # Non-selected goal locations remain as inert runtime events and
            # must not gate accessibility for seeds using a different goal mode.
            if goal_location_name != goal_label:
                set_rule(goal_location, lambda _state: True)
                continue

            if goal_location_name == _DARK_MIND_GOAL_LABEL:
                # Sequenced after Dark Meta Knight within the Dimension Mirror.
                def dmk_rule(state):
                    return (
                        _has_all_shards(state, world.player)
                        and state.has(_DMK_DIMENSION_MIRROR_EVENT, world.player)
                    )
                set_rule(goal_location, dmk_rule)
            elif goal_location_name == _ANY_AREA_BOSS_GOAL_LABEL:
                def any_area_boss_rule(state):
                    return any(
                        state.can_reach_location(location_name, world.player)
                        for location_name in _BOSS_DEFEAT_LOCATION_LABELS
                    )
                set_rule(goal_location, any_area_boss_rule)
            elif goal_location_name == _CONFIGURED_AREA_BOSS_GOAL_LABEL:
                configured_goal_key = getattr(
                    world,
                    "_resolved_configured_area_boss_goal_key",
                    None,
                )
                configured_goal = (
                    data.locations.get(configured_goal_key)
                    if isinstance(configured_goal_key, str)
                    else None
                )
                if configured_goal is None or not isinstance(configured_goal.label, str):
                    raise ValueError(
                        f"[P{world.player}] Configured area-boss goal target was not resolved "
                        f"for goal location {goal_location_name!r}"
                    )

                def configured_area_boss_rule(state):
                    return state.can_reach_location(configured_goal.label, world.player)

                set_rule(goal_location, configured_area_boss_rule)
            elif goal_location_name == _HIDDEN_RANDOM_AREA_BOSS_GOAL_LABEL:
                def hidden_area_boss_rule(state):
                    hidden_goal_key = getattr(world, "_resolved_hidden_area_boss_goal_key", None)
                    hidden_goal = data.locations.get(hidden_goal_key) if isinstance(hidden_goal_key, str) else None
                    return bool(
                        hidden_goal is not None
                        and isinstance(hidden_goal.label, str)
                        and state.can_reach_location(hidden_goal.label, world.player)
                    )

                set_rule(goal_location, hidden_area_boss_rule)
        except KeyError:
            logger.warning(
                "[P%s] Goal location %s not found; goal-specific rule was not applied",
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
        current_region = graph[current]
        if not isinstance(current_region, dict):
            continue
        exits, _requirements = normalize_region_exits(current, current_region)
        for next_room in exits:
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
        locations_payload = region_def.get("locations")
        if not isinstance(room_meta, dict) and isinstance(locations_payload, dict):
            room_meta = locations_payload.get("room_sanity")
        if not isinstance(room_meta, dict) or not bool(room_meta.get("included", False)):
            continue

        match = re.match(r"REGION_[A-Z_]+/ROOM_(\d+)_([A-Z0-9_]+)$", region_name)
        if not match:
            continue

        area_code = int(match.group(1))
        room_code = match.group(2)
        location_name = f"ROOM_SANITY_{area_code}_{room_code}"

        if region_name in world_regions:
            locations = world_regions[region_name].get("locations")
            if isinstance(locations, dict):
                locations.setdefault(location_name, None)
            else:
                if not isinstance(locations, list):
                    locations = []
                    world_regions[region_name]["locations"] = locations
                if location_name not in locations:
                    locations.append(location_name)
