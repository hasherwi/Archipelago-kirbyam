"""Seed-resolved Capture the Flag target and shared slot-data contract."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from BaseClasses import CollectionState, Location, LocationProgressType

from .data import LocationCategory, data
from .options import Goal

if TYPE_CHECKING:
    from . import KirbyAmWorld

GOAL_EVENT = "Capture the Flag"
FLAG_SLOT_KEY = "goal_flag_location_id"
BOSS_FLAG_CONFIG_ROM_OFFSET = 0x1006FF4
_BOSS_FLAG_INDEX = {entry.location_id: entry.bit_index for entry in data.locations.values()
                    if entry.category == LocationCategory.BOSS_DEFEAT and entry.bit_index is not None}


def boss_flag_config(location_id: int | None) -> bytes | None:
    """Only the seed's selected boss, never item ownership, can claim this flag."""
    index = _BOSS_FLAG_INDEX.get(location_id) if location_id is not None else None
    return b"CFB" + bytes([index]) if index is not None and 0 <= index < 8 else None

LOCATION_NAMES = {entry.location_id: entry.label for entry in data.locations.values()
                  if entry.category != LocationCategory.GOAL and type(entry.location_id) is int}


def flag_location_id(slot_data: dict[str, Any]) -> int | None:
    location_id = slot_data.get(FLAG_SLOT_KEY)
    return location_id if type(location_id) is int and location_id in LOCATION_NAMES else None


def active_flag_location_id(slot_data: Any) -> int | None:
    if not isinstance(slot_data, dict) or type(slot_data.get("goal")) is not int:
        return None
    return flag_location_id(slot_data) if slot_data["goal"] == Goal.option_capture_the_flag else None


def eligible_locations(world: KirbyAmWorld) -> tuple[Location, ...]:
    """Enabled numeric checks, excluding anything the host marked excluded."""
    return tuple(location for location in world.multiworld.get_locations(world.player)
                 if location.address in LOCATION_NAMES
                 and location.progress_type != LocationProgressType.EXCLUDED
                 and location.name not in world.options.exclude_locations.value)


def install_goal_event(world: KirbyAmWorld) -> None:
    menu = world.multiworld.get_region(world.origin_region_name, world.player)
    event = Location(world.player, GOAL_EVENT, parent=menu)
    menu.locations.append(event)
    event.place_locked_item(world.create_event(GOAL_EVENT))
    by_id = {location.address: location for location in eligible_locations(world)}

    def can_capture_flag(state: CollectionState) -> bool:
        target = world._flag_location_id
        if target is not None:
            location = by_id.get(target)
            return location is not None and location.can_reach(state)
        # Fill can use any candidate provisionally. This event has no consumers
        # other than the goal and cannot unlock an item or a path to itself.
        return any(location.can_reach(state) for location in by_id.values())

    event.access_rule = can_capture_flag


def resolve_flag(world: KirbyAmWorld) -> int:
    # Sweep actual placements just like the final accessibility audit. Using
    # get_all_state() instead could count a check unlocked by its own item.
    state = CollectionState(world.multiworld)
    state.sweep_for_advancements()
    reachable_ids = sorted(location.address for location in eligible_locations(world)
                           if location.address is not None and location.item is not None and location.can_reach(state))
    if not reachable_ids:
        raise ValueError(f"KirbyAM ({world.player_name}): Capture the Flag has no reachable eligible checks.")
    return world.random.choice(reachable_ids)
