"""Phone grants preserve the native-file and complete-history trust boundary."""
import asyncio
import base64
from types import SimpleNamespace
from typing import Any, Sequence, cast
from unittest.mock import AsyncMock

import pytest
from worlds import _bizhawk as bizhawk
from .. import phone_protocol as protocol
from ..copy_room_protocol import COPY_ROOM_CONTEXT_ADDRESS


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


@pytest.mark.parametrize("version", [None, False, True, -1, 2, "1", 1.0, [], {}])
def test_malformed_capability_never_reads_memory(monkeypatch: pytest.MonkeyPatch, version: Any) -> None:
    ctx = _ctx([protocol.PHONE_ITEM_ID])
    ctx.slot_data["phone_protocol_version"] = version
    read = AsyncMock()
    monkeypatch.setattr(bizhawk, "read", read)
    with pytest.raises(ValueError):
        asyncio.run(protocol.sync_phone_ownership(ctx, lambda _: True))
    read.assert_not_called()


@pytest.mark.parametrize("owned", [None, 0, 1, "true", [], {}])
def test_malformed_starting_ownership_never_reads_memory(monkeypatch: pytest.MonkeyPatch, owned: Any) -> None:
    ctx = _ctx([protocol.PHONE_ITEM_ID])
    ctx.slot_data["starting_phone_access"] = owned
    read = AsyncMock()
    monkeypatch.setattr(bizhawk, "read", read)
    with pytest.raises(ValueError):
        asyncio.run(protocol.sync_phone_ownership(ctx, lambda _: True))
    read.assert_not_called()


@pytest.mark.parametrize("field", ["server_seed_name", "team", "slot", "server", "bizhawk_ctx"])
@pytest.mark.parametrize("pending_read", [1, 2])
def test_session_replacement_during_either_read_never_grants(
        monkeypatch: pytest.MonkeyPatch, field: str, pending_read: int) -> None:
    ctx = _ctx([protocol.PHONE_ITEM_ID])
    raw, fence = _reads(ctx)
    calls = 0

    async def read(_ctx: object, _requests: object) -> list[bytes]:
        nonlocal calls
        calls += 1
        if calls == pending_read:
            setattr(ctx, field, object())
        return raw if calls == 1 else fence

    monkeypatch.setattr(bizhawk, "read", read)
    write = AsyncMock()
    monkeypatch.setattr(bizhawk, "guarded_write", write)
    assert not asyncio.run(protocol.sync_phone_ownership(ctx, lambda _: True))
    write.assert_not_called()


@pytest.mark.parametrize("key,value", [
    ("phone_protocol_version", 0), ("phone_protocol_version", True),
    ("copy_ability_room_protocol_version", 0), ("shared_save_protocol_version", 1),
    ("starting_phone_access", False), ("starting_phone_access", 1),
])
@pytest.mark.parametrize("pending_read", [1, 2])
def test_in_place_slot_change_during_read_never_grants(
        monkeypatch: pytest.MonkeyPatch, key: str, value: Any, pending_read: int) -> None:
    ctx = _ctx(precollected=True)
    raw, fence = _reads(ctx)
    calls = 0

    async def read(_ctx: object, _requests: object) -> list[bytes]:
        nonlocal calls
        calls += 1
        if calls == pending_read:
            ctx.slot_data[key] = value
        return raw if calls == 1 else fence

    monkeypatch.setattr(bizhawk, "read", read)
    write = AsyncMock(return_value=True)
    monkeypatch.setattr(bizhawk, "guarded_write", write)
    assert not asyncio.run(protocol.sync_phone_ownership(ctx, lambda _: True))
    write.assert_not_called()


