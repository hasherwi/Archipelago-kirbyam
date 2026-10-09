"""Executable lever lifecycle and fail-closed USA-ROM hook contracts."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
import shutil
import subprocess

import pytest

PAYLOAD_DIR = Path(__file__).resolve().parents[1] / "kirby_ap_payload"
SPEC = importlib.util.spec_from_file_location("runtime_regression_patch", PAYLOAD_DIR / "patch_rom.py")
assert SPEC and SPEC.loader
patch_rom = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(patch_rom)


def regression_fixture() -> tuple[bytearray, dict[str, int]]:
    rom = bytearray(0x400000)
    offset = patch_rom.BIG_CHEST_INITIALIZER_POINTER_OFFSET
    rom[offset:offset + 4] = (0x0800BD4D).to_bytes(4, "little")
    rom[0xB9B0:0xB9B4] = patch_rom.thumb_bl_bytes(0x0800B9B0, 0x080029F4)
    for offset in (0x5C200, 0x5C400):
        rom[offset:offset + 4] = (0x0805C619).to_bytes(4, "little")
    targets = {
        "chest_initializer_hook_target": 0x0815E100,
        "chest_popup_room_counter_hook_target": 0x0815E200,
        "ability_commit_hook_target": 0x0815E300,
    }
    return rom, targets


def test_regression_writes_target_only_verified_paths() -> None:
    rom, targets = regression_fixture()
    # Same symbols outside the scoped native functions must remain untouched.
    rom[0xA000:0xA004] = patch_rom.thumb_bl_bytes(0x0800A000, 0x080029F4)
    rom[0x5C700:0x5C704] = (0x0805C619).to_bytes(4, "little")
    before = bytes(rom)
    writes = patch_rom.build_runtime_regression_writes(rom, targets)
    assert bytes(rom) == before
    assert set(writes) == {0x352270, 0xB9B0, 0x5C200, 0x5C400}
    assert writes[0x352270] == (targets["chest_initializer_hook_target"] | 1).to_bytes(4, "little")
    assert (patch_rom.decode_thumb_bl_target(0x0800B9B0, writes[0xB9B0])
            == targets["chest_popup_room_counter_hook_target"])
    for offset in (0x5C200, 0x5C400):
        assert writes[offset] == (targets["ability_commit_hook_target"] | 1).to_bytes(4, "little")


@pytest.mark.parametrize("offset, message", [
    (0x352270, "verified USA-ROM bytes"),
    (0xB9B0, "room-counter calls"),
    (0x5C200, "two final ability-state"),
])
def test_unknown_regression_hook_input_fails_without_mutation(offset: int, message: str) -> None:
    rom, targets = regression_fixture()
    rom[offset:offset + 4] = bytes(4)
    before = bytes(rom)
    with pytest.raises(SystemExit, match=message):
        patch_rom.build_runtime_regression_writes(rom, targets)
    assert bytes(rom) == before


def _function(source: str, name: str) -> str:
    """Compile the actual payload function bodies, with only platform IO stubbed."""
    start = source.index(name + "(")
    start = source.rfind("\n", 0, start) + 1
    brace = source.index("{", start)
    depth = 1
    end = brace + 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[start:end]


def test_native_lever_lifecycle_and_final_ability_gate(tmp_path: Path) -> None:
    compiler = shutil.which("cc") or shutil.which("clang") or shutil.which("gcc")
    if not sys.platform.startswith("linux") or not compiler:
        pytest.skip("requires Linux low-address test memory and a native C compiler")
    source = (PAYLOAD_DIR / "ap_payload.c").read_text(encoding="utf-8")
    names = (
        "ap_lever_bit_for_obj", "ap_record_minor_chest_collection_from_obj_ptr",
        "ap_lever_wall_owned", "ap_update_lever_wall", "ap_on_initialize_chest",
        "ap_on_chest_popup_room_counter", "ap_on_commit_copy_ability_transition",
    )
    functions = "\n\n".join(_function(source, name) for name in names)
    functions = functions.replace('register uint32_t popup_obj_ptr asm("r8");',
                                  'uint32_t popup_obj_ptr = TEST_POPUP;')
    functions = functions.replace('((KirbyCommitAbilityFn)0x0805C619u)', 'commit_native')
    harness = r'''
#define _GNU_SOURCE
#include <stdint.h>
#include <sys/mman.h>
#include <string.h>
#include "lever_runtime_logic.h"
#include "statue_runtime_logic.h"
#define CHECK(c) do { if (!(c)) return __LINE__; } while (0)
#define TEST_CHEST 0x03000100u
#define TEST_POPUP 0x03000500u
#define KIRBY_SMALL_CHEST_FLAGS_ADDR 0x02038960u
#define KIRBY_LEVEL_INFO_BASE 0x02023530u
#define KIRBY_LEVEL_INFO_STRIDE 0x668u
#define KIRBY_LEVEL_INFO_ROOM_SLOT_OFFSET 0x65Eu
#define KIRBY_PLAYER_COUNT 4u
#define KIRBY_TRANSITIONING_ABILITY_OFFSET 0xDDu
#define AP_MINOR_CHEST_ITEM_SUPPRESSION_MARKER 0x12345678u
#define KIRBY_MINOR_CHEST_NO_NATIVE_ITEM 0x63u
static uint32_t AP_LEVER_ACTIVATION_FLAGS, AP_ABILITY_GATE_MASK, AP_ABILITY_UNLOCK_MASK;
static unsigned counter[4], ring_count, native_init_calls, commits;
static uint8_t last_pending;
typedef void (*KirbyChestFn)(void*);
static void room_counter(uint32_t slot, uint32_t amount) { counter[slot] += amount; }
static void chest_wait(void *chest) { (void)chest; }
static void chest_open(void *chest) { (void)chest; }
static uint8_t native_owned(uint8_t id) {
    return (*(uint8_t*)(KIRBY_SMALL_CHEST_FLAGS_ADDR + (id >> 3)) >> (id & 7)) & 1;
}
static void collect_native(uint32_t id) {
    *(uint8_t*)(KIRBY_SMALL_CHEST_FLAGS_ADDR + (id >> 3)) |= 1u << (id & 7);
}
static void chest_init(void *chest) {
    uint8_t *c = chest;
    native_init_calls++;
    *(KirbyChestFn*)(c + 0x78) = native_owned(c[0xE2]) ? chest_open : chest_wait;
    if (native_owned(c[0xE2])) counter[0]++;
}
static void commit_native(void *kirby) {
    uint8_t *k = kirby;
    last_pending = k[0xDD];
    k[0x103] = k[0xDD] & 31u;
    k[0xDD] = 0;
    commits++;
}
#define KIRBY_ROOM_COUNTER_FN room_counter
#define KIRBY_CHEST_INIT_FN chest_init
#define KIRBY_CHEST_WAIT_FN chest_wait
#define KIRBY_CHEST_OPEN_FN chest_open
#define ap_collect_small_chest_native collect_native
static uint8_t ap_is_ap_owned_minor_chest_source(uint32_t p) { (void)p; return 0; }
static void ap_record_minor_chest_source_ptr(uint32_t p) { (void)p; ring_count++; }
'''
    # Host function pointers are 8 bytes, while the real ARM struct stores 4.
    # Use separate variables for the two callback fields to keep the test layout honest.
    functions = functions.replace('*(KirbyChestFn volatile *)(chest_obj_ptr + 0x78u)', 'test_main_callback')
    functions = functions.replace('*(KirbyChestFn volatile *)(chest_obj_ptr + 0x7Cu)', 'test_aux_callback')
    harness += '\nstatic KirbyChestFn test_main_callback, test_aux_callback;\n' + functions
    harness += r'''
int main(void) {
    const uint32_t sources[] = {0x088BE07C, 0x088CD240, 0x088D2E68, 0x088D1454};
    const uint8_t ids[] = {18, 65, 77, 74};
    uint8_t *chest = (void*)TEST_CHEST;
    unsigned i, first, ability, upper;
    CHECK(mmap((void*)0x02000000, 0x40000, PROT_READ|PROT_WRITE,
        MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED, -1, 0) == (void*)0x02000000);
    CHECK(mmap((void*)0x03000000, 0x8000, PROT_READ|PROT_WRITE,
        MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED, -1, 0) == (void*)0x03000000);
    *(uint32_t*)(TEST_POPUP + 0x4C) = TEST_CHEST;
    for (i = 0; i < 4; i++) for (first = 0; first < 2; first++) {
        memset((void*)0x02000000, 0, 0x40000);
        memset(chest, 0, 0x100);
        AP_LEVER_ACTIVATION_FLAGS = counter[0] = ring_count = 0;
        *(uint32_t*)(chest+0xB0) = sources[i];
        *(uint16_t*)(chest+0xE0) = 0x63;
        chest[0xE2] = ids[i];
        if (first) collect_native(ids[i]);
        ap_on_initialize_chest(chest);
        CHECK(counter[0] == first);
        CHECK(test_main_callback == chest_wait && chest[0x83] == 2);
        CHECK(AP_LEVER_ACTIVATION_FLAGS == 0);
        ap_record_minor_chest_collection_from_obj_ptr(TEST_CHEST);
        CHECK(AP_LEVER_ACTIVATION_FLAGS == (1u << i));
        CHECK(native_owned(ids[i]) == first && ring_count == 0);
        ap_on_chest_popup_room_counter(0, 1);
        CHECK(counter[0] == first);
        collect_native(ids[i]);
        test_aux_callback(chest);
        test_aux_callback(chest);
        CHECK(counter[0] == 1);
        /* New room instance, fresh counter, same AP state: apply only once. */
        counter[0] = 0;
        *(uint32_t*)(chest+0xDC) = 0;
        ap_on_initialize_chest(chest);
        CHECK(test_main_callback == chest_open && chest[0x83] == 3);
        test_aux_callback(chest);
        CHECK(counter[0] == 1);
        /* All three identity fields are mandatory. */
        CHECK(!ap_lever_bit_for_chest(sources[i]+4, 0x63, ids[i]));
        CHECK(!ap_lever_bit_for_chest(sources[i], 0, ids[i]));
        CHECK(!ap_lever_bit_for_chest(sources[i], 0x63, ids[i]+1));
    }
    *(uint32_t*)(chest+0xB0) = 0x08800000;
    counter[0] = ring_count = 0;
    ap_record_minor_chest_collection_from_obj_ptr(TEST_CHEST);
    ap_on_chest_popup_room_counter(0, 1);
    CHECK(counter[0] == 1 && ring_count == 1);
    ap_on_initialize_chest(chest);
    CHECK(native_init_calls == 17);
    /* The final gate handles every ability and upper-flag combination, even
       when a native roulette rewrites pendingAbility after entry was gated. */
    for (ability = 1; ability < 32; ability++) for (upper = 0; upper < 256; upper += 32) {
        AP_ABILITY_GATE_MASK = 1u << ability;
        AP_ABILITY_UNLOCK_MASK = 0;
        chest[0xDD] = upper | ability;
        ap_on_commit_copy_ability_transition(chest);
        CHECK(chest[0x103] == 0 && last_pending == upper);
        AP_ABILITY_UNLOCK_MASK = 1u << ability;
        chest[0xDD] = upper | ability;
        ap_on_commit_copy_ability_transition(chest);
        CHECK(chest[0x103] == ability && last_pending == (upper | ability));
        AP_ABILITY_GATE_MASK = 0;
        AP_ABILITY_UNLOCK_MASK = 0;
        chest[0xDD] = upper | ability;
        ap_on_commit_copy_ability_transition(chest);
        CHECK(chest[0x103] == ability && last_pending == (upper | ability));
    }
    CHECK(commits == 31*8*3);
    ap_on_commit_copy_ability_transition(0);
    CHECK(commits == 31*8*3);
    return 0;
}
'''
    src = tmp_path / "runtime_contract.c"
    exe = tmp_path / "runtime_contract"
    src.write_text(harness, encoding="utf-8")
    compiled = subprocess.run([
        compiler, "-std=c99", "-Wall", "-Wextra", "-Werror",
        "-Wno-int-to-pointer-cast", "-Wno-pointer-to-int-cast", "-Wno-unused-local-typedefs",
        "-I", str(PAYLOAD_DIR), str(src), "-o", str(exe),
    ], capture_output=True, text=True, check=False)
    assert compiled.returncode == 0, compiled.stdout + compiled.stderr
    result = subprocess.run([str(exe)], capture_output=True, text=True, check=False)
    assert result.returncode == 0, f"runtime C contract failed at line modulo 256: {result.returncode}"
