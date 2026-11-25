"""Immutable per-seed assignments for randomized world statues, not room 970."""
from .enemy_ability_runtime_patch import _STATUE_TABLES

STATUE_CONFIG_ROM_OFFSET = 0x100EE00
STATUE_CONFIG_MARKER = b"APST01\0\0"
STATUE_SLOT_ADDRESSES = tuple(address + index for address, abilities in _STATUE_TABLES
                              for index in range(len(abilities)))
STATUE_CONFIG_EMPTY = STATUE_CONFIG_MARKER + bytes(20)
COPY_ABILITY_ROOM = 970


def build_statue_seed_config(mode: int, enabled: bool, writes: dict[int, int]) -> bytes:
    if not enabled or not mode:
        return STATUE_CONFIG_EMPTY
    if mode not in (1, 2):
        raise ValueError(f"Unknown statue randomization mode {mode}")
    try:
        grants = bytes(writes[address] for address in STATUE_SLOT_ADDRESSES)
    except KeyError as exc:
        raise ValueError("Missing verified statue assignment") from exc
    if len(grants) != 19 or any(not 0 < ability < 32 for ability in grants):
        raise ValueError("Invalid statue ability ID in assignment")
    return STATUE_CONFIG_MARKER + bytes([mode]) + grants
