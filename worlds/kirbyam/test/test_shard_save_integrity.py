"""Run shard grant/boss/scrub paths with mapped RAM and untouched SRAM.

This is host execution of payload C, not emulator or native save/load acceptance.
Unrelated ROM callbacks and ARM register reads are replaced; shard paths are not.
"""
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest

WORLD = Path(__file__).resolve().parents[1]


def test_shard_paths_preserve_all_save_bytes(tmp_path):
    compiler = shutil.which("cc")
    if not compiler or not sys.platform.startswith("linux"):
        pytest.skip("requires Linux mapped memory and a C compiler")
    source = (WORLD / "kirby_ap_payload/ap_payload.c").read_text()
    source = re.sub(r'register uint32_t (\w+) asm\("r[458]"\);', r'uint32_t \1 = 0;', source)
    source = source.replace('__asm__ volatile("mov %0, lr" : "=r"(caller_lr_snapshot));',
                            'caller_lr_snapshot = 0;')
    # These callbacks do not participate in shard delivery or its SRAM writes.
    for name in ("ap_sync_hub_switch_flags_from_world_props", "ap_apply_starting_kirby_color_config"):
        match = re.search(r"static void " + name + r"\(void\)\s*\{", source)
        assert match
        end, depth = match.end(), 1
        while depth:
            depth += (source[end] == "{") - (source[end] == "}")
            end += 1
        source = source[:match.end()] + "}\n" + source[end:]
    source = '#define _GNU_SOURCE\n#include <sys/mman.h>\n#include <stdio.h>\n#include <string.h>\n' + source
    source += r'''
#define SAVE ((unsigned char *)0x0E000000u)
static unsigned char before[0x8000];
#define CHECK(x) do { if (!(x)) {printf("failed line %d native=%u authority=%u\n", __LINE__, KIRBY_SHARD_FLAGS, AP_DELIVERED_SHARD_BITFIELD);return 1;} } while(0)
static void reset(unsigned flags) {
    memset((void *)0x02000000u, 0, 0x40000);
    KIRBY_SHARD_FLAGS = flags;
    AP_DELIVERED_SHARD_BITFIELD = flags;
    AP_MAILBOX_INIT_COOKIE = AP_MAILBOX_INIT_COOKIE_VALUE;
    AI_KIRBY_STATE = AI_STATE_NORMAL;
}
int main(void) {
    CHECK(mmap((void*)0x02000000u,0x40000,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0)==(void*)0x02000000u);
    CHECK(mmap(SAVE,0x8000,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0)==SAVE);
    for(unsigned i=0;i<sizeof(before);i++) before[i]=(unsigned char)(i*37u+13u);
    memcpy(SAVE,before,sizeof(before));
    for(unsigned old=0;old<256;old++) for(unsigned bit=0;bit<8;bit++) {
        unsigned mask=1u<<bit;
        reset(old);
        AP_IN_ITEM_ID=3860002u+bit; AP_IN_FLAG=1; AP_IN_PLAYER=2;
        ap_poll_mailbox_c();
        CHECK(KIRBY_SHARD_FLAGS==(old|mask));
        CHECK(AP_DELIVERED_SHARD_BITFIELD==(old|mask));
        CHECK(AP_ITEM_RCVD_COUNTER==1 && AP_IN_FLAG==0);
        CHECK(memcmp(SAVE,before,sizeof(before))==0);
        AP_IN_FLAG=1;ap_poll_mailbox_c();
        CHECK(KIRBY_SHARD_FLAGS==(old|mask) && AP_ITEM_RCVD_COUNTER==2);
        CHECK(memcmp(SAVE,before,sizeof(before))==0);
        reset(old);
        ap_on_boss_defeat_collect_shard(bit);
        CHECK(KIRBY_SHARD_FLAGS==(old|mask));
        CHECK(AP_BOSS_DEFEAT_FLAGS==mask && AP_BOSS_TEMP_SHARD_BITFIELD==mask);
        CHECK(memcmp(SAVE,before,sizeof(before))==0);
        ap_poll_mailbox_c();
        CHECK(KIRBY_SHARD_FLAGS==old && AP_BOSS_TEMP_SHARD_BITFIELD==0);
        CHECK(memcmp(SAVE,before,sizeof(before))==0);
    }
    puts("2048 prior-state/shard cases: mailbox grant/replay, boss grant and gameplay scrub preserve all 32768 SRAM bytes");
    return 0;
}
'''
    cfile, exe = tmp_path / "save-integrity.c", tmp_path / "save-integrity"
    cfile.write_text(source)
    result = subprocess.run([compiler, "-std=gnu99", "-w", "-I", str(WORLD / "kirby_ap_payload"),
                             str(cfile), "-o", str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    result = subprocess.run([str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
