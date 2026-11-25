"""One seed assignment drives world statue art/grants without altering room 970."""
from pathlib import Path
import random
import re
import runpy
import shutil
import subprocess
from typing import Any, cast

import pytest

from ..ability_randomization import build_enemy_copy_ability_policy
from ..enemy_ability_runtime_patch import _STATUE_TABLES, build_enemy_copy_runtime_patch_writes
from ..rom import KirbyAmPatchExtension, write_tokens
from ..statue_seed import (
    COPY_ABILITY_ROOM, STATUE_CONFIG_EMPTY, STATUE_CONFIG_MARKER, STATUE_CONFIG_ROM_OFFSET,
    STATUE_SLOT_ADDRESSES,
)
from ..traversal import Node, Placement, Position, SourcePolicy, TraversalGraph
from .test_rom_tokens import _DummyPatch, _make_world
from .test_runtime_regression_hooks import patch_rom


WORLD = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('mode,toggle', [(0, False), (0, True), (1, False), (1, True), (2, False), (2, True)])
def test_seed_keeps_vanilla_tables_and_serializes_exact_preview_assignment(mode, toggle):
    world = _make_world(mode, randomize_statues=toggle)
    policy = build_enemy_copy_ability_policy(
        random.Random(1), mode, True, True, whitelist=("Sword", "UFO"), no_ability_weight=100,
    )
    world._enemy_copy_ability_policy = policy
    patch = _DummyPatch()
    write_tokens(cast(Any, world), cast(Any, patch))
    writes = {offset: value for _, offset, value in patch.token_writes}
    assert not (set(writes) & set(STATUE_SLOT_ADDRESSES))
    assignments = build_enemy_copy_runtime_patch_writes(policy, include_statues=toggle)
    expected = (STATUE_CONFIG_MARKER + bytes([mode])
                + bytes(assignments[a] for a in STATUE_SLOT_ADDRESSES)
                if mode and toggle else STATUE_CONFIG_EMPTY)
    assert writes[STATUE_CONFIG_ROM_OFFSET] == expected


@pytest.mark.parametrize('mode', [1, 2])
def test_world_and_copy_room_share_subtype_not_grant_or_retry_policy(mode):
    policy = SourcePolicy(build_enemy_copy_ability_policy(
        random.Random(3), mode, True, True, whitelist=("UFO",), no_ability_weight=100,
    ), include_statues=True)
    for base, native in _STATUE_TABLES:
        for subtype, ability in enumerate(native):
            key = f'STATUE:{base + subtype:06X}'
            world = policy.grant(key, lambda _: True, native_room=190)
            fixed = policy.grant(key, lambda _: True, native_room=COPY_ABILITY_ROOM)
            locked = policy.grant(key, lambda name: name != ability, native_room=COPY_ABILITY_ROOM)
            assert world.abilities == {"UFO"} and world.randomized == (mode == 2)
            assert fixed.guaranteed == {ability} and not fixed.randomized
            assert not locked.abilities

    key = "STATUE:3538FC"  # Beam sculpture, world policy replaces with UFO.
    graph = TraversalGraph((Node("outside", 190), Node("copy", 970)), (),
                           (Placement("outside", key, renewable=True, retry_evidence="world retouch"),
                            Placement("copy", key, frozenset({"Copy Ability Room Access"}), renewable=True)),
                           (Position("outside"), Position("copy")), frozenset())
    owned = frozenset({"Copy Ability Room Access", "Beam Ability", "UFO Ability"})
    combined = graph.evaluate(policy, owned, True, allow_documented_retries=True)
    assert any(p.node == "outside" and p.equipped == "UFO" for p in combined.positions)
    assert any(p.node == "copy" and p.equipped == "Beam" for p in combined.positions)
    assert not any(p.node == "copy" and p.equipped == "UFO" for p in combined.positions)


