"""Executable C behavior tests for transition-attempt classification helpers."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import pytest


_PAYLOAD_DIR = Path(__file__).resolve().parents[1] / "kirby_ap_payload"


def _native_c_compiler() -> str | None:
    return shutil.which("cc") or shutil.which("clang") or shutil.which("gcc")


def test_transition_attempt_policy_executes_from_payload_header() -> None:
    compiler = _native_c_compiler()
    if compiler is None:
        pytest.skip("no native C compiler available for payload transition policy contract")

    harness = r'''
#include <stdint.h>
#include "transition_runtime_logic.h"

#define CHECK(condition, code) do { if (!(condition)) return (code); } while (0)

int main(void) {
    /* Idle door contact and non-human helper calls are not player attempts. */
    CHECK(!ap_transition_is_human_up_attempt(0u, 1u, 0u), 1);
    CHECK(!ap_transition_is_human_up_attempt(1u, 1u, 0x40u), 2);
    CHECK(!ap_transition_is_human_up_attempt(0u, 0u, 0x40u), 3);
    CHECK(ap_transition_is_human_up_attempt(0u, 1u, 0x40u), 4);
    CHECK(ap_transition_is_human_up_attempt(1u, 2u, 0xC0u), 5);

    /* Explicit helper telemetry also requires an exact destination and spawn. */
    CHECK(!ap_transition_matches_special_tile(0x0200u, 3u, 4u, 0x0201u, 3u, 4u), 6);
    CHECK(!ap_transition_matches_special_tile(0x0200u, 3u, 4u, 0x0200u, 3u, 5u), 7);
    CHECK(ap_transition_matches_special_tile(0x0200u, 3u, 4u, 0x0200u, 3u, 4u), 8);

    CHECK(!(
        ap_transition_is_human_up_attempt(1u, 1u, 0x40u)
        && ap_transition_matches_special_tile(0x0200u, 3u, 4u, 0x0200u, 3u, 4u)
    ), 9);
    CHECK(!(
        ap_transition_is_human_up_attempt(0u, 1u, 0u)
        && ap_transition_matches_special_tile(0x0200u, 3u, 4u, 0x0200u, 3u, 4u)
    ), 10);
    CHECK(!(
        ap_transition_is_human_up_attempt(0u, 1u, 0x40u)
        && ap_transition_matches_special_tile(0x0200u, 3u, 4u, 0x0200u, 3u, 5u)
    ), 11);
    CHECK(
        ap_transition_is_human_up_attempt(0u, 1u, 0x40u)
        && ap_transition_matches_special_tile(0x0200u, 3u, 4u, 0x0200u, 3u, 4u),
        12
    );
    return 0;
}
'''

    with tempfile.TemporaryDirectory(prefix="kirbyam-transition-contract-") as tmpdir:
        tmp = Path(tmpdir)
        source = tmp / "transition_contract.c"
        executable = tmp / ("transition_contract.exe" if os.name == "nt" else "transition_contract")
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

        run_result = subprocess.run([str(executable)], check=False, capture_output=True, text=True)
        assert run_result.returncode == 0, run_result.stdout + run_result.stderr
