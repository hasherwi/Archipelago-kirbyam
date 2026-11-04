"""Completed saves remain playable without treating stale ending RAM as gameplay."""
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from ..client import KirbyAmClient


@pytest.fixture
def completed_save():
    client = KirbyAmClient()
    client.initialize_client()
    ctx = SimpleNamespace(bizhawk_ctx=object())
    hp = client._native_addr("kirby_hp_native")
    owner = hp - 0x34
    task = 0x03001A40
    header = bytearray(20)
    header[2:4] = (0x19A0).to_bytes(2, "little")
    header[4:6] = (0x1A54).to_bytes(2, "little")
    header[6:8] = (0x3A58).to_bytes(2, "little")
    header[8:12] = (0x0803EE19).to_bytes(4, "little")
    header[16:18] = (0x3000).to_bytes(2, "little")
    memory = {
        client._native_addr("ai_kirby_state_native"): (9999).to_bytes(4, "little"),
        client._native_addr("demo_playback_flags_native"): bytes(4),
        hp: bytes([10]),
        owner: task.to_bytes(4, "little"),
        client._native_addr("current_room_native"): (101).to_bytes(2, "little"),
        hp - 0xA0: (101).to_bytes(2, "little"),
        task: header,
        0x03003A58: b"\0",
    }

    async def read(_ctx, requests):
        return [bytes(memory.get(address, bytes(size)))[:size] for address, size, _domain in requests]

    with patch("worlds.kirbyam.client.bizhawk.read", side_effect=read):
        yield client, ctx, memory, hp, owner, task, header


@pytest.mark.asyncio
@pytest.mark.parametrize("state", [9999, 10000])
@pytest.mark.parametrize("room", [101, 801, 909, 919])
@pytest.mark.parametrize("ewram_payload", [False, True])
async def test_completed_save_resumes_gameplay(completed_save, state, room, ewram_payload):
    client, ctx, memory, hp, owner, task, header = completed_save
    memory[client._native_addr("ai_kirby_state_native")] = state.to_bytes(4, "little")
    memory[client._native_addr("current_room_native")] = room.to_bytes(2, "little")
    memory[hp - 0xA0] = room.to_bytes(2, "little")
    if ewram_payload:
        header[18] = 0x10
        memory[0x02000000 + (0x3A58 << 2)] = b"\0"
    assert await client._runtime_gameplay_state(ctx) == (True, "gameplay_active", state)


@pytest.mark.asyncio
@pytest.mark.parametrize("fault", [
    "missing_task", "unaligned_task", "out_of_range_task", "destroyed_task", "inactive_task",
    "wrong_priority", "wrong_player", "missing_payload", "wrong_room", "no_room", "no_links",
    "invalid_iwram_payload", "short_header",
])
async def test_stale_or_invalid_player_state_defers_delivery(completed_save, fault):
    client, ctx, memory, hp, owner, task, header = completed_save
    if fault == "missing_task":
        memory[owner] = bytes(4)
    elif fault == "unaligned_task":
        memory[owner] = (task + 1).to_bytes(4, "little")
    elif fault == "out_of_range_task":
        memory[owner] = (0x0803EE18).to_bytes(4, "little")
    elif fault == "destroyed_task":
        header[8:12] = bytes(4)
    elif fault == "inactive_task":
        header[18] = 1
    elif fault == "wrong_priority":
        header[16:18] = bytes(2)
    elif fault == "wrong_player":
        memory[0x03003A58] = b"\1"
    elif fault == "missing_payload":
        header[6:8] = bytes(2)
    elif fault == "wrong_room":
        memory[hp - 0xA0] = (804).to_bytes(2, "little")
    elif fault == "no_room":
        memory[client._native_addr("current_room_native")] = bytes(2)
    elif fault == "no_links":
        header[2:6] = bytes(4)
    elif fault == "invalid_iwram_payload":
        header[6:8] = (0xFFFF).to_bytes(2, "little")
    elif fault == "short_header":
        memory[task] = bytes(4)
    assert await client._runtime_gameplay_state(ctx) == (False, "non_gameplay_goal_clear", 9999)


@pytest.mark.asyncio
@pytest.mark.parametrize("state", [9999, 10000])
async def test_completed_save_demo_still_defers(completed_save, state):
    client, ctx, memory, hp, owner, task, header = completed_save
    memory[client._native_addr("ai_kirby_state_native")] = state.to_bytes(4, "little")
    memory[client._native_addr("demo_playback_flags_native")] = (0x10).to_bytes(4, "little")
    assert await client._runtime_gameplay_state(ctx) == (False, "non_gameplay_title_demo", state)


@pytest.mark.asyncio
@pytest.mark.parametrize("state", [9999, 10000])
@pytest.mark.parametrize("flags", [0x20, 0x40, 0x60])
async def test_replay_credits_with_live_player_still_defer(completed_save, state, flags):
    client, ctx, memory, hp, owner, task, header = completed_save
    memory[client._native_addr("ai_kirby_state_native")] = state.to_bytes(4, "little")
    memory[client._native_addr("demo_playback_flags_native")] = flags.to_bytes(4, "little")
    memory[client._native_addr("current_room_native")] = (919).to_bytes(2, "little")
    memory[hp - 0xA0] = (919).to_bytes(2, "little")
    assert await client._runtime_gameplay_state(ctx) == (False, "non_gameplay_goal_clear", state)


@pytest.mark.asyncio
async def test_completed_save_death_remains_visible_to_deathlink(completed_save):
    client, ctx, memory, hp, owner, task, header = completed_save
    memory[hp] = b"\0"
    assert await client._runtime_gameplay_state(ctx) == (False, "non_gameplay_kirby_dead", 9999)


@pytest.mark.asyncio
@pytest.mark.parametrize("changed", ["owner", "callback", "credits", "hp", "global_room", "player_room"])
async def test_task_destruction_between_reads_defers(completed_save, changed):
    client, ctx, memory, hp, owner, task, header = completed_save
    calls = 0

    async def read(_ctx, requests):
        nonlocal calls
        calls += 1
        if calls == 4:
            if changed == "owner":
                memory[owner] = bytes(4)
            elif changed == "callback":
                header[8:12] = bytes(4)
            elif changed == "credits":
                memory[client._native_addr("demo_playback_flags_native")] = (0x20).to_bytes(4, "little")
            elif changed == "hp":
                memory[hp] = b"\0"
            elif changed == "global_room":
                memory[client._native_addr("current_room_native")] = (804).to_bytes(2, "little")
            else:
                memory[hp - 0xA0] = (804).to_bytes(2, "little")
        return [bytes(memory.get(address, bytes(size)))[:size] for address, size, _domain in requests]

    with patch("worlds.kirbyam.client.bizhawk.read", side_effect=read):
        assert await client._runtime_gameplay_state(ctx) == (False, "non_gameplay_goal_clear", 9999)
