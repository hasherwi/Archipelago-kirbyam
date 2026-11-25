"""Native selector input and rendering patches must stay local to the file menu."""
from collections.abc import Iterator

import pytest

from ..kirby_ap_payload import patch_rom


DRAW_TARGET = 0x0815F200
ROM_BASE = 0x08000000


@pytest.fixture
def selector_rom() -> Iterator[bytearray]:
    end = max(patch_rom.FILE_SELECTOR_DRAW_OFFSETS) + 4
    rom = bytearray(end)
    for offset, original, _, _ in patch_rom.FILE_SELECTOR_EDITS:
        rom[offset:offset + len(original)] = original
    for offset in patch_rom.FILE_SELECTOR_DRAW_OFFSETS:
        rom[offset:offset + 4] = patch_rom.thumb_bl_bytes(
            ROM_BASE + offset, patch_rom.FILE_SELECTOR_DRAW_ADDR)
    yield rom


def test_patch_preserves_native_selector_entry_and_keeps_one_confirmation(
    selector_rom: bytearray,
) -> None:
    baseline = bytes(selector_rom)
    writes = patch_rom.build_file_selector_writes(selector_rom, DRAW_TARGET)
    assert bytes(selector_rom) == baseline  # Validation alone cannot edit the ROM.
    assert set(writes) == {
        0x138C96, 0x13CA3A, 0x13CA50, 0x13CAE0,
        *patch_rom.FILE_SELECTOR_DRAW_OFFSETS,
    }
    # No title dispatch, mode menu constructor, or save IO site may be patched.
    assert {0x14A802, 0x138B44, 0x138F68, 0x13CA60, 0x00A91C, 0x00ACD4}.isdisjoint(writes)
    assert writes[0x138C96] == b"\xc0\x46"  # Keep native zero cursor.
    assert writes[0x13CA3A] == b"\x02\x28"  # Native confirm and Back only.
    guard_offset = int.from_bytes(writes[0x13CA50], "little") - ROM_BASE
    read_slot, compare_slot, rejected, accepted = (
        int.from_bytes(writes[guard_offset][i:i + 2], "little") for i in range(0, 8, 2))
    assert (read_slot, compare_slot) == (0x7AA0, 0x2800)  # [r4,#10], zero.
    assert rejected & 0xFF00 == 0xD100 and guard_offset + 8 + ((rejected & 0xFF) << 1) == 0x13CB10
    displacement = (accepted & 0x7FF) - 0x800
    assert accepted & 0xF800 == 0xE000 and guard_offset + 10 + displacement * 2 == 0x13CA60
    for offset in patch_rom.FILE_SELECTOR_DRAW_OFFSETS:
        assert patch_rom.decode_thumb_bl_target(ROM_BASE + offset, writes[offset]) == DRAW_TARGET


@pytest.mark.parametrize("offset", (
    *(entry[0] for entry in patch_rom.FILE_SELECTOR_EDITS),
    *patch_rom.FILE_SELECTOR_DRAW_OFFSETS,
))
def test_patch_rejects_unexpected_retail_bytes(selector_rom: bytearray, offset: int) -> None:
    selector_rom[offset] ^= 1
    with pytest.raises(SystemExit, match="(selector|file confirmation)"):
        patch_rom.build_file_selector_writes(selector_rom, DRAW_TARGET)
