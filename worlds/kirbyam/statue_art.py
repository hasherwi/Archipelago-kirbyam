"""Seed-specific ability-statue visuals for the USA ROM (issue #824).

The grant tables and animation selectors are independent. Keep the grant bytes
and all native callbacks intact; redirect only the 19 regular AnimInfo records.
Custom icons extend animation 0x384, sharing its native 16x16 frame and palette.
"""
from __future__ import annotations

import json
import pkgutil
import struct

from .enemy_ability_data import ABILITY_NAME_TO_ID

STATUE_VISUAL_MODE_FILE = "statue_visual_mode.bin"
CUSTOM_STATUE_ABILITIES = ("Cook", "Crash", "Magic", "Mini", "Sleep", "UFO", "?")
GRANT_TABLE_OFFSET = 0x3538FC
ANIM_INFO_OFFSET = 0x35369C
ANIM_POINTER_OFFSET = 0x448574 + 0x384 * 4
NATIVE_ANIM_TABLE_OFFSET = 0x440A0C
NATIVE_SCRIPT_OFFSET = 0x4405B0
TILES_BASE = 0x4BED4C
ROM_BASE = 0x08000000
NATIVE_VARIANT_COUNT = 31


def parse_native_statues(abilities: dict[str, object]) -> tuple[tuple[str, int], ...]:
    """Read the explicit USA regular-statue map; null means no verified entry.

    Offsets are file offsets, never GBA pointers. Require the complete known
    layout so a typo cannot silently redirect another object's animation.
    """
    slots: dict[int, tuple[str, int]] = {}
    for name, entry in abilities.items():
        if not isinstance(entry, dict) or "native_regular_statue" not in entry:
            raise ValueError(f"Missing native_regular_statue declaration for {name}")
        native = entry["native_regular_statue"]
        if native is None:
            continue
        if not isinstance(native, dict) or set(native) != {
                "grant_rom_offset", "animation_info_rom_offset", "animation_id", "animation_variant"}:
            raise ValueError(f"Invalid native statue metadata for {name}")
        try:
            grant = int(native["grant_rom_offset"], 16)
            info = int(native["animation_info_rom_offset"], 16)
            anim, variant = native["animation_id"], native["animation_variant"]
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid native statue offsets for {name}") from exc
        slot = grant - GRANT_TABLE_OFFSET
        if (name not in ABILITY_NAME_TO_ID or not 0 <= slot < 19 or slot in slots
                or info != ANIM_INFO_OFFSET + slot * 4 or anim != 0x384
                or type(variant) is not int or not 11 <= variant <= 29):
            raise ValueError(f"Native statue metadata does not match USA layout: {name}")
        slots[slot] = (name, variant)
    if set(slots) != set(range(19)) or {v for _, v in slots.values()} != set(range(11, 30)):
        raise ValueError("Native statue map must cover 19 distinct slots and variants")
    return tuple(slots[i] for i in range(19))


_metadata = pkgutil.get_data(__name__, "data/abilities.json")
if _metadata is None:
    raise FileNotFoundError("Missing abilities.json")
_NATIVE_STATUES = parse_native_statues(json.loads(_metadata))
NATIVE_STATUE_ABILITIES = tuple(name for name, _ in _NATIVE_STATUES)
NATIVE_VARIANTS = tuple(variant for _, variant in _NATIVE_STATUES)


def load_statue_pixels() -> dict[str, tuple[str, ...]]:
    raw = pkgutil.get_data(__name__, "data/statue_art.json")
    if raw is None:
        raise FileNotFoundError("Missing statue_art.json")
    sprites = json.loads(raw)["sprites"]
    if set(sprites) != set(CUSTOM_STATUE_ABILITIES):
        raise ValueError("Statue art must contain all six abilities and ?")
    result = {}
    for name in CUSTOM_STATUE_ABILITIES:
        rows = sprites[name]
        if (len(rows) != 16 or any(len(row) != 16 for row in rows)
                or any(pixel not in ".123456789ABCDEF" for row in rows for pixel in row)):
            raise ValueError(f"Invalid 16x16 indexed statue art: {name}")
        result[name] = tuple(rows)
    return result


def encode_statue_tiles(rows: tuple[str, ...]) -> bytes:
    """Native 4bpp, four 8x8 tiles in row order; low nibble is left pixel."""
    return bytes(
        int(rows[ty + y][tx + x].replace(".", "0"), 16)
        | (int(rows[ty + y][tx + x + 1].replace(".", "0"), 16) << 4)
        for ty in (0, 8) for tx in (0, 8) for y in range(8) for x in range(0, 8, 2)
    )


