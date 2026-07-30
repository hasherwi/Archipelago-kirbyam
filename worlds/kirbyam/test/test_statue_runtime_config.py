"""Client mailbox regression tests for ability-statue gating configuration."""

from __future__ import annotations

from unittest.mock import AsyncMock, Mock, patch

import pytest

from ..client import KirbyAmClient
from ..data import data
from ..enemy_ability_data import ABILITY_NAME_TO_ID, GATEABLE_ENEMY_COPY_ABILITIES


def _gateable_ability_mask() -> int:
    mask = 0
    for ability_name in GATEABLE_ENEMY_COPY_ABILITIES:
        ability_id = ABILITY_NAME_TO_ID.get(ability_name)
        if ability_id is not None and 0 < ability_id <= 31:
            mask |= 1 << ability_id
    return mask


def _written_u32_by_address(mock_write: AsyncMock) -> dict[int, int]:
    writes = mock_write.await_args.args[1]
    return {
        address: int.from_bytes(payload, "little")
        for address, payload, domain in writes
        if domain == "System Bus"
    }


@pytest.mark.asyncio
async def test_legacy_slot_data_still_syncs_statue_gating_masks(
    mock_bizhawk_context,
) -> None:
    """Legacy worlds without structured policy still enforce gating (Issue #874)."""
    client = KirbyAmClient()
    client.initialize_client()

    magic_item_id = next(
        item_id
        for item_id, item_data in data.items.items()
        if item_data.label == "Magic Ability"
    )
    magic_ability_id = ABILITY_NAME_TO_ID["Magic"]
    allowed_mask = (
        (1 << ABILITY_NAME_TO_ID["Beam"])
        | (1 << magic_ability_id)
    )

    mock_bizhawk_context.slot_data = {
        "ability_gating": True,
        "ability_randomization_mode": 0,
        "ability_randomization_no_ability_weight": 0,
        "enemy_copy_ability_whitelist": ["Beam", "Magic"],
    }
    mock_bizhawk_context.items_received = [Mock(item=magic_item_id)]

    with patch("worlds.kirbyam.client.bizhawk.write", new_callable=AsyncMock) as mock_write:
        await client._sync_enemy_copy_ability_runtime_config(mock_bizhawk_context)

    gate_mask = _gateable_ability_mask()
    assert client._last_ability_runtime_config_signature == (
        0,
        0,
        0,
        0,
        allowed_mask,
        True,
        gate_mask,
        1 << magic_ability_id,
    )
    written = _written_u32_by_address(mock_write)
    assert written[data.transport_ram_addresses["ability_randomization_allowed_mask_runtime"]] == allowed_mask
    assert written[data.transport_ram_addresses["ability_gate_mask_runtime"]] == gate_mask
    assert written[data.transport_ram_addresses["ability_unlock_mask_runtime"]] == (1 << magic_ability_id)


@pytest.mark.asyncio
async def test_gating_disabled_writes_zero_gate_and_unlock_masks(
    mock_bizhawk_context,
) -> None:
    """Explicitly disabled gating must not suppress any statue ability."""
    client = KirbyAmClient()
    client.initialize_client()

    magic_item_id = next(
        item_id
        for item_id, item_data in data.items.items()
        if item_data.label == "Magic Ability"
    )
    mock_bizhawk_context.slot_data = {
        "ability_gating": False,
        # These values must be ignored while gating is disabled.
        "ability_gateable_abilities": ["Magic"],
        "ability_unlock_items": {"Magic": "Magic Ability"},
        "enemy_copy_ability_policy": {
            "mode": 2,
            "seed": 7,
            "ability_randomization_no_ability_weight": 55,
            "allowed_abilities": ["Beam", "Magic"],
        },
    }
    mock_bizhawk_context.items_received = [Mock(item=magic_item_id)]

    with patch("worlds.kirbyam.client.bizhawk.write", new_callable=AsyncMock) as mock_write:
        await client._sync_enemy_copy_ability_runtime_config(mock_bizhawk_context)

    assert client._last_ability_runtime_config_signature is not None
    assert client._last_ability_runtime_config_signature[-3:] == (False, 0, 0)
    written = _written_u32_by_address(mock_write)
    assert written[data.transport_ram_addresses["ability_gate_mask_runtime"]] == 0
    assert written[data.transport_ram_addresses["ability_unlock_mask_runtime"]] == 0
