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
    assert [c.key for c in colors[14:]] == ['shadow', 'ivory', 'citrus', 'white', 'lavender', 'rainbow', 'candy_corn', 'hot_pepper', 'negative']
    assert [(c.color_id, StartingKirbyColor.from_text(c.key).value) for c in colors] == [(i, i) for i in range(23)]
    assert colors[13].key == 'chalk' and not colors[13].palettes
    assert module('generate_colors').render() == (WORLD / 'kirby_ap_payload/color_tables.h').read_text()
    rng = Random(599)
    for current in range(23):
        seen = {choose_different_kirby_color(current, rng).color_id for _ in range(500)}
        assert seen == set(range(23)) - {current}
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
    extension = b'APCOL03\0' + bytes(56)
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
    extension = b'APCOL03\0' + bytes(56)
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


@pytest.mark.parametrize('version,maximum', [(1, 13), (2, 18), (3, 22), ([], 13), ({}, 13)])
def test_catalog_limits_preserve_old_seed_pool(mock_bizhawk_context, version, maximum):
    client = KirbyAmClient()
    for color in range(23):
        mock_bizhawk_context.slot_data = {'kirby_color_catalog_version': version, 'starting_kirby_color': color}
        assert (client._get_starting_kirby_color_config(mock_bizhawk_context) is not None) == (color <= maximum)
    rng = Random(19)
    seen = {choose_different_kirby_color(0, rng, max_color_id=maximum).color_id for _ in range(1000)}
    assert seen == set(range(1, maximum + 1))


@pytest.mark.asyncio
@pytest.mark.parametrize('version,marker,ready', [
    (3, b'APCOL03\0', True), (3, b'APCOL02\0', False),
    (2, b'APCOL02\0', True), (2, b'APCOL03\0', False),
])
async def test_catalog_version_requires_matching_rom(mock_bizhawk_context, version, marker, ready):
    client = KirbyAmClient()
    client.initialize_client()
    mock_bizhawk_context.slot_data = {'kirby_color_catalog_version': version}
    with patch('worlds.kirbyam.client.bizhawk.read', new_callable=AsyncMock, return_value=[marker]):
        assert await client._color_catalog_ready(mock_bizhawk_context) is ready


@pytest.mark.parametrize('key', ['rainbow', 'candy_corn', 'hot_pepper', 'negative'])
def test_original_palette_preserves_shared_ui_and_effect_slots(key):
    color = next(c for c in load_kirby_colors() if c.key == key)
    normal, ufo, hud = color.palettes
    assert normal[0:2] == ufo[0:2] == (0, 0)
    assert normal[12:] == (12915, 20215, 27581, 32767)
    assert ufo[4] == 24218
    assert ufo[12:] == (118, 4127, 16912, 32767)
    assert hud[1:7] == tuple(normal[i] for i in (3, 4, 5, 10, 6, 7))
    assert hud[7:] == (0, 32767, 863, 32589, 607, 479, 20480, 863, 19026)


def test_negative_inverts_native_body_and_saucer_without_inverting_shared_details():
    color = next(c for c in load_kirby_colors() if c.key == 'negative')
    normal, ufo, _ = color.palettes
    native_body = (31583, 28319, 25183, 20958, 14651, 7318, 2124, 16511, 10266, 5142)
    assert normal[2:12] == tuple(word ^ 0x7FFF for word in native_body)
    assert ufo[9:12] == tuple(word ^ 0x7FFF for word in (703, 511, 284))
