"""Shared record authentication and client fencing; native tests are separate."""
from pathlib import Path
import shutil
import struct
import subprocess

import pytest

from ..shared_save_protocol import decode_shared_snapshot, shared_slot_version


def test_shared_record_authentication(tmp_path):
    cc = shutil.which('cc')
    if not cc:
        pytest.skip('C compiler unavailable')
    source = r'''
#include <string.h>
#include "shared_save_logic.h"
#define CHECK(x) do { if (!(x)) return __LINE__; } while (0)
int main(void) {
    uint32_t world[32],disk[3][32],auth[4]={1,2,3,4};
    for(unsigned slot=0;slot<3;slot++) {
        for(unsigned i=0;i<32;i++) world[i]=0xdead0000+i;
        CHECK(ap_shared_record_init(world+22,auth));
        CHECK(!ap_shared_record_init(world+22,auth));
        CHECK(ap_shared_record_bits(world+22,auth)==0);
        for(unsigned i=0;i<32;i++) if(i<22||i>26) CHECK(world[i]==0xdead0000+i);
        CHECK(ap_shared_record_update(world+22,auth,0,AP_SHARED_ACCESS_VALID|AP_SHARED_ACCESS_OWNED));
        for(unsigned i=0;i<16;i++) CHECK(ap_shared_record_update(world+22,auth,0,1u<<i));
        CHECK(ap_shared_record_bits(world+22,auth)==AP_SHARED_BITS);
        CHECK(!ap_shared_record_update(world+22,auth,0,1));
        CHECK(!ap_shared_record_update(world+22,auth,1u<<19,0));
        CHECK(ap_shared_record_update(world+22,auth,AP_SHARED_ACCESS_OWNED,0));
        CHECK(ap_shared_record_bits(world+22,auth)==(AP_SHARED_GOALS|AP_SHARED_ACCESS_VALID));
        memcpy(disk[slot],world,sizeof(world));memset(world,0,sizeof(world));
        memcpy(world,disk[slot],sizeof(world));
        CHECK(ap_shared_record_bits(world+22,auth)==(AP_SHARED_GOALS|AP_SHARED_ACCESS_VALID));
        for(unsigned i=0;i<4;i++) {
            auth[i]^=16;
            CHECK(!ap_shared_record_valid(world+22,auth));
            CHECK(!ap_shared_record_update(world+22,auth,0,1));
            CHECK(ap_shared_record_init(world+22,auth));
            CHECK(ap_shared_record_bits(world+22,auth)==0);
            auth[i]^=16;
            CHECK(ap_shared_record_init(world+22,auth));
            CHECK(ap_shared_record_update(world+22,auth,0,AP_SHARED_BITS));
        }
        world[26]^=1u<<18;
        CHECK(!ap_shared_record_valid(world+22,auth));
        CHECK(ap_shared_record_init(world+22,auth));
        CHECK(ap_shared_record_bits(world+22,auth)==0);
    }
    CHECK(ap_shared_next_epoch(0)==1);
    CHECK(ap_shared_next_epoch(0xffffffff)==1);
    CHECK(ap_shared_next_epoch(999)==1000);
    return 0;
}
'''
    include = Path(__file__).resolve().parents[1] / 'kirby_ap_payload'
    cfile, exe = tmp_path/'shared.c', tmp_path/'shared'
    cfile.write_text(source)
    subprocess.run([cc,'-std=c99','-Wall','-Wextra','-Werror','-I',str(include),str(cfile),'-o',str(exe)],
                   check=True, capture_output=True)
    result = subprocess.run([str(exe)], capture_output=True)
    assert result.returncode == 0, result.returncode


