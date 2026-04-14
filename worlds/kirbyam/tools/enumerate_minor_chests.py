"""
Build a ROM-backed evidence manifest for minor chests.

This script reads the AMR SmallChest address table, then inspects each chest entry
directly from a vanilla Kirby & The Amazing Mirror ROM to extract:
- item byte at entry + 0x0E
- chest index byte at entry + 0x11

It also resolves AMR room slots through native gRoomProps metadata to capture
candidate native room IDs, doorsIdx values, and AP room-sanity keys.

Usage:
    python worlds/kirbyam/tools/enumerate_minor_chests.py --rom path/to/katam.gba
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


GBA_ROM_BASE = 0x08000000
ROOM_PROPS_ROM_BASE = 0x009331AC
ROOM_PROPS_SIZE = 0x00009998
ROOM_PROPS_STRIDE = 0x28
ROOM_PROPS_OBJECT_LIST_IDX_OFFSET = 0x20
ROOM_PROPS_DOORS_IDX_OFFSET = 0x24
AMR_SMALL_CHEST_ITEM_OFFSET = 0x0E
AMR_SMALL_CHEST_INDEX_OFFSET = 0x11


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_doors_idx_to_room_keys(rooms: dict) -> dict[int, list[str]]:
    mapping: dict[int, list[str]] = defaultdict(list)
    for room_key, room_data in rooms.items():
        room_sanity = room_data.get("room_sanity")
        if not isinstance(room_sanity, dict):
            continue
        if not room_sanity.get("included", False):
            continue
        bit_index = room_sanity.get("bit_index")
        if not isinstance(bit_index, int):
            continue
        mapping[bit_index].append(room_key)
    return {doors_idx: sorted(keys) for doors_idx, keys in mapping.items()}


def read_u16(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset:offset + 2], "little")


def parse_groomprops(rom_bytes: bytes) -> list[dict[str, int]]:
    room_props_entries: list[dict[str, int]] = []
    for entry_offset in range(0, ROOM_PROPS_SIZE, ROOM_PROPS_STRIDE):
        base = ROOM_PROPS_ROM_BASE + entry_offset
        object_list_idx = read_u16(rom_bytes, base + ROOM_PROPS_OBJECT_LIST_IDX_OFFSET)
        doors_idx = read_u16(rom_bytes, base + ROOM_PROPS_DOORS_IDX_OFFSET)
        room_props_entries.append(
            {
                "native_room_id": entry_offset // ROOM_PROPS_STRIDE,
                "object_list_idx": object_list_idx,
                "doors_idx": doors_idx,
            }
        )
    return room_props_entries


def resolve_default_paths(repo_root: Path) -> tuple[Path, Path, Path]:
    amr_items_default = repo_root.parent / "Amazing-Mirror-Randomizer" / "JSON" / "items.json"
    rooms_default = repo_root / "worlds" / "kirbyam" / "data" / "regions" / "rooms.json"
    output_default = repo_root / "worlds" / "kirbyam" / "data" / "minor_chest_manifest.json"
    return amr_items_default, rooms_default, output_default


def normalize_rom_address(addr: int) -> int:
    if addr >= GBA_ROM_BASE:
        return addr - GBA_ROM_BASE
    return addr


def main() -> int:
    repo_root = Path(__file__).resolve().parents[3]
    amr_items_default, rooms_default, output_default = resolve_default_paths(repo_root)

    parser = argparse.ArgumentParser(description="Enumerate KirbyAM minor chest evidence from ROM")
    parser.add_argument("--rom", required=True, help="Path to vanilla Kirby & The Amazing Mirror ROM")
    parser.add_argument("--amr-items", default=str(amr_items_default), help="Path to AMR items.json")
    parser.add_argument("--rooms", default=str(rooms_default), help="Path to KirbyAM rooms.json")
    parser.add_argument("--output", default=str(output_default), help="Output manifest JSON path")
    args = parser.parse_args()

    rom_path = Path(args.rom)
    amr_items_path = Path(args.amr_items)
    rooms_path = Path(args.rooms)
    output_path = Path(args.output)

    if not rom_path.exists():
        raise FileNotFoundError(f"ROM file not found: {rom_path}")
    if not amr_items_path.exists():
        raise FileNotFoundError(f"AMR items file not found: {amr_items_path}")
    if not rooms_path.exists():
        raise FileNotFoundError(f"rooms.json not found: {rooms_path}")

    rom_bytes = rom_path.read_bytes()
    amr_items = load_json(amr_items_path)
    rooms = load_json(rooms_path)

    small_chest_data = amr_items.get("SmallChest")
    if not isinstance(small_chest_data, dict):
        raise ValueError("AMR items.json missing SmallChest block")

    chest_addresses = small_chest_data.get("address")
    amr_room_slots = small_chest_data.get("room")
    if not isinstance(chest_addresses, list) or not isinstance(amr_room_slots, list):
        raise ValueError("AMR SmallChest.address and SmallChest.room must be lists")
    if len(chest_addresses) != len(amr_room_slots):
        raise ValueError("AMR SmallChest.address and SmallChest.room length mismatch")

    doors_idx_to_room_keys = build_doors_idx_to_room_keys(rooms)
    room_props = parse_groomprops(rom_bytes)

    native_by_object_list_idx: dict[int, list[dict[str, int]]] = defaultdict(list)
    for entry in room_props:
        native_by_object_list_idx[entry["object_list_idx"]].append(entry)

    manifest_entries: list[dict] = []
    slot_counts: dict[int, int] = defaultdict(int)
    ambiguous_entries = 0

    for index, (raw_address, amr_room_slot) in enumerate(zip(chest_addresses, amr_room_slots)):
        rom_offset = normalize_rom_address(int(raw_address))
        if rom_offset + AMR_SMALL_CHEST_INDEX_OFFSET >= len(rom_bytes):
            raise ValueError(
                f"Chest entry out of ROM bounds: index={index}, address=0x{int(raw_address):08X}"
            )

        item_id = rom_bytes[rom_offset + AMR_SMALL_CHEST_ITEM_OFFSET]
        chest_index = rom_bytes[rom_offset + AMR_SMALL_CHEST_INDEX_OFFSET]

        native_candidates = native_by_object_list_idx.get(int(amr_room_slot), [])
        native_room_ids = [candidate["native_room_id"] for candidate in native_candidates]
        doors_idx_candidates = sorted({candidate["doors_idx"] for candidate in native_candidates})

        ap_room_key_candidates: list[str] = []
        for doors_idx in doors_idx_candidates:
            ap_room_key_candidates.extend(doors_idx_to_room_keys.get(doors_idx, []))
        ap_room_key_candidates = sorted(set(ap_room_key_candidates))

        if len(native_room_ids) > 1:
            ambiguous_entries += 1

        slot_counts[int(amr_room_slot)] += 1

        manifest_entries.append(
            {
                "entry_index": index,
                "amr_room_slot": int(amr_room_slot),
                "rom_address": f"0x{int(raw_address):08X}",
                "rom_offset": f"0x{rom_offset:08X}",
                "item_id": item_id,
                "item_id_hex": f"0x{item_id:02X}",
                "chest_index": chest_index,
                "chest_index_hex": f"0x{chest_index:02X}",
                "candidate_native_room_ids": native_room_ids,
                "candidate_doors_idx": doors_idx_candidates,
                "candidate_ap_room_keys": ap_room_key_candidates,
            }
        )

    slot_resolution_summary = []
    for slot in sorted(slot_counts.keys()):
        native_candidates = native_by_object_list_idx.get(slot, [])
        native_room_ids = [candidate["native_room_id"] for candidate in native_candidates]
        doors_idx_candidates = sorted({candidate["doors_idx"] for candidate in native_candidates})
        ap_room_key_candidates: list[str] = []
        for doors_idx in doors_idx_candidates:
            ap_room_key_candidates.extend(doors_idx_to_room_keys.get(doors_idx, []))
        slot_resolution_summary.append(
            {
                "amr_room_slot": slot,
                "chest_count": slot_counts[slot],
                "candidate_native_room_ids": native_room_ids,
                "candidate_doors_idx": doors_idx_candidates,
                "candidate_ap_room_keys": sorted(set(ap_room_key_candidates)),
            }
        )

    manifest = {
        "metadata": {
            "rom": str(rom_path),
            "amr_items": str(amr_items_path),
            "rooms": str(rooms_path),
            "total_minor_chests": len(manifest_entries),
            "total_unique_amr_room_slots": len(slot_counts),
            "ambiguous_entries": ambiguous_entries,
            "room_props": {
                "rom_offset": f"0x{ROOM_PROPS_ROM_BASE:08X}",
                "size": f"0x{ROOM_PROPS_SIZE:04X}",
                "stride": f"0x{ROOM_PROPS_STRIDE:02X}",
                "object_list_idx_offset": f"0x{ROOM_PROPS_OBJECT_LIST_IDX_OFFSET:02X}",
                "doors_idx_offset": f"0x{ROOM_PROPS_DOORS_IDX_OFFSET:02X}",
            },
        },
        "entries": manifest_entries,
        "slot_resolution_summary": slot_resolution_summary,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")

    print(f"Wrote {len(manifest_entries)} chest entries to: {output_path}")
    print(f"Ambiguous entry count: {ambiguous_entries}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
