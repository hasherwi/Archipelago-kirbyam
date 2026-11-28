# mypy: ignore-errors
# TODO(typing): retain strict checks in CI while this rules module transitions
# from dynamic rule construction helpers to precise static types.

"""Logic rules for Kirby & The Amazing Mirror.

This implementation is intentionally minimal while the world data model and
client/ROM integration are still in flux.

Current rules:
    - Access to the area graph starts from REGION_GAME_START, which feeds Rainbow
      Route; area-to-area hub exits require the corresponding Hub Connection item.
    - Access to the Dimension Mirror region from Rainbow Route requires collecting
            all 8 Mirror Shards (implemented as 8 progression items).
        - Within the Dimension Mirror:
            * Defeat Dark Meta Knight (Dimension Mirror) is an event available once
                the region is entered (no additional items required beyond the shards gate).
            * Defeat Dark Mind goal location requires: all 8 shards + DMK event.
        - Completion conditions:
            * Dark Mind: collect Defeat Dark Mind.
            * Defeat Any Area Boss: collect Defeat Any Area Boss.
            * Defeat Area Boss: collect Defeat Area Boss after the selected boss
              defeat location becomes reachable.

Goals are locked addressless AP events for generation. The client sends
CLIENT_GOAL after the selected runtime predicate passes; full completion also
requires acknowledgements for its physical checks.
"""

from __future__ import annotations

from collections import deque
from functools import partial
from typing import TYPE_CHECKING

from BaseClasses import CollectionState
from worlds.generic.Rules import add_rule, forbid_items_for_player, set_rule

from .area_keys import (
    AREA_KEY_LABEL_BY_AREA_ID,
    area_key_entrance_area_ids,
    dimension_mirror_entrance_names,
)
from .data import LocationCategory, data, load_json_data, normalize_region_exits
from .generation_logging import logger
from .groups import resolve_item_group
from .options import Goal
from .capture_the_flag import GOAL_EVENT as FLAG_GOAL_EVENT, install_goal_event
from .completion import PHYSICAL_KEYS, REQUIRED_ITEMS, ROOM_REGIONS
from .traversal import CAPABILITY_ABILITIES

if TYPE_CHECKING:
    from . import KirbyAmWorld


def _load_goal_logic():
    payload = load_json_data("goal_logic.json")
    if not isinstance(payload, dict) or type(payload.get("schema")) is not int or payload["schema"] != 1:
        raise ValueError("Unsupported Kirby goal logic schema")
    goals = payload.get("goals")
    if not isinstance(goals, dict) or goals.keys() != set(Goal.name_lookup.values()):
        raise ValueError("Kirby goal logic must declare every supported mode")
    if payload.get("default_goal") not in goals:
        raise ValueError("Unknown default Kirby goal")
    event = payload["dark_mind_prerequisite_event"]
    event_regions = [region.name for region in data.regions.values()
                     if any(item.name == event for item in region.events)]
    if len(event_regions) != 1:
        raise ValueError("Dark Mind prerequisite must name a unique region event")
    modes = {}
    for value, name in Goal.name_lookup.items():
        row = goals[name]
        if value == Goal.option_capture_the_flag:
            if row != {"goal_event": FLAG_GOAL_EVENT}:
                raise ValueError("Invalid Kirby Capture the Flag goal event")
            modes[value] = (row["goal_event"], ())
            continue
        if not isinstance(row, dict) or set(row) != {"goal_location", "all_of"}:
            raise ValueError(f"Invalid Kirby goal declaration: {name}")
        location = data.locations.get(row["goal_location"])
        if location is None or location.category != LocationCategory.GOAL:
            raise ValueError(f"Kirby goal declaration must name a goal location: {name}")
        requirements = row["all_of"]
        if not isinstance(requirements, list) or not requirements:
            raise ValueError(f"Kirby goal must declare requirements: {name}")
        clauses = []
        for requirement in requirements:
            if isinstance(requirement, str) and requirement in {
                "all_shards", "dark_mind_prerequisite_event", "configured_boss",
                "completion_items", "completion_rooms", "completion_checks",
            }:
                clauses.append((requirement, None))
                continue
            if isinstance(requirement, dict) and set(requirement) == {"reachable_bosses"}:
                count = requirement["reachable_bosses"]
                if type(count) is int and 1 <= count <= len(_BOSS_DEFEAT_LOCATION_LABELS):
                    clauses.append(("reachable_bosses", count))
                    continue
                if count == {"option": "required_area_bosses"}:
                    clauses.append(("reachable_bosses", "required_area_bosses"))
                    continue
            raise ValueError(f"Unknown or invalid Kirby goal requirement: {requirement!r}")
        modes[value] = (location.label, tuple(clauses))
    if len({label for label, _ in modes.values()}) != len(modes):
        raise ValueError("Kirby goal modes must bind distinct goal locations")
    return modes, Goal.options[payload["default_goal"]], event, event_regions[0]


