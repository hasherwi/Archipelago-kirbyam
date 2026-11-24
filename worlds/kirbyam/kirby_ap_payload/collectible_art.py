"""Build palette-safe 16×16 OBJ tiles from the clean USA collectible sources."""

from __future__ import annotations

import hashlib
import struct

OFFSET = 0x100D000
MARKER = b"APART04\0"
ART_SIZE = 128
FIRST_ART = 9
LAST_ART = 47
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
        # Single square 32×32 runtime display slot, independent of native shard actors.
        0x421BD0: struct.pack("<9i", -2, 205, 16, -1, 45169, 16, 1, 0, -4),
        0x46D528: struct.pack("<4H2h", 0, 1, 32, 32, 16, 14),
        0x4A7FE6: struct.pack("<3H", 0, 0x8000, 0),
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
    _validate_access_art_sources(rom)
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
    for art, tiles in zip(range(45, 48), _access_art(rom), strict=True):
        put(art, tiles)
    return bytes(table)


SHARD_ANIM_OFFSET = 0x1007000
SHARD_ANIM_MARKER = b"APSHD01\0"
SHARD_ANIM_TICKS = 40
SHARD_ANIM_FRAME_SIZE = 512
SHARD_ANIM_SIZE = len(SHARD_ANIM_MARKER) + SHARD_ANIM_TICKS * SHARD_ANIM_FRAME_SIZE
AURA_BASE = 0x61098C
SHARD_ANIM_ROWS = ((45779, 9, 3), (45788, 9, 5), (45797, 3, 5),
                   (45800, 9, 5), (45809, 9, 5), (45818, 9, 5),
                   (45827, 3, 5), (45830, 9, 5), (45839, 9, 2))
AURA_DELAYS = (2, *(1,) * 10, 4, *(1,) * 7)
SHARD_ANIM_SCRIPT = struct.pack("<49i", -2, 220, 16, *(
    word for frame, (tile, count, delay) in enumerate(SHARD_ANIM_ROWS)
    for word in (-1, tile, count, delay, frame)), -4)
AURA_SCRIPT = struct.pack("<45i", -2, 175, 16, -1, 43234, 256, *(
    word for frame, delay in enumerate(AURA_DELAYS) for word in (delay, frame)), -4)

# These ranges pin the native images, frame bounds, OAM and flip declarations.
ANIM_RETAIL_HASHES = {
    (AURA_BASE, 8192): "16f2e8d1f4156257a850e8c1f6d4a1645920fd641716f1dbf09cb1b4b29b2e5c",
    (SHARD_BASE, 2208): "db1b5658eb3b9d524363ad09372e92ea1ccb04cfe25752adeb4d720645ce282a",
    (0x46A234, 228): "be9eb9418c4f33341f1f9a1b0ea696c16f0ea99961df865f8f49bbe2db065c64",
    (0x4A043E, 714): "c0a99433c3fb3f3773aae6b0fec6be75cf9723ef771d760e93282f11d2fb5c0a",
    (0x46D81C, 108): "f4a035b36e9cb5a1f3cd554c8f8b512c62ceca66be76f0e0165c62b87635f857",
    (0x4A8286, 192): "d45d334320d0f41177b8c68a06aba5f5d7c7f0a0b3f7e3f7ca0eefdfe7611a21",
}


def synthetic_animation_assets() -> dict[int, bytes]:
    """Playable metadata shape but invented fixture graphics; no retail art."""
    shard_attrs, shard_oam = bytearray(), bytearray()
    for frame in range(9):
        first = len(shard_oam) // 6
        if frame in (2, 6):
            shard_attrs.extend(struct.pack("<4H2h", first, 2, 8, 24, 3, 11))
            shard_oam.extend(struct.pack("<6H", 0x8000, 0, 0, 16, 0, 2))
        else:
            shard_attrs.extend(struct.pack("<4H2h", first, 4, 24, 24, 11, 11))
            shard_oam.extend(native_abi_fixtures()[0x4A8286])
    return {
        0x422894: SHARD_ANIM_SCRIPT,
        0x41DCE0: AURA_SCRIPT,
        # Artificial per-frame particles, including native-style negative coordinates.
        0x46A234: b"".join(struct.pack("<4H2h", frame, 1, 0, 0, 0, 0) for frame in range(19)),
        0x4A043E: b"".join(struct.pack("<3H", 0xF2, (frame - 9) & 511, frame) for frame in range(19)) + bytes(600),
        0x46D81C: bytes(shard_attrs),
        0x4A8286: bytes(shard_oam),
        AURA_BASE: hashlib.shake_256(b"KirbyAM synthetic aura").digest(8192),
        SHARD_BASE: synthetic_assets()[SHARD_BASE] + hashlib.shake_256(b"KirbyAM synthetic rotation").digest(1920),
        PALETTE_BASE + 175 * 32: struct.pack("<16H", *BANK_F),
    }


