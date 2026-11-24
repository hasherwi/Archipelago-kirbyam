"""Build palette-safe 16×16 OBJ tiles from the clean USA collectible sources."""

from __future__ import annotations

import hashlib
import struct

OFFSET = 0x100D000
MARKER = b"APART03\0"
ART_SIZE = 128
FIRST_ART = 9
LAST_ART = 44
TABLE_SIZE = len(MARKER) + (LAST_ART - FIRST_ART + 1) * ART_SIZE

PALETTE_BASE = 0x4BB0EC
BANK_F = (0x5EA0, 0x7E80, 0x00D2, 0x01B8, 0x02FE, 0x08BF, 0x025F, 0x0000,
          0x6E9F, 0x7D40, 0x7FA0, 0x1C96, 0x393B, 0x1262, 0x7FFF, 0x03FF)
MEDIA_BASE = 0x62006C
SHARD_BASE = 0x6247AC
SHARD_PIECES = ((0, 0, 16, 16, 0), (0, 16, 16, 8, 4), (16, 0, 8, 16, 6), (16, 16, 8, 8, 8))
ALL_MEDIA_PALS = (205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218)
NINE_AREA_PALS = (206, 207, 208, 209, 211, 212, 213, 214, 215)
TEN_SHEET_PALS = (205, 206, 207, 208, 209, 211, 212, 213, 214, 215)
RETAIL_REGION_HASHES = {
    (MEDIA_BASE, 3 * ART_SIZE): "51de6a74b6ef4dc84515c381384387b9e80cdbc855e3e8a3c3956addafcde4a7",
    (SHARD_BASE, 9 * 32): "ff2d8b54eac53bb96b7846f952862b36df77ca6796938f8e4e87445ec7333b34",
    (PALETTE_BASE + 205 * 32, 16 * 32): "b7c01e9e0128df99f5916b6f21f1da094779cbba9f5f9badc56b76903bc1345c",
}


def native_abi_fixtures() -> dict[int, bytes]:
    """Exact metadata used by these retail frames; not the source graphics."""
    script_rows = ((0x421C60, 45209, 4, ALL_MEDIA_PALS),
                   (0x421E58, 45213, 5, TEN_SHEET_PALS),
                   (0x421FC0, 45217, 6, (205, *NINE_AREA_PALS)))
    records = {
        start + i * 36: struct.pack("<9i", -2, palette, 16, -1, tile, 4, 1, frame, -4)
        for start, tile, frame, palettes in script_rows for i, palette in enumerate(palettes)
    }
    records.update({
        0x421B50: struct.pack("<9i", -2, 159, 16, -1, 45161, 4, 1, 12, -4),
        0x421B74: struct.pack("<9i", -2, 159, 16, -1, 45165, 4, 1, 13, -4),
        0x422894: struct.pack("<11i", -2, 220, 16, -1, 45779, 9, 3, 0, -1, 45788, 9),
        0x46D558: b"".join(struct.pack("<4H2h", f, 1, 16, 16, 8, 8) for f in (4, 5, 6)),
        0x46D81C: struct.pack("<4H2h", 0, 4, 24, 24, 11, 11),
        0x4A7FE6 + 4 * 6: struct.pack("<9H", *(0, 0x4000, 0) * 3),
        0x4A8286: struct.pack("<12H", 0, 0x4000, 0, 0x4010, 0, 4, 0x8000, 16, 6, 16, 16, 8),
    })
    return records


def synthetic_assets() -> dict[int, bytes]:
    """A non-retail checker/hash pattern used only by deterministic CI input."""
    return {
        offset: hashlib.shake_256(f"KirbyAM synthetic collectible {offset:x}".encode()).digest(size)
        for offset, size in RETAIL_REGION_HASHES
    }


def _validate_sources(rom: bytes | bytearray) -> None:
    for offset, expected in native_abi_fixtures().items():
        if rom[offset:offset + len(expected)] != expected:
            raise ValueError(f"Unexpected native collectible animation/OAM metadata at {offset:#x}")
    assets = synthetic_assets()
    synthetic = all(rom[offset:offset + len(value)] == value for offset, value in assets.items())
    if not synthetic:
        for (offset, size), expected in RETAIL_REGION_HASHES.items():
            digest = hashlib.sha256(rom[offset:offset + size]).hexdigest()
            if digest != expected:
                raise ValueError(f"Unexpected native collectible tiles/palette at {offset:#x}")


def _palette(rom: bytes | bytearray, index: int) -> tuple[int, ...]:
    return struct.unpack_from("<16H", rom, PALETTE_BASE + index * 32)


def _rgb(value: int) -> tuple[int, ...]:
    return tuple(value >> shift & 31 for shift in (0, 5, 10))


def _remap(source: tuple[int, ...]) -> tuple[int, ...]:
    f = tuple(map(_rgb, BANK_F))

    def nearest(color: int) -> int:
        rgb = _rgb(color)
        return min(range(1, 16), key=lambda slot: sum(
            weight * (a - b) ** 2 for weight, a, b in zip((3, 4, 2), rgb, f[slot])
        ))

    return (0, *(nearest(color) for color in source[1:]))


def _to_tiles(image: list[int]) -> bytes:
    return bytes(
        image[16 * y + x] | image[16 * y + x + 1] << 4
        for ty in (0, 8) for tx in (0, 8)
        for y in range(ty, ty + 8) for x in range(tx, tx + 8, 2)
    )


def _shard_icon(rom: bytes | bytearray) -> bytes:
    grid = [0] * (24 * 24)
    colors = _remap(_palette(rom, 220))
    # Native 24×24 frame zero is four OAM pieces in 1D tile packing.
    for x, y, width, height, first in SHARD_PIECES:
        for py in range(height):
            for px in range(width):
                tile = first + (py // 8) * (width // 8) + px // 8
                pixel = rom[SHARD_BASE + tile * 32 + (py % 8) * 4 + (px % 8) // 2]
                grid[(y + py) * 24 + x + px] = colors[pixel >> (4 * (px % 2)) & 15]
    nearest = tuple((i * 3 + 1) // 2 for i in range(16))
    return _to_tiles([grid[y * 24 + x] for y in nearest for x in nearest])


def build_collectible_art_table(rom: bytes | bytearray, extension: bytes) -> bytes:
    """Build one exact, reserved extension write; never alter retail palettes."""
    start = OFFSET - 0x1000000
    if (len(rom) != 0x1000000 or len(extension) < start + TABLE_SIZE
            or any(extension[start:start + TABLE_SIZE])):
        raise ValueError("Missing empty collectible reward-art reserved extension slot")
    _validate_sources(rom)
    table = bytearray(TABLE_SIZE)
    table[:len(MARKER)] = MARKER

    def put(art: int, data: bytes) -> None:
        offset = len(MARKER) + (art - FIRST_ART) * ART_SIZE
        table[offset:offset + ART_SIZE] = data

    # Vitality (18) and Sound Player (19) use their direct bank-F retail tiles.
    for first, tile_offset, palettes in (
        (9, 2 * ART_SIZE, NINE_AREA_PALS),
        (20, 0, ALL_MEDIA_PALS),
        (34, ART_SIZE, TEN_SHEET_PALS),
    ):
        src = rom[MEDIA_BASE + tile_offset:MEDIA_BASE + tile_offset + ART_SIZE]
        for i, palette in enumerate(palettes):
            colors = _remap(_palette(rom, palette))
            put(first + i, bytes(colors[n & 15] | colors[n >> 4] << 4 for n in src))
    put(44, _shard_icon(rom))
    return bytes(table)
