"""Offline reset replay uses physical +1 ACKs, never history-index ACKs."""
from unittest.mock import AsyncMock, patch

import pytest
from NetUtils import NetworkItem

from ..client import KirbyAmClient


class Mailbox:
    def __init__(self, client, count=0, cursor=0):
        self.client = client
        self.memory = {client._transport_addr(key): value.to_bytes(4, 'little') for key, value in {
            'incoming_item_flag': 0, 'debug_item_counter': count,
            'delivered_item_index': cursor, 'frame_counter': 1, 'hook_heartbeat': 1,
        }.items()}
        self.offers = []
        self.applied = []

    async def read(self, _ctx, requests):
        return [self.memory.get(a, bytes(n)) for a, n, _ in requests]

    async def write(self, _ctx, requests):
        for address, value, _ in requests:
            self.memory[address] = value
            if address == self.client._transport_addr('incoming_item_id'):
                self.offers.append(int.from_bytes(value, 'little'))

    def consume(self):
        c = self.client
        flag = c._transport_addr('incoming_item_flag')
        assert self.memory[flag] == (1).to_bytes(4, 'little')
        self.applied.append(int.from_bytes(self.memory[c._transport_addr('incoming_item_id')], 'little'))
        self.memory[flag] = bytes(4)
        counter = c._transport_addr('debug_item_counter')
        self.memory[counter] = (int.from_bytes(self.memory[counter], 'little') + 1).to_bytes(4, 'little')


@pytest.mark.asyncio
@pytest.mark.parametrize('fresh_item', [3860001, 3860026, 3860027, 3860032, 3860033, 3860034])
@pytest.mark.parametrize('restore_cursor', [False, True])
@pytest.mark.parametrize('pending_polls', [0, 3])
async def test_reset_skipped_food_and_battery_keep_vitality_pending_and_fresh_effect_once(
    mock_bizhawk_context, fresh_item, restore_cursor, pending_polls,
):
    ctx = mock_bizhawk_context
    client = KirbyAmClient()
    client.initialize_client()
    ctx.items_received = [NetworkItem(item, location, 1) for item, location in [
        (3860026, 3960209), (3860019, 3960451), (3860027, 3960566),
    ]]
    client._delivered_item_index = 3
    client._last_rom_received_count = 3
    client._acknowledged_non_redeliverable_indices.update({0, 2})
    box = Mailbox(client)
    with patch('worlds.kirbyam.client.bizhawk.read', side_effect=box.read), \
         patch('worlds.kirbyam.client.bizhawk.write', side_effect=box.write), \
         patch.object(client, '_emit_receive_notification', new_callable=AsyncMock), \
         patch.object(client, '_log_verbose') as log:
        await client._deliver_items(ctx)
        assert client._delivery_pending_item_index == 1
        # Owner log's two offers must not be caused by idle polls erasing this request.
        for _ in range(pending_polls):
            await client._deliver_items(ctx)
            assert client._delivery_pending_item_index == 1
        assert box.offers == [3860019]
        box.consume()
        # ACK while the watcher gates new writes during title/file loading.
        await client._deliver_items(ctx, allow_new_writes=False)
        assert client._delivered_item_index == 2
        await client._deliver_items(ctx)
        assert client._delivered_item_index == 3
        log.reset_mock()
        for _ in range(240):
            await client._deliver_items(ctx)
        assert not log.called
        assert not client._delivery_pending
        assert box.offers == [3860019]
        if restore_cursor:
            await client._load_persistent_state(ctx)
        ctx.items_received.append(NetworkItem(fresh_item, 3960567, 1))
        await client._deliver_items(ctx)
        for _ in range(3):
            await client._deliver_items(ctx)
            assert client._delivery_pending_item_index == 3
        box.consume()
        for _ in range(4):
            await client._deliver_items(ctx)
        assert box.offers == [3860019, fresh_item]
        assert box.applied == [3860019, fresh_item]
        assert client._delivered_item_index == 4
        assert not client._delivery_pending


@pytest.mark.asyncio
async def test_observed_counter_two_cursor_three_is_stable_after_battery_skip(mock_bizhawk_context):
    ctx = mock_bizhawk_context
    client = KirbyAmClient()
    client.initialize_client()
    ctx.items_received = [NetworkItem(item, 3960566 + i, 1)
                          for i, item in enumerate([3860026, 3860019, 3860027])]
    client._delivered_item_index = 2
    client._acknowledged_non_redeliverable_indices.update({0, 2})
    box = Mailbox(client, count=2, cursor=2)
    with patch('worlds.kirbyam.client.bizhawk.read', side_effect=box.read), \
         patch('worlds.kirbyam.client.bizhawk.write', side_effect=box.write), \
         patch.object(client, '_log_verbose') as log:
        await client._deliver_items(ctx)
        log.reset_mock()
        for _ in range(240):
            await client._deliver_items(ctx)
        assert client._delivered_item_index == 3
        assert not box.offers
        assert not log.called
