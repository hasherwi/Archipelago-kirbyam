"""Seed-exact Universal Tracker reconstruction, independent of UT imports."""
from collections import Counter
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Iterable

from BaseClasses import Item
from .options import KirbyAmOptions

TRACKER_OPTIONS = (*KirbyAmOptions.__annotations__, "accessibility", "exclude_locations")

if TYPE_CHECKING:
    from . import KirbyAmWorld


def validate_tracker_data(slot_data: dict[str, Any]) -> dict[str, Any]:
    tracker = slot_data.get("tracker")
    if not isinstance(tracker, dict) or tracker.get("version") != 1:
        raise ValueError(
            "This Kirby slot lacks supported Universal Tracker reconstruction data. "
            "For older seeds use the matching older APWorld and a YAML with resolved "
            "options; shuffled enemy policies may not track correctly. Generate a new "
            "seed with tracker schema 1 for exact YAML-less tracking."
        )
    required = set(TRACKER_OPTIONS) - {"exclude_trap_types"}  # Older schema-1 seeds used the empty default.
    if not required.issubset(tracker.get("options", {})):
        raise ValueError("Incomplete Kirby tracker options; refusing to reroll the seed.")
    for key in ("enemy_copy_ability_policy", "goal_configured_area_boss_key",
                "starting_kirby_color", "starting_kirby_color_name"):
        if key not in slot_data:
            raise ValueError(f"Missing Kirby tracker field: {key}")
    if not isinstance(tracker.get("precollected_items"), dict):
        raise ValueError("Missing Kirby tracker starting inventory.")
    return tracker


def export_tracker_data(world: "KirbyAmWorld", items: Iterable[Item]) -> dict[str, Any]:
    # Keep resolved Option values separate from client fields, and encode
    # sets in a stable JSON form without changing their generation semantics.
    options = {}
    for name in TRACKER_OPTIONS:
        value = getattr(world.options, name).value
        options[name] = sorted(value) if isinstance(value, (set, frozenset)) else deepcopy(value)
    return {
        "version": 1,
        "options": options,
        "precollected_items": dict(Counter(item.name for item in items)),
    }


def restore_tracker_data(world: "KirbyAmWorld", slot_data: dict[str, Any]) -> None:
    tracker = validate_tracker_data(slot_data)
    for name, option_type in KirbyAmOptions.type_hints.items():
        if name in TRACKER_OPTIONS:
            # Values were already rolled by generation. Do not call from_any,
            # which permits random choice strings to consume fresh randomness.
            value = deepcopy(tracker["options"].get(name, option_type.default))
            setattr(world.options, name, option_type(set(value) if name in {"exclude_locations", "exclude_trap_types"} else value))
    world._enemy_copy_ability_policy = deepcopy(slot_data["enemy_copy_ability_policy"])
    world._resolved_configured_area_boss_goal_key = slot_data["goal_configured_area_boss_key"]
    world._resolved_starting_kirby_color_id = slot_data["starting_kirby_color"]
    world._resolved_starting_kirby_color_name = slot_data["starting_kirby_color_name"]
    # Needed while building conditional permission rules. UT removes coded
    # precollects after generation and uses the server's ReceivedItems history.
    # Do not also apply automatic starting abilities/maps or a local YAML inventory.
    world.options.start_inventory.value = deepcopy(tracker["precollected_items"])
    for name, count in tracker["precollected_items"].items():
        for _ in range(count):
            world.push_precollected(world.create_item(name))
