"""Decode configured Warp Star and fuse-cannon destinations from the USA ROM."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .extract_room_evidence import ROM_BASE, USA_SHA1, unpack

INVENTORY = Path(__file__).resolve().parents[1] / "data/ability_source_inventory.json"
WARP_STAR = 0x84
FUSE_CANNON = 0x8A
REVIEWED_TYPES = {WARP_STAR, FUSE_CANNON}


def decode_destination(rom: bytes, offset: int, expected_type: int) -> tuple[int, list[int]]:
    """Read the values assigned to Kirby's destination and spawn fields."""
    table, size, type_id = unpack(rom, "<BB10xB", offset)
    if (table, size, type_id) != (1, 0x24, expected_type):
        raise ValueError(f"Unexpected native object template at {offset:#x}")
    unpack(rom, "<36x", offset)
    if type_id == WARP_STAR:
        # CreateWarpStar copies 1E to roomId, 1A/1C to the spawn fields.
        x, y, room = unpack(rom, "<hhH", offset + 0x1A)
    elif type_id == FUSE_CANNON:
        # sub_08121AF8 initializes these fields; sub_08121FCC launches Kirby.
        room, = unpack(rom, "<H", offset + 0x12)
        packed, = unpack(rom, "<H", offset + 0x18)
        x, = unpack(rom, "<b", offset + 0x19)
        y = int(packed != 0)
    else:
        raise ValueError(f"No destination decoder for native object type {type_id:#x}")
    return room, [x, y]


def _extract(rom: bytes, inventory: dict[str, Any]) -> list[dict[str, Any]]:
    populated = {row["native_room"] for row in inventory["rooms"] if not row["unused_room_slot"]}
    rows = []
    seen = set()
    for placement in inventory["placements"]:
        type_id = placement["type_id"]
        if placement["spawn_table"] != 1 or type_id not in REVIEWED_TYPES:
            continue
        source = placement["native_room"]
        address = placement["template_address"]
        key = source, address
        if source not in populated or key in seen:
            raise ValueError(f"Invalid or duplicate source object placement: {key}")
        seen.add(key)
        offset = int(address, 16) - ROM_BASE
        if list(unpack(rom, "<hh", offset + 6)) != placement["position_pixels"]:
            raise ValueError(f"Native object position does not match its indexed placement: {key}")
        target, spawn = decode_destination(rom, offset, type_id)
        rows.append({
            "source_native_room": source,
            "mechanism": "warp_star" if type_id == WARP_STAR else "fuse_cannon",
            "template_address": address,
            "position_pixels": placement["position_pixels"],
            "destination_native_room": target,
            "destination_is_populated": target in populated,
            "configured_spawn_arguments": spawn,
        })
    return sorted(rows, key=lambda row: (row["source_native_room"], row["template_address"]))


def build_evidence(rom: bytes, inventory: dict[str, Any]) -> dict[str, Any]:
    if len(rom) != 0x1000000 or hashlib.sha1(rom).hexdigest() != USA_SHA1:
        raise ValueError("Expected the unmodified USA ROM (size and SHA-1 mismatch)")
    if inventory.get("rom_sha1") != USA_SHA1:
        raise ValueError("Native object inventory does not match the USA ROM")
    return {
        "schema": 1,
        "rom_sha1": USA_SHA1,
        "scope": ("Native template destinations only. Does not prove object availability, "
                  "usable launch state, final landing compartment, or carry."),
        "transitions": _extract(rom, inventory),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True, help="Private local unmodified USA game file")
    parser.add_argument("--output", type=Path, required=True, help="Derived JSON metadata, never ROM bytes")
    args = parser.parse_args()
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    evidence = build_evidence(args.rom.read_bytes(), inventory)
    args.output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
