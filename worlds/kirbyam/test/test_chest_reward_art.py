"""Native stop, palette and constructor contracts for reward visuals."""
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
        *((offset + 16, "consumable tile script")
          for offset, _ in patch_rom.CHEST_REWARD_ART_CONSUMABLE_SCRIPTS),
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


def test_native_trap_tiles_use_owner_shape_and_shared_palette() -> None:
    image = pytest.importorskip("PIL.Image")
    art = runpy.run_path(str(PAYLOAD / "generate_trap_reward_art.py"))
    src = image.open(art["SOURCE"]).convert("RGBA")
    preview = image.open(art["PREVIEW"]).convert("RGBA")
    assert src.size == preview.size == (16, 16)
    tiles = [int(x, 16) for x in re.findall(r"0x([\dA-F]{2})", art["HEADER"].read_text())]
    assert len(tiles) == 128
    for y in range(16):
        for x in range(16):
            tile = (y // 8) * 2 + x // 8
            index = (tiles[tile * 32 + (y % 8) * 4 + (x % 8) // 2] >> (4 * (x % 2))) & 15
            assert index == art["palette_index"](src.getpixel((x, y)))
            color = patch_rom.CHEST_REWARD_ART_NATIVE_PALETTE_DATA[index]
            rendered = tuple(((color >> c) & 31) * 255 // 31 for c in (0, 5, 10))
            assert preview.getpixel((x, y)) == rendered + (255 if index else 0,)
    assert preview.tobytes() != src.tobytes()


def test_exact_native_consumable_tiles_match_validated_animation_variants() -> None:
    code = (PAYLOAD / "ap_payload.c").read_text()
    native_variants = dict(re.findall(
        r"case AP_REWARD_(\w+): return AP_CHEST_NATIVE_TILES \+ (\d+)u \* AP_CHEST_ART_SIZE", code,
    ))
    assert native_variants == {
        "ONE_UP": "0", "FOOD": "4", "DRINK": "2", "MEAT": "5",
        "TOMATO": "3", "CANDY": "1", "BATTERY": "6",
        "VITALITY": "12", "SOUND_PLAYER": "13",
    }
    import struct
    scripts = [patch_rom.CHEST_REWARD_ART_NATIVE_SCRIPT_DATA,
               *(script for _, script in patch_rom.CHEST_REWARD_ART_CONSUMABLE_SCRIPTS)]
    assert set(map(int, native_variants.values())) == {*range(len(scripts)), 12, 13}
    for variant, script in enumerate(scripts):
        palette, palette_start, cmd, start, length = struct.unpack_from("<5i", script, 4)
        assert (palette, palette_start, cmd, start, length) == (159, 16, -1, 45113 + 4 * variant, 4)


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
    )
    for old, new in substitutes:
        assert wrapper.count(old) == 1
        wrapper = wrapper.replace(old, new)
    key_begin = code.index("ap_reward_key_for_chest(const void *chest)")
    key_end = code.index("\n}", key_begin) + 2
    wrapper = "static uint32_t " + code[key_begin:key_end] + "\n" + wrapper
    harness = (WORLD / "test" / "native" / "chest_reward_art_host.c").read_text()
    source = tmp_path / "art.c"
    source.write_text(harness.replace("/* WRAPPER */", wrapper))
    exe = tmp_path / "test-chest-art"
    suffix = ".exe" if os.name == "nt" else ""
    exe = exe.with_suffix(suffix)
    subprocess.run([cc, "-std=c99", "-Wall", "-Wextra", "-Werror", "-I", str(PAYLOAD),
                    str(source), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)


def test_big_switch_rom_guard_rejects_mismatched_native_call() -> None:
    dummy = runpy.run_path(str(WORLD / "tools" / "create_dummy_rom.py"))["build_dummy_rom"]()
    call = patch_rom.BIG_SWITCH_REWARD_ART_CALLSITE
    target = 0x0815E102
    assert patch_rom.build_big_switch_reward_art_hook(dummy, target) == {
        call: patch_rom.thumb_bl_bytes(0x08000000 + call, target),
    }
    dummy[call + 2] ^= 1
    with pytest.raises(SystemExit, match="Big Switch reward art dispatch"):
        patch_rom.build_big_switch_reward_art_hook(dummy, target)


def test_big_switch_reward_art_triggers_only_on_fresh_physical_ap_checks(tmp_path: Path) -> None:
    cc = shutil.which("cc")
    if not cc:
        pytest.skip("requires a native C compiler")
    code = (PAYLOAD / "ap_payload.c").read_text()
    begin = code.index("void ap_big_switch_reward_art(")
    end = code.index("\n}", begin) + 2
    wrapper = code[begin:end]
    hook = "((void (*)(void*))0x08119B3Du)(object);"
    assert wrapper.count(hook) == 1
    wrapper = wrapper.replace(hook, "native_dispatch(object);")
    # The native source pointer is four bytes; avoid overlapping adjacent
    # halfwords when exercising the same wrapper on a 64-bit host.
    source_read = "*(const uint8_t*const volatile*)(sw + 0xB0u)"
    assert wrapper.count(source_read) == 1
    wrapper = wrapper.replace(source_read, "fixture_source")
    frame_begin = code.index("void ap_reward_gem_frame(")
    frame_end = code.index("\n}", frame_begin) + 2
    frame = code[frame_begin:frame_end]
    for old, new in (
        ("*(void *volatile*)0x030035D0u", "fixture_task"),
        ("((void (*)(void*))0x08152C3Du)(task)", "destroy_task(task)"),
        ("((void (*)(void*))0x0806FAC9u)(effect)", "draw_effect(effect)"),
    ):
        assert frame.count(old) == 1
        frame = frame.replace(old, new)
    harness = (WORLD / "test" / "native" / "big_switch_reward_art_host.c").read_text()
    source = tmp_path / "switch.c"
    source.write_text(harness.replace("/* WRAPPER */", wrapper).replace("/* FRAME */", frame))
    exe = tmp_path / ("test-switch-art.exe" if os.name == "nt" else "test-switch-art")
    subprocess.run([cc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-I", str(PAYLOAD),
                    str(source), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)

def test_pressure_guards_mirror_native_allocator_and_safe_cleanup(tmp_path: Path) -> None:
    cc = shutil.which("cc")
    if not cc:
        pytest.skip("requires a native C compiler")
    code = (PAYLOAD / "ap_payload.c").read_text()
    begin = code.index("void ap_drop_invalid_reward_task(")
    end = code.index("\n}", begin) + 2
    cleanup = code[begin:end]
    native = "((void (*)(void*))0x08152C3Du)(task)"
    assert cleanup.count(native) == 1
    cleanup = cleanup.replace(native, "destroy_task(task)")
    source = tmp_path / "pressure.c"
    source.write_text(r"""
#include <assert.h>
#include "chest_reward_art_runtime.h"

static unsigned deletes;
static void destroy_task(void *task) {
    uint8_t *raw = task;
    assert(*(uint16_t*)(raw + 6u) == 0);
    assert(*(uint32_t*)(raw + 0xCu) == 0);
    ++deletes;
}
""" + cleanup + r"""
int main(void) {
    const uint32_t obj = 0x06014000u;
    /* Occupied runs have a length only at the start. Interior zeros
     * cannot combine with the one true free segment. */
    uint16_t heap[] = {3, 0, 0, 0, 1};
    assert(!ap_reward_native_vram_can_fit(heap, 10, obj));
    heap[4] = 0;
    assert(ap_reward_native_vram_can_fit(heap, 10, obj));
    assert(!ap_reward_native_vram_can_fit(heap, 8, obj));
    assert(!ap_reward_native_vram_can_fit(heap, 0, obj));
    assert(!ap_reward_native_vram_can_fit(heap, 10, 0x06017000u + 0xF80u));
    assert(!ap_reward_native_vram_can_fit(heap, 10, 0x06010000u));
    heap[0] = 5;
    assert(!ap_reward_native_vram_can_fit(heap, 10, obj));
    assert(ap_reward_vram_address_is_valid(0x06017F80u));
    assert(!ap_reward_vram_address_is_valid(0x06017FC0u));

    /* Nonempty native task can have zero offset after the dual-heap failure.
     * Reject that, an upper/end sentinel, and non-heap data offsets. */
    assert(!ap_reward_task_effect_address(0, 0x10u));
    assert(!ap_reward_task_effect_address(0, 0));
    assert(!ap_reward_task_effect_address((0x3ADE4u >> 2), 0x10u));
    assert(!ap_reward_task_effect_address(0x6010u, 0));
    assert(ap_reward_task_effect_address(2u, 0x10u) == 0x02000008u);
    assert(ap_reward_task_effect_address(0x3A24u, 0) == 0x03003A24u);
    _Alignas(4) uint8_t task[20] = {0};
    *(uint16_t*)(task + 6u) = (0x3ADE4u >> 2);
    *(uint32_t*)(task + 0xCu) = 0x0803DCCDu;
    ap_drop_invalid_reward_task(task);
    assert(deletes == 1);
    return 0;
}
""")
    exe = tmp_path / ("test-pressure.exe" if os.name == "nt" else "test-pressure")
    subprocess.run([cc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-I", str(PAYLOAD),
                    str(source), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)


def test_saturated_dma_ring_preserves_native_chest_timer_and_drops_optional_effect(tmp_path: Path) -> None:
    cc = shutil.which("cc")
    if not cc:
        pytest.skip("requires a native C compiler")
    code = (PAYLOAD / "ap_payload.c").read_text()

    def project(signature: str, replacements: tuple[tuple[str, str], ...]) -> str:
        begin = code.index(signature)
        end = code.index("\n}", begin) + 2
        entry = code[begin:end]
        for native, host in replacements:
            assert entry.count(native) == 1
            entry = entry.replace(native, host)
        return entry

    chest = project("void ap_chest_reward_art(", (
        ("(ChestPopupFn)0x0800B415u", "native_chest"),
        ("(volatile uint8_t *)0x030039A4u", "&dma_head"),
        ("(volatile struct ApChestTileUpload *)0x03002EC0u", "dma_ring"),
    ))
    overlay = project("uint8_t ap_show_room_reward_gem(", (
        ("(volatile uint8_t*)0x030039A4u", "&dma_head"),
        ("(volatile struct ApChestTileUpload*)0x03002EC0u", "dma_ring"),
        ("((TaskCreateFn)0x08152B01u)", "((TaskCreateFn)create_task)"),
    ))
    harness = (WORLD / "test" / "native" / "reward_dma_pressure_host.c").read_text()
    source = tmp_path / "dma_pressure.c"
    source.write_text(harness.replace("/* CHEST */", chest).replace("/* OVERLAY */", overlay))
    exe = tmp_path / ("test-dma-pressure.exe" if os.name == "nt" else "test-dma-pressure")
    subprocess.run([cc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-I", str(PAYLOAD),
                    str(source), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