def test_rom_guard_and_three_patch_sites_are_pinned():
    dummy = runpy.run_path(str(WORLD / "tools" / "create_dummy_rom.py"))["build_dummy_rom"]()
    targets = {name: 0x0815E800 for name, _, _ in patch_rom.WORLD_STATUE_HOOK_GROUPS}
    changes = patch_rom.build_world_statue_hooks(dummy, targets)
    assert set(changes) == {0x099E42, 0x0AA4B0, 0x0AA4CE, 0x09A884, 0x09A8B0, 0x09D868, 0x09A97E, 0x09D8B8}
    for offset in changes:
        corrupted = bytearray(dummy)
        corrupted[offset] ^= 1
        with pytest.raises(SystemExit, match="native world statue call"):
            patch_rom.build_world_statue_hooks(corrupted, targets)
    # Do not apply a retail delta to fabricated zero source data: bsdiff can
    # reuse arbitrary retail bytes even in the appended region.
    base = bytes(STATUE_CONFIG_ROM_OFFSET) + STATUE_CONFIG_EMPTY
    assert KirbyAmPatchExtension.validate_statue_seed_base(None, base) is base
    for rel in (0, 8, 27):
        corrupt = bytearray(base)
        corrupt[STATUE_CONFIG_ROM_OFFSET + rel] ^= 1
        with pytest.raises(ValueError, match="Statue assignment marker"):
            KirbyAmPatchExtension.validate_statue_seed_base(None, corrupt)
    logo_header = (WORLD / "kirby_ap_payload" / "statue_logo.h").read_text()
    logo = bytes(int(h, 16) for h in re.findall(r"0x([0-9A-F]{2})", logo_header))
    assert len(logo) == 128
    assert {value for b in logo for value in (b & 15, b >> 4)} == {0, 1, 4, 6, 8, 12, 13}


