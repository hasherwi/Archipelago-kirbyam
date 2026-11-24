"""Late Hub receipts must install ownership before native item effects."""
import base64
import json
from pathlib import Path
from typing import Any, Callable
from unittest.mock import AsyncMock, Mock, patch

import pytest

from NetUtils import NetworkItem
from worlds._bizhawk import RequestFailedError
from ..client import COPY_ROOM_CONTEXT_ADDRESS, KirbyAmClient, _MAILBOX_ACK_TIMEOUT_FRAMES
from ..data import data
from ..receipts import ReceiptJournal, receipt_key


class Bridge:
    """Ordered requests; connector errors do not abort the remaining batch."""

    def __init__(self) -> None:
        self.ram: dict[int, bytes] = {}
        self.offers: list[tuple[int, int]] = []
        self.mask_error_prefix: int | None = None
        self.lose_mask_reply = False
        self.after_mask: Callable[[], None] | None = None
        self.before_guard: Callable[[], None] | None = None
        self.after_offer: Callable[[], None] | None = None
        self.lose_offer_reply = False
        self.addresses = data.transport_ram_addresses

    def value(self, name: str) -> int:
        return int.from_bytes(self.ram.get(self.addresses[name], bytes(4)), 'little')

    async def send(self, raw: str) -> str:
        responses: list[dict[str, Any]] = []
        offered = False
        for req in json.loads(raw):
            addr = req['address']
            if req['type'] == 'READ':
                initial = int(addr in [self.addresses[k] for k in
                                       ('debug_item_counter', 'frame_counter', 'hook_heartbeat')])
                value = self.ram.get(addr, initial.to_bytes(req['size'], 'little'))
                responses.append({'type': 'READ_RESPONSE', 'value': base64.b64encode(value).decode()})
            elif req['type'] == 'GUARD':
                if self.before_guard:
                    callback, self.before_guard = self.before_guard, None
                    callback()
                expected = base64.b64decode(req['expected_data'])
                valid = self.ram.get(addr, bytes(len(expected))) == expected
                responses.append({'type': 'GUARD_RESPONSE', 'value': valid})
                if not valid:
                    break
            elif req['type'] == 'WRITE':
                value = base64.b64decode(req['value'])
                if addr == self.addresses['hub_connection_item_mask'] and self.mask_error_prefix is not None:
                    n = self.mask_error_prefix
                    self.ram[addr] = value[:n] + self.ram.get(addr, bytes(4))[n:]
                    responses.append({'type': 'ERROR', 'err': 'controlled partial mask write'})
                    continue
                self.ram[addr] = value
                responses.append({'type': 'WRITE_RESPONSE'})
                if addr == self.addresses['hub_connection_item_mask']:
                    if self.after_mask:
                        self.after_mask()
                    if self.lose_mask_reply:
                        raise RequestFailedError('controlled lost mask acknowledgement')
                if addr == self.addresses['incoming_item_flag'] and int.from_bytes(value, 'little') == 1:
                    self.offers.append((self.value('incoming_item_id'), self.value('hub_connection_item_mask')))
                    offered = True
                    if self.after_offer:
                        self.after_offer()
        if offered and self.lose_offer_reply:
            raise RequestFailedError('controlled lost offer acknowledgement')
        return json.dumps(responses)


async def setup_client(ctx: Any) -> tuple[KirbyAmClient, Bridge]:
    client = KirbyAmClient()
    client.initialize_client()
    client._notification_settings_loaded = True
    client._delivered_item_index = 1
    ctx.items_received = [Mock(item=3860405, player=1)]
    client.on_package(ctx, 'ReceivedItems', {'index': 0})
    bridge = Bridge()
    ctx.bizhawk_ctx._send_message.side_effect = bridge.send
    await client._sync_hub_connection_item_ownership(ctx)
    # The watcher can receive this item during any intervening awaited poll.
    ctx.items_received.append(Mock(item=3860409, player=1))
    client.on_package(ctx, 'ReceivedItems', {'index': 1})
    return client, bridge


