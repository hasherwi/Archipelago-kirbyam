"""Seed-authenticated Copy Room ownership on the native three-file save layout."""
import base64
from dataclasses import dataclass
from typing import Any, Callable

from worlds import _bizhawk as bizhawk

COPY_ROOM_ITEM_ID = 3860500
COPY_ROOM_PROTOCOL_VERSION = 2
COPY_ROOM_MARKER_OFFSET = 0x100FFD4
COPY_ROOM_MARKER = b"APCPY02\0"
COPY_ROOM_CONTEXT_ADDRESS = 0x0203B13C
COPY_ROOM_REQUEST_ADDRESS = 0x0203B160


def copy_room_slot_version(slot: dict[str, Any]) -> int:
    version = slot.get("copy_ability_room_protocol_version", 0)
    if type(version) is not int or version not in (0, COPY_ROOM_PROTOCOL_VERSION):
        raise ValueError("unsupported Copy Ability Room protocol; regenerate seed and patch")
    if not version and "Copy Ability Room Access" in slot.get("unique_items", ()):
        raise ValueError("Copy Ability Room item requires a compatible slot")
    if version and slot.get("shared_save_protocol_version", 0):
        raise ValueError("Copy Ability Room protocol 2 requires the native save layout")
    return version


@dataclass(frozen=True)
class CopyRoomSnapshot:
    epoch: int
    slot: int
    owned: bool
    dirty: bool


def decode_copy_room_snapshot(raw: bytes, fence: bytes) -> CopyRoomSnapshot | None:
    if len(raw) != 36 or len(fence) != 12 or raw[:12] != fence:
        return None
    epoch, serial, slot, dirty, loaded_slot, task, owned, cookie, _retry = (
        int.from_bytes(raw[i:i+4], "little") for i in range(0, 36, 4)
    )
    if (not epoch or epoch != serial or slot > 2 or loaded_slot != slot
            or dirty not in (0, 1) or owned not in (0, 1) or cookie != 0x43504332
            or not 0x03000000 <= task <= 0x03007FEC or task & 3):
        return None
    return CopyRoomSnapshot(epoch, slot, bool(owned), bool(dirty))


def _session(ctx: Any) -> tuple[Any, ...]:
    return (getattr(ctx, "server_seed_name", None), ctx.auth,
            getattr(ctx, "team", None), getattr(ctx, "slot", None),
            getattr(ctx, "server", None), getattr(getattr(ctx, "server", None), "socket", None),
            ctx.bizhawk_ctx)


async def sync_copy_room_ownership(ctx: Any, history_ready: Callable[[Any], bool]) -> bool:
    """Grant permanently within the authenticated native file; never revoke."""
    slot = getattr(ctx, "slot_data", {})
    if not copy_room_slot_version(slot) or not history_ready(ctx):
        return False
    session = _session(ctx)
    items = tuple(ctx.items_received)
    owned = slot.get("starting_copy_ability_room_access", False)
    if type(owned) is not bool:
        raise ValueError("invalid starting Copy Ability Room ownership")
    owned = owned or any(getattr(item, "item", None) == COPY_ROOM_ITEM_ID for item in items)
    if not owned:
        return False  # No grant evidence. Preserve saved ownership, including offline grants.
    try:
        auth = base64.b64decode(ctx.auth, validate=True)
    except (ValueError, TypeError):
        return False
    if len(auth) != 16:
        return False
    raw = await bizhawk.read(ctx.bizhawk_ctx, [
        (COPY_ROOM_CONTEXT_ADDRESS, 36, "System Bus"), (0xF00000, 16, "ROM")])
    fence = await bizhawk.read(ctx.bizhawk_ctx, [
        (COPY_ROOM_CONTEXT_ADDRESS, 12, "System Bus"), (0xF00000, 16, "ROM")])
    if (session != _session(ctx) or ctx.slot_data is not slot or not history_ready(ctx)
            or tuple(ctx.items_received) != items or len(raw) != 2 or len(fence) != 2
            or bytes(raw[1]) != auth or bytes(fence[1]) != auth):
        return False
    snapshot = decode_copy_room_snapshot(bytes(raw[0]), bytes(fence[0]))
    if snapshot is None:
        return False
    if snapshot.owned:
        return True
    # The native handler checks the epoch, selected/loaded file, live task and
    # saved seed identity again. Publish request epoch last, never write WORLD.
    return await bizhawk.guarded_write(ctx.bizhawk_ctx, [
        (COPY_ROOM_REQUEST_ADDRESS + 4, (1).to_bytes(4, "little"), "System Bus"),
        (COPY_ROOM_REQUEST_ADDRESS, snapshot.epoch.to_bytes(4, "little"), "System Bus"),
    ], [
        (COPY_ROOM_CONTEXT_ADDRESS, bytes(fence[0]), "System Bus"),
        (0xF00000, auth, "ROM"),
    ])
