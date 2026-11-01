"""Synthetic native Area Key contracts shared by CI and patch tests.

This adds strict transition sentinels to an existing 16 MiB fixture; it never
builds a ROM or calls the hub fixture, avoiding recursive fixture population.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

WORLD_ROOT = Path(__file__).resolve().parents[2]
PATCH_ROM_PATH = WORLD_ROOT / "kirby_ap_payload" / "patch_rom.py"
ROM_BASE = 0x08000000
CALLSITE_START = 0x23000
NATIVE_AREA_RECORDS_START = 0x300000


def _load_patch_rom_module() -> Any:
    spec = importlib.util.spec_from_file_location("kirbyam_patch_rom_fixture", PATCH_ROM_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load patch_rom.py from {PATCH_ROM_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def populate_area_key_transition_fixture(rom: bytearray) -> None:
    if len(rom) != 0x1000000:
        raise ValueError("Expected a synthetic 16 MiB fixture")
    patch_rom = _load_patch_rom_module()

    # This is an exact retail-byte precondition. Keep it strict in patch_rom.py;
    # the synthetic fixture must provide the verified bytes explicitly.
    rom[
        patch_rom.AUTOMATIC_TRANSITION_GUARD_OFFSET:
        patch_rom.AUTOMATIC_TRANSITION_GUARD_OFFSET + len(patch_rom.AUTOMATIC_TRANSITION_GUARD_ORIGINAL)
    ] = patch_rom.AUTOMATIC_TRANSITION_GUARD_ORIGINAL
    rom[
        patch_rom.UNKNOWN83_CALLBACK_POINTER_OFFSET:
        patch_rom.UNKNOWN83_CALLBACK_POINTER_OFFSET + 4
    ] = patch_rom.UNKNOWN83_CALLBACK_POINTER_ORIGINAL
    rom[0x0001C6BC:0x0001C6C0] = patch_rom.MIRROR_SHARD_CALLBACK_POINTER_ORIGINAL

    # Populate all doorsIdx values from rooms.json with native room metadata.
    # Each AP doorsIdx is represented by a unique synthetic native room ID.
    metadata_offset = NATIVE_AREA_RECORDS_START
    for room_id, (doors_idx, native_area) in enumerate(
        sorted(patch_rom.load_expected_native_area_by_doors_idx().items())
    ):
        record_offset = metadata_offset + room_id * 0x50
        info_address = ROM_BASE + record_offset
        table_offset = patch_rom.ROOM_AREA_INFO_TABLE_OFFSET + room_id * 4
        props_offset = (
            patch_rom.ROOM_PROPS_TABLE_OFFSET
            + room_id * patch_rom.ROOM_PROPS_STRIDE
            + patch_rom.ROOM_PROPS_DOORS_IDX_OFFSET
        )
        rom[table_offset:table_offset + 4] = info_address.to_bytes(4, "little")
        rom[record_offset + patch_rom.ROOM_AREA_INFO_AREA_OFFSET] = native_area
        rom[props_offset:props_offset + 2] = doors_idx.to_bytes(2, "little")

    def put_bl(offset: int, target: int) -> None:
        rom[offset:offset + 4] = patch_rom.thumb_bl_bytes(ROM_BASE + offset, target)

    # Exact direct call families used by Area Key discovery.
    callsite_offset = CALLSITE_START
    for count, target in (
        (patch_rom.EXPECTED_SPECIAL_DOOR_STATE_CALLSITES, patch_rom.ORIGINAL_SPECIAL_DOOR_STATE_FN_ADDR),
        (patch_rom.EXPECTED_BUTTON_SPECIAL_TRANSITION_CALLSITES, patch_rom.ORIGINAL_BUTTON_SPECIAL_TRANSITION_FN_ADDR),
        (patch_rom.EXPECTED_EXPLICIT_ROOM_TRANSITION_CALLSITES, patch_rom.ORIGINAL_EXPLICIT_ROOM_TRANSITION_FN_ADDR),
        (patch_rom.EXPECTED_WARP_STAR_TRANSITION_CALLSITES, patch_rom.ORIGINAL_WARP_STAR_TRANSITION_FN_ADDR),
    ):
        for _ in range(count):
            put_bl(callsite_offset, target)
            callsite_offset += 8

    # Exact retail cannon boarding helper calls in sub_08121B70. The patcher
    # validates and rewrites these before passenger bits begin the launch path.
    for offset in (0x00121C46, 0x00121C9E, 0x00121CF6, 0x00121D54):
        put_bl(offset, patch_rom.ORIGINAL_CANNON_BOARD_HELPER_ADDR)

    # Exact route records used by admission gating; no lane geometry is fabricated.
    evidence = json.loads((WORLD_ROOT / "test/data/area_key_transports.json").read_text())
    for entry in evidence["byte_preconditions"]:
        if "special tile transition" in entry["purpose"]:
            expected = bytes.fromhex(entry["expected_hex"])
            offset = entry["rom_offset"]
            rom[offset:offset + len(expected)] = expected
    # Payload relocation reserves these bytes before the legacy payload area.
    rom[patch_rom.PAYLOAD_OFFSET:patch_rom.PAYLOAD_LEGACY_OFFSET] = bytes(0x400)