def apply_statue_visuals(rom: bytes, mode: int) -> bytes:
    """Apply after grant tokens. 0 is off/disabled, 1 shuffled, 2 per-touch random.

    Allocate at EOF, so other append-only extensions cannot be overwritten.
    Validate the native layout before modifying anything. No base-patch rebuild
    or runtime hook is needed. The Master Sword's record follows our 19 records
    and is deliberately excluded.
    """
    if mode == 0:
        return rom
    if mode not in (1, 2):
        raise ValueError(f"Unsupported statue visual mode: {mode}")
    if not 0x1000000 <= len(rom) <= 0x2000000 - 4096:
        raise ValueError("Statue visuals require a USA ROM with room for the art extension")
    expected_info = b"".join(struct.pack("<HBB", 0x384, v, 0) for v in NATIVE_VARIANTS)
    if rom[ANIM_INFO_OFFSET:ANIM_INFO_OFFSET + len(expected_info)] != expected_info:
        raise ValueError("Unexpected native statue AnimInfo records (or already patched)")
    expected_table = b"".join(struct.pack("<I", ROM_BASE + NATIVE_SCRIPT_OFFSET + i * 36)
                              for i in range(NATIVE_VARIANT_COUNT))
    if (rom[ANIM_POINTER_OFFSET:ANIM_POINTER_OFFSET + 4]
            != struct.pack("<I", ROM_BASE + NATIVE_ANIM_TABLE_OFFSET)
            or rom[NATIVE_ANIM_TABLE_OFFSET:NATIVE_ANIM_TABLE_OFFSET + len(expected_table)] != expected_table):
        raise ValueError("Unexpected native statue animation table")
    # Custom icons reuse frame 11's one 16x16 OBJ and palette 429. This avoids
    # introducing palette-bank conflicts between statues in the same room.
    if (rom[0x476564 + 11 * 12:0x476564 + 12 * 12]
            != struct.pack("<HHHHhh", 44, 1, 16, 16, 8, 8)
            or rom[NATIVE_SCRIPT_OFFSET + 11 * 36:NATIVE_SCRIPT_OFFSET + 12 * 36]
            != struct.pack("<9i", -2, 429, 16, -1, 103349, 4, 1, 11, -4)
            or rom[0x3B909C:0x3B909C + 24]
            != struct.pack("<6I", 0x08448574, 0x084789C4, 0x084BA240,
                           0x084BB0EC, ROM_BASE + TILES_BASE, 0x08869B6C)):
        raise ValueError("Unexpected native statue sprite layout")
    variants = {ABILITY_NAME_TO_ID[name]: variant
                for name, variant in zip(NATIVE_STATUE_ABILITIES, NATIVE_VARIANTS)}
    variants.update({ABILITY_NAME_TO_ID[name]: NATIVE_VARIANT_COUNT + i
                     for i, name in enumerate(CUSTOM_STATUE_ABILITIES[:-1])})
    grants = rom[GRANT_TABLE_OFFSET:GRANT_TABLE_OFFSET + 19]
    if any(ability not in variants for ability in grants):
        raise ValueError("Statue grant is outside the 25 supported abilities")
    pixels = load_statue_pixels()
    result = bytearray(rom)
    result.extend(b"APSTAT01")
    # Native tile commands index from TILES_BASE in 32-byte units.
    result.extend(bytes((TILES_BASE - len(result)) % 32))
    tile_offset = len(result)
    for name in CUSTOM_STATUE_ABILITIES:
        result.extend(encode_statue_tiles(pixels[name]))
    script_offset = len(result)
    for i in range(len(CUSTOM_STATUE_ABILITIES)):
        tile_index = (tile_offset + i * 128 - TILES_BASE) // 32
        result.extend(struct.pack("<9i", -2, 429, 16, -1, tile_index, 4, 1, 11, -4))
    table_offset = len(result)
    result.extend(expected_table)
    for i in range(len(CUSTOM_STATUE_ABILITIES)):
        result.extend(struct.pack("<I", ROM_BASE + script_offset + i * 36))
    struct.pack_into("<I", result, ANIM_POINTER_OFFSET, ROM_BASE + table_offset)
    for i, ability in enumerate(grants):
        variant = variants[ability] if mode == 1 else NATIVE_VARIANT_COUNT + 6
        struct.pack_into("<HBB", result, ANIM_INFO_OFFSET + i * 4, 0x384, variant, 0)
    return bytes(result)
