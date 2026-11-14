"""Execute shipping switch persistence against host RAM and a save-call spy.

This verifies call policy and buffer reload, not native ARM/SRAM acceptance.
"""
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest


def test_shipping_switch_callback_and_initializer(tmp_path):
    cc = shutil.which('cc')
    if not cc or not sys.platform.startswith('linux'):
        pytest.skip('Linux mapped memory and C compiler required')
    payload = Path(__file__).resolve().parents[1] / 'kirby_ap_payload'
    source = (payload / 'ap_payload.c').read_text()
    source += "\n" + (payload / 'copy_room.c').read_text()
    source += "\n" + (payload / 'phone.c').read_text()
    source = re.sub(r'register uint32_t (\w+) asm\("r[458]"\);', r'uint32_t \1 = 0;', source)
    source = source.replace('__asm__ volatile("mov %0, lr" : "=r"(caller_lr_snapshot));',
                            'caller_lr_snapshot = 0;')
    source = source.replace('0x08039671u', '&fake_complete')
    source = source.replace('0x0800ACD5u', '&fake_save').replace('0x08031CE5u', '&fake_network')
    source = '''#define _GNU_SOURCE
#include <sys/mman.h>
#include <string.h>
#include <stdint.h>
#include <stdio.h>
static int16_t fake_save(uint32_t, uint16_t);
static void fake_network(uint32_t);
static void fake_complete(void);
static void fake_unknown(void);
''' + source
    source += r'''
#define CHECK(x) do { if (!(x)) {printf("line %d\n",__LINE__);return 1;} } while(0)
static unsigned saves, network_requests, completions, unknown_calls;
static void fake_complete(void) { completions++; }
static void fake_unknown(void) { unknown_calls++; }
static uint32_t disk[3][32];
static int16_t fake_save(uint32_t section, uint16_t slot) {
    if(section!=1 || slot>2) return -1;
    saves++; memcpy(disk[slot],(void*)0x02028C10u,128); return 0;
}
static void fake_network(uint32_t request) { if(request==8) network_requests++; }
int main(void) {
    CHECK(mmap((void*)0x09000000u,0x10000,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0)==(void*)0x09000000u);
    CHECK(mmap((void*)0x02000000u,0x40000,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0)==(void*)0x02000000u);
    CHECK(mmap((void*)0x08F00000u,4096,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0)==(void*)0x08F00000u);
    CHECK(mmap((void*)0x08340000u,65536,PROT_READ|PROT_WRITE,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0)==(void*)0x08340000u);
    for(unsigned i=0;i<15;i++) ((uint32_t*)0x0834BDBCu)[i]=0x08126405u+12*i;
    ap_on_world_map_unlock_call(fake_unknown); CHECK(unknown_calls==1 && completions==0 && saves==0);
    ap_on_world_map_unlock_call(0); CHECK(unknown_calls==1 && completions==0);
    memcpy((void*)AP_HUB_ROM_AUTH,"0123456789abcdef",16);
    for(unsigned slot=0;slot<3;slot++) {
        memset((void*)0x02000000u,0,0x40000);
        *(uint16_t*)0x0203AD48u=slot;
        for(unsigned door=1;door<=15;door++) {
            unsigned bit=ap_hub_bits[door], before=saves;
            /* Receipt opens a door but must leave the physical switch visible. */
            *(uint32_t*)(0x02028C10u+ap_hub_props[door]*4)=1;
            CHECK(*ap_on_hub_switch_init_state_lookup(2,ap_hub_props[door],0)==0);
            unsigned complete_before=completions;
            ap_on_world_map_unlock_call((WorldMapUnlockFn)(uintptr_t)(0x08126405u+12*(door-1)));
            CHECK(saves==before+1 && completions==complete_before+1 && unknown_calls==1);
            ap_set_hub_switch_flag(bit); CHECK(saves==before+1);
            memset((void*)0x02028C10u,0,128); AP_HUB_SWITCH_FLAGS=0;
            memcpy((void*)0x02028C10u,disk[slot],128);
            CHECK(*ap_on_hub_switch_init_state_lookup(2,ap_hub_props[door],0)==1);
            CHECK(AP_HUB_SWITCH_FLAGS&(1u<<bit));
            CHECK(*(uint32_t*)(0x02028C10u+ap_hub_props[door]*4)==1);
        }
        CHECK(AP_HUB_SWITCH_FLAGS==0x7FFF);
        *(uint32_t*)AP_HUB_ROM_AUTH^=1;ap_restore_hub_switch_checks();CHECK(AP_HUB_SWITCH_FLAGS==0);
        *(uint32_t*)AP_HUB_ROM_AUTH^=1;ap_restore_hub_switch_checks();CHECK(AP_HUB_SWITCH_FLAGS==0x7FFF);
        memset((void*)AP_HUB_SAVED_CHECKS,0,20);ap_restore_hub_switch_checks();CHECK(AP_HUB_SWITCH_FLAGS==0);
        unsigned before=saves;
        *(uint32_t*)0x0203AD10u=0x10;ap_set_hub_switch_flag(0);CHECK(saves==before);
        *(uint32_t*)0x0203AD10u=2;*(uint8_t*)0x0203AD3Cu=1;
        ap_set_hub_switch_flag(1);CHECK(saves==before && network_requests==slot+1);
        *(uint8_t*)0x0203AD24u=1;ap_set_hub_switch_flag(2);CHECK(saves==before+1);
    }
    return 0;
}
'''
    cfile, exe = tmp_path / 'payload.c', tmp_path / 'payload'
    cfile.write_text(source)
    result = subprocess.run([cc, '-std=gnu99', '-w', '-I', str(payload), str(cfile), '-o', str(exe)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    result = subprocess.run([str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
