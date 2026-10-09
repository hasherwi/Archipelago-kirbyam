from unittest.mock import AsyncMock, patch
import pytest
from NetUtils import NetworkItem
from .test_start_inventory_protocol import validated_client, mailbox

@pytest.mark.asyncio
@pytest.mark.parametrize('fresh_item',[3860001,3860026,3860027,3860032,3860033,3860034])
async def test_migrated_ack_prefix_does_not_repeat_fresh_effect(mock_bizhawk_context,fresh_item):
    ctx=mock_bizhawk_context; client=await validated_client(ctx)
    ctx.items_received=[NetworkItem(3860018,-2,0)]+[NetworkItem(3860026,3960566+i,1) for i in range(3)]+[NetworkItem(fresh_item,3960569,1)]
    client.on_package(ctx,'ReceivedItems',{'index':0,'items':ctx.items_received})
    client._acknowledged_non_redeliverable_indices.update({0,1,2})
    client._delivered_item_index=3
    memory=mailbox(client,received=3,delivered=3)
    async def read(_ctx,requests):return [memory.get(a,bytes(n)) for a,n,d in requests]
    async def write(_ctx,requests):
        for a,v,d in requests:memory[a]=v
    async def guarded(_ctx,requests,guards):
        if any(memory[a]!=v for a,v,d in guards):return False
        await write(_ctx,requests);return True
    observed=[];flag=client._transport_addr('incoming_item_flag');counter=client._transport_addr('debug_item_counter')
    with patch('worlds.kirbyam.client.bizhawk.read',side_effect=read),patch('worlds.kirbyam.client.bizhawk.write',side_effect=write),patch('worlds.kirbyam.client.bizhawk.guarded_write',side_effect=guarded),patch.object(client,'_emit_receive_notification',new_callable=AsyncMock):
        assert not await client._start_inventory_cursor_ready(ctx)
        for key in ['debug_item_counter','delivered_item_index','incoming_item_flag']:memory[client._transport_addr(key)]=bytes(4)
        assert await client._start_inventory_cursor_ready(ctx)
        assert client._acknowledged_non_redeliverable_indices=={1,2,3}
        for tick in range(16):
            await client._deliver_items(ctx)
            if int.from_bytes(memory[flag],'little')==1:
                observed.append(int.from_bytes(memory[client._transport_addr('incoming_item_id')],'little'))
                memory[flag]=bytes(4)
                memory[counter]=(int.from_bytes(memory[counter],'little')+1).to_bytes(4,'little')
    assert observed==[3860018,fresh_item],observed


@pytest.mark.asyncio
@pytest.mark.parametrize('reconnect', [False, True])
async def test_multiple_receipt_gaps_survive_idle_polls_reconnect_and_rollback(mock_bizhawk_context, reconnect):
    ctx = mock_bizhawk_context
    client = await validated_client(ctx)
    ctx.items_received = [NetworkItem(item, 3960566 + i, 1) for i, item in enumerate(
        [3860026, 3860032, 3860027, 3860026, 3860033, 3860027, 3860034])]
    client._acknowledged_non_redeliverable_indices.update({0, 2, 3, 5})
    memory = mailbox(client)
    flag = client._transport_addr('incoming_item_flag')
    counter = client._transport_addr('debug_item_counter')
    item_addr = client._transport_addr('incoming_item_id')
    observed = []

    async def read(_ctx, requests):
        return [memory.get(a, bytes(n)) for a, n, _ in requests]

    async def write(_ctx, requests):
        for address, value, _ in requests:
            memory[address] = value

    with patch('worlds.kirbyam.client.bizhawk.read', side_effect=read), \
         patch('worlds.kirbyam.client.bizhawk.write', side_effect=write):
        client._emit_receive_notification = AsyncMock()
        for expected_index in [1, 4, 6]:
            await client._deliver_items(ctx)
            assert client._delivery_pending_item_index == expected_index
            # Polls before native consumption must retain the exact request.
            for _ in range(3):
                await client._deliver_items(ctx)
                assert client._delivery_pending_item_index == expected_index
                assert int.from_bytes(memory[flag], 'little') == 1
            observed.append(int.from_bytes(memory[item_addr], 'little'))
            memory[flag] = bytes(4)
            memory[counter] = (int.from_bytes(memory[counter], 'little') + 1).to_bytes(4, 'little')
            # Limit history temporarily so ACK cannot also queue the next request.
            history = ctx.items_received
            ctx.items_received = history[:expected_index + 1]
            await client._deliver_items(ctx)
            for _ in range(3):
                await client._deliver_items(ctx)
                assert not client._delivery_pending
            if reconnect:
                client = await validated_client(ctx)
                client._emit_receive_notification = AsyncMock()
                await client._load_persistent_state(ctx)
                client._acknowledged_non_redeliverable_indices.update({0, 2, 3, 5})
            ctx.items_received = history
        assert observed == [3860032, 3860033, 3860034]
        assert client._delivered_item_index == 7
        assert int.from_bytes(memory[counter], 'little') == 3
        # An actual physical-counter rollback must not replay acknowledged effects.
        memory[counter] = bytes(4)
        memory[client._transport_addr('delivered_item_index')] = bytes(4)
        for _ in range(3):
            await client._deliver_items(ctx)
            assert not client._delivery_pending
            assert memory[flag] == bytes(4)
        assert client._delivered_item_index == 7
