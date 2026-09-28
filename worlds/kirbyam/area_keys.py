"""Area Key item and directed entrance contracts.

Area Keys are keyed by the destination area's AP area ID.  Keeping the
direction in this contract is important: returning to Rainbow Route is always
free, while entering one of areas 2 through 9 requires that destination's key.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from functools import lru_cache

from .data import data


EARLY_REACHABLE_CHECK_THRESHOLD = 4
FALLBACK_STARTING_AREA_ID = 2
DIMENSION_MIRROR_AREA_ID = 10

AREA_NAME_BY_ID: dict[int, str] = {
    2: "Moonlight Mansion",
    3: "Cabbage Cavern",
    4: "Mustard Mountain",
    5: "Carrot Castle",
    6: "Olive Ocean",
    7: "Peppermint Palace",
    8: "Radish Ruins",
    9: "Candy Constellation",
}
AREA_KEY_LABEL_BY_AREA_ID: dict[int, str] = {
    area_id: f"{area_name} - Area Key"
    for area_id, area_name in AREA_NAME_BY_ID.items()
}
AREA_KEY_AREA_ID_BY_LABEL: dict[str, int] = {
    label: area_id
    for area_id, label in AREA_KEY_LABEL_BY_AREA_ID.items()
}
AREA_KEY_LABELS: tuple[str, ...] = tuple(
    AREA_KEY_LABEL_BY_AREA_ID[area_id]
    for area_id in sorted(AREA_KEY_LABEL_BY_AREA_ID)
)
AREA_KEY_BITFIELD_MASK = sum(1 << area_id for area_id in AREA_KEY_LABEL_BY_AREA_ID)
FALLBACK_STARTING_AREA_KEY_LABEL = AREA_KEY_LABEL_BY_AREA_ID[FALLBACK_STARTING_AREA_ID]

_REGION_AREA_TOKEN_PATTERN = re.compile(r"^REGION_([A-Z_]+)(?:/|$)")
_AREA_ID_BY_REGION_TOKEN: dict[str, int] = {
    "TUTORIAL": 0,
    "RAINBOW_ROUTE": 1,
    "MOONLIGHT_MANSION": 2,
    "CABBAGE_CAVERN": 3,
    "MUSTARD_MOUNTAIN": 4,
    "CARROT_CASTLE": 5,
    "OLIVE_OCEAN": 6,
    "PEPPERMINT_PALACE": 7,
    "RADISH_RUINS": 8,
    "CANDY_CONSTELLATION": 9,
    "DIMENSION_MIRROR": DIMENSION_MIRROR_AREA_ID,
}


def area_id_from_region_key(region_key: str) -> int | None:
    """Return the AP area ID encoded by a region key, if it has one."""
    match = _REGION_AREA_TOKEN_PATTERN.match(region_key)
    if match is None:
        return None
    return _AREA_ID_BY_REGION_TOKEN.get(match.group(1))


@lru_cache(maxsize=1)
def area_key_entrance_area_ids() -> dict[str, int]:
    """Map every directed cross-area entrance into areas 2..9 to its key ID."""
    gated: dict[str, int] = {}
    for source_region, region_data in data.regions.items():
        source_area_id = area_id_from_region_key(source_region)
        for destination_region in region_data.exits:
            destination_area_id = area_id_from_region_key(destination_region)
            if destination_area_id not in AREA_KEY_LABEL_BY_AREA_ID:
                continue
            if source_area_id == destination_area_id:
                continue
            gated[f"{source_region} -> {destination_region}"] = destination_area_id
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