def test_snapshot_rejects_reload_menu_wrong_slot_and_partial_reads():
    words = [4,4,0,1,0,0x03001000,0x3ffff,0x41505331,0]
    raw = struct.pack('<9I', *words)
    snapshot = decode_shared_snapshot(raw,raw[:12])
    assert snapshot is not None and (snapshot.epoch,snapshot.slot,snapshot.bits,snapshot.dirty)==(4,0,0x3ffff,True)
    assert decode_shared_snapshot(raw,struct.pack('<3I',5,5,2)) is None
    assert decode_shared_snapshot(raw[:-1],raw[:12]) is None
    for index,value in [(0,0),(1,5),(2,3),(3,2),(4,1),(5,0),(6,0x40000),(7,0)]:
        bad=words.copy();bad[index]=value
        data=struct.pack('<9I',*bad)
        assert decode_shared_snapshot(data,data[:12]) is None


def test_capability_explicit_and_legacy_unchanged():
    assert shared_slot_version({}) == 0
    assert shared_slot_version({'shared_save_protocol_version':1}) == 1
    for value in (True,'1',2,None):
        with pytest.raises(ValueError):
            shared_slot_version({'shared_save_protocol_version':value})


@pytest.mark.parametrize('change', ['none','epoch','first_auth','second_auth','session','socket'])
def test_async_snapshot_fences_identity_and_context(monkeypatch, change):
    import asyncio
    import base64
    from types import SimpleNamespace
    from .. import shared_save_protocol as protocol
    auth = bytes(range(16))
    raw = struct.pack('<9I',4,4,0,0,0,0x03001000,3,0x41505331,0)
    ctx = SimpleNamespace(auth=base64.b64encode(auth).decode(),team=0,slot=1,
                          server_seed_name='seed',server=SimpleNamespace(socket=object()),bizhawk_ctx=object())
    calls = 0

    async def read(_connector, requests):
        nonlocal calls
        calls += 1
        if calls == 1:
            assert requests[0][1] == 36
            return [raw, bytes(16) if change == 'first_auth' else auth]
        if change == 'session':
            ctx.slot = 2
        if change == 'socket':
            ctx.server.socket = object()
        return [struct.pack('<3I',5,5,2) if change == 'epoch' else raw[:12],
                bytes(16) if change == 'second_auth' else auth]

    monkeypatch.setattr(protocol, 'read', read)
    result = asyncio.run(protocol.read_shared_snapshot(ctx))
    assert (result is not None) == (change == 'none')


