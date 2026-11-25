"""Animated shard renders into its own graphics allocation or fails closed."""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

WORLD = Path(__file__).resolve().parents[1]
PAYLOAD = WORLD / "kirby_ap_payload"


def test_animated_shard_queue_bounds_and_cleanup(tmp_path: Path) -> None:
    cc = shutil.which("cc")
    if not cc:
        pytest.skip("requires a native C compiler")
    source = tmp_path / "shard.c"
    source.write_text(r'''
#include <assert.h>
#include "shard_award_runtime.h"

int main(void) {
    uint16_t heap[9] = {1u, 0, 0, 0, 0, 0, 0, 0, 0};
    assert(ap_reward_native_vram_can_fit_tiles(heap, 18u, 0x06014000u, 16u));
    assert(!ap_reward_native_vram_can_fit_tiles(heap, 16u, 0x06014000u, 16u));
    heap[0] = 3u; /* Interior zeros are not a free run. */
    assert(!ap_reward_native_vram_can_fit_tiles(heap, 18u, 0x06014000u, 16u));
    assert(ap_reward_native_vram_can_fit(heap, 18u, 0x06014000u));
    assert(!ap_reward_native_vram_can_fit_tiles(heap, 18u, 0x06017F00u, 16u));

    struct ApChestTileUpload ring[64] = {0};
    const uint32_t gfx = 0x06015000u, other = 0x06015200u;
    uint8_t head = 63u;
    ring[63] = (struct ApChestTileUpload){AP_SHARD_AWARD_NATIVE_TILES, gfx, 512u, 0u};
    assert(ap_shard_award_redirect_first(ring, 63u, 0u, gfx));
    assert(ring[63].source == AP_SHARD_AWARD_FIRST && ring[63].size == 512u);
    assert(!ap_shard_award_redirect_first(ring, 63u, 0u, gfx));
    assert(!ap_shard_award_queue_frame(ring, &head, 0u, gfx, 38u)); /* Full ring. */
    assert(!ap_shard_award_queue_frame(ring, &head, 2u, gfx, 40u));
    assert(!ap_shard_award_queue_frame(ring, &head, 2u, 0x06017F80u, 38u));
    assert(ap_shard_award_queue_frame(ring, &head, 62u, gfx, 38u) && head == 0u);
    assert(ring[63].source == AP_SHARD_AWARD_FIRST + 38u * 512u && ring[63].size == 512u);
    assert(ap_shard_award_queue_frame(ring, &head, 62u, other, 2u) && head == 1u);
    ring[1] = (struct ApChestTileUpload){AP_SHARD_AWARD_NATIVE_TILES, gfx, 512u, 0u};
    /* Cleanup may only cancel pending transfers of that owned effect. */
    ap_shard_award_cancel_uploads(ring, 2u, 63u, gfx);
    assert(!ring[63].size && ring[0].size == 512u && ring[1].size == 512u);
    ap_shard_award_cancel_uploads(ring, 2u, 9u, other);
    assert(!ring[0].size && ring[1].size == 512u);
    unsigned changed = 0u;
    for (unsigned tick = 0u; tick < 40u; ++tick) changed += ap_shard_award_frame_changed(tick);
    assert(changed == 20u && ap_shard_award_frame_changed(8u) && ap_shard_award_frame_changed(38u));
    assert(!ap_shard_award_frame_changed(22u) && !ap_shard_award_frame_changed(40u));
    return 0;
}
''')
    exe = tmp_path / ("shard.exe" if sys.platform == "win32" else "shard")
    subprocess.run([cc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-I", str(PAYLOAD),
                    str(source), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
