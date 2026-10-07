"""ROM-to-client transition-attempt telemetry contract tests."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from ..client import KirbyAmClient
from ..data import data


def _event(sequence: int, source: int, destination: int, method: int, allowed: bool, reason: int) -> bytes:
    metadata = (method & 0xF) | (int(allowed) << 4) | ((reason & 0xF) << 5)
    return b"".join((
        sequence.to_bytes(4, "little"),
        ((source << 16) | destination).to_bytes(4, "little"),
        metadata.to_bytes(4, "little"),
    ))


@pytest.mark.asyncio
async def test_transition_event_logs_allowed_and_denied_fields(mock_bizhawk_context: Any) -> None:
    client = KirbyAmClient()
    client.initialize_client()
    mock_bizhawk_context.slot_data["starting_area_key_bitfield"] = 0
    client._last_transition_event_counter = 4
    ring_addr = 0x0203B0C8

    async def read(_ctx: Any, requests: Any) -> list[bytes]:
        address, size, _domain = requests[0]
        if address == 0x0203B130:
            return [0x54524E31.to_bytes(4, "little"), (8).to_bytes(4, "little")]
        sequence = ((address - ring_addr) // 12)
        if sequence == 5 % 8:
            return [_event(5, 0x0100, 0x0200, 1, False, 2)]
        if sequence == 6 % 8:
            return [_event(6, 0x0200, 0x0201, 0, True, 0)]
        if sequence == 7 % 8:
            return [_event(7, 0x0201, 0x0202, 4, True, 0)]
        if sequence == 0:
            return [_event(8, 0x0202, 0x0203, 3, True, 0)]
        return [bytes(size)]

    with patch.dict(data.native_ram_addresses, {
        "transition_event_counter_runtime": 0x0203B0C4,
        "transition_event_ring_runtime": ring_addr,
        "transition_event_telemetry_cookie_runtime": 0x0203B130,
    }, clear=False), patch(
        "worlds.kirbyam.client.bizhawk.read", new_callable=AsyncMock, side_effect=read
    ), patch("CommonClient.logger") as logger:
        await client._poll_transition_attempt_events(mock_bizhawk_context)

    assert logger.info.call_count == 4
    denied = logger.info.call_args_list[0]
    assert denied.args[1:] == ("denied", "warp star", 0x0100, 0x0200, "missing destination Area Key")
    allowed = logger.info.call_args_list[1]
    assert allowed.args[1:] == ("allowed", "unclassified transition", 0x0200, 0x0201, "same-area allowance")
    mirror_shard = logger.info.call_args_list[2]
    assert mirror_shard.args[1:3] == ("allowed", "Mirror Shard")
    unclassified = logger.info.call_args_list[3]
    assert unclassified.args[1:3] == ("allowed", "unclassified method 3")
    assert all(call.kwargs["extra"] == {"NoStream": True, "skip_gui": True}
               for call in logger.info.call_args_list)
    assert client._last_transition_event_counter == 8


@pytest.mark.asyncio
async def test_missing_area_key_shows_destination_specific_bizhawk_notice(mock_bizhawk_context: Any) -> None:
    client = KirbyAmClient()
    client.initialize_client()
    mock_bizhawk_context.slot_data["starting_area_key_bitfield"] = 0
    client._last_transition_event_counter = 0
    client._room_area_id_by_doors_idx = {77: 4}
    ring_addr = 0x0203B0C8
    destination_room = 0x0200

    async def read(_ctx: Any, requests: Any) -> list[bytes]:
        if len(requests) == 2:
            return [0x54524E31.to_bytes(4, "little"), (1).to_bytes(4, "little")]
        address, size, _domain = requests[0]
        if address == ring_addr + 12:
            return [_event(1, 0x0100, destination_room, 1, False, 2)]
        if address == 0x009331AC + destination_room * 0x28 + 0x24:
            return [(77).to_bytes(2, "little")]
        return [bytes(size)]

    with patch.dict(data.native_ram_addresses, {
        "transition_event_counter_runtime": 0x0203B0C4,
        "transition_event_ring_runtime": ring_addr,
        "transition_event_telemetry_cookie_runtime": 0x0203B130,
    }, clear=False), patch(
        "worlds.kirbyam.client.bizhawk.read", new_callable=AsyncMock, side_effect=read
    ), patch(
        "worlds.kirbyam.client.bizhawk.display_message", new_callable=AsyncMock
    ) as display:
        await client._poll_transition_attempt_events(mock_bizhawk_context)

    display.assert_awaited_once_with(
        mock_bizhawk_context.bizhawk_ctx,
        "You need the Mustard Mountain Area Key.",
    )


@pytest.mark.asyncio
async def test_allowed_transition_never_shows_area_key_notice(mock_bizhawk_context: Any) -> None:
    client = KirbyAmClient()
    client.initialize_client()
    mock_bizhawk_context.slot_data["starting_area_key_bitfield"] = 0
    client._last_transition_event_counter = 0
    ring_addr = 0x0203B0C8

    async def read(_ctx: Any, requests: Any) -> list[bytes]:
        if len(requests) == 2:
            return [0x54524E31.to_bytes(4, "little"), (1).to_bytes(4, "little")]
        address, size, _domain = requests[0]
        if address == ring_addr + 12:
            return [_event(1, 0x0100, 0x0200, 1, True, 3)]
        return [bytes(size)]

    with patch.dict(data.native_ram_addresses, {
        "transition_event_counter_runtime": 0x0203B0C4,
        "transition_event_ring_runtime": ring_addr,
        "transition_event_telemetry_cookie_runtime": 0x0203B130,
    }, clear=False), patch(
        "worlds.kirbyam.client.bizhawk.read", new_callable=AsyncMock, side_effect=read
    ), patch(
        "worlds.kirbyam.client.bizhawk.display_message", new_callable=AsyncMock
    ) as display:
        await client._poll_transition_attempt_events(mock_bizhawk_context)

    display.assert_not_awaited()


@pytest.mark.asyncio
async def test_repeated_blocked_exit_notice_is_rate_limited(mock_bizhawk_context: Any) -> None:
    client = KirbyAmClient()
    client.initialize_client()
    mock_bizhawk_context.slot_data["starting_area_key_bitfield"] = 0
    client._last_transition_event_counter = 0
    client._room_area_id_by_doors_idx = {77: 4}
    ring_addr = 0x0203B0C8
    destination_room = 0x0200

    async def read(_ctx: Any, requests: Any) -> list[bytes]:
        if len(requests) == 2:
            return [0x54524E31.to_bytes(4, "little"), (2).to_bytes(4, "little")]
        address, size, _domain = requests[0]
        if address == ring_addr + 12:
            return [_event(1, 0x0100, destination_room, 1, False, 2)]
        if address == ring_addr + 24:
            return [_event(2, 0x0100, destination_room, 0, False, 2)]
        if address == 0x009331AC + destination_room * 0x28 + 0x24:
            return [(77).to_bytes(2, "little")]
        return [bytes(size)]

    with patch.dict(data.native_ram_addresses, {
        "transition_event_counter_runtime": 0x0203B0C4,
        "transition_event_ring_runtime": ring_addr,
        "transition_event_telemetry_cookie_runtime": 0x0203B130,
    }, clear=False), patch(
        "worlds.kirbyam.client.bizhawk.read", new_callable=AsyncMock, side_effect=read
    ), patch("worlds.kirbyam.client.time.monotonic", side_effect=(100.0, 100.5)), patch(
        "worlds.kirbyam.client.bizhawk.display_message", new_callable=AsyncMock
    ) as display:
        await client._poll_transition_attempt_events(mock_bizhawk_context)

    display.assert_awaited_once_with(
        mock_bizhawk_context.bizhawk_ctx,
        "You need the Mustard Mountain Area Key.",
    )


@pytest.mark.asyncio
async def test_transition_event_counter_baseline_and_reconnect_replay(mock_bizhawk_context: Any) -> None:
    client = KirbyAmClient()
    client.initialize_client()
    mock_bizhawk_context.slot_data["starting_area_key_bitfield"] = 0
    with patch.dict(data.native_ram_addresses, {
        "transition_event_counter_runtime": 0x0203B0C4,
        "transition_event_ring_runtime": 0x0203B0C8,
        "transition_event_telemetry_cookie_runtime": 0x0203B130,
    }, clear=False), patch(
        "worlds.kirbyam.client.bizhawk.read", new_callable=AsyncMock,
        return_value=[0x54524E31.to_bytes(4, "little"), (9).to_bytes(4, "little")],
    ), patch("CommonClient.logger") as logger:
        await client._poll_transition_attempt_events(mock_bizhawk_context)
        assert client._last_transition_event_counter == 9
        assert logger.info.call_count == 0

        # A reconnect resets unrelated watcher state but retains the log cursor,
        # so event 10 emitted while disconnected is replayed exactly once.
        client._last_transition_event_counter = 9
        client._reset_reconnect_transient_state()
        assert client._last_transition_event_counter == 9

        async def replay_read(_ctx: Any, requests: Any) -> list[bytes]:
            address, _size, _domain = requests[0]
            if address == 0x0203B130:
                return [0x54524E31.to_bytes(4, "little"), (10).to_bytes(4, "little")]
            return [_event(10, 0x0100, 0x0200, 2, False, 2)]

        with patch("worlds.kirbyam.client.bizhawk.read", new_callable=AsyncMock, side_effect=replay_read):
            await client._poll_transition_attempt_events(mock_bizhawk_context)
            await client._poll_transition_attempt_events(mock_bizhawk_context)
        assert client._last_transition_event_counter == 10
        logger.info.assert_called_once()


@pytest.mark.asyncio
async def test_transition_event_poller_ignores_rom_without_telemetry_cookie(mock_bizhawk_context: Any) -> None:
    client = KirbyAmClient()
    client.initialize_client()
    mock_bizhawk_context.slot_data["starting_area_key_bitfield"] = 0
    with patch.dict(data.native_ram_addresses, {
        "transition_event_counter_runtime": 0x0203B0C4,
        "transition_event_ring_runtime": 0x0203B0C8,
        "transition_event_telemetry_cookie_runtime": 0x0203B130,
    }, clear=False), patch(
        "worlds.kirbyam.client.bizhawk.read", new_callable=AsyncMock,
        return_value=[(0).to_bytes(4, "little"), (123).to_bytes(4, "little")],
    ) as mock_read, patch("CommonClient.logger") as logger:
        await client._poll_transition_attempt_events(mock_bizhawk_context)

    mock_read.assert_awaited_once()
    logger.info.assert_not_called()
    assert client._last_transition_event_counter is None


def test_rom_transition_telemetry_ring_is_sequence_tagged_and_debounced() -> None:
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "kirby_ap_payload" / "ap_payload.c").read_text(
        encoding="utf-8"
    )
    assert "AP_TRANSITION_EVENT_RING_SLOTS 8u" in source
    assert "AP_TRANSITION_EVENT_LAST_SIGNATURE" in source
    assert "(frame - AP_TRANSITION_EVENT_LAST_FRAME) < 30u" in source
    assert "AP_TRANSITION_EVENT_COUNTER = counter" in source
