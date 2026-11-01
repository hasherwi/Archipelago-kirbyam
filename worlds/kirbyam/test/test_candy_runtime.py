"""Native Candy acceptance must agree with its verified retail effect restrictions."""
import re
import runpy
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from ..candy import CANDY_EXCLUDED_ROOMS
from .test_native_transport_guards import _function
from .test_runtime_regression_hooks import PAYLOAD_DIR, patch_rom


def test_candy_native_table_verification() -> None:
    rom = bytearray(0x351070)
    rooms = (999, 324, 710, 417, 822, 219, 516, 738, 129)
    assert CANDY_EXCLUDED_ROOMS == {801, *rooms[1:]}
    rom[0x35105C:0x35106E] = b"".join(room.to_bytes(2, "little") for room in rooms)
    patch_rom.validate_candy_room_table(rom)
    for i in range(9):
        bad = bytearray(rom)
        bad[0x35105C + i * 2] ^= 1
        with pytest.raises(SystemExit, match="Candy exclusion room table"):
            patch_rom.validate_candy_room_table(bad)


def test_shared_smoke_fixtures_include_native_candy_table() -> None:
    world = PAYLOAD_DIR.parent
    namespace = runpy.run_path(str(world / "test/native/hub_transition_fixture.py"))
    rom = bytearray(0x1000000)
    namespace["populate_hub_transition_fixture"](rom)
    patch_rom.validate_candy_room_table(rom)
    builder = runpy.run_path(str(world / "tools/create_dummy_rom.py"))
    patch_rom.validate_candy_room_table(builder["build_dummy_rom"]())


def test_production_candy_readiness(tmp_path: Path) -> None:
    cc = shutil.which("cc")
    if not sys.platform.startswith("linux") or cc is None:
        pytest.skip("requires Linux low mappings and native C compiler")
    assert cc is not None
    payload = (PAYLOAD_DIR / "ap_payload.c").read_text()
    constants = []
    for name in ("KIRBY_PLAYER_COUNT", "KIRBY_STRUCTS_ADDR", "KIRBY_STRUCT_STRIDE",
                 "KIRBY_STRUCT_TASK_OFFSET", "KIRBY_STRUCT_HP_OFFSET", "KIRBY_STRUCT_ROOM_OFFSET",
                 "AI_STATE_NORMAL"):
        match = re.search(r"^#define " + name + r" .+$", payload, re.MULTILINE)
        assert match
        constants.append(match.group())
    functions = "\n".join(_function(payload, name) for name in
                          ("ap_get_active_kirby_addr", "ap_invincibility_candy_ready"))
    source = r'''
#define _GNU_SOURCE
#include <stdint.h>
#include <sys/mman.h>
#include "candy_runtime_logic.h"
#define CHECK(c) do { if (!(c)) return __LINE__; } while (0)
static uint32_t KIRBY_CURRENT_PLAYER, AI_KIRBY_STATE, DEMO_PLAYBACK_FLAGS;
'''+"\n".join(constants)+"\n"+functions+r'''
int main(void) {
    CHECK(mmap((void*)0x02000000, 0x40000, 3, MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0) != MAP_FAILED);
    CHECK(mmap((void*)0x08350000, 0x10000, 3, MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0) != MAP_FAILED);
    uint16_t rooms[] = {999,324,710,417,822,219,516,738,129};
    volatile uint16_t *table = (void*)0x0835105c;
    for(unsigned i=0;i<9;i++) table[i]=rooms[i];
    for(unsigned player=0;player<4;player++) {
        KIRBY_CURRENT_PLAYER=player;
        uint32_t p=ap_get_active_kirby_addr();
        *(uint32_t*)(uintptr_t)(p+0xcc)=0x03001000;
        *(uint8_t*)(uintptr_t)(p+0x100)=10;
        AI_KIRBY_STATE=300;
        for(unsigned room=0;room<1000;room++) {
            *(uint16_t*)(uintptr_t)(p+0x60)=room;
            unsigned expected=room<=899 && room!=801;
            for(unsigned i=1;i<9;i++) if(room==rooms[i]) expected=0;
            CHECK(ap_invincibility_candy_ready()==expected);
        }
        *(uint16_t*)(uintptr_t)(p+0x60)=101;
        *(uint32_t*)(uintptr_t)(p+0xc)=0x40;
        CHECK(!ap_invincibility_candy_ready());
        *(uint32_t*)(uintptr_t)(p+0xc)=0;
        *(uint8_t*)(uintptr_t)(p+0x100)=0;
        CHECK(!ap_invincibility_candy_ready());
        *(uint8_t*)(uintptr_t)(p+0x100)=255;
        CHECK(!ap_invincibility_candy_ready());
        *(uint8_t*)(uintptr_t)(p+0x100)=10;
        uint32_t badtasks[]={0,0x02001000,0x03001001,0x03008000};
        for(unsigned i=0;i<4;i++) {
            *(uint32_t*)(uintptr_t)(p+0xcc)=badtasks[i]; CHECK(!ap_invincibility_candy_ready());
        }
        *(uint32_t*)(uintptr_t)(p+0xcc)=0x03001000;
        for(unsigned flags=2;flags<=16;flags*=2) {
            DEMO_PLAYBACK_FLAGS=flags;
            CHECK(ap_invincibility_candy_ready()==(flags==8));
        }
        DEMO_PLAYBACK_FLAGS=0;
        AI_KIRBY_STATE=200; CHECK(!ap_invincibility_candy_ready());
    }
    KIRBY_CURRENT_PLAYER=4; CHECK(!ap_invincibility_candy_ready());
    return 0;
}
'''
    path = tmp_path / "candy.c"
    path.write_text(source)
    exe = tmp_path / "candy"
    subprocess.run([cc, "-std=c99", "-O2", "-Wall", "-Wextra", "-Werror",
                    "-Wno-int-to-pointer-cast", "-I", str(PAYLOAD_DIR), str(path), "-o", str(exe)],
                   check=True, capture_output=True, text=True)
    subprocess.run([str(exe)], check=True)
