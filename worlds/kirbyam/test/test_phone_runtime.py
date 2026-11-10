"""Compile the shipping gate and persistent ownership code on a host CPU."""
from pathlib import Path
import shutil
import subprocess
import sys

import pytest
from ..kirby_ap_payload.patch_rom import build_phone_gate_writes


def test_r_entry_patch_validates_displaced_bytes_and_preserves_l() -> None:
    rom = bytearray(0x56E50)
    rom[0x56C2C:0x56C34] = bytes.fromhex("f0 b5 47 46 80 b4 81 b0")
    original = bytes(rom)
    assert build_phone_gate_writes(rom, 0x09001234) == {
        0x56C2C: bytes.fromhex("00 4b 18 47 35 12 00 09")}
    assert bytes(rom) == original
    for offset in range(0x56C2C, 0x56C34):
        corrupt = bytearray(rom)
        corrupt[offset] ^= 1
        with pytest.raises(SystemExit):
            build_phone_gate_writes(corrupt, 0x09001234)
    for target in (0, 0x0815E000, 0x0900FFD4):
        with pytest.raises(SystemExit):
            build_phone_gate_writes(rom, target)


def test_native_phone_ownership_preserves_copy_room_and_file_isolation(tmp_path: Path) -> None:
    cc = shutil.which("cc")
    if not cc or not sys.platform.startswith("linux"):
        pytest.skip("Linux mapped-memory host harness and C compiler required")
    assert cc is not None
    payload = Path(__file__).resolve().parents[1] / "kirby_ap_payload"
    source = (payload / "copy_room.c").read_text() + '\n' + (payload / "phone.c").read_text()
    for address, name in (("0x0800ACD5u", "fake_save"), ("0x0800A91Du", "fake_load"),
                          ("0x0800AC01u", "fake_clear"), ("0x080332BDu", "fake_start")):
        source = source.replace(address, "&" + name)
    source = r'''
#define _GNU_SOURCE
#include <sys/mman.h>
#include <stdint.h>
#include <string.h>
#include <stdio.h>
static int16_t fake_save(uint32_t,uint16_t);
static int16_t fake_load(uint32_t,uint16_t);
static void fake_clear(uint32_t);
static void fake_start(uint8_t,uint8_t,const uint16_t*,const int32_t*,const uint32_t*);
''' + source + r'''
#define WORLD ((uint32_t*)0x02028C10u)
static uint32_t files[3][32], saves, fail_save;
static int16_t fake_save(uint32_t kind,uint16_t slot) {
    saves++; if(fail_save) return -1;
    memcpy(files[slot],WORLD,sizeof(files[slot])); return 0;
}
static int16_t fake_load(uint32_t kind,uint16_t slot) {
    memcpy(WORLD,files[slot],sizeof(files[slot])); return 0;
}
static void fake_clear(uint32_t kind) { memset(WORLD,0,sizeof(files[0])); }
static void fake_start(uint8_t humans,uint8_t local,const uint16_t*r,const int32_t*p,const uint32_t*s) {
    LOCAL=local;HUMANS=humans;
    U32(KIRBY+0xCC)=0x03001000;U32(0x03001008)=0x0803EE19;
    U16(0x03001010)=0x3000;U16(0x03001002)=1;U16(0x03001004)=1;
    U16(0x03001006)=0x2000;U16(0x03001012)=0;U8(0x03002000)=0;
}
#define CHECK(x) do { if(!(x)) {printf("line %d\n",__LINE__);return 1;} }while(0)
#define START(slot) do { SAVE_SLOT=slot;ap_copy_room_load(1,slot);ap_copy_room_start(1,0,0,0,0); }while(0)
#define PHONE(value) do { AP_PHONE_REQUEST[0]=CTX->epoch;AP_PHONE_REQUEST[1]=(value);ap_phone_poll(); }while(0)
#define COPY() do { REQUEST[0]=CTX->epoch;REQUEST[1]=1;ap_copy_room_poll(); }while(0)
int main(void) {
    CHECK(mmap((void*)0x02000000,0x40000,3,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0)!=(void*)-1);
    CHECK(mmap((void*)0x03000000,0x8000,3,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0)!=(void*)-1);
    CHECK(mmap((void*)0x08F00000,0x1000,3,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0)!=(void*)-1);
    CHECK(mmap((void*)0x09000000,0x10000,3,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0)!=(void*)-1);
    memcpy((void*)AUTH,"0123456789abcdef",16);U32(0x0900FFD0)=1;
    for(unsigned slot=0;slot<3;slot++) {
        START(slot);ap_phone_poll();CHECK(!ap_phone_owned() && !ap_copy_room_owned());
        if(slot&1) COPY();
        fail_save=1;PHONE(1);ap_copy_room_poll();CHECK(ap_phone_owned() && CTX->dirty);
        fail_save=0;for(unsigned i=0;i<61;i++)ap_copy_room_poll();
        CHECK(!CTX->dirty && (files[slot][26]&AP_PHONE_OWNED));
        COPY();CHECK(ap_phone_owned() && ap_copy_room_owned() && files[slot][26]==(AP_COPY_TAG|3));
        unsigned before=saves;PHONE(0);PHONE(2);PHONE(1);ap_copy_room_poll();CHECK(saves==before);
        uint32_t stale=CTX->epoch;START(slot);CHECK(CTX->epoch!=stale);
        AP_PHONE_REQUEST[0]=stale;AP_PHONE_REQUEST[1]=1;ap_phone_poll();
        CHECK(ap_phone_owned() && ap_copy_room_owned());
        U16(KIRBY+0x60)=147;U8(0x02021580)=255;U8(0x0203AD44)=4;
        CHECK(!ap_phone_call_blocked(KIRBY));
    }
    /* Cross-seed native file invalidation revokes both, not just Copy Room. */
    ((uint32_t*)AUTH)[3]^=1;START(2);CHECK(!ap_phone_owned() && !ap_copy_room_owned());
    U16(KIRBY+0x60)=147;CHECK(ap_phone_call_blocked(KIRBY));
    CHECK(!ap_phone_call_blocked(KIRBY+0x1A8)); /* Naturally present CPU unchanged. */
    U8(0x02021580)=1;CHECK(!ap_phone_call_blocked(KIRBY)); /* Answering remains native. */
    U8(0x02021580)=255;
    for(unsigned room=803;room<=805;room++){U16(KIRBY+0x60)=room;CHECK(!ap_phone_call_blocked(KIRBY));}
    CHECK(!ap_phone_owned()); /* Tutorial bypass is not a grant. */
    U16(KIRBY+0x60)=147;U32(0x0900FFD0)=0;CHECK(!ap_phone_call_blocked(KIRBY));
    PHONE(1);CHECK(!ap_phone_owned() && !AP_PHONE_CONTEXT->epoch);
    U32(0x0900FFD0)=1;HUMANS=2;CHECK(!ap_phone_call_blocked(KIRBY));
    CHECK(!ap_copy_room_epoch()); /* Linked play is outside the single-player AP epoch. */
    return 0;
}
'''
    cfile, exe = tmp_path / "phone.c", tmp_path / "phone"
    cfile.write_text(source)
    result = subprocess.run([cc, "-std=c99", "-Wno-attributes", "-I", str(payload), str(cfile), "-o", str(exe)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    result = subprocess.run([str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
