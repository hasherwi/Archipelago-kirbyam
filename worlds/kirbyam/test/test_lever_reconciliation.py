"""Acknowledged physical pulls survive reset without borrowing wall ownership."""
import base64
from unittest.mock import AsyncMock, patch

import pytest

from ..client import KirbyAmClient, _AUTH_TOKEN_SIZE, _normalize_gba_rom_address
from ..data import data


@pytest.fixture
def lever_session(mock_bizhawk_context):
    ctx = mock_bizhawk_context
    client = KirbyAmClient()
    client.initialize_client()
    auth = bytes(range(_AUTH_TOKEN_SIZE))
    client._health_rom_auth = auth
    client._notification_settings_loaded = True
    ctx.auth = base64.b64encode(auth).decode()
    ctx.server_seed_name, ctx.team, ctx.slot = 'lever-seed', 0, 1
    ctx.server_locations = {3960415, 3960416, 3960417, 3960418}
    ctx.checked_locations = {3960415}
    client.on_package(ctx, 'Connected', {})
    lever = client._transport_addr('lever_activation_flags')
    cookie = client._transport_addr('mailbox_init_cookie')
    auth_addr = _normalize_gba_rom_address(data.rom_addresses['gArchipelagoInfo'])
    memory = {(lever, 'System Bus'): bytes(4),
              (cookie, 'System Bus'): (0x4B41504D).to_bytes(4, 'little'),
              (auth_addr, 'ROM'): auth}

    async def read(connector, reads):
        return [memory[address, domain][:length] for address, length, domain in reads]

    async def guarded(connector, writes, guards):
        if any(memory[address, domain] != value for address, value, domain in guards):
            return False
        for address, value, domain in writes:
            memory[address, domain] = value
        return True

    with patch('worlds.kirbyam.client.bizhawk.read', AsyncMock(side_effect=read)) as reads, \
            patch('worlds.kirbyam.client.bizhawk.guarded_write', AsyncMock(side_effect=guarded)) as writes:
        yield client, ctx, memory, lever, cookie, auth_addr, reads, writes


@pytest.mark.asyncio
@pytest.mark.parametrize('bit', range(4))
async def test_reset_reconnect_and_duplicate_pulls(lever_session, bit):
    client, ctx, memory, lever, cookie, auth_addr, reads, writes = lever_session
    ctx.checked_locations = {3960415 + bit}
    await client._reconcile_lever_activations(ctx)
    assert int.from_bytes(memory[lever, 'System Bus'], 'little') == 1 << bit
    await client._poll_lever_locations(ctx)
    ctx.send_msgs.assert_not_awaited()
    # Normal reconnect does not write again or clear physical state.
    client._reset_reconnect_transient_state()
    client.on_package(ctx, 'Connected', {})
    await client._reconcile_lever_activations(ctx)
    assert writes.await_count == 1
    # Reset while the same client stays connected must also restore every tick.
    memory[lever, 'System Bus'] = bytes(4)
    await client._reconcile_lever_activations(ctx)
    assert writes.await_count == 2
    # No writes to native wall bits; all guards accompany the latch write.
    assert writes.call_args.args[1] == [(lever, (1 << bit).to_bytes(4, 'little'), 'System Bus')]
    assert {g[0] for g in writes.call_args.args[2]} == {lever, cookie, auth_addr}


@pytest.mark.asyncio
async def test_only_active_acknowledged_checks_are_restored(lever_session):
    client, ctx, memory, lever, *rest = lever_session
    ctx.checked_locations = {3960415, 3960416, 3960417, 3960418}
    ctx.server_locations = {3960415, 3960417}
    # Preserve an unacknowledged physical pull and unrelated upper transport bits.
    memory[lever, 'System Bus'] = (0x80000008).to_bytes(4, 'little')
    await client._reconcile_lever_activations(ctx)
    assert int.from_bytes(memory[lever, 'System Bus'], 'little') == 0x8000000D


