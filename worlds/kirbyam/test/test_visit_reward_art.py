"""First-area art follows the same native visit attribution as client checks."""
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


def test_generated_area_table_matches_client_eligibility() -> None:
    from ..client import KirbyAmClient
    from ..data import LocationCategory, data

    generator = WORLD / "tools" / "generate_visit_reward_art_rooms.py"
    subprocess.run([sys.executable, str(generator), "--check"], check=True)
    table = (PAYLOAD / "generated_visit_reward_art_rooms.inc").read_text()
    def values(name: str) -> list[int]:
        body = re.search(rf'{name}\[.*?= \{{(.*?)\}};', table, flags=re.S)
        assert body
        return list(map(int, re.findall(r"\b(\d+)u\b", body[1])))

    actual = values("ap_visit_areas")
    expected = KirbyAmClient._build_room_metadata_maps()[2]
    assert len(actual) == 288
    assert {i: area for i, area in enumerate(actual) if area} == {
        i: area for i, area in expected.items() if 0 <= i < len(actual)
    }
    assert set(actual) == set(range(10))
    kinds = values("ap_visit_room_kinds")
    assert len(kinds) == len(actual)
    assert {i: kind for i, kind in enumerate(kinds) if kind} == {
        loc.bit_index: 2 if "CoreLandmark" in loc.tags else 1
        for loc in data.locations.values() if loc.category == LocationCategory.ROOM_SANITY
    }


def test_exact_native_visit_callsite_guard() -> None:
    dummy = runpy.run_path(str(WORLD / "tools" / "create_dummy_rom.py"))["build_dummy_rom"]()
    call = patch_rom.ROOM_VISIT_REWARD_ART_CALLSITE
    target = 0x0815E102
    assert patch_rom.build_room_visit_reward_art_hook(dummy, target) == {
        call: patch_rom.thumb_bl_bytes(0x08000000 + call, target),
    }
    dummy[call + 2] ^= 1
    with pytest.raises(SystemExit, match="room visit reward art dispatch"):
        patch_rom.build_room_visit_reward_art_hook(dummy, target)


def test_native_first_visit_identity_and_transition_gates(tmp_path: Path) -> None:
    cc = shutil.which("cc")
    if not cc:
        pytest.skip("requires a native C compiler")
    source = tmp_path / "visit.c"
    source.write_text(r'''
#include <assert.h>
#include <stdint.h>
/* Only the GBA ELF build needs ROM sections; these are host behavior tests. */
#if defined(__MACH__)
#if defined(__clang__)
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wkeyword-macro"
#endif
#define __attribute__(...)
#endif
#include "visit_reward_art_runtime.h"
#include "generated_visit_reward_art_rooms.inc"
#if defined(__MACH__)
#undef __attribute__
#if defined(__clang__)
#pragma clang diagnostic pop
#endif
#endif

int main(void) {
    uint16_t visits[AP_VISIT_ENTRY_COUNT] = {0};
    struct ApRewardArtConfig art = {.marker = AP_REWARD_ART_MAGIC, .count = 1u,
        .keys = {AP_REWARD_KEY(AP_REWARD_ROOM, 77u)}, .variants = {AP_REWARD_TRAP}};
    assert(ap_visit_reward_arts(visits, ap_visit_areas, ap_visit_room_kinds, 77u, AP_VISIT_ALL_ROOMS, &art)
           == ap_reward_pair_add(AP_REWARD_TRAP + 1u, AP_REWARD_GEM));
    assert(ap_visit_reward_arts(visits, ap_visit_areas, ap_visit_room_kinds, 77u, AP_VISIT_CORE_ONLY, &art)
           == AP_REWARD_GEM + 1u);
    art.keys[1] = AP_REWARD_KEY(AP_REWARD_AREA, 2u);
    art.variants[1] = AP_REWARD_TRAP;
    art.count = 2u;
    assert(ap_visit_reward_arts(visits, ap_visit_areas, ap_visit_room_kinds, 77u, AP_VISIT_ALL_ROOMS, &art)
           == AP_REWARD_TRAP + 1u);
    art.variants[0] = AP_REWARD_MIRROR_SHARD;
    uint16_t pair = ap_visit_reward_arts(visits, ap_visit_areas, ap_visit_room_kinds, 77u, AP_VISIT_ALL_ROOMS, &art);
    assert((pair & 0xFFu) == AP_REWARD_TRAP + 1u);
    assert((pair >> 8) == AP_REWARD_MIRROR_SHARD + 1u);
    assert((ap_reward_pair_add(AP_REWARD_GEM + 1u, AP_REWARD_BATTERY) & 0xFFu) == AP_REWARD_BATTERY + 1u);
    assert(!ap_visit_is_first_area(visits, ap_visit_areas, AP_VISIT_ENTRY_COUNT));
    for (uint16_t i = 0; i < AP_VISIT_ENTRY_COUNT; ++i) {
        assert(ap_visit_is_first_area(visits, ap_visit_areas, i) == (ap_visit_areas[i] != 0u));
    }
    visits[0] = 3u; /* Door flags without the high bit do not represent arrival. */
    assert(ap_visit_areas[0] == 1u && ap_visit_areas[21] == 1u);
    assert(ap_visit_is_first_area(visits, ap_visit_areas, 21u));
    visits[0] = 0x8003u;
    assert(!ap_visit_is_first_area(visits, ap_visit_areas, 0u));
    assert(!ap_visit_is_first_area(visits, ap_visit_areas, 21u));
    assert(ap_visit_areas[77] == 2u);
    assert(ap_visit_is_first_area(visits, ap_visit_areas, 77u));
    assert(ap_visit_room_kinds[21] == 1u && ap_visit_room_kinds[80] == 2u);
    assert(!ap_visit_reward_arts(visits, ap_visit_areas, ap_visit_room_kinds, 21u, AP_VISIT_CORE_ONLY, &art));
    assert(!ap_visit_reward_arts(visits, ap_visit_areas, ap_visit_room_kinds, 21u, 0u, &art));
    assert(ap_visit_reward_arts(visits, ap_visit_areas, ap_visit_room_kinds, 21u, AP_VISIT_ALL_ROOMS, &art));
    visits[21] = 0x8000u;
    assert(!ap_visit_reward_arts(visits, ap_visit_areas, ap_visit_room_kinds, 21u, AP_VISIT_ALL_ROOMS, &art));
    visits[77] = 0x8000u;
    assert(!ap_visit_is_first_area(visits, ap_visit_areas, 80u));
    assert(ap_visit_reward_arts(visits, ap_visit_areas, ap_visit_room_kinds, 80u, AP_VISIT_CORE_ONLY, &art));
    assert(ap_visit_reward_arts(visits, ap_visit_areas, ap_visit_room_kinds, 80u, AP_VISIT_ALL_ROOMS, &art));
    visits[80] = 0x8000u;
    assert(!ap_visit_reward_arts(visits, ap_visit_areas, ap_visit_room_kinds, 80u, AP_VISIT_CORE_ONLY, &art));
    assert(!ap_visit_scene_ready(0xB00u, 0u, 0u, 0u));
    assert(!ap_visit_scene_ready(0u, 0xC00u, 0u, 0u));
    assert(!ap_visit_scene_ready(0u, 0u, 0x80u, 9u));
    assert(ap_visit_scene_ready(2u, 0u, 0x80u, 0u));
    assert(ap_visit_scene_ready(2u, 0u, 0x40u, 0u));
    return 0;
}
''')
    exe = tmp_path / ("test-visit-art.exe" if sys.platform == "win32" else "test-visit-art")
    subprocess.run([cc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-I", str(PAYLOAD),
                    str(source), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
