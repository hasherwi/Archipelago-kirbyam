"""One public health configuration, with safe legacy YAML/seed compatibility."""
from collections import Counter
import io
import struct
from unittest.mock import AsyncMock, patch
import zipfile

import pytest
from Options import Visibility

from ..client import KirbyAmClient, _CHALLENGE_RUNTIME_CONFIG_REVALIDATE_TICKS
from ..options import OneHitMode, OPTION_GROUPS
from ..rom import HEALTH_INITIAL_ROM_OFFSET
from ..vitality import resolve_vitality_plan
from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive


def _health_word(archive):
    with zipfile.ZipFile(archive) as generated:
        name = next(name for name in generated.namelist() if name.endswith('.apkirbyam'))
        with zipfile.ZipFile(io.BytesIO(generated.read(name))) as patch_file:
            tokens = patch_file.read('token_data.bin')
    count, = struct.unpack_from('<I', tokens)
    cursor = 4
    for _ in range(count):
        kind, address, size = struct.unpack_from('<BII', tokens, cursor)
        cursor += 9
        value = tokens[cursor:cursor + size]
        cursor += size
        if address == HEALTH_INITIAL_ROM_OFFSET:
            assert kind == 0 and size == 4
            return int.from_bytes(value, 'little')
    raise AssertionError('missing native initial health config')


@pytest.mark.parametrize('legacy,maximum', [('exclude_vitality_counters', 1), ('include_vitality_counters', 5),
                                          ('1', 1), ('2', 5)])
def test_legacy_yaml_normalizes_to_canonical_health(tmp_path, caplog, legacy, maximum):
    outputs = []
    for label, options in [
        ('legacy', f'  minimum_health: 8\n  maximum_health: 10\n  one_hit_mode: {legacy}\n'),
        ('canonical', f'  minimum_health: 1\n  maximum_health: {maximum}\n'),
    ]:
        player = tmp_path / f'{label}.yaml'
        player.write_text('name: Health Migration\ngame: Kirby & The Amazing Mirror\n'
                          'Kirby & The Amazing Mirror:\n' + options, encoding='utf-8')
        archive = generate_archive_from_fixture(player, tmp_path / label, seed=955)
        decoded = load_multidata_from_archive(archive)
        slot = decoded['slot_data'][1]
        assert 'one_hit_mode' not in slot
        assert (slot['minimum_health'], slot['maximum_health']) == (1, maximum)
        assert _health_word(archive) == 0xA9020000 | (maximum << 8) | 1
        outputs.append(decoded)
    assert 'one_hit_mode is deprecated' in caplog.text
    assert Counter(i[0] for i in outputs[0]['locations'][1].values()) == Counter(
        i[0] for i in outputs[1]['locations'][1].values())
    assert outputs[0]['precollected_items'] == outputs[1]['precollected_items']


def test_legacy_selector_is_hidden_and_removed_from_groups():
    assert OneHitMode.visibility == Visibility.none
    assert all(OneHitMode not in group.options for group in OPTION_GROUPS)


@pytest.mark.asyncio
@pytest.mark.parametrize('minimum,maximum', [(lo, hi) for lo in range(1, 11) for hi in range(lo, 11)])
async def test_new_health_bounds_drive_native_trap_policy(mock_bizhawk_context, minimum, maximum):
    ctx = mock_bizhawk_context
    ctx.slot_data = {'minimum_health': minimum, 'maximum_health': maximum, 'no_extra_lives': False}
    client = KirbyAmClient()
    client.initialize_client()
    memory = {}

    async def write(_ctx, requests):
        for address, value, _domain in requests:
            memory[address] = value

    async def read(_ctx, requests):
        return [memory.get(address, bytes(size)) for address, size, _domain in requests]

    with patch('worlds.kirbyam.client.bizhawk.write', side_effect=write), \
         patch('worlds.kirbyam.client.bizhawk.read', side_effect=read):
        for _ in range(2):
            # Native cold boot initializes both config words to the sentinel.
            for key in ('one_hit_mode_runtime', 'no_extra_lives_runtime'):
                memory[client._transport_addr(key)] = b'\xff' * 4
            for _tick in range(_CHALLENGE_RUNTIME_CONFIG_REVALIDATE_TICKS):
                await client._sync_challenge_runtime_config(ctx)
            assert int.from_bytes(memory[client._transport_addr('one_hit_mode_runtime')], 'little') == (minimum == 1)
    assert resolve_vitality_plan(minimum, maximum).count == maximum - minimum


@pytest.mark.asyncio
@pytest.mark.parametrize('mode,expected', [(0, (6, 10)), (1, (1, 1)), (2, (1, 5))])
async def test_old_slot_data_preserves_preset_and_mailbox(mock_bizhawk_context, mode, expected):
    ctx = mock_bizhawk_context
    ctx.slot_data = {'one_hit_mode': mode}
    client = KirbyAmClient()
    client.initialize_client()
    with patch('worlds.kirbyam.client.bizhawk.write', new_callable=AsyncMock) as write:
        await client._sync_challenge_runtime_config(ctx)
    values = {address: int.from_bytes(value, 'little') for address, value, _ in write.call_args.args[1]}
    assert values[client._transport_addr('one_hit_mode_runtime')] == mode
    plan = resolve_vitality_plan(one_hit_mode=mode)
    assert (plan.minimum, plan.maximum) == expected


@pytest.mark.asyncio
async def test_invalid_canonical_bounds_do_not_write_trap_policy(mock_bizhawk_context):
    client = KirbyAmClient()
    client.initialize_client()
    mock_bizhawk_context.slot_data = {'minimum_health': 8, 'maximum_health': 3}
    with patch('worlds.kirbyam.client.bizhawk.write', new_callable=AsyncMock) as write:
        await client._sync_challenge_runtime_config(mock_bizhawk_context)
    write.assert_not_awaited()
