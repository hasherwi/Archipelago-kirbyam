"""Seed-side ABI for cosmetic art selected by a physical location's item."""
from collections.abc import Iterable
import struct

from BaseClasses import ItemClassification, Location

from .data import LocationCategory, LocationData, data
from .locations import KirbyAmLocation


# Fixed append-only ROM window reserved by kirby_ap_payload/linker.ld.
REWARD_ART_CONFIG_ROM_OFFSET = 0x100F000
REWARD_ART_CONFIG_SIZE = 0x800
REWARD_ART_CONFIG_MAGIC = b"ARV1"
REWARD_ART_CONFIG_MAX_KEYS = (REWARD_ART_CONFIG_SIZE - 8) // 4
REWARD_ART_CONFIG_EMPTY = REWARD_ART_CONFIG_MAGIC.ljust(REWARD_ART_CONFIG_SIZE, b"\0")

_BIT_INDEXED_CATEGORIES = frozenset({
    LocationCategory.BOSS_DEFEAT,
    LocationCategory.MAP_CHEST,
    LocationCategory.VITALITY_CHEST,
    LocationCategory.SOUND_PLAYER_CHEST,
    LocationCategory.ROOM_SANITY,
    LocationCategory.HUB_SWITCH,
    LocationCategory.AREA_VISIT,
    LocationCategory.LEVER,
    LocationCategory.GOAL_GAME,
})


def reward_art_location_key(location: LocationData) -> int | None:
    """Return the identity observable by the native interaction, not the item ID."""
    if location.category == LocationCategory.MINOR_CHEST:
        index = location.source_rom_offset
    elif location.category in _BIT_INDEXED_CATEGORIES:
        index = location.bit_index
    else:
        return None
    if index is None or not 0 <= index < (1 << 24):
        return None
    return (int(location.category) << 24) | index


def build_reward_art_config(locations: Iterable[Location]) -> bytes:
    """Serialize only trap locations; unlisted physical checks use the generic art.

    Placement is authoritative even for an outgoing (possibly cross-game) item.
    The config does not disclose recipient IDs, names, or item IDs to the ROM.
    """
    keys: set[int] = set()
    for location in locations:
        if not isinstance(location, KirbyAmLocation) or location.key is None or location.address is None:
            continue
        item = location.item
        if item is None or item.code is None or not (item.classification & ItemClassification.trap):
            continue
        location_data = data.locations.get(location.key)
        if location_data is None or location.address != location_data.location_id:
            continue
        key = reward_art_location_key(location_data)
        if key is not None:
            keys.add(key)
    if len(keys) > REWARD_ART_CONFIG_MAX_KEYS:
        raise ValueError(f"Too many Kirby reward art locations: {len(keys)}")
    if not keys:
        return REWARD_ART_CONFIG_EMPTY
    # Always overwrite the entire reserved window, even for seeds without any
    # trap placements, so no previous seed's trailing keys can be retained.
    return (
        struct.pack("<4sI", REWARD_ART_CONFIG_MAGIC, len(keys))
        + b"".join(struct.pack("<I", key) for key in sorted(keys))
    ).ljust(REWARD_ART_CONFIG_SIZE, b"\0")