@pytest.mark.asyncio
async def test_late_hub_receipt_installs_ownership_before_native_offer(mock_bizhawk_context: Any) -> None:
    ctx = mock_bizhawk_context
    client, bridge = await setup_client(ctx)
    with patch.object(client, '_prepare_receipts', return_value=True):
        await client._deliver_items(ctx)
    assert bridge.offers == [(3860409, 0x220)]
    assert client._delivery_pending is True


@pytest.mark.asyncio
@pytest.mark.parametrize('prefix', [0, 2, 4])
async def test_partial_mask_write_error_never_offers_hub_item(mock_bizhawk_context: Any, prefix: int) -> None:
    ctx = mock_bizhawk_context
    client, bridge = await setup_client(ctx)
    bridge.mask_error_prefix = prefix
    with (
        patch.object(client, '_prepare_receipts', return_value=True),
        pytest.raises(Exception, match='Connector script returned errors|controlled partial mask write'),
    ):
        await client._deliver_items(ctx)
    assert bridge.offers == []
    assert client._delivery_pending is False


@pytest.mark.asyncio
async def test_lost_mask_ack_never_offers_hub_item(mock_bizhawk_context: Any) -> None:
    ctx = mock_bizhawk_context
    client, bridge = await setup_client(ctx)
    bridge.lose_mask_reply = True
    with patch.object(client, '_prepare_receipts', return_value=True), pytest.raises(RequestFailedError):
        await client._deliver_items(ctx)
    assert bridge.offers == []


@pytest.mark.asyncio
@pytest.mark.parametrize('change', ['socket', 'streams', 'auth', 'receipt'])
async def test_reconnect_during_ownership_ack_defers_hub_offer(mock_bizhawk_context: Any, change: str) -> None:
    ctx = mock_bizhawk_context
    client, bridge = await setup_client(ctx)

    def invalidate() -> None:
        if change == 'socket':
            ctx.server.socket = Mock(closed=False)
            client.on_package(ctx, 'ReceivedItems', {'index': 0})
        elif change == 'streams':
            ctx.bizhawk_ctx.streams = object()
        elif change == 'auth':
            ctx.auth = 'different-auth'
        else:
            ctx.items_received[1] = Mock(item=3860001, player=1)
    bridge.after_mask = invalidate
    with patch.object(client, '_prepare_receipts', return_value=True):
        await client._deliver_items(ctx)
    assert bridge.offers == []
    assert client._delivery_pending is False


@pytest.mark.asyncio
@pytest.mark.parametrize('field,value', [('hub_connection_item_mask', 0x20), ('incoming_item_flag', 1)])
async def test_changed_ownership_or_busy_mailbox_guard_defers_offer(
    mock_bizhawk_context: Any, field: str, value: int,
) -> None:
    ctx = mock_bizhawk_context
    client, bridge = await setup_client(ctx)
    bridge.before_guard = lambda: bridge.ram.__setitem__(bridge.addresses[field], value.to_bytes(4, 'little'))
    with patch.object(client, '_prepare_receipts', return_value=True):
        await client._deliver_items(ctx)
    assert bridge.offers == []
    assert client._delivery_pending is False


@pytest.mark.asyncio
async def test_unknown_reconnect_history_never_offers_hub_item(mock_bizhawk_context: Any) -> None:
    ctx = mock_bizhawk_context
    client, bridge = await setup_client(ctx)
    ctx.server.socket = Mock(closed=False)
    with patch.object(client, '_prepare_receipts', return_value=True):
        await client._deliver_items(ctx)
    assert bridge.offers == []


