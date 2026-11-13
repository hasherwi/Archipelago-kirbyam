#!/usr/bin/env python3
"""Enrich a spawn-table-1 native object mapping with per-room ROM usage counts.

ObjectTemplate types are local to their spawn table. This helper accepts only
mappings of table-1 type IDs (the OBJ_* / gSpawnFuncTable1 namespace); it does
not merge table-2 records into those IDs and rejects unknown spawn tables. The optional default
mapping file is not distributed here, so callers must verify that convention
for their input mapping.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, List

ROM_BASE = 0x08000000

LEVEL_OBJ_LISTS_ADDR = 0x08D637AC
LEVEL_OBJ_LISTS_COUNT = 287

ROOM_PROPS_ADDR = 0x089331AC
ROOM_PROPS_SIZE = 0x00009998
ROOM_PROPS_STRIDE = 0x28
ROOM_PROPS_OBJECT_LIST2_IDX_OFFSET = 0x1C
ROOM_PROPS_OBJECT_LIST_IDX_OFFSET = 0x20
ROOM_PROPS_DOORS_IDX_OFFSET = 0x24

LEVEL_INFO_1E4_SIZE = 0x10
LEVEL_INFO_1E4_OBJ_PTR_OFFSET = 0x00
# Header +0x0C counts distinct spawn-table-1 types, not object records.
LEVEL_INFO_1E4_COUNT_OFFSET = 0x0C

OBJECT_SIZE = 0x24
OBJECT_SIZE_OFFSET = 0x01
OBJECT_SPAWN_TABLE_OFFSET = 0x00
MAPPING_SPAWN_TABLE = 1
OBJECT_TYPE_OFFSET = 0x0C


ROOT = Path(__file__).resolve().parents[3]
MAPPING_PATH = ROOT / "worlds" / "kirbyam" / "data" / "native_item_id_to_name_mapping.json"
ROOMS_PATH = ROOT / "worlds" / "kirbyam" / "data" / "regions" / "rooms.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enrich a spawn-table-1 native object mapping with per-room ROM usage counts.",
    )
    parser.add_argument(
        "--rom",
        type=Path,
        required=True,
        help="Path to Kirby & The Amazing Mirror ROM (required).",
    )
    parser.add_argument(
        "--mapping",
        type=Path,
        default=MAPPING_PATH,
        help=f"Path to spawn-table-1 type-ID mapping JSON (default: {MAPPING_PATH}).",
    )
    parser.add_argument(
        "--rooms",
        type=Path,
        default=ROOMS_PATH,
        help=f"Path to AP rooms JSON (default: {ROOMS_PATH}).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path (default: <mapping>.enriched.json). Ignored when --in-place is used.",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Overwrite the mapping file in place.",
    )
    return parser.parse_args()


def gba_addr_to_offset(addr: int) -> int:
    if addr < ROM_BASE:
        raise ValueError(f"Address 0x{addr:08X} is not in GBA ROM region")
    return addr - ROM_BASE


def require_bytes(data: bytes, offset: int, size: int) -> None:
    if offset < 0 or offset + size > len(data):
        raise ValueError(f"Truncated ROM data at offset 0x{offset:X} (need {size} bytes)")


def read_u16(data: bytes, offset: int) -> int:
    require_bytes(data, offset, 2)
    return int.from_bytes(data[offset:offset + 2], "little")


def read_u32(data: bytes, offset: int) -> int:
    require_bytes(data, offset, 4)
    return int.from_bytes(data[offset:offset + 4], "little")


def parse_level_obj_list_ptrs(rom: bytes) -> List[int]:
    base = gba_addr_to_offset(LEVEL_OBJ_LISTS_ADDR)
    ptrs: List[int] = []
    for idx in range(LEVEL_OBJ_LISTS_COUNT):
        ptrs.append(read_u32(rom, base + idx * 4))
    return ptrs


def parse_room_props(rom: bytes) -> List[dict[str, int]]:
    base = gba_addr_to_offset(ROOM_PROPS_ADDR)
    entries: List[dict[str, int]] = []
    for entry_offset in range(0, ROOM_PROPS_SIZE, ROOM_PROPS_STRIDE):
        off = base + entry_offset
        entries.append(
            {
                "native_room_id": entry_offset // ROOM_PROPS_STRIDE,
                "object_list2_idx": read_u16(rom, off + ROOM_PROPS_OBJECT_LIST2_IDX_OFFSET),
                "object_list_idx": read_u16(rom, off + ROOM_PROPS_OBJECT_LIST_IDX_OFFSET),
                "doors_idx": read_u16(rom, off + ROOM_PROPS_DOORS_IDX_OFFSET),
            }
        )
    return entries


def build_doors_idx_to_ap_room_keys(rooms_data: dict[str, Any]) -> dict[int, list[str]]:
    mapping: dict[int, list[str]] = defaultdict(list)
    for room_key, room_info in rooms_data.items():
        room_sanity = room_info.get("room_sanity")
        locations_payload = room_info.get("locations")
        if not isinstance(room_sanity, dict) and isinstance(locations_payload, dict):
            room_sanity = locations_payload.get("room_sanity")
        if not isinstance(room_sanity, dict):
            continue
        if not room_sanity.get("included"):
            continue
        bit_index = room_sanity.get("bit_index")
        if isinstance(bit_index, int):
            mapping[bit_index].append(room_key)
    return {k: sorted(v) for k, v in mapping.items()}


def parse_object_types_for_list(rom: bytes, list_ptr_addr: int) -> List[int]:
    """Return table-1 type IDs, validating and stepping over every record."""
    # A null pointer represents an absent list. Other invalid pointers fail closed.
    if list_ptr_addr == 0:
        return []

    list_off = gba_addr_to_offset(list_ptr_addr)
    require_bytes(rom, list_off, LEVEL_INFO_1E4_SIZE)
    obj_ptr = read_u32(rom, list_off + LEVEL_INFO_1E4_OBJ_PTR_OFFSET)
    if obj_ptr == 0:
        return []

    obj_off = gba_addr_to_offset(obj_ptr)
    out: List[int] = []
    # CreateLevelObjects (code_080023A4.c) walks by ObjectTemplate::unk1,
    # the size byte at +1, until zero. The header's unkC is not a record count.
    while True:
        require_bytes(rom, obj_off, OBJECT_SIZE_OFFSET + 1)
        size = rom[obj_off + OBJECT_SIZE_OFFSET]
        if size == 0:
            return out
        if size <= OBJECT_TYPE_OFFSET:
            raise ValueError(f"Object record at 0x{obj_off:X} is too short for its type: {size}")
        require_bytes(rom, obj_off, size)
        # CreateObject dispatches by spawnTable before interpreting the type.
        # Table 2 must not collide with table-1 mapping IDs.
        spawn_table = rom[obj_off + OBJECT_SPAWN_TABLE_OFFSET]
        if spawn_table not in (1, 2):
            raise ValueError(f"Object record at 0x{obj_off:X} has unknown spawn table {spawn_table}")
        if spawn_table == MAPPING_SPAWN_TABLE:
            out.append(rom[obj_off + OBJECT_TYPE_OFFSET])
        obj_off += size


def main() -> None:  # noqa: C901
    args = parse_args()

    mapping_path = args.mapping.resolve()
    rooms_path = args.rooms.resolve()
    rom_path = args.rom.resolve()

    if not rom_path.is_file():
        raise FileNotFoundError(f"ROM file not found: {rom_path}")
    if not mapping_path.is_file():
        raise FileNotFoundError(f"Mapping file not found: {mapping_path}")
    if not rooms_path.is_file():
        raise FileNotFoundError(f"Rooms file not found: {rooms_path}")

    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    rooms_data = json.loads(rooms_path.read_text(encoding="utf-8"))
    rom = rom_path.read_bytes()

    level_obj_list_ptrs = parse_level_obj_list_ptrs(rom)
    room_props = parse_room_props(rom)
    doors_idx_to_ap = build_doors_idx_to_ap_room_keys(rooms_data)

    # gLevelObjLists is a union: background-only entries are not object streams.
    # Parse only the objectListIdx selected by level.c, never objectList2Idx/unk22.
    object_types_by_list_idx: dict[int, list[int]] = {}

    total_usage_by_object: Counter[int] = Counter()
    per_room_usage_by_object: dict[int, dict[int, int]] = defaultdict(dict)
    room_keys_by_object: dict[int, dict[int, list[str]]] = defaultdict(dict)

    for entry in room_props:
        room_id = entry["native_room_id"]
        doors_idx = entry["doors_idx"]

        room_counter: Counter[int] = Counter()

        list_idx = entry["object_list_idx"]
        if list_idx == 0xFFFF:
            continue
        if list_idx >= len(level_obj_list_ptrs):
            raise ValueError(f"Room {room_id} has invalid object list index {list_idx}")
        if list_idx not in object_types_by_list_idx:
            object_types_by_list_idx[list_idx] = parse_object_types_for_list(
                rom, level_obj_list_ptrs[list_idx],
            )
        room_counter.update(object_types_by_list_idx[list_idx])

        if not room_counter:
            continue

        for obj_id, count in room_counter.items():
            total_usage_by_object[obj_id] += count
            per_room_usage_by_object[obj_id][room_id] = count
            room_keys_by_object[obj_id][room_id] = doors_idx_to_ap.get(doors_idx, [])

    for hex_key, mapping_entry in mapping.items():
        if not isinstance(mapping_entry, dict):
            continue

        entry_obj_id = mapping_entry.get("item_id")
        if not isinstance(entry_obj_id, int):
            entry_obj_id = int(hex_key, 16)
            mapping_entry["item_id"] = entry_obj_id

        total = int(total_usage_by_object.get(entry_obj_id, 0))
        per_room = per_room_usage_by_object.get(entry_obj_id, {})

        rooms_payload = []
        for room_id, count in sorted(per_room.items()):
            rooms_payload.append(
                {
                    "native_room_id": room_id,
                    "count": count,
                    "ap_room_keys": room_keys_by_object[entry_obj_id].get(room_id, []),
                }
            )

        mapping_entry["room_usage"] = {
            "total_count_all_rooms": total,
            "rooms": rooms_payload,
        }

    if args.in_place:
        output_path = mapping_path
    else:
        output_path = (
            args.output.resolve()
            if args.output
            else mapping_path.with_name(f"{mapping_path.stem}.enriched.json")
        )

    output_path.write_text(json.dumps(mapping, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Updated mapping with room usage: {len(mapping)} object IDs")
    print(f"Wrote output to: {output_path}")


if __name__ == "__main__":
    main()