def test_runtime_uses_same_slot_and_preserves_owned_dma_shape(tmp_path):
    cc = shutil.which("cc")
    if cc is None:
        pytest.skip("requires a native C compiler")
    c = tmp_path / "statue.c"
    c.write_text(r'''
#include <assert.h>
#include "statue_art_runtime.h"
#include "statue_runtime_logic.h"
int main(void) {
    struct ApStatueConfig cfg = { .magic = "APST01" };
    const uint8_t variant[] = {11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,29,26,27,28};
    const uint8_t type[] = {0x92,0x92,0x92,0x92,0x92,0x92,0x92,0x92,0x93,0x93,
                            0x93,0x93,0x93,0x93,0x93,0x94,0x95,0x95,0x95};
    for (unsigned i = 0; i < 19; ++i) {
        cfg.assignments[i] = i + 1;
        cfg.mode = 0;
        assert(!ap_statue_world_art(190, type[i], variant[i], &cfg));
        cfg.mode = 1;
        assert(ap_statue_world_art(190, type[i], variant[i], &cfg) == i + 1);
        assert(!ap_statue_world_art(970, type[i], variant[i], &cfg));
        assert(!ap_statue_world_ability(970, type[i], 0, &cfg));
        cfg.mode = 2;
        assert(ap_statue_world_art(190, type[i], variant[i], &cfg) == AP_STATUE_LOGO);
        assert(!ap_statue_world_art(970, type[i], variant[i], &cfg));
        assert(!ap_statue_world_mode(970, &cfg));
    }
    assert(!ap_statue_world_art(190, 0x97, 11, &cfg));  /* Master/non-statue */
    assert(!ap_statue_world_art(190, 0x92, 29, &cfg));
    struct ApStatueTileUpload ring[64] = {0};
    ring[63] = (struct ApStatueTileUpload){AP_STATUE_NATIVE_TILES, 0x06014000u, 128u, 0u};
    assert(!ap_statue_replace_upload(ring, 63, 1, 0x06014000u, 11u, 0x0900ED10u));
    assert(!ap_statue_replace_upload(ring, 63, 0, 0x06014080u, 11u, 0x0900ED10u));
    assert(ap_statue_replace_upload(ring, 63, 0, 0x06014000u, 11u, 0x0900ED10u));
    assert(ring[63].source == 0x0900ED10u && ring[63].size == 128u);

    const uint32_t dest = 0x06014000u, art = 0x0900ED10u;
    const uint32_t expected[32] = { [31] = 0x44000000 };
    uint32_t resident[32] = {0};
    /* Failed signature must keep the native palette, even if the recycled
     * allocation still holds the previous room's custom tiles. */
    ring[0] = (struct ApStatueTileUpload){AP_STATUE_NATIVE_TILES, dest, 128u, 0u};
    ring[1] = (struct ApStatueTileUpload){0x08700000u, dest + 64u, 64u, 0u};
    assert(!ap_statue_replace_upload(ring, 0, 2, dest, 11u, art));
    resident[31] = expected[31];
    assert(!ap_statue_tiles_confirmed(ring, 2, 0, dest, art, resident, expected));
    /* Ring wrap and correct independent allocations on the same frame. */
    ring[0].destination = dest + 128u;
    resident[31] = 0;
    assert(ap_statue_tiles_confirmed(ring, 1, 63, dest, art, resident, expected));
    assert(!ap_statue_tiles_confirmed(ring, 1, 63, dest + 128u, art, resident, expected));
    /* After the DMA drains, use the actual allocation contents; after an
     * overwrite or newly allocated native statue, restore native palette. */
    resident[31] = expected[31];
    assert(ap_statue_tiles_confirmed(ring, 1, 1, dest, art, resident, expected));
    resident[31] = 0;
    assert(!ap_statue_tiles_confirmed(ring, 1, 1, dest, art, resident, expected));
    assert(!ap_statue_tiles_confirmed(ring, 64, 1, dest, art, resident, expected));
}
''')
    exe = tmp_path / "statue.exe"
    subprocess.run([cc, "-std=c99", "-Wall", "-Wextra", "-Werror", "-I",
                    str(WORLD / "kirby_ap_payload"), str(c), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)


def test_native_statue_frames_share_collectible_bank_without_overwriting_skin_or_markers():
    dummy = runpy.run_path(str(WORLD / "tools" / "create_dummy_rom.py"))["build_dummy_rom"]()
    assets = WORLD / "kirby_ap_payload"
    collectible = runpy.run_path(str(assets / "collectible_art.py"))
    statue = runpy.run_path(str(assets / "world_statue_assets.py"))
    region = bytes(0x10000)
    shared = collectible["build_collectible_art_table"](dummy, region)
    offset, frames = next(iter(statue["build_statue_art_table"](dummy, region).items()))
    start = offset - collectible["OFFSET"]
    assert start >= len(collectible["MARKER"])
    assert shared[start:] == frames
    assert offset + len(frames) == 0x100ED08
    assert offset + len(frames) <= 0x100ED10 < STATUE_CONFIG_ROM_OFFSET


def test_boss_shard_and_world_statue_hooks_share_one_native_render_dispatch():
    dummy = runpy.run_path(str(WORLD / "tools" / "create_dummy_rom.py"))["build_dummy_rom"]()
    names = {name for group in (patch_rom.WORLD_STATUE_HOOK_GROUPS, patch_rom.BOSS_SHARD_ART_HOOK_GROUPS)
             for name, _, _ in group}
    targets = {name: 0x0815E800 + i * 8 for i, name in enumerate(sorted(names))}
    statues = patch_rom.build_world_statue_hooks(dummy, targets)
    bosses = patch_rom.build_boss_shard_art_hooks(dummy, targets)
    shared = statues.keys() & bosses.keys()
    assert shared == {0x09A884, 0x09A8B0, 0x09D868, 0x09A97E, 0x09D8B8}
    assert all(statues[site] == bosses[site] for site in shared)
    assert len(statues.keys() - bosses.keys()) == 3
    assert len(bosses.keys() - statues.keys()) == 1
