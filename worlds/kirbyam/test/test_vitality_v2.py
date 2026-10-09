"""Executable format-2 policy; not a claim that shipping ROM hooks are enabled."""

import ctypes
import json
import os
from pathlib import Path
import shutil
import subprocess
from collections import Counter
from itertools import product
from types import SimpleNamespace

import pytest

from ..health import resolve_health_range
from ..vitality import (
    HEALTH_ROM_TITLE, LEGACY_ROM_TITLE, VITALITY_ITEM_IDS, VitalityPlan,
    authoritative_health, decode_health_config, history_mask, partial_receipt,
    remaining_pool, replace_owned_bits, resolve_vitality_plan, validate_health_protocol,
)

RANGES = [(a, b) for a in range(1, 11) for b in range(a, 11)]
WORLD = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("minimum,maximum", RANGES)
def test_all_ranges_pool_and_history(minimum, maximum):
    plan = resolve_vitality_plan(minimum, maximum)
    assert decode_health_config(plan.config_word) == plan
    assert len(plan.item_ids) == maximum - minimum
    assert len(set(plan.item_ids)) == plan.count
    for percentage in (0, 1, 25, 50, 99, 100):
        filler, traps = remaining_pool(plan, 100, 25, percentage)
        assert filler + traps + 25 + plan.count == 100
        assert traps == (75 - plan.count) * percentage // 100
    # Exhaustive ownership, including inactive/precollected IDs and duplicate packets.
    for bits in range(512):
        ids = [item for index, item in enumerate(VITALITY_ITEM_IDS) if bits & (1 << index)]
        assert history_mask(ids + ids + [3860026]) == bits
        earned = min(len(ids), maximum - minimum)
        assert plan.earned(bits | 0xFFFFFE00) == earned
        assert replace_owned_bits(0x80000200, bits) == 0x80000200 | bits
        for hp in (0, -1, -128):
            assert authoritative_health(plan, bits, hp, 6, 0) == (earned, hp, minimum + earned)
        count, hp, capacity = authoritative_health(plan, bits, 1, minimum + earned, earned)
        assert (count, hp, capacity) == (earned, 1, minimum + earned)
        assert authoritative_health(plan, bits, hp, capacity, count) == (count, hp, capacity)


@pytest.mark.parametrize("minimum,maximum", RANGES)
def test_partial_replay_loaded_save_then_fresh_items(minimum, maximum):
    plan = VitalityPlan(minimum, maximum)
    for saved in range(plan.count + 1):
        count, mask = saved, 0x80000000
        increases = 0
        for item in reversed(plan.item_ids):
            mask, count, increased = partial_receipt(plan, mask, count, item)
            increases += increased
            assert mask & 0x80000000
            assert count >= saved
            # Idle polls and retries do not purchase a second effect.
            assert partial_receipt(plan, mask, count, item) == (mask, count, False)
        assert count == plan.count
        assert increases == plan.count - saved


def test_defaults_one_hit_ids_and_legacy_gate():
    assert resolve_vitality_plan().item_ids == (3860018, 3860019, 3860020, 3860021)
    assert resolve_vitality_plan(1, 10).item_ids[-5:] == tuple(range(3860224, 3860229))
    assert resolve_vitality_plan(10, 1, 1) == VitalityPlan(1, 1)
    assert resolve_vitality_plan(10, 1, 2) == VitalityPlan(1, 5)
    assert remaining_pool(VitalityPlan(6, 6), 100, 20)[0] == remaining_pool(VitalityPlan(6, 10), 100, 20)[0] + 4
    # Still blocked in shipping generation until #931 and native hooks integrate.
    with pytest.raises(ValueError, match="at most 4"):
        resolve_health_range(1, 10)
    catalog = json.loads((WORLD / "data/items.json").read_text())
    assigned = {entry["item_id"] for entry in catalog.values() if "item_id" in entry}
    assert not assigned.intersection(VITALITY_ITEM_IDS[4:])
    for index, item_id in enumerate(VITALITY_ITEM_IDS[:4], 1):
        assert catalog[f"VITALITY_COUNTER_{index}"]["item_id"] == item_id


@pytest.mark.parametrize("minimum,maximum", [(0, 1), (1, 11), (9, 8), (True, 5), (1, "9")])
def test_invalid_bounds(minimum, maximum):
    with pytest.raises(ValueError):
        VitalityPlan(minimum, maximum)


