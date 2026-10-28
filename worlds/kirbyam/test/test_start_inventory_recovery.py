"""Stock Sync precollect ownership with empty history and cold RAM recovery (#943)."""
from typing import Any
from unittest.mock import patch

import pytest
from NetUtils import NetworkItem

from . import test_start_inventory_protocol as protocol

# These existing bridge/server fixtures intentionally model dynamic contexts.
validated_client: Any = protocol.validated_client
server_history: Any = protocol.server_history
mailbox: Any = protocol.mailbox
io: Any = protocol.io


@pytest.mark.asyncio
@pytest.mark.parametrize('normal', [[], [NetworkItem(3860026, 3960566, 1)]])
@pytest.mark.parametrize('copies', [1, 2])
async def test_stock_precollects_recover_unique_vitality_after_cold_ram_reset(
    mock_bizhawk_context: Any, normal: list[NetworkItem], copies: int,
) -> None:
    ctx = mock_bizhawk_context
    client = await validated_client(ctx)
    starting = [NetworkItem(3860018, -2, 0)] * copies
    server, connection = await server_history(ctx, starting, normal)
    packet = server.send_msgs.call_args.args[1][0]
    assert packet == {'cmd': 'ReceivedItems', 'index': 0, 'items': starting + normal}
    assert connection.send_index == copies + len(normal)
    ctx.items_received = packet['items']
    memory = mailbox(client)
    read, write = io(memory)
    with patch('worlds.kirbyam.client.bizhawk.read', side_effect=read), \
            patch('worlds.kirbyam.client.bizhawk.guarded_write', side_effect=write):
        client.on_package(ctx, 'ReceivedItems', packet)
        await client._reconcile_vitality_ownership(ctx)
        assert memory[client._native_addr('kirby_hp_native')] == b'\x07'
        for _ in range(3):
            # Reauthenticate against real server output after transport/native
            # RAM loss. The same unique upgrade must never heal or stack.
            client.on_package(ctx, 'Connected', {})
            server, _ = await server_history(ctx, starting, normal)
            client.on_package(ctx, 'ReceivedItems', server.send_msgs.call_args.args[1][0])
            memory.update(mailbox(client))
            # Native save retained ownership and damage; only transport RAM was lost.
            memory[client._native_addr('kirby_vitality_counter_native')] = b'\x01\x00'
            memory[client._native_addr('kirby_max_hp_native')] = b'\x07'
            await client._reconcile_vitality_ownership(ctx)
            assert memory[client._native_addr('kirby_vitality_counter_native')] == b'\x01\x00'
            assert memory[client._native_addr('kirby_hp_native')] == b'\x02'
            assert memory[client._native_addr('kirby_max_hp_native')] == b'\x07'
            assert memory[client._transport_addr('delivered_vitality_item_bits')] == b'\x01\x00\x00\x80'
            after = dict(memory)
            await client._reconcile_vitality_ownership(ctx)
            assert memory == after
