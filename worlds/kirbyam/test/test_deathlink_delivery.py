"""DeathLink watcher ordering, without emulator or native-save writes."""
from contextlib import ExitStack
from unittest.mock import AsyncMock, patch

import pytest
from NetUtils import NetworkItem

from .test_receipt_journal import make_client, tick
from .test_reset_counter_gaps import Mailbox


@pytest.fixture
def deathlink_session(mock_bizhawk_context):
    ctx = mock_bizhawk_context
    ctx.server_seed_name = 'deathlink-ordering'
    ctx.items_received = [NetworkItem(3860018, 3960301, 1)]
    client = make_client(ctx)
    client._death_link_enabled = True
    client._watcher_server_ready = True
    client._ram_state_loaded = True
    box = Mailbox(client)
    hp = client._native_addr('kirby_hp_native')
    box.memory[hp] = bytes([3])
    box.memory[client._native_addr('ai_kirby_state_native')] = (300).to_bytes(4, 'little')
    display = AsyncMock()
    # Keep actual watcher, gameplay/HP gate, DeathLink write, and delivery/ACK
    # paths. Isolate unrelated polling and already-tested ownership reconciliation.
    unrelated = (
        '_sync_death_link_setting', '_sync_enemy_copy_ability_runtime_config',
        '_sync_challenge_runtime_config', '_sync_starting_kirby_color_runtime_config',
        '_log_boss_shard_debug_window', '_reconcile_native_shard_ownership',
        '_reconcile_native_map_ownership', '_reconcile_vitality_ownership',
        '_enforce_no_extra_lives', '_enforce_health_range', '_poll_saved_chest_locations',
        '_poll_boss_defeat_locations', '_poll_major_chest_locations',
        '_poll_minor_chest_locations', '_poll_vitality_chest_locations',
        '_poll_sound_player_chest_locations', '_poll_hub_switch_locations',
        '_poll_lever_locations', '_poll_area_visit_locations', '_poll_room_sanity_locations',
        '_poll_room_entry_logging', '_probe_boss_defeat_candidates',
        '_probe_unsafe_delivery_candidates', '_poll_enemy_ability_reroll_events',
        '_maybe_report_goal',
    )
    with ExitStack() as stack:
        for name in unrelated:
            stack.enter_context(patch.object(client, name, new_callable=AsyncMock))
        stack.enter_context(patch.object(client, '_health_protocol_ready', AsyncMock(return_value=True)))
        stack.enter_context(patch('worlds.kirbyam.client.bizhawk.read', side_effect=box.read))
        stack.enter_context(patch('worlds.kirbyam.client.bizhawk.write', side_effect=box.write))
        stack.enter_context(patch('worlds.kirbyam.client.bizhawk.display_message', display))
        yield client, ctx, box, hp, display


@pytest.mark.asyncio
@pytest.mark.parametrize('late', [False, True])
async def test_deathlink_blocks_fresh_offer_until_alive_tick(deathlink_session, late):
    client, ctx, box, hp, display = deathlink_session
    if late:
        async def queue_during_poll(_ctx):
            client._incoming_death_link_pending = True
        client._poll_saved_chest_locations.side_effect = queue_during_poll
    else:
        client._incoming_death_link_pending = True
    await client.game_watcher(ctx)
    assert not box.offers
    assert not client._delivery_pending
    assert client._delivered_item_index == 0
    if late:
        client._poll_saved_chest_locations.side_effect = None
        await client.game_watcher(ctx)
    assert box.memory[hp] == bytes([0])
    await client.game_watcher(ctx)
    assert not box.offers
    # Respawn supplies a fresh alive snapshot; the deferred item is not lost.
    box.memory[hp] = bytes([3])
    await client.game_watcher(ctx)
    assert box.offers == [3860018]
    box.consume()
    await client.game_watcher(ctx)
    assert client._receipt_journal.acknowledged('[3860018,3960301,1,0]')
    assert box.applied == [3860018]


@pytest.mark.asyncio
@pytest.mark.parametrize('hp_value', [0, -1, -128])
@pytest.mark.parametrize('ack_ready', [False, True])
async def test_dead_watcher_retains_pending_offer_and_processes_ack(deathlink_session, hp_value, ack_ready):
    client, ctx, box, hp, display = deathlink_session
    await tick(client, ctx, box, display)
    assert box.offers == [3860018]
    if ack_ready:
        box.consume()
    box.memory[hp] = bytes([hp_value & 255])
    client._incoming_death_link_pending = True
    await client.game_watcher(ctx)
    assert box.offers == [3860018]
    assert box.memory[hp] == bytes([hp_value & 255])
    assert client._delivery_pending is not ack_ready
    if not ack_ready:
        box.consume()  # The payload can finish an already offered item while dead.
        await client.game_watcher(ctx)
    assert not client._delivery_pending
    assert box.applied == [3860018]
    client._reset_reconnect_transient_state()
    await client.game_watcher(ctx)
    assert box.offers == [3860018]


@pytest.mark.asyncio
@pytest.mark.parametrize('ack_ready', [False, True])
async def test_pending_mailbox_survives_deathlink_tick(deathlink_session, ack_ready):
    client, ctx, box, hp, display = deathlink_session
    await tick(client, ctx, box, display)
    if ack_ready:
        box.consume()
    ctx.items_received.append(NetworkItem(3860019, 3960302, 1))
    client._incoming_death_link_pending = True
    await client.game_watcher(ctx)
    assert box.memory[hp] == bytes([0])
    assert client._delivered_item_index == int(ack_ready)
    assert box.offers == [3860018]  # Process ACK without offering the next item.
    if not ack_ready:
        assert client._delivery_pending
        box.consume()
        await client.game_watcher(ctx)
        assert client._delivered_item_index == 1
        assert box.offers == [3860018]
