"""Actual live-counter C with synthetic mapped context; no game execution."""
from pathlib import Path
import shutil
import subprocess
import sys
import pytest
from ..kirby_ap_payload.patch_rom import BATTERY_SITES, build_battery_writes


def test_all_native_battery_sites_have_closed_byte_guards():
    rom = bytearray(0x123200)
    targets = {name: 0x0815F600 for name in BATTERY_SITES}
    for _, (offset, data) in BATTERY_SITES.items():
        rom[offset:offset+4] = bytes.fromhex(data)
    original = bytes(rom)
    writes = build_battery_writes(rom, targets)
    assert len(writes) == 13 and bytes(rom) == original
    for name, (offset, _) in BATTERY_SITES.items():
        for byte in range(4):
            broken = bytearray(rom); broken[offset+byte] ^= 1
            with pytest.raises(SystemExit): build_battery_writes(broken, targets)
        for bad in (True, 0, 0x0815F689, 0x09000000):
            with pytest.raises(SystemExit): build_battery_writes(rom, dict(targets, **{name: bad}))


def test_actual_live_counter_boundaries_and_context(tmp_path):
    if not shutil.which("cc") or not sys.platform.startswith("linux"):
        pytest.skip("Linux mapped-memory C harness required")
    payload = Path(__file__).resolve().parents[1] / "kirby_ap_payload"
    source = r'''
#define _GNU_SOURCE
#include <sys/mman.h>
#include <assert.h>
#include <stdint.h>
#include "battery.h"
static uint32_t epoch=1, owned;
uint32_t ap_copy_room_epoch(void) { return epoch; }
uint32_t ap_phone_owned(void) { return owned; }
''' + (payload / "battery.c").read_text() + r'''
int main(void) {
 assert(mmap((void*)0x02000000,0x40000,3,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0)!=(void*)-1);
 assert(mmap((void*)0x09000000,0x10000,3,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0)!=(void*)-1);
 *(uint8_t*)0x0203AD30=1; *(uint32_t*)0x0900FFD0=1; AP_COPY_CONTEXT->task=0x03001000; AP_COPY_CONTEXT->epoch=epoch;
 ap_battery_start(); assert(BATCTX->count==3 && *(uint8_t*)LOCAL_BYTE==3);
 assert(ap_battery_visible(LOCAL_BYTE)==0); assert(ap_battery_grant(LOCAL_KIRBY));
 assert(BATCTX->count==4 && ap_battery_visible(LOCAL_BYTE)==0);
 owned=1; assert(ap_battery_visible(LOCAL_BYTE)==4 && BATCTX->count==4);
 owned=0; epoch=0; assert(ap_battery_visible(LOCAL_BYTE)==4 && !BATCTX->active);
 epoch=1; ap_battery_start(); assert(ap_battery_visible(LOCAL_BYTE)==0);
 owned=1;
 uint32_t values[]={0,1,2,3,4,254,255,256,UINT32_MAX};
 for(unsigned i=0;i<sizeof(values)/sizeof(*values);i++) {
   uint32_t n=values[i]; BATCTX->count=n; *(uint8_t*)LOCAL_BYTE=ap_battery_proxy(n);
   uint32_t success=ap_battery_grant(LOCAL_KIRBY);
   assert(success==(n!=UINT32_MAX)); assert(BATCTX->count==(n==UINT32_MAX?n:n+1));
   assert(*(uint8_t*)LOCAL_BYTE==ap_battery_proxy(BATCTX->count));
   ap_battery_native(LOCAL_BYTE,AP_BATTERY_DRAIN); assert(BATCTX->count==0);
   ap_battery_native(LOCAL_BYTE,AP_BATTERY_SET1); assert(BATCTX->count==1);
   ap_battery_native(LOCAL_BYTE,AP_BATTERY_SET3); assert(BATCTX->count==3);
   ap_battery_native(LOCAL_BYTE,AP_BATTERY_PICKUP); assert(BATCTX->count==3);
 }
 BATCTX->count=257; *(uint8_t*)LOCAL_BYTE=255;
 for(unsigned n=256;n>=254;n--) {ap_battery_native(LOCAL_BYTE,AP_BATTERY_SPEND);assert(BATCTX->count==n);assert(*(uint8_t*)LOCAL_BYTE==ap_battery_proxy(n));}
 ap_battery_native(LOCAL_BYTE,AP_BATTERY_SET1); assert(BATCTX->count==254);
 for(unsigned n=0;n<256;n++) { *(uint8_t*)LOCAL_BYTE=n; owned=0;assert(ap_battery_visible(LOCAL_BYTE)==0);owned=1;assert(ap_battery_visible(LOCAL_BYTE)==n); }
 BATCTX->count=300; *(uint8_t*)(LOCAL_BYTE+0x1A8)=2;
 ap_battery_native(LOCAL_BYTE+0x1A8,AP_BATTERY_PICKUP);
 assert(BATCTX->count==300 && *(uint8_t*)(LOCAL_BYTE+0x1A8)==3);
 epoch=2; assert(!ap_battery_grant(LOCAL_KIRBY) && !BATCTX->active);
 AP_COPY_CONTEXT->epoch=epoch; ap_battery_start(); assert(BATCTX->count==3);
 BATCTX->count=999; AP_COPY_CONTEXT->task++; assert(!ap_battery_grant(LOCAL_KIRBY));
 ap_battery_start(); epoch=0; assert(!ap_battery_grant(LOCAL_KIRBY));
 *(uint32_t*)0x0900FFD0=0; *(uint8_t*)LOCAL_BYTE=3;
 assert(ap_battery_grant(LOCAL_KIRBY) && *(uint8_t*)LOCAL_BYTE==3);
 return 0;
}
'''
    c = tmp_path / "battery.c"; c.write_text(source)
    exe = tmp_path / "battery"
    subprocess.run(["cc", "-std=c11", "-Wno-attributes", "-I", str(payload), str(c), "-o", str(exe)], check=True)
    subprocess.run([str(exe)], check=True, timeout=5)
