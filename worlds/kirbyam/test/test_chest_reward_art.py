"""Chest art is unconditional on item, without rewriting item or check behavior."""
import os
import re
import runpy
import shutil
import subprocess
from pathlib import Path

import pytest

from .test_runtime_regression_hooks import patch_rom


WORLD = Path(__file__).resolve().parents[1]
PAYLOAD = WORLD / "kirby_ap_payload"


def test_clean_guard_accepts_synthetic_contract_and_rejects_invalid_native_fields() -> None:
    dummy = runpy.run_path(str(WORLD / "tools" / "create_dummy_rom.py"))["build_dummy_rom"]()
    call = patch_rom.CHEST_REWARD_ART_CALLSITE
    target = 0x0815E100
    assert patch_rom.build_chest_reward_art_hook(dummy, target) == {
        call: patch_rom.thumb_bl_bytes(0x08000000 + call, target),
    }
    for offset, label in (
        (call, "constructor"),
        (patch_rom.CHEST_REWARD_ART_NATIVE_SCRIPT + 16, "tile script"),
        (patch_rom.CHEST_REWARD_ART_NATIVE_PALETTE + 14, "palette"),
    ):
        dummy[offset] ^= 1
        with pytest.raises(SystemExit, match="chest reward art " + label):
            patch_rom.build_chest_reward_art_hook(dummy, target)
        dummy[offset] ^= 1


def test_submitted_shape_and_generated_palette_conversion() -> None:
    image = pytest.importorskip("PIL.Image")
    art = runpy.run_path(str(PAYLOAD / "generate_chest_reward_art.py"))
    src = image.open(art["SOURCE"]).convert("RGBA")
    preview = image.open(art["PREVIEW"]).convert("RGBA")
    assert src.size == preview.size == (16, 16)
    tiles = [int(x, 16) for x in re.findall(r"0x([\dA-F]{2})", art["HEADER"].read_text())]
    assert len(tiles) == 128
    decoded = [0] * 256
    for q in range(4):
        for y in range(8):
            for x in range(8):
                pixel = ((q // 2) * 8 + y) * 16 + (q % 2) * 8 + x
                decoded[pixel] = (tiles[q * 32 + y * 4 + x // 2] >> ((x % 2) * 4)) & 15
    assert decoded == [art["palette_index"](src.getpixel((x, y))) for y in range(16) for x in range(16)]
    assert {5, 13, 9, 8, 6, 15, 14} <= set(decoded)
    assert art["NATIVE_COLORS"] == patch_rom.CHEST_REWARD_ART_NATIVE_PALETTE_DATA
    for j, value in enumerate(decoded):
        x, y = j % 16, j // 16
        assert bool(value) == bool(src.getpixel((x, y))[3]) == bool(preview.getpixel((x, y))[3])


def test_actual_popup_wrapper_changes_only_matching_tile_upload(tmp_path: Path) -> None:
    cc = shutil.which("cc")
    if not cc:
        pytest.skip("requires a native C compiler")
    code = (PAYLOAD / "ap_payload.c").read_text()
    begin = code.index("void ap_chest_reward_art(")
    end = code.index("\n}", begin) + 2
    wrapper = code[begin:end]
    substitutes = (
        ("(ChestPopupFn)0x0800B415u", "(ChestPopupFn)native_popup_host"),
        ("(volatile uint8_t *)0x030039A4u", "&head"),
        ("(volatile struct ApChestTileUpload *)0x03002EC0u", "ring"),
        ("(uint32_t)(uintptr_t)gApChestRewardArt", "ART"),
    )
    for old, new in substitutes:
        assert wrapper.count(old) == 1
        wrapper = wrapper.replace(old, new)
    harness = (WORLD / "test" / "native" / "chest_reward_art_host.c").read_text()
    source = tmp_path / "art.c"
    source.write_text(harness.replace("/* WRAPPER */", wrapper))
    exe = tmp_path / "test-chest-art"
    suffix = ".exe" if os.name == "nt" else ""
    exe = exe.with_suffix(suffix)
    subprocess.run([cc, "-std=c99", "-Wall", "-Wextra", "-Werror", "-I", str(PAYLOAD),
                    str(source), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
