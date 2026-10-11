"""Execute Vitality collection and delayed popup hooks; no emulator claims."""
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest


def test_vitality_collection_defers_native_popup_reward(tmp_path):
    compiler = shutil.which("cc")
    if not sys.platform.startswith("linux") or not compiler:
        pytest.skip("requires Linux low-address memory and a C compiler")
    payload = (Path(__file__).resolve().parents[1] / "kirby_ap_payload/ap_payload.c").read_text()
    bodies = []
    for name in ("ap_on_collect_vitality_chest", "ap_on_minor_chest_reward_popup"):
        match = re.search(r"[^\n]*\b" + name + r"\([^)]*\)\s*\{", payload)
        assert match
        end, depth = match.end(), 1
        while depth:
            depth += (payload[end] == "{") - (payload[end] == "}")
            end += 1
        bodies.append(payload[match.start():end].replace(
            'register uint32_t chest_obj_ptr asm("r5");', 'uint32_t chest_obj_ptr = TEST_CHEST;'
        ).replace('register uint32_t popup_obj_ptr asm("r8");', 'uint32_t popup_obj_ptr = TEST_POPUP;'))
    source = r'''
#define _GNU_SOURCE
#include <stdint.h>
#include <sys/mman.h>
#define TEST_CHEST 0x03000100u
#define TEST_POPUP 0x03000500u
#define AP_MINOR_CHEST_ITEM_SUPPRESSION_MARKER 0x41504348u
#define KIRBY_MINOR_CHEST_NO_NATIVE_ITEM 0x63u
#define CHECK(x) do { if (!(x)) return __LINE__; } while (0)
static uint16_t checked_room;
static void ap_set_vitality_chest_flag_for_room(uint16_t room) { checked_room=room; }
''' + '\n'.join(bodies) + r'''
int main(void) {
    const uint16_t rooms[] = {739,815,610,403};
    CHECK(mmap((void*)0x03000000,0x8000,PROT_READ|PROT_WRITE,
        MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0)==(void*)0x03000000);
    *(uint32_t*)(TEST_POPUP+0x4C)=TEST_CHEST;
    for (unsigned i=0;i<4;i++) {
        *(uint16_t*)(TEST_CHEST+0x60)=rooms[i];
        *(uint16_t*)(TEST_CHEST+0xE0)=6;
        ap_on_collect_vitality_chest();
        CHECK(checked_room==rooms[i]);
        /* Preserve the native reward through initial popup presentation. */
        CHECK(*(uint16_t*)(TEST_CHEST+0xE0)==6);
        ap_on_minor_chest_reward_popup();
        /* Native 0x63 branch increments room completion without HP/heal. */
        CHECK(*(uint16_t*)(TEST_CHEST+0xE0)==0x63);
        CHECK(*(uint32_t*)(TEST_CHEST+0xDC)==0);
        ap_on_minor_chest_reward_popup();
        CHECK(*(uint16_t*)(TEST_CHEST+0xE0)==0x63);
    }
    return 0;
}
'''
    path, executable = tmp_path / "vitality.c", tmp_path / "vitality"
    path.write_text(source)
    result = subprocess.run([compiler, "-Wall", "-Wextra", "-Werror", "-Wno-int-to-pointer-cast",
                             str(path), "-o", str(executable)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    result = subprocess.run([str(executable)], capture_output=True, text=True)
    assert result.returncode == 0, f"Vitality hook contract failed at C line {result.returncode}"
