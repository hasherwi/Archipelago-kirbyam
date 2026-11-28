"""Seed-side ABI for cosmetic art selected by a physical location's item."""
from collections.abc import Iterable
import struct

from BaseClasses import Location

from .data import LocationCategory, LocationData, data
from .generated_hub_switch_contract import HUB_SWITCH_RUNTIME_AP_BIT_BY_LOCATION_KEY
from .locations import KirbyAmLocation
from .reward_art_types import RewardArt, reward_art_for_item


# Fixed append-only ROM window reserved by kirby_ap_payload/linker.ld.
REWARD_ART_CONFIG_ROM_OFFSET = 0x100F000
REWARD_ART_CONFIG_SIZE = 0xA00
REWARD_ART_CONFIG_MAGIC = b"ARV3"
REWARD_ART_CONFIG_MAX_KEYS = 510
REWARD_ART_CONFIG_VARIANT_OFFSET = 8 + 4 * REWARD_ART_CONFIG_MAX_KEYS
REWARD_ART_CONFIG_EMPTY = REWARD_ART_CONFIG_MAGIC.ljust(REWARD_ART_CONFIG_SIZE, b"\0")

_BIT_INDEXED_CATEGORIES = frozenset({
    LocationCategory.BOSS_DEFEAT,
    LocationCategory.MAP_CHEST,
    LocationCategory.VITALITY_CHEST,
    LocationCategory.SOUND_PLAYER_CHEST,
    LocationCategory.ROOM_SANITY,
    LocationCategory.AREA_VISIT,
    LocationCategory.LEVER,
    LocationCategory.GOAL_GAME,
})
# Existing category values 16 and 17 do not fit the four-bit namespace.
# Explicitly remap them to unused namespaces; key zero stays invalid.
_CATEGORY_NAMESPACE_OVERRIDES = {
    LocationCategory.LEVER: 3,
    LocationCategory.GOAL_GAME: 4,
}


def reward_art_location_key(location: LocationData) -> int | None:
    """Return the identity observable by the native interaction, not the item ID."""
    if location.category == LocationCategory.MINOR_CHEST:
        index = location.source_rom_offset
    elif location.category == LocationCategory.HUB_SWITCH:
        index = HUB_SWITCH_RUNTIME_AP_BIT_BY_LOCATION_KEY[location.name]
    elif location.category in _BIT_INDEXED_CATEGORIES:
        index = location.bit_index
    else:
        return None
    if index is None or not 0 <= index < (1 << 24):
        return None
    namespace = _CATEGORY_NAMESPACE_OVERRIDES.get(location.category, int(location.category))
    return (namespace << 24) | index


def build_reward_art_config(locations: Iterable[Location]) -> bytes:
    """Serialize exceptions to generic art, sorted by the masked physical key.

    The config does not disclose recipient IDs, names, or item IDs to the ROM.
    """
    variants: dict[int, RewardArt] = {}
    for location in locations:
        if not isinstance(location, KirbyAmLocation) or location.key is None or location.address is None:
            continue
        art = reward_art_for_item(location.item, location.player)
        if art == RewardArt.GEM:
            continue
        location_data = data.locations.get(location.key)
        if location_data is None or location.address != location_data.location_id:
            continue
        key = reward_art_location_key(location_data)
        if key is not None:
            old = variants.get(key)
            if old is not None and old != art:
                raise ValueError(f"Conflicting Kirby reward art placements for key 0x{key:07X}")
            variants[key] = art
    if len(variants) > REWARD_ART_CONFIG_MAX_KEYS:
        raise ValueError(f"Too many Kirby reward art locations: {len(variants)}")
    if not variants:
        return REWARD_ART_CONFIG_EMPTY
    # Always overwrite the full window, so no trailing entries can carry over.
    buffer = bytearray(REWARD_ART_CONFIG_EMPTY)
    struct.pack_into("<I", buffer, 4, len(variants))
    for index, (key, art) in enumerate(sorted(variants.items())):
        struct.pack_into("<I", buffer, 8 + 4 * index, key)
        buffer[REWARD_ART_CONFIG_VARIANT_OFFSET + index] = art
    return bytes(buffer)
