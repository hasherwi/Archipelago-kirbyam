"""
Build a ROM-backed evidence manifest for minor chests.

This script reads the AMR SmallChest address table, then inspects each chest entry
directly from the authorized USA Kirby & The Amazing Mirror ROM to extract:
- reward ID at ObjectTemplate + 0x0E (AMR fragment byte 2)
- chest flag index at ObjectTemplate + 0x11 (AMR fragment byte 5)

It also resolves AMR room slots through native gRoomProps metadata to capture
candidate native room IDs, doorsIdx values, and AP room-sanity keys.

Usage:
    python worlds/kirbyam/tools/enumerate_minor_chests.py \
        --rom path/to/katam.gba \
        [--amr-items path/to/amr_items.json] \
        [--rooms worlds/kirbyam/data/regions/rooms.json] \
        [--output worlds/kirbyam/data/minor_chest_manifest.json]
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOM_PROPS_ROM_BASE = 0x009331AC
ROOM_PROPS_SIZE = 0x00009998
ROOM_PROPS_STRIDE = 0x28
# gRoomProps layout:
#   0x20 -> roomObjectListIdx
#   0x24 -> doors_idx
ROOM_PROPS_OBJECT_LIST_IDX_OFFSET = 0x20
ROOM_PROPS_DOORS_IDX_OFFSET = 0x24
# AMR's address identifies the six packed chest bytes at ObjectTemplate + 0x0C.
# The event-ring source pointer is the ObjectTemplate base, so subtract this
# field offset after matching the packed bytes in the ROM.
AMR_OBJECT_TEMPLATE_FRAGMENT_OFFSET = 0x0C
AMR_SMALL_CHEST_ITEM_OFFSET = 0x0E
AMR_SMALL_CHEST_INDEX_OFFSET = 0x11
AMR_PACKED_ITEM_SIZE = 6
ROM_ENTRY_READ_SIZE = max(AMR_SMALL_CHEST_ITEM_OFFSET, AMR_SMALL_CHEST_INDEX_OFFSET) + 1
AMR_JP_TO_US_ROM_SHIFT = 0x2FE74
AUTHORIZED_USA_ROM_SHA1 = "274b102b6d940f46861a92b4e65f89a51815c12c"
AMR_SOURCE_COMMIT = "2ea1c963535405e1ba7d678bb4361a7f5c30703b"
AMR_ITEMS_BLOB = "23b6a79e1138789518132eafe696d0076e485465"
EXPECTED_CONSUMABLE_CHEST_FLAGS = (
    2, 3, 4, 6, 8, 9, 10, 12, 14, 17, 19, 20, 23, 24, 26, 28, 29, 30, 31, 33, 34,
    35, 36, 38, 40, 41, 42, 44, 48, 50, 53, 56, 60, 62, 64, 67, 71, 72, 75, 78, 82,
)
EXPECTED_REWARD_PATH_COUNTS = {
    "ordinary_item_chest": 41,
    "spray_paint_chest": 14,
    "music_or_sound_chest": 10,
}
REWARD_PROFILE_EVIDENCE = [
    "katam/include/data.h: ObjectTemplate subtype1 is at +0x0E and unk11 is at +0x11",
    "katam/src/chest.c: CreateChest copies subtype1 and unk11 into the live chest object",
    "katam/src/chest.c: chest reward dispatch classifies item IDs 0..5, 0x14..0x21, and 0x28..0x32",
]
RESPAWN_POLICY_EVIDENCE = [
    "katam/src/treasures.c: CollectChest(u8) only sets chestFields bit; no clear/reset helper exists",
    "katam/src/treasures.c: HasChest(u8) reads persisted chestFields bit",
    "katam/asm/chest.s: spawn path gates chest state via HasChest at object+0xE2",
    "katam/asm/chest.s: collect path calls CollectChest with object+0xE2",
]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return payload


def build_doors_idx_to_room_keys(rooms: dict[str, Any]) -> dict[int, list[str]]:
    mapping: dict[int, list[str]] = defaultdict(list)
    for room_key, room_data in rooms.items():
        room_sanity = room_data.get("room_sanity")
        locations_payload = room_data.get("locations")
        if not isinstance(room_sanity, dict) and isinstance(locations_payload, dict):
            room_sanity = locations_payload.get("room_sanity")
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


def decode_amr_small_chest_fragment(fragment: bytes) -> dict[str, int]:
    """Decode the six-byte AMR fragment embedded at ObjectTemplate + 0x0C."""
    if len(fragment) != AMR_PACKED_ITEM_SIZE:
        raise ValueError(f"Expected {AMR_PACKED_ITEM_SIZE}-byte AMR fragment, got {len(fragment)}")
    return {
        "entry_type": fragment[0],
        "entry_marker": fragment[1],
        "reward_id": fragment[2],
        "unknown_object_field": fragment[3],
        "entry_aux_hi": fragment[4],
        "native_chest_flag_index": fragment[5],
    }


def resolve_amr_room_slot_object_list_idx(amr_room_slot: int) -> int:
    """Translate AMR's compact room slot to the native gRoomProps object-list index."""
    return amr_room_slot + 1 if amr_room_slot >= 4 else amr_room_slot


