"""Room-sanity polling tests for native gVisitedDoors -> LocationChecks mapping."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from ..client import KirbyAmClient
from ..data import data


def _room_visit_bytes(*visited_doors_idx: int) -> bytes:
    payload = bytearray(0x120 * 2)
    for doors_idx in visited_doors_idx:
        if 0 <= doors_idx < 0x120:
            offset = doors_idx * 2
            payload[offset:offset + 2] = (0x8000).to_bytes(2, "little")
    return bytes(payload)


@pytest.mark.asyncio
async def test_poll_room_sanity_sends_location_checks_for_visited_doors(mock_bizhawk_context):
    client = KirbyAmClient()
    client.initialize_client()

    mock_bizhawk_context.slot_data["room_sanity"] = True
    mock_bizhawk_context.checked_locations = set()

    room_1_01_data = data.locations["ROOM_SANITY_1_01"]
    room_1_02_data = data.locations["ROOM_SANITY_1_02"]
    room_1_01 = room_1_01_data.location_id
    room_1_02 = room_1_02_data.location_id
    assert room_1_01_data.bit_index is not None
    assert room_1_02_data.bit_index is not None

    with patch.dict(data.native_ram_addresses, {"room_visit_flags_native": 0x02028CA0}, clear=False), \
         patch("worlds.kirbyam.client.bizhawk.read", new_callable=AsyncMock) as mock_read, \
         patch.object(mock_bizhawk_context, "send_msgs", new_callable=AsyncMock) as mock_send:
        # Derive visited bits from current location metadata instead of hard-coding doorsIdx constants.
        mock_read.return_value = [_room_visit_bytes(room_1_01_data.bit_index, room_1_02_data.bit_index)]

        await client._poll_room_sanity_locations(mock_bizhawk_context)

    mock_send.assert_awaited_once_with([
        {"cmd": "LocationChecks", "locations": [room_1_01, room_1_02]}
    ])


@pytest.mark.asyncio
async def test_poll_room_sanity_is_gated_off_when_option_disabled(mock_bizhawk_context):
    client = KirbyAmClient()
    client.initialize_client()

    mock_bizhawk_context.slot_data["room_sanity"] = False

    with patch.dict(data.native_ram_addresses, {"room_visit_flags_native": 0x02028CA0}, clear=False), \
         patch("worlds.kirbyam.client.bizhawk.read", new_callable=AsyncMock) as mock_read, \
         patch.object(mock_bizhawk_context, "send_msgs", new_callable=AsyncMock) as mock_send:
        await client._poll_room_sanity_locations(mock_bizhawk_context)

    mock_read.assert_not_awaited()
    mock_send.assert_not_awaited()


@pytest.mark.asyncio
async def test_poll_room_sanity_dedupes_already_server_acknowledged(mock_bizhawk_context):
    client = KirbyAmClient()
    client.initialize_client()

    mock_bizhawk_context.slot_data["room_sanity"] = True
    room_1_01_data = data.locations["ROOM_SANITY_1_01"]
    room_1_01 = room_1_01_data.location_id
    assert room_1_01_data.bit_index is not None
    mock_bizhawk_context.checked_locations = {room_1_01}

    with patch.dict(data.native_ram_addresses, {"room_visit_flags_native": 0x02028CA0}, clear=False), \
         patch("worlds.kirbyam.client.bizhawk.read", new_callable=AsyncMock) as mock_read, \
         patch.object(mock_bizhawk_context, "send_msgs", new_callable=AsyncMock) as mock_send, \
         patch("CommonClient.logger") as mock_logger:
        mock_read.return_value = [_room_visit_bytes(room_1_01_data.bit_index)]

        await client._poll_room_sanity_locations(mock_bizhawk_context)

    mock_send.assert_not_awaited()
    mock_logger.debug.assert_called_once()
    debug_args = mock_logger.debug.call_args.args
    assert "dedupe suppressed room-sanity LocationChecks" in debug_args[0]
    assert debug_args[1] == [room_1_01]


@pytest.mark.asyncio
async def test_poll_room_sanity_skips_when_address_missing(mock_bizhawk_context):
    client = KirbyAmClient()
    client.initialize_client()

    mock_bizhawk_context.slot_data["room_sanity"] = True

    native_without_room_visits = {
        key: value
        for key, value in data.native_ram_addresses.items()
        if key != "room_visit_flags_native"
    }

    with patch.dict(data.native_ram_addresses, native_without_room_visits, clear=True), \
         patch("worlds.kirbyam.client.bizhawk.read", new_callable=AsyncMock) as mock_read, \
         patch.object(mock_bizhawk_context, "send_msgs", new_callable=AsyncMock) as mock_send:
        await client._poll_room_sanity_locations(mock_bizhawk_context)

    mock_read.assert_not_awaited()
    mock_send.assert_not_awaited()


@pytest.mark.asyncio
async def test_reconnect_room_sanity_resends_once_then_dedupes(mock_bizhawk_context):
    """Reconnect-equivalent room polling should resend once then dedupe after server ack."""
    client = KirbyAmClient()
    client.initialize_client()

    mock_bizhawk_context.slot_data["room_sanity"] = True
    room_1_01_data = data.locations["ROOM_SANITY_1_01"]
    room_1_01 = room_1_01_data.location_id
    assert room_1_01_data.bit_index is not None
    mock_bizhawk_context.checked_locations = set()

    with patch.dict(data.native_ram_addresses, {"room_visit_flags_native": 0x02028CA0}, clear=False), \
         patch("worlds.kirbyam.client.bizhawk.read", new_callable=AsyncMock) as mock_read:
        # First poll: visited in RAM but not on server -> send.
        mock_read.return_value = [_room_visit_bytes(room_1_01_data.bit_index)]
        await client._poll_room_sanity_locations(mock_bizhawk_context)

        # Reconnect-equivalent poll: now server has acknowledged -> dedupe.
        mock_bizhawk_context.checked_locations = {room_1_01}
        mock_read.return_value = [_room_visit_bytes(room_1_01_data.bit_index)]
        await client._poll_room_sanity_locations(mock_bizhawk_context)

    mock_bizhawk_context.send_msgs.assert_awaited_once_with([
        {"cmd": "LocationChecks", "locations": [room_1_01]}
    ])


@pytest.mark.asyncio
async def test_log_room_entry_debug_logs_transitions_and_revisits(mock_bizhawk_context):
    client = KirbyAmClient()
    client.initialize_client()
    client._debug_logging_enabled = True

    with patch.dict(
        data.native_ram_addresses,
        {
            "current_kirby_index_native": 0x0203AD3C,
            "kirbys_native": 0x02020EE0,
        },
        clear=False,
    ), patch.dict(
        data.transport_ram_addresses,
        {"hook_heartbeat": 0x0202C034},
        clear=False,
    ), patch("worlds.kirbyam.client.bizhawk.read", new_callable=AsyncMock) as mock_read, patch(
        "CommonClient.logger"
    ) as mock_logger:
        mock_read.side_effect = [
            [b"\x00", (100).to_bytes(4, "little")],
            [(190).to_bytes(2, "little")],
            [b"\x00", (101).to_bytes(4, "little")],
            [(191).to_bytes(2, "little")],
            [b"\x00", (102).to_bytes(4, "little")],
            [(190).to_bytes(2, "little")],
        ]

        await client._log_room_entry_debug(mock_bizhawk_context)
        await client._log_room_entry_debug(mock_bizhawk_context)
        await client._log_room_entry_debug(mock_bizhawk_context)

    calls = [
        c
        for c in mock_logger.info.call_args_list
        if c.args and isinstance(c.args[0], str) and "room entry detected" in c.args[0]
    ]
    assert len(calls) == 3

    assert calls[0].args[1] == 190

    assert calls[1].args[1] == 191
    assert calls[1].args[4] == 190

    # Revisit of previously seen room should still log as an entry transition.
    assert calls[2].args[1] == 190
    assert calls[2].args[4] == 191


@pytest.mark.asyncio
async def test_log_room_entry_debug_noops_when_debug_disabled(mock_bizhawk_context):
    client = KirbyAmClient()
    client.initialize_client()
    client._debug_logging_enabled = False

    with patch("worlds.kirbyam.client.bizhawk.read", new_callable=AsyncMock) as mock_read, patch(
        "CommonClient.logger"
    ) as mock_logger:
        await client._log_room_entry_debug(mock_bizhawk_context)

    mock_read.assert_not_awaited()
    mock_logger.info.assert_not_called()