@pytest.mark.asyncio
async def test_lost_offer_ack_reads_busy_mailbox_before_retry(mock_bizhawk_context: Any) -> None:
    ctx = mock_bizhawk_context
    client, bridge = await setup_client(ctx)
    bridge.lose_offer_reply = True
    with patch.object(client, '_prepare_receipts', return_value=True):
        with pytest.raises(RequestFailedError):
            await client._deliver_items(ctx)
        bridge.lose_offer_reply = False
        await client._deliver_items(ctx)
    assert bridge.offers == [(3860409, 0x220)]


@pytest.mark.asyncio
async def test_reconnect_during_offer_does_not_attach_old_pending_state(mock_bizhawk_context: Any) -> None:
    ctx = mock_bizhawk_context
    client, bridge = await setup_client(ctx)
    bridge.after_offer = lambda: setattr(ctx.server, 'socket', Mock(closed=False))
    with patch.object(client, '_prepare_receipts', return_value=True):
        await client._deliver_items(ctx)
    assert bridge.offers == [(3860409, 0x220)]
    assert client._delivery_pending is False


@pytest.mark.asyncio
@pytest.mark.parametrize('failure', ['partial_mask', 'lost_mask_reply', 'reconnect'])
async def test_recovery_installs_complete_ownership_before_retry(mock_bizhawk_context: Any, failure: str) -> None:
    ctx = mock_bizhawk_context
    client, bridge = await setup_client(ctx)
    with patch.object(client, '_prepare_receipts', return_value=True):
        if failure == 'partial_mask':
            bridge.mask_error_prefix = 2
            with pytest.raises(Exception, match='Connector script returned errors|controlled partial mask write'):
                await client._deliver_items(ctx)
            bridge.mask_error_prefix = None
        elif failure == 'lost_mask_reply':
            bridge.lose_mask_reply = True
            with pytest.raises(RequestFailedError):
                await client._deliver_items(ctx)
            bridge.lose_mask_reply = False
        else:
            ctx.server.socket = Mock(closed=False)
            await client._deliver_items(ctx)
            client.on_package(ctx, 'ReceivedItems', {'index': 0})
        assert bridge.offers == []
        await client._deliver_items(ctx)
    assert bridge.offers == [(3860409, 0x220)]
    assert client._delivery_pending is True


@pytest.mark.asyncio
@pytest.mark.parametrize("item_id", [3860041, 3860402], ids=["area-key", "hub-connection"])
@pytest.mark.parametrize("event", ["ack", "timeout", "reset", "file-change"])
async def test_durable_progress_timeout_preserves_exactly_one_ack(
    mock_bizhawk_context: Any, tmp_path: Path, item_id: int, event: str,
) -> None:
    ctx = mock_bizhawk_context
    ctx.slot_data["copy_ability_room_protocol_version"] = 2
    ctx.items_received = [NetworkItem(item_id, 3960209, 1, 1)]
    client = KirbyAmClient()
    client.initialize_client()
    client._health_rom_auth = b"test scoped auth"
    client.on_package(ctx, "ReceivedItems", {"index": 0})
    bridge = Bridge()
    ctx.bizhawk_ctx._send_message.side_effect = bridge.send
    bridge.ram[0xF00000] = client._health_rom_auth
    native_file = (1).to_bytes(4, "little") + bytes(8)
    bridge.ram[COPY_ROOM_CONTEXT_ADDRESS] = native_file
    flag = bridge.addresses["incoming_item_flag"]
    counter = bridge.addresses["debug_item_counter"]
    frame = bridge.addresses["frame_counter"]
    bridge.ram[counter] = bytes(4)
    bridge.ram[frame] = (1).to_bytes(4, "little")
    client._receipt_journal = journal = ReceiptJournal(str(tmp_path / "receipts.sqlite3"), "test")
    client._receipt_scope = "test"
    key = receipt_key(ctx.items_received, 0)

    def native_ack() -> None:
        assert bridge.value("incoming_item_flag") == 1
        bridge.ram[flag] = bytes(4)
        bridge.ram[counter] = (bridge.value("debug_item_counter") + 1).to_bytes(4, "little")

    def native_reset() -> None:
        bridge.ram[flag] = bytes(4)

    def file_change() -> None:
        # A busy mailbox whose flag and counter still match is not enough if
        # the native file context has changed since the actual offer.
        bridge.ram[COPY_ROOM_CONTEXT_ADDRESS] = (2).to_bytes(4, "little") + bytes(8)

    try:
        with (
            patch.object(client, "_prepare_receipts", return_value=True),
            patch.object(client, "_emit_receive_notification", new_callable=AsyncMock),
        ):
            await client._deliver_items(ctx)
            assert len(bridge.offers) == 1 and client._delivery_pending
            bridge.before_guard = {"ack": native_ack, "reset": native_reset,
                                   "file-change": file_change}.get(event)
            bridge.ram[frame] = (1 + _MAILBOX_ACK_TIMEOUT_FRAMES).to_bytes(4, "little")
            await client._deliver_items(ctx)
            assert client._delivery_pending == (event != "timeout")
            assert client._delivery_timeout_total == (event == "timeout")
            assert not journal.acknowledged(key)
            if event == "file-change":
                assert bridge.value("incoming_item_flag") == 1
                native_reset()
            if event in {"reset", "file-change"}:
                await client._deliver_items(ctx)  # A reset (flag without count) is not an ACK.
                assert client._delivered_item_index == 0 and not journal.acknowledged(key)
            if event != "ack":
                client._delivery_retry_not_before = 0
                await client._deliver_items(ctx)
                assert len(bridge.offers) == 2
                native_ack()
            await client._deliver_items(ctx)
            assert len(bridge.offers) == (1 if event == "ack" else 2)
            assert client._delivered_item_index == 1 and journal.acknowledged(key)
            assert bridge.value("debug_item_counter") == 1
            assert not client._delivery_counter_ahead_fallback_active
    finally:
        journal.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("keys_enabled", [False, True])
