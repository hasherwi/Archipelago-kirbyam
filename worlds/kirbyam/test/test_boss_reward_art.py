"""Boss art does not take over the native defeat/reward path or location bits."""
import re
import runpy
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from .test_runtime_regression_hooks import patch_rom

WORLD = Path(__file__).resolve().parents[1]
PAYLOAD = WORLD / "kirby_ap_payload"


def test_all_eight_exact_native_boss_finish_calls_are_guarded() -> None:
    rom = runpy.run_path(str(WORLD / "tools" / "create_dummy_rom.py"))["build_dummy_rom"]()
    offsets = patch_rom.AREA_BOSS_REWARD_ART_CALLSITES
    assert len(offsets) == len(set(offsets)) == 8
    target = 0x0815E10C
    assert patch_rom.build_area_boss_reward_art_hooks(rom, target) == {
        offset: patch_rom.thumb_bl_bytes(0x08000000 + offset, target) for offset in offsets
    }
    for offset in offsets:
        rom[offset] ^= 1
        with pytest.raises(SystemExit, match="native area boss reward art dispatch"):
            patch_rom.build_area_boss_reward_art_hooks(rom, target)
        rom[offset] ^= 1


def test_real_defeat_wrapper_vetoes_replays_wrong_rooms_and_non_adventure(tmp_path: Path) -> None:
    cc = shutil.which("cc")
    if not cc:
        pytest.skip("requires a native C compiler")
    code = (PAYLOAD / "ap_payload.c").read_text()
    room_lookup = re.search(
        r"static const uint16_t ap_area_boss_rooms\[8\].*?\n};", code, flags=re.S
    )
    assert room_lookup
    begin = code.index("void ap_area_boss_reward_art(")
    end = code.index("\n}", begin) + 2
    wrapper = code[begin:end]
    for old, new in (
        ("((void (*)(void*, uint16_t))0x08088701u)(boss, identity)", "native_finish(boss, identity)"),
        ("*(volatile uint32_t*)0x0203AD10u", "fixture_flags"),
        ("*(volatile uint16_t*)0x0203AD48u", "fixture_slot"),
    ):
        assert wrapper.count(old) == 1
        wrapper = wrapper.replace(old, new)
    harness = r'''
#include <assert.h>
#include "hub_save_logic.h"
static _Alignas(4) uint8_t boss_fixture[0x64];
static uint16_t local_room, fixture_slot;
static unsigned native_calls, gems;
static uint32_t fixture_flags, world[32], auth[4] = {1,2,3,4};
#define AP_HUB_SAVED_CHECKS (world+27)
#define AP_HUB_ROM_AUTH auth
static uint16_t ap_reward_local_room(void) { return local_room; }
static void native_finish(void *boss, uint16_t id) {
    assert(boss == boss_fixture && id <= 9u);
    ++native_calls;
}
static void ap_show_room_reward_gem(uint16_t room, int32_t x, int32_t y, uint32_t stop) {
    assert(native_calls > gems && room == local_room && x == 150*256 && y == 72*256 && stop == 0);
    ++gems;
}
'''
    exercise = r'''
int main(void) {
    *(int32_t*)(boss_fixture+0x40u) = 150*256;
    *(int32_t*)(boss_fixture+0x44u) = 100*256;
    for (uint16_t id=1; id<=8; ++id) {
        local_room=ap_area_boss_rooms[id-1u];
        *(uint16_t*)(boss_fixture+0x60u)=local_room;
        ap_area_boss_reward_art(boss_fixture,id);
        ap_area_boss_reward_art(boss_fixture,id);
        assert(gems==id && native_calls==2u*id);
    }
    assert(!ap_physical_saved_checks(AP_HUB_SAVED_CHECKS,auth));
    assert(ap_physical_saved_bits(AP_HUB_SAVED_CHECKS,auth)==(0xFFu<<19));
    auth[3]^=1;
    *(uint16_t*)(boss_fixture+0x60u)=710u;
    ap_area_boss_reward_art(boss_fixture,2); /* Other Kirby's room. */
    local_room=710u;
    ap_area_boss_reward_art(boss_fixture,1); /* Different boss for same room. */
    ap_area_boss_reward_art(boss_fixture,0);
    ap_area_boss_reward_art(boss_fixture,9);
    fixture_flags=0x10u;
    ap_area_boss_reward_art(boss_fixture,2); /* Demo. */
    fixture_flags=0u;
    fixture_slot=3u;
    ap_area_boss_reward_art(boss_fixture,2); /* No native adventure file. */
    assert(gems==8u && native_calls==22u && !ap_physical_saved_bits(AP_HUB_SAVED_CHECKS,auth));
    fixture_slot=1u;
    ap_area_boss_reward_art(boss_fixture,2);
    assert(gems==9u && native_calls==23u);
    return 0;
}
'''
    source = tmp_path / "boss-art.c"
    source.write_text(harness + room_lookup.group() + "\n" + wrapper + exercise)
    exe = tmp_path / ("test-boss-art.exe" if sys.platform == "win32" else "test-boss-art")
    subprocess.run([cc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-I", str(PAYLOAD),
                    str(source), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
