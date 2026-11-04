"""Incoming DeathLink replay suppression belongs to the authenticated slot."""
import pytest

from ..client import KirbyAmClient
from .test_deathlink_delivery import deathlink_session  # noqa: F401


def packet(timestamp=100.0):
    return {"tags": ["DeathLink"], "data": {"time": timestamp, "source": "Isolated peer"}}


@pytest.mark.asyncio
async def test_same_slot_reconnect_does_not_repeat_native_death(deathlink_session):
    client, ctx, box, hp, display = deathlink_session
    ctx.items_received = []
    client.on_package(ctx, "Bounced", packet())
    await client.game_watcher(ctx)
    assert box.memory[hp] == b"\0"
    box.memory[hp] = b"\3"
    await client.game_watcher(ctx)
    server = ctx.server
    ctx.server = None
    await client.game_watcher(ctx)
    assert not client._incoming_death_link_pending
    assert client._last_incoming_death_link_time == 100.0
    ctx.server = server
    client._death_link_enabled = True
    client._reset_reconnect_transient_state()
    client.on_package(ctx, "Connected", {})
    client.on_package(ctx, "ReceivedItems", {"index": 0})
    for timestamp in (100.0, 99.0):
        client.on_package(ctx, "Bounced", packet(timestamp))
        await client.game_watcher(ctx)
        assert box.memory[hp] == b"\3"
    client.on_package(ctx, "Bounced", packet(101.0))
    await client.game_watcher(ctx)
    assert box.memory[hp] == b"\0"
    ctx.send_death.assert_not_awaited()


@pytest.mark.parametrize("field,value", [
    ("server_seed_name", "other-seed"), ("auth", "other-auth"), ("team", 7), ("slot", 8),
])
def test_changed_identity_has_its_own_deathlink_history(mock_bizhawk_context, field, value):
    ctx = mock_bizhawk_context
    client = KirbyAmClient()
    client.initialize_client()
    client._death_link_enabled = True
    client.on_package(ctx, "Bounced", packet())
    client._incoming_death_link_pending = False
    setattr(ctx, field, value)
    client.on_package(ctx, "Bounced", packet(99.0))
    assert client._incoming_death_link_pending
    assert client._last_incoming_death_link_time == 99.0


@pytest.mark.asyncio
async def test_disable_enable_preserves_same_slot_replay_suppression(mock_bizhawk_context):
    ctx = mock_bizhawk_context
    client = KirbyAmClient()
    client.initialize_client()
    client._death_link_enabled = True
    client.on_package(ctx, "Bounced", packet())
    ctx.slot_data["death_link"] = False
    await client._sync_death_link_setting(ctx)
    assert not client._incoming_death_link_pending
    ctx.slot_data["death_link"] = True
    await client._sync_death_link_setting(ctx)
    client.on_package(ctx, "Bounced", packet())
    assert not client._incoming_death_link_pending
    client.on_package(ctx, "Bounced", packet(101.0))
    assert client._incoming_death_link_pending


def test_disconnected_packets_do_not_change_replay_history(mock_bizhawk_context):
    ctx = mock_bizhawk_context
    client = KirbyAmClient()
    client.initialize_client()
    client._death_link_enabled = True
    client.on_package(ctx, "Bounced", packet())
    client._incoming_death_link_pending = False
    ctx.server = None
    client.on_package(ctx, "Bounced", packet(101.0))
    assert not client._incoming_death_link_pending
    assert client._last_incoming_death_link_time == 100.0
