"""Copy Ability Room ownership, synchronized only from authenticated history."""
import base64
from worlds import _bizhawk as bizhawk
from .shared_save_protocol import read_shared_snapshot, SHARED_CONTEXT_ADDRESS

COPY_ROOM_ITEM_ID = 3860500
COPY_ROOM_PROTOCOL_VERSION = 1
COPY_ROOM_MARKER_OFFSET = 0x100FFD4
COPY_ROOM_MARKER = b'APCPY01\0'
COPY_ROOM_REQUEST_ADDRESS = 0x0203B160


def copy_room_slot_version(slot: dict) -> int:
    version = slot.get('copy_ability_room_protocol_version', 0)
    if type(version) is not int or version not in (0, COPY_ROOM_PROTOCOL_VERSION):
        raise ValueError('unsupported Copy Ability Room protocol')
    if not version and 'Copy Ability Room Access' in slot.get('unique_items', ()):
        raise ValueError('Copy Ability Room item requires a compatible slot')
    if version and (type(slot.get('shared_save_protocol_version')) is not int
                    or slot.get('shared_save_protocol_version') != 1):
        raise ValueError('Copy Ability Room requires shared save protocol 1')
    return version


async def sync_copy_room_ownership(ctx, history_ready) -> bool:
    """Fence a complete history snapshot and the native context at write time."""
    slot = getattr(ctx, 'slot_data', {})
    if not copy_room_slot_version(slot) or not history_ready(ctx):
        return False
    server = ctx.server
    socket = server.socket
    auth = ctx.auth
    items = tuple(ctx.items_received)
    owned = slot.get('starting_copy_ability_room_access', False)
    if type(owned) is not bool:
        raise ValueError('invalid starting Copy Ability Room ownership')
    owned = owned or any(getattr(item, 'item', None) == COPY_ROOM_ITEM_ID for item in items)
    snapshot = await read_shared_snapshot(ctx)
    if (snapshot is None or ctx.server is not server or server.socket is not socket
            or ctx.auth != auth or ctx.slot_data is not slot or not history_ready(ctx)
            or tuple(ctx.items_received) != items):
        return False
    # This command batch checks the epoch and ROM identity immediately before
    # writing. Runtime checks the epoch again before changing native ownership.
    return await bizhawk.guarded_write(ctx.bizhawk_ctx, [
        (COPY_ROOM_REQUEST_ADDRESS + 4, int(owned).to_bytes(4, 'little'), 'System Bus'),
        (COPY_ROOM_REQUEST_ADDRESS, snapshot.epoch.to_bytes(4, 'little'), 'System Bus'),
    ], [
        (SHARED_CONTEXT_ADDRESS, snapshot.epoch.to_bytes(4, 'little'), 'System Bus'),
        (SHARED_CONTEXT_ADDRESS + 8, snapshot.slot.to_bytes(4, 'little'), 'System Bus'),
        (0xF00000, base64.b64decode(auth, validate=True), 'ROM'),
    ])
