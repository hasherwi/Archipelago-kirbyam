"""Extract room identities, completion records and transitions from the USA ROM.

No ROM bytes are emitted. This is evidence, not a generator for AP logic edges.
Layouts: jiangzhengwenjz/katam at 7d969fbce14fdc838d2c1ea01389717fb96c3189,
include/data.h, src/level.c and src/code_080023A4.c. In particular, doorsIdx
indexes completion records; tile-triggered transitions live in gSolidityMaps.unk4.
Object-driven doors and traversability conditions are outside this decoder.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
from typing import Any

USA_SHA1 = "274b102b6d940f46861a92b4e65f89a51815c12c"
ROM_BASE = 0x08000000
ROOM_PROPS = 0x9331AC
ROOM_COUNT = 0x9998 // 0x28
SOLIDITY_TABLE = 0xD63330
COMPLETION_TABLE = 0xD640A4
TABLE_COUNT = 287


def unpack(rom: bytes, fmt: str, offset: int) -> tuple[int, ...]:
    size = struct.calcsize(fmt)
    if offset < 0 or offset + size > len(rom):
        raise ValueError(f"ROM read out of bounds: {offset:#x} + {size}")
    return struct.unpack_from(fmt, rom, offset)


def pointer(rom: bytes, offset: int) -> int:
    result = unpack(rom, "<I", offset)[0] - ROM_BASE
    if not 0 <= result < len(rom):
        raise ValueError(f"Invalid ROM pointer at {offset:#x}")
    return result


def extract_room(rom: bytes, room_id: int, rooms: dict[str, Any]) -> dict[str, Any]:
    if not 0 <= room_id < ROOM_COUNT:
        raise ValueError(f"Invalid native room: {room_id}")
    props = ROOM_PROPS + room_id * 0x28
    fields = unpack(rom, "<20H", props)
    solidity_idx, object_idx, doors_idx = fields[13], fields[16], fields[18]
    if max(solidity_idx, object_idx, doors_idx) >= TABLE_COUNT:
        raise ValueError("Room table index out of bounds")
    keys = []
    for key, room in rooms.items():
        sanity = room.get("room_sanity") or (room.get("locations") or {}).get("room_sanity") or {}
        if sanity.get("included") and sanity.get("bit_index") == doors_idx:
            keys.append(key)

    completion_header = pointer(rom, COMPLETION_TABLE + doors_idx * 4)
    count = unpack(rom, "<B", completion_header + 4)[0]
    if count > 15:  # top bit is the room-visited bit in gVisitedDoors
        raise ValueError("Too many room completion entries")
    cursor = pointer(rom, completion_header) if count else 0
    completion = []
    for _ in range(count):
        kind, size = unpack(rom, "<BB", cursor)
        if kind not in (1, 2) or size != 8:
            raise ValueError(f"Unknown completion record at {cursor:#x}")
        entry: dict[str, Any] = {"rom_offset": cursor, "kind": kind}
        if kind == 1:
            entry["chest_position_pixels"] = list(unpack(rom, "<hh", cursor + 4))
        else:
            destination, x, y = unpack(rom, "<HBB", cursor + 4)
            entry.update(destination_room=destination, destination_spawn_tiles=[x, y])
        completion.append(entry)
        cursor += size

    solidity_header = pointer(rom, SOLIDITY_TABLE + solidity_idx * 4)
    cursor = pointer(rom, solidity_header + 4)
    transitions = []
    for _ in range(4096):  # reject malformed lists instead of walking arbitrary ROM data
        kind = unpack(rom, "<B", cursor)[0]
        if kind == 0:  # zero-kind terminator observed in the pinned USA lists
            break
        kind, attribute, x, y, size = unpack(rom, "<4BH", cursor)
        expected_size = {1: 0x12, 2: 0xE, 3: 0xE}.get(kind)
        if expected_size is None or size != expected_size:
            raise ValueError(f"Unknown solidity record at {cursor:#x}")
        unpack(rom, f"<{size}x", cursor)  # include unused fields and alignment padding
        if kind == 3:
            destination, spawn_x, spawn_y = unpack(rom, "<HBB", cursor + 8)
            if destination >= ROOM_COUNT:
                raise ValueError(f"Invalid destination room at {cursor:#x}")
            transition_flags = unpack(rom, "<B", cursor + 0xC)[0]
            transitions.append({
                "rom_offset": cursor,
                "source_tiles": [x, y],
                "collision_attribute": attribute,
                "transition_flags": transition_flags,
                "destination_room": destination,
                "destination_spawn_tiles": [spawn_x, spawn_y],
            })
        cursor += size
    else:
        raise ValueError("Unterminated solidity record list")

    return {
        "native_room_id": room_id,
        "room_props_rom_offset": props,
        "object_list_idx": object_idx,
        "solidity_map_idx": solidity_idx,
        "doors_idx": doors_idx,
        "ap_room_keys": sorted(keys),
        "completion_entries": completion,
        "transitions": transitions,
    }


def build_evidence(rom: bytes, room_ids: list[int], rooms: dict[str, Any]) -> dict[str, Any]:
    if len(rom) != 0x1000000 or hashlib.sha1(rom).hexdigest() != USA_SHA1:
        raise ValueError("Expected the unmodified USA ROM (size and SHA-1 mismatch)")
    return {
        "rom_sha1": USA_SHA1,
        "source_commit": "7d969fbce14fdc838d2c1ea01389717fb96c3189",
        "scope": "Completion and tile-triggered transition records only; object-driven doors, collision-state conditions, AP routes, ability requirements and gameplay acceptance are not inferred.",
        "rooms": [extract_room(rom, room_id, rooms) for room_id in room_ids],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--room", type=int, action="append", required=True)
    parser.add_argument("--rooms", type=Path,
                        default=Path(__file__).resolve().parents[1] / "data/regions/rooms.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    evidence = build_evidence(args.rom.read_bytes(), args.room, json.loads(args.rooms.read_text()))
    args.output.write_text(json.dumps(evidence, indent=2) + "\n")
    print(f"Wrote evidence for {len(evidence['rooms'])} native rooms to {args.output}")


if __name__ == "__main__":
    main()
