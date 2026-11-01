"""Native Invincible Candy eligibility; no custom invincibility behavior."""

CANDY_ITEM_ID = 3860029
# Retail gUnk_0835105C[1:9]; patch construction verifies this table.
CANDY_EXCLUDED_ROOMS = frozenset((801, 324, 710, 417, 822, 219, 516, 738, 129))


def candy_delivery_ready(room: int, task: int, flags: int, hp: int) -> bool:
    """Wait until the native effect can start, without replacing active Candy."""
    return (0 <= room <= 899 and room not in CANDY_EXCLUDED_ROOMS
            and 0x03000000 <= task < 0x03008000 and task % 4 == 0
            and hp > 0 and not flags & 0x40)
