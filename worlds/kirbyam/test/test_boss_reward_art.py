"""Only the native area boss shard sprite is restyled; no new reward event."""
import runpy
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from .test_runtime_regression_hooks import patch_rom

WORLD = Path(__file__).resolve().parents[1]
PAYLOAD = WORLD / "kirby_ap_payload"


def test_native_shard_render_calls_and_animation_are_guarded() -> None:
    rom = runpy.run_path(str(WORLD / "tools" / "create_dummy_rom.py"))["build_dummy_rom"]()
    groups = patch_rom.BOSS_SHARD_ART_HOOK_GROUPS
    targets = {name: 0x0815E110 + 4 * i for i, (name, _, _) in enumerate(groups)}
    offsets = {offset for _, _, calls in groups for offset in calls}
    assert len(offsets) == 6
    assert patch_rom.build_boss_shard_art_hooks(rom, targets) == {
        offset: patch_rom.thumb_bl_bytes(0x08000000 + offset, targets[name])
        for name, _, calls in groups for offset in calls
    }
    for offset in (*offsets, patch_rom.BOSS_SHARD_NATIVE_SCRIPT_OFFSET + 54):
        rom[offset] ^= 1
        with pytest.raises(SystemExit, match="native boss shard"):
            patch_rom.build_boss_shard_art_hooks(rom, targets)
        rom[offset] ^= 1


def test_nine_native_tile_batches_keep_original_queue_length_and_destination(tmp_path: Path) -> None:
    cc = shutil.which("cc")
    if not cc:
        pytest.skip("requires a native C compiler")
    source = tmp_path / "shard-art.c"
    source.write_text(r'''
#include <assert.h>
#include "boss_shard_art_runtime.h"
#include "chest_reward_art.h"

int main(void) {
    struct ApChestTileUpload ring[64] = {0};
    const uint32_t addr[9]={0x086247ACu, 0x086248CCu, 0x086249ECu, 0x08624A4Cu,
        0x08624B6Cu, 0x08624C8Cu, 0x08624DACu, 0x08624E0Cu, 0x08624F2Cu};
    const uint32_t tile=0x06014800u, art=0x09004280u;
    assert(sizeof(gApChestRewardArt)==288u);
    for (unsigned i=128u; i<288u; ++i) assert(gApChestRewardArt[i]==0u);
    for (unsigned frame=0; frame<9; ++frame) {
        uint8_t dest=frame ? frame-1u : 63u, next=(dest+1u)&63u;
        uint16_t size=frame==2u || frame==6u ? 96u : 288u;
        ring[dest]=(struct ApChestTileUpload){addr[frame],tile,size,0xA5A5u};
        assert(!ap_boss_shard_redirect_upload(ring,dest,next,tile+32u,art));
        assert(!ap_boss_shard_redirect_upload(ring,dest,(dest+2u)&63u,tile,art));
        assert(ring[dest].source==addr[frame] && ring[dest].size==size);
        assert(ap_boss_shard_redirect_upload(ring,dest,next,tile,art));
        assert(ring[dest].source==art && ring[dest].size==size
               && ring[dest].destination==tile && ring[dest].padding==0xA5A5u);
    }
    ring[63]=(struct ApChestTileUpload){0x086247ACu,tile,96u,0u};
    assert(!ap_boss_shard_redirect_upload(ring,63u,0u,tile,art));
    ring[63]=(struct ApChestTileUpload){0x0861F46Cu,tile,128u,0u};
    assert(!ap_boss_shard_redirect_upload(ring,63u,0u,tile,art));
    return 0;
}
''')
    exe = tmp_path / ("test-shard-art.exe" if sys.platform == "win32" else "test-shard-art")
    subprocess.run([cc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-I", str(PAYLOAD),
                    str(source), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