def test_protocol_fail_closed():
    assert len(HEALTH_ROM_TITLE) == len(LEGACY_ROM_TITLE) == 12
    plan = VitalityPlan(1, 10)
    validate_health_protocol(HEALTH_ROM_TITLE, plan.config_word, 2, plan)
    for title, config, version in (
        (LEGACY_ROM_TITLE, plan.config_word, 2),
        (HEALTH_ROM_TITLE, plan.config_word, 1),
        (HEALTH_ROM_TITLE, 0xA9020000, 2),
        (HEALTH_ROM_TITLE, VitalityPlan(6, 10).config_word, 2),
        (HEALTH_ROM_TITLE, plan.config_word, True),
        (HEALTH_ROM_TITLE, plan.config_word | (1 << 32), 2),
    ):
        with pytest.raises(ValueError):
            validate_health_protocol(title, config, version, plan)
    with pytest.raises(ValueError, match="exceed"):
        remaining_pool(plan, 8, 0)


@pytest.fixture(scope="module")
def native_policy(tmp_path_factory):
    compiler = shutil.which("cc")
    if compiler is None or os.name == "nt":
        pytest.skip("native C shared-library compiler unavailable")
    root = tmp_path_factory.mktemp("vitality-native")
    source = root / "policy.c"
    source.write_text('''
#include "vitality_runtime_logic.h"
uint32_t bit(uint32_t id) { return ap_vitality_item_bit(id); }
uint32_t valid(uint32_t c) { return ap_health_config_valid(c); }
uint32_t earned(uint32_t c, uint32_t m) { return ap_vitality_earned(c,m); }
uint32_t capacity(uint32_t c, uint32_t n) { return ap_vitality_capacity(c,n); }
uint32_t partial(uint32_t c, uint32_t m, uint32_t n) { return ap_vitality_partial_count(c,m,n); }
int32_t hp(int32_t h, uint32_t c, uint32_t fresh) { return ap_vitality_grant_hp(h,c,fresh); }
uint32_t menu(uint32_t n) {
    /* Model the verified native table search with adjacent sentinel storage. */
    uint32_t arr[6] = {0xAA,0,0,0,0,0xBB};
    uint32_t table[4] = {0x800,0x801,0x802,0x803};
    for (uint32_t j=0;j<ap_vitality_menu_count(n);j++) {
        uint32_t i;
        for (i=0;i<4;i++) if (table[i]==j+0x800) break;
        arr[i+1]=1;
    }
    if(arr[0]!=0xAA || arr[5]!=0xBB) return 999;
    return arr[1]+arr[2]+arr[3]+arr[4];
}
''')
    binary = root / "policy.so"
    subprocess.run([compiler, "-shared", "-fPIC", "-O2", "-Wall", "-Wextra", "-Werror",
                    "-I", str(WORLD / "kirby_ap_payload"), str(source), "-o", str(binary)], check=True)
    library = ctypes.CDLL(str(binary))
    for name, count in (("bit", 1), ("valid", 1), ("earned", 2), ("capacity", 2),
                        ("partial", 3), ("menu", 1)):
        fn = getattr(library, name)
        fn.argtypes = [ctypes.c_uint32] * count
        fn.restype = ctypes.c_uint32
    library.hp.argtypes = [ctypes.c_int32, ctypes.c_uint32, ctypes.c_uint32]
    library.hp.restype = ctypes.c_int32
    return library


@pytest.mark.parametrize("minimum,maximum", RANGES)
def test_native_policy_matches_full_ownership_domain(native_policy, minimum, maximum):
    native = native_policy
    plan = VitalityPlan(minimum, maximum)
    config = plan.config_word
    assert native.valid(config)
    for bits in range(512):
        assert native.earned(config, bits | 0xFFFFFE00) == plan.earned(bits)
        for saved in (0, plan.count, 9, 65535):
            assert native.capacity(config, saved) == plan.capacity(saved)
            assert native.partial(config, bits, saved) == max(min(saved, plan.count), plan.earned(bits))
    for hp in (0, -1, -128):
        assert native.hp(hp, maximum, 1) == hp
    assert native.hp(1, maximum, 0) == 1
    assert native.hp(1, maximum, 1) == maximum


def test_native_mapping_and_menu_bounds(native_policy):
    for index, item in enumerate(VITALITY_ITEM_IDS):
        assert native_policy.bit(item) == 1 << index
    for item in (0, 3860017, 3860022, 3860031, 3860223, 3860229):
        assert native_policy.bit(item) == 0
    for saved in (*range(10), 255, 65535):
        assert native_policy.menu(saved) == min(saved, 4)
    for invalid in (0, 0xFFFFFFFF, 0xA9020000, 0xA9020B01, 0xA9020102):
        assert not native_policy.valid(invalid)
        assert native_policy.capacity(invalid, 65535) == 10


