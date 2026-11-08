"""Goal Game completion flags in the authenticated native three-file save."""
import base64

from worlds import _bizhawk as bizhawk
from .copy_room_protocol import (
    COPY_ROOM_CONTEXT_ADDRESS, _session, copy_room_slot_version, decode_copy_room_snapshot,
)

GOAL_MARKER_OFFSET = 0x1000010
GOAL_MARKER = b'APGOAL2\0'
GOAL_LOCATION_BASE = 3960700
GOAL_RECORD_ADDRESS = 0x02028C68


def goal_slot_version(slot: dict) -> int:
    version = slot.get('goal_game_protocol_version', 0)
    if type(version) is not int or version not in (0, 2):
        raise ValueError('unsupported Goal Game protocol; regenerate seed and patch')
    if version and copy_room_slot_version(slot) != 2:
        raise ValueError('Goal Games require the authenticated native save context')
    return version


async def poll_goal_games(ctx) -> None:
    slot = getattr(ctx, 'slot_data', None)
    if not isinstance(slot, dict) or not goal_slot_version(slot):
        return
    session = _session(ctx)
    server = getattr(ctx, 'server', None)
    socket = getattr(server, 'socket', None)
    if socket is None or getattr(socket, 'closed', True):
        return
    try:
        auth = base64.b64decode(ctx.auth, validate=True)
    except (ValueError, TypeError):
        return
    if len(auth) != 16:
        return
    raw = await bizhawk.read(ctx.bizhawk_ctx, [
        (COPY_ROOM_CONTEXT_ADDRESS, 36, 'System Bus'),
        (GOAL_RECORD_ADDRESS, 20, 'System Bus'), (0xF00000, 16, 'ROM'),
    ])
    fence = await bizhawk.read(ctx.bizhawk_ctx, [
        (COPY_ROOM_CONTEXT_ADDRESS, 12, 'System Bus'),
        (GOAL_RECORD_ADDRESS, 20, 'System Bus'), (0xF00000, 16, 'ROM'),
    ])
    if (session != _session(ctx) or ctx.slot_data is not slot
            or getattr(ctx, "server", None) is not server
            or getattr(server, "socket", None) is not socket
            or getattr(socket, 'closed', True) or len(raw) != 3 or len(fence) != 3
            or bytes(raw[2]) != auth or bytes(fence[2]) != auth
            or bytes(raw[1]) != bytes(fence[1])):
        return
    snapshot = decode_copy_room_snapshot(bytes(raw[0]), bytes(fence[0]))
    record = bytes(raw[1])
    if snapshot is None or len(record) != 20 or record[:16] != auth:
        return
    flags = int.from_bytes(record[16:], 'little')
    if flags & ~0x1FFFF != 0x43500000:
        return
    bits = (flags >> 1) & 0xFFFF
    # Re-read persistent flags on each connection; never retain a RAM-derived queue.
    checks = {GOAL_LOCATION_BASE + bit for bit in range(16) if bits & (1 << bit)}
    missing = sorted(checks & set(ctx.missing_locations) - set(ctx.checked_locations))
    if missing:
        await ctx.send_msgs([{'cmd': 'LocationChecks', 'locations': missing}])
