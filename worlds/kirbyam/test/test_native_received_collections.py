"""Execute shipping mailbox receipts against native RAM fields (#953, #971).

Host execution checks native effects and ACKs; it does not simulate the ARM ABI,
rendered HUD, cheats, or emulator save/load.
"""
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest

WORLD = Path(__file__).resolve().parents[1]


def test_mailbox_collections_and_active_player_vitality(tmp_path: Path) -> None:
    compiler = shutil.which('cc')
    if not compiler or not sys.platform.startswith('linux'):
        pytest.skip('requires Linux mapped memory and a C compiler')
    source = (WORLD / 'kirby_ap_payload/ap_payload.c').read_text()
    source = re.sub(r'register uint32_t (\w+) asm\("r[458]"\);', r'uint32_t \1 = 0;', source)
    source = source.replace('__asm__ volatile("mov %0, lr" : "=r"(caller_lr_snapshot));',
                            'caller_lr_snapshot = 0;')
    # These ROM callbacks are unrelated to the receipt/ACK paths under test.
    for name in ('ap_sync_hub_switch_flags_from_world_props', 'ap_apply_starting_kirby_color_config'):
        match = re.search(r'static void ' + name + r'\(void\)\s*\{', source)
        assert match
        end, depth = match.end(), 1
        while depth:
            depth += (source[end] == '{') - (source[end] == '}')
            end += 1
        source = source[:match.end()] + '}\n' + source[end:]
    source = '#define _GNU_SOURCE\n#include <sys/mman.h>\n#include <stdio.h>\n#include <string.h>\n' + source
    source += r'''
#define CHECK(x) do { if (!(x)) {printf("failed line %d\n", __LINE__);return 1;} } while(0)
static void reset(void) {
    memset((void *)0x02000000u, 0, 0x40000);
    AP_MAILBOX_INIT_COOKIE = AP_MAILBOX_INIT_COOKIE_VALUE;
    AI_KIRBY_STATE = AI_STATE_NORMAL;
}
static void receive(unsigned item) {
    AP_IN_ITEM_ID = item;
    AP_IN_PLAYER = 2;
    AP_IN_FLAG = 1;
    ap_poll_mailbox_c();
}
int main(void) {
    CHECK(mmap((void*)0x02000000u, 0x40000, PROT_READ|PROT_WRITE,
        MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED, -1, 0) == (void*)0x02000000u);
    for (unsigned item=3860200; item<=3860223; item++) {
        for (unsigned player_owned=0; player_owned<2; player_owned++) {
            reset();
            unsigned char chest_before[16];
            memset(chest_before, 0xA5, sizeof(chest_before));
            memcpy((void*)0x02038960u, chest_before, sizeof(chest_before));
            KIRBY_SPRAY_PAINT_FLAGS = 0x80000000u;
            KIRBY_MUSIC_PLAYER_AND_SHEETS_FLAGS = 0x40000000u | player_owned;
            unsigned spray = KIRBY_SPRAY_PAINT_FLAGS;
            unsigned music = KIRBY_MUSIC_PLAYER_AND_SHEETS_FLAGS;
            if (item<3860214) spray |= 1u<<(item-3860200);
            else music |= 1u<<(item-3860214+1);
            for (unsigned replay=0; replay<2; replay++) {
                receive(item);
                CHECK(AP_IN_FLAG == 0 && AP_ITEM_RCVD_COUNTER == replay+1);
                CHECK(KIRBY_SPRAY_PAINT_FLAGS == spray);
                CHECK(KIRBY_MUSIC_PLAYER_AND_SHEETS_FLAGS == music);
                CHECK(memcmp((void*)0x02038960u, chest_before, sizeof(chest_before)) == 0);
                CHECK(AP_MINOR_CHEST_EVENT_COUNTER == 0);
            }
        }
    }
    for (unsigned player=0; player<4; player++) {
        for (unsigned dead=0; dead<2; dead++) {
            reset();
            KIRBY_CURRENT_PLAYER = player;
            for (unsigned i=0; i<4; i++) {
                unsigned address = KIRBY_STRUCTS_ADDR + i*KIRBY_STRUCT_STRIDE;
                *(int8_t*)(address+KIRBY_STRUCT_HP_OFFSET) = i==player && dead ? 0 : 3;
                *(int8_t*)(address+KIRBY_STRUCT_MAX_HP_OFFSET) = 6;
            }
            receive(3860018);
            CHECK(AP_IN_FLAG == 0 && AP_ITEM_RCVD_COUNTER == 1);
            CHECK(KIRBY_VITALITY_COUNTER == 1);
            for (unsigned i=0; i<4; i++) {
                unsigned address = KIRBY_STRUCTS_ADDR + i*KIRBY_STRUCT_STRIDE;
                CHECK(*(int8_t*)(address+KIRBY_STRUCT_HP_OFFSET) == (i==player ? (dead ? 0 : 7) : 3));
                CHECK(*(int8_t*)(address+KIRBY_STRUCT_MAX_HP_OFFSET) == (i==player ? 7 : 6));
            }
            unsigned address = KIRBY_STRUCTS_ADDR + player*KIRBY_STRUCT_STRIDE;
            *(int8_t*)(address+KIRBY_STRUCT_HP_OFFSET) = dead ? 0 : 2;
            receive(3860018);
            CHECK(AP_IN_FLAG == 0 && AP_ITEM_RCVD_COUNTER == 2);
            CHECK(KIRBY_VITALITY_COUNTER == 1);
            CHECK(*(int8_t*)(address+KIRBY_STRUCT_HP_OFFSET) == (dead ? 0 : 2));
        }
    }
    return 0;
}
'''
    cfile, executable = tmp_path / 'receipts.c', tmp_path / 'receipts'
    cfile.write_text(source)
    result = subprocess.run([compiler, '-std=gnu99', '-w', '-I', str(WORLD / 'kirby_ap_payload'),
                             str(cfile), '-o', str(executable)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    result = subprocess.run([str(executable)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
