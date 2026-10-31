"""Verify two Radish compartment boundaries from a private unmodified USA ROM.

Outputs interpreted endpoints and component sizes, never ROM bytes. Connectivity
is deliberately over-approximated: every tile except solid attribute 13 is open.
Disconnected components prove separation; connected components do not prove play.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from importlib import import_module

evidence = import_module('.extract_room_evidence', __package__) if __package__ else import_module('extract_room_evidence')


def decompress_rl(rom: bytes, offset: int, expected: int) -> bytes:
    header = evidence.unpack(rom, '<I', offset)[0]
    if header & 255 != 0x30 or header >> 8 != expected or not 0 < expected <= 0x2000:
        raise ValueError('Unsupported RL header or dimensions')
    cursor = offset + 4
    result = bytearray()
    while len(result) < expected:
        control = evidence.unpack(rom, '<B', cursor)[0]
        cursor += 1
        count = (control & 127) + (3 if control & 128 else 1)
        if len(result) + count > expected:
            raise ValueError('RL output overrun')
        if control & 128:
            result.extend([evidence.unpack(rom, '<B', cursor)[0]] * count)
            cursor += 1
        else:
            result.extend(evidence.unpack(rom, f'<{count}B', cursor))
            cursor += count
    return bytes(result)


def component(grid: bytes, width: int, start: tuple[int, int]) -> set[tuple[int, int]]:
    height, remainder = divmod(len(grid), width)
    x, y = start
    if remainder or not (0 <= x < width and 0 <= y < height) or grid[y * width + x] == 13:
        raise ValueError('Invalid component start or grid dimensions')
    reached = {start}
    pending = [start]
    for x, y in pending:
        for a, b in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if (0 <= a < width and 0 <= b < height and grid[b * width + a] != 13
                    and (a, b) not in reached):
                reached.add((a, b))
                pending.append((a, b))
    return reached


def incoming_start(rom: bytes, source: int, offset: int, destination: int,
                   expected_spawn: tuple[int, int]) -> tuple[int, int]:
    """Decode a source-owned transition and check independently recorded provenance."""
    records = [record for record in evidence.extract_room(rom, source, {})['transitions']
               if record['rom_offset'] == offset]
    if len(records) != 1:
        raise ValueError(f'Missing incoming transition in room {source} at {offset:#x}')
    record = records[0]
    if record['destination_room'] != destination:
        raise ValueError(f'Unexpected incoming destination at {offset:#x}')
    sx, sy = record['destination_spawn_tiles']
    if (sx, sy) != expected_spawn:
        raise ValueError(f'Unexpected incoming spawn at {offset:#x}')
    # sub_080562D0: native fixed-point position, then collision-tile floor.
    return ((sx << 12) - 0x800) // 4096, ((sy << 12) - 0x701) // 4096


def verify(rom: bytes) -> dict:
    if hashlib.sha1(rom).hexdigest() != evidence.USA_SHA1:
        raise ValueError('Requires the unmodified USA ROM')
    output = {}
    # Provenance fixtures from independently decoded USA records: source room,
    # record offset and recorded spawn. These are assertions, not inferred edges.
    for room, incoming, endpoints, expected_sizes in (
        (623, ((604, 0x8A96E0, (3, 3)), (601, 0x8A89CC, (4, 12))),
         ((34, 7), (3, 15)), (161, 58)),
        (604, ((603, 0x8A9024, (4, 6)), (606, 0x8AA228, (78, 9))),
         ((102, 2), (48, 8)), (335, 108)),
    ):
        starts = [incoming_start(rom, source, offset, room, spawn)
                  for source, offset, spawn in incoming]
        fields = evidence.unpack(rom, '<20H', evidence.ROOM_PROPS + room * 40)
        foreground = evidence.pointer(rom, 0xD64520 + fields[12] * 4)
        raw_w, raw_h = evidence.unpack(rom, '<HH', foreground)
        width, height = raw_w // 2, raw_h // 2
        header = evidence.pointer(rom, evidence.SOLIDITY_TABLE + fields[13] * 4)
        grid = decompress_rl(rom, evidence.pointer(rom, header), width * height)
        parts = [component(grid, width, start) for start in starts]
        if (parts[0] & parts[1] or tuple(map(len, parts)) != expected_sizes
                or any(endpoint not in part for endpoint, part in zip(endpoints, parts))):
            raise ValueError(f'Unexpected compartment geometry for room {room}')
        if room == 623 and (11, 11) not in parts[1]:
            raise ValueError('Chest is not in the lower compartment')
        row = evidence.extract_room(rom, room, {})
        output[str(room)] = {'component_sizes': list(map(len, parts)),
                             'incoming_collision_tiles': starts,
                             'transitions': row['transitions'],
                             'completion_entries': row['completion_entries']}
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.rom.read_bytes()), indent=2))
