"""Incoming DeathLink replay suppression belongs to the authenticated slot."""
import pytest

from ..client import KirbyAmClient
from .test_deathlink_delivery import deathlink_session  # noqa: F401


def packet(timestamp=100.0):
    return {"tags": ["DeathLink"], "data": {"time": timestamp, "source": "Isolated peer"}}


def set_playable_runtime(client, box, hp, state):
    """A live player task distinguishes a completed save from ending screens."""
    box.memory[client._native_addr("ai_kirby_state_native")] = state.to_bytes(4, "little")
    if state == 300:
        return
    task = 0x03001A40
    header = bytearray(20)
    header[2:4] = (0x19A0).to_bytes(2, "little")
    header[4:6] = (0x1A54).to_bytes(2, "little")
    header[6:8] = (0x3A58).to_bytes(2, "little")
    header[8:12] = (0x0803EE19).to_bytes(4, "little")
    header[16:18] = (0x3000).to_bytes(2, "little")
    box.memory[hp - 0x34] = task.to_bytes(4, "little")
    box.memory[task] = bytes(header)
    box.memory[0x03003A58] = b"\0"
    box.memory[client._native_addr("current_room_native")] = (101).to_bytes(2, "little")
    box.memory[hp - 0xA0] = (101).to_bytes(2, "little")
    box.memory[client._native_addr("demo_playback_flags_native")] = bytes(4)


@pytest.mark.asyncio
@pytest.mark.parametrize("native_state", [300, 9999, 10000])
async def test_same_slot_reconnect_does_not_repeat_native_death(deathlink_session, native_state):
    client, ctx, box, hp, display = deathlink_session
    set_playable_runtime(client, box, hp, native_state)
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


@pytest.mark.asyncio
@pytest.mark.parametrize("native_state", [9999, 10000])
@pytest.mark.parametrize("credits_flags", [0x20, 0x40])
async def test_completed_save_credits_defer_death_and_item_delivery(
    deathlink_session, native_state, credits_flags
):
    client, ctx, box, hp, display = deathlink_session
    set_playable_runtime(client, box, hp, native_state)
    demo = client._native_addr("demo_playback_flags_native")
    box.memory[demo] = credits_flags.to_bytes(4, "little")
    client.on_package(ctx, "Bounced", packet())
    await client.game_watcher(ctx)
    assert box.memory[hp] == b"\3"
    assert client._incoming_death_link_pending
    assert not box.offers
    # Returning to playable completed-save state applies the death first.
    box.memory[demo] = bytes(4)
    await client.game_watcher(ctx)
    assert box.memory[hp] == b"\0"
    assert not box.offers
    box.memory[hp] = b"\3"
    await client.game_watcher(ctx)
    assert box.offers == [3860018]
    box.consume()
    await client.game_watcher(ctx)
    assert box.applied == [3860018]
    assert client._receipt_journal.acknowledged('[3860018,3960301,1,0]')
    ctx.send_death.assert_not_awaited()
