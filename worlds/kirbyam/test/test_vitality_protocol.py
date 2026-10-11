"""Shipping ROM identity, fail-closed watcher and nine-counter authority tests."""
import base64
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from ..client import KirbyAmClient, _normalize_gba_rom_address
from ..data import data
from ..rom import KirbyAmPatchExtension
from ..vitality import HEALTH_ROM_TITLE, LEGACY_ROM_TITLE, VitalityPlan, VITALITY_ITEM_IDS


def _identity(client, ctx, version=2, minimum=1, maximum=10):
    auth = bytes(range(1, 17))
    client._health_protocol_version = version
    client._health_rom_auth = auth
    ctx.auth = base64.b64encode(auth).decode()
    ctx.slot_data.update(health_protocol_version=version, minimum_health=minimum, maximum_health=maximum)
    return {
        (0xA0, 'ROM'): HEALTH_ROM_TITLE if version == 2 else LEGACY_ROM_TITLE,
        (0x15F690, 'ROM'): VitalityPlan(minimum, maximum).config_word.to_bytes(4, 'little'),
        (_normalize_gba_rom_address(data.rom_addresses['gArchipelagoInfo']), 'ROM'): auth,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize('version', [1, 2])
@pytest.mark.parametrize('mutation', ['title', 'auth', 'slot_version', 'bounds', 'config', 'missing_version'])
async def test_watcher_rejects_identity_change_before_any_side_effect(mock_bizhawk_context, version, mutation):
    client = KirbyAmClient(); client.initialize_client()
    ctx = mock_bizhawk_context
    memory = _identity(client, ctx, version, 6, 10)
    async def read(_, requests):
        return [memory[a, domain] for a, _, domain in requests]
    with patch('worlds.kirbyam.client.bizhawk.read', side_effect=read):
        assert await client._health_protocol_ready(ctx)
    if mutation == 'title':
        memory[0xA0, 'ROM'] = LEGACY_ROM_TITLE if version == 2 else HEALTH_ROM_TITLE
    elif mutation == 'auth':
        memory[_normalize_gba_rom_address(data.rom_addresses['gArchipelagoInfo']), 'ROM'] = bytes(16)
    elif mutation == 'slot_version':
        ctx.slot_data['health_protocol_version'] = 3 - version
    elif mutation == 'bounds':
        ctx.slot_data['minimum_health'] = 1
    elif mutation == 'config':
        if version == 1:
            # Old packages have no health config contract; title/auth remain the gate.
            return
        memory[0x15F690, 'ROM'] = bytes(4)
    else:
        if version == 1:
            return  # Missing version is the explicitly supported legacy contract.
        del ctx.slot_data['health_protocol_version']
    with patch('worlds.kirbyam.client.bizhawk.read', side_effect=read), \
         patch('worlds.kirbyam.client.bizhawk.write', new_callable=AsyncMock) as write, \
         patch('worlds.kirbyam.client.bizhawk.guarded_write', new_callable=AsyncMock) as guarded, \
         patch.object(client, '_sync_death_link_setting', new_callable=AsyncMock) as death:
        await client.game_watcher(ctx)
    write.assert_not_awaited(); guarded.assert_not_awaited(); death.assert_not_awaited()
    ctx.send_msgs.assert_not_awaited()


@pytest.mark.asyncio
async def test_unvalidated_client_cannot_run_watcher(mock_bizhawk_context):
    client = KirbyAmClient(); client.initialize_client()
    with patch.object(client, '_sync_death_link_setting', new_callable=AsyncMock) as sync:
        await client.game_watcher(mock_bizhawk_context)
    sync.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize('minimum,maximum', [(a,b) for a in range(1,11) for b in range(a,11)])
@pytest.mark.parametrize('hp', [1, 0, -1, -128])
async def test_shipping_authority_all_ranges_preserves_metadata_and_death(mock_bizhawk_context, minimum, maximum, hp):
    client = KirbyAmClient(); client.initialize_client()
    ctx = mock_bizhawk_context
    memory = _identity(client, ctx, 2, minimum, maximum)
    ctx.items_received = [SimpleNamespace(item=item) for item in reversed(VITALITY_ITEM_IDS)] * 2
    client.on_package(ctx, 'ReceivedItems', {'index': 0})
    client._start_inventory_cursor_ready = AsyncMock(return_value=True)
    addresses = [client._transport_addr('delivered_vitality_item_bits'),
                 client._native_addr('kirby_vitality_counter_native'),
                 client._native_addr('kirby_hp_native'), client._native_addr('kirby_max_hp_native')]
    for address, value in zip(addresses, [(0xABCDE000).to_bytes(4,'little'), bytes(2),
                                         hp.to_bytes(1,'little',signed=True), bytes([minimum])]):
        memory[address, 'System Bus'] = value
    async def read(_, requests): return [memory[a,d] for a,_,d in requests]
    async def write(_, writes, guards):
        assert all(memory[a,d] == v for a,v,d in guards)
        for a,v,d in writes: memory[a,d] = v
        return True
    with patch('worlds.kirbyam.client.bizhawk.read', side_effect=read), \
         patch('worlds.kirbyam.client.bizhawk.guarded_write', side_effect=write) as writes:
        await client._reconcile_vitality_ownership(ctx)
        snapshot = dict(memory)
        await client._reconcile_vitality_ownership(ctx)
    count = maximum-minimum
    assert int.from_bytes(memory[addresses[0],'System Bus'],'little') == 0xABCDE1FF
    assert int.from_bytes(memory[addresses[1],'System Bus'],'little') == count
    assert int.from_bytes(memory[addresses[2],'System Bus'],'little',signed=True) == (maximum if hp>0 and count else hp)
    assert memory[addresses[3],'System Bus'] == bytes([maximum])
    assert memory == snapshot
    assert writes.await_count == 1


def test_final_header_checksum_preserves_game_code_and_auth():
    rom = bytearray(0x160000)
    rom[0xA0:0xAC] = LEGACY_ROM_TITLE
    rom[0xAC:0xB2] = b'B8KE01'
    rom[0x15F690:0x15F694] = VitalityPlan(1,10).config_word.to_bytes(4,'little')
    final = KirbyAmPatchExtension.finalize_health_header(None, bytes(rom))
    assert final[0xA0:0xAC] == HEALTH_ROM_TITLE
    assert final[0xAC:0xBD] == rom[0xAC:0xBD]
    assert (sum(final[0xA0:0xBE]) + 0x19) & 0xFF == 0
    assert final[0xBE:] == rom[0xBE:]


@pytest.mark.asyncio
@pytest.mark.parametrize('item_id', VITALITY_ITEM_IDS)
async def test_stock_server_precollects_each_v2_identity(mock_bizhawk_context, item_id):
    from NetUtils import NetworkItem
    from .test_start_inventory_protocol import server_history, mailbox
    client = KirbyAmClient(); client.initialize_client()
    ctx = mock_bizhawk_context
    ctx.items_handling = 0b111
    identity = _identity(client, ctx)
    server, _ = await server_history(ctx, [NetworkItem(item_id,-2,0)], [NetworkItem(3860026,3960566,1)])
    packet = server.send_msgs.call_args.args[1][0]
    assert packet['index'] == 0 and packet['items'][0].item == item_id
    ctx.items_received = packet['items']; client.on_package(ctx,'ReceivedItems',packet)
    memory = {(a,'System Bus'):v for a,v in mailbox(client).items()}
    memory.update(identity)
    async def read(_, requests): return [memory[a,d] for a,_,d in requests]
    async def write(_, writes, guards):
        if not all(memory[a,d] == v for a,v,d in guards): return False
        for a,v,d in writes: memory[a,d] = v
        return True
    with patch('worlds.kirbyam.client.bizhawk.read',side_effect=read), \
         patch('worlds.kirbyam.client.bizhawk.guarded_write',side_effect=write):
        await client._reconcile_vitality_ownership(ctx)
    assert int.from_bytes(memory[client._native_addr('kirby_vitality_counter_native'),'System Bus'],'little') == 1
    assert int.from_bytes(memory[client._transport_addr('delivered_vitality_item_bits'),'System Bus'],'little') == 0x80000000 | (1 << VITALITY_ITEM_IDS.index(item_id))


@pytest.mark.asyncio
@pytest.mark.parametrize('error_name', ['RequestFailedError', 'NotConnectedError', 'ConnectorError', 'SyncError'])
async def test_identity_read_transport_failure_pauses_writes(mock_bizhawk_context, error_name):
    from ..client import bizhawk
    client = KirbyAmClient(); client.initialize_client()
    _identity(client, mock_bizhawk_context)
    with patch('worlds.kirbyam.client.bizhawk.read', side_effect=getattr(bizhawk,error_name)('lost connector')), \
         patch.object(client, '_sync_death_link_setting', new_callable=AsyncMock) as sync:
        await client.game_watcher(mock_bizhawk_context)
    sync.assert_not_awaited()
