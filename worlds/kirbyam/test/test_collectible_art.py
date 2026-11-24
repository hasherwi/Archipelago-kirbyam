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
    assert set(writes) == {0x100D000}
    table = writes[0x100D000]
    assert table[:8] == b"APART03\0"
    assert 0x100D000 + len(table) == 0x100E208
    for art_id in range(9, 45):
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
    occupied[0xE207] = 1
    with pytest.raises(ValueError, match="reserved extension slot"):
        build(rom, occupied)
    with pytest.raises(ValueError, match="reserved extension slot"):
        build(rom, bytes(0xE207))


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
