"""Fail-closed patch contracts for the three USA health HUD callers."""
import importlib.util
from pathlib import Path

import pytest

_PATH = Path(__file__).resolve().parents[1] / 'kirby_ap_payload' / 'patch_rom.py'
_SPEC = importlib.util.spec_from_file_location('health_hud_patch', _PATH)
patch = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(patch)


def fixture_rom():
    rom = bytearray(0x40000)
    for offset in patch.HEALTH_HUD_CALLSITES:
        rom[offset:offset + 4] = patch.thumb_bl_bytes(0x08000000 + offset, 0x0803518C)
    return rom


def test_health_hud_validates_all_callers_without_mutating_input():
    rom = fixture_rom()
    before = bytes(rom)
    writes = patch.build_health_hud_writes(rom, 0x0815E100)
    assert bytes(rom) == before
    assert set(writes) == {0x339B2, 0x33BF2, 0x35A62}
    for offset, data in writes.items():
        assert patch.decode_thumb_bl_target(0x08000000 + offset, data) == 0x0815E100


@pytest.mark.parametrize('offset', patch.HEALTH_HUD_CALLSITES)
def test_health_hud_rejects_each_wrong_native_call(offset):
    rom = fixture_rom()
    rom[offset:offset + 4] = b'\x00' * 4
    with pytest.raises(SystemExit, match='native health HUD call'):
        patch.build_health_hud_writes(rom, 0x0815E100)


def test_health_hud_rejects_already_patched_input():
    rom = fixture_rom()
    for offset, data in patch.build_health_hud_writes(rom, 0x0815E100).items():
        rom[offset:offset + 4] = data
    with pytest.raises(SystemExit, match='native health HUD call'):
        patch.build_health_hud_writes(rom, 0x0815E100)
