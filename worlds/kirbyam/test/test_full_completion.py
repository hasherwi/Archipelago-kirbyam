"""Full completion cannot confuse physical actions, ownership, or save identity."""
from __future__ import annotations

import base64
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from NetUtils import ClientStatus
from ..client import KirbyAmClient
from ..completion import (
    CompletionProgress, FULL_COMPLETION_MARKER, FULL_COMPLETION_MARKER_OFFSET, PHYSICAL_IDS,
    PHYSICAL_SAVE_MASK, PHYSICAL_SAVE_TAG, REQUIRED_ITEM_IDS, ROOM_INDICES,
    merge_acknowledged_levers, native_progress, ownership_complete, saved_physical_mask,
)
from ..vitality import VITALITY_ITEM_IDS
from .test_client import _run_goal_command
from . import test_post_clear_gameplay

completed_save = test_post_clear_gameplay.completed_save

AUTH = bytes(range(16))


def complete_native(save_id: int = 0) -> list[bytes]:
    visits = bytearray(576)
    for index in ROOM_INDICES:
        visits[index * 2:index * 2 + 2] = b'\x00\x80'
    return [(2**84 - 1).to_bytes(16, 'little'), (255).to_bytes(4, 'little'), bytes(visits),
            (1).to_bytes(4, 'little') * 15, save_id.to_bytes(2, 'little'),
            (9999).to_bytes(4, 'little'), bytes(4)]


def progress(values: list[bytes]) -> CompletionProgress:
    result = native_progress(values)
    assert result is not None
    return result


def record(mask: int = PHYSICAL_SAVE_MASK) -> bytes:
    return AUTH + (PHYSICAL_SAVE_TAG | mask).to_bytes(4, 'little')


@pytest.mark.parametrize('family,index', [('chest', i) for i in range(84)]
                         + [('room', i) for i in ROOM_INDICES]
                         + [('switch', i) for i in range(15)] + [('shard', i) for i in range(8)])
def test_every_native_obligation_is_required(family: str, index: int) -> None:
    values = complete_native()
    assert progress(values).complete
    if family == 'room':
        visits = bytearray(values[2])
        visits[index * 2:index * 2 + 2] = bytes(2)
        values[2] = bytes(visits)
    elif family == 'switch':
        switches = bytearray(values[3])
        switches[index * 4:index * 4 + 4] = bytes(4)
        values[3] = bytes(switches)
    else:
        field = 0 if family == 'chest' else 1
        # Spare bits cannot compensate for the missing real requirement.
        bits = int.from_bytes(values[field], 'little') & ~(1 << index)
        bits |= 1 << (100 if field == 0 else 16)
        values[field] = bits.to_bytes(len(values[field]), 'little')
    assert not progress(values).complete


@pytest.mark.parametrize('state', [0, 100, 200, 300, 9998, 10001, 65535])
def test_clear_is_required_and_unknown_states_cannot_complete(state: int) -> None:
    values = complete_native()
    values[5] = state.to_bytes(4, 'little')
    result = native_progress(values)
    assert result is None or not result.complete


@pytest.mark.parametrize('index', range(7))
def test_short_reads_fail_closed(index: int) -> None:
    values = complete_native()
    values[index] = values[index][:-1]
    assert native_progress(values) is None


def test_invalid_save_demo_and_stale_percentage_are_not_evidence() -> None:
    values = complete_native(3)
    assert native_progress(values) is None
    values = complete_native()
    values[6] = (16).to_bytes(4, 'little')
    assert native_progress(values) is None
    # No percentage input: neither a cached100 nor a latched10000 fills a missing chest.
    values = complete_native()
    values[5] = (10000).to_bytes(4, 'little')
    values[0] = bytes(16)
    assert not progress(values).complete


@pytest.mark.parametrize('minimum,maximum', [(a, b) for a in range(1, 11) for b in range(a, 11)])
def test_health_range_ownership_is_independent(minimum: int, maximum: int) -> None:
    required = set(REQUIRED_ITEM_IDS)
    assert ownership_complete(required)
    assert ownership_complete([*required, *VITALITY_ITEM_IDS[:maximum-minimum], *VITALITY_ITEM_IDS])
    for item in required:
        assert not ownership_complete((required - {item}) | set(VITALITY_ITEM_IDS))
    assert progress(complete_native()).complete


def test_saved_mask_and_legacy_migration_do_not_invent_physical_pulls() -> None:
    assert saved_physical_mask(record(), AUTH) == PHYSICAL_SAVE_MASK
    assert saved_physical_mask(record(), bytes(16)) is None
    legacy = AUTH + (0x48530000 | 0x4321).to_bytes(4, 'little')
    migrated = merge_acknowledged_levers(legacy, AUTH, 2)
    assert saved_physical_mask(migrated, AUTH) == 0x4321 | (2 << 15)
    assert merge_acknowledged_levers(migrated, AUTH, 2) == migrated
    assert saved_physical_mask(merge_acknowledged_levers(record(), bytes(16), 1), bytes(16)) == 1 << 15