# Stable order matches canonical boss bit indices and shard item identity.
_SHARD_ITEM_LABELS = [item.label for item in sorted(data.items.values(), key=lambda item: item.item_id)
                      if "Shards" in item.tags]
_BOSS_DEFEAT_LOCATION_LABELS = [
    loc.label for loc in sorted(data.locations.values(), key=lambda loc: loc.location_id)
    if loc.category == LocationCategory.BOSS_DEFEAT
]
_GOAL_LOGIC, _DEFAULT_GOAL, _DMK_DIMENSION_MIRROR_EVENT, _DMK_EVENT_REGION = _load_goal_logic()
_GOAL_LOCATION_LABELS = {value: label for value, (label, _) in _GOAL_LOGIC.items()}

_ABILITY_GATE_STATUS_VALUES = frozenset({"confirmed", "semantic_candidate", "unconfirmed"})

def _load_compact_room_logic():
    payload = load_json_data("compact_room_logic.json")
    if not isinstance(payload, dict) or type(payload.get("schema")) is not int or payload["schema"] != 1:
        raise ValueError("Unsupported Kirby compact room logic schema")

    def tokens(field):
        values = payload[field]
        if not isinstance(values, list) or not values or any(
            not isinstance(token, str) or not token for token in values
        ) or len(set(values)) != len(values):
            raise ValueError(f"Invalid Kirby compact room token list: {field}")
        return frozenset(values)

    normal = tokens("normal_movement_tokens")
    unreviewed = tokens("legacy_unreviewed_tokens")
    occupied = set(normal | unreviewed)
    if normal & unreviewed:
        raise ValueError("Normal and unreviewed Kirby room tokens overlap")
    canonical_by_alias = {}
    providers_by_gate = {}
    for canonical, row in payload["legacy_capability_aliases"].items():
        room_token, capabilities = row["room_token"], row["provider_capabilities"]
        if (not isinstance(room_token, str) or not room_token or room_token == canonical
                or canonical in occupied or room_token in occupied
                or not isinstance(capabilities, list) or not capabilities
                or any(not isinstance(key, str) or key not in CAPABILITY_ABILITIES for key in capabilities)):
            raise ValueError(f"Invalid Kirby legacy capability alias: {canonical!r}")
        canonical_by_alias.update({canonical: canonical, room_token: canonical})
        providers_by_gate[canonical] = frozenset().union(*(CAPABILITY_ABILITIES[key] for key in capabilities))
        occupied.update((canonical, room_token))
    stake = payload["legacy_stake_transition_gate"]
    if stake not in providers_by_gate:
        raise ValueError("Kirby stake transition must name a legacy capability gate")
    return normal, unreviewed, canonical_by_alias, providers_by_gate, stake


(_NORMAL_MOVEMENT_REQUIREMENTS, _PENDING_ROOM_ABILITY_REQUIREMENTS, _ROOM_ABILITY_GATE_ALIASES,
 _ABILITY_GATE_PLACEHOLDER_SOURCES, _STAKE_TRANSITION_GATE_NAME) = _load_compact_room_logic()


def _load_lever_wall_items() -> dict[str, str]:
    payload = load_json_data("lever_wall_logic.json")
    if not isinstance(payload, dict) or type(payload.get("schema")) is not int or payload["schema"] != 1:
        raise ValueError("Unsupported Kirby lever wall logic schema")
    mapping = payload.get("required_item_by_wall_token")
    if not isinstance(mapping, dict) or not mapping:
        raise ValueError("Kirby lever wall logic must declare required items")
    labels = {}
    for token, item_key in mapping.items():
        if not isinstance(token, str) or not token.endswith("_lever") or not isinstance(item_key, str):
            raise ValueError(f"Invalid Kirby lever wall requirement: {token!r}")
        item_id = data.item_key_to_id.get(item_key)
        item = data.items.get(item_id) if item_id is not None else None
        if item is None or "Levers" not in item.tags:
            raise ValueError(f"Kirby lever wall requirement must name a catalog Lever Wall item: {item_key!r}")
        if item.label in labels.values():
            raise ValueError(f"Duplicate Kirby Lever Wall item: {item_key!r}")
        labels[token] = item.label
    return labels


