"""Execute actual collection wrappers with host stand-ins for r5 and RAM.

This tests source dispatch and reward fields, not ARM register ABI or gameplay.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

WORLD = Path(__file__).resolve().parents[1]


def test_actual_collection_wrappers_suppress_all_owned_collections_and_preserve_unknown_sources(tmp_path: Path) -> None:
    compiler = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
    if compiler is None:
        pytest.skip("requires a native C compiler")
    payload = (WORLD / "kirby_ap_payload/ap_payload.c").read_text()
    functions = []
    for name in ("ap_is_ap_owned_minor_chest_source", "ap_set_sound_player_chest_flag",
                 "ap_on_collect_spray_paint_chest", "ap_on_collect_sound_player_chest"):
        match = re.search(r"[^\n]*\b" + name + r"\([^)]*\)\s*\{", payload)
        assert match
        end, depth = match.end(), 1
        while depth:
            depth += (payload[end] == "{") - (payload[end] == "}")
            end += 1
        functions.append(payload[match.start():end].replace(
            'register uint32_t chest_obj_ptr asm("r5");',
            'uintptr_t chest_obj_ptr = (uintptr_t)chest;'))
    table = re.search(r"static const uint32_t AP_OWNED_MINOR_CHEST_SOURCE_PTRS\[\] = \{.*?\};",
                      payload, re.S)
    assert table
    entries = json.loads((WORLD / "data/minor_chest_manifest.json").read_text())["entries"]
    cases = []
    for entry in entries:
        reward = entry["native_reward_id"]
        if 0x14 <= reward <= 0x21 or 0x29 <= reward <= 0x32:
            offset = entry["rom_offset"]
            offset = int(offset, 0) if isinstance(offset, str) else offset
            cases.append(f"{{0x{0x08000000 + offset:X}u, {reward}u, 1u}}")
    assert len(cases) == 24
    prelude = r'''
#include <stdint.h>
#include <string.h>
#include "minor_chest_runtime_logic.h"
static uint32_t chest_words[64];
#define chest ((unsigned char *)chest_words)
static uint32_t spray, music, checks;
#define KIRBY_SPRAY_PAINT_FLAGS spray
#define KIRBY_MUSIC_PLAYER_AND_SHEETS_FLAGS music
#define AP_SOUND_PLAYER_CHEST_FLAGS checks
#define CHECK(x) do { if (!(x)) return __LINE__; } while (0)
'''
    harness = prelude + table.group() + "\n" + "\n".join(functions) + r'''
struct Case { uint32_t source, reward, owned; };
static const struct Case cases[] = {''' + ",\n".join(cases) + r'''};
int main(void) {
    for (unsigned i=0; i<24; i++) {
        const struct Case *c=&cases[i];
        uint32_t index=c->reward < 0x28 ? c->reward-0x14 : c->reward-0x28;
        for (unsigned fallback=0; fallback<2; fallback++) {
            uint32_t source=fallback ? 0x08000000u : c->source;
            memcpy(chest+0xB0, &source, sizeof(source));
            spray=0x80000000u; music=0x40000001u; checks=0;
            if(c->reward < 0x28) {
                ap_on_collect_spray_paint_chest(index);
                CHECK(spray==(0x80000000u | ((!fallback && c->owned) ? 0u : 1u<<index)));
                CHECK(music==0x40000001u);
            } else {
                ap_on_collect_sound_player_chest(index);
                CHECK(music==(0x40000001u | ((!fallback && c->owned) ? 0u : 1u<<index)));
                CHECK(spray==0x80000000u);
            }
            CHECK(checks==0);
            uint32_t prior_spray=spray, prior_music=music;
            ap_on_collect_sound_player_chest(0);
            CHECK(checks==1 && spray==prior_spray && music==prior_music);
            ap_on_collect_spray_paint_chest(14);
            ap_on_collect_sound_player_chest(11);
            ap_on_collect_spray_paint_chest(0xFFFFFFFFu);
            ap_on_collect_sound_player_chest(0xFFFFFFFFu);
            CHECK(spray==prior_spray && music==prior_music);
        }
    }
    return 0;
}
'''
    source, executable = tmp_path / "wrappers.c", tmp_path / "wrappers"
    source.write_text(harness)
    built = subprocess.run([compiler, "-std=c99", "-Wall", "-Wextra", "-Werror",
                            "-I", str(WORLD / "kirby_ap_payload"), str(source), "-o", str(executable)],
                           capture_output=True, text=True)
    assert built.returncode == 0, built.stdout + built.stderr
    run = subprocess.run([str(executable)], capture_output=True, text=True)
    assert run.returncode == 0, f"actual wrapper contract line {run.returncode}: {run.stderr}"
