"""Tutorial receipts remain an ordered, precollect-only permission exception."""
from unittest.mock import AsyncMock, patch

import pytest
from NetUtils import NetworkItem
from ..client import KirbyAmClient
from .test_start_inventory_protocol import validated_client, server_history, mailbox

STARTING = [3860107, 3860103, 3860106, 3860123, 3860104, 3860108]


@pytest.mark.asyncio
@pytest.mark.parametrize('room,demo,hp,ready', [
    (803, 0, 1, True), (804, 0, 1, True), (805, 0, 1, True),
    (801, 0, 1, False), (0, 0, 1, False), (803, 0x10, 1, False),
    (803, 2, 1, False), (803, 0, 0, False), (803, 0, 255, False),
])
async def test_live_tutorial_readiness(mock_bizhawk_context, room, demo, hp, ready):
    client = KirbyAmClient()
    client.initialize_client()
    with patch('worlds.kirbyam.client.bizhawk.read', new_callable=AsyncMock) as read:
        read.return_value = [room.to_bytes(2, 'little'), demo.to_bytes(4, 'little'), bytes([hp])]
        assert await client._tutorial_starting_abilities_ready(mock_bizhawk_context) is ready


@pytest.mark.asyncio
@pytest.mark.parametrize('blocked', [
    NetworkItem(3860026, -2, 0),  # Even precollected food stays deferred.
    NetworkItem(3860018, -2, 0),  # No health changes in the tutorial exception.
    NetworkItem(3860118, -2, 0),  # Sword isn't a guaranteed permission.
    NetworkItem(3860107, 3960566, 1),  # Physical ability checks aren't precollects.
])
async def test_stock_history_tutorial_ack_order_and_stop(mock_bizhawk_context, blocked):
    ctx = mock_bizhawk_context
    client = await validated_client(ctx)
    starting = [NetworkItem(code, -2, 0) for code in STARTING]
    # Stock server, not an invented ReceivedItems packet.
    server, _ = await server_history(ctx, starting, [blocked, starting[0]])
    packet = server.send_msgs.call_args.args[1][0]
    ctx.items_received = packet['items']
    client.on_package(ctx, 'ReceivedItems', packet)
    memory = mailbox(client)
    offers = []
    flag = client._transport_addr('incoming_item_flag')
    counter = client._transport_addr('debug_item_counter')
    item_addr = client._transport_addr('incoming_item_id')

    async def read(_ctx, requests):
        return [memory.get(a, bytes(n)) for a, n, _ in requests]

    async def write(_ctx, requests):
        for a, value, _ in requests:
            memory[a] = value
            if a == flag and int.from_bytes(value, 'little') == 1:
                offers.append(int.from_bytes(memory[item_addr], 'little'))

    async def guarded(_ctx, requests, guards):
        if not all(memory.get(a, bytes(len(v))) == v for a, v, _ in guards):
            return False
        await write(_ctx, requests)
        return True

    with patch('worlds.kirbyam.client.bizhawk.read', side_effect=read), \
         patch('worlds.kirbyam.client.bizhawk.write', side_effect=write), \
         patch('worlds.kirbyam.client.bizhawk.guarded_write', side_effect=guarded), \
         patch.object(client, '_display_client_message', new_callable=AsyncMock):
        for i, code in enumerate(STARTING):
            await client._deliver_items(ctx, allow_new_writes=False, allow_starting_abilities=True)
            assert offers == STARTING[:i+1]
            # Idle pending polls must not reoffer or advance history.
            await client._deliver_items(ctx, allow_new_writes=False, allow_starting_abilities=True)
            assert offers == STARTING[:i+1]
            memory[flag] = bytes(4)
            memory[counter] = (i+1).to_bytes(4, 'little')  # Actual payload +1 ACK.
            await client._deliver_items(ctx, allow_new_writes=False)  # ACK only.
            assert client._delivered_item_index == i+1
        for _ in range(3):
            await client._deliver_items(ctx, allow_new_writes=False, allow_starting_abilities=True)
        assert offers == STARTING
        assert client._delivered_item_index == 6


@pytest.mark.parametrize('value', [None, [], {}, 'bad'])
def test_malformed_starting_receipt_stays_deferred(value):
    from types import SimpleNamespace
    item = SimpleNamespace(item=value, location=-2, player=0)
    assert not KirbyAmClient._is_guaranteed_starting_ability_receipt(item)
