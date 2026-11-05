"""Run shipping shared context and Copy Room C with native save/reload spies."""
from pathlib import Path
import shutil
import subprocess
import pytest


def test_authenticated_runtime_ownership_and_reconciliation(tmp_path):
    cc = shutil.which('cc')
    if not cc:
        pytest.skip('C compiler unavailable')
    payload = Path(__file__).resolve().parents[1] / 'kirby_ap_payload'
    shared = (payload/'shared_save.c').read_text().replace('0x0800ACD5u', '&fake_save')
    copy = (payload/'copy_room.c').read_text().replace('0x080551FDu', '&fake_reload')
    source = r'''
#define _GNU_SOURCE
#include <sys/mman.h>
#include <stdint.h>
#include <string.h>
#include <stdio.h>
static int16_t fake_save(uint32_t,uint16_t);
static uint8_t fake_reload(void*,uint16_t,uint8_t,uint8_t);
''' + shared + '\n' + copy + r'''
static unsigned saves,reloads,fail;
static int16_t fake_save(uint32_t kind,uint16_t slot) { saves++;return fail ? -1 : 0; }
static uint8_t fake_reload(void*k,uint16_t r,uint8_t x,uint8_t y) { reloads++;return 1; }
#define CHECK(x) do { if(!(x)) {printf("line %d\n",__LINE__);return 1;} }while(0)
static void activate(unsigned slot,unsigned epoch) {
    CTX->cookie=COOKIE;CTX->epoch=epoch;CTX->serial=epoch;CTX->slot=slot;
    CTX->loaded_slot=slot;CTX->dirty=0;CTX->task=0x03001000;
    SAVE_SLOT=slot;FLAGS=0;LOCAL=0;HUMANS=1;
    U32(KIRBY+0xCC)=CTX->task;U32(CTX->task+8)=0x0803EE19;
    U16(CTX->task+0x10)=0x3000;U16(CTX->task+2)=1;U16(CTX->task+4)=1;
    U16(CTX->task+6)=0x2000;U16(CTX->task+0x12)=0;U8(0x03002000)=0;
    ap_shared_record_init(RECORD,AUTH);CTX->bits=ap_shared_record_bits(RECORD,AUTH);
}
int main(void) {
    CHECK(mmap((void*)0x02000000,0x40000,3,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0)!=(void*)-1);
    CHECK(mmap((void*)0x03000000,0x8000,3,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0)!=(void*)-1);
    CHECK(mmap((void*)0x08F00000,0x1000,3,MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED,-1,0)!=(void*)-1);
    memcpy((void*)AUTH,"0123456789abcdef",16);
    for(unsigned slot=0;slot<3;slot++) {
        memset((void*)RECORD,0,20);activate(slot,slot+1);
        WORD18=1;CHECK(*ap_copy_room_state(2,18,0)==0);CHECK(!ap_copy_room_owned());
        U16(KIRBY+0x60)=801;
        REQUEST[0]=slot+1;REQUEST[1]=1;ap_copy_room_poll();
        CHECK(WORD18==1 && ap_copy_room_owned() && CTX->dirty);
        CHECK(REQUEST[0]==0 && REQUEST[2]==slot+1 && REQUEST[3]==1);
        CHECK(ap_shared_update(0,AP_SHARED_GOALS));
        unsigned before=saves;fail=1;ap_shared_poll();CHECK(CTX->dirty && saves==before+1);
        fail=0;for(unsigned i=0;i<61;i++)ap_shared_poll();CHECK(!CTX->dirty);
        /* Offline polling, duplicate history and ordinary reload preserve ownership. */
        for(unsigned i=0;i<5;i++)ap_copy_room_poll();CHECK(WORD18==1);
        REQUEST[0]=slot+1;REQUEST[1]=1;ap_copy_room_poll();CHECK(!CTX->dirty);
        CTX->epoch=0;activate(slot,slot+10);CHECK(ap_copy_room_owned());
        /* A delayed command belongs to the old context and cannot revoke access. */
        REQUEST[0]=slot+1;REQUEST[1]=0;ap_copy_room_poll();CHECK(WORD18==1);
        REQUEST[0]=slot+10;REQUEST[1]=0;unsigned before_reload=reloads;ap_copy_room_poll();
        CHECK(!WORD18 && !ap_copy_room_owned() && reloads==before_reload+1);
        CHECK((CTX->bits&AP_SHARED_GOALS)==AP_SHARED_GOALS);
        ap_copy_room_poll();CHECK(reloads==before_reload+1);
        /* Mismatching auth invalidates before accepting a pending command. */
        ((uint32_t*)AUTH)[3]^=1;REQUEST[0]=slot+10;REQUEST[1]=1;ap_copy_room_poll();
        CHECK(!CTX->epoch && !ap_copy_room_owned());
        WORD18=0x1234;ap_copy_room_poll();CHECK(WORD18==0x1234); /* preview untouched */
        activate(slot,slot+20);CHECK(!ap_copy_room_owned());CHECK(CTX->bits==0);
        CHECK(*ap_copy_room_state(2,18,0)==0);
    }
    return 0;
}
'''
    cfile, exe = tmp_path/'runtime.c', tmp_path/'runtime'
    cfile.write_text(source)
    result = subprocess.run([cc,'-std=c99','-Wno-attributes','-I',str(payload),str(cfile),'-o',str(exe)],
                            capture_output=True,text=True)
    assert result.returncode == 0, result.stderr
    result = subprocess.run([str(exe)],capture_output=True,text=True)
    assert result.returncode == 0, result.stdout + result.stderr
