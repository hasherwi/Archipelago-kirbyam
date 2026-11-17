"""Boards-only variant adds metadata; native frames, wood and palette stay native."""
import runpy
import struct
from pathlib import Path

import pytest

from .test_area_key_object_patch import patch


def fixture():
    dummy = runpy.run_path(str(Path(__file__).parents[1] / 'tools/create_dummy_rom.py'))
    rom = dummy['build_dummy_rom']()
    # Distinct unrelated table entries expose accidental truncation/replacement.
    struct.pack_into('<I', rom, patch.HUB_BOARD_NATIVE_VARIANTS, 0x0841E1A0)
    struct.pack_into('<H', rom, patch.HUB_BOARD_NATIVE_ATTRS, 123)
    return rom, 0x09008000, patch.HUB_BOARD_MARKER + bytes(768)


def test_new_variant_preserves_all_retail_variants_frames_and_pixels():
    rom, address, reserved = fixture()
    before = bytes(rom)
    writes = patch.build_hub_board_sprite_writes(rom, address, reserved)
    assert bytes(rom) == before
    assert set(writes) == {address - 0x08000000, 0x448FC4, 0x479414}
    metadata = writes[address - 0x08000000]
    assert len(metadata) == 776
    assert metadata[44:88] == before[0x41E494:0x41E494 + 44]
    assert metadata[92:764] == before[0x46A744:0x46A744 + 672]
    assert struct.unpack_from('<I', metadata, 88) == (address + 8,)
    assert struct.unpack_from('<I', metadata, 36) == (56,)
    assert metadata[8:36] == patch.HUB_BOARD_SCRIPT[:28]
    assert metadata[40:44] == patch.HUB_BOARD_SCRIPT[32:]
    assert struct.unpack_from('<6H', metadata, 764) == (137, 4, 0, 0, 0, 0)
    # Frame 32 still has all six pieces, while frame 56 uses only native wood.
    assert struct.unpack_from('<H', metadata, 92 + 32 * 12 + 2) == (6,)
    assert struct.unpack('<I', writes[0x448FC4]) == (address + 44,)
    assert struct.unpack('<I', writes[0x479414]) == (address + 92,)


@pytest.mark.parametrize('offset', [0x448FC4, 0x479414, 0x41E494 + 24,
                                   0x41E348, 0x46A744 + 384,
                                   patch.HUB_BOARD_OAM_OFFSET + 24])
def test_changed_native_sprite_contract_rejected_without_writes(offset):
    rom, address, reserved = fixture()
    rom[offset] ^= 1
    before = bytes(rom)
    with pytest.raises(SystemExit, match='native hub board sprite contract'):
        patch.build_hub_board_sprite_writes(rom, address, reserved)
    assert bytes(rom) == before


@pytest.mark.parametrize('address', [0x08008000, 0x09008001, 0x0900FD00])
def test_metadata_cannot_overlap_other_rom_or_configuration(address):
    rom, _, reserved = fixture()
    with pytest.raises(SystemExit, match='reserved extension'):
        patch.build_hub_board_sprite_writes(rom, address, reserved)


def test_existing_nonempty_reservation_is_not_overwritten():
    rom, address, reserved = fixture()
    with pytest.raises(SystemExit, match='reservation mismatch'):
        patch.build_hub_board_sprite_writes(rom, address, reserved[:-1] + b'X')