@pytest.mark.asyncio
async def test_wall_items_and_unacknowledged_pulls_do_not_restore(lever_session):
    client, ctx, memory, lever, cookie, auth_addr, reads, writes = lever_session
    ctx.checked_locations = set()
    ctx.items_received = [type('Item', (), {'item': 3860037})()]
    await client._reconcile_lever_activations(ctx)
    reads.assert_not_awaited()
    writes.assert_not_awaited()
    memory[lever, 'System Bus'] = (1).to_bytes(4, 'little')
    await client._poll_lever_locations(ctx)
    ctx.send_msgs.assert_awaited_once_with([{'cmd': 'LocationChecks', 'locations': [3960415]}])
    memory[lever, 'System Bus'] = bytes(4)
    await client._reconcile_lever_activations(ctx)
    assert memory[lever, 'System Bus'] == bytes(4)


@pytest.mark.asyncio
@pytest.mark.parametrize('change', ['seed', 'team', 'slot', 'auth', 'server', 'connector', 'disconnect'])
async def test_session_change_during_read_discards_mask(lever_session, change):
    client, ctx, memory, lever, cookie, auth_addr, reads, writes = lever_session
    original = reads.side_effect

    async def changed(connector, request):
        values = await original(connector, request)
        if change == 'disconnect':
            ctx.server.socket.closed = True
        else:
            attr = {'seed': 'server_seed_name', 'connector': 'bizhawk_ctx'}.get(change, change)
            setattr(ctx, attr, object())
        return values

    reads.side_effect = changed
    await client._reconcile_lever_activations(ctx)
    writes.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize('race', ['pull', 'reset', 'rom'])
async def test_guard_rejects_concurrent_changes_and_retries(lever_session, race):
    client, ctx, memory, lever, cookie, auth_addr, reads, writes = lever_session
    original = writes.side_effect

    async def changed(connector, request, guards):
        address, domain, value = {
            'pull': (lever, 'System Bus', (2).to_bytes(4, 'little')),
            'reset': (cookie, 'System Bus', bytes(4)),
            'rom': (auth_addr, 'ROM', bytes(_AUTH_TOKEN_SIZE)),
        }[race]
        memory[address, domain] = value
        return await original(connector, request, guards)

    writes.side_effect = changed
    await client._reconcile_lever_activations(ctx)
    assert int.from_bytes(memory[lever, 'System Bus'], 'little') == (2 if race == 'pull' else 0)
    writes.side_effect = original
    if race == 'pull':
        await client._reconcile_lever_activations(ctx)
        assert int.from_bytes(memory[lever, 'System Bus'], 'little') == 3
    elif race == 'reset':
        memory[cookie, 'System Bus'] = (0x4B41504D).to_bytes(4, 'little')
        await client._reconcile_lever_activations(ctx)
        assert int.from_bytes(memory[lever, 'System Bus'], 'little') == 1
    else:
        await client._reconcile_lever_activations(ctx)
        assert memory[lever, 'System Bus'] == bytes(4)


@pytest.mark.asyncio
@pytest.mark.parametrize('invalid', ['not_connected', 'uninitialized', 'truncated', 'wrong_auth', 'new_slot'])
async def test_incomplete_or_foreign_state_does_not_write(lever_session, invalid):
    client, ctx, memory, lever, cookie, auth_addr, reads, writes = lever_session
    if invalid == 'not_connected':
        client._lever_checked_session = None
    elif invalid == 'uninitialized':
        memory[cookie, 'System Bus'] = bytes(4)
    elif invalid == 'truncated':
        memory[lever, 'System Bus'] = b'\0'
    elif invalid == 'wrong_auth':
        ctx.auth = 'another ROM'
    else:
        ctx.slot = 2
    await client._reconcile_lever_activations(ctx)
    writes.assert_not_awaited()


@pytest.mark.asyncio
async def test_new_slot_connected_does_not_reuse_previous_mask(lever_session):
    client, ctx, memory, lever, cookie, auth_addr, reads, writes = lever_session
    await client._reconcile_lever_activations(ctx)
    ctx.slot = 2
    ctx.checked_locations = {3960418}
    new_auth = bytes([9]) * _AUTH_TOKEN_SIZE
    ctx.auth = base64.b64encode(new_auth).decode()
    client._health_rom_auth = new_auth
    memory[auth_addr, 'ROM'] = new_auth
    memory[lever, 'System Bus'] = bytes(4)
    client.on_package(ctx, 'Connected', {})
    await client._reconcile_lever_activations(ctx)
    assert int.from_bytes(memory[lever, 'System Bus'], 'little') == 8
