"""Pending ROM reads must not diagnose an ordinary AP disconnect as a bad patch."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from CommonClient import CommonContext
from ..client import KirbyAmClient, bizhawk
from ..hub_protocol import HUB_MARKER, HUB_MARKER_OFFSET
from .test_vitality_protocol import _identity


@pytest.mark.asyncio
@pytest.mark.parametrize('boundary', ['identity', 'hub_before', 'hub_after'])
@pytest.mark.parametrize('change', ['reset', 'close', 'server', 'socket', 'slot', 'slot_data'])
async def test_expired_rom_poll_is_quiet_and_has_no_side_effects(mock_bizhawk_context, boundary, change):
    client = KirbyAmClient()
    client.initialize_client()
    ctx = mock_bizhawk_context
    memory = _identity(client, ctx, 2, 6, 10)
    if boundary == 'hub_before':
        ctx.slot_data['hub_connection_protocol_version'] = 2
        memory[HUB_MARKER_OFFSET, 'ROM'] = HUB_MARKER
    original_server = ctx.server
    original_socket = ctx.server.socket
    original_slot = ctx.slot
    original_auth = ctx.auth
    original_data = ctx.slot_data
    original_team = ctx.team
    original_seed = ctx.server_seed_name
    changed = False

    async def read(_, requests):
        nonlocal changed
        is_identity = any(a == 0xA0 for a, _, _ in requests)
        if not changed and ((boundary == 'identity') == is_identity):
            changed = True
            if change == 'reset':
                CommonContext.reset_server_state(ctx)
            elif change == 'close':
                ctx.server.socket.closed = True
            elif change == 'server':
                ctx.server = SimpleNamespace(socket=SimpleNamespace(closed=False))
            elif change == 'socket':
                ctx.server.socket = SimpleNamespace(closed=False)
            elif change == 'slot':
                ctx.slot += 1
            else:
                ctx.slot_data = dict(ctx.slot_data)
        return [memory[a, domain] for a, _, domain in requests]

    with patch('worlds.kirbyam.client.bizhawk.read', side_effect=read), \
            patch('worlds.kirbyam.client.bizhawk.write', new_callable=AsyncMock) as write, \
            patch('worlds.kirbyam.client.bizhawk.guarded_write', new_callable=AsyncMock) as guarded, \
            patch.object(client, '_log_client') as log, \
            patch.object(client, '_sync_death_link_setting', new_callable=AsyncMock) as sync:
        await client.game_watcher(ctx)
        assert changed
        log.assert_not_called()
        write.assert_not_awaited()
        guarded.assert_not_awaited()
        sync.assert_not_awaited()
        ctx.send_msgs.assert_not_awaited()
        # Re-authenticated subsequent poll can validate the very same ROM.
        ctx.server = original_server
        ctx.server.socket = original_socket
        original_socket.closed = False
        ctx.slot = original_slot
        ctx.auth = original_auth
        ctx.slot_data = original_data
        ctx.team = original_team
        ctx.server_seed_name = original_seed
        assert await client._health_protocol_ready(ctx)


@pytest.mark.asyncio
@pytest.mark.parametrize('disconnect', [False, True])
@pytest.mark.parametrize('error_name', ['RequestFailedError', 'NotConnectedError', 'ConnectorError', 'SyncError'])
async def test_connector_loss_pauses_without_compatibility_error(mock_bizhawk_context, disconnect, error_name):
    client = KirbyAmClient()
    client.initialize_client()
    ctx = mock_bizhawk_context
    memory = _identity(client, ctx)
    client._ram_state_loaded = True
    client._delivery_pending = True

    async def failed_read(_, requests):
        if disconnect:
            CommonContext.reset_server_state(ctx)
        raise getattr(bizhawk, error_name)('Connection reset')

    with patch('worlds.kirbyam.client.bizhawk.read', side_effect=failed_read), \
            patch('worlds.kirbyam.client.bizhawk.write', new_callable=AsyncMock) as write, \
            patch('worlds.kirbyam.client.bizhawk.guarded_write', new_callable=AsyncMock) as guarded, \
            patch.object(client, '_sync_death_link_setting', new_callable=AsyncMock) as sync, \
            patch.object(client, '_log_verbose') as verbose, \
            patch.object(client, '_log_client') as log:
        await client.game_watcher(ctx)
        await client.game_watcher(ctx)
        log.assert_not_called()
        write.assert_not_awaited()
        guarded.assert_not_awaited()
        sync.assert_not_awaited()
        assert verbose.call_count == (0 if disconnect else 1)
    if not disconnect:
        assert client._watcher_requires_bizhawk_resync
        assert not client._ram_state_loaded
        assert not client._delivery_pending

        async def restored_read(_, requests):
            return [memory[a, domain] for a, _, domain in requests]

        with patch('worlds.kirbyam.client.bizhawk.read', side_effect=restored_read):
            assert await client._health_protocol_ready(ctx)


@pytest.mark.asyncio
async def test_real_config_mismatch_still_reports_compatibility_error(mock_bizhawk_context):
    client = KirbyAmClient()
    client.initialize_client()
    ctx = mock_bizhawk_context
    memory = _identity(client, ctx)
    memory[0x15F690, 'ROM'] = bytes(4)

    async def read(_, requests):
        return [memory[a, domain] for a, _, domain in requests]

    with patch('worlds.kirbyam.client.bizhawk.read', side_effect=read), \
            patch.object(client, '_log_client') as log:
        assert not await client._health_protocol_ready(ctx)
    assert log.call_count == 1
    assert 'compatibility check failed' in log.call_args.args[1]
    assert not client._watcher_requires_bizhawk_resync


@pytest.mark.asyncio
async def test_live_auth_change_still_reports_real_mismatch(mock_bizhawk_context):
    client = KirbyAmClient()
    client.initialize_client()
    ctx = mock_bizhawk_context
    memory = _identity(client, ctx)

    async def read(_, requests):
        ctx.auth = 'different-live-auth'
        return [memory[a, domain] for a, _, domain in requests]

    with patch('worlds.kirbyam.client.bizhawk.read', side_effect=read), \
            patch.object(client, '_log_client') as log:
        assert not await client._health_protocol_ready(ctx)
    assert log.call_args.args[-1] == 'ROM authentication changed'
