"""Extract and validate palette-safe world statue art from the USA base ROM."""

from __future__ import annotations

import hashlib
import struct

OFFSET = 0x100E388
ART_SIZE = 128
PALETTE_BASE = 0x4BB0EC
BANK_F = (0x5EA0, 0x7E80, 0x00D2, 0x01B8, 0x02FE, 0x08BF, 0x025F, 0x0000,
          0x6E9F, 0x7D40, 0x7FA0, 0x1C96, 0x393B, 0x1262, 0x7FFF, 0x03FF)


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


# Sprite order follows native animation 0x384/variants 11 through 29, not
# Archipelago item-ID or native ability-ID order.
STATUE_ABILITY_IDS = (7, 3, 13, 1, 8, 20, 9, 16, 4, 2, 15, 25, 22, 10, 17, 18, 6, 19, 5)
STATUE_ART_BASE = 0x7E63EC
STATUE_PALETTE_INDEXES = (429,) * 8 + (430,) * 7 + (431,) * 3 + (42,)
STATUE_SOURCE_HASHES = {
    (STATUE_ART_BASE, 19 * ART_SIZE): "69345a0f0ce23b7fd076f740f601a16307776e8b415938db8deecf1b5f684fa5",
    (PALETTE_BASE + 429 * 32, 96): "4b45a206c7ebeaf0e12035063f6e7dc749b504224e9b5555cf488921df4deeb4",
}
STATUE_METADATA = {
    # Object table groups 0x92, 0x93, 0x94 and 0x95; Parasol's type 0x94
    # is ordered ahead of type 0x95 in the native ID array, but not in art.
    0x35369C: b"".join(struct.pack("<HBB", 0x384, n, 0)
                      for n in (*range(11, 26), 29, 26, 27, 28)),
    0x3538FC: bytes((*STATUE_ABILITY_IDS[:15], 5, *STATUE_ABILITY_IDS[15:18])),
    0x44073C: b"".join(struct.pack("<9i", -2, palette, 16, -1, 103349 + frame * 4,
                                   4, 1, frame + 11, -4)
                      for frame, palette in enumerate(STATUE_PALETTE_INDEXES)),
    0x4765E8: b"".join(struct.pack("<4H2h", 44 + frame, 1, 16, 16, 8, 8) for frame in range(19)),
    0x4B7658: struct.pack("<3H", 0, 0x4000, 0) * 19,
}


def synthetic_statue_assets() -> dict[int, bytes]:
    scratch = {
        offset: hashlib.shake_256(f"KirbyAM synthetic statue sprite {offset:x}".encode()).digest(size)
        for offset, size in STATUE_SOURCE_HASHES
    }
    return {**scratch, **STATUE_METADATA}


def _validate_statue_sources(rom: bytes | bytearray) -> None:
    for offset, expected in STATUE_METADATA.items():
        if rom[offset:offset + len(expected)] != expected:
            raise ValueError(f"Unexpected native ability-statue animation/OAM at {offset:#x}")
    if not all(rom[offset:offset + len(expected)] == expected
               for offset, expected in synthetic_statue_assets().items()):
        for (offset, size), expected_hash in STATUE_SOURCE_HASHES.items():
            if hashlib.sha256(rom[offset:offset + size]).hexdigest() != expected_hash:
                raise ValueError(f"Unexpected native ability-statue tiles or palette at {offset:#x}")
    if _palette(rom, 42)[1:] != BANK_F[1:]:
        raise ValueError("Unexpected native Parasol statue palette")


def _statue_art(rom: bytes | bytearray) -> tuple[bytes, ...]:
    output = []
    for index, palette in enumerate(STATUE_PALETTE_INDEXES):
        start = STATUE_ART_BASE + index * ART_SIZE
        tiles = rom[start:start + ART_SIZE]
        if palette == 42:
            # Parasol already uses stock palette F.
            output.append(bytes(tiles))
        else:
            colors = _remap(_palette(rom, palette))
            output.append(bytes(colors[n & 15] | colors[n >> 4] << 4 for n in tiles))
    return tuple(output)


def build_statue_art_table(rom: bytes | bytearray, extension: bytes) -> dict[int, bytes]:
    """Populate only the statue frame table, keeping the retail art untouched."""
    start = OFFSET - 0x1000000
    end = start + len(STATUE_ABILITY_IDS) * ART_SIZE
    if len(rom) != 0x1000000 or len(extension) < end or any(extension[start:end]):
        raise ValueError("Missing empty world statue art table reservation")
    _validate_statue_sources(rom)
    return {OFFSET: b"".join(_statue_art(rom))}
