"""Experimental Phone receipt transport; no generation option is enabled yet.

Ownership shares the authenticated native-file record with Copy Room, but has
its own request queue. Empty histories cannot revoke either item.
"""
import base64
from typing import Any, Callable

from worlds import _bizhawk as bizhawk
from .copy_room_protocol import (
    COPY_ROOM_CONTEXT_ADDRESS, _session, copy_room_slot_version, decode_copy_room_snapshot,
)

PHONE_ITEM_ID = 3860501
PHONE_PROTOCOL_VERSION = 1
PHONE_CONFIG_OFFSET = 0x100FFC8
PHONE_MARKER = b"APPHN01\0"
PHONE_ENABLED_CONFIG = PHONE_MARKER + b"\1\0\0\0"
PHONE_CONTEXT_ADDRESS = 0x0203B170
PHONE_REQUEST_ADDRESS = 0x0203B180
PHONE_COOKIE = 0x50484E31


def phone_slot_version(slot: dict[str, Any]) -> int:
    version = slot.get("phone_protocol_version", 0)
    if type(version) is not int or version not in (0, PHONE_PROTOCOL_VERSION):
        raise ValueError("unsupported Phone protocol; regenerate seed and patch")
    if not version and "Phone a Friend" in slot.get("unique_items", ()):
        raise ValueError("Phone item requires a compatible slot")
    if version and copy_room_slot_version(slot) != 2:
        raise ValueError("Phone protocol requires authenticated native-file ownership")
    return version


async def sync_phone_ownership(ctx: Any, history_ready: Callable[[Any], bool]) -> bool:
    """Grant only after complete history, ROM identity and native-file fencing."""
    slot = getattr(ctx, "slot_data", {})
    if not phone_slot_version(slot) or not history_ready(ctx):
        return False
    session = _session(ctx)
    items = tuple(ctx.items_received)
    owned = slot.get("starting_phone_access", False)
    if type(owned) is not bool:
        raise ValueError("invalid starting Phone ownership")
    if not owned and not any(getattr(item, "item", None) == PHONE_ITEM_ID for item in items):
        return False
    try:
        auth = base64.b64decode(ctx.auth, validate=True)
    except (ValueError, TypeError):
        return False
    if len(auth) != 16:
        return False
    reads = [(COPY_ROOM_CONTEXT_ADDRESS, 36, "System Bus"),
             (PHONE_CONTEXT_ADDRESS, 16, "System Bus"),
             (0xF00000, 16, "ROM"), (PHONE_CONFIG_OFFSET, 12, "ROM")]
    raw = await bizhawk.read(ctx.bizhawk_ctx, reads)
    fence = await bizhawk.read(ctx.bizhawk_ctx, [(COPY_ROOM_CONTEXT_ADDRESS, 12, "System Bus"), *reads[1:]])
    if (session != _session(ctx) or ctx.slot_data is not slot or not history_ready(ctx)
            or tuple(ctx.items_received) != items or len(raw) != 4 or len(fence) != 4
            or bytes(raw[2]) != auth or bytes(fence[2]) != auth
            or bytes(raw[3]) != PHONE_ENABLED_CONFIG or bytes(fence[3]) != PHONE_ENABLED_CONFIG
            or bytes(raw[1]) != bytes(fence[1]) or len(raw[1]) != 16):
        return False
    snapshot = decode_copy_room_snapshot(bytes(raw[0]), bytes(fence[0]))
    epoch, native_slot, saved, cookie = (int.from_bytes(raw[1][i:i + 4], "little") for i in range(0, 16, 4))
    if (snapshot is None or epoch != snapshot.epoch or native_slot != snapshot.slot
            or saved not in (0, 1) or cookie != PHONE_COOKIE):
        return False
    if saved:
        return True
    return await bizhawk.guarded_write(ctx.bizhawk_ctx, [
        (PHONE_REQUEST_ADDRESS + 4, (1).to_bytes(4, "little"), "System Bus"),
        (PHONE_REQUEST_ADDRESS, epoch.to_bytes(4, "little"), "System Bus"),
    ], [
        (COPY_ROOM_CONTEXT_ADDRESS, bytes(fence[0]), "System Bus"),
        (PHONE_CONTEXT_ADDRESS, bytes(fence[1]), "System Bus"),
        (0xF00000, auth, "ROM"), (PHONE_CONFIG_OFFSET, PHONE_ENABLED_CONFIG, "ROM"),
    ])
