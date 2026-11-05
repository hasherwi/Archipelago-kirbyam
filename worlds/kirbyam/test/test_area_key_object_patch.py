"""Fail-closed hook contracts for Area Key object reconciliation."""
import importlib.util
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location("area_object_patch", Path(__file__).parents[1] / "kirby_ap_payload/patch_rom.py")
assert _spec and _spec.loader
patch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(patch)


def fixture():
    rom = bytearray(0x120000)
    targets = {}
    for offset, (adapter, expected) in patch.AREA_OBJECT_SPAWN_SITES.items():
        rom[offset - 6:offset + 8] = expected
        targets["ap_area_spawn_" + adapter + "_entry"] = 0x0815E000
    for offset, (native, name) in patch.AREA_OBJECT_TASK_POINTERS.items():
        rom[offset:offset + 4] = native.to_bytes(4, "little")
        targets[name] = 0x09001000
    for offset in patch.AREA_DOOR_DECORATION_SITES:
        rom[offset:offset + 4] = patch.thumb_bl_bytes(0x08000000 + offset, 0x0802B2F4)
    targets["ap_area_door_decoration_entry"] = 0x0815E020
    return rom, targets


def test_installs_all_scanners_tasks_and_decoration_calls():
    rom, targets = fixture()
    original = bytes(rom)
    writes = patch.build_area_object_writes(rom, targets)
    assert len(writes) == 11
    assert bytes(rom) == original
    for offset in patch.AREA_OBJECT_TASK_POINTERS:
        assert int.from_bytes(writes[offset], "little") == 0x09001001
    for offset in patch.AREA_OBJECT_SPAWN_SITES:
        assert patch.decode_thumb_bl_target(0x08000000 + offset, writes[offset]) == 0x0815E000


@pytest.mark.parametrize("offset", [0xA196, 0xA300, 0xA4AC, 0xBE44, 0x1E300, 0x2AB38, 0x119D28, 0xA840, 0x2B2B8, 0x2B446, 0x2B48A])
def test_rejects_changed_native_hook_or_register_contract(offset):
    rom, targets = fixture()
    rom[offset] ^= 1
    with pytest.raises(SystemExit):
        patch.build_area_object_writes(rom, targets)
