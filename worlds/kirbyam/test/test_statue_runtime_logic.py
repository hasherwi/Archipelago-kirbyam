"""Executable contract tests for the payload's ability-statue policy helpers."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import pytest


_WORLD_DIR = Path(__file__).resolve().parents[1]
_PAYLOAD_DIR = _WORLD_DIR / "kirby_ap_payload"


def _native_c_compiler() -> str | None:
    if os.name == "nt":
        # The GitHub Windows Python matrix does not establish an MSVC developer
        # shell.  Linux/macOS still execute the compiled behavioral contract.
        return None
    return shutil.which("cc") or shutil.which("clang") or shutil.which("gcc")


def test_statue_runtime_logic_header_contract_executes() -> None:
    """Compile and execute the real C helpers used by the ARM payload."""
    compiler = _native_c_compiler()
    if compiler is None:
        pytest.skip("no native C compiler available for payload helper contract")

    harness = r'''
#include <stdint.h>
#include "statue_runtime_logic.h"

#define CHECK(condition, code) do { if (!(condition)) return (code); } while (0)

int main(void) {
    uint32_t pool = (1u << 2) | (1u << 5) | (1u << 9);
    uint32_t gate_mask = (1u << 5) | (1u << 9);
    uint32_t unlock_mask = (1u << 9);
    uint8_t flags = 0xA0u | 5u;

    /* The regular-statue function range is exact and excludes Master Sword. */
    CHECK(ap_statue_is_direct_touch_callsite(AP_STATUE_TOUCH_CALLSITE_START), 1);
    CHECK(ap_statue_is_direct_touch_callsite(AP_STATUE_TOUCH_CALLSITE_END - 2u), 2);
    CHECK(!ap_statue_is_direct_touch_callsite(AP_STATUE_TOUCH_CALLSITE_START - 2u), 3);
    CHECK(!ap_statue_is_direct_touch_callsite(AP_STATUE_TOUCH_CALLSITE_END), 4);

    /* Only enabled completely-random regular statues reroll per touch. */
    CHECK(ap_statue_should_reroll(AP_STATUE_TOUCH_CALLSITE_START, 2u, pool), 5);
    CHECK(!ap_statue_should_reroll(AP_STATUE_TOUCH_CALLSITE_START, 0u, pool), 6);
    CHECK(!ap_statue_should_reroll(AP_STATUE_TOUCH_CALLSITE_START, 1u, pool), 7);
    CHECK(!ap_statue_should_reroll(AP_STATUE_TOUCH_CALLSITE_START, 2u, 0u), 8);
    CHECK(!ap_statue_should_reroll(AP_STATUE_TOUCH_CALLSITE_END, 2u, pool), 9);

    /* Gating off leaves the per-seed statue pool unchanged. */
    CHECK(ap_statue_unlocked_candidate_mask(pool, 0u, 0u) == pool, 10);
    /* Gating removes only gateable abilities that have not been unlocked. */
    CHECK(
        ap_statue_unlocked_candidate_mask(pool, gate_mask, unlock_mask)
            == ((1u << 2) | (1u << 9)),
        11
    );
    CHECK(ap_statue_unlocked_candidate_mask(pool, pool, 0u) == 0u, 12);
    CHECK(ap_statue_unlocked_candidate_mask(pool, pool, pool) == pool, 21);

    /* Final gating applies in every mode/path, including Master Sword paths. */
    CHECK(ap_statue_apply_final_gate(flags, 0u, 0u) == flags, 22);
    CHECK(
        ap_statue_apply_final_gate(flags, (1u << 5), 0u) == 0xA0u,
        23
    );
    CHECK(
        ap_statue_apply_final_gate(flags, (1u << 5), (1u << 5)) == flags,
        24
    );

    /* Selection is uniform over set bits and never treats bit 0 as an ability. */
    CHECK(ap_statue_select_ability(pool, 0u) == 2u, 13);
    CHECK(ap_statue_select_ability(pool, 1u) == 5u, 14);
    CHECK(ap_statue_select_ability(pool, 2u) == 9u, 15);
    CHECK(ap_statue_select_ability(pool, 3u) == 2u, 16);
    CHECK(ap_statue_select_ability(0u, 123u) == 0u, 17);
    CHECK(ap_statue_select_ability(1u, 123u) == 0u, 18);

    /* Rewriting the ability ID preserves every upper transition flag. */
    CHECK(ap_statue_replace_ability_bits(flags, 9u) == (uint8_t)(0xA0u | 9u), 19);
    CHECK(ap_statue_replace_ability_bits(flags, 0u) == 0xA0u, 20);

    return 0;
}
'''

    with tempfile.TemporaryDirectory(prefix="kirbyam-statue-contract-") as tmpdir:
        tmp = Path(tmpdir)
        source = tmp / "statue_contract.c"
        executable = tmp / "statue_contract"
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
            f"statue runtime C contract failed at check {run_result.returncode}\n"
            f"stdout:\n{run_result.stdout}\nstderr:\n{run_result.stderr}"
        )