# Physical lever events report checks; only received AP items unlock walls.
_ROOM_LEVER_WALL_ITEMS = _load_lever_wall_items()


def _has_all_shards(state: CollectionState, player: int) -> bool:
    return state.has_from_list_unique(_SHARD_ITEM_LABELS, player, len(_SHARD_ITEM_LABELS))


def can_complete_dark_mind_sequence(state: CollectionState, player: int) -> bool:
    """Existing reached-boss model, never selected/unselected-goal shortcuts.

    Actual native victory and ordinary Continue are still needed in game. This
    predicate models the opportunity, not a client receipt or equipped Master.
    """
    return (_has_all_shards(state, player)
            and state.can_reach_region(_DMK_EVENT_REGION, player)
            and state.has(_DMK_DIMENSION_MIRROR_EVENT, player))


def install_central_return_rule(world: KirbyAmWorld) -> None:
    from .master_source import CENTRAL_RETURN_EVENT

    # Missing declared event is a schema defect, not an optional goal.
    event = world.multiworld.get_location(CENTRAL_RETURN_EVENT, world.player)
    set_rule(event, lambda state: can_complete_dark_mind_sequence(state, world.player))


def _allow_pending_ability_gate(_state: CollectionState, _player: int, _gate_name: str) -> bool:
    return True


def _legacy_gate_rule(state: CollectionState, player: int, *, name: str) -> bool:
    # The catalog describes provider possibilities, not access to an equipped copy.
    # Source-backed route overlays, not these aliases, enforce reviewed witnesses.
    return _allow_pending_ability_gate(state, player, name)


ABILITY_GATE_RULES = {name: partial(_legacy_gate_rule, name=name)
                      for name in _ABILITY_GATE_PLACEHOLDER_SOURCES}
_ROOM_ABILITY_GATE_RULES = {alias: ABILITY_GATE_RULES[canonical]
                           for alias, canonical in _ROOM_ABILITY_GATE_ALIASES.items()}


def normal_movement_satisfies_requirement(requirement) -> bool:
    """Recognize existing Boolean Normal alternatives without invoking ability gates.

    This proves only the authored compact requirement, not physical geometry,
    equipment carry, or a separately installed traversal target.
    """
    if requirement is None:
        return True
    if isinstance(requirement, str):
        return requirement in _NORMAL_MOVEMENT_REQUIREMENTS
    if isinstance(requirement, dict) and len(requirement) == 1:
        operator, operands = next(iter(requirement.items()))
        if isinstance(operands, list):
            if operator == "all":
                return all(normal_movement_satisfies_requirement(item) for item in operands)
            if operator == "any":
                return any(normal_movement_satisfies_requirement(item) for item in operands)
    return False


def evaluate_room_logic_requirement(requirement, state: CollectionState, player: int) -> bool:
    """Evaluate the compact condition values used by room exits and locations.

    Normal movement needs no Copy Ability acquisition. Other ability-related
    tokens intentionally retain the existing permissive behavior
    until their source-backed predicates are finalized. Every lever token
    requires its matching Lever Wall progression item, not a physical event.
    """
    if requirement is None:
        return True
    if isinstance(requirement, str):
        if requirement in _NORMAL_MOVEMENT_REQUIREMENTS:
            return True
        if requirement in _ROOM_LEVER_WALL_ITEMS:
            return state.has(_ROOM_LEVER_WALL_ITEMS[requirement], player)
        if requirement in _ROOM_ABILITY_GATE_RULES:
            return _ROOM_ABILITY_GATE_RULES[requirement](state, player)
        if requirement in _PENDING_ROOM_ABILITY_REQUIREMENTS:
            return _allow_pending_ability_gate(state, player, requirement)
        raise ValueError(f"Unknown KirbyAM room logic requirement token: {requirement!r}")
    if isinstance(requirement, dict) and len(requirement) == 1:
        operator, operands = next(iter(requirement.items()))
        if operator == "item" and isinstance(operands, str) and operands:
            return state.has(operands, player)
        if isinstance(operands, list):
            if operator == "all":
                return all(evaluate_room_logic_requirement(item, state, player) for item in operands)
            if operator == "any":
                # A declared Normal alternative must not consult an unrelated
                # pending equipment branch just because it appears first.
                return (normal_movement_satisfies_requirement(requirement)
                        or any(evaluate_room_logic_requirement(item, state, player) for item in operands))
    raise TypeError(f"Invalid KirbyAM room logic requirement: {requirement!r}")