def setup_client(ctx: Any) -> Any:
    client: Any = KirbyAmClient()
    client.initialize_client()
    ctx.slot_data = {'goal': 5, 'full_completion_version': 1, 'physical_check_save_version': 1}
    ctx.auth = base64.b64encode(AUTH).decode()
    ctx.checked_locations = set(PHYSICAL_IDS)
    ctx.server_locations = set(PHYSICAL_IDS)
    ctx.finished_game = False
    ctx.items_received = [SimpleNamespace(item=item, location=100, player=1) for item in REQUIRED_ITEM_IDS]
    client._health_rom_auth = AUTH
    client._hub_connection_received_items_ready = True
    client._hub_connection_received_items_socket = ctx.server.socket
    client._lever_checked_session = client._authenticated_session_key(ctx)
    client._post_clear_player_task_active = AsyncMock(return_value=True)
    return client


@pytest.mark.asyncio
@pytest.mark.parametrize('save_id', [0, 1, 2])
async def test_goal_complete_after_ack_dedup_and_reconnect(mock_bizhawk_context: Any, save_id: int) -> None:
    ctx = mock_bizhawk_context
    client = setup_client(ctx)
    values = complete_native(save_id) + [record(), bytes([6])]
    with patch('worlds.kirbyam.client.bizhawk.guarded_read', new_callable=AsyncMock) as read, \
            patch.object(client, '_display_client_message', new_callable=AsyncMock):
        read.side_effect = [values, [], values]
        await client._maybe_report_goal(ctx)
        await client._maybe_report_goal(ctx)
        ctx.send_msgs.assert_awaited_once_with([{'cmd': 'StatusUpdate', 'status': ClientStatus.CLIENT_GOAL}])
        assert read.call_args_list[0].args[2][1] == (FULL_COMPLETION_MARKER_OFFSET, FULL_COMPLETION_MARKER, 'ROM')
        # New connection can finish without replaying the final boss.
        ctx.send_msgs.reset_mock()
        client = setup_client(ctx)
        read.side_effect = [values, []]
        await client._maybe_report_goal(ctx)
        ctx.send_msgs.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize('missing', sorted(PHYSICAL_IDS))
async def test_every_physical_ack_required(mock_bizhawk_context: Any, missing: int) -> None:
    ctx = mock_bizhawk_context
    client = setup_client(ctx)
    ctx.checked_locations.remove(missing)
    client._native_goal_signal_seen = True
    with patch('worlds.kirbyam.client.bizhawk.guarded_read', new_callable=AsyncMock) as read:
        await client._maybe_report_goal(ctx, ai_state_override=10000)
        read.assert_not_awaited()
    ctx.send_msgs.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize('case', ['no_version', 'bool_version', 'history', 'foreign_auth', 'missing_item',
                                  'inactive_check', 'marker', 'short', 'foreign_save', 'physical',
                                  'rewind', 'menu', 'credits'])
async def test_completion_fail_closed(mock_bizhawk_context: Any, case: str) -> None:
    ctx = mock_bizhawk_context
    client = setup_client(ctx)
    values = complete_native() + [record(), bytes([6])]
    if case == 'no_version':
        del ctx.slot_data['full_completion_version']
    if case == 'bool_version':
        ctx.slot_data['full_completion_version'] = True
    if case == 'history':
        client._hub_connection_received_items_ready = False
    if case == 'foreign_auth':
        ctx.auth = 'different'
    if case == 'missing_item':
        ctx.items_received.pop()
    if case == 'inactive_check':
        ctx.server_locations.remove(next(iter(PHYSICAL_IDS)))
    if case == 'menu':
        client._post_clear_player_task_active.return_value = False
    if case == 'credits':
        values[6] = (0x20).to_bytes(4, 'little')
    if case == 'short':
        values[0] = b''
    if case == 'foreign_save':
        values[7] = bytes(20)
    if case == 'physical':
        values[7] = record(PHYSICAL_SAVE_MASK & ~(1 << 15))
    with patch('worlds.kirbyam.client.bizhawk.guarded_read', new_callable=AsyncMock) as read:
        read.side_effect = [None if case == 'marker' else values, None if case == 'rewind' else []]
        await client._maybe_report_goal(ctx)
    ctx.send_msgs.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize('change', ['socket', 'slot', 'seed', 'connector', 'slot_data', 'history'])
