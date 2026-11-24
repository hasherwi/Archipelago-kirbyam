"""Native receipt visual mailbox is fail-closed and independent of item delivery."""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from ..receipt_visuals import VISUAL_MAILBOX, VISUAL_ROM_MARKER, VISUAL_ROM_OFFSET

WORLD = Path(__file__).resolve().parents[1]
PAYLOAD = WORLD / "kirby_ap_payload"


def test_native_receipt_visual_abi() -> None:
    header = (PAYLOAD / "receipt_visual_runtime.h").read_text()
    linker = (PAYLOAD / "linker.ld").read_text()
    code = (PAYLOAD / "ap_payload.c").read_text()
    assert f"#define AP_VISUAL_MAILBOX_ADDRESS 0x{VISUAL_MAILBOX:08X}u" in header
    assert f"gApReceiptVisualInfo == 0x{0x08000000 + VISUAL_ROM_OFFSET:08X}" in linker
    assert f'gApReceiptVisualInfo[8] = "{VISUAL_ROM_MARKER[:-1].decode()}"' in code


def test_actual_native_visual_poll_accepts_only_one_fresh_ready_command(tmp_path: Path) -> None:
    cc = shutil.which("cc")
    if not cc:
        pytest.skip("requires a native C compiler")
    code = (PAYLOAD / "ap_payload.c").read_text()
    start = code.index("void ap_receipt_visual_poll(")
    stop = code.index("\n}", start) + 2
    source = tmp_path / "visual.c"
    source.write_text(r'''
#include <assert.h>
#include "receipt_visual_runtime.h"
#include "shard_award_runtime.h"
#include "reward_art_config.h"

static struct ApReceiptVisualMailbox fixture;
#define AP_VISUAL_MAILBOX (&fixture)
static uint32_t AP_FRAME_COUNTER, epoch = 1u, last_token;
static unsigned draws;
static uint8_t gameplay = 1u, palette = 1u, create = 1u, last_art;
static uint8_t ap_receipt_cue_gameplay_ready(void) { return gameplay; }
static uint32_t ap_copy_room_epoch(void) { return epoch; }
static uint8_t ap_visit_palette_ready(void) { return palette; }
static uint8_t ap_show_incoming_reward(uint8_t art, uint32_t token) {
    last_art = art;
    last_token = token;
    draws += create;
    return create;
}
''' + code[start:stop] + r'''
static void rejected(uint32_t request) {
    unsigned before = draws;
    fixture.request = request;
    ap_receipt_visual_poll();
    assert(!fixture.request && fixture.result == (request | AP_VISUAL_REJECTED) && draws == before);
}
int main(void) {
    AP_FRAME_COUNTER = 504u;
    ap_receipt_visual_poll();
    assert(fixture.ready == AP_VISUAL_READY);
    uint32_t request = (500u << AP_VISUAL_FRAME_SHIFT) | AP_VISUAL_TRAP;
    fixture.request = request;
    ap_receipt_visual_poll();
    assert(!fixture.request && fixture.result == request && !fixture.ready);
    assert(draws == 1 && last_art == AP_REWARD_TRAP && fixture.active == last_token);
    rejected((504u << AP_VISUAL_FRAME_SHIFT) | AP_VISUAL_GEM); /* No overlapping incoming effects. */
    AP_FRAME_COUNTER += AP_VISUAL_DURATION;
    ap_receipt_visual_poll();
    assert(!fixture.active && fixture.ready);
    rejected((500u << AP_VISUAL_FRAME_SHIFT) | AP_VISUAL_TRAP); /* Old or rewind-ambiguous. */
    rejected(((AP_FRAME_COUNTER + 1u) << AP_VISUAL_FRAME_SHIFT) | AP_VISUAL_TRAP);
    rejected((AP_FRAME_COUNTER << AP_VISUAL_FRAME_SHIFT) | (AP_VISUAL_MAX_CODE + 1u));
    request = (AP_FRAME_COUNTER << AP_VISUAL_FRAME_SHIFT) | AP_VISUAL_GEM;
    gameplay = 0u; rejected(request);
    gameplay = 1u; epoch = 0u; rejected(request);
    epoch = 1u; palette = 0u; rejected(request);
    palette = 1u; create = 0u; rejected(request); /* Native allocation guard. */
    create = 1u;
    fixture.request = request;
    ap_receipt_visual_poll();
    assert(draws == 2 && last_art == AP_REWARD_GEM && fixture.active);
    gameplay = 0u; ap_receipt_visual_poll();
    assert(!fixture.active && !fixture.ready);
    gameplay = 1u;
    ++AP_FRAME_COUNTER;
    request = (AP_FRAME_COUNTER << AP_VISUAL_FRAME_SHIFT) | (AP_REWARD_MIRROR_SHARD + 1u);
    fixture.request = request;
    ap_receipt_visual_poll();
    assert(draws == 3 && last_art == AP_REWARD_MIRROR_SHARD && fixture.result == request);
    AP_FRAME_COUNTER += AP_SHARD_AWARD_TICKS - 1u;
    ap_receipt_visual_poll();
    assert(fixture.active && !fixture.ready);
    ++AP_FRAME_COUNTER;
    ap_receipt_visual_poll();
    assert(!fixture.active && fixture.ready); /* Don't resume a cue with the pause. */
    request = (AP_FRAME_COUNTER << AP_VISUAL_FRAME_SHIFT) | AP_VISUAL_MAX_CODE;
    fixture.request = request;
    ap_receipt_visual_poll();
    assert(draws == 4 && last_art == AP_REWARD_LEVER_WALL && fixture.result == request);
    assert(ap_visual_can_start((AP_VISUAL_FRAME_MASK << AP_VISUAL_FRAME_SHIFT) | AP_VISUAL_GEM, 0u, AP_VISUAL_READY));
    return 0;
}
''')
    exe = tmp_path / ("visual.exe" if sys.platform == "win32" else "visual")
    subprocess.run([cc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-I", str(PAYLOAD),
                    str(source), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
