"""Validated format-2 native patch plan; not enabled by the shipping patcher.

The whole plan is validated before returning any writes. Runtime integration must
also install format-2 config/title/client gates and rebuilt payload bytes.
"""

from .thumb_branch import thumb_bl_bytes

INITIAL_CAPACITY_CALL = 0x3EB0E
INITIAL_CAPACITY_ADD = 0x3EB12
COLLECTION_MENU_CALL = 0x14380A
NATIVE_VITALITY_GETTER = 0x08019F0C
ROM_BASE = 0x08000000
PAYLOAD_START = 0x0815E000
HEALTH_CONFIG_START = 0x0815F690


def build_vitality_hook_writes(rom: bytes | bytearray, *, capacity_target: int,
                              menu_target: int) -> tuple[tuple[int, bytes], ...]:
    """Accept verified retail callsites only; already-patched input is rejected."""
    for offset in (INITIAL_CAPACITY_CALL, COLLECTION_MENU_CALL):
        expected = thumb_bl_bytes(ROM_BASE + offset, NATIVE_VITALITY_GETTER)
        if rom[offset:offset + 4] != expected:
            raise ValueError(f"unexpected Vitality getter callsite at {offset:#x}")
    if rom[INITIAL_CAPACITY_ADD:INITIAL_CAPACITY_ADD + 2] != b"\x06\x30":
        raise ValueError("unexpected native +6 health instruction")
    targets = (capacity_target, menu_target)
    if any(type(target) is not int or target & 1 or not PAYLOAD_START <= target < HEALTH_CONFIG_START
           for target in targets):
        raise ValueError("Vitality target must be aligned code inside the payload")
    if capacity_target == menu_target:
        raise ValueError("health and menu targets must be distinct")
    return (
        (INITIAL_CAPACITY_CALL, thumb_bl_bytes(ROM_BASE + INITIAL_CAPACITY_CALL, capacity_target)),
        (INITIAL_CAPACITY_ADD, b"\xc0\x46"),  # mov r8,r8 (Thumb-1 NOP), preserves flags
        (COLLECTION_MENU_CALL, thumb_bl_bytes(ROM_BASE + COLLECTION_MENU_CALL, menu_target)),
    )