@pytest.mark.parametrize("read_boundary", [1, 2])
@pytest.mark.parametrize("saved_owned", [0, 1])
@pytest.mark.parametrize("key", ["starting_phone_access", "shared_save_protocol_version"])
def test_absent_slot_field_becoming_none_during_read_never_grants(
        monkeypatch: pytest.MonkeyPatch, read_boundary: int, saved_owned: int, key: str) -> None:
    ctx = _ctx([protocol.PHONE_ITEM_ID])
    ctx.slot_data.pop(key, None)
    raw, fence = _reads(ctx, owned=saved_owned)
    calls = 0

    async def read(_ctx: object, _requests: object) -> list[bytes]:
        nonlocal calls
        calls += 1
        if calls == read_boundary:
            ctx.slot_data[key] = None
        return raw if calls == 1 else fence

    monkeypatch.setattr(bizhawk, "read", read)
    write = AsyncMock(return_value=True)
    monkeypatch.setattr(bizhawk, "guarded_write", write)
    assert not asyncio.run(protocol.sync_phone_ownership(ctx, lambda _: True))
    assert calls == 2
    write.assert_not_called()


@pytest.mark.parametrize("saved_owned", [0, 1])
def test_absent_optional_slot_fields_allow_receipt_grants(
        monkeypatch: pytest.MonkeyPatch, saved_owned: int) -> None:
    ctx = _ctx([protocol.PHONE_ITEM_ID])
    del ctx.slot_data["starting_phone_access"]
    raw, fence = _reads(ctx, owned=saved_owned)
    monkeypatch.setattr(bizhawk, "read", AsyncMock(side_effect=[raw, fence]))
    write = AsyncMock(return_value=True)
    monkeypatch.setattr(bizhawk, "guarded_write", write)
    assert asyncio.run(protocol.sync_phone_ownership(ctx, lambda _: True))
    assert write.await_count == 1 - saved_owned


def test_failed_guard_can_retry_only_with_fresh_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ctx([protocol.PHONE_ITEM_ID])
    raw, fence = _reads(ctx)
    next_raw, next_fence = _reads(ctx, slot=2)
    read = AsyncMock(side_effect=[raw, fence, next_raw, next_fence])
    write = AsyncMock(side_effect=[False, True])
    monkeypatch.setattr(bizhawk, "read", read)
    monkeypatch.setattr(bizhawk, "guarded_write", write)
    assert not asyncio.run(protocol.sync_phone_ownership(ctx, lambda _: True))
    assert asyncio.run(protocol.sync_phone_ownership(ctx, lambda _: True))
    assert read.await_count == 4
    assert write.await_count == 2
    assert write.call_args is not None
    assert write.call_args.args[2] == [
        (COPY_ROOM_CONTEXT_ADDRESS, next_fence[0], "System Bus"),
        (protocol.PHONE_CONTEXT_ADDRESS, next_fence[1], "System Bus"),
        (0xF00000, base64.b64decode(ctx.auth), "ROM"),
        (protocol.PHONE_CONFIG_OFFSET, protocol.PHONE_ENABLED_CONFIG, "ROM"),
    ]


@pytest.mark.asyncio
async def test_disconnect_during_pairing_read_does_not_poison_reconnected_session(
        monkeypatch: pytest.MonkeyPatch) -> None:
    from ..client import KirbyAmClient
    client = KirbyAmClient()
    client.initialize_client()
    ctx = SimpleNamespace(slot_data={}, bizhawk_ctx=object(), items_received=[],
                          server=SimpleNamespace(socket=SimpleNamespace(closed=False)))

    async def disconnect(_ctx: object, _requests: object) -> list[bytes]:
        ctx.server = None
        return [protocol.PHONE_ENABLED_CONFIG]

    monkeypatch.setattr(bizhawk, "read", disconnect)
    assert not await client._health_protocol_ready(ctx, require_identity=False)
    assert not getattr(client, "_last_health_protocol_error", None)
    ctx.server = SimpleNamespace(socket=SimpleNamespace(closed=False))
    monkeypatch.setattr(bizhawk, "read", AsyncMock(return_value=[protocol.PHONE_MARKER + bytes(4)]))
    assert await client._health_protocol_ready(ctx, require_identity=False)
