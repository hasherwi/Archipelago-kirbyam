"""Completed Goal Games are read from the authenticated shared native save."""
from .shared_save_protocol import read_shared_snapshot, shared_slot_version

GOAL_MARKER_OFFSET = 0x1000018
GOAL_MARKER = b'APGOAL1\0'
GOAL_LOCATION_BASE = 3960700


def goal_slot_version(slot: dict) -> int:
    version = slot.get('goal_game_protocol_version', 0)
    if type(version) is not int or version not in (0, 1):
        raise ValueError('unsupported Goal Game protocol')
    if version and shared_slot_version(slot) != 1:
        raise ValueError('Goal Games require authenticated shared saves')
    return version


async def poll_goal_games(ctx) -> None:
    slot = getattr(ctx, 'slot_data', None)
    if not isinstance(slot, dict) or not goal_slot_version(slot):
        return
    server = getattr(ctx, 'server', None)
    socket = getattr(server, 'socket', None)
    snapshot = await read_shared_snapshot(ctx)
    if snapshot is None or getattr(ctx, 'slot_data', None) is not slot:
        return
    # Do not queue RAM-derived checks across reconnects. Re-read the active save
    # on every poll; resend until acknowledged by this AP session.
    if (getattr(ctx, 'server', None) is not server
            or getattr(server, 'socket', None) is not socket):
        return
    if socket is None or getattr(socket, 'closed', True):
        return
    checks = {GOAL_LOCATION_BASE + bit for bit in range(16) if snapshot.bits & (1 << bit)}
    missing = sorted(checks & set(ctx.missing_locations) - set(ctx.checked_locations))
    if missing:
        await ctx.send_msgs([{'cmd': 'LocationChecks', 'locations': missing}])
