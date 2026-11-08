"""Three-file ownership protocol rejects stale history, native context and ROMs."""
import asyncio
import base64
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from .. import copy_room_protocol as protocol


def _ctx(items=(), precollected=False):
    return SimpleNamespace(auth=base64.b64encode(bytes(range(16))).decode(),
                           server=SimpleNamespace(socket=object()), bizhawk_ctx=object(),
                           slot_data={"copy_ability_room_protocol_version": 2,
                                      "starting_copy_ability_room_access": precollected},
                           items_received=[SimpleNamespace(item=item) for item in items])


def _raw(slot=0, epoch=7, owned=0):
    return b"".join(word.to_bytes(4, "little") for word in
                    (epoch, epoch, slot, 0, slot, 0x03001000, owned, 0x43504332, 0))


def test_protocol_requires_native_layout_and_explicit_capability():
    assert protocol.copy_room_slot_version({}) == 0
    assert protocol.copy_room_slot_version({"copy_ability_room_protocol_version": 2}) == 2
    for slot in ({"copy_ability_room_protocol_version": True}, {"copy_ability_room_protocol_version": 1},
                 {"copy_ability_room_protocol_version": 3}, {"unique_items": ["Copy Ability Room Access"]},
                 {"copy_ability_room_protocol_version": 2, "shared_save_protocol_version": 1}):
        with pytest.raises(ValueError):
            protocol.copy_room_slot_version(slot)


@pytest.mark.parametrize("slot", [0, 1, 2])
@pytest.mark.parametrize("received,precollected,owned", [(False, False, 0), (True, False, 1), (False, True, 1)])
def test_complete_history_and_precollection_in_each_native_file(monkeypatch, slot, received, precollected, owned):
    ctx = _ctx([3860500] if received else [], precollected)
    raw = _raw(slot)
    auth = base64.b64decode(ctx.auth)
    monkeypatch.setattr(protocol.bizhawk, "read", AsyncMock(side_effect=[[raw, auth], [raw[:12], auth]]))
    write = AsyncMock(return_value=True)
    monkeypatch.setattr(protocol.bizhawk, "guarded_write", write)
    assert asyncio.run(protocol.sync_copy_room_ownership(ctx, lambda _: True)) == bool(owned)
    if not owned:
        write.assert_not_called()
        return
    assert write.call_args.args[1] == [(0x0203B164, owned.to_bytes(4, "little"), "System Bus"),
                                       (0x0203B160, (7).to_bytes(4, "little"), "System Bus")]
    assert write.call_args.args[2] == [(0x0203B13C, raw[:12], "System Bus"), (0xF00000, auth, "ROM")]


@pytest.mark.parametrize("change", ["epoch", "native_slot", "socket", "auth", "slot", "history", "not_ready",
                                    "rom_auth", "short", "inactive", "task", "invalid_slot"])
def test_no_write_after_snapshot_race_or_invalid_context(monkeypatch, change):
    ctx = _ctx([3860500])
    ready = True
    raw = _raw()
    auth = base64.b64decode(ctx.auth)
    calls = 0

    async def read(_ctx, _reads):
        nonlocal ready, calls
        calls += 1
        if calls == 1:
            altered = {"inactive": _raw(epoch=0), "task": raw[:20] + bytes(4) + raw[24:],
                       "invalid_slot": _raw(slot=3)}
            return [altered.get(change, raw), auth]
        if change == "socket":
            ctx.server.socket = object()
        if change == "auth":
            ctx.auth = "changed"
        if change == "slot":
            ctx.slot_data = dict(ctx.slot_data)
        if change == "history":
            ctx.items_received = []
        if change == "not_ready":
            ready = False
        if change == "epoch":
            return [_raw(epoch=8)[:12], auth]
        if change == "native_slot":
            return [_raw(slot=1)[:12], auth]
        if change == "rom_auth":
            return [raw[:12], bytes(16)]
        if change == "short":
            return [raw[:8], auth]
        return [raw[:12], auth]
    monkeypatch.setattr(protocol.bizhawk, "read", read)
    write = AsyncMock(return_value=True)
    monkeypatch.setattr(protocol.bizhawk, "guarded_write", write)
    assert not asyncio.run(protocol.sync_copy_room_ownership(ctx, lambda _: ready))
    write.assert_not_called()


def test_disconnect_or_incomplete_replay_never_revokes_offline_ownership(monkeypatch):
    read = AsyncMock()
    monkeypatch.setattr(protocol.bizhawk, "read", read)
    assert not asyncio.run(protocol.sync_copy_room_ownership(_ctx(), lambda _: False))
    read.assert_not_called()


@pytest.mark.parametrize("slot", [0, 1, 2])
@pytest.mark.parametrize("received", [False, True])
def test_saved_grant_is_permanent_across_complete_history_replay(monkeypatch, slot, received):
    ctx = _ctx([3860500] if received else [])
    raw = _raw(slot, owned=1)
    auth = base64.b64decode(ctx.auth)
    read = AsyncMock(side_effect=[[raw, auth], [raw[:12], auth]])
    write = AsyncMock()
    monkeypatch.setattr(protocol.bizhawk, "read", read)
    monkeypatch.setattr(protocol.bizhawk, "guarded_write", write)
    assert asyncio.run(protocol.sync_copy_room_ownership(ctx, lambda _: True)) == received
    write.assert_not_called()
    if not received:
        read.assert_not_called()  # Empty history is not an instruction to clear saved ownership.
