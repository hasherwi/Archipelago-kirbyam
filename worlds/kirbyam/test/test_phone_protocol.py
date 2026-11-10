"""Phone grants preserve the native-file and complete-history trust boundary."""
import asyncio
import base64
from types import SimpleNamespace
from typing import Any, Sequence, cast
from unittest.mock import AsyncMock

import pytest
from worlds import _bizhawk as bizhawk
from .. import phone_protocol as protocol


def _ctx(items: Sequence[int] = (), precollected: bool = False) -> SimpleNamespace:
    return SimpleNamespace(auth=base64.b64encode(bytes(range(16))).decode(),
                           server=SimpleNamespace(socket=object()), bizhawk_ctx=object(),
                           slot_data={"copy_ability_room_protocol_version": 2, "phone_protocol_version": 1,
                                      "starting_phone_access": precollected},
                           items_received=[SimpleNamespace(item=item) for item in items])


def _words(*values: int) -> bytes:
    return b"".join(value.to_bytes(4, "little") for value in values)


def _reads(ctx: SimpleNamespace, slot: int = 0, owned: int = 0) -> tuple[list[bytes], list[bytes]]:
    native = _words(7, 7, slot, 0, slot, 0x03001000, 0, 0x43504332, 0)
    phone = _words(7, slot, owned, protocol.PHONE_COOKIE)
    values = [native, phone, base64.b64decode(ctx.auth), protocol.PHONE_ENABLED_CONFIG]
    return values, [native[:12], *values[1:]]


def test_capability_and_native_save_layout_are_required() -> None:
    assert protocol.phone_slot_version({}) == 0
    assert protocol.phone_slot_version(_ctx().slot_data) == 1
    for slot in ({"phone_protocol_version": True}, {"phone_protocol_version": 2},
                 {"phone_protocol_version": 1}, {"unique_items": ["Phone a Friend"]},
                 {**_ctx().slot_data, "shared_save_protocol_version": 1}):
        with pytest.raises(ValueError):
            protocol.phone_slot_version(slot)


@pytest.mark.parametrize("slot", [0, 1, 2])
@pytest.mark.parametrize("precollected", [False, True])
@pytest.mark.parametrize("saved", [0, 1])
def test_grant_only_transport_in_all_native_files(
        monkeypatch: pytest.MonkeyPatch, slot: int, precollected: bool, saved: int) -> None:
    ctx = _ctx([] if precollected else [protocol.PHONE_ITEM_ID], precollected)
    raw, fence = _reads(ctx, slot, saved)
    monkeypatch.setattr(bizhawk, "read", AsyncMock(side_effect=[raw, fence]))
    write = AsyncMock(return_value=True)
    monkeypatch.setattr(bizhawk, "guarded_write", write)
    assert asyncio.run(protocol.sync_phone_ownership(ctx, lambda _: True))
    if saved:
        write.assert_not_called()
    else:
        assert write.call_args is not None
        assert write.call_args.args[1] == [
            (protocol.PHONE_REQUEST_ADDRESS + 4, _words(1), "System Bus"),
            (protocol.PHONE_REQUEST_ADDRESS, _words(7), "System Bus"),
        ]
        assert len(write.call_args.args[2]) == 4


@pytest.mark.parametrize("mutation", ["epoch", "slot", "context", "cookie", "owned", "rom_auth",
                                      "disabled", "marker", "socket", "auth", "history", "incomplete",
                                      "short", "inactive", "slot_object", "phone_race"])
def test_stale_or_mismatched_grants_fail_closed(monkeypatch: pytest.MonkeyPatch, mutation: str) -> None:
    ctx = _ctx([protocol.PHONE_ITEM_ID])
    raw, fence = _reads(ctx)
    ready = True
    calls = 0

    async def read(_ctx: object, _reads: object) -> list[bytes]:
        nonlocal calls, ready
        calls += 1
        if calls == 1:
            return raw
        phone_values = {
            "slot": _words(7, 1, 0, protocol.PHONE_COOKIE), "cookie": _words(7, 0, 0, 0),
            "owned": _words(7, 0, 2, protocol.PHONE_COOKIE), "short": b"",
        }
        if mutation in phone_values:
            raw[1] = fence[1] = phone_values[mutation]
        if mutation == "context":
            raw[0] = _words(7, 7, 0, 0, 0, 0, 0, 0x43504332, 0)
        if mutation == "inactive":
            raw[0] = _words(0, 0, 0, 0, 0, 0x03001000, 0, 0x43504332, 0)
            fence[0] = raw[0][:12]
        fence_changes = {
            "epoch": (0, _words(8, 8, 0)), "rom_auth": (2, bytes(16)),
            "disabled": (3, protocol.PHONE_MARKER + bytes(4)), "marker": (3, bytes(12)),
            "phone_race": (1, _words(8, 0, 0, protocol.PHONE_COOKIE)),
        }
        if mutation in fence_changes:
            index, value = fence_changes[mutation]
            fence[index] = value
        context_changes = {
            "socket": lambda: setattr(ctx.server, "socket", object()),
            "auth": lambda: setattr(ctx, "auth", "changed"),
            "history": lambda: setattr(ctx, "items_received", []),
            "slot_object": lambda: setattr(ctx, "slot_data", dict(ctx.slot_data)),
        }
        context_changes.get(mutation, lambda: None)()
        ready = mutation != "incomplete"
        return fence
    monkeypatch.setattr(bizhawk, "read", read)
    write = AsyncMock()
    monkeypatch.setattr(bizhawk, "guarded_write", write)
    assert not asyncio.run(protocol.sync_phone_ownership(ctx, lambda _: ready))
    write.assert_not_called()


