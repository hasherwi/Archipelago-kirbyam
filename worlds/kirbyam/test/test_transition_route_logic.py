"""Execute the native chute admission policy, including exact-tuple boundaries."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


def test_wind_chute_admission_targets(tmp_path: Path) -> None:
    compiler = shutil.which("cc") or shutil.which("clang") or shutil.which("gcc")
    if compiler is None:
        pytest.skip("no host C compiler available")
    assert compiler is not None
    source = tmp_path / "chute_policy.c"
    executable = tmp_path / ("chute_policy.exe" if os.name == "nt" else "chute_policy")
    source.write_text(r'''
#include "transition_route_logic.h"
#define CHECK(c) do { if (!(c)) return __LINE__; } while (0)
int main(void) {
    CHECK(AP_TRANSITION_METHOD_WIND_CHUTE == 3u);
    /* The two forward routes require the eventual destination's key before
     * entering their same-area transport room. Reverse routes target the
     * opposite area; they do not require the departing area's key as well. */
    CHECK(ap_transition_route_destination(743, 180, 5, 3) == 824);
    CHECK(ap_transition_route_destination(170, 181, 5, 3) == 619);
    CHECK(ap_transition_route_destination(824, 180, 12, 49) == 743);
    CHECK(ap_transition_route_destination(619, 181, 12, 49) == 170);
    /* A source/room/spawn mismatch is not evidence of a forced lane. */
    CHECK(ap_transition_route_destination(742, 180, 5, 3) == 180);
    CHECK(ap_transition_route_destination(743, 181, 5, 3) == 181);
    CHECK(ap_transition_route_destination(743, 180, 6, 3) == 180);
    CHECK(ap_transition_route_destination(743, 180, 5, 4) == 180);
    CHECK(ap_transition_route_destination(824, 180, 5, 3) == 180);
    CHECK(ap_transition_route_destination(619, 181, 12, 48) == 181);
    /* Chute exits, ordinary mirrors, same-area cannons, Warp Stars and free
     * Rainbow returns retain their actual destination. */
    CHECK(ap_transition_route_destination(180, 824, 12, 4) == 824);
    CHECK(ap_transition_route_destination(181, 170, 3, 9) == 170);
    CHECK(ap_transition_route_destination(101, 106, 3, 4) == 106);
    CHECK(ap_transition_route_destination(126, 570, 0, 0) == 570);
    CHECK(ap_transition_route_destination(323, 300, 0, 0) == 300);
    CHECK(ap_transition_route_destination(502, 525, 0, 0) == 525);
    CHECK(ap_transition_route_destination(827, 133, 0, 0) == 133);
    CHECK(ap_transition_route_destination(142, 195, 0, 0) == 195);
    CHECK(ap_transition_route_destination(195, 801, 0, 0) == 801);
    return 0;
}
''', encoding="utf-8")
    payload = Path(__file__).resolve().parents[1] / "kirby_ap_payload"
    result = subprocess.run(
        [compiler, "-std=c99", "-Wall", "-Wextra", "-Werror", "-I", str(payload),
         str(source), "-o", str(executable)], capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    result = subprocess.run([str(executable)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
