"""Area Key option reconciliation across legacy seeds and reconnects."""
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ..client import KirbyAmClient
from ..data import data


@pytest.mark.parametrize("option", [False, 0])
@pytest.mark.asyncio
async def test_disabled_keys_clear_stale_save_ownership_after_reconnect(
    mock_bizhawk_context: Any, option: bool | int,
) -> None:
    client = KirbyAmClient()
    client.initialize_client()
    mock_bizhawk_context.slot_data.update(area_keys=option, starting_area_key_bitfield=0x3FC)
    mock_bizhawk_context.items_received = [Mock(item=3860041), Mock(item=3860048)]
    address = 0x0203B0C0
    for reconnect in (False, True):
        if reconnect:
            client._reset_reconnect_transient_state()
        client._delivered_item_index = 2
        client._cached_delivered_area_key_bits = 0x3FC
        with patch.dict(data.transport_ram_addresses, {"area_key_bitfield_runtime": address}), patch(
            "worlds.kirbyam.client.bizhawk.read", new_callable=AsyncMock, return_value=[(0x3FC).to_bytes(4, "little")],
        ), patch("worlds.kirbyam.client.bizhawk.write", new_callable=AsyncMock) as write:
            await client._sync_area_key_runtime_config(mock_bizhawk_context)
        write.assert_awaited_once_with(mock_bizhawk_context.bizhawk_ctx, [(address, bytes(4), "System Bus")])
        assert client._starting_area_key_bits(mock_bizhawk_context) == 0
        assert client._cached_delivered_area_key_bits == 0


def test_disabled_seed_cannot_reuse_previous_enabled_delivery_cache(mock_bizhawk_context: Any) -> None:
    client = KirbyAmClient()
    client.initialize_client()
    mock_bizhawk_context.slot_data["starting_area_key_bitfield"] = 0
    mock_bizhawk_context.items_received = [Mock(item=3860041)]
    client._delivered_item_index = 1
    assert client._ap_owned_area_key_bits(mock_bizhawk_context) == 1 << 2
    mock_bizhawk_context.slot_data["area_keys"] = False
    assert client._ap_owned_area_key_bits(mock_bizhawk_context) == 0
    mock_bizhawk_context.slot_data["area_keys"] = True
    mock_bizhawk_context.items_received = [Mock(item=3860048)]
    assert client._ap_owned_area_key_bits(mock_bizhawk_context) == 1 << 9


@pytest.mark.asyncio
async def test_pre_area_key_slot_data_does_not_write_unknown_runtime_memory(mock_bizhawk_context: Any) -> None:
    client = KirbyAmClient()
    client.initialize_client()
    mock_bizhawk_context.slot_data.pop("starting_area_key_bitfield", None)
    with patch("worlds.kirbyam.client.bizhawk.read", new_callable=AsyncMock) as read, patch(
        "worlds.kirbyam.client.bizhawk.write", new_callable=AsyncMock,
    ) as write:
        await client._sync_area_key_runtime_config(mock_bizhawk_context)
    read.assert_not_awaited()
    write.assert_not_awaited()


@pytest.mark.parametrize("allowed,reason", [(True, 6), (False, 2)])
@pytest.mark.asyncio
async def test_disabled_seed_logs_events_without_missing_key_overlay(
    mock_bizhawk_context: Any, allowed: bool, reason: int,
) -> None:
    client = KirbyAmClient()
    client.initialize_client()
    mock_bizhawk_context.slot_data.update(area_keys=False, starting_area_key_bitfield=0)
    client._last_transition_event_counter = 0
    metadata = 1 | (int(allowed) << 4) | (reason << 5)
    event = (1).to_bytes(4, "little") + ((142 << 16) | 195).to_bytes(4, "little") + metadata.to_bytes(4, "little")
    with patch("worlds.kirbyam.client.bizhawk.read", new_callable=AsyncMock, side_effect=[
        [0x54524E31.to_bytes(4, "little"), (1).to_bytes(4, "little")], [event],
    ]) as read, patch("worlds.kirbyam.client.bizhawk.display_message", new_callable=AsyncMock) as display, patch(
        "CommonClient.logger",
    ) as logger:
        await client._poll_transition_attempt_events(mock_bizhawk_context)
    assert read.await_count == 2
    display.assert_not_awaited()
    logger.info.assert_called_once()
    if allowed:
        assert "Area Keys disabled for this seed" in logger.info.call_args.args
