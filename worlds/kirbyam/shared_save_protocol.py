"""Shared Goal Game / Copy Room save-context contract (version 1)."""
import base64
from dataclasses import dataclass

from worlds._bizhawk import read

SHARED_PROTOCOL_VERSION = 1
SHARED_MARKER_OFFSET = 0x1000010
SHARED_MARKER = b'APSHR01\0'
SHARED_CONTEXT_ADDRESS = 0x0203B13C
SHARED_GOALS_MASK = 0xFFFF
SHARED_ACCESS_OWNED = 1 << 16
SHARED_ACCESS_VALID = 1 << 17
SHARED_FEATURE_MASK = (1 << 18) - 1


def shared_slot_version(slot: dict) -> int:
    value = slot.get('shared_save_protocol_version', 0)
    if type(value) is not int or value not in (0, SHARED_PROTOCOL_VERSION):
        raise ValueError('unsupported shared save protocol')
    return value


@dataclass(frozen=True)
class SharedSaveSnapshot:
    epoch: int
    slot: int
    bits: int
    dirty: bool


def decode_shared_snapshot(raw: bytes, fence: bytes) -> SharedSaveSnapshot | None:
    """Fence a snapshot across asynchronous connector reads and native reloads."""
    if len(raw) != 36 or len(fence) != 12 or raw[:12] != fence:
        return None
    words = [int.from_bytes(raw[i:i+4], 'little') for i in range(0, 36, 4)]
    epoch, serial, slot, dirty, loaded_slot, task, bits, cookie, _retry = words
    if (not epoch or epoch != serial or slot >= 3 or loaded_slot != slot
            or dirty not in (0, 1) or bits & ~SHARED_FEATURE_MASK
            or cookie != 0x41505331 or not 0x03000000 <= task <= 0x03007FEC or task & 3):
        return None
    return SharedSaveSnapshot(epoch, slot, bits, bool(dirty))


async def read_shared_snapshot(ctx) -> SharedSaveSnapshot | None:
    """Use only after ROM/slot authentication. Retain no pending checks here."""
    session = (getattr(ctx, 'server_seed_name', None), ctx.auth, ctx.team, ctx.slot,
               getattr(ctx, 'server', None), getattr(getattr(ctx, 'server', None), 'socket', None),
               getattr(ctx, 'bizhawk_ctx', None))
    try:
        auth = base64.b64decode(ctx.auth, validate=True)
    except (ValueError, TypeError):
        return None
    if len(auth) != 16:
        return None
    raw = await read(ctx.bizhawk_ctx, [(SHARED_CONTEXT_ADDRESS, 36, 'System Bus'),
                                     (0xF00000, 16, 'ROM')])
    fence = await read(ctx.bizhawk_ctx, [(SHARED_CONTEXT_ADDRESS, 12, 'System Bus'),
                                       (0xF00000, 16, 'ROM')])
    if session != (getattr(ctx, 'server_seed_name', None), ctx.auth, ctx.team, ctx.slot,
                   getattr(ctx, 'server', None), getattr(getattr(ctx, 'server', None), 'socket', None),
                   getattr(ctx, 'bizhawk_ctx', None)):
        return None
    if len(raw) != 2 or len(fence) != 2 or bytes(raw[1]) != auth or bytes(fence[1]) != auth:
        return None
    return decode_shared_snapshot(bytes(raw[0]), bytes(fence[0]))
