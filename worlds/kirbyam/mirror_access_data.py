"""Validate the data shared by generation's Area Key and starting mirror rules."""
from __future__ import annotations

from .data import LocationCategory, data, load_json_data


def _catalog_item(key: str, tag: str):
    item_id = data.item_key_to_id.get(key)
    if item_id is None or tag not in (item := data.items[item_id]).tags:
        raise ValueError(f"Expected a Kirby {tag} catalog item: {key!r}")
    return item


def _edge(row: dict) -> str:
    origin, destination = row["from_region"], row["to_region"]
    if origin not in data.regions or destination not in data.regions[origin].exits:
        raise ValueError(f"Unknown directed Kirby mirror access edge: {origin} -> {destination}")
    return f"{origin} -> {destination}"


def _load_mirror_access():
    payload = load_json_data("mirror_access.json")
    if not isinstance(payload, dict) or type(payload.get("schema")) is not int or payload["schema"] != 1:
        raise ValueError("Unsupported Kirby mirror access schema")

    keys = payload["area_keys"]
    ids, items = keys["region_ids"], keys["key_items"]
    if (any(type(number) is not int or not 0 <= number < 32 for number in ids.values())
            or len(set(ids.values())) != len(ids) or not items.keys() <= ids.keys()):
        raise ValueError("Invalid Kirby Area Key region IDs")
    by_area = {ids[region]: _catalog_item(key, "AreaKeys") for region, key in items.items()}
    if {item.item_id for item in by_area.values()} != {
        item.item_id for item in data.items.values() if "AreaKeys" in item.tags
    } or len({item.item_id for item in by_area.values()}) != len(by_area):
        raise ValueError("Each Kirby Area Key item must belong to one region")
    if any(keys[field] not in items for field in ("starting_key_region", "fallback_key_region")):
        raise ValueError("Kirby starting and fallback key regions must have Area Keys")
    threshold = keys["minimum_early_reachable_checks"]
    if type(threshold) is not int or threshold < 1:
        raise ValueError("Invalid Kirby early-check threshold")
    exclusions = keys["rainbow_return_excluded_source_markers"]
    if not isinstance(exclusions, list) or any(not isinstance(mark, str) or not mark for mark in exclusions):
        raise ValueError("Invalid Kirby Rainbow return source exclusions")
    forced = {}
    for row in keys["forced_route_key_requirements"]:
        edge = _edge(row)
        if edge in forced or row["key_region"] not in items:
            raise ValueError(f"Invalid Kirby forced-route Area Key: {edge}")
        forced[edge] = ids[row["key_region"]]

    start = payload["starting_mirror"]
    start_edge = _edge(start)
    start_item = _catalog_item(start["unlock_item"], "HubConnections")
    reward = data.locations.get(start["tutorial_reward_location"])
    if reward is None or reward.category != LocationCategory.MAP_CHEST:
        raise ValueError("Kirby starting mirror reward must name a map chest")
    if type(start["native_unlock_bit"]) is not int or not 0 < start["native_unlock_bit"] < 32:
        raise ValueError("Invalid Kirby starting mirror unlock bit")
    return keys, by_area, forced, start, start_edge, start_item, reward


(AREA_KEY_CONFIG, AREA_KEY_ITEMS, FORCED_ROUTE_KEYS, STARTING_MIRROR_CONFIG,
 STARTING_MIRROR_EDGE, STARTING_MIRROR_CATALOG_ITEM, TUTORIAL_REWARD_LOCATION) = _load_mirror_access()
