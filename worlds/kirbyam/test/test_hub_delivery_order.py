"""Late Hub receipts must install ownership before native item effects."""
import base64
import json
from typing import Any, Callable
from unittest.mock import Mock, patch

import pytest

from worlds._bizhawk import RequestFailedError
from ..client import KirbyAmClient
from ..data import data


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
    ctx.items_received = [Mock(item=3860045, player=1)]
    client.on_package(ctx, 'ReceivedItems', {'index': 0})
    bridge = Bridge()
    ctx.bizhawk_ctx._send_message.side_effect = bridge.send
    await client._sync_hub_connection_item_ownership(ctx)
    # The watcher can receive this item during any intervening awaited poll.
    ctx.items_received.append(Mock(item=3860049, player=1))
    client.on_package(ctx, 'ReceivedItems', {'index': 1})
    return client, bridge


@pytest.mark.asyncio
async def test_late_hub_receipt_installs_ownership_before_native_offer(mock_bizhawk_context: Any) -> None:
    ctx = mock_bizhawk_context
    client, bridge = await setup_client(ctx)
    with patch.object(client, '_prepare_receipts', return_value=True):
        await client._deliver_items(ctx)
    assert bridge.offers == [(3860049, 0x220)]
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
    assert bridge.offers == [(3860049, 0x220)]


@pytest.mark.asyncio
async def test_reconnect_during_offer_does_not_attach_old_pending_state(mock_bizhawk_context: Any) -> None:
    ctx = mock_bizhawk_context
    client, bridge = await setup_client(ctx)
    bridge.after_offer = lambda: setattr(ctx.server, 'socket', Mock(closed=False))
    with patch.object(client, '_prepare_receipts', return_value=True):
        await client._deliver_items(ctx)
    assert bridge.offers == [(3860049, 0x220)]
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
    assert bridge.offers == [(3860049, 0x220)]
    assert client._delivery_pending is True