async def test_session_change_during_read_cannot_finish(mock_bizhawk_context: Any, change: str) -> None:
    ctx = mock_bizhawk_context
    client = setup_client(ctx)

    async def read(*args: Any) -> list[bytes]:
        if change == 'socket':
            ctx.server.socket = SimpleNamespace(closed=False)
        elif change == 'connector':
            ctx.bizhawk_ctx = object()
        elif change == 'slot_data':
            ctx.slot_data = dict(ctx.slot_data)
        elif change == 'history':
            ctx.items_received = []
        elif change == 'seed':
            ctx.server_seed_name = 'new'
        else:
            ctx.slot = 2
        return complete_native() + [record(), bytes([6])]
    with patch('worlds.kirbyam.client.bizhawk.guarded_read', side_effect=read):
        await client._maybe_report_goal(ctx)
    ctx.send_msgs.assert_not_awaited()


def test_goal_description() -> None:
    result = _run_goal_command({'goal': 5, 'full_completion_version': 1})
    assert '272 native rooms' in result[0]
    assert 'Vitality ownership and Goal Games are not required' in result[0]


@pytest.mark.asyncio
@pytest.mark.parametrize('race', [None, 'owner', 'task', 'credits'])
async def test_real_player_evidence_reaches_final_guard(
    completed_save: Any, mock_bizhawk_context: Any, race: str | None,
) -> None:
    from ..completion import NATIVE_READS, PHYSICAL_SAVE_ADDRESS
    _unused, _ctx, memory, hp, owner, task, _header = completed_save
    ctx = mock_bizhawk_context
    client = setup_client(ctx)
    del client._post_clear_player_task_active  # Exercise shipping helper, not the ordinary mock.
    for (address, _size, _domain), value in zip(NATIVE_READS, complete_native()):
        memory[address] = value
    memory[hp] = bytes([6])
    memory[PHYSICAL_SAVE_ADDRESS] = record()
    memory[0xF00000] = AUTH
    memory[FULL_COMPLETION_MARKER_OFFSET] = FULL_COMPLETION_MARKER
    memory[0x0203B040] = (0x4B41504D).to_bytes(4, 'little')
    final_guards = []

    async def guarded(_ctx: Any, reads: Any, guards: Any) -> list[bytes] | None:
        if not reads:
            final_guards.extend(guards)
            if race == 'owner':
                memory[owner] = bytes(4)
            elif race == 'task':
                memory[task] = bytes(20)
            elif race == 'credits':
                memory[0x0203AD10] = (0x20).to_bytes(4, 'little')
        if any(bytes(memory.get(address, b'')) != expected for address, expected, _domain in guards):
            return None
        return [bytes(memory[address]) for address, _size, _domain in reads]

    with patch('worlds.kirbyam.client.bizhawk.guarded_read', side_effect=guarded), \
            patch.object(client, '_display_client_message', new_callable=AsyncMock):
        await client._maybe_report_goal(ctx)
    assert {owner, task, 0x03003A58} <= {address for address, _value, _domain in final_guards}
    assert ctx.send_msgs.await_count == (1 if race is None else 0)


@pytest.mark.asyncio
@pytest.mark.parametrize('race', [None, 'socket', 'slot', 'invalid_file', 'guard'])
async def test_acknowledged_lever_restore_uses_guarded_native_record(
    mock_bizhawk_context: Any, race: str | None,
) -> None:
    from ..completion import PHYSICAL_SAVE_ADDRESS, SAVE_ID_ADDRESS
    ctx = mock_bizhawk_context
    client = setup_client(ctx)
    previous = record(0x1234)
    save = (2 if race != 'invalid_file' else 3).to_bytes(2, 'little')

    async def read(*_args: Any) -> list[bytes] | None:
        if race == 'socket':
            ctx.server.socket = SimpleNamespace(closed=False)
        elif race == 'slot':
            ctx.slot = 2
        return None if race == 'guard' else [previous, save]

    with patch('worlds.kirbyam.client.bizhawk.guarded_read', side_effect=read), \
            patch('worlds.kirbyam.client.bizhawk.guarded_write', new_callable=AsyncMock) as write:
        await client._reconcile_lever_activations(ctx)
    if race is not None:
        write.assert_not_awaited()
    else:
        writes, guards = write.call_args.args[1:]
        assert writes == [(PHYSICAL_SAVE_ADDRESS, record(0x1234 | (15 << 15)), 'System Bus')]
        assert (SAVE_ID_ADDRESS, save, 'System Bus') in guards
        assert (PHYSICAL_SAVE_ADDRESS, previous, 'System Bus') in guards
        assert (0xF00000, AUTH, 'ROM') in guards
        assert (FULL_COMPLETION_MARKER_OFFSET, FULL_COMPLETION_MARKER, 'ROM') in guards