def parse_groomprops(rom_bytes: bytes) -> list[dict[str, int]]:
    room_props_end = ROOM_PROPS_ROM_BASE + ROOM_PROPS_SIZE
    if room_props_end > len(rom_bytes):
        raise ValueError(
            "ROM too small for gRoomProps table: "
            f"need end offset 0x{room_props_end:08X}, got ROM size 0x{len(rom_bytes):08X}"
        )

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


def resolve_default_paths(kirbyam_dir: Path) -> tuple[Path, Path]:
    rooms_default = kirbyam_dir / "data" / "regions" / "rooms.json"
    output_default = kirbyam_dir / "data" / "minor_chest_manifest.json"
    return rooms_default, output_default


def classify_reward_profile(reward_id: int) -> tuple[str, bool]:
    """Classify ObjectTemplate.subtype1 using the native CreateChest dispatch."""
    if 0 <= reward_id <= 5:
        return "ordinary_item_chest", True
    if reward_id == 0x06:
        return "vitality_chest", False
    if 0x0A <= reward_id <= 0x13:
        return "big_chest", False
    if 0x14 <= reward_id <= 0x21:
        return "spray_paint_chest", False
    if 0x28 <= reward_id <= 0x32:
        return "music_or_sound_chest", False
    if reward_id == 0x63:
        return "no_bonus_chest", False
    return "unclassified_chest_reward", False


