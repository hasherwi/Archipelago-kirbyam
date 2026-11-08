"""Exact-site patch contract; native gameplay acceptance is separate."""
import pytest

from ..kirby_ap_payload.patch_rom import build_copy_room_native_grant_writes


def _fixture():
    rom = bytearray(0x1263BC)
    rom[0x12630A:0x12631C] = bytes.fromhex(
        "0f 2d 46 d1 02 20 12 21 00 22 dc f6 b8 fa 01 21 01 60")
    rom[0x12639C:0x1263A8] = bytes.fromhex("03 48 00 68 2c f0 4c fc 13 f7 64 f9")
    return rom


def test_branch_skips_grant_save_and_presentation_to_native_cleanup():
    rom = _fixture()
    before = bytes(rom)
    writes = build_copy_room_native_grant_writes(rom)
    assert bytes(rom) == before  # preflight is read-only
    assert writes == {0x12630C: bytes.fromhex("46 e0")}
    instruction = int.from_bytes(writes[0x12630C], "little")
    assert instruction & 0xF800 == 0xE000
    assert 0x12630C + 4 + 2 * (instruction & 0x7FF) == 0x12639C


@pytest.mark.parametrize("offset", [0x12630A, 0x126314, 0x12631A, 0x12639C, 0x1263A4])
def test_reject_changed_native_grant_or_cleanup(offset):
    rom = _fixture()
    rom[offset] ^= 1
    with pytest.raises(SystemExit):
        build_copy_room_native_grant_writes(rom)


def test_context_hooks_preserve_native_three_file_selection_and_world_layout():
    from ..kirby_ap_payload.patch_rom import (
        COPY_ROOM_NATIVE_CALLS, build_copy_room_context_writes, thumb_bl_bytes,
    )
    rom = bytearray(0x2D9240)
    targets = {"copy_room_load_target": 0x0815F300, "copy_room_clear_target": 0x0815F310,
               "copy_room_state_target": 0x0815F320}
    for native, _key, offsets in COPY_ROOM_NATIVE_CALLS:
        for offset in offsets:
            rom[offset:offset + 4] = thumb_bl_bytes(0x08000000 + offset, native)
    before = bytes(rom)
    writes = build_copy_room_context_writes(rom, targets)
    assert bytes(rom) == before
    assert set(writes) == {offset for _native, _key, offsets in COPY_ROOM_NATIVE_CALLS for offset in offsets}
    assert len(writes) == 22
    # No title/file-selector bypass, Back pointer, slot bounds or descriptor edits.
    untouched = {0x14A802, 0x13D8A0, 0x26A, 0x278, 0x2D91FC,
                 0xA9EC, 0xAA18, 0xAADC, 0xAB04, 0xABF4, 0xAD4C, 0x325DC, 0x32640, 0x3280C}
    assert not set(writes) & untouched
    for native, key, offsets in COPY_ROOM_NATIVE_CALLS:
        for offset in offsets:
            assert writes[offset] == thumb_bl_bytes(0x08000000 + offset, targets[key])
            corrupt = bytearray(before)
            corrupt[offset] ^= 1
            with pytest.raises(SystemExit):
                build_copy_room_context_writes(corrupt, targets)
