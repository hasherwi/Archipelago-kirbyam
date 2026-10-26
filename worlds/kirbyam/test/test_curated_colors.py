"""Registry, compatibility, and bounded patch contracts for curated colors."""
import importlib.util
import json
from pathlib import Path
from random import Random
from unittest.mock import AsyncMock, patch

import pytest

from ..color_registry import parse_color_catalog
from ..colors import choose_different_kirby_color, load_kirby_colors
from ..client import KirbyAmClient
from ..options import StartingKirbyColor

WORLD = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, WORLD / 'kirby_ap_payload' / (name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def test_registry_build_and_options_agree():
    colors = load_kirby_colors()
    assert [c.key for c in colors[14:]] == ['shadow', 'ivory', 'citrus', 'white', 'lavender']
    assert [(c.color_id, StartingKirbyColor.from_text(c.key).value) for c in colors] == [(i, i) for i in range(19)]
    assert colors[13].key == 'chalk' and not colors[13].palettes
    assert module('generate_colors').render() == (WORLD / 'kirby_ap_payload/color_tables.h').read_text()
    rng = Random(599)
    for current in range(19):
        seen = {choose_different_kirby_color(current, rng).color_id for _ in range(500)}
        assert seen == set(range(19)) - {current}
    for current in range(14):
        seen = {choose_different_kirby_color(current, rng, native_only=True).color_id for _ in range(500)}
        assert seen == set(range(14)) - {current}


@pytest.mark.parametrize('defect', ['short', 'wide', 'bool', 'transparent', 'missing_context', 'fallback', 'provenance', 'native_id'])
def test_registry_rejects_unsafe_palette_data(defect):
    data = json.loads((WORLD / 'data/colors.json').read_text())
    custom = data['colors'][14]
    if defect == 'short': custom['palettes']['normal'].pop()
    elif defect == 'wide': custom['palettes']['ufo'][4] = 0x8000
    elif defect == 'bool': custom['palettes']['hud'][1] = True
    elif defect == 'transparent': custom['palettes']['normal'][0] = 1
    elif defect == 'missing_context': del custom['palettes']['ufo']
    elif defect == 'fallback': custom['native_fallback'] = 14
    elif defect == 'provenance': custom['provenance']['hud'] = ''
    elif defect == 'native_id': data['colors'][13]['key'] = 'white'
    with pytest.raises(ValueError): parse_color_catalog(data)


def fixture_rom():
    api = module('color_patch')
    rom = bytearray(api.COLOR_EXTENSION_OFFSET)
    rom[api.OBJ_DISPATCH_OFFSET:api.OBJ_DISPATCH_OFFSET + 4] = (0x08155401).to_bytes(4, 'little')
    rom[api.HUD_ENTRY_OFFSET:api.HUD_ENTRY_OFFSET + 8] = bytes.fromhex('70b5041c0d1c161c')
    return api, rom


def test_extension_appends_and_validates_both_native_hooks_before_mutation():
    api, rom = fixture_rom()
    original = bytes(rom)
    extension = b'APCOL02\0' + bytes(56)
    writes = api.build_color_extension_writes(rom, extension, 0x09000008, 0x09000020)
    assert bytes(rom) == original
    for offset, content in writes.items(): rom[offset:offset + len(content)] = content
    assert len(rom) == len(original) + len(extension)
    assert rom[len(original):] == extension
    assert rom[api.HUD_ENTRY_OFFSET:api.HUD_ENTRY_OFFSET + 8] == bytes.fromhex('004b184721000009')
    assert rom[api.OBJ_DISPATCH_OFFSET:api.OBJ_DISPATCH_OFFSET + 4] == bytes.fromhex('09000009')
    with pytest.raises(ValueError): api.build_color_extension_writes(rom, extension, 0x09000008, 0x09000020)


@pytest.mark.parametrize('defect', ['empty', 'oversized', 'odd', 'outside', 'marker', 'dispatch', 'hud'])
def test_extension_refuses_unsafe_inputs(defect):
    api, rom = fixture_rom()
    extension = b'APCOL02\0' + bytes(56)
    target = 0x09000008
    if defect == 'empty': extension = b''
    elif defect == 'oversized': extension += bytes(65536)
    elif defect == 'odd': target += 1
    elif defect == 'outside': target = 0x0815E000
    elif defect == 'marker': extension = bytes(64)
    elif defect == 'dispatch': rom[api.OBJ_DISPATCH_OFFSET] ^= 1
    elif defect == 'hud': rom[api.HUD_ENTRY_OFFSET] ^= 1
    original = bytes(rom)
    with pytest.raises(ValueError): api.build_color_extension_writes(rom, extension, target, 0x09000020)
    assert bytes(rom) == original


@pytest.mark.asyncio
@pytest.mark.parametrize('marker', [b'APCOL02\0', bytes(8)])
async def test_client_requires_new_payload_for_curated_catalog(mock_bizhawk_context, marker):
    client = KirbyAmClient()
    client.initialize_client()
    mock_bizhawk_context.slot_data = {'starting_kirby_color': 14, 'kirby_color_catalog_version': 2}
    with patch('worlds.kirbyam.client.bizhawk.read', new_callable=AsyncMock,
               side_effect=[[marker], [(0xFFFFFFFF).to_bytes(4, 'little')]]) as read, \
         patch('worlds.kirbyam.client.bizhawk.write', new_callable=AsyncMock) as write:
        await client._sync_starting_kirby_color_runtime_config(mock_bizhawk_context)
        if marker == b'APCOL02\0':
            assert write.call_args.args[1][0][1] == (14).to_bytes(4, 'little')
        else:
            assert not write.called
            await client._sync_starting_kirby_color_runtime_config(mock_bizhawk_context)
            assert read.await_count == 1
