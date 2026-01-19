from typing import Dict, Set

from .data import LocationCategory, data


# Item Groups
ITEM_GROUPS: Dict[str, Set[str]] = {}

for item in data.items.values():
    for tag in item.tags:
        ITEM_GROUPS.setdefault(tag, set()).add(item.label)


# Location Groups
# These map groups are based on location tags. Each group collects all location labels
# that have at least one of the listed map tags.
_LOCATION_GROUP_MAPS: Dict[str, Set[str]] = {
    "0. Game Start": {"MAP_GAME_START"},
    "1. Rainbow Route": {"MAP_RAINBOW_ROUTE"},
    "2. Moonlight Mansion": {"MAP_MOONLIGHT_MANSION"},
    "3. Cabbage Cavern": {"MAP_CABBAGE_CAVERN"},
    "4. Mustard Mountain": {"MAP_MUSTARD_MOUNTAIN"},
    "5. Carrot Castle": {"MAP_CARROT_CASTLE"},
    "6. Olive Ocean": {"MAP_OLIVE_OCEAN"},
    "7. Peppermint Palace": {"MAP_PEPPERMINT_PALACE"},
    "8. Radish Ruins": {"MAP_RADISH_RUINS"},
    "9. Candy Constellation": {"MAP_CANDY_CONSTELLATION"},
    "10. Dimension Mirror": {"MAP_DIMENSION_MIRROR"},
}

_LOCATION_CATEGORY_TO_GROUP_NAME = {
    LocationCategory.SHARD: "Mirror Shards",
}

# Pre-create category groups and map/area groups so they are always present.
LOCATION_GROUPS: Dict[str, Set[str]] = {group_name: set() for group_name in _LOCATION_CATEGORY_TO_GROUP_NAME.values()}
for group_name in _LOCATION_GROUP_MAPS.keys():
    LOCATION_GROUPS.setdefault(group_name, set())

# Build reverse lookup: map tag -> area group(s)
_map_tag_to_area: Dict[str, Set[str]] = {}
for area_name, tags in _LOCATION_GROUP_MAPS.items():
    for t in tags:
        _map_tag_to_area.setdefault(t, set()).add(area_name)

for location in data.locations.values():
    # Category groups (tolerant of incomplete category coverage)
    category_group = _LOCATION_CATEGORY_TO_GROUP_NAME.get(location.category)
    if category_group is not None:
        LOCATION_GROUPS[category_group].add(location.label)

    # Tag groups + map/area groups
    for tag in location.tags:
        LOCATION_GROUPS.setdefault(tag, set()).add(location.label)

        for area_name in _map_tag_to_area.get(tag, ()):  # noqa: SIM401
            LOCATION_GROUPS[area_name].add(location.label)

# Meta-groups
LOCATION_GROUPS["Areas"] = {
    *LOCATION_GROUPS.get("0. Game Start", set()),
    *LOCATION_GROUPS.get("1. Rainbow Route", set()),
    *LOCATION_GROUPS.get("2. Moonlight Mansion", set()),
    *LOCATION_GROUPS.get("3. Cabbage Cavern", set()),
    *LOCATION_GROUPS.get("4. Mustard Mountain", set()),
    *LOCATION_GROUPS.get("5. Carrot Castle", set()),
    *LOCATION_GROUPS.get("6. Olive Ocean", set()),
    *LOCATION_GROUPS.get("7. Peppermint Palace", set()),
    *LOCATION_GROUPS.get("8. Radish Ruins", set()),
    *LOCATION_GROUPS.get("9. Candy Constellation", set()),
    *LOCATION_GROUPS.get("10. Dimension Mirror", set()),
}
