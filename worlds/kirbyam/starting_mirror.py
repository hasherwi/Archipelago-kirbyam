"""AP item and directed gate for the original Central Circle exit."""
from typing import TYPE_CHECKING

from .area_keys import area_key_entrance_area_ids
from .data import data
from .mirror_access_data import (
    STARTING_MIRROR_CATALOG_ITEM, STARTING_MIRROR_CONFIG, STARTING_MIRROR_EDGE,
    TUTORIAL_REWARD_LOCATION,
)

if TYPE_CHECKING:
    from . import KirbyAmWorld

CENTRAL_CIRCLE = STARTING_MIRROR_CONFIG["from_region"]
STARTING_MIRROR_ENTRANCE = STARTING_MIRROR_EDGE
STARTING_MIRROR_ITEM = STARTING_MIRROR_CATALOG_ITEM.label
STARTING_MIRROR_ITEM_ID = STARTING_MIRROR_CATALOG_ITEM.item_id
STARTING_MIRROR_MASK_BIT = STARTING_MIRROR_CONFIG["native_unlock_bit"]
TUTORIAL_WORLD_MAP_KEY = TUTORIAL_REWARD_LOCATION.name
TUTORIAL_WORLD_MAP_NAME = TUTORIAL_REWARD_LOCATION.label


def random_starting_mirror_enabled(world: "KirbyAmWorld") -> bool:
    option = getattr(world.options, "random_starting_mirror", False)
    return bool(getattr(option, "value", option))


def starting_mirror_candidates(area_keys_enabled: bool) -> dict[str, str]:
    """Map eligible rewards to the entrances they open, in stable item order.

    A connection needing an Area Key is not an immediate tutorial exit when
    keys are enabled. Do not rely on a particular start inventory or fallback.
    """
    candidates = {STARTING_MIRROR_ITEM: STARTING_MIRROR_ENTRANCE}
    keyed_edges = area_key_entrance_area_ids() if area_keys_enabled else {}
    for target, rule in data.regions[CENTRAL_CIRCLE].exit_requirements.items():
        edge = f"{CENTRAL_CIRCLE} -> {target}"
        item = rule.get("item") if isinstance(rule, dict) else None
        if (isinstance(item, str) and item.endswith(" - Hub Connection") and edge not in keyed_edges):
            candidates[item] = edge
    return dict(sorted(candidates.items()))
