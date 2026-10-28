"""All eight remote shards survive repeated receipt-journal reopen cycles (#974)."""
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from NetUtils import NetworkItem

from . import test_receipt_journal as receipts
from . import test_reset_counter_gaps as counters

receipt_env = receipts.receipt_env
make_client: Any = receipts.make_client
drain: Any = receipts.drain
Mailbox: Any = counters.Mailbox


@pytest.mark.asyncio
@pytest.mark.parametrize('saved_mask', [0, 0x07, 0xFF])
async def test_every_shard_restores_after_twelve_cold_reopens(receipt_env: Any, saved_mask: int) -> None:
    ctx = receipt_env
    # Interleave transient effects to ensure skipped old receipts cannot confuse
    # the physical ACK count with the index into full server history.
    ids = [3860002 + bit for bit in range(8)]
    history = [item for pair in zip(ids, [3860026] * 8) for item in pair]
    ctx.items_received = [NetworkItem(item, 3960000 + index, 2) for index, item in enumerate(history)]
    client = make_client(ctx)
    box = Mailbox(client)
    display = AsyncMock()
    await drain(client, ctx, box, display)
    assert box.applied == history
    assert client._delivered_item_index == len(history)
    for _ in range(12):
        client._receipt_journal.close()
        client = make_client(ctx)
        box = Mailbox(client)
        native = client._native_addr('shard_bitfield_native')
        delivered = client._transport_addr('delivered_shard_bitfield')
        box.memory[native] = bytes([saved_mask])
        # Transport RAM is lost, even when native save ownership survives.
        box.memory[delivered] = bytes(4)
        display.reset_mock()
        await drain(client, ctx, box, display)
        assert box.applied == ids
        assert client._delivered_item_index == len(history)
        assert int.from_bytes(box.memory[client._transport_addr('debug_item_counter')], 'little') == 8
        display.assert_not_awaited()
        with patch('worlds.kirbyam.client.bizhawk.read', side_effect=box.read), \
                patch('worlds.kirbyam.client.bizhawk.write', side_effect=box.write):
            await client._reconcile_native_shard_ownership(ctx)
            assert box.memory[native] == b'\xff'
            assert box.memory[delivered] == b'\xff\x00\x00\x00'
            after = dict(box.memory)
            await client._reconcile_native_shard_ownership(ctx)
            assert box.memory == after
    client._receipt_journal.close()
