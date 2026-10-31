"""Execute the actual live transition hook with native memory and mailbox stubs."""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from .test_runtime_regression_hooks import PAYLOAD_DIR, _function, patch_rom
from .test_rom_tokens import _DummyPatch, _make_world
from ..rom import ABILITY_RANDOMIZATION_MINNY_ROM_OFFSET, write_tokens
from typing import Any, cast


@pytest.mark.parametrize("include", [False, True, None])
@pytest.mark.parametrize("mode", [0, 1, 2])
def test_minny_rom_policy(mode: int, include: bool | None) -> None:
    world = _make_world(mode)
    world._enemy_copy_ability_policy = {"mode": mode, "allowed_abilities": ["Mini", "Beam"]}
    if include is not None:
        world._enemy_copy_ability_policy["ability_randomization_minny"] = include
    patch = _DummyPatch()
    write_tokens(cast(Any, world), cast(Any, patch))
    assert [(offset, value) for _, offset, value in patch.token_writes
            if offset == ABILITY_RANDOMIZATION_MINNY_ROM_OFFSET] == [
        (0x15F68C, int(include is not False).to_bytes(4, "little"))
    ]


def test_minny_native_hook(tmp_path: Path) -> None:
    compiler = shutil.which("cc")
    if not sys.platform.startswith("linux") or not compiler:
        pytest.skip("requires Linux low-address memory and a native C compiler")
    source = (PAYLOAD_DIR / "ap_payload.c").read_text(encoding="utf-8")
    names = ("ap_mix_u32", "ap_next_rng_u32", "ap_select_random_allowed_ability",
             "ap_is_locked_gated_ability", "ap_select_random_allowed_ability_excluding",
             "ap_on_request_copy_ability_transition_c")
    functions = "\n".join(_function(source, name) for name in names)
    constants = source[source.index("#define ABILITY_RANDOMIZATION_MODE_SHUFFLED"):
                       source.index("static uint32_t ap_mix_u32")]
    harness = r'''
#define _GNU_SOURCE
#include <stdint.h>
#include <sys/mman.h>
#include "enemy_runtime_logic.h"
#define CHECK(c) do { if (!(c)) return __LINE__; } while (0)
static uint32_t AP_ABILITY_RANDOMIZATION_MODE, AP_ABILITY_RANDOMIZATION_SEED_LO;
static uint32_t AP_ABILITY_RANDOMIZATION_SEED_HI, AP_ABILITY_RANDOMIZATION_NO_ABILITY_WEIGHT;
static uint32_t AP_ABILITY_RANDOMIZATION_ALLOWED_MASK, AP_ABILITY_RANDOMIZATION_RNG_STATE;
static uint32_t AP_ABILITY_GATE_MASK, AP_ABILITY_UNLOCK_MASK, gApRandomizeMinny;
static uint32_t AP_ABILITY_REROLL_SOURCE_ADDR, AP_ABILITY_REROLL_ABILITY_ID;
static uint32_t AP_ABILITY_REROLL_SOURCE_KIND, AP_ABILITY_REROLL_CALLSITE_PC;
static uint32_t AP_ABILITY_REROLL_KIRBY_INDEX, AP_ABILITY_REROLL_EVENT_COUNTER;
static uint32_t KIRBY_CURRENT_PLAYER, result, calls;
static void native_transition(void *kirby, uint32_t flags) { (void)kirby; result = flags; calls++; }
#define KIRBY_REQUEST_ABILITY_TRANSITION_FN native_transition
'''
    harness += constants + functions + r'''
static void grant(uint32_t pc, uint32_t ptr, uint32_t flags) {
    ap_on_request_copy_ability_transition_c(0, flags, ptr, (pc + 4u) | 1u);
}
int main(void) {
    uint8_t *object = mmap((void*)0x02000000u, 0x40000, PROT_READ | PROT_WRITE,
                          MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED, -1, 0);
    uint8_t *fallback = mmap((void*)0x03000000u, 0x8000, PROT_READ | PROT_WRITE,
                            MAP_PRIVATE | MAP_ANONYMOUS | MAP_FIXED, -1, 0);
    uint32_t upper, mode, i, before;
    uint32_t bad_ptrs[] = {0u, 0x03007FFFu, 0x0203FFFFu, 0x0203FF7Eu, 0x02000001u};
    CHECK(object != MAP_FAILED && fallback != MAP_FAILED);
    fallback[0x82] = AP_ENEMY_MINNY_TYPE;
    object[0x82] = AP_ENEMY_MINNY_TYPE;
    AP_ABILITY_RANDOMIZATION_ALLOWED_MASK = 1u << 2;
    AP_ABILITY_RANDOMIZATION_MODE = 2;
    /* Excluded Minny preserves all input flags, consumes no RNG, emits no reroll. */
    for (upper = 0; upper < 256; upper += 32) {
        grant(AP_ENEMY_SWALLOW_CALLSITE, 0x02000000u, upper | 23u);
        CHECK(result == (upper | 23u));
    }
    CHECK(calls == 8 && AP_ABILITY_RANDOMIZATION_RNG_STATE == 0);
    CHECK(AP_ABILITY_REROLL_EVENT_COUNTER == 0);
    grant(AP_ENEMY_SWALLOW_CALLSITE, 0x03000000u, 23u);
    CHECK(result == 23 && AP_ABILITY_RANDOMIZATION_RNG_STATE == 0);
    /* Final gating is still authoritative on the excluded path. */
    AP_ABILITY_GATE_MASK = 1u << 23;
    grant(AP_ENEMY_SWALLOW_CALLSITE, 0x02000000u, 23u);
    CHECK(result == 0);
    AP_ABILITY_UNLOCK_MASK = 1u << 23;
    grant(AP_ENEMY_SWALLOW_CALLSITE, 0x02000000u, 23u);
    CHECK(result == 23);
    AP_ABILITY_GATE_MASK = AP_ABILITY_UNLOCK_MASK = 0;
    /* Opted-in Minny rerolls, including weighted Normal. */
    gApRandomizeMinny = 1;
    grant(AP_ENEMY_SWALLOW_CALLSITE, 0x02000000u, 23u);
    CHECK(result == 2 && AP_ABILITY_REROLL_SOURCE_ADDR == 0x3519F6u);
    CHECK(AP_ABILITY_REROLL_CALLSITE_PC == AP_ENEMY_SWALLOW_CALLSITE);
    AP_ABILITY_RANDOMIZATION_NO_ABILITY_WEIGHT = 100;
    grant(AP_ENEMY_SWALLOW_CALLSITE, 0x02000000u, 23u);
    CHECK(result == 0);
    AP_ABILITY_RANDOMIZATION_NO_ABILITY_WEIGHT = 0;
    gApRandomizeMinny = 0;
    /* Other enemies granting Mini must still reroll. */
    object[0x82] = 1;
    grant(AP_ENEMY_SWALLOW_CALLSITE, 0x02000000u, 23u);
    CHECK(result == 2);
    /* Star/effect callers cannot borrow a coincidental Minny byte in r5. */
    object[0x82] = AP_ENEMY_MINNY_TYPE;
    grant(0x0809C69Cu, 0x02000000u, 0x80u | 23u);
    CHECK(result == (0x80u | 2u));
    grant(0x08089050u, 0x02000000u, 23u);
    CHECK(result == 2);
    for (i = 0; i < sizeof(bad_ptrs)/sizeof(*bad_ptrs); i++) {
        grant(AP_ENEMY_SWALLOW_CALLSITE, bad_ptrs[i], 23u);
        CHECK(result == 2);
    }
    /* Included candidates remain gated; an empty unlocked pool gives Normal. */
    AP_ABILITY_GATE_MASK = 1u << 2;
    grant(0x0809C69Cu, 0x02000000u, 0x80u | 23u);
    CHECK(result == 0x80u);
    AP_ABILITY_GATE_MASK = 0;
    before = AP_ABILITY_RANDOMIZATION_RNG_STATE;
    for (mode = 0; mode < 2; mode++) {
        AP_ABILITY_RANDOMIZATION_MODE = mode;
        gApRandomizeMinny = 1;
        grant(AP_ENEMY_SWALLOW_CALLSITE, 0x02000000u, 23u);
        CHECK(result == 23 && AP_ABILITY_RANDOMIZATION_RNG_STATE == before);
    }
    return 0;
}
'''
    c_file = tmp_path / "minny.c"
    executable = tmp_path / "minny"
    c_file.write_text(harness, encoding="utf-8")
    subprocess.run([compiler, "-std=c99", "-O2", "-Wall", "-Wextra", "-Werror",
                    "-Wno-int-to-pointer-cast", "-I", str(PAYLOAD_DIR), str(c_file),
                    "-o", str(executable)], check=True, capture_output=True, text=True)
    subprocess.run([str(executable)], check=True, capture_output=True, text=True)


def test_minny_callsite_validation() -> None:
    rom = bytearray(0xA0000)
    offset = patch_rom.MINNY_SWALLOW_CALL_OFFSET
    rom[offset - 8:offset] = bytes.fromhex("2c 1c 84 34 21 78 30 1c")
    rom[offset:offset + 4] = patch_rom.thumb_bl_bytes(0x08000000 + offset, 0x080547C4)
    patch_rom.validate_minny_swallow_callsite(rom)
    rom[offset - 8] ^= 1
    with pytest.raises(SystemExit, match="Minny source ABI"):
        patch_rom.validate_minny_swallow_callsite(rom)
