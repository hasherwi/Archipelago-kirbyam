"""Cross-feature room-counter contract for suppressed chest rewards and levers."""
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest

from .test_runtime_regression_hooks import _function


PAYLOAD_DIR = Path(__file__).resolve().parents[1] / "kirby_ap_payload"


def test_suppressed_ordinary_popup_does_not_increment_native_room_counter(tmp_path: Path) -> None:
    """Execute the actual popup hook and counter wrapper together.

    Native chest.c creates ordinary bonuses with unk2=0/unk3=31; bonus.c
    deliberately omits their room-counter increment. Converting an AP-owned
    reward to 0x63 must not accidentally take the native lever-counter branch.
    """
    compiler = shutil.which("cc") or shutil.which("clang") or shutil.which("gcc")
    if not sys.platform.startswith("linux") or compiler is None:
        pytest.skip("requires Linux low-address test memory and a native C compiler")
    payload = (PAYLOAD_DIR / "ap_payload.c").read_text(encoding="utf-8")
    table = re.search(r"static const uint32_t AP_OWNED_MINOR_CHEST_SOURCE_PTRS\[\] = \{.*?\n\};", payload, re.S)
    assert table is not None
    functions = "\n\n".join(_function(payload, name) for name in (
        "ap_is_ap_owned_minor_chest_source", "ap_lever_bit_for_obj",
        "ap_on_minor_chest_reward_popup", "ap_on_chest_popup_room_counter",
    ))
    functions = functions.replace('register uint32_t popup_obj_ptr asm("r8");',
                                  'uint32_t popup_obj_ptr = TEST_POPUP;')
    harness = r'''
#define _GNU_SOURCE
#include <stdint.h>
#include <string.h>
#include <sys/mman.h>
#include "lever_runtime_logic.h"
#define CHECK(value) do { if (!(value)) return __LINE__; } while (0)
#define TEST_CHEST 0x03000100u
#define TEST_POPUP 0x03000500u
#define AP_MINOR_CHEST_ITEM_SUPPRESSION_MARKER 0x41504348u
#define KIRBY_MINOR_CHEST_NO_NATIVE_ITEM 0x63u
static uint32_t counters[4];
static void native_counter(uint32_t slot, uint32_t amount) { counters[slot] += amount; }
#define KIRBY_ROOM_COUNTER_FN native_counter
'''
    harness += table.group(0) + "\n" + functions
    harness += r'''
int main(void) {
    uint8_t *chest = (void*)TEST_CHEST;
    const uint32_t levers[] = {0x088BE07Cu, 0x088CD240u, 0x088D2E68u, 0x088D1454u};
    const uint8_t lever_ids[] = {18u, 65u, 77u, 74u};
    const uint16_t native_rewards[] = {6u, 0x14u, 0x29u};
    uint32_t reward, i;
    CHECK(mmap((void*)0x03000000, 0x8000, PROT_READ|PROT_WRITE,
        MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED, -1, 0) == (void*)0x03000000);
    *(uint32_t*)(TEST_POPUP + 0x4Cu) = TEST_CHEST;
    CHECK(ap_is_ap_owned_minor_chest_source(0x088B6510u));
    for (reward = 0; reward <= 5u; ++reward) {
        memset(chest, 0, 0x100);
        *(uint32_t*)(chest + 0xB0) = 0x088B6510u;
        *(uint16_t*)(chest + 0xE0) = (uint16_t)reward;
        *(uint32_t*)(chest + 0xDC) = AP_MINOR_CHEST_ITEM_SUPPRESSION_MARKER;
        ap_on_minor_chest_reward_popup();
        CHECK(*(uint16_t*)(chest + 0xE0) == 0x63u);
        CHECK(*(uint32_t*)(chest + 0xDC) == 0u);
        ap_on_chest_popup_room_counter(1u, 1u);
        CHECK(counters[1] == 0u);
    }
    for (i = 0; i < 4; ++i) {
        *(uint32_t*)(chest + 0xB0) = levers[i];
        *(uint16_t*)(chest + 0xE0) = 0x63u;
        chest[0xE2] = lever_ids[i];
        ap_on_chest_popup_room_counter(1u, 1u);
        CHECK(counters[1] == 0u);
    }
    /* Native vitality/collection side effects must remain even on owned sources. */
    *(uint32_t*)(chest + 0xB0) = 0x088B6510u;
    for (i = 0; i < 3; ++i) {
        *(uint16_t*)(chest + 0xE0) = native_rewards[i];
        ap_on_minor_chest_reward_popup();
        CHECK(*(uint16_t*)(chest + 0xE0) == native_rewards[i]);
        ap_on_chest_popup_room_counter(2u, 1u);
        CHECK(counters[2] == i + 1u);
    }
    /* An unrelated native 0x63 chest is not an AP-owned suppressed source. */
    *(uint32_t*)(chest + 0xB0) = 0x08800000u;
    *(uint16_t*)(chest + 0xE0) = 0x63u;
    ap_on_chest_popup_room_counter(3u, 2u);
    CHECK(counters[3] == 2u);
    return 0;
}
'''
    source = tmp_path / "chest_counter.c"
    executable = tmp_path / "chest_counter"
    source.write_text(harness, encoding="utf-8")
    compiled = subprocess.run([compiler, "-std=c99", "-Wall", "-Wextra", "-Werror",
                               "-Wno-int-to-pointer-cast",
                               "-I", str(PAYLOAD_DIR), str(source), "-o", str(executable)],
                              capture_output=True, text=True, check=False)
    assert compiled.returncode == 0, compiled.stdout + compiled.stderr
    executed = subprocess.run([str(executable)], capture_output=True, text=True, check=False)
    assert executed.returncode == 0, f"native chest-counter contract failed at C line {executed.returncode}"
