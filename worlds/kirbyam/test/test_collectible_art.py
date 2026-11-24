"""Exercise bounded collectible art conversion without retail image fixtures."""

import runpy
from pathlib import Path

import pytest

from .test_runtime_regression_hooks import patch_rom

WORLD = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def art():
    return runpy.run_path(str(WORLD / "kirby_ap_payload" / "collectible_art.py"))


@pytest.fixture(scope="module")
def rom():
    return runpy.run_path(str(WORLD / "tools" / "create_dummy_rom.py"))["build_dummy_rom"]()


def test_reserved_table_and_runtime_art_ids(art, rom):
    writes = patch_rom.build_collectible_art_extension(rom, bytes(65536))
    assert set(writes) == {0x1007000, 0x100D000}
    table = writes[0x100D000]
    assert table[:8] == b"APART04\0"
    assert 0x100D000 + len(table) == 0x100E388
    for art_id in range(9, 48):
        offset = 8 + (art_id - 9) * 128
        assert bool(any(table[offset:offset + 128])) == (art_id not in (18, 19))

    # Conversion must use every correct source palette and preserve alpha.
    transform = (
        (range(9, 18), art["NINE_AREA_PALS"], art["MEDIA_BASE"] + 256),
        (range(20, 34), art["ALL_MEDIA_PALS"], art["MEDIA_BASE"]),
        (range(34, 44), art["TEN_SHEET_PALS"], art["MEDIA_BASE"] + 128),
    )
    for ids, palettes, source in transform:
        for art_id, palette in zip(ids, palettes, strict=True):
            offset = 8 + (art_id - 9) * 128
            colors = art["_remap"](art["_palette"](rom, palette))
            raw = rom[source:source + 128]
            dest = table[offset:offset + 128]
            assert dest == bytes(colors[n & 15] | colors[n >> 4] << 4 for n in raw)
            assert [(not (n & 15), not (n >> 4)) for n in raw] == [
                (not (n & 15), not (n >> 4)) for n in dest
            ]


def test_rejects_bad_native_abi_or_occupied_slot(art, rom):
    build = art["build_collectible_art_table"]
    for offset in (0x421FC0, 0x422894, 0x46D81C, 0x4A8286, art["MEDIA_BASE"], art["SHARD_BASE"]):
        bad = bytearray(rom)
        bad[offset] ^= 1
        with pytest.raises(ValueError, match="Unexpected native collectible"):
            build(bad, bytes(65536))
    occupied = bytearray(65536)
    occupied[0xE387] = 1
    with pytest.raises(ValueError, match="reserved extension slot"):
        build(rom, occupied)
    with pytest.raises(ValueError, match="reserved extension slot"):
        build(rom, bytes(0xE387))


def test_shard_composite_piece_packing(art):
    source = bytearray(0x1000000)
    shard, pal = art["SHARD_BASE"], art["PALETTE_BASE"] + 220 * 32
    source[pal:pal + 32] = b"".join(v.to_bytes(2, "little") for v in art["BANK_F"])
    for x, y, w, h, first in art["SHARD_PIECES"]:
        color = first + 1
        source[shard + first * 32:shard + (first + w * h // 64) * 32] = bytes(
            [color * 17] * (w * h // 2)
        )
    raw = art["_shard_icon"](source)
    assert [raw[0] & 15, raw[35] >> 4, raw[92] & 15, raw[127] >> 4] == [1, 7, 5, 9]


def test_shard_animation_exact_ticks_and_reserved_slot(art, rom):
    build = art["build_shard_animation"]
    table = build(rom, bytes(65536))
    assert table[:8] == b"APSHD01\0"
    assert 0x1007000 + len(table) == 0x100C008
    frames = [table[8 + i * 512:8 + (i + 1) * 512] for i in range(40)]
    assert all(any(frame) for frame in frames)
    assert len(set(frames[:23])) >= 19  # Aura samples track exact native frame progression.
    assert frames[23] == frames[27]
    assert frames[28] != frames[27] and frames[28] == frames[32]
    assert frames[33] != frames[32] and frames[33] == frames[37]
    assert frames[38] == frames[39] and frames[37] != frames[38]
    occupied = bytearray(65536)
    occupied[0xC007] = 1
    with pytest.raises(ValueError, match="rotating shard extension slot"):
        build(rom, occupied)
    for addr in (0x41DCE0, 0x422894, 0x46A234, 0x4A043E, art["AURA_BASE"], 0x4BC6CE):
        bad = bytearray(rom)
        bad[addr] ^= 1
        with pytest.raises(ValueError, match="Unexpected native"):
            build(bad, bytes(65536))


def test_access_art_uses_fixed_pink_palette_and_stock_object_geometry(art, rom):
    build = art["build_collectible_art_table"]
    table = build(rom, bytes(65536))
    # The added IDs follow the original static shard tile without any overlap.
    icons = [table[8 + (i - 9) * 128:8 + (i - 8) * 128] for i in range(45, 48)]
    assert icons == list(art["_access_art"](rom))
    assert len(set(icons)) == 3

    def pixel(tiles, x, y):
        b = tiles[32 * (y // 8 * 2 + x // 8) + 4 * (y % 8) + x % 8 // 2]
        return b >> (4 * (x % 2)) & 15

    # Phone occupies its native 8×16 box, horizontally centered, and uses
    # sHudPalettes[0] rather than the neighboring alternate character palette.
    source = art["_piece"](rom, art["PHONE_TILES"], 8, 16)
    pal = art["struct"].unpack_from("<16H", rom, art["PHONE_PINK_PALETTE"])
    colors = art["_remap"](pal)
    assert all(pixel(icons[0], x, y) == (colors[source[y][x - 4]] if 4 <= x < 12 else 0)
               for y in range(16) for x in range(16))
    altered_neighboring_palette = bytearray(rom)
    altered_neighboring_palette[art["PHONE_PINK_PALETTE"] + 32] ^= 1
    assert build(altered_neighboring_palette, bytes(65536)) == table
    for native_offset in (art["PHONE_TILES"], art["PHONE_PINK_PALETTE"], art["LEVER_TILES"],
                          art["SWITCH_TILES"], 0x423934, 0x4A8010):
        bad = bytearray(rom)
        bad[native_offset] ^= 1
        with pytest.raises(ValueError, match="Unexpected native Phone/Switch/Lever"):
            build(bad, bytes(65536))
