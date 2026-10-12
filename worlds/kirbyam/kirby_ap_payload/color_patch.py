"""Validated append-only curated-color extension and USA palette hooks."""
import struct

COLOR_EXTENSION_OFFSET = 0x1000000
COLOR_EXTENSION_ADDRESS = 0x09000000
COLOR_EXTENSION_LIMIT = 0x10000
OBJ_DISPATCH_OFFSET = 0xD60820
HUD_ENTRY_OFFSET = 0x3D21C


def build_color_extension_writes(rom: bytes | bytearray, extension: bytes,
                                 sprite_target: int, hud_target: int) -> dict[int, bytes]:
    """Validate every input before the caller mutates the ROM; reject repatching."""
    if len(rom) != COLOR_EXTENSION_OFFSET:
        raise ValueError("Color extension requires the original 16 MiB ROM size")
    if not extension or len(extension) > COLOR_EXTENSION_LIMIT:
        raise ValueError("Color extension must occupy 1..65536 bytes")
    if extension[:8] != b"APCOL02\0":
        raise ValueError("Color extension catalog marker mismatch")
    for target in (sprite_target, hud_target):
        if target & 1 or not COLOR_EXTENSION_ADDRESS + 8 <= target < COLOR_EXTENSION_ADDRESS + len(extension):
            raise ValueError("Color hook target must be aligned inside the appended extension")
    if rom[OBJ_DISPATCH_OFFSET:OBJ_DISPATCH_OFFSET + 4] != struct.pack('<I', 0x08155401):
        raise ValueError("Unexpected native OBJ palette dispatch")
    if rom[HUD_ENTRY_OFFSET:HUD_ENTRY_OFFSET + 8] != bytes.fromhex('70b5041c0d1c161c'):
        raise ValueError("Unexpected native HUD palette entry")
    return {
        COLOR_EXTENSION_OFFSET: extension,
        OBJ_DISPATCH_OFFSET: struct.pack('<I', sprite_target | 1),
        # Thumb tail jump, aligned literal; r0-r2 and caller LR remain intact.
        HUD_ENTRY_OFFSET: bytes.fromhex('004b1847') + struct.pack('<I', hud_target | 1),
    }
