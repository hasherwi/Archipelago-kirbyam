"""Read-only USA KATAM collision-map inventory; emit coordinates, not ROM assets.

F5 is ordinary metal; F7 is the separate environmental-only/reinforced class.
F6 is recorded as a control, not included in the metal-room count. This scanner
covers initial maps and solidity-record replacements, not traversal acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
from typing import Any

ROOM_PROPS = 0x9331AC
FOREGROUND_TABLE = 0xD64520
SOLIDITY_TABLE = 0xD63330
COLLISION_ATTRIBUTES = 0x2D88B8
ROOM_COUNT = 0x9998 // 40
TABLE_COUNT = 287
USA_SHA1 = "274b102b6d940f46861a92b4e65f89a51815c12c"
UNUSED_SENTINEL = (65535,) * 19 + (0,)
TRACKED_TILES = (0xF5, 0xF6, 0xF7)


def unpack(rom: bytes, fmt: str, offset: int) -> tuple[int, ...]:
    size = struct.calcsize(fmt)
    if offset < 0 or offset + size > len(rom):
        raise ValueError("ROM read out of bounds")
    return struct.unpack_from(fmt, rom, offset)


def pointer(rom: bytes, offset: int) -> int:
    value = unpack(rom, "<I", offset)[0] - 0x08000000
    if not 0 <= value < len(rom):
        raise ValueError("Invalid pointer")
    return value


def decompress_rl(rom: bytes, offset: int, expected: int) -> bytes:
    header = unpack(rom, "<I", offset)[0]
    if header & 255 != 0x30 or header >> 8 != expected or not 0 < expected <= 0x2000:
        raise ValueError("Unsupported RL header or dimensions")
    cursor = offset + 4
    result = bytearray()
    while len(result) < expected:
        control = unpack(rom, "<B", cursor)[0]
        cursor += 1
        count = (control & 127) + (3 if control & 128 else 1)
        if len(result) + count > expected:
            raise ValueError("RL output overrun")
        if control & 128:
            result.extend([unpack(rom, "<B", cursor)[0]] * count)
            cursor += 1
        else:
            result.extend(unpack(rom, f"<{count}B", cursor))
            cursor += count
    return bytes(result)


def records(rom: bytes, cursor: int) -> list[dict[str, int]]:
    result: list[dict[str, int]] = []
    for _ in range(4096):
        if unpack(rom, "<B", cursor)[0] == 0:
            return result
        kind, attribute, x, y, size = unpack(rom, "<4BH", cursor)
        if size != {1: 18, 2: 14, 3: 14}.get(kind):
            raise ValueError("Unsupported solidity record")
        unpack(rom, f"<{size}x", cursor)
        result.append(dict(offset=cursor, kind=kind, attribute=attribute, x=x, y=y))
        cursor += size
    raise ValueError("Unterminated solidity list")


def extract_room(rom: bytes, room: int, props: tuple[int, ...]) -> dict[str, Any]:
    if props[12] >= TABLE_COUNT or props[13] >= TABLE_COUNT:
        raise ValueError("Room table index out of range")
    foreground = pointer(rom, FOREGROUND_TABLE + props[12] * 4)
    width, height = unpack(rom, "<HH", foreground)
    if width % 2 or height % 2:
        raise ValueError("Odd foreground dimensions")
    width //= 2
    height //= 2
    solidity = pointer(rom, SOLIDITY_TABLE + props[13] * 4)
    grid = decompress_rl(rom, pointer(rom, solidity), width * height)
    entries = records(rom, pointer(rom, solidity + 4))
    tiles = [dict(x=i % width, y=i // width, tile=hex(value))
             for i, value in enumerate(grid) if value in TRACKED_TILES]
    mutations = []
    for entry in entries:
        replacement = None
        if entry["kind"] in (1, 2):
            offset = entry["offset"] + (16 if entry["kind"] == 1 else 12)
            replacement = unpack(rom, "<B", offset)[0]
        if entry["attribute"] in TRACKED_TILES or replacement in TRACKED_TILES:
            mutations.append(dict(entry, replacement=replacement))
    return dict(room=room, width=width, height=height, tiles=tiles, records=mutations)


def build_inventory(rom: bytes) -> dict[str, Any]:
    if len(rom) != 0x1000000 or hashlib.sha1(rom).hexdigest() != USA_SHA1:
        raise ValueError("Expected the unmodified USA ROM (size and SHA-1 mismatch)")
    attributes = {hex(i): hex(unpack(rom, "<I", COLLISION_ATTRIBUTES + i * 4)[0]) for i in TRACKED_TILES}
    output: dict[str, Any] = dict(sha1=USA_SHA1, count=ROOM_COUNT, attributes=attributes,
                                  rooms=[], errors=[], unused_slots=[], valid_room_ids=[])
    for room in range(ROOM_COUNT):
        props = unpack(rom, "<20H", ROOM_PROPS + room * 40)
        if props == UNUSED_SENTINEL:
            output["unused_slots"].append(room)
            continue
        # Fail closed: never publish a partial inventory as an exhaustive result.
        entry = extract_room(rom, room, props)
        output["valid_room_ids"].append(room)
        if entry["tiles"] or entry["records"]:
            output["rooms"].append(entry)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path, help="Privately held unmodified USA ROM; never emitted")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = build_inventory(args.rom.read_bytes())
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
