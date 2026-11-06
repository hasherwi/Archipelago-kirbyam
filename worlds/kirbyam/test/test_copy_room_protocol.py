"""Authoritative history and epoch-fenced writes for Copy Room access."""
import asyncio
import base64
from types import SimpleNamespace
from unittest.mock import AsyncMock
import pytest
from .. import copy_room_protocol as protocol
from ..shared_save_protocol import SharedSaveSnapshot


def test_slot_requires_explicit_compatible_capabilities():
    assert protocol.copy_room_slot_version({}) == 0
    assert protocol.copy_room_slot_version({'copy_ability_room_protocol_version':1,
                                          'shared_save_protocol_version':1}) == 1
    for slot in ({'copy_ability_room_protocol_version':True},
                 {'copy_ability_room_protocol_version':2},
                 {'copy_ability_room_protocol_version':1},
                 {'unique_items':['Copy Ability Room Access']}):
        with pytest.raises(ValueError):
            protocol.copy_room_slot_version(slot)


@pytest.mark.parametrize('received,precollected,owned', [(False,False,0),(True,False,1),(False,True,1)])
def test_history_and_precollection_share_ownership_path(monkeypatch, received, precollected, owned):
    auth=bytes(range(16))
    ctx=SimpleNamespace(auth=base64.b64encode(auth).decode(),server=SimpleNamespace(socket=object()),
        slot_data={'copy_ability_room_protocol_version':1,'shared_save_protocol_version':1,
                   'starting_copy_ability_room_access':precollected},
        items_received=[SimpleNamespace(item=3860500)] if received else [],bizhawk_ctx=object())
    monkeypatch.setattr(protocol,'read_shared_snapshot',AsyncMock(return_value=SharedSaveSnapshot(7,2,0,False)))
    write=AsyncMock(return_value=True)
    monkeypatch.setattr(protocol.shared_io.bizhawk,'guarded_write',write)
    assert asyncio.run(protocol.sync_copy_room_ownership(ctx,lambda _: True))
    args=write.call_args.args
    assert args[1] == [(0x0203B164,owned.to_bytes(4,'little'),'System Bus'),
                       (0x0203B160,(7).to_bytes(4,'little'),'System Bus')]
    assert args[2] == [(0x0203B13C,(7).to_bytes(4,'little'),'System Bus'),
                       (0x0203B144,(2).to_bytes(4,'little'),'System Bus'),
                       (0xF00000,auth,'ROM')]


@pytest.mark.parametrize('change',['inactive','socket','auth','slot','history','not_ready'])
def test_never_write_after_snapshot_race(monkeypatch,change):
    ctx=SimpleNamespace(auth=base64.b64encode(bytes(16)).decode(),server=SimpleNamespace(socket=object()),
        slot_data={'copy_ability_room_protocol_version':1,'shared_save_protocol_version':1},
        items_received=[],bizhawk_ctx=object())
    ready=True
    async def snapshot(_ctx):
        nonlocal ready
        if change=='inactive': return None
        if change=='socket':ctx.server.socket=object()
        if change=='auth':ctx.auth='changed'
        if change=='slot':ctx.slot_data=dict(ctx.slot_data)
        if change=='history':ctx.items_received=[SimpleNamespace(item=3860500)]
        if change=='not_ready':ready=False
        return SharedSaveSnapshot(7,2,0,False)
    write=AsyncMock(return_value=True)
    monkeypatch.setattr(protocol,'read_shared_snapshot',snapshot)
    monkeypatch.setattr(protocol.shared_io.bizhawk,'guarded_write',write)
    assert not asyncio.run(protocol.sync_copy_room_ownership(ctx,lambda _: ready))
    write.assert_not_called()


@pytest.mark.asyncio
async def test_reset_before_copy_snapshot_cannot_adopt_new_epoch(monkeypatch):
    """A resumed Copy sync cannot escape the epoch captured by its watcher."""
    io = protocol.shared_io
    auth = bytes(range(16))
    ctx = SimpleNamespace(auth=base64.b64encode(auth).decode(), team=0, slot=1,
        server=SimpleNamespace(socket=object()), bizhawk_ctx=object(),
        slot_data={'copy_ability_room_protocol_version':1,'shared_save_protocol_version':1},
        items_received=[SimpleNamespace(item=3860500)])
    writes = []
    monkeypatch.setattr(protocol, 'read_shared_snapshot',
                        AsyncMock(return_value=SharedSaveSnapshot(2,0,0,False)))
    async def guarded_write(connector, offered, guards):
        if guards[0][1][:4] != (2).to_bytes(4, 'little'):
            return False
        writes.extend(offered)
        return True
    monkeypatch.setattr(io.bizhawk, 'guarded_write', guarded_write)
    monkeypatch.setattr(io.bizhawk, 'guarded_read', AsyncMock(return_value=None))
    with io.shared_watcher(ctx, SharedSaveSnapshot(1,0,0,False)):
        with pytest.raises(io.SharedContextChanged):
            await protocol.sync_copy_room_ownership(ctx, lambda _: True)
    assert not writes
