"""DeathLink transitions must run through the watcher gameplay gate (#975)."""
from typing import Any

import pytest

from . import test_deathlink_delivery as delivery

deathlink_session = delivery.deathlink_session


@pytest.mark.asyncio
@pytest.mark.parametrize('hp_value', [0, -1, -128])
async def test_watcher_reports_local_death_once_and_rearms_after_respawn(deathlink_session: Any, hp_value: int) -> None:
    client, ctx, box, hp, display = deathlink_session
    ctx.items_received = []
    await client.game_watcher(ctx)
    box.memory[hp] = bytes([hp_value & 255])
    for _ in range(3):
        await client.game_watcher(ctx)
    assert ctx.send_death.await_count == 1
    assert not box.offers
    box.memory[hp] = bytes([3])
    await client.game_watcher(ctx)
    box.memory[hp] = bytes([0])
    await client.game_watcher(ctx)
    assert ctx.send_death.await_count == 2


@pytest.mark.asyncio
async def test_watcher_received_death_while_dead_does_not_kill_respawn(deathlink_session: Any) -> None:
    client, ctx, box, hp, display = deathlink_session
    ctx.items_received = []
    await client.game_watcher(ctx)
    box.memory[hp] = bytes([0])
    client._incoming_death_link_pending = True
    await client.game_watcher(ctx)
    assert not client._incoming_death_link_pending
    box.memory[hp] = bytes([3])
    await client.game_watcher(ctx)
    assert box.memory[hp] == bytes([3])
    ctx.send_death.assert_not_awaited()
    box.memory[hp] = bytes([0])
    await client.game_watcher(ctx)
    ctx.send_death.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize('state,demo', [(0, 0), (200, 0), (300, 0x10), (9999, 0), (10000, 0)])
async def test_zero_hp_outside_gameplay_never_sends_deathlink(deathlink_session: Any, state: int, demo: int) -> None:
    client, ctx, box, hp, display = deathlink_session
    ctx.items_received = []
    await client.game_watcher(ctx)
    box.memory[hp] = bytes([0])
    box.memory[client._native_addr('ai_kirby_state_native')] = state.to_bytes(4, 'little')
    box.memory[client._native_addr('demo_playback_flags_native')] = demo.to_bytes(4, 'little')
    await client.game_watcher(ctx)
    ctx.send_death.assert_not_awaited()
    assert not box.offers


@pytest.mark.asyncio
async def test_incoming_link_on_first_tick_does_not_suppress_later_local_death(deathlink_session: Any) -> None:
    client, ctx, box, hp, display = deathlink_session
    ctx.items_received = []
    client._incoming_death_link_pending = True
    await client.game_watcher(ctx)
    assert box.memory[hp] == bytes([0])
    ctx.send_death.assert_not_awaited()
    box.memory[hp] = bytes([3])
    await client.game_watcher(ctx)
    box.memory[hp] = bytes([0])
    await client.game_watcher(ctx)
    ctx.send_death.assert_awaited_once()
