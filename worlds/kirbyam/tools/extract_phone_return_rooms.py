"""Read the native L-return room enable bit; never write or emit ROM bytes."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .extract_room_evidence import ROOM_COUNT, ROOM_PROPS, USA_SHA1, unpack

ROOM_RECORD_SIZE = 0x28
PRIORITY_FLAGS_OFFSET = 0x12
L_RETURN_FLAG = 0x40
ENCOUNTER_ROOM_TABLE = 0x35105C
CENTRAL_CIRCLE = 801
CATALOG = Path(__file__).resolve().parents[1] / "dev-docs/native-room-wikirby-map.json"


def _room_flags(rom: bytes, catalog: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract only facts; eligibility also depends on live character/session state."""
    encounter_rooms = unpack(rom, "<16H", ENCOUNTER_ROOM_TABLE)
    encounter_slots: dict[int, list[int]] = {}
    for index in range(1, 14):
        slot = index if index < 9 else index + 3
        encounter_slots.setdefault(encounter_rooms[index], []).append(slot)

    rows = []
    seen = set()
    for room in catalog["rooms"]:
        room_id = room["native_id"]
        if type(room_id) is not int or room_id in seen or not 0 <= room_id < ROOM_COUNT:
            raise ValueError(f"Invalid or duplicate populated native room: {room_id!r}")
        seen.add(room_id)
        offset = ROOM_PROPS + ROOM_RECORD_SIZE * room_id
        flags, = unpack(rom, "<H", offset + PRIORITY_FLAGS_OFFSET)
        if flags == 0xFFFF:
            raise ValueError(f"Catalog lists unused native room as populated: {room_id}")
        rows.append({
            "native_room": room_id,
            "ap_compartments": room["ap_keys"],
            "room_allows_phone_return": bool(flags & L_RETURN_FLAG),
            "encounter_session_slots": encounter_slots.get(room_id, []),
        })
    return rows


def build_evidence(rom: bytes, catalog: dict[str, Any]) -> dict[str, Any]:
    if len(rom) != 0x1000000 or hashlib.sha1(rom).hexdigest() != USA_SHA1:
        raise ValueError("Expected the unmodified USA ROM (size and SHA-1 mismatch)")
    if catalog.get("rom_sha1") != USA_SHA1:
        raise ValueError("Native room catalog does not match the USA ROM")
    rows = _room_flags(rom, catalog)
    return {
        "schema": 1,
        "rom_sha1": USA_SHA1,
        "scope": ("Static room flag and encounter-slot inventory. No claim about active combat, "
                  "eligible character state, spawn compartment, or success in an actual run."),
        "destination_native_room": CENTRAL_CIRCLE,
        "battery_charge_required": False,
        "phone_item_required": False,
        "rooms": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True, help="Private local unmodified USA game file")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    evidence = build_evidence(args.rom.read_bytes(), catalog)
    args.output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
