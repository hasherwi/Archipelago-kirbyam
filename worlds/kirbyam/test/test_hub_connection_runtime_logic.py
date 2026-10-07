"""Executable contract tests for hub-connection native runtime behavior."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import tempfile

import pytest


_WORLD_DIR = Path(__file__).resolve().parents[1]
_PAYLOAD_DIR = _WORLD_DIR / "kirby_ap_payload"
_CONTRACT_PATH = _WORLD_DIR / "data" / "hub_switch_contract.json"


def _native_c_compiler() -> str | None:
    return shutil.which("cc") or shutil.which("clang") or shutil.which("gcc")


def test_hub_connection_runtime_logic_executes_against_all_contract_doors() -> None:
    compiler = _native_c_compiler()
    if compiler is None:
        pytest.skip("no native C compiler available for payload helper contract")

    contract = json.loads(_CONTRACT_PATH.read_text(encoding="utf-8"))
    entries = contract["entries"]
    assert len(entries) == 15
    assert len({entry["world_props_unlock_index"] for entry in entries}) == 15

    by_door = sorted(entries, key=lambda entry: entry["native_world_map_door_index"])
    world_props = ", ".join(
        ["0u"] + [f"{entry['world_props_unlock_index']}u" for entry in by_door]
    )
    switch_bits = ", ".join(
        ["0u"] + [f"{entry['ap_bit_index']}u" for entry in by_door]
    )

    harness = f'''
#include <stdint.h>
#include "hub_connection_runtime_logic.h"

#define CHECK(condition, code) do {{ if (!(condition)) return (code); }} while (0)

static const uint8_t world_props_by_door[16] = {{{world_props}}};
static const uint8_t switch_bits_by_door[16] = {{{switch_bits}}};
static const uint8_t incomplete_world_props_by_door[16] = {{0u, 1u, 2u, 3u, 4u, 5u, 6u, 7u, 8u, 9u, 10u, 11u, 12u, 13u, 14u, 0xFFu}};
static uint32_t unlock_calls;
static uint32_t finish_calls;
static uint32_t record_calls;
static uint32_t recorded_switch_bit;

static void native_unlock(void) {{ unlock_calls++; }}
static void transition_complete(void) {{ finish_calls++; }}
static void record_switch(uint32_t bit) {{ record_calls++; recorded_switch_bit = bit; }}
static uint8_t sub_0802AD00_door_initializer(uint32_t world_props_state) {{
    /* special_doors.c opens the door only when this native state is nonzero. */
    return (world_props_state != 0u);
}}
static uint8_t sub_0811938C_big_switch_initializer(uint32_t world_props_state) {{
    /* big_small_switch.s hides a collected switch (state != 0). */
    return (world_props_state == 0u);
}}

int main(void) {{
    uint32_t door;
    for (door = 1u; door <= 15u; door++) {{
        uint32_t item_mask = 1u << door;
        uint32_t switch_bit = switch_bits_by_door[door];
        uint32_t native_door_state = 1u; /* AP item delivery persists the real door unlock. */
        uint32_t switch_init_state;
        uint8_t door_to_hub_visible = sub_0802AD00_door_initializer(native_door_state);
        uint8_t switch_visible;
        uint8_t mask_switch_state = ap_should_mask_item_owned_hub_unlock(
            2u, 2u, world_props_by_door[door], item_mask, 0u,
            world_props_by_door, switch_bits_by_door);

        /* sub_0802AD00 reads the native world-props state without masking it,
           so the item-owned physical route remains visible. */
        CHECK(door_to_hub_visible, 11);
        switch_init_state = mask_switch_state ? 0u : native_door_state;
        switch_visible = sub_0811938C_big_switch_initializer(switch_init_state);
        CHECK(switch_visible, 12);
        CHECK(ap_should_mask_item_owned_hub_unlock(
            2u, 2u, world_props_by_door[door], item_mask, 0u,
            world_props_by_door, switch_bits_by_door), 1);
        CHECK(!ap_should_mask_item_owned_hub_unlock(
            2u, 2u, world_props_by_door[door], item_mask, 1u << switch_bit,
            world_props_by_door, switch_bits_by_door), 2);
        switch_init_state = ap_should_mask_item_owned_hub_unlock(
            2u, 2u, world_props_by_door[door], item_mask, 1u << switch_bit,
            world_props_by_door, switch_bits_by_door) ? 0u : native_door_state;
        switch_visible = sub_0811938C_big_switch_initializer(switch_init_state);
        CHECK(!switch_visible, 13);
        CHECK(!ap_should_mask_item_owned_hub_unlock(
            2u, 2u, world_props_by_door[door], 0u, 0u,
            world_props_by_door, switch_bits_by_door), 3);
    }}

    CHECK(!ap_should_mask_item_owned_hub_unlock(
        1u, 2u, world_props_by_door[1], 1u << 1, 0u,
        world_props_by_door, switch_bits_by_door), 4);
    CHECK(!ap_should_mask_item_owned_hub_unlock(
        2u, 2u, world_props_by_door[1], 0xFFFFFFFFu, 0u,
        world_props_by_door, switch_bits_by_door), 5);
    CHECK(!ap_should_mask_item_owned_hub_unlock(
        2u, 2u, 0xFFu, 1u << 15, 0u,
        incomplete_world_props_by_door, switch_bits_by_door), 10);

    /* A mapped switch reports its AP check and finishes the transition without
       calling the callback that would grant its native hub connection. */
    ap_dispatch_world_map_unlock(1u, 11u, native_unlock, transition_complete, record_switch);
    CHECK(unlock_calls == 0u && finish_calls == 1u && record_calls == 1u, 6);
    CHECK(recorded_switch_bit == 11u, 7);

    /* NO_UNLOCK and unknown indices retain their selected native callback. */
    ap_dispatch_world_map_unlock(0u, 0u, native_unlock, transition_complete, record_switch);
    CHECK(unlock_calls == 1u && finish_calls == 1u && record_calls == 1u, 8);
    ap_dispatch_world_map_unlock(0u, 0u, 0, transition_complete, record_switch);
    CHECK(unlock_calls == 1u && finish_calls == 1u && record_calls == 1u, 9);
    return 0;
}}
'''

    with tempfile.TemporaryDirectory(prefix="kirbyam-hub-connection-contract-") as tmpdir:
        tmp = Path(tmpdir)
        source = tmp / "hub_connection_contract.c"
        executable = tmp / "hub_connection_contract.exe"
        source.write_text(harness, encoding="utf-8")

        compile_result = subprocess.run(
            [
                compiler,
                "-std=c99",
                "-Wall",
                "-Wextra",
                "-Werror",
                "-I",
                str(_PAYLOAD_DIR),
                str(source),
                "-o",
                str(executable),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        assert compile_result.returncode == 0, compile_result.stdout + compile_result.stderr

        run_result = subprocess.run(
            [str(executable)],
            check=False,
            capture_output=True,
            text=True,
        )
        assert run_result.returncode == 0, (
            f"hub connection runtime C contract failed at check {run_result.returncode}\n"
            f"stdout:\n{run_result.stdout}\nstderr:\n{run_result.stderr}"
        )