def test_empty_or_incomplete_history_never_revokes(monkeypatch: pytest.MonkeyPatch) -> None:
    read = AsyncMock()
    monkeypatch.setattr(bizhawk, "read", read)
    assert not asyncio.run(protocol.sync_phone_ownership(_ctx(), lambda _: True))
    assert not asyncio.run(protocol.sync_phone_ownership(_ctx([protocol.PHONE_ITEM_ID]), lambda _: False))
    read.assert_not_called()


@pytest.mark.parametrize("config", [bytes(12), bytes(range(12)), protocol.PHONE_MARKER + bytes(4)])
def test_legacy_and_disabled_rom_pairing(config: bytes) -> None:
    assert protocol.validate_phone_pairing({}, config) == 0
    with pytest.raises(ValueError):
        protocol.validate_phone_pairing(_ctx().slot_data, config)


def test_enabled_and_malformed_rom_pairing() -> None:
    assert protocol.validate_phone_pairing(_ctx().slot_data, protocol.PHONE_ENABLED_CONFIG) == 1
    for config in (b"", bytes(11), protocol.PHONE_ENABLED_CONFIG,
                   b"APPHN02\0" + bytes(4), protocol.PHONE_MARKER + _words(2)):
        with pytest.raises(ValueError):
            protocol.validate_phone_pairing({}, config)


def test_watcher_rechecks_reverse_phone_pairing(monkeypatch: pytest.MonkeyPatch) -> None:
    from ..client import KirbyAmClient
    client = KirbyAmClient()
    client.initialize_client()
    ctx = SimpleNamespace(slot_data={}, bizhawk_ctx=object(), items_received=[],
                          server=SimpleNamespace(socket=SimpleNamespace(closed=False)))
    read = AsyncMock(return_value=[bytes(12)])
    monkeypatch.setattr(bizhawk, "read", read)
    assert asyncio.run(client._health_protocol_ready(ctx, require_identity=False))
    read.return_value = [protocol.PHONE_ENABLED_CONFIG]
    assert not asyncio.run(client._health_protocol_ready(ctx, require_identity=False))
    read.return_value = [protocol.PHONE_MARKER + bytes(4)]
    assert asyncio.run(client._health_protocol_ready(ctx, require_identity=False))
    assert read.call_args is not None
    assert read.call_args.args[1] == [(protocol.PHONE_CONFIG_BUS_ADDRESS, 12, "System Bus")]


@pytest.mark.asyncio
async def test_reverse_pairing_stops_watcher_side_effects(monkeypatch: pytest.MonkeyPatch) -> None:
    from ..client import KirbyAmClient
    from .test_vitality_protocol import _identity
    client = KirbyAmClient()
    client.initialize_client()
    ctx = cast(Any, SimpleNamespace(slot_data={}, bizhawk_ctx=object(), items_received=[],
                                    server=SimpleNamespace(socket=SimpleNamespace(closed=False)),
                                    team=0, slot=1, server_seed_name="Phone pairing regression", send_msgs=AsyncMock()))
    memory = _identity(client, ctx, 2, 6, 10)
    memory[protocol.PHONE_CONFIG_BUS_ADDRESS, "System Bus"] = protocol.PHONE_ENABLED_CONFIG

    async def read(_ctx: object, requests: list[tuple[int, int, str]]) -> list[bytes]:
        return [memory[address, domain] for address, _, domain in requests]

    monkeypatch.setattr(bizhawk, "read", read)
    write, guarded, death = AsyncMock(), AsyncMock(), AsyncMock()
    monkeypatch.setattr(bizhawk, "write", write)
    monkeypatch.setattr(bizhawk, "guarded_write", guarded)
    monkeypatch.setattr(client, "_sync_death_link_setting", death)
    await client.game_watcher(ctx)
    write.assert_not_called()
    guarded.assert_not_called()
    death.assert_not_called()
    ctx.send_msgs.assert_not_called()
