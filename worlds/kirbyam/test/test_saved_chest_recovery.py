"""Durable physical checks use chestFields, not item ownership or lever bits."""
from unittest.mock import AsyncMock, patch

import pytest

from ..client import KirbyAmClient
from ..data import data, load_json_data


def test_inventory_covers_all_unique_native_chests_and_excludes_non_checks():
    records = load_json_data('chest_recovery.json')['records']
    assert len(records) == 84
    assert {r['flag'] for r in records} == set(range(84))
    excluded = [r for r in records if r['location_key'] is None]
    assert sorted(r['reward'] for r in excluded) == [99, 99, 99, 99]
    manifest = load_json_data('minor_chest_manifest.json')['entries']
    inventory = {int(r['source'], 0): r for r in records}
    for entry in manifest:
        row = inventory[int(entry['rom_offset'], 0)]
        assert (row['flag'], row['reward']) == (entry['chest_index'], entry['reward_id'])
        if row['location_key']:
            assert data.locations[row['location_key']].source_rom_offset == int(row['source'], 0)


@pytest.mark.asyncio
@pytest.mark.parametrize('fresh_client', [False, True])
async def test_saved_flags_recover_overflow_cold_boot_and_exit_before_ack(mock_bizhawk_context, fresh_client):
    ctx = mock_bizhawk_context
    client = KirbyAmClient()
    client.initialize_client()
    rows = [r for r in load_json_data('chest_recovery.json')['records']
            if r['type'] == 128 and r['location_key']][:9]
    ids = {data.locations[r['location_key']].location_id for r in rows}
    ctx.server_locations = set(client._saved_chest_location_by_flag.values())
    bits = sum(1 << r['flag'] for r in rows)
    with patch('worlds.kirbyam.client.bizhawk.read', new_callable=AsyncMock) as read:
        read.return_value = [bits.to_bytes(16, 'little')]
        await client._poll_saved_chest_locations(ctx)
        assert set(ctx.send_msgs.call_args.args[0][0]['locations']) == ids
        if fresh_client:
            client = KirbyAmClient()
            client.initialize_client()
        # Saved state is sufficient: no volatile transport or pending observations.
        client._last_minor_chest_event_counter = 0
        await client._poll_saved_chest_locations(ctx)
        assert ctx.send_msgs.await_count == 2
        ctx.checked_locations = ids
        await client._poll_saved_chest_locations(ctx)
        assert ctx.send_msgs.await_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize('category', ['MAP_CHEST', 'VITALITY_CHEST', 'SOUND_PLAYER_CHEST'])
async def test_each_big_chest_family_recovers_without_reward_ownership(mock_bizhawk_context, category):
    client = KirbyAmClient()
    client.initialize_client()
    ctx = mock_bizhawk_context
    ctx.server_locations = set(client._saved_chest_location_by_flag.values())
    rows = [r for r in load_json_data('chest_recovery.json')['records'] if r['location_key']
            and data.locations[r['location_key']].category.name == category]
    assert rows
    for row in rows:
        with patch('worlds.kirbyam.client.bizhawk.read', new_callable=AsyncMock) as read:
            read.return_value = [(1 << row['flag']).to_bytes(16, 'little')]
            await client._poll_saved_chest_locations(ctx)
            ctx.send_msgs.assert_awaited_with([{'cmd':'LocationChecks', 'locations': [data.locations[row['location_key']].location_id]}])


@pytest.mark.asyncio
async def test_recovery_filters_inactive_locations_and_levers(mock_bizhawk_context):
    client = KirbyAmClient()
    client.initialize_client()
    ctx = mock_bizhawk_context
    one_id = next(iter(client._saved_chest_location_by_flag.values()))
    ctx.server_locations = {one_id}
    with patch('worlds.kirbyam.client.bizhawk.read', new_callable=AsyncMock) as read:
        read.return_value = [bytes([255])*16]
        await client._poll_saved_chest_locations(ctx)
        ctx.send_msgs.assert_awaited_once_with([{'cmd':'LocationChecks', 'locations':[one_id]}])
        ctx.send_msgs.reset_mock()
        excluded = [r for r in load_json_data('chest_recovery.json')['records'] if r['location_key'] is None]
        read.return_value = [sum(1 << r['flag'] for r in excluded).to_bytes(16,'little')]
        await client._poll_saved_chest_locations(ctx)
        ctx.send_msgs.assert_not_awaited()


@pytest.mark.asyncio
async def test_recovery_discards_cross_session_read(mock_bizhawk_context):
    client = KirbyAmClient()
    client.initialize_client()
    ctx = mock_bizhawk_context
    ctx.server_locations = set(client._saved_chest_location_by_flag.values())
    async def switched(*args):
        ctx.auth = 'another-ROM-token'
        return [bytes([255])*16]
    with patch('worlds.kirbyam.client.bizhawk.read', side_effect=switched):
        await client._poll_saved_chest_locations(ctx)
    ctx.send_msgs.assert_not_awaited()
