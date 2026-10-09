"""Location-only contracts: all native sources, recovery and room ownership."""
from unittest.mock import AsyncMock, patch

import pytest
from BaseClasses import CollectionState, MultiWorld, Region

from .. import KirbyAmWorld
from ..client import KirbyAmClient
from ..data import data, load_json_data
from .test_client import _minor_chest_event_ring


@pytest.mark.asyncio
@pytest.mark.parametrize('entry', load_json_data('minor_chest_manifest.json')['entries'],
                         ids=lambda entry: entry['rom_offset'])
async def test_each_of_65_native_sources_reports_its_historical_location(mock_bizhawk_context, entry):
    client = KirbyAmClient()
    client.initialize_client()
    source = int(entry['rom_offset'], 0)
    location_id = client._minor_chest_location_id_by_source_ptr[source]
    mock_bizhawk_context.server_locations = {location_id}
    with patch('worlds.kirbyam.client.bizhawk.read', new_callable=AsyncMock) as read:
        read.return_value = [(1).to_bytes(4, 'little'), _minor_chest_event_ring(source + 0x08000000)]
        await client._poll_minor_chest_locations(mock_bizhawk_context)
        mock_bizhawk_context.send_msgs.assert_awaited_once_with([
            {'cmd': 'LocationChecks', 'locations': [location_id]}])
        mock_bizhawk_context.checked_locations = {location_id}
        await client._poll_minor_chest_locations(mock_bizhawk_context)
        assert mock_bizhawk_context.send_msgs.await_count == 1


@pytest.mark.asyncio
async def test_first_post_rollback_event_retries_until_server_ack(mock_bizhawk_context):
    client = KirbyAmClient()
    client.initialize_client()
    client._last_minor_chest_event_counter = 5
    target = data.locations['MINOR_CHEST_RAINBOW_ROUTE_1_02']
    with patch('worlds.kirbyam.client.bizhawk.read', new_callable=AsyncMock) as read:
        read.return_value = [(1).to_bytes(4, 'little'),
                             _minor_chest_event_ring(0x08000000 + target.source_rom_offset)]
        for _ in range(2):
            await client._poll_minor_chest_locations(mock_bizhawk_context)
            mock_bizhawk_context.send_msgs.assert_awaited_with([
                {'cmd': 'LocationChecks', 'locations': [target.location_id]}])
        assert mock_bizhawk_context.send_msgs.await_count == 2
        mock_bizhawk_context.checked_locations = {target.location_id}
        await client._poll_minor_chest_locations(mock_bizhawk_context)
        assert mock_bizhawk_context.send_msgs.await_count == 2


@pytest.mark.asyncio
async def test_nine_offline_opens_recover_from_actual_saved_flags(mock_bizhawk_context):
    client = KirbyAmClient()
    client.initialize_client()
    rows = [r for r in load_json_data('chest_recovery.json')['records'] if r['type'] == 128][:9]
    ids = {data.locations[row['location_key']].location_id for row in rows}
    mock_bizhawk_context.server_locations = ids
    ring = _minor_chest_event_ring(*(int(row['source'], 0) + 0x08000000 for row in rows))
    flags = sum(1 << row['flag'] for row in rows).to_bytes(16, 'little')
    async def read_memory(_ctx, reads):
        memory = {data.transport_ram_addresses['minor_chest_event_counter']: (9).to_bytes(4, 'little'),
                  data.transport_ram_addresses['minor_chest_event_ring_base']: ring,
                  data.ram_addresses['other_chest_flags_native']: flags}
        return [memory[address] for address, _, _ in reads]
    with patch('worlds.kirbyam.client.bizhawk.read', side_effect=read_memory):
        await client._poll_saved_chest_locations(mock_bizhawk_context)
        await client._poll_minor_chest_locations(mock_bizhawk_context)
    sent = {loc for call in mock_bizhawk_context.send_msgs.call_args_list
            for packet in call.args[0] for loc in packet['locations']}
    assert sent == ids


@pytest.mark.parametrize('entry,lower,upper', [
    ('ROOM_5_07', True, False), ('ROOM_5_14', False, True),
    ('ROOM_5_12', False, False), ('ROOM_5_18', False, False), ('ROOM_5_WARP', False, False),
])
def test_carrot_physical_compartments(entry, lower, upper):
    prefix = 'REGION_CARROT_CASTLE/'
    parent = prefix + 'ROOM_5_13'
    entries = ['ROOM_5_07', 'ROOM_5_14', 'ROOM_5_12', 'ROOM_5_18', 'ROOM_5_WARP']
    names = [parent, *(prefix + name for name in entries),
             *(name for name in data.regions if name.startswith(parent + '__LOGIC__'))]
    multiworld = MultiWorld(1)
    multiworld.worlds[1] = KirbyAmWorld(multiworld, 1)
    regions = {name: Region(name, 1, multiworld) for name in ['Menu', *names]}
    multiworld.regions.extend(regions.values())
    for name in names:
        definition = data.regions[name]
        for destination in definition.exits:
            if destination in regions and (name.startswith(parent) or destination.startswith(parent)):
                regions[name].connect(regions[destination])
        regions[name].add_locations({key: data.locations[key].location_id for key in definition.locations})
    regions['Menu'].connect(regions[prefix + entry])
    state = CollectionState(multiworld)
    assert multiworld.get_location('MINOR_CHEST_CARROT_CASTLE_5_13_OBJECT_02', 1).can_reach(state) is lower
    assert multiworld.get_location('MINOR_CHEST_MUSIC_NOTE_06', 1).can_reach(state) is upper
    assert not regions[parent].can_reach(state)


def test_all_65_chests_are_reachable_without_received_ap_items():
    """Current v0.4 graph, including event sweep, requires no new item gates."""
    from argparse import Namespace
    multiworld = MultiWorld(1)
    multiworld.game[1] = KirbyAmWorld.game
    multiworld.player_name = {1: 'Starting access audit'}
    multiworld.set_seed(930)
    args = Namespace()
    for name, option in KirbyAmWorld.options_dataclass.type_hints.items():
        setattr(args, name, {1: option.from_any(option.default)})
    multiworld.set_options(args)
    world = multiworld.worlds[1]
    world.create_regions()
    world.set_rules()
    state = CollectionState(multiworld)
    state.sweep_for_advancements()
    rows = [row for row in data.locations.values()
            if row.name.startswith('MINOR_CHEST_') and row.source_rom_offset is not None]
    assert len(rows) == 65
    assert not [row.name for row in rows
                if not multiworld.get_location(row.label, 1).can_reach(state)]


def test_starting_ungated_native_abilities_cover_current_capability_groups():
    from ..rules import _ABILITY_GATE_PLACEHOLDER_SOURCES
    abilities = load_json_data('abilities.json')
    ungated = {name for name, row in abilities.items()
               if not row.get('safe_to_gate') and row.get('enemy_copy_allowed', True)}
    assert ungated == {'Beam', 'Burning', 'Cutter', 'Mini', 'Stone', 'Wheel'}
    assert all(ungated & choices for choices in _ABILITY_GATE_PLACEHOLDER_SOURCES.values())
