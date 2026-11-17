"""Hub drafts cannot reuse incompatible IDs, mailbox layout or save semantics."""
from unittest.mock import AsyncMock, patch

import pytest

from ..client import KirbyAmClient
from ..hub_protocol import HUB_MARKER, HUB_MARKER_OFFSET, hub_slot_version


@pytest.mark.parametrize("slot", [
    {"hub_connection_protocol_version": v} for v in (True, 1, 3, "2")
] + [{"unique_items": ["Moonlight Mansion - Hub Connection"]}, {"unique_items": "bad"}])
def test_incompatible_hub_slots_rejected(slot):
    with pytest.raises(ValueError):
        hub_slot_version(slot)


def test_legacy_main_catalog_retained():
    assert hub_slot_version({"unique_items": ["Moonlight Mansion - Mirror Shard"]}) == 0
    assert hub_slot_version({"hub_connection_protocol_version": 2}) == 2


@pytest.mark.asyncio
async def test_hub_marker_rechecked_before_writes(mock_bizhawk_context):
    ctx = mock_bizhawk_context
    ctx.slot_data = {"hub_connection_protocol_version": 2}
    client = KirbyAmClient()
    client.initialize_client()
    with patch("worlds.kirbyam.client.bizhawk.read", new_callable=AsyncMock) as read, \
            patch("worlds.kirbyam.client.bizhawk.write", new_callable=AsyncMock) as write:
        read.return_value = [HUB_MARKER]
        read.side_effect = lambda _ctx, requests: (
            [bytes(12)] if requests == [(0x0900FFC8, 12, "System Bus")] else read.return_value)
        assert await client._health_protocol_ready(ctx, require_identity=False)
        read.assert_called_with(ctx.bizhawk_ctx, [(HUB_MARKER_OFFSET, 8, "ROM")])
        read.return_value = [b"APHUB01\0"]
        assert not await client._health_protocol_ready(ctx, require_identity=False)
        read.return_value = [b""]
        assert not await client._health_protocol_ready(ctx, require_identity=False)
        write.assert_not_called()


@pytest.mark.asyncio
async def test_offline_saved_switch_is_reported_on_first_connection(mock_bizhawk_context):
    ctx = mock_bizhawk_context
    ctx.slot_data = {"hub_connection_protocol_version": 2}
    ctx.checked_locations = set()
    client = KirbyAmClient()
    client.initialize_client()
    client._hub_switch_location_ids_by_bit = {0: [123]}
    with patch("worlds.kirbyam.client.bizhawk.read", new_callable=AsyncMock) as read:
        read.return_value = [(1).to_bytes(4, "little")]
        await client._poll_hub_switch_locations(ctx)
        ctx.send_msgs.assert_awaited_with([{"cmd": "LocationChecks", "locations": [123]}])
        ctx.checked_locations = {123}
        ctx.send_msgs.reset_mock()
        await client._poll_hub_switch_locations(ctx)
        ctx.send_msgs.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("mutation", ["legacy_slot", "draft_slot", "old_rom", "changed_auth"])
async def test_mixed_hub_identity_has_no_watcher_side_effects(mock_bizhawk_context, mutation):
    from .test_vitality_protocol import _identity
    client = KirbyAmClient()
    client.initialize_client()
    ctx = mock_bizhawk_context
    memory = _identity(client, ctx, 2, 6, 10)
    ctx.slot_data["hub_connection_protocol_version"] = 2
    memory[HUB_MARKER_OFFSET, "ROM"] = HUB_MARKER

    async def read(_, requests):
        return [memory[a, domain] for a, _, domain in requests]

    with patch("worlds.kirbyam.client.bizhawk.read", side_effect=read):
        assert await client._health_protocol_ready(ctx)
        if mutation == "legacy_slot":
            del ctx.slot_data["hub_connection_protocol_version"]
        elif mutation == "draft_slot":
            del ctx.slot_data["hub_connection_protocol_version"]
            ctx.slot_data["unique_items"] = ["Moonlight Mansion - Hub Connection"]
        elif mutation == "old_rom":
            memory[HUB_MARKER_OFFSET, "ROM"] = bytes(8)
        else:
            ctx.auth = "different seed"
        with patch("worlds.kirbyam.client.bizhawk.write", new_callable=AsyncMock) as write, \
                patch("worlds.kirbyam.client.bizhawk.guarded_write", new_callable=AsyncMock) as guarded:
            await client.game_watcher(ctx)
            write.assert_not_called()
            guarded.assert_not_called()
            ctx.send_msgs.assert_not_called()


def test_corrected_names_preserve_protocol_two_numeric_receipts():
    from ..client import _HUB_CONNECTION_ITEM_ID_TO_DOOR_INDEX
    from ..data import data
    # Old protocol-2 catalogs contain these same names. Receipt IDs, not names,
    # choose the mailbox bits, so existing saves need no migration.
    assert hub_slot_version({"hub_connection_protocol_version": 2,
                             "unique_items": ["Moonlight Mansion - Hub Connection",
                                              "Rainbow Route East - Hub Connection"]}) == 2
    assert data.item_key_to_id['HUB_CONNECTION_RAINBOW_ROUTE_EAST'] == 3860401
    assert data.item_key_to_id['HUB_CONNECTION_MOONLIGHT_MANSION'] == 3860402
    assert _HUB_CONNECTION_ITEM_ID_TO_DOOR_INDEX[3860401] == 1
    assert _HUB_CONNECTION_ITEM_ID_TO_DOOR_INDEX[3860402] == 2