def test_shipping_single_save_lifecycle_and_retry(tmp_path):
    """Mapped host memory; only native I/O/startup calls are substituted."""
    import sys
    if not shutil.which('cc') or not sys.platform.startswith('linux'):
        pytest.skip('Linux mapped-memory host harness required')
    payload = Path(__file__).resolve().parents[1] / 'kirby_ap_payload'
    source = (payload/'shared_save.c').read_text()
    for address, replacement in {
        '0x0800ACD5u':'&save', '0x0800A91Du':'&load', '0x0800AC01u':'&clear',
        '0x080332BDu':'&start', '0x08138F69u':'&enter', '0x0813914Du':'&completion', '0x08150251u':'&stop',
    }.items():
        source = source.replace(address, replacement)
    source = r'''
#define _GNU_SOURCE
#include <stdint.h>
#include <sys/mman.h>
#include <string.h>
#include <stdio.h>
static int16_t save(uint32_t,uint16_t),load(uint32_t,uint16_t);
static void clear(uint32_t),enter(void),stop(void);
static int8_t completion(uint8_t);
static void start(uint8_t,uint8_t,const uint16_t*,const int32_t*,const uint32_t*);
''' + source + r'''
#define CHECK(x) do {if(!(x)){printf("line %d\n",__LINE__);return 1;}}while(0)
static int fails, saves, loads, clears, stops, bad;
static int16_t save(uint32_t kind,uint16_t slot){bad|=kind!=1||slot!=0;saves++;return fails;}
static int16_t load(uint32_t kind,uint16_t slot){bad|=kind!=1||slot!=0;loads++;return 0;}
static void clear(uint32_t kind){bad|=kind!=1;clears++;}
static void stop(void){stops++;}
static void start(uint8_t h,uint8_t l,const uint16_t*r,const int32_t*p,const uint32_t*s){
 (void)r;(void)p;(void)s;bad|=CTX->epoch!=0;
 HUMANS=h;LOCAL=l;FLAGS=0;
 U32(KIRBY+0xCC)=0x03001000;U16(0x03001002)=1;U16(0x03001004)=1;
 U16(0x03001006)=0x6000;U32(0x03001008)=0x0803EE19;
 U16(0x03001010)=0x3000;U16(0x03001012)=0;U8(0x03006000)=0;
}
static int8_t completion(uint8_t slot){bad|=slot!=0;return 100;}
static void enter(void){bad|=U16(0x030024E8)||U16(0x030024EA)||U16(0x030024EC);
 bad|=CTX->epoch!=0||U8(0x0203ACB0)!=100||U8(0x0203ACB1)!=255||U8(0x0203ACB2)!=255;}
static void adventure(void){ap_single_save_enter();ap_shared_start(1,0,0,0,0);}
int main(void){
 CHECK(mmap((void*)0x02000000,0x40000,3,0x32,-1,0)==(void*)0x02000000);
 CHECK(mmap((void*)0x03000000,0x8000,3,0x32,-1,0)==(void*)0x03000000);
 CHECK(mmap((void*)0x08F00000,4096,3,0x32,-1,0)==(void*)0x08F00000);
 memcpy((void*)AUTH,"0123456789abcdef",16);
 U32(0x0203B1FC)=0x12345678;U32(0x0203C200)=0x87654321;
 memset((void*)0x0203B200,0xA5,4096);SAVE_SLOT=2;
 U16(0x030024E8)=0xFF;U16(0x030024EC)=16;
 adventure();CHECK(!bad&&loads==1&&stops==1&&SAVE_SLOT==0&&CTX->epoch==1);
 CHECK(CTX->dirty&&U32(0x0203B200)==0&&U32(0x0203C1FC)==0);
 CHECK(U32(0x0203B1FC)==0x12345678&&U32(0x0203C200)==0x87654321);
 fails=1;ap_shared_poll();CHECK(saves==1&&CTX->dirty&&CTX->retry==60);
 for(unsigned i=0;i<60;i++)ap_shared_poll();CHECK(saves==1&&CTX->dirty);
 fails=0;ap_shared_poll();CHECK(saves==2&&!CTX->dirty);
 U32(0x0203B200)=7;CHECK(ap_shared_update(0,0x30081));ap_shared_poll();
 adventure();CHECK(CTX->epoch==2&&CTX->bits==0x30081&&U32(0x0203B200)==7);
 U32(KIRBY+0xCC)=0;CHECK(!ap_shared_epoch()&&!ap_shared_update(0,1));
 ap_shared_clear(1);CHECK(clears==1&&CTX->loaded_slot==0&&!CTX->epoch);
 adventure();CHECK(CTX->epoch==3);
 ((uint32_t*)AUTH)[3]^=1;CHECK(!ap_shared_epoch());
 adventure();CHECK(CTX->epoch==4&&CTX->bits==0&&U32(0x0203B200)==0);
 SAVE_SLOT=1;CHECK(!ap_shared_epoch());
 ap_shared_start(1,0,0,0,0);CHECK(!CTX->epoch);
 CHECK(!bad);return 0;
}
'''
    cfile, exe = tmp_path/'lifecycle.c', tmp_path/'lifecycle'
    cfile.write_text(source)
    subprocess.run(['cc','-std=gnu99','-w','-I',str(payload),str(cfile),'-o',str(exe)],
                   check=True,capture_output=True)
    result = subprocess.run([str(exe)],capture_output=True,text=True)
    assert result.returncode == 0, result.stdout + result.stderr
