"""Execute the actual request hook for verified native Mini-star recovery."""
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from .test_runtime_regression_hooks import PAYLOAD_DIR, _function, patch_rom


def test_mini_star_callsite_validation():
    rom = bytearray(0xA0000)
    offset = 0x9C69C
    rom[offset - 12:offset] = bytes.fromhex("2c 1c 84 34 20 78 80 21 01 43 30 1c")
    rom[offset:offset + 4] = patch_rom.thumb_bl_bytes(0x08000000 + offset, 0x080547C4)
    patch_rom.validate_mini_star_callsite(rom)
    for index in range(offset - 12, offset + 4):
        rom[index] ^= 1
        with pytest.raises(SystemExit, match="Mini star source ABI"):
            patch_rom.validate_mini_star_callsite(rom)
        rom[index] ^= 1


def test_mini_star_native_hook(tmp_path: Path):
    compiler = shutil.which("cc") or shutil.which("gcc")
    if not compiler or sys.platform not in ("linux", "win32"):
        pytest.skip("requires native compiler and fixed-address test allocation")
    source = (PAYLOAD_DIR / "ap_payload.c").read_text(encoding="utf-8")
    names = ("ap_mix_u32", "ap_next_rng_u32", "ap_select_random_allowed_ability",
             "ap_is_locked_gated_ability", "ap_select_random_allowed_ability_excluding",
             "ap_enemy_seed_source_allows", "ap_on_request_copy_ability_transition_c")
    functions = "\n".join(_function(source, name) for name in names)
    functions = functions.replace("noinline, long_call,", "noinline,")
    constants = source[source.index("#define ABILITY_RANDOMIZATION_MODE_SHUFFLED"):
                       source.rfind("\n", 0, source.index("uint32_t ap_mix_u32"))]
    harness = r'''
#define _GNU_SOURCE
#include <stdint.h>
#ifdef _WIN32
#include <windows.h>
#define ALLOC(p,n) VirtualAlloc((void*)(uintptr_t)(p), n, MEM_RESERVE|MEM_COMMIT, PAGE_READWRITE)
#else
#include <sys/mman.h>
#define ALLOC(p,n) mmap((void*)(uintptr_t)(p), n, PROT_READ|PROT_WRITE, MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED, -1, 0)
#endif
#include "enemy_runtime_logic.h"
#define CHECK(c) do { if (!(c)) return __LINE__; } while (0)
static uint32_t AP_ABILITY_RANDOMIZATION_MODE, AP_ABILITY_RANDOMIZATION_SEED_LO;
static uint32_t AP_ABILITY_RANDOMIZATION_SEED_HI, AP_ABILITY_RANDOMIZATION_NO_ABILITY_WEIGHT;
static uint32_t AP_ABILITY_RANDOMIZATION_ALLOWED_MASK, AP_ABILITY_RANDOMIZATION_RNG_STATE;
static uint32_t AP_ABILITY_GATE_MASK, AP_ABILITY_UNLOCK_MASK, gApRandomizeMinny;
static uint32_t AP_ABILITY_REROLL_SOURCE_ADDR, AP_ABILITY_REROLL_ABILITY_ID;
static uint32_t AP_ABILITY_REROLL_SOURCE_KIND, AP_ABILITY_REROLL_CALLSITE_PC;
static uint32_t AP_ABILITY_REROLL_KIRBY_INDEX, AP_ABILITY_REROLL_EVENT_COUNTER;
static uint32_t KIRBY_CURRENT_PLAYER, result;
static const uint32_t gApEnemySourceConfig[9] = { AP_ENEMY_SOURCE_CONFIG_LEGACY };
static void native_transition(void *kirby, uint32_t flags) { (void)kirby; result = flags; }
#define KIRBY_REQUEST_ABILITY_TRANSITION_FN native_transition
'''
    harness += constants + functions + r'''
static void grant(uint32_t pc, uint32_t ptr, uint32_t flags) {
    ap_on_request_copy_ability_transition_c(0, flags, ptr, (pc + 4u) | 1u);
}
int main(void) {
    uint8_t *object = ALLOC(0x02000000u, 0x40000);
    uint8_t *fallback = ALLOC(0x03000000u, 0x8000);
    uint32_t mode, type, unlocked, extra, i, before;
    uint32_t bad[] = {0u, 0x02000001u, 0x0203FFFFu, 0x03007FFFu};
    CHECK((uintptr_t)object == 0x02000000u && (uintptr_t)fallback == 0x03000000u);
    AP_ABILITY_RANDOMIZATION_ALLOWED_MASK = 1u << 2;
    for (mode=0; mode<3; mode++) for (type=0xA3; type<=0xA4; type++)
    for (unlocked=0; unlocked<2; unlocked++) for (extra=0; extra<0x80; extra+=0x20) {
        AP_ABILITY_RANDOMIZATION_MODE=mode;
        AP_ABILITY_GATE_MASK=1u<<23;
        AP_ABILITY_UNLOCK_MASK=unlocked ? 1u<<23 : 0;
        object[0x82]=fallback[0x82]=type;
        AP_ABILITY_RANDOMIZATION_RNG_STATE=0;
        before=AP_ABILITY_REROLL_EVENT_COUNTER;
        grant(0x0809C69C, 0x02000000, 0x97|extra);
        CHECK(result == ((unlocked ? 0x97u : 0x80u)|extra));
        grant(0x0809C69C, 0x03000000, 0x97|extra);
        CHECK(result == ((unlocked ? 0x97u : 0x80u)|extra));
        CHECK(AP_ABILITY_RANDOMIZATION_RNG_STATE==0);
        if (mode==2) CHECK(AP_ABILITY_REROLL_EVENT_COUNTER==before);
    }
    AP_ABILITY_RANDOMIZATION_MODE=2;
    AP_ABILITY_GATE_MASK=AP_ABILITY_UNLOCK_MASK=0;
    object[0x82]=0xA3;
    /* Other raw stars reroll, including when their randomized output is Mini. */
    grant(0x0809C69C, 0x02000000, 0x81);
    CHECK(result==0x82);
    AP_ABILITY_RANDOMIZATION_ALLOWED_MASK=1u<<23;
    grant(0x0809C69C, 0x02000000, 0x81);
    CHECK(result==0x97 && AP_ABILITY_RANDOMIZATION_RNG_STATE!=0);
    AP_ABILITY_GATE_MASK=1u<<23;
    grant(0x0809C69C, 0x02000000, 0x81);
    CHECK(result==0x80);
    AP_ABILITY_GATE_MASK=0;
    AP_ABILITY_RANDOMIZATION_ALLOWED_MASK=1u<<2;
    /* No leak through unknown callers, invalid sources, missing flag or enemy Mini. */
    grant(0x08089050, 0x02000000, 0x97); CHECK(result==0x82);
    grant(0x0809C69C, 0x02000000, 23); CHECK(result==2);
    for(i=0;i<sizeof(bad)/sizeof(*bad);i++) {
        grant(0x0809C69C,bad[i],0x97); CHECK(result==0x82);
    }
    object[0x82]=1;
    grant(0x0809C69C,0x02000000,0x97); CHECK(result==0x82);
    grant(AP_ENEMY_SWALLOW_CALLSITE,0x02000000,23); CHECK(result==2);
    /* Existing native-star Normal weighting is unchanged outside Mini recovery. */
    object[0x82]=0xA4;
    AP_ABILITY_RANDOMIZATION_NO_ABILITY_WEIGHT=100;
    grant(0x0809C69C,0x02000000,0x81); CHECK(result==0x80);
    before=AP_ABILITY_RANDOMIZATION_RNG_STATE;
    grant(0x0809C69C,0x02000000,0x97); CHECK(result==0x97);
    CHECK(before==AP_ABILITY_RANDOMIZATION_RNG_STATE);
    return 0;
}
'''
    c_file = tmp_path / "mini_star.c"
    executable = tmp_path / ("mini_star.exe" if sys.platform == "win32" else "mini_star")
    c_file.write_text(harness, encoding="utf-8")
    subprocess.run([compiler, "-std=c99", "-O2", "-Wall", "-Wextra", "-Werror",
                    "-Wno-int-to-pointer-cast", "-I", str(PAYLOAD_DIR), str(c_file),
                    "-o", str(executable)], check=True, capture_output=True, text=True)
    subprocess.run([str(executable)], check=True, capture_output=True, text=True)
