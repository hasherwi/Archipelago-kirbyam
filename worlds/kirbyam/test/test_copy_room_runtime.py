"""Execute shipping C against three native-file save/load spies, not an emulator."""
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


def test_three_file_ownership_and_save_retries(tmp_path):
    cc = shutil.which("cc")
    if not cc or not sys.platform.startswith("linux"):
        pytest.skip("Linux mapped-memory host harness and C compiler required")
    payload = Path(__file__).resolve().parents[1] / "kirby_ap_payload"
    source = (payload / "copy_room.c").read_text()
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
static uint32_t files[3][32];
static unsigned saves[3], fail_save, fail_load;
static int16_t fake_save(uint32_t kind,uint16_t slot) {
    if(kind!=1 || slot>2) return -99;
    saves[slot]++; if(fail_save) return -1;
    memcpy(files[slot], WORLD, sizeof(files[slot]));return 0;
}
static int16_t fake_load(uint32_t kind,uint16_t slot) {
    if(kind!=1) return 0;
    if(fail_load || slot>2) return -1;
    memcpy(WORLD,files[slot],sizeof(files[slot]));return 0;
}
static void fake_clear(uint32_t kind) { if(kind==1) memset(WORLD,0,sizeof(files[0])); }
static void fake_start(uint8_t humans,uint8_t local,const uint16_t*r,const int32_t*p,const uint32_t*s) {
    LOCAL=local;HUMANS=humans;
    U32(KIRBY+0xCC)=0x03001000;U32(0x03001008)=0x0803EE19;
    U16(0x03001010)=0x3000;U16(0x03001002)=1;U16(0x03001004)=1;
    U16(0x03001006)=0x2000;U16(0x03001012)=0;U8(0x03002000)=0;
}
#define CHECK(x) do { if(!(x)) {printf("line %d\n",__LINE__);return 1;} }while(0)
#define START() ap_copy_room_start(1,0,0,0,0)
#define COMMAND(v) do{REQUEST[0]=CTX->epoch;REQUEST[1]=(v);ap_copy_room_poll();}while(0)
int main(void) {
    CHECK(mmap((void*)0x02000000,0x40000,3,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0)!=(void*)-1);
    CHECK(mmap((void*)0x03000000,0x8000,3,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0)!=(void*)-1);
    CHECK(mmap((void*)0x08F00000,0x1000,3,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0)!=(void*)-1);
    memcpy((void*)AUTH,"0123456789abcdef",16);
    for(unsigned slot=0;slot<3;slot++) {
        for(unsigned i=0;i<32;i++) files[slot][i]=0xA5000000+slot*256+i;
        files[slot][18]=1; /* Old native all-switch bit is never ownership. */
        SAVE_SLOT=slot;FLAGS=0;CHECK(ap_copy_room_load(1,slot)==0);
        CHECK(!ap_copy_room_owned());
        unsigned before=saves[slot];uint32_t preview[32];memcpy(preview,WORLD,sizeof(preview));
        REQUEST[0]=123;REQUEST[1]=1;ap_copy_room_poll();
        CHECK(!memcmp(preview,WORLD,sizeof(preview)) && saves[slot]==before);
        START();CHECK(CTX->slot==slot && CTX->loaded_slot==slot && CTX->epoch);
        CHECK(*ap_copy_room_state(2,18,0)==0 && !ap_copy_room_owned());
        U16(KIRBY+0x60)=801;
        fail_save=1;COMMAND(1);CHECK(ap_copy_room_owned() && WORD18==1 && CTX->dirty);
        CHECK(saves[slot]==before+1 && (files[slot][26]&~1u)!=AP_COPY_TAG);
        fail_save=0;for(unsigned i=0;i<61;i++)ap_copy_room_poll();
        CHECK(!CTX->dirty && saves[slot]==before+2 && files[slot][26]==(AP_COPY_TAG|1));
        for(unsigned i=0;i<32;i++) if(i!=18 && (i<22 || i>26))
            CHECK(files[slot][i]==0xA5000000+slot*256+i); /* Hub and all other words preserved. */
        before=saves[slot];COMMAND(1);CHECK(!CTX->dirty && saves[slot]==before);
        for(unsigned i=0;i<5;i++)ap_copy_room_poll();CHECK(ap_copy_room_owned());
        uint32_t old_epoch=CTX->epoch;
        CHECK(ap_copy_room_load(1,slot)==0);CHECK(!ap_copy_room_epoch());START();
        CHECK(ap_copy_room_owned() && CTX->epoch!=old_epoch);
        REQUEST[0]=old_epoch;REQUEST[1]=0;ap_copy_room_poll();CHECK(ap_copy_room_owned());
        COMMAND(0);
        CHECK(!ap_copy_room_owned() && !WORD18);
        CHECK(files[slot][26]==AP_COPY_TAG);ap_copy_room_poll();CHECK(!ap_copy_room_owned());
        COMMAND(1); /* Preserve independently for final offline loads. */
    }
    for(unsigned slot=0;slot<3;slot++) {
        SAVE_SLOT=slot;CHECK(ap_copy_room_load(1,slot)==0);START();CHECK(ap_copy_room_owned());
        CHECK(CTX->slot==slot);
    }
    /* A pending command cannot cross a file preview, failed load or clear. */
    uint32_t stale=CTX->epoch;REQUEST[0]=stale;REQUEST[1]=0;
    SAVE_SLOT=0;CHECK(ap_copy_room_load(1,0)==0);CHECK(!REQUEST[0]);START();
    CHECK(ap_copy_room_owned());
    fail_load=1;CHECK(ap_copy_room_load(1,1)==-1);START();CHECK(!ap_copy_room_epoch());fail_load=0;
    SAVE_SLOT=1;ap_copy_room_clear(1);CHECK(!ap_copy_room_epoch());START();CHECK(!ap_copy_room_owned());
    COMMAND(1);CHECK(ap_copy_room_owned());
    /* Changed native selection / non-adventure task revokes context, not another save. */
    SAVE_SLOT=2;REQUEST[0]=CTX->epoch;REQUEST[1]=0;CHECK(!ap_copy_room_epoch());
    CHECK(ap_copy_room_load(1,2)==0);START();CHECK(ap_copy_room_owned());
    FLAGS=0x10;CHECK(!ap_copy_room_epoch());FLAGS=0;CHECK(!ap_copy_room_epoch());
    CHECK(ap_copy_room_load(1,2)==0);START();CHECK(ap_copy_room_owned());
    U32(CTX->task+8)=0;CHECK(!ap_copy_room_epoch());
    /* Wrong seed is never migrated from native word18 or old record. */
    ((uint32_t*)AUTH)[3]^=1;SAVE_SLOT=2;CHECK(ap_copy_room_load(1,2)==0);START();
    CHECK(!ap_copy_room_owned());COMMAND(0);CHECK(files[2][26]==AP_COPY_TAG);
    for(unsigned slot=3;slot<5;slot++) {
        SAVE_SLOT=slot;ap_copy_room_clear(1);START();CHECK(!ap_copy_room_epoch());
    }
    return 0;
}
'''
    cfile, exe = tmp_path / "runtime.c", tmp_path / "runtime"
    cfile.write_text(source)
    result = subprocess.run([cc, "-std=c99", "-Wno-attributes", "-I", str(payload), str(cfile), "-o", str(exe)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    result = subprocess.run([str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
