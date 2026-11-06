"""Async reset/ROM/session interleavings execute the shipping watcher fence."""
import asyncio
import base64
import struct
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from .. import shared_watcher as io
from ..shared_save_protocol import SharedSaveSnapshot


@pytest.mark.asyncio
@pytest.mark.parametrize('change', ['epoch', 'inactive', 'rom', 'socket'])
@pytest.mark.parametrize('operation', ['read', 'write', 'guarded_write', 'send'])
async def test_reset_during_suspended_operation_rejects_stale_tick(monkeypatch, change, operation):
    auth = bytes(range(16))
    ctx = SimpleNamespace(auth=base64.b64encode(auth).decode(),team=0,slot=1,
                          server_seed_name='seed',server=SimpleNamespace(socket=object()),
                          bizhawk_ctx=object(),send_msgs=AsyncMock())
    state = {'epoch':1,'auth':auth}
    entered, resume = asyncio.Event(), asyncio.Event()
    writes = []

    def matches(guards):
        return (guards[0] == (0x0203B13C,struct.pack('<3I',state['epoch'],state['epoch'],0),'System Bus')
                and guards[1] == (0xF00000,state['auth'],'ROM'))

    async def guarded_read(_connector, reads, guards):
        # First response was produced before reset, delivered after reset.
        if not entered.is_set():
            result = [b'old' for _ in reads] if matches(guards) else None
            entered.set()
            await resume.wait()
            return result
        return [b'current' for _ in reads] if matches(guards) else None

    async def guarded_write(_connector, offered, guards):
        entered.set()
        await resume.wait()
        if not matches(guards):
            return False
        writes.extend(offered)
        return True

    monkeypatch.setattr(io.bizhawk,'guarded_read',guarded_read)
    monkeypatch.setattr(io.bizhawk,'guarded_write',guarded_write)
    with io.shared_watcher(ctx,SharedSaveSnapshot(1,0,0,False)):
        if operation == 'read': coro=io.read(ctx.bizhawk_ctx,[(1,3,'RAM')])
        elif operation == 'write': coro=io.write(ctx.bizhawk_ctx,[(1,b'new','RAM')])
        elif operation == 'guarded_write': coro=io.guarded_write(ctx.bizhawk_ctx,[(1,b'new','RAM')],[])
        else: coro=io.send_msgs(ctx,[{'cmd':'LocationChecks','locations':[1]}])
        task=asyncio.create_task(coro)
        await entered.wait()
        if change == 'epoch': state['epoch']=2
        elif change == 'inactive': state['epoch']=0
        elif change == 'rom': state['auth']=bytes(16)
        else: ctx.server.socket=object()
        resume.set()
        with pytest.raises(io.SharedContextChanged):
            await task
    ctx.send_msgs.assert_not_awaited()
    if change != 'socket':
        assert not writes
    assert io._active.get() is None


@pytest.mark.asyncio
async def test_guarded_native_failure_and_task_local_cleanup(monkeypatch):
    ctx=SimpleNamespace(auth=base64.b64encode(bytes(16)).decode(),team=0,slot=1,
                        server=SimpleNamespace(socket=object()),bizhawk_ctx=object())
    monkeypatch.setattr(io.bizhawk,'guarded_read',AsyncMock(return_value=[]))
    bridge=AsyncMock(return_value=False)
    monkeypatch.setattr(io.bizhawk,'guarded_write',bridge)
    native=[(42,b'owned','RAM')]
    with io.shared_watcher(ctx,SharedSaveSnapshot(3,0,0,False)):
        assert not await io.guarded_write(ctx.bizhawk_ctx,[(7,b'x','RAM')],native)
        assert bridge.call_args.args[2][-1] == native[0]
    assert io._active.get() is None


@pytest.mark.asyncio
async def test_actual_watcher_cancels_receipt_after_epoch_changes(monkeypatch):
    from ..client import KirbyAmClient
    from .. import client as module
    ctx=SimpleNamespace(auth=base64.b64encode(bytes(16)).decode(),team=0,slot=1,
                        server=SimpleNamespace(socket=object()),bizhawk_ctx=object(),
                        slot_data={'shared_save_protocol_version':1})
    client=KirbyAmClient();client.initialize_client()
    client._ram_state_loaded=True
    monkeypatch.setattr(client,'_server_session_ready',lambda ctx:True)
    monkeypatch.setattr(client,'_health_protocol_ready',AsyncMock(return_value=True))
    monkeypatch.setattr(module,'read_shared_snapshot',AsyncMock(return_value=SharedSaveSnapshot(1,0,0,False)))
    state={'epoch':1};writes=[];finished=[]
    async def read(connector, requests, guards):
        return [b'old' for _ in requests] if guards[0][1][:4]==state['epoch'].to_bytes(4,'little') else None
    async def write(connector, offered, guards):
        if guards[0][1][:4]!=state['epoch'].to_bytes(4,'little'):return False
        writes.extend(offered);return True
    async def active(ctx):
        await io.read(ctx.bizhawk_ctx,[(10,3,'RAM')])
        state['epoch']=2  # Reset/re-entry during the longer watcher tick.
        await io.write(ctx.bizhawk_ctx,[(20,b'old receipt','RAM')])
        finished.append(True)
    monkeypatch.setattr(io.bizhawk,'guarded_read',read)
    monkeypatch.setattr(io.bizhawk,'guarded_write',write)
    monkeypatch.setattr(client,'_watch_active_game',active)
    await client.game_watcher(ctx)
    assert not writes and not finished
    assert client._watcher_requires_bizhawk_resync and not client._ram_state_loaded
    assert io._active.get() is None