def _requirement_contains_token(requirement, token: str) -> bool:
    if requirement == token or (isinstance(requirement, str)
                                and _ROOM_ABILITY_GATE_ALIASES.get(requirement) == token):
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


def _compile_goal_requirements(world: KirbyAmWorld, goal_value: int):
    player = world.player
    label, clauses = _GOAL_LOGIC[goal_value]
    compiled = []
    for kind, argument in clauses:
        if kind == "all_shards":
            compiled.append(lambda state: _has_all_shards(state, player))
        elif kind == "dark_mind_prerequisite_event":
            compiled.append(lambda state: state.has(_DMK_DIMENSION_MIRROR_EVENT, player))
        elif kind == "completion_items":
            compiled.append(lambda state: all(state.has(item.label, player) for item in REQUIRED_ITEMS))
        elif kind == "completion_rooms":
            compiled.append(lambda state: all(any(state.can_reach_region(region, player) for region in regions)
                                              for regions in ROOM_REGIONS))
        elif kind == "completion_checks":
            compiled.append(lambda state: all(state.can_reach_location(data.locations[key].label, player)
                                              for key in PHYSICAL_KEYS))
        elif kind == "reachable_bosses":
            count = getattr(world.options, argument).value if isinstance(argument, str) else argument
            if count == 1:
                compiled.append(lambda state: any(state.can_reach_location(boss, player)
                                                  for boss in _BOSS_DEFEAT_LOCATION_LABELS))
            else:
                compiled.append(lambda state, required=count: sum(state.can_reach_location(boss, player)
                                                                 for boss in _BOSS_DEFEAT_LOCATION_LABELS)
                                >= required)
        elif kind == "configured_boss":
            key = getattr(world, "_resolved_configured_area_boss_goal_key", None)
            target = data.locations.get(key) if isinstance(key, str) else None
            if target is None or target.category != LocationCategory.BOSS_DEFEAT:
                raise ValueError(f"[P{player}] Configured area-boss goal target was not resolved "
                                 f"for goal location {label!r}")
            compiled.append(lambda state, boss=target.label: state.can_reach_location(boss, player))
        else:
            raise ValueError(f"Uncompiled Kirby goal requirement: {kind!r}")
    return lambda state: all(pred(state) for pred in compiled)


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
    goal_label = _GOAL_LOCATION_LABELS.get(goal_value, _GOAL_LOCATION_LABELS[_DEFAULT_GOAL])

    if goal_value not in _GOAL_LOCATION_LABELS:
        logger.warning(
            "[P%s] Unknown goal value %s; defaulting to %s",
            world.player,
            goal_value,
            goal_label,
        )
    else:
        logger.debug("[P%s] Goal mode %s: require %s", world.player, goal_value, goal_label)

    # Every current goal is represented by a locked event location. The access
    # rule below determines when that event can be collected; completion itself
    # consistently requires the selected goal event item.
    world.multiworld.completion_condition[world.player] = (
        lambda state, required_goal=goal_label: state.has(required_goal, world.player)
    )

    if goal_value == Goal.option_capture_the_flag:
        install_goal_event(world)

    from .starting_mirror import STARTING_MIRROR_ENTRANCE, STARTING_MIRROR_ITEM, random_starting_mirror_enabled
    if random_starting_mirror_enabled(world):
        entrance = world.multiworld.get_entrance(STARTING_MIRROR_ENTRANCE, world.player)
        add_rule(entrance, lambda state: state.has(STARTING_MIRROR_ITEM, world.player))

    # Area Keys are directional destination gates.  Use add_rule so an entrance
    # can simultaneously require its destination key and another traversal rule.
    area_keys_option = getattr(world.options, "area_keys", None)
    area_keys_value = getattr(area_keys_option, "value", area_keys_option)
    if area_keys_value is None or bool(area_keys_value):
        area_key_gates = area_key_entrance_area_ids()
        if not area_key_gates:
            raise ValueError("Area Key entrance contract is empty; refusing to generate an ungated world")

        applied_area_key_gates = 0
        for entrance_name, destination_area_id in area_key_gates.items():
            try:
                entrance = world.multiworld.get_entrance(entrance_name, world.player)
            except KeyError as exc:
                raise ValueError(
                    f"[P{world.player}] Canonical Area Key entrance {entrance_name!r} "
                    "was not created; refusing to generate a partially gated world"
                ) from exc

            area_key_label = AREA_KEY_LABEL_BY_AREA_ID[destination_area_id]
            add_rule(
                entrance,
                lambda state, required_key=area_key_label: state.has(required_key, world.player),
            )
            applied_area_key_gates += 1

        logger.debug(
            "[P%s] Applied %s directed Area-Key entrance rule(s)",
            world.player,
            applied_area_key_gates,
        )

    # Preserve the shard requirement on every graph ingress into the Dimension
    # Mirror, not just the coarse Rainbow Route /MAIN edge.
    dimension_mirror_gates = dimension_mirror_entrance_names()
    if not dimension_mirror_gates:
        raise ValueError(
            "Dimension Mirror entrance contract is empty; refusing to generate without shard gates"
        )

    applied_dimension_mirror_gates = 0
    for entrance_name in dimension_mirror_gates:
        try:
            entrance = world.multiworld.get_entrance(entrance_name, world.player)
        except KeyError as exc:
            raise ValueError(
                f"[P{world.player}] Canonical Dimension Mirror entrance {entrance_name!r} "
                "was not created; refusing to generate without every shard gate"
            ) from exc
        add_rule(entrance, shard_gate_rule)
        applied_dimension_mirror_gates += 1

    logger.debug(
        "[P%s] Applied %s Dimension Mirror shard gate(s)",
        world.player,
        applied_dimension_mirror_gates,
    )

    # Apply compact room-edge and location requirements after region creation.
    applied_room_requirements = 0
    compact_requirement_entrances: set[str] = set()
    for source_name, region_data in data.regions.items():
        for destination_name, requirement in region_data.exit_requirements.items():
            requirement_entrance_name = f"{source_name} -> {destination_name}"
            try:
                requirement_entrance = world.multiworld.get_entrance(
                    requirement_entrance_name,
                    world.player,
                )
                add_rule(
                    requirement_entrance,
                    lambda state, required=requirement: evaluate_room_logic_requirement(
                        required,
                        state,
                        world.player,
                    ),
                )
                compact_requirement_entrances.add(requirement_entrance_name)
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
        return ABILITY_GATE_RULES[_STAKE_TRANSITION_GATE_NAME](state, world.player)
    stake_entrance_names = get_stake_gated_transition_entrance_names()
    applied_stake_gates = 0
    for stake_entrance_name in stake_entrance_names:
        try:
            stake_entrance = world.multiworld.get_entrance(stake_entrance_name, world.player)
            # Compact rules already include this capability, possibly inside
            # an all/any expression. Never replace that complete predicate.
            if stake_entrance_name not in compact_requirement_entrances:
                add_rule(stake_entrance, stake_gate_rule)
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

    install_central_return_rule(world)

    from .mini_traversal import install_mini_rules
    install_mini_rules(world)
    from .peg_traversal import install_peg_rules
    install_peg_rules(world)
    from .wheel_traversal import install_wheel_rules
    install_wheel_rules(world)
    from .traversal_rules import install_extra_traversal_rules
    install_extra_traversal_rules(world)
    from .phone_traversal import install_phone_rules
    install_phone_rules(world)

    for goal_location_name in _GOAL_LOCATION_LABELS.values():
        if goal_location_name == FLAG_GOAL_EVENT:  # Installed separately; no static ROM check.
            continue
        try:
            goal_location = world.multiworld.get_location(goal_location_name, world.player)

            # Non-selected goal locations remain as inert runtime events and
            # must not gate accessibility for seeds using a different goal mode.
            if goal_location_name != goal_label:
                set_rule(goal_location, lambda _state: True)
                continue

            selected_goal = goal_value if goal_value in _GOAL_LOGIC else _DEFAULT_GOAL
            set_rule(goal_location, _compile_goal_requirements(world, selected_goal))
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
