"""Seed-exact Universal Tracker reconstruction, independent of UT imports."""
from collections import Counter
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Iterable

from BaseClasses import Item
from .conditional_routes import CANDY_FUSE as candy912_fuse
from .enemy_ability_data import resolve_slot_gateable_abilities
from .options import ExcludeTrapTypes, KirbyAmOptions
from .starting_mirror import starting_mirror_candidates
from .narcolepsy import NARCOLEPSY_ITEM_NAME, NARCOLEPSY_TRAP_CATALOG_VERSION
from .random_teleport import RANDOM_TELEPORT_ITEM_NAME, TRAP_CATALOG_VERSION

TRACKER_SCHEMA_VERSION = 2

TRACKER_OPTIONS = (*KirbyAmOptions.__annotations__, "accessibility", "exclude_locations")

if TYPE_CHECKING:
    from . import KirbyAmWorld


def validate_tracker_data(slot_data: dict[str, Any]) -> dict[str, Any]:
    tracker = slot_data.get("tracker")
    if (not isinstance(tracker, dict)
            or type(version := tracker.get("version")) is not int or version != TRACKER_SCHEMA_VERSION):
        raise ValueError(
            "This Kirby seed does not support tracking with the current rules. "
            "Update the KirbyAM APWorld and generate a new seed for Universal Tracker."
        )
    required = set(TRACKER_OPTIONS) - {"exclude_trap_types", "random_starting_mirror"}  # Older schema-1 seeds used legacy behavior.
    options = tracker.get("options")
    if not isinstance(options, dict) or not required.issubset(options):
        raise ValueError("Incomplete Kirby tracker options; refusing to reroll the seed.")
    version = tracker.get("trap_catalog_version", 0)
    if "trap_catalog_version" in tracker:
        if type(version) is not int or version not in (NARCOLEPSY_TRAP_CATALOG_VERSION, TRAP_CATALOG_VERSION):
            raise ValueError("Unsupported Kirby tracker trap catalog; use the matching APWorld.")
        if "exclude_trap_types" not in options:
            raise ValueError("Missing Kirby tracker exclude_trap_types for this trap catalog.")
    if "exclude_trap_types" in options:
        exclusions = options["exclude_trap_types"]
        if not isinstance(exclusions, list) or any(
            not isinstance(name, str) or name not in ExcludeTrapTypes.valid_keys for name in exclusions
        ):
            raise ValueError("Invalid Kirby tracker exclude_trap_types; expected a list of known trap names.")
        if version < TRAP_CATALOG_VERSION and RANDOM_TELEPORT_ITEM_NAME in exclusions:
            raise ValueError("Kirby tracker lists Random Teleport Trap without its trap catalog version.")
        if version < NARCOLEPSY_TRAP_CATALOG_VERSION and NARCOLEPSY_ITEM_NAME in exclusions:
            raise ValueError("Kirby tracker lists Narcolepsy without its trap catalog version.")
    for key in ("enemy_copy_ability_policy", "goal_configured_area_boss_key",
                "starting_kirby_color", "starting_kirby_color_name"):
        if key not in slot_data:
            raise ValueError(f"Missing Kirby tracker field: {key}")
    candy912_fuse.enabled(slot_data)  # Reject invalid explicit seed intent.
    if not isinstance(tracker.get("precollected_items"), dict):
        raise ValueError("Missing Kirby tracker starting inventory.")
    mirror = options.get("random_starting_mirror", 0)
    if type(mirror) is not int or mirror not in (0, 1):
        raise ValueError("Invalid Kirby tracker Random Starting Mirror option.")
    if mirror and tracker.get("starting_mirror_tutorial_item") not in starting_mirror_candidates(bool(options["area_keys"])):
        raise ValueError("Missing or invalid Kirby tracker tutorial Hub Connection.")
    return tracker


def export_tracker_data(world: "KirbyAmWorld", items: Iterable[Item]) -> dict[str, Any]:
    # Keep resolved Option values separate from client fields, and encode
    # sets in a stable JSON form without changing their generation semantics.
    options = {}
    for name in TRACKER_OPTIONS:
        value = getattr(world.options, name).value
        options[name] = sorted(value) if isinstance(value, (set, frozenset)) else deepcopy(value)
    return {
        "version": TRACKER_SCHEMA_VERSION,
        **({"trap_catalog_version": version} if
           (version := getattr(world, "_tracker_trap_catalog_version", TRAP_CATALOG_VERSION)) else {}),
        # Keep original options separate from resolved client fields.
        "options": options,
        **({"starting_mirror_tutorial_item": reward}
           if (reward := getattr(world, "_starting_mirror_tutorial_item", None)) else {}),
        "precollected_items": dict(Counter(item.name for item in items)),
    }


def restore_tracker_data(world: "KirbyAmWorld", slot_data: dict[str, Any]) -> None:
    tracker = validate_tracker_data(slot_data)
    world._tracker_trap_catalog_version = tracker.get("trap_catalog_version", 0)
    for name, option_type in KirbyAmOptions.type_hints.items():
        if name in TRACKER_OPTIONS:
            # Values were already rolled by generation. Do not call from_any,
            # which permits random choice strings to consume fresh randomness.
            value = deepcopy(tracker["options"].get(name, 0 if name == "random_starting_mirror" else option_type.default))
            setattr(world.options, name, option_type(set(value) if name in {"exclude_locations", "exclude_trap_types"} else value))
    world._starting_mirror_tutorial_item = tracker.get("starting_mirror_tutorial_item")
    world._enemy_copy_ability_policy = deepcopy(slot_data["enemy_copy_ability_policy"])
    world._seed_gateable_abilities = resolve_slot_gateable_abilities(slot_data.get("ability_gateable_abilities"))
    world._candy912_linked_west_fuse = candy912_fuse.enabled(slot_data)
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
