"""Deferred Candy must not block independent checks, goals or ownership sync."""
import ast
import inspect
import textwrap
from contextlib import ExitStack
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from NetUtils import NetworkItem

from ..candy import CANDY_ITEM_ID
from ..client import KirbyAmClient
from ..data import data
from ..receipts import ReceiptJournal
from .test_candy_delivery import set_native_state
from .test_hub_delivery_order import setup_client
from .test_receipt_journal import receipt_env, make_client  # noqa: F401
from .test_reset_counter_gaps import Mailbox


@pytest.mark.asyncio
@pytest.mark.parametrize('room,goal,gameplay,ai', [
    (129, 1, True, 300), (822, 0, False, 9999), (801, 0, False, 10000),
])
async def test_deferred_candy_does_not_block_checks_or_goal(
    receipt_env: Any, room: int, goal: int, gameplay: bool, ai: int,  # noqa: F811
) -> None:
    ctx = receipt_env
    ctx.slot_data['goal'] = goal
    ctx.server_locations = set()
    ctx.finished_game = False
    ctx.items_received = [NetworkItem(CANDY_ITEM_ID, 1, 1), NetworkItem(3860026, 2, 1)]
    client = make_client(ctx)
    box = Mailbox(client)
    set_native_state(client, box, room=room)
    boss = data.locations['BOSS_DEFEAT_1'].location_id
    bit = next(b for b, ids in client._boss_location_ids_by_bit.items() if boss in ids)
    box.memory[data.transport_ram_addresses['boss_defeat_flags']] = (1 << bit).to_bytes(4, 'little')

    # Isolate unrelated hardware domains while retaining the whole watcher and
    # real boss polling, Candy preflight/journal, and goal-reporting methods.
    tree = ast.parse(textwrap.dedent(inspect.getsource(KirbyAmClient.game_watcher)))
    names = {
        node.value.func.attr for node in ast.walk(tree)
        if isinstance(node, ast.Await) and isinstance(node.value, ast.Call)
        and isinstance(node.value.func, ast.Attribute)
        and isinstance(node.value.func.value, ast.Name) and node.value.func.value.id == 'self'
    }
    real = {'_deliver_items', '_poll_boss_defeat_locations', '_maybe_report_goal'}
    with ExitStack() as stack:
        mocks = {
            name: stack.enter_context(patch.object(client, name, new_callable=AsyncMock))
            for name in names - real
        }
        mocks['_health_protocol_ready'].return_value = True
        mocks['_start_inventory_cursor_ready'].return_value = True
        mocks['_runtime_gameplay_state'].return_value = (gameplay, None if gameplay else 'goal_clear', ai)
        stack.enter_context(patch.object(client, '_hub_connection_item_history_ready', return_value=True))
        stack.enter_context(patch('worlds.kirbyam.client.bizhawk.read', side_effect=box.read))
        stack.enter_context(patch('worlds.kirbyam.client.bizhawk.write', side_effect=box.write))
        stack.enter_context(patch('worlds.kirbyam.client.bizhawk.display_message', new_callable=AsyncMock))
        reserve = stack.enter_context(patch.object(ReceiptJournal, 'reserve', autospec=True, return_value=True))
        await client.game_watcher(ctx)
        assert box.offers == [] and client._delivered_item_index == 0
        reserve.assert_not_called()
        mocks['_sync_hub_connection_item_ownership'].assert_awaited_once()
        if gameplay:
            packets = [packet for call in ctx.send_msgs.await_args_list for packet in call.args[0]]
            assert {'cmd': 'LocationChecks', 'locations': [boss]} in packets
            assert not any(packet['cmd'] == 'StatusUpdate' for packet in packets)
            mocks['_poll_saved_chest_locations'].assert_awaited_once()
            mocks['_poll_room_sanity_locations'].assert_awaited_once()
            # Normal server acknowledgement activates the goal on the next poll.
            ctx.checked_locations.add(boss)
            await client.game_watcher(ctx)
        packets = [packet for call in ctx.send_msgs.await_args_list for packet in call.args[0]]
        assert sum(packet['cmd'] == 'StatusUpdate' and packet['status'] == 30 for packet in packets) == 1
        assert client._delivered_item_index == 0 and box.offers == []
        assert not client._delivery_pending
        reserve.assert_not_called()
        assert ctx.finished_game


@pytest.mark.asyncio
async def test_reconnect_restores_hub_ownership_behind_deferred_candy(mock_bizhawk_context: Any) -> None:
    ctx = mock_bizhawk_context
    client, bridge = await setup_client(ctx)
    client._delivered_item_index = 0
    ctx.items_received = [NetworkItem(CANDY_ITEM_ID, 1, 1), NetworkItem(3860405, 2, 1)]
    ctx.server = SimpleNamespace(socket=SimpleNamespace(closed=False))
    client.on_package(ctx, 'Connected', {})
    client.on_package(ctx, 'ReceivedItems', {'index': 0})
    hp = client._native_addr('kirby_hp_native')
    assert hp is not None
    bridge.ram.update({
        hp: bytes([6]), hp - 0x100 + 0x60: (129).to_bytes(2, 'little'),
        hp - 0x100 + 0xCC: (0x03001000).to_bytes(4, 'little'),
    })
    bridge.ram[bridge.addresses['hub_connection_item_mask']] = bytes(4)
    with patch.object(ReceiptJournal, 'reserve', autospec=True, return_value=True) as reserve:
        await client._sync_hub_connection_item_ownership(ctx)
        assert bridge.value('hub_connection_item_mask') == 0x20
        await client._deliver_items(ctx)
        reserve.assert_not_called()
    assert bridge.offers == [] and client._delivered_item_index == 0
    assert not client._delivery_pending
