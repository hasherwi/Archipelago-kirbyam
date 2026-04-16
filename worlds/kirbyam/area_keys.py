from __future__ import annotations

import re
from collections import deque
from functools import lru_cache

from .data import LocationCategory, data, load_json_data

EARLY_REACHABLE_CHECK_THRESHOLD = 4
FALLBACK_STARTING_AREA_ID = 2
DIMENSION_MIRROR_MAIN_REGION = "REGION_DIMENSION_MIRROR/MAIN"

AREA_KEY_LABEL_BY_AREA_ID: dict[int, str] = {
    2: "Moonlight Mansion - Area Key",
    3: "Cabbage Cavern - Area Key",
    4: "Mustard Mountain - Area Key",
    5: "Carrot Castle - Area Key",
    6: "Olive Ocean - Area Key",
    7: "Peppermint Palace - Area Key",
    8: "Radish Ruins - Area Key",
    9: "Candy Constellation - Area Key",
}
AREA_KEY_LABELS: tuple[str, ...] = tuple(AREA_KEY_LABEL_BY_AREA_ID[area_id] for area_id in sorted(AREA_KEY_LABEL_BY_AREA_ID))

_REGION_AREA_TOKEN_PATTERN = re.compile(r"^REGION_([A-Z_]+)")
_AREA_TOKEN_TO_AREA_ID: dict[str, int] = {
    "RAINBOW_ROUTE": 1,
    "MOONLIGHT_MANSION": 2,
    "CABBAGE_CAVERN": 3,
    "MUSTARD_MOUNTAIN": 4,
    "CARROT_CASTLE": 5,
    "OLIVE_OCEAN": 6,
    "PEPPERMINT_PALACE": 7,
    "RADISH_RUINS": 8,
    "CANDY_CONSTELLATION": 9,
    "DIMENSION_MIRROR": 10,
}


def area_id_from_region_key(region_key: str) -> int | None:
    match = _REGION_AREA_TOKEN_PATTERN.match(region_key)
    if match is None:
        return None
    return _AREA_TOKEN_TO_AREA_ID.get(match.group(1))


@lru_cache(maxsize=1)
def gated_area_main_entrance_area_ids() -> dict[str, int]:
    gated: dict[str, int] = {}
    for region_name, region_data in data.regions.items():
        if not region_name.endswith("/MAIN"):
            continue
        source_area_id = area_id_from_region_key(region_name)
        if source_area_id is None:
            continue
        for exit_name in region_data.exits:
            if not exit_name.endswith("/MAIN"):
                continue
            destination_area_id = area_id_from_region_key(exit_name)
            if destination_area_id is None:
                continue
            if destination_area_id not in AREA_KEY_LABEL_BY_AREA_ID:
                continue
            if destination_area_id == source_area_id:
                continue
            gated[f"{region_name} -> {exit_name}"] = destination_area_id
    return gated


@lru_cache(maxsize=1)
def gated_room_entrance_area_ids() -> dict[str, int]:
    payload = load_json_data("regions/transitions.json")
    if not isinstance(payload, dict):
        return {}

    transitions = payload.get("transitions", [])
    if not isinstance(transitions, list):
        return {}

    gated: dict[str, int] = {}
    for transition in transitions:
        if not isinstance(transition, dict):
            continue

        source_room = transition.get("source_room")
        destination_room = transition.get("destination_room")
        transport_type = transition.get("transport_type", "")
        if not isinstance(source_room, str) or not isinstance(destination_room, str):
            continue
        if not isinstance(transport_type, str):
            continue
        if "mirror" not in transport_type.lower():
            continue

        source_area_id = area_id_from_region_key(source_room)
        destination_area_id = area_id_from_region_key(destination_room)
        if source_area_id is None or destination_area_id is None:
            continue
        if destination_area_id not in AREA_KEY_LABEL_BY_AREA_ID:
            continue
        if destination_area_id == source_area_id:
            continue

        gated[f"{source_room} -> {destination_room}"] = destination_area_id
    return gated


@lru_cache(maxsize=8)
def early_reachable_location_count(room_sanity_enabled: bool, starting_area_key_bitfield: int = 0) -> int:
    gated_entrances = {}
    gated_entrances.update(gated_area_main_entrance_area_ids())
    gated_entrances.update(gated_room_entrance_area_ids())

    visited: set[str] = set()
    queue = deque(["REGION_GAME_START"])

    while queue:
        current_region = queue.popleft()
        if current_region in visited:
            continue

        region_data = data.regions.get(current_region)
        if region_data is None:
            continue

        visited.add(current_region)

        for exit_name in region_data.exits:
            entrance_name = f"{current_region} -> {exit_name}"
            if exit_name == DIMENSION_MIRROR_MAIN_REGION:
                continue

            gated_area_id = gated_entrances.get(entrance_name)
            if gated_area_id is not None and not (starting_area_key_bitfield & (1 << gated_area_id)):
                continue

            if exit_name not in visited:
                queue.append(exit_name)

    count = 0
    for region_name in visited:
        region_data = data.regions.get(region_name)
        if region_data is None:
            continue
        for loc_key in region_data.locations:
            loc_meta = data.locations.get(loc_key)
            if loc_meta is None:
                continue
            if loc_meta.category == LocationCategory.GOAL:
                continue
            if loc_meta.category == LocationCategory.ROOM_SANITY and not room_sanity_enabled:
                continue
            count += 1
    return count
