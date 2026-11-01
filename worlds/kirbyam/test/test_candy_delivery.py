"""Candy preflight preserves transient ordering and eventual physical ACKs."""
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from NetUtils import NetworkItem

from ..candy import CANDY_EXCLUDED_ROOMS, CANDY_ITEM_ID
from ..receipts import ReceiptJournal, receipt_key
from .test_receipt_journal import receipt_env, make_client, tick, drain  # noqa: F401
from .test_reset_counter_gaps import Mailbox


def set_native_state(client: Any, box: Any, *, room: int = 101, task: int = 0x03001000,
                     flags: int = 0, hp: int = 10) -> None:
    hp_address = client._native_addr('kirby_hp_native')
    kirby = hp_address - 0x100
    for address, value, size in [(kirby + 0x60, room, 2), (kirby + 0xCC, task, 4),
                                 (kirby + 0x0C, flags, 4), (hp_address, hp & 255, 1)]:
        box.memory[address] = value.to_bytes(size, 'little')


@pytest.mark.asyncio
@pytest.mark.parametrize('room,task,flags,hp,expected', [
    (101, 0x03001000, 0, 10, True), (0, 0x03000000, 0, 1, True),
    (899, 0x03007FFC, 0, 10, True), (900, 0x03001000, 0, 10, False),
    (65535, 0x03001000, 0, 10, False), (101, 0x02FFFFFC, 0, 10, False),
    (101, 0x03008000, 0, 10, False), (101, 0x03001001, 0, 10, False),
    (101, 0, 0, 10, False), (101, 0x03001000, 0x40, 10, False),
    (101, 0x03001000, 0x20, 10, True), (101, 0x03001000, 0, 0, False),
    (101, 0x03001000, 0, -1, False),
] + [(room, 0x03001000, 0, 10, False) for room in sorted(CANDY_EXCLUDED_ROOMS)])
async def test_candy_preflight_reads_native_boundaries(
    receipt_env: Any, room: int, task: int, flags: int, hp: int, expected: bool,  # noqa: F811
) -> None:  # noqa: F811
    client = make_client(receipt_env)
    box = Mailbox(client)
    set_native_state(client, box, room=room, task=task, flags=flags, hp=hp)
    with patch('worlds.kirbyam.client.bizhawk.read', side_effect=box.read) as read:
        assert await client._invincibility_candy_ready(receipt_env) is expected
    base = client._native_addr('kirby_hp_native') - 0x100
    read.assert_awaited_once_with(receipt_env.bizhawk_ctx, [
        (base + 0x60, 2, 'System Bus'), (base + 0xCC, 4, 'System Bus'),
        (base + 0x0C, 4, 'System Bus'), (base + 0x100, 1, 'System Bus'),
    ])


@pytest.mark.asyncio
async def test_candy_blocks_queue_before_reservation_then_resumes(receipt_env: Any) -> None:  # noqa: F811
    ctx = receipt_env
    ctx.items_received = [NetworkItem(CANDY_ITEM_ID, 1, 1), NetworkItem(3860026, 2, 1)]
    client = make_client(ctx)
    box = Mailbox(client)
    display = AsyncMock()
    set_native_state(client, box, room=801)
    with patch.object(ReceiptJournal, 'reserve', autospec=True, return_value=True) as reserve:
        for _ in range(3):
            await tick(client, ctx, box, display)
        reserve.assert_not_called()
    assert box.offers == [] and client._delivered_item_index == 0
    assert not client._delivery_pending
    set_native_state(client, box)
    await drain(client, ctx, box, display)
    assert box.applied == [CANDY_ITEM_ID, 3860026]
    assert client._delivered_item_index == 2


@pytest.mark.asyncio
async def test_pending_candy_survives_timeout_and_two_copies_ack_in_order(receipt_env: Any) -> None:  # noqa: F811
    ctx = receipt_env
    ctx.items_received = [NetworkItem(CANDY_ITEM_ID, 1, 1), NetworkItem(CANDY_ITEM_ID, 2, 1)]
    client = make_client(ctx)
    box = Mailbox(client)
    display = AsyncMock()
    set_native_state(client, box)
    await tick(client, ctx, box, display)
    assert box.offers == [CANDY_ITEM_ID]
    client._delivery_pending_frame = -100000
    client._delivery_pending_time = -100000.0
    for _ in range(5):
        await tick(client, ctx, box, display)
    assert box.offers == [CANDY_ITEM_ID]
    assert client._delivery_pending and client._delivered_item_index == 0
    assert box.memory[client._transport_addr('incoming_item_flag')] == (1).to_bytes(4, 'little')
    box.consume()
    set_native_state(client, box, flags=0x40)
    await tick(client, ctx, box, display)
    assert client._delivered_item_index == 1 and box.offers == [CANDY_ITEM_ID]
    assert not client._delivery_pending
    set_native_state(client, box)
    await drain(client, ctx, box, display)
    assert box.offers == [CANDY_ITEM_ID, CANDY_ITEM_ID]
    assert box.applied == [CANDY_ITEM_ID, CANDY_ITEM_ID]
    assert client._delivered_item_index == 2 and display.await_count == 2
    assert receipt_key(ctx.items_received, 0) != receipt_key(ctx.items_received, 1)


@pytest.mark.asyncio
@pytest.mark.parametrize('changed', ['auth', 'rom', 'socket', 'streams', 'item', 'history'])
async def test_candy_preflight_rejects_session_or_history_change(receipt_env: Any, changed: str) -> None:  # noqa: F811
    ctx = receipt_env
    ctx.items_received = [NetworkItem(CANDY_ITEM_ID, 1, 1)]
    client = make_client(ctx)
    box = Mailbox(client)
    set_native_state(client, box)
    base = client._native_addr('kirby_hp_native') - 0x100

    async def read_with_change(bridge: Any, requests: Any) -> Any:
        result = await box.read(bridge, requests)
        if requests[0][0] == base + 0x60:
            if changed == 'auth':
                ctx.auth = 'new-auth'
            elif changed == 'rom':
                client._health_rom_auth = b'fedcba0987654321'
            elif changed == 'socket':
                ctx.server = SimpleNamespace(socket=object())
            elif changed == 'streams':
                ctx.bizhawk_ctx.streams = object()
            elif changed == 'item':
                ctx.items_received[0] = NetworkItem(CANDY_ITEM_ID, 2, 1)
            else:
                ctx.items_received.clear()
        return result

    with patch('worlds.kirbyam.client.bizhawk.read', side_effect=read_with_change), \
            patch('worlds.kirbyam.client.bizhawk.write', side_effect=box.write), \
            patch.object(ReceiptJournal, 'reserve', autospec=True, return_value=True) as reserve:
        await client._deliver_items(ctx)
        reserve.assert_not_called()
    assert box.offers == [] and not client._delivery_pending
    assert client._delivered_item_index == 0