async def test_file_restore_only_grants_confirmed_prior_permanent_receipts(
    mock_bizhawk_context, tmp_path, keys_enabled,
):
    from ..client import bizhawk
    ctx = mock_bizhawk_context
    ctx.slot_data = {"copy_ability_room_protocol_version": 2, "area_keys": int(keys_enabled)}
    ctx.items_received = [
        NetworkItem(3860401, 1, 1, 0), NetworkItem(3860041, 2, 1, 0),
        NetworkItem(3860027, 3, 1, 0), NetworkItem(3860402, 4, 1, 0),
        NetworkItem(3860403, 5, 1, 0),
    ]
    client = KirbyAmClient()
    client.initialize_client()
    client.on_package(ctx, "ReceivedItems", {"index": 0})
    client._health_rom_auth = bytes(range(16))
    client._delivered_item_index = 4
    journal = ReceiptJournal(str(tmp_path / "receipts.sqlite3"), "test")
    client._receipt_journal = journal
    for index in (0, 1, 2, 4):
        journal.acknowledge(receipt_key(ctx.items_received, index))
    native = b"".join(x.to_bytes(4, "little") for x in
                      (2, 2, 1, 0, 1, 0x03000000, 0, 0x43504332, 0))
    want = 0x100 | keys_enabled
    read = [native, bytes(4), bytes(4), client._health_rom_auth]
    try:
        with patch.object(bizhawk, "read", new=AsyncMock(return_value=read)), \
                patch.object(bizhawk, "guarded_write", new=AsyncMock(return_value=True)) as write:
            assert not await client._restore_confirmed_file_progress(ctx, 0x0203B004)
            writes, guards = write.await_args.args[1:]
            assert writes == [(0x0203B1C8, want.to_bytes(4, "little") + native[:4], "System Bus")]
            assert (COPY_ROOM_CONTEXT_ADDRESS, native[:12], "System Bus") in guards
            assert (0x0203B004, bytes(4), "System Bus") in guards
            assert client._delivered_item_index == 4
            write.reset_mock()
            read[2] = native[:4]
            assert not await client._restore_confirmed_file_progress(ctx, 0x0203B004)
            write.assert_not_awaited()
            read[1] = (0xA9000000 | want).to_bytes(4, "little")
            read[2] = bytes(4)
            assert await client._restore_confirmed_file_progress(ctx, 0x0203B004)
            write.assert_not_awaited()
            read[0] = bytes(36)
            assert not await client._restore_confirmed_file_progress(ctx, 0x0203B004)
            write.assert_not_awaited()
    finally:
        journal.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("native_active,mailbox_flag,allow_new_writes,writes_restore", [
    (True, 0, True, True),
    (True, 1, True, False),
    (True, 0, False, False),
    (False, 0, True, False),
])
async def test_file_restore_keeps_unresolved_transient_queue_suspended(
    mock_bizhawk_context, tmp_path, native_active, mailbox_flag, allow_new_writes, writes_restore,
):
    from ..client import bizhawk

    ctx = mock_bizhawk_context
    ctx.slot_data = {"copy_ability_room_protocol_version": 2, "area_keys": 1}
    ctx.items_received = [
        NetworkItem(3860401, 11, 1, 0), NetworkItem(3860041, 12, 1, 0),
        NetworkItem(3860031, 13, 1, 0), NetworkItem(3860402, 14, 1, 0),
    ]
    client = KirbyAmClient()
    client.initialize_client()
    client._health_rom_auth = bytes(range(16))
    client._delivered_item_index = 2
    client.on_package(ctx, "ReceivedItems", {"index": 0})
    journal = ReceiptJournal(str(tmp_path / "receipts.sqlite3"), "test")
    client._receipt_journal = journal
    for index in (0, 1):
        journal.acknowledge(receipt_key(ctx.items_received, index))
    transient = receipt_key(ctx.items_received, 2)
    assert journal.reserve(transient)
    flag_addr = client._transport_addr("incoming_item_flag")
    native = (b"".join(x.to_bytes(4, "little") for x in
                      (2, 2, 1, 0, 1, 0x03000000, 0, 0x43504332, 0))
              if native_active else bytes(36))
    read_mailbox = [mailbox_flag.to_bytes(4, "little"), bytes(4), bytes(4), bytes(4)]
    read_restore = [native, bytes(4), bytes(4), client._health_rom_auth]
    readback = [native, (0xA9000101).to_bytes(4, "little"), bytes(4), client._health_rom_auth]
    read_side_effect = [read_mailbox, read_restore]
    if writes_restore:
        read_side_effect += [read_mailbox, readback]
    try:
        with (
            patch.object(client, "_start_inventory_cursor_ready", new=AsyncMock(return_value=True)),
            patch.object(client, "_prepare_receipts", return_value=True),
            patch.object(bizhawk, "read", new=AsyncMock(side_effect=read_side_effect)),
            patch.object(bizhawk, "write", new=AsyncMock()) as ordinary_write,
            patch.object(bizhawk, "guarded_write", new=AsyncMock(return_value=True)) as guarded,
        ):
            await client._deliver_items(ctx, allow_new_writes=allow_new_writes)
            if writes_restore:
                writes, guards = guarded.await_args.args[1:]
                assert writes == [(0x0203B1C8, (0x101).to_bytes(4, "little") + native[:4], "System Bus")]
                assert (flag_addr, bytes(4), "System Bus") in guards
                assert (COPY_ROOM_CONTEXT_ADDRESS, native[:12], "System Bus") in guards
                await client._deliver_items(ctx)
                guarded.assert_awaited_once()
            else:
                guarded.assert_not_awaited()
            ordinary_write.assert_not_awaited()
            assert client._delivered_item_index == 2
            assert not client._delivery_pending
            assert journal.pending() == [transient]
            assert not journal.acknowledged(transient)
            assert not journal.acknowledged(receipt_key(ctx.items_received, 3))
    finally:
        journal.close()
