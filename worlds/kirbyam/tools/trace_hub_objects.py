"""Read-only, bounded native evidence for four USA DoorToHub objects.

This proves record selection, not AP graph reachability or emulator acceptance.
No ROM bytes are emitted. See docs/hub-object-evidence.md for source references.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

try:
    from . import extract_room_evidence as room_evidence
except ImportError:
    room_evidence = importlib.import_module("extract_room_evidence")

ROOM_PROPS = room_evidence.ROOM_PROPS
SOLIDITY_TABLE = room_evidence.SOLIDITY_TABLE
USA_SHA1 = room_evidence.USA_SHA1
pointer = room_evidence.pointer
unpack = room_evidence.unpack

OBJECT_TABLE = 0xD637AC
FOREGROUND_TABLE = 0xD64520
COLLISION_ATTRIBUTES = 0x2D88B8
SPAWN_TABLE = 0x35107C
SCOPE = {192: (0x8BB3E4, 0x8BB408), 592: (0x8CEF38, 0x8CEF5C)}


def decompress_rl(rom: bytes, offset: int, expected: int) -> bytes:
    header = unpack(rom, '<I', offset)[0]
    if header & 255 != 0x30 or header >> 8 != expected or not 0 < expected <= 0x2000:
        raise ValueError('Unsupported RL header or dimensions')
    cursor = offset + 4
    result = bytearray()
    while len(result) < expected:
        control = unpack(rom, '<B', cursor)[0]
        cursor += 1
        count = (control & 127) + (3 if control & 128 else 1)
        if len(result) + count > expected:
            raise ValueError('RL output overrun')
        if control & 128:
            result.extend([unpack(rom, '<B', cursor)[0]] * count)
            cursor += 1
        else:
            result.extend(unpack(rom, f'<{count}B', cursor))
            cursor += count
    return bytes(result)


def records(rom: bytes, cursor: int) -> list[dict[str, int]]:
    result: list[dict[str, int]] = []
    for _ in range(4096):
        if unpack(rom, '<B', cursor)[0] == 0:
            return result
        kind, attribute, x, y, size = unpack(rom, '<4BH', cursor)
        if size != {1: 18, 2: 14, 3: 14}.get(kind):
            raise ValueError('Unsupported solidity record')
        unpack(rom, f'<{size}x', cursor)
        result.append(dict(offset=cursor, kind=kind, attribute=attribute, x=x, y=y))
        cursor += size
    raise ValueError('Unterminated solidity list')


def select(entries: list[dict[str, int]], x: int, y: int, attribute: int) -> dict[str, int]:
    matches = [r for r in entries if (r['x'], r['y'], r['attribute']) == (x, y, attribute)]
    if len(matches) != 1:
        raise ValueError('Missing or ambiguous collision-state record')
    return matches[0]


def trace_state(rom: bytes, entries: list[dict[str, int]], x: int, y: int,
                attribute: int) -> dict[str, Any]:
    closed = select(entries, x, y, attribute)
    if closed['kind'] not in (1, 2):
        raise ValueError('Expected closed mutation record')
    if unpack(rom, '<I', COLLISION_ATTRIBUTES + attribute * 4)[0] & 0x4000:
        raise ValueError('Initial tile already open')
    replacement = unpack(rom, '<B', closed['offset'] + (16 if closed['kind'] == 1 else 12))[0]
    if not unpack(rom, '<I', COLLISION_ATTRIBUTES + replacement * 4)[0] & 0x4000:
        raise ValueError('Replacement is not a transition tile')
    opened = select(entries, x, y, replacement)
    if opened['kind'] != 3:
        raise ValueError('Expected open transition record')
    dest, sx, sy, flags = unpack(rom, '<HBBB', opened['offset'] + 8)
    if dest >= 0x9998 // 40:
        raise ValueError('Destination out of range')
    return dict(closed_record=closed['offset'], closed_attribute=attribute,
                open_record=opened['offset'], open_attribute=replacement,
                destination_room=dest, spawn_tiles=[sx, sy], transition_flags=flags,
                zero_unlock='closed; no mutation', nonzero_unlock='replace tile; select open record')


def build_evidence(rom: bytes, contract: dict[str, Any]) -> dict[str, Any]:
    if len(rom) != 0x1000000 or hashlib.sha1(rom).hexdigest() != USA_SHA1:
        raise ValueError('Requires unmodified USA ROM')
    if unpack(rom, '<I', SPAWN_TABLE + 0x97 * 4)[0] != 0x0802AAF9:
        raise ValueError('Unexpected DoorToHub handler')
    output = []
    for room, expected_objects in SCOPE.items():
        fields = unpack(rom, '<20H', ROOM_PROPS + room * 40)
        if max(fields[12], fields[13], fields[16]) >= 287:
            raise ValueError('Table index out of range')
        foreground = pointer(rom, FOREGROUND_TABLE + fields[12] * 4)
        width, height = unpack(rom, '<HH', foreground)
        if width % 2 or height % 2:
            raise ValueError('Unsupported dimensions')
        width, height = width // 2, height // 2
        solidity = pointer(rom, SOLIDITY_TABLE + fields[13] * 4)
        grid = decompress_rl(rom, pointer(rom, solidity), width * height)
        entries = records(rom, pointer(rom, solidity + 4))
        cursor = pointer(rom, pointer(rom, OBJECT_TABLE + fields[16] * 4))
        found = []
        for _ in range(4096):
            table, size = unpack(rom, '<BB', cursor)
            if size == 0:
                break
            if size < 14:
                raise ValueError('Short object record')
            unpack(rom, f'<{size}x', cursor)
            if unpack(rom, '<B', cursor + 12)[0] == 0x97:
                if table != 1 or size != 36 or unpack(rom, '<H', cursor + 34)[0] != 0:
                    raise ValueError('Unsupported DoorToHub variant')
                found.append(cursor)
                px, py = unpack(rom, '<hh', cursor + 6)
                x, y = px // 16, (py - 8) // 16
                if y != (py * 256 - 0xFFF) >> 12 or not (0 <= x < width and 0 <= y < height):
                    raise ValueError('Unsupported lookup coordinates')
                unlock = unpack(rom, '<B', cursor + 4)[0]
                mapping = [e for e in contract['entries'] if e['world_props_unlock_index'] == unlock]
                if len(mapping) != 1:
                    raise ValueError('Unknown or ambiguous unlock index')
                output.append(dict(room=room, object_offset=cursor, pixels=[px, py], tile=[x, y],
                                   unlock_index=unlock, switch_contract=mapping[0],
                                   **trace_state(rom, entries, x, y, grid[y * width + x])))
            cursor += size
        else:
            raise ValueError('Unterminated object list')
        if tuple(found) != expected_objects:
            raise ValueError('Unexpected scoped object inventory')
    return dict(rom_sha1=USA_SHA1, objects=output, graph_edges_added=0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    args = parser.parse_args()
    contract = json.loads((Path(__file__).parents[1] / 'data/hub_switch_contract.json').read_text())
    print(json.dumps(build_evidence(args.rom.read_bytes(), contract), indent=2))


if __name__ == '__main__':
    main()
