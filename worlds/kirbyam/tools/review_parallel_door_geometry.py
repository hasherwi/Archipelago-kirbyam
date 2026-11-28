"""Reproduce the selected native parallel-port profiles from a local USA ROM."""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import json
from pathlib import Path

from .extract_room_evidence import ROOM_PROPS, SOLIDITY_TABLE, USA_SHA1, extract_room, pointer, unpack

FOREGROUND_TABLE = 0xD64520
STRICT_CELLS = {0x00, 0x48, 0xF3, 0xFC, 0xFD, 0xFE, 0xFF}
PLAIN_SOLID_CELLS = {0x0D, *range(0x22, 0x28)}


def decode_rl(rom: bytes, offset: int, expected_cells: int) -> bytes:
    header, = unpack(rom, "<I", offset)
    if header & 0xFF != 0x30 or header >> 8 != expected_cells:
        raise ValueError("Collision grid RL header doesn't match the room dimensions")
    cursor = offset + 4
    cells = bytearray()
    while len(cells) < expected_cells:
        control, = unpack(rom, "<B", cursor)
        cursor += 1
        if control & 0x80:
            value, = unpack(rom, "<B", cursor)
            cells.extend(bytes([value]) * ((control & 0x7F) + 3))
            cursor += 1
        else:
            count = control + 1
            cells.extend(unpack(rom, f"<{count}B", cursor))
            cursor += count
    if len(cells) != expected_cells:
        raise ValueError("Collision grid overflows the room dimensions")
    return bytes(cells)


def reachable_cells(grid: bytes, width: int, height: int, start: tuple[int, int],
                    *, optimistic: bool) -> set[tuple[int, int]]:
    """Four-neighbor cell model, explicitly not character collision physics."""
    def admitted(x: int, y: int) -> bool:
        if not 0 <= x < width or not 0 <= y < height:
            return False
        cell = grid[y * width + x]
        return cell not in PLAIN_SOLID_CELLS if optimistic else cell in STRICT_CELLS

    if not admitted(*start):
        return set()
    seen = {start}
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        for nxt in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if nxt not in seen and admitted(*nxt):
                seen.add(nxt)
                queue.append(nxt)
    return seen


def profile(rom: bytes, source: int, destination: int) -> dict:
    source_room = extract_room(rom, source, {})
    destination_room = extract_room(rom, destination, {})
    props = ROOM_PROPS + destination * 0x28
    foreground_index, = unpack(rom, "<H", props + 0x18)
    width, height = (v // 2 for v in unpack(rom, "<HH", pointer(rom, FOREGROUND_TABLE + 4 * foreground_index)))
    solidity = pointer(rom, SOLIDITY_TABLE + 4 * destination_room["solidity_map_idx"])
    cells = decode_rl(rom, pointer(rom, solidity), width * height)
    args = sorted({tuple(row["destination_spawn_tiles"]) for row in source_room["transitions"]
                   if row["destination_room"] == destination})
    centers = [(x - 1, y - 1) for x, y in args]
    arrivals = []
    for (x, y), start in zip(args, centers):
        row = {"spawn_arguments": [x, y]}
        for key in ("strict", "optimistic"):
            reached = reachable_cells(cells, width, height, start, optimistic=key == "optimistic")
            row[key] = {
                "cells": len(reached),
                "other_arrival_count": sum(p in reached for p in centers if p != start),
                "exits": sorted({exit_["destination_room"] for exit_ in destination_room["transitions"]
                                 if tuple(exit_["source_tiles"]) in reached}),
            }
        arrivals.append(row)
    return {"source_native_room": source, "destination_native_room": destination, "arrivals": arrivals}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True, help="Checked-in parallel-door-geometry.json")
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    if len(rom) != 0x1000000 or hashlib.sha1(rom).hexdigest() != USA_SHA1:
        raise ValueError("Expected the unmodified USA ROM (size and SHA-1 mismatch)")
    review = json.loads(args.review.read_text(encoding="utf-8"))
    if review["schema"] != 1 or review["rom_sha1"] != USA_SHA1:
        raise ValueError("Review does not match the extraction schema and base image")
    for expected in review["room_pairs"]:
        source, destination = expected["source_native_room"], expected["destination_native_room"]
        if profile(rom, source, destination) != expected:
            raise ValueError(f"Native geometry differs from review at {source} → {destination}")
    print(f"Verified {len(review['room_pairs'])} native room-pair profiles.")


if __name__ == "__main__":
    main()