@pytest.mark.parametrize("minimum,maximum", RANGES)
def test_authority_and_mailbox_arrival_order(native_policy, minimum, maximum):
    plan = VitalityPlan(minimum, maximum)
    for saved in range(plan.count):
        mask = (1 << (saved + 1)) - 1
        capacity = minimum + saved + 1
        for hp in (1, 0, -1, -128):
            expected_hp = capacity if hp > 0 else hp
            authority = authoritative_health(plan, mask, hp, minimum + saved, saved)
            assert authority == (saved + 1, expected_hp, capacity)
            native_hp = native_policy.hp(hp, capacity, 1)
            assert native_hp == expected_hp
            assert authoritative_health(plan, mask, native_hp, capacity, saved + 1) == authority
            # Authority first, then mailbox replay, also preserves damage after receipt.
            assert native_policy.hp(1 if hp > 0 else hp, capacity, 0) == (1 if hp > 0 else hp)


def test_native_patch_plan_rejects_unknown_code_and_targets():
    from ..kirby_ap_payload.vitality_patch import (
        build_vitality_hook_writes, INITIAL_CAPACITY_CALL, INITIAL_CAPACITY_ADD,
        COLLECTION_MENU_CALL, NATIVE_VITALITY_GETTER,
    )
    from ..kirby_ap_payload.thumb_branch import thumb_bl_bytes
    rom = bytearray(COLLECTION_MENU_CALL + 4)
    for offset in (INITIAL_CAPACITY_CALL, COLLECTION_MENU_CALL):
        rom[offset:offset + 4] = thumb_bl_bytes(0x08000000 + offset, NATIVE_VITALITY_GETTER)
    rom[INITIAL_CAPACITY_ADD:INITIAL_CAPACITY_ADD + 2] = b"\x06\x30"
    original = bytes(rom)
    writes = build_vitality_hook_writes(rom, capacity_target=0x0815E100, menu_target=0x0815E200)
    assert bytes(rom) == original
    assert [offset for offset, _ in writes] == [INITIAL_CAPACITY_CALL, INITIAL_CAPACITY_ADD, COLLECTION_MENU_CALL]
    for offset in (INITIAL_CAPACITY_CALL, INITIAL_CAPACITY_ADD, COLLECTION_MENU_CALL):
        bad = bytearray(original)
        bad[offset] ^= 1
        with pytest.raises(ValueError):
            build_vitality_hook_writes(bad, capacity_target=0x0815E100, menu_target=0x0815E200)
    for target in (0x0815DFFE, 0x0815F690, 0x0815E101, 0x0815E200):
        with pytest.raises(ValueError):
            build_vitality_hook_writes(rom, capacity_target=target, menu_target=0x0815E200)


@pytest.mark.parametrize("minimum,maximum", RANGES)
@pytest.mark.parametrize("shards", [0, 2])
def test_real_pool_builder_with_isolated_format2_catalog(monkeypatch, minimum, maximum, shards):
    """Exercise actual pool code without enabling unsafe shipping ROM generation.

    Only the proposed catalog additions and validated range are injected. All
    selection, filler/trap exclusions, rounding, and item creation use real code.
    This is not full generation/precollect or emulator acceptance.
    """
    from BaseClasses import ItemClassification
    from .. import KirbyAmWorld
    from ..data import data, ItemData
    from ..health import HealthRange
    from .test_item_pool import _build_world_for_create_items

    for index, code in enumerate(VITALITY_ITEM_IDS[4:], 5):
        label = f"Vitality Counter #{index}"
        monkeypatch.setitem(data.items, code, ItemData(label, code, ItemClassification.useful,
                                                     frozenset(("Vitality", "Useful", "Unique"))))
        monkeypatch.setitem(KirbyAmWorld.item_name_to_id, label, code)
        monkeypatch.setitem(KirbyAmWorld.item_id_to_name, code, label)
    for one_hit, maps, no_lives, gating in product(range(3), range(2), range(2), range(2)):
        plan = resolve_vitality_plan(minimum, maximum, one_hit)
        world, locations = _build_world_for_create_items(shards, one_hit_mode=one_hit,
                                                        start_with_all_maps=maps, enable_traps=1,
                                                        trap_fill_percentage=25)
        world.options.no_extra_lives = SimpleNamespace(value=no_lives)
        world.options.ability_gating = SimpleNamespace(value=gating)
        world._health_range = lambda: HealthRange(plan.minimum, plan.maximum)
        world.create_items()
        pool = world.multiworld.itempool
        assert len(pool) == sum(location.item is None for location in locations)
        assert Counter(item.code for item in pool if item.code in VITALITY_ITEM_IDS) == Counter(plan.item_ids)
        disposable = [item for item in pool if item.classification in
                      (ItemClassification.filler, ItemClassification.trap)]
        assert sum(item.classification == ItemClassification.trap for item in disposable) == len(disposable) * 25 // 100
        if maps:
            assert all("Maps" not in item.tags for item in pool)
        if not gating:
            assert all("Abilities" not in item.tags for item in pool)
        if no_lives:
            assert not {3860001, 3860033, 3860036}.intersection(item.code for item in pool)
