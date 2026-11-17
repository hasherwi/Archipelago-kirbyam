"""Battery deferral keeps one receipt in flight; this does not simulate native charges."""
import ast
import base64
import inspect
import textwrap
from contextlib import ExitStack
from unittest.mock import AsyncMock, patch

import pytest
from NetUtils import NetworkItem

from ..client import KirbyAmClient
from ..phone_protocol import PHONE_ITEM_ID, PHONE_REQUEST_ADDRESS
from ..copy_room_protocol import COPY_ROOM_CONTEXT_ADDRESS
from ..receipts import receipt_key
from .test_phone_protocol import _reads
from .test_receipt_journal import receipt_env, make_client, tick, drain  # noqa: F401
from .test_reset_counter_gaps import Mailbox

BATTERY = 3860027


def expire(client, box, clock):
    if clock == 'frame':
        client._delivery_pending_frame = -100000
    else:
        client._delivery_pending_frame = 1
        client._delivery_pending_time = -100000.0


@pytest.mark.asyncio
@pytest.mark.parametrize('clock', ['frame', 'wall'])
@pytest.mark.parametrize('allow_new_writes', [False, True])
async def test_battery_timeout_then_late_ack_is_exactly_once(receipt_env, clock, allow_new_writes):
    ctx = receipt_env
    ctx.items_received = [NetworkItem(BATTERY, 1, 1), NetworkItem(BATTERY, 2, 1)]
    client = make_client(ctx)
    box = Mailbox(client)
    display = AsyncMock()
    await tick(client, ctx, box, display)
    key = receipt_key(ctx.items_received, 0)
    assert client._receipt_journal.pending() == [key]
    expire(client, box, clock)
    for _ in range(5):
        await tick(client, ctx, box, display, allow_new_writes=allow_new_writes)
    assert box.offers == [BATTERY] and box.applied == []
    assert client._delivery_pending and client._delivered_item_index == 0
    assert client._receipt_journal.pending() == [key]
    assert not client._receipt_journal.acknowledged(key)
    assert client._delivery_timeout_total == 0
    assert box.memory[client._transport_addr('incoming_item_flag')] == (1).to_bytes(4, 'little')
    display.assert_not_awaited()
    box.consume()  # Simulated standard ACK only after native acceptance.
    await tick(client, ctx, box, display, allow_new_writes=False)
    assert client._delivered_item_index == 1 and not client._delivery_pending
    assert client._receipt_journal.acknowledged(key)
    await drain(client, ctx, box, display)
    assert box.offers == box.applied == [BATTERY, BATTERY]
    assert client._delivered_item_index == 2 and display.await_count == 2
    # Native reload starts fresh: historical Battery credits must not replay.
    client._receipt_journal.close()
    client = make_client(ctx)
    reloaded = Mailbox(client)
    await drain(client, ctx, reloaded, display)
    assert not reloaded.offers and not reloaded.applied
    assert display.await_count == 2


@pytest.mark.asyncio
async def test_battery_deferral_reset_without_ack_stays_uncertain(receipt_env):
    ctx = receipt_env
    ctx.items_received = [NetworkItem(BATTERY, 1, 1)]
    client = make_client(ctx)
    box = Mailbox(client)
    display = AsyncMock()
    await tick(client, ctx, box, display)
    expire(client, box, 'frame')
    await tick(client, ctx, box, display)
    key = receipt_key(ctx.items_received, 0)
    reset = Mailbox(client)  # Flag0/count0 is reset, not an ACK.
    for _ in range(3):
        await tick(client, ctx, reset, display)
    assert client._receipt_blocked and client._receipt_journal.pending() == [key]
    assert not reset.offers and client._delivered_item_index == 0
    display.assert_not_awaited()


@pytest.mark.asyncio
async def test_pending_battery_does_not_block_actual_phone_ownership_sync(receipt_env):
    ctx = receipt_env
    ctx.auth = base64.b64encode(b'1234567890abcdef').decode()
    ctx.slot_data.update(copy_ability_room_protocol_version=2, phone_protocol_version=1,
                         starting_phone_access=False)
    ctx.items_received = [NetworkItem(BATTERY, 1, 1), NetworkItem(PHONE_ITEM_ID, 2, 1)]
    client = make_client(ctx)
    box = Mailbox(client)
    await tick(client, ctx, box, AsyncMock())
    expire(client, box, 'frame')
    client._watcher_server_ready = True
    client._ram_state_loaded = True
    client._watcher_requires_bizhawk_resync = False
    raw, fence = _reads(ctx)
    phone_reads = iter((raw, fence))

    async def read(bridge, requests):
        if requests[0][0] == COPY_ROOM_CONTEXT_ADDRESS:
            return next(phone_reads)
        return await box.read(bridge, requests)

    tree = ast.parse(textwrap.dedent(inspect.getsource(KirbyAmClient.game_watcher)))
    names = {node.value.func.attr for node in ast.walk(tree)
             if isinstance(node, ast.Await) and isinstance(node.value, ast.Call)
             and isinstance(node.value.func, ast.Attribute)
             and isinstance(node.value.func.value, ast.Name) and node.value.func.value.id == 'self'}
    with ExitStack() as stack:
        mocks = {name: stack.enter_context(patch.object(client, name, new_callable=AsyncMock))
                 for name in names - {'_deliver_items'}}
        mocks['_health_protocol_ready'].return_value = True
        mocks['_start_inventory_cursor_ready'].return_value = True
        mocks['_runtime_gameplay_state'].return_value = (True, None, 300)
        stack.enter_context(patch.object(client, '_hub_connection_item_history_ready', return_value=True))
        stack.enter_context(patch('worlds.kirbyam.client.sync_copy_room_ownership', new_callable=AsyncMock))
        stack.enter_context(patch('worlds.kirbyam.client.bizhawk.read', side_effect=read))
        stack.enter_context(patch('worlds.kirbyam.client.bizhawk.write', side_effect=box.write))
        grant = stack.enter_context(patch('worlds.kirbyam.client.bizhawk.guarded_write', new_callable=AsyncMock, return_value=True))
        await client.game_watcher(ctx)
    grant.assert_awaited_once()
    assert grant.call_args.args[1] == [(PHONE_REQUEST_ADDRESS + 4, (1).to_bytes(4, 'little'), 'System Bus'),
                                       (PHONE_REQUEST_ADDRESS, (7).to_bytes(4, 'little'), 'System Bus')]
    assert client._delivery_pending and client._delivered_item_index == 0
    assert box.offers == [BATTERY] and not box.applied
