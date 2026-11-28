"""Area Key item and directed entrance contracts.

Area Keys are keyed by the destination area's AP area ID.  Keeping the
direction in this contract is important: a cross-area entrance needs its
destination key, but new seeds start with the Rainbow Route key. Tutorial,
Dimension Mirror, boss and Goal Game returns do not acquire a new Rainbow gate.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from functools import lru_cache

from .data import data
from .mirror_access_data import AREA_KEY_CONFIG, AREA_KEY_ITEMS, FORCED_ROUTE_KEYS


EARLY_REACHABLE_CHECK_THRESHOLD = AREA_KEY_CONFIG["minimum_early_reachable_checks"]
_AREA_ID_BY_REGION_TOKEN = AREA_KEY_CONFIG["region_ids"]
RAINBOW_ROUTE_AREA_ID = _AREA_ID_BY_REGION_TOKEN[AREA_KEY_CONFIG["starting_key_region"]]
RAINBOW_ROUTE_AREA_KEY_ID = AREA_KEY_ITEMS[RAINBOW_ROUTE_AREA_ID].item_id
FALLBACK_STARTING_AREA_ID = _AREA_ID_BY_REGION_TOKEN[AREA_KEY_CONFIG["fallback_key_region"]]
DIMENSION_MIRROR_AREA_ID = _AREA_ID_BY_REGION_TOKEN["DIMENSION_MIRROR"]

AREA_KEY_LABEL_BY_AREA_ID = {area_id: item.label for area_id, item in AREA_KEY_ITEMS.items()}
AREA_NAME_BY_ID = {area_id: label.removesuffix(" - Area Key")
                   for area_id, label in AREA_KEY_LABEL_BY_AREA_ID.items()}
AREA_KEY_AREA_ID_BY_LABEL: dict[str, int] = {
    label: area_id
    for area_id, label in AREA_KEY_LABEL_BY_AREA_ID.items()
}
AREA_KEY_LABELS: tuple[str, ...] = tuple(
    AREA_KEY_LABEL_BY_AREA_ID[area_id]
    for area_id in sorted(AREA_KEY_LABEL_BY_AREA_ID)
)
AREA_KEY_BITFIELD_MASK = sum(1 << area_id for area_id in AREA_KEY_LABEL_BY_AREA_ID)
RAINBOW_ROUTE_AREA_KEY_LABEL = AREA_KEY_LABEL_BY_AREA_ID[RAINBOW_ROUTE_AREA_ID]
FALLBACK_STARTING_AREA_KEY_LABEL = AREA_KEY_LABEL_BY_AREA_ID[FALLBACK_STARTING_AREA_ID]

_REGION_AREA_TOKEN_PATTERN = re.compile(r"^REGION_([A-Z_]+)(?:/|$)")


def area_id_from_region_key(region_key: str) -> int | None:
    """Return the AP area ID encoded by a region key, if it has one."""
    match = _REGION_AREA_TOKEN_PATTERN.match(region_key)
    if match is None:
        return None
    return _AREA_ID_BY_REGION_TOKEN.get(match.group(1))


@lru_cache(maxsize=1)
def area_key_entrance_area_ids() -> dict[str, int]:
    """Map keyed directed cross-area entrances to their destination key ID."""
    gated: dict[str, int] = {}
    for source_region, region_data in data.regions.items():
        source_area_id = area_id_from_region_key(source_region)
        for destination_region in region_data.exits:
            destination_area_id = area_id_from_region_key(destination_region)
            if destination_area_id not in AREA_KEY_LABEL_BY_AREA_ID:
                continue
            if source_area_id == destination_area_id:
                continue
            if destination_area_id == RAINBOW_ROUTE_AREA_ID:
                # Boss and Goal Game return stars aren't area mirrors.
                source_room = source_region.split("/", 1)[-1]
                if source_area_id not in AREA_KEY_ITEMS or any(
                    marker in source_room for marker in AREA_KEY_CONFIG["rainbow_return_excluded_source_markers"]
                ):
                    continue
            gated[f"{source_region} -> {destination_region}"] = destination_area_id
    # Gate admission to forced wind lanes before a player can be stranded at
    # the later cross-area exit. Other room edges retain destination semantics.
    gated.update(FORCED_ROUTE_KEYS)
    return gated


@lru_cache(maxsize=1)
def dimension_mirror_entrance_names() -> tuple[str, ...]:
    """Return every directed entrance into Dimension Mirror from another area."""
    entrance_names: set[str] = set()
    for source_region, region_data in data.regions.items():
        source_area_id = area_id_from_region_key(source_region)
        if source_area_id == DIMENSION_MIRROR_AREA_ID:
            continue
        for destination_region in region_data.exits:
            if area_id_from_region_key(destination_region) == DIMENSION_MIRROR_AREA_ID:
                entrance_names.add(f"{source_region} -> {destination_region}")
    return tuple(sorted(entrance_names))


def area_key_bitfield_from_items(items: Iterable[object]) -> int:
    """Encode precollected Area Keys using their AP destination-area bits."""
    bitfield = 0
    for item in items:
        item_name = getattr(item, "name", None)
        area_id = AREA_KEY_AREA_ID_BY_LABEL.get(item_name) if isinstance(item_name, str) else None
        if area_id is not None:
            bitfield |= 1 << area_id
    return bitfield & AREA_KEY_BITFIELD_MASK