def summarize_duplicate_room_sources(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Report multiple checks in one room; source-pointer identity remains exact."""
    room_to_entries: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        keys = entry.get("candidate_ap_room_keys") or []
        if len(keys) == 1:
            room_to_entries[keys[0]].append(entry)

    return [
        {
            "room_key": room_key,
            "chest_count": len(room_entries),
            "source_rom_offsets": [entry["rom_offset"] for entry in room_entries],
            "source_offsets_unique": len({entry["rom_offset"] for entry in room_entries}) == len(room_entries),
        }
        for room_key, room_entries in sorted(room_to_entries.items())
        if len(room_entries) > 1
    ]


def metadata_path(path: Path, repo_root: Path) -> str:
    resolved_path = path.resolve()
    resolved_repo_root = repo_root.resolve()
    try:
        return str(resolved_path.relative_to(resolved_repo_root)).replace("\\", "/")
    except ValueError:
        return f"external:{resolved_path.name}"


def normalize_rom_address(addr: int) -> int:
    if 0x08000000 <= addr < 0x0A000000:
        return addr - 0x08000000
    if 0x0A000000 <= addr < 0x0C000000:
        return addr - 0x0A000000
    return addr


def resolve_amr_entry_rom_offset(raw_address: int, rom_bytes: bytes, amr_entry_payload: bytes) -> tuple[int, str]:
    """
    Resolve an AMR SmallChest address to an offset in the current ROM.

    AMR items data is JP-ROM scoped. Its address points to the six-byte packed
    item field at ObjectTemplate + 0x0C. In USA ROM workflows, addresses are
    shifted. Match the packed bytes at that field, then return the ObjectTemplate
    base because the runtime event ring records that source pointer.

    Returns:
        (resolved_offset, resolution_mode)
        resolution_mode is one of: "direct", "jp_to_us_shift"
    """
    raw_offset = normalize_rom_address(raw_address)
    payload_len = len(amr_entry_payload)

    if raw_offset + payload_len <= len(rom_bytes):
        if rom_bytes[raw_offset:raw_offset + payload_len] == amr_entry_payload:
            object_template_offset = raw_offset - AMR_OBJECT_TEMPLATE_FRAGMENT_OFFSET
            if object_template_offset >= 0:
                return object_template_offset, "direct"

    translated_payload_offset = raw_offset + AMR_JP_TO_US_ROM_SHIFT
    if translated_payload_offset + payload_len <= len(rom_bytes):
        if rom_bytes[translated_payload_offset:translated_payload_offset + payload_len] == amr_entry_payload:
            object_template_offset = translated_payload_offset - AMR_OBJECT_TEMPLATE_FRAGMENT_OFFSET
            if object_template_offset >= 0:
                return object_template_offset, "jp_to_us_shift"

    raise ValueError(
        "Unable to resolve AMR SmallChest address in ROM: "
        f"raw_address=0x{raw_address:08X}, template_offset=0x{raw_offset:08X}, "
        f"jp_to_us_shift=0x{AMR_JP_TO_US_ROM_SHIFT:X}"
    )


def main() -> int:  # noqa: C901
    kirbyam_dir = Path(__file__).resolve().parent.parent
    repo_root = kirbyam_dir.parents[1]
    rooms_default, output_default = resolve_default_paths(kirbyam_dir)
    amr_items_default = repo_root.parent / "Amazing-Mirror-Randomizer" / "JSON" / "items.json"

    parser = argparse.ArgumentParser(description="Enumerate KirbyAM minor chest evidence from ROM")
    parser.add_argument("--rom", required=True, help="Path to vanilla Kirby & The Amazing Mirror ROM")
    parser.add_argument(
        "--amr-items",
        default=str(amr_items_default),
        help="Path to AMR items.json (defaults to ../Amazing-Mirror-Randomizer/JSON/items.json)",
    )
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
    rom_sha1 = hashlib.sha1(rom_bytes).hexdigest()
    if rom_sha1 != AUTHORIZED_USA_ROM_SHA1:
        raise ValueError(
            "Wrong ROM for the checked-in minor-chest evidence: "
            f"expected SHA1 {AUTHORIZED_USA_ROM_SHA1}, got {rom_sha1} ({rom_path})"
        )
    amr_items = load_json(amr_items_path)
    rooms = load_json(rooms_path)

    if not isinstance(amr_items, dict):
        raise ValueError(f"AMR items JSON must contain a top-level object: {amr_items_path}")
    if not isinstance(rooms, dict):
        raise ValueError(f"rooms.json must contain a top-level object: {rooms_path}")

    small_chest_data = amr_items.get("SmallChest")
    if not isinstance(small_chest_data, dict):
        raise ValueError("AMR items.json missing SmallChest block")

    chest_item_values = small_chest_data.get("item")
    chest_addresses = small_chest_data.get("address")
    amr_room_slots = small_chest_data.get("room")
    if (
        not isinstance(chest_item_values, list)
        or not isinstance(chest_addresses, list)
        or not isinstance(amr_room_slots, list)
    ):
        raise ValueError("AMR SmallChest.item, SmallChest.address, and SmallChest.room must be lists")
    if len(chest_item_values) != len(chest_addresses) or len(chest_addresses) != len(amr_room_slots):
        raise ValueError("AMR SmallChest.item/address/room length mismatch")

    doors_idx_to_room_keys = build_doors_idx_to_room_keys(rooms)
    room_props = parse_groomprops(rom_bytes)
    native_by_object_list_idx: dict[int, list[dict[str, int]]] = defaultdict(list)
    for entry in room_props:
        native_by_object_list_idx[entry["object_list_idx"]].append(entry)

    manifest_entries: list[dict[str, Any]] = []
    slot_counts: dict[int, int] = defaultdict(int)
    ambiguous_entries = 0
    modeled_non_collection_pool_entries = 0
    address_resolution_counts: dict[str, int] = defaultdict(int)

    for index, (packed_item_value, raw_address, amr_room_slot) in enumerate(
        zip(chest_item_values, chest_addresses, amr_room_slots)
    ):
        amr_entry_payload = int(packed_item_value).to_bytes(AMR_PACKED_ITEM_SIZE, "big")
        rom_offset, address_resolution = resolve_amr_entry_rom_offset(int(raw_address), rom_bytes, amr_entry_payload)
        if rom_offset + ROM_ENTRY_READ_SIZE > len(rom_bytes):
            raise ValueError(
                f"Chest entry out of ROM bounds: index={index}, address=0x{int(raw_address):08X}, "
                f"required_end=0x{rom_offset + ROM_ENTRY_READ_SIZE:08X}, rom_size=0x{len(rom_bytes):08X}"
            )

        fragment_fields = decode_amr_small_chest_fragment(amr_entry_payload)
        payload_b0 = fragment_fields["entry_type"]
        payload_b1 = fragment_fields["entry_marker"]
        reward_id = fragment_fields["reward_id"]
        payload_b3 = fragment_fields["unknown_object_field"]
        payload_b4 = fragment_fields["entry_aux_hi"]
        payload_b5 = fragment_fields["native_chest_flag_index"]
        rom_payload = rom_bytes[rom_offset:rom_offset + ROM_ENTRY_READ_SIZE]

        item_id = rom_bytes[rom_offset + AMR_SMALL_CHEST_ITEM_OFFSET]
        chest_index = rom_bytes[rom_offset + AMR_SMALL_CHEST_INDEX_OFFSET]
        if item_id != reward_id or chest_index != payload_b5:
            raise ValueError(
                "AMR fragment and USA ObjectTemplate fields disagree: "
                f"entry={index}, reward_id=0x{reward_id:02X}/0x{item_id:02X}, "
                f"chest_flag=0x{payload_b5:02X}/0x{chest_index:02X}"
            )
        reward_path, is_ordinary_item_chest = classify_reward_profile(reward_id)
        resolved_object_list_idx = resolve_amr_room_slot_object_list_idx(int(amr_room_slot))
        native_candidates = native_by_object_list_idx.get(resolved_object_list_idx, [])
        native_room_ids = [candidate["native_room_id"] for candidate in native_candidates]
        doors_idx_candidates = sorted({candidate["doors_idx"] for candidate in native_candidates})

        ap_room_key_candidates: list[str] = []
        for doors_idx in doors_idx_candidates:
            ap_room_key_candidates.extend(doors_idx_to_room_keys.get(doors_idx, []))
        ap_room_key_candidates = sorted(set(ap_room_key_candidates))

        if is_ordinary_item_chest:
            if len(ap_room_key_candidates) != 1:
                raise ValueError(
                    "Ordinary chest does not resolve to exactly one AP room: "
                    f"entry={index}, source=0x{rom_offset:08X}, rooms={ap_room_key_candidates}"
                )
            modeled_non_collection_pool_entries += 1
        if len(native_room_ids) > 1:
            ambiguous_entries += 1
        address_resolution_counts[address_resolution] += 1

        slot_counts[int(amr_room_slot)] += 1
        manifest_entries.append(
            {
                "entry_index": index,
                "amr_room_slot": int(amr_room_slot),
                "raw_address": f"0x{int(raw_address):08X}",
                "rom_offset": f"0x{rom_offset:08X}",
                "resolved_rom_offset": f"0x{rom_offset:08X}",
                "address_resolution": address_resolution,
                "amr_packed_item": int(packed_item_value),
                "amr_packed_item_hex": amr_entry_payload.hex(),
                "rom_slice_length": len(rom_payload),
                "rom_slice_sha256": hashlib.sha256(rom_payload).hexdigest(),
                "entry_type": payload_b0,
                "entry_type_hex": f"0x{payload_b0:02X}",
                "entry_marker": payload_b1,
                "entry_marker_hex": f"0x{payload_b1:02X}",
                "native_chest_flag_index": chest_index,
                "native_chest_flag_index_hex": f"0x{chest_index:02X}",
                "unknown_object_field": payload_b3,
                "unknown_object_field_hex": f"0x{payload_b3:02X}",
                "native_reward_path": reward_path,
                "is_ordinary_item_chest": is_ordinary_item_chest,
                "entry_aux_hi": payload_b4,
                "amr_fragment_chest_flag_index": payload_b5,
                "reward_id": reward_id,
                "reward_id_hex": f"0x{reward_id:02X}",
                "native_reward_id": item_id,
                "native_reward_id_hex": f"0x{item_id:02X}",
                "chest_index": chest_index,
                "chest_index_hex": f"0x{chest_index:02X}",
                "candidate_native_room_ids": native_room_ids,
                "candidate_doors_idx": doors_idx_candidates,
                "candidate_ap_room_keys": ap_room_key_candidates,
            }
        )

    multi_chest_room_disambiguation = summarize_duplicate_room_sources(manifest_entries)

    consumable_chest_flags = tuple(
        sorted(
            entry["native_chest_flag_index"]
            for entry in manifest_entries
            if entry["native_reward_path"] == "ordinary_item_chest"
        )
    )
    if consumable_chest_flags != EXPECTED_CONSUMABLE_CHEST_FLAGS:
        raise ValueError(
            "USA-ROM consumable chest flags differ from the independently audited set: "
            f"expected {EXPECTED_CONSUMABLE_CHEST_FLAGS}, got {consumable_chest_flags}"
        )
    ordinary_source_offsets = [
        entry["rom_offset"] for entry in manifest_entries if entry["is_ordinary_item_chest"]
    ]
    if len(ordinary_source_offsets) != len(set(ordinary_source_offsets)):
        raise ValueError("Ordinary minor chests do not have unique ObjectTemplate source offsets")
    if len(ordinary_source_offsets) != 41:
        raise ValueError(f"Expected 41 ordinary item chests, got {len(ordinary_source_offsets)}")
    reward_path_counts = {
        path: sum(entry["native_reward_path"] == path for entry in manifest_entries)
        for path in sorted({entry["native_reward_path"] for entry in manifest_entries})
    }
    if reward_path_counts != EXPECTED_REWARD_PATH_COUNTS:
        raise ValueError(
            "USA-ROM chest reward classes differ from the decomp-audited set: "
            f"expected {EXPECTED_REWARD_PATH_COUNTS}, got {reward_path_counts}"
        )

    slot_resolution_summary = []
    for slot in sorted(slot_counts.keys()):
        resolved_object_list_idx = resolve_amr_room_slot_object_list_idx(slot)
        native_candidates = native_by_object_list_idx.get(resolved_object_list_idx, [])
        native_room_ids = [candidate["native_room_id"] for candidate in native_candidates]
        doors_idx_candidates = sorted({candidate["doors_idx"] for candidate in native_candidates})
        slot_ap_room_key_candidates: list[str] = []
        for doors_idx in doors_idx_candidates:
            slot_ap_room_key_candidates.extend(doors_idx_to_room_keys.get(doors_idx, []))
        slot_resolution_summary.append(
            {
                "amr_room_slot": slot,
                "resolved_object_list_idx": resolved_object_list_idx,
                "chest_count": slot_counts[slot],
                "candidate_native_room_ids": native_room_ids,
                "candidate_doors_idx": doors_idx_candidates,
                "candidate_ap_room_keys": sorted(set(slot_ap_room_key_candidates)),
            }
        )

    manifest = {
        "metadata": {
            "rom": metadata_path(rom_path, repo_root),
            "rom_sha256": hashlib.sha256(rom_bytes).hexdigest(),
            "rom_sha1": rom_sha1,
            "amr_items": metadata_path(amr_items_path, repo_root),
            "amr_items_sha256": hashlib.sha256(amr_items_path.read_bytes()).hexdigest(),
            "amr_source_commit": AMR_SOURCE_COMMIT,
            "amr_items_blob": AMR_ITEMS_BLOB,
            "rooms": metadata_path(rooms_path, repo_root),
            "rooms_sha256": hashlib.sha256(rooms_path.read_bytes()).hexdigest(),
            "total_minor_chests": len(manifest_entries),
            "total_unique_amr_room_slots": len(slot_counts),
            "ambiguous_entries": ambiguous_entries,
            "identified_entries": len(manifest_entries),
            "unresolved_entries": 0,
            "modeled_non_collection_pool_entries": modeled_non_collection_pool_entries,
            "reward_profile_evidence": REWARD_PROFILE_EVIDENCE,
            "address_resolution_counts": dict(sorted(address_resolution_counts.items())),
            "amr_address_resolution": {
                "jp_to_us_shift_hex": f"0x{AMR_JP_TO_US_ROM_SHIFT:X}",
                "notes": [
                    "AMR items.json addresses are JP-ROM scoped.",
                    "This tool resolves each entry by payload-prefix match in the target ROM.",
                ],
            },
            "multi_chest_rooms_total": len(multi_chest_room_disambiguation),
            "multi_chest_rooms_exact_source_offsets_unique": sum(
                1 for room in multi_chest_room_disambiguation if room["source_offsets_unique"]
            ),
            "respawn_reopen_policy": {
                "conclusion": "no_repeatable_minor_chest_reopen_path_confirmed",
                "ap_handling": (
                    "Use the exact ObjectTemplate source pointer for each AP check; preserve native chest flags "
                    "and do not infer check identity from shared native chest bits"
                ),
                "evidence": RESPAWN_POLICY_EVIDENCE,
            },
            "room_props": {
                "rom_offset": f"0x{ROOM_PROPS_ROM_BASE:08X}",
                "size": f"0x{ROOM_PROPS_SIZE:04X}",
                "stride": f"0x{ROOM_PROPS_STRIDE:02X}",
                "object_list_idx_offset": f"0x{ROOM_PROPS_OBJECT_LIST_IDX_OFFSET:02X}",
                "doors_idx_offset": f"0x{ROOM_PROPS_DOORS_IDX_OFFSET:02X}",
                "amr_fragment_offset_from_object_template": f"0x{AMR_OBJECT_TEMPLATE_FRAGMENT_OFFSET:02X}",
            },
        },
        "entries": manifest_entries,
        "reward_path_summary": reward_path_counts,
        "slot_resolution_summary": slot_resolution_summary,
        "multi_chest_room_disambiguation": multi_chest_room_disambiguation,
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
