"""Explicit owned-paint selection, color priority and palette lifecycle contracts."""
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest

from ..colors import encode_color_config
from .test_runtime_regression_hooks import patch_rom

WORLD = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('color', range(19))
@pytest.mark.parametrize('per_room', [False, True])
def test_color_config_encodes_mode_without_moving_rom_word(color: int, per_room: bool) -> None:
    assert encode_color_config(color, per_room) == 0xC0100000 | (int(per_room) << 8) | color


@pytest.mark.parametrize('color', [-1, 19, 254, 0xFFFFFFFF])
def test_color_config_rejects_non_concrete_colors(color: int) -> None:
    with pytest.raises(ValueError):
        encode_color_config(color, False)


def test_treasure_hook_validates_native_call_before_mutation() -> None:
    rom = bytearray(0x150000)
    off = patch_rom.TREASURE_PAINT_CALL_OFFSET
    rom[off:off + 4] = patch_rom.thumb_bl_bytes(0x08000000 + off, 0x081447E0)
    before = bytes(rom)
    writes = patch_rom.build_treasure_paint_writes(rom, 0x0815E100)
    assert bytes(rom) == before
    assert list(writes) == [0x14406C]
    assert patch_rom.decode_thumb_bl_target(0x0814406C, writes[off]) == 0x0815E100
    rom[off:off + 4] = writes[off]
    with pytest.raises(SystemExit, match='native treasure paint selection'):
        patch_rom.build_treasure_paint_writes(rom, 0x0815E100)


def test_shipping_color_precedence_and_lifecycle(tmp_path: Path) -> None:
    cc = shutil.which('cc')
    if not cc or not sys.platform.startswith('linux'):
        pytest.skip('requires Linux mapped-memory C harness')
    assert cc is not None
    source = (WORLD / 'kirby_ap_payload/ap_payload.c').read_text()
    source = re.sub(r'register uint32_t (\w+) asm\("r[458]"\);', r'uint32_t \1 = 0;', source)
    source = source.replace('__asm__ volatile("mov %0, lr" : "=r"(caller_lr_snapshot));',
                            'caller_lr_snapshot = 0;')
    source = source.replace('volatile const uint32_t gApStartingKirbyColorInitial',
                            'volatile uint32_t gApStartingKirbyColorInitial')
    for macro, replacement in {
        'KIRBY_TRANSFORM_BG_PALETTE_FN': 'transform_bg',
        'KIRBY_REFRESH_PALETTE_FN': 'refresh_obj', 'KIRBY_LOAD_BG_PALETTE_FN': 'load_bg',
        'KIRBY_START_GAME_FN': 'start_game', 'KIRBY_MENU_SELECT_FN': 'menu_select',
        'KIRBY_SAVE_WORLD_FN': 'save_world',
    }.items():
        source = re.sub(r'^#define '+macro+r' .+$', '#define '+macro+' '+replacement,
                        source, flags=re.M)
    source = '''#define _GNU_SOURCE
#include <stdint.h>
#include <sys/mman.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static void transform_bg(const uint16_t*,uint8_t,uint16_t);
static void refresh_obj(uint8_t);
static void load_bg(const uint16_t*,uint8_t,uint16_t);
static void start_game(uint8_t,uint8_t,const uint16_t*,const int32_t*,const uint32_t*);
static uint32_t menu_select(uint8_t*);
static int16_t save_world(uint32_t,uint16_t);
''' + source + (WORLD / 'test/native/color_precedence_host.c').read_text()
    cfile = tmp_path / 'color.c'
    cfile.write_text(source)
    exe = tmp_path / 'color'
    result = subprocess.run([cc, '-std=gnu99', '-w', '-I', str(WORLD / 'kirby_ap_payload'),
                             str(cfile), '-o', str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    result = subprocess.run([str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert '45600 precedence cases' in result.stdout