def _validate_animation_sources(rom: bytes | bytearray) -> None:
    for off, script in ((0x422894, SHARD_ANIM_SCRIPT), (0x41DCE0, AURA_SCRIPT)):
        if rom[off:off + len(script)] != script:
            raise ValueError(f"Unexpected native shard/aura animation script at {off:#x}")
    synthetic = all(
        rom[off:off + len(data)] == data for off, data in synthetic_animation_assets().items()
    )
    if not synthetic:
        for (off, size), expected in ANIM_RETAIL_HASHES.items():
            if hashlib.sha256(rom[off:off + size]).hexdigest() != expected:
                raise ValueError(f"Unexpected native shard/aura tiles or OAM at {off:#x}")
    # Retail aura palette 175 uses the stock bank-F visible colors already.
    if _palette(rom, 175)[1:] != BANK_F[1:]:
        raise ValueError("Unexpected native aura palette")


OAM_SIZES = (((8, 8), (16, 16), (32, 32), (64, 64)),
             ((16, 8), (32, 8), (32, 16), (64, 32)),
             ((8, 16), (8, 32), (16, 32), (32, 64)))


def _draw_native_frame(
    rom: bytes | bytearray, grid: list[int], attrs: int, oam: int,
    tiles: int, tile_count: int, colors: tuple[int, ...],
) -> None:
    first, count, _, _, offset_x, offset_y = struct.unpack_from("<4H2h", rom, attrs)
    first &= 0x3FFF
    # Earlier entries have native OAM foreground precedence.
    for piece in range(first + count - 1, first - 1, -1):
        a, b, c = struct.unpack_from("<3H", rom, oam + 6 * piece)
        if a & 0x2300 or (a >> 14) == 3:
            raise ValueError("Unexpected affine/8bpp native shard/aura OAM")
        width, height = OAM_SIZES[a >> 14][b >> 14]
        origin_x = ((b & 511) ^ 256) - 256 + 16 - offset_x
        origin_y = ((a & 255) ^ 128) - 128 + 16 - offset_y
        tile = c & 1023
        if tile + width * height // 64 > tile_count:
            raise ValueError("Native shard/aura OAM tile range is invalid")
        for y in range(max(0, -origin_y), min(height, 32 - origin_y)):
            py = height - 1 - y if b & 0x2000 else y
            for x in range(max(0, -origin_x), min(width, 32 - origin_x)):
                px = width - 1 - x if b & 0x1000 else x
                raw_tile = tile + py // 8 * (width // 8) + px // 8
                raw = rom[tiles + raw_tile * 32 + py % 8 * 4 + px % 8 // 2]
                pixel = raw >> (4 * (px & 1)) & 15
                if pixel:
                    grid[(origin_y + y) * 32 + origin_x + x] = colors[pixel]


def _pack_32(image: list[int]) -> bytes:
    return bytes(
        image[32 * y + x] | image[32 * y + x + 1] << 4
        for ty in range(0, 32, 8) for tx in range(0, 32, 8)
        for y in range(ty, ty + 8) for x in range(tx, tx + 8, 2)
    )


def build_shard_animation(rom: bytes | bytearray, extension: bytes) -> bytes:
    start = SHARD_ANIM_OFFSET - 0x1000000
    if (len(rom) != 0x1000000 or len(extension) < start + SHARD_ANIM_SIZE
            or any(extension[start:start + SHARD_ANIM_SIZE])):
        raise ValueError("Missing empty rotating shard extension slot")
    _validate_animation_sources(rom)
    shard_colors = _remap(_palette(rom, 220))
    aura_colors = tuple(range(16))
    aura_ticks = [frame for frame, duration in enumerate(AURA_DELAYS) for _ in range(duration)]
    output = bytearray(SHARD_ANIM_MARKER)
    tick = 0
    for frame, (tile, count, duration) in enumerate(SHARD_ANIM_ROWS):
        for _ in range(duration):
            grid = [0] * 1024
            if tick < len(aura_ticks):
                _draw_native_frame(rom, grid, 0x46A234 + aura_ticks[tick] * 12,
                                   0x4A043E, AURA_BASE, 256, aura_colors)
                # Bloom and outer trail can fill the square clip. Keep the
                # native shard below unmasked; soften the aura to a round footprint.
                for j in range(1024):
                    if (2 * (j % 32) - 31) ** 2 + (2 * (j // 32) - 31) ** 2 > 31 ** 2:
                        grid[j] = 0
            _draw_native_frame(rom, grid, 0x46D81C + frame * 12, 0x4A8286,
                               SHARD_BASE + (tile - 45779) * 32, count, shard_colors)
            output.extend(_pack_32(grid))
            tick += 1
    return bytes(output)


# The actual Pink Kirby HUD handset, raised Switch, and unpulled Lever.
PHONE_TILES = 0x2ECD00  # gUnk_082EC7A0 + (0x1B0 - 0x185) * 32
PHONE_PINK_PALETTE = 0x34BB20  # sHudPalettes[0], never the receiving player's palette
SWITCH_TILES = 0x62CFAC
SWITCH_PALETTE = PALETTE_BASE + 235 * 32
LEVER_TILES = 0x6201EC
LEVER_PALETTE = PALETTE_BASE + 159 * 32
ACCESS_ART_HASHES = {
    (PHONE_TILES, 64): "8c01f992e79d5187c2739de8f144bca02783f873573dd8eb9dfb1a2dbae61957",
    (PHONE_PINK_PALETTE, 32): "788408cc93930da91747f3a08879a9203a864ee0d50dab5df3c6cb298c8dbbe0",
    (SWITCH_TILES, 768): "c742776a996cc3000aa6c87d8ecd28ccd9e722087a7ac6cdd1c793316c154323",
    (SWITCH_PALETTE, 32): "ebe01e8ad3bd345ad6df704ce4052135a80118b9edbeb8109e148647960e7a47",
    (LEVER_TILES, 512): "df700d9cc5942911f0be01034a024a94d193b7d97ca6447c0c767a83dd4d9b95",
    (LEVER_PALETTE, 32): "bd84dbaddcea92197b3164da1d4d9bf7a54c172951314717be5171fa1ae12247",
}
ACCESS_ART_METADATA = {
    0x423934: struct.pack("<9i", -2, 235, 16, -1, 46867, 24, 1, 0, -4),
    0x46DCD8: struct.pack("<4H2h", 0, 2, 48, 32, 24, 30),
    0x4A8898: struct.pack("<6H", 0, 0x8000, 0, 0x8000, 0x8020, 16),
    0x422128: struct.pack("<9i", -2, 159, 16, -1, 45221, 16, 1, 7, -4),
    0x46D57C: struct.pack("<4H2h", 7, 1, 32, 32, 8, 15),
    0x4A8010: struct.pack("<3H", 0, 0x8000, 0),
}


def synthetic_access_assets() -> dict[int, bytes]:
    scratch = {
        offset: hashlib.shake_256(f"KirbyAM synthetic access sprite {offset:x}".encode()).digest(size)
        for offset, size in ACCESS_ART_HASHES
    }
    scratch[LEVER_PALETTE] = struct.pack("<16H", *BANK_F)
    return {**scratch, **ACCESS_ART_METADATA}


def _validate_access_art_sources(rom: bytes | bytearray) -> None:
    for offset, expected in ACCESS_ART_METADATA.items():
        if rom[offset:offset + len(expected)] != expected:
            raise ValueError(f"Unexpected native Phone/Switch/Lever animation/OAM at {offset:#x}")
    if not all(rom[offset:offset + len(expected)] == expected
               for offset, expected in synthetic_access_assets().items()):
        for (offset, size), expected_hash in ACCESS_ART_HASHES.items():
            if hashlib.sha256(rom[offset:offset + size]).hexdigest() != expected_hash:
                raise ValueError(f"Unexpected native Phone/Switch/Lever tiles or palette at {offset:#x}")
    if struct.unpack_from("<16H", rom, LEVER_PALETTE)[1:] != BANK_F[1:]:
        raise ValueError("Unexpected native Lever palette")


def _piece(rom: bytes | bytearray, offset: int, width: int, height: int) -> list[list[int]]:
    return [
        [rom[offset + 32 * (y // 8 * (width // 8) + x // 8) + 4 * (y % 8) + x % 8 // 2]
         >> (4 * (x & 1)) & 15 for x in range(width)]
        for y in range(height)
    ]


def _fit_access_art(image: list[list[int]], colors: tuple[int, ...],
                    *, preserve_native_box: bool = False) -> bytes:
    dest = [0] * 256
    if preserve_native_box:
        left, top, right, bottom = 0, 0, len(image[0]), len(image)
    else:
        opaque = [(x, y) for y, row in enumerate(image) for x, value in enumerate(row) if value]
        if not opaque:
            raise ValueError("Native access sprite is blank")
        left = min(x for x, _ in opaque)
        top = min(y for _, y in opaque)
        right = 1 + max(x for x, _ in opaque)
        bottom = 1 + max(y for _, y in opaque)
    src_w, src_h = right - left, bottom - top
    scale_denominator = max(src_w, src_h, 16)
    width = max(1, (src_w * 16 + scale_denominator // 2) // scale_denominator)
    height = max(1, (src_h * 16 + scale_denominator // 2) // scale_denominator)
    for dy in range(height):
        sy = top + (2 * dy + 1) * src_h // (2 * height)
        for dx in range(width):
            sx = left + (2 * dx + 1) * src_w // (2 * width)
            dest[((16 - height) // 2 + dy) * 16 + (16 - width) // 2 + dx] = colors[image[sy][sx]]
    return _to_tiles(dest)


def _access_art(rom: bytes | bytearray) -> tuple[bytes, ...]:
    phone = _piece(rom, PHONE_TILES, 8, 16)
    first, last = (_piece(rom, SWITCH_TILES, 32, 32), _piece(rom, SWITCH_TILES + 512, 16, 32))
    switch = [a + b for a, b in zip(first, last, strict=True)]
    lever = _piece(rom, LEVER_TILES, 32, 32)
    return (
        _fit_access_art(phone, _remap(struct.unpack_from("<16H", rom, PHONE_PINK_PALETTE)),
                        preserve_native_box=True),
        _fit_access_art(switch, _remap(struct.unpack_from("<16H", rom, SWITCH_PALETTE))),
        _fit_access_art(lever, tuple(range(16))),
    )
