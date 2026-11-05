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
    words = [4,4,2,1,2,0x03001000,0x3ffff,0x41505331,0]
    raw = struct.pack('<9I', *words)
    snapshot = decode_shared_snapshot(raw,raw[:12])
    assert snapshot is not None and (snapshot.epoch,snapshot.slot,snapshot.bits,snapshot.dirty)==(4,2,0x3ffff,True)
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
    raw = struct.pack('<9I',4,4,2,0,2,0x03001000,3,0x41505331,0)
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
