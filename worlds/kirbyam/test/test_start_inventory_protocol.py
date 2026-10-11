"""Exercise stock server history, precollect authority and cursor migration."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from MultiServer import Client, process_client_cmd
from NetUtils import NetworkItem
from ..client import KirbyAmClient
from ..data import data


async def validated_client(ctx):
    client = KirbyAmClient()
    ctx.command_processor = None
    with patch('worlds.kirbyam.client.bizhawk.read', new_callable=AsyncMock) as read:
        read.side_effect = [[b'AGB KIRBY AM', b'B8KE', b'01'],
                            [b'\x01' + bytes(15)], [b'\x00\xf0\x00\xf8']]
        assert await client.validate_rom(ctx)
    import base64
    ctx.auth = base64.b64encode(b"\x01" + bytes(15)).decode()
    return client


async def server_history(ctx, starting, received):
    server = SimpleNamespace(start_inventory={1: starting}, received_items={(0,1,True): received},
                             send_msgs=AsyncMock())
    connection = SimpleNamespace(auth=True, slot=1, team=0, send_index=0)
    Client.items_handling.fset(connection, ctx.items_handling)
    await process_client_cmd(server, connection, {'cmd': 'Sync'})
    return server, connection


def mailbox(client, *, received=0, delivered=0, bits=0, cookie=0x4B41504D, flag=0):
    values = {'delivered_vitality_item_bits':bits, 'debug_item_counter':received,
              'delivered_item_index':delivered, 'incoming_item_flag':flag, 'mailbox_init_cookie':cookie}
    memory = {client._transport_addr(k):v.to_bytes(4,'little') for k,v in values.items()}
    memory.update({client._native_addr('kirby_vitality_counter_native'):bytes(2),
                   client._native_addr('kirby_hp_native'):bytes([2]),
                   client._native_addr('kirby_max_hp_native'):bytes([6])})
    memory.update({0xA0: b"AGB KIRBY AM", 0x15F690: bytes(4),
                   data.rom_addresses["gArchipelagoInfo"] & 0x1FFFFFF: b"\x01" + bytes(15)})
    return memory


def io(memory):
    async def read(_ctx, requests): return [memory[a] for a,n,d in requests]
    async def write(_ctx, requests, guards):
        if not all(memory[a] == value for a,value,d in guards): return False
        for a,value,d in requests: memory[a]=value
        return True
    return read,write


@pytest.mark.asyncio
async def test_stock_server_starting_vitality_reaches_authoritative_mask(mock_bizhawk_context):
    ctx=mock_bizhawk_context;client=await validated_client(ctx)
    server,_=await server_history(ctx,[NetworkItem(3860018,-2,0)],[NetworkItem(3860026,3960566,1)])
    packet=server.send_msgs.call_args.args[1][0]
    assert packet['index']==0
    assert [item.item for item in packet['items']]==[3860018,3860026]
    ctx.items_received=packet['items'];client.on_package(ctx,'ReceivedItems',packet)
    memory=mailbox(client);read,write=io(memory)
    with patch('worlds.kirbyam.client.bizhawk.read',side_effect=read), patch('worlds.kirbyam.client.bizhawk.guarded_write',side_effect=write):
        await client._reconcile_vitality_ownership(ctx)
        assert int.from_bytes(memory[client._native_addr('kirby_vitality_counter_native')],'little')==1
        assert int.from_bytes(memory[client._transport_addr('delivered_vitality_item_bits')],'little')==0x80000001
        memory[client._native_addr('kirby_hp_native')]=bytes([2])
        client.on_package(ctx,'Connected',{})
        client.on_package(ctx,'ReceivedItems',packet)
        await client._reconcile_vitality_ownership(ctx)
        assert memory[client._native_addr('kirby_hp_native')]==bytes([2])


@pytest.mark.asyncio
async def test_stock_server_includes_every_starting_item_type(mock_bizhawk_context):
    ctx=mock_bizhawk_context;await validated_client(ctx)
    starting=[NetworkItem(item.item_id,-2,0) for item in data.items.values()]
    server,connection=await server_history(ctx,starting,[NetworkItem(3860026,3960566,1)])
    packet=server.send_msgs.call_args.args[1][0]
    assert packet['items']==starting+[NetworkItem(3860026,3960566,1)]
    assert connection.send_index==len(starting)+1


@pytest.mark.asyncio
async def test_truly_empty_stock_history_does_not_authorize_migration(mock_bizhawk_context):
    ctx=mock_bizhawk_context;client=await validated_client(ctx)
    server,_=await server_history(ctx,[],[])
    server.send_msgs.assert_not_awaited()
    client.on_package(ctx,'Connected',{})
    with patch('worlds.kirbyam.client.bizhawk.read',new_callable=AsyncMock) as read:
        await client._reconcile_vitality_ownership(ctx)
        read.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize('received,delivered,flag',[(3,3,0),(0,2,0),(0,0,1)])
async def test_legacy_prefixed_history_blocks_then_adopts_cold_boot(mock_bizhawk_context,received,delivered,flag):
    ctx=mock_bizhawk_context;client=await validated_client(ctx)
    ctx.items_received=[NetworkItem(3860018,-2,0),NetworkItem(3860026,3960566,1)]
    client.on_package(ctx,'ReceivedItems',{'index':0,'items':ctx.items_received})
    client._delivered_item_index=3
    client._acknowledged_non_redeliverable_indices.add(0)
    memory=mailbox(client,received=received,delivered=delivered,flag=flag);read,write=io(memory)
    with patch('worlds.kirbyam.client.bizhawk.read',side_effect=read), patch('worlds.kirbyam.client.bizhawk.guarded_write',side_effect=write) as writes:
        assert not await client._start_inventory_cursor_ready(ctx)
        await client._reconcile_vitality_ownership(ctx)
        await client._deliver_items(ctx)
        writes.assert_not_called()
        for key in ['debug_item_counter','delivered_item_index','incoming_item_flag']:
            memory[client._transport_addr(key)]=bytes(4)
        assert await client._start_inventory_cursor_ready(ctx)
        assert client._delivered_item_index==0
        assert client._acknowledged_non_redeliverable_indices=={1}
        # A new-format live cursor remains valid through reconnect, without reset.
        memory[client._transport_addr('debug_item_counter')]=(2).to_bytes(4,'little')
        client._delivered_item_index=2
        assert await client._start_inventory_cursor_ready(ctx)
        assert client._delivered_item_index==2


@pytest.mark.asyncio
async def test_prefix_marker_waits_for_payload_init_and_atomic_guard(mock_bizhawk_context):
    ctx=mock_bizhawk_context;client=await validated_client(ctx)
    ctx.items_received=[NetworkItem(3860018,-2,0)]
    client.on_package(ctx,'ReceivedItems',{'index':0,'items':ctx.items_received})
    memory=mailbox(client,cookie=0);read,_=io(memory)
    with patch('worlds.kirbyam.client.bizhawk.read',side_effect=read), patch('worlds.kirbyam.client.bizhawk.guarded_write',new_callable=AsyncMock,return_value=False) as write:
        assert not await client._start_inventory_cursor_ready(ctx)
        write.assert_not_called()
        memory[client._transport_addr('mailbox_init_cookie')]=(0x4B41504D).to_bytes(4,'little')
        assert not await client._start_inventory_cursor_ready(ctx)
        assert memory[client._transport_addr('delivered_vitality_item_bits')]==bytes(4)


@pytest.mark.asyncio
async def test_all_starting_item_ids_keep_mailbox_order_before_normal_history(mock_bizhawk_context):
    ctx=mock_bizhawk_context;client=await validated_client(ctx)
    starting=[NetworkItem(item.item_id,-2,0) for item in data.items.values()]
    server,_=await server_history(ctx,starting,[NetworkItem(3860026,3960566,1)])
    packet=server.send_msgs.call_args.args[1][0]
    ctx.items_received=packet['items'];client.on_package(ctx,'ReceivedItems',packet)
    memory=mailbox(client)
    async def read(_ctx, requests): return [memory.get(a,bytes(n)) for a,n,d in requests]
    async def write(_ctx, requests):
        for a,v,d in requests:memory[a]=v
    async def guarded(_ctx, requests, guards):
        assert all(memory[a]==v for a,v,d in guards)
        await write(_ctx,requests);return True
    observed=[];flag=client._transport_addr('incoming_item_flag')
    with patch('worlds.kirbyam.client.bizhawk.read',side_effect=read), \
         patch('worlds.kirbyam.client.bizhawk.write',side_effect=write), \
         patch('worlds.kirbyam.client.bizhawk.guarded_write',side_effect=guarded), \
         patch.object(client,'_emit_receive_notification',new_callable=AsyncMock):
        for index in range(len(ctx.items_received)):
            await client._deliver_items(ctx)
            assert int.from_bytes(memory[flag],'little')==1
            observed.append(int.from_bytes(memory[client._transport_addr('incoming_item_id')],'little'))
            memory[flag]=bytes(4)
            counter = client._transport_addr('debug_item_counter')
            memory[counter]=(int.from_bytes(memory[counter], 'little')+1).to_bytes(4,'little')
        await client._deliver_items(ctx)
    assert observed==[item.item for item in packet['items']]
    assert client._delivered_item_index==len(observed)
