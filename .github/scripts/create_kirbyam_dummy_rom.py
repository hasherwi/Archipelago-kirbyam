#!/usr/bin/env python3
"""Create a deterministic synthetic KirbyAM ROM for patch-builder smoke checks."""

from __future__ import annotations

import argparse
import importlib.util
import random
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PATCH_ROM_PATH = ROOT / "worlds" / "kirbyam" / "kirby_ap_payload" / "patch_rom.py"
ROM_BASE = 0x08000000
ROM_SIZE = 0x1000000
CALLSITE_START = 0x23000
NATIVE_AREA_RECORDS_START = 0x300000


def _load_patch_rom_module() -> Any:
    spec = importlib.util.spec_from_file_location("kirbyam_patch_rom_fixture", PATCH_ROM_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load patch_rom.py from {PATCH_ROM_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_dummy_rom() -> bytearray:
    """Build enough synthetic retail structure to exercise every strict guard."""
    patch_rom = _load_patch_rom_module()
    # Avoid pathological bsdiff behavior on a highly repetitive all-zero input.
    rom = bytearray(random.Random(0xA11CE).randbytes(ROM_SIZE))

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

    # Fixed retail callsites validated for Thumb-BL shape only.
    placeholder_bl = bytes.fromhex("00 f0 00 f8")
    for offset in (
        0x001D952,
        0x0000B144,
        0x0000B0CC,
        0x0000B1D0,
        0x0000B264,
        0x00039EEE,
        0x0000AFEC,
        0x00119B98,  # Small-switch effect dispatch used by lever-item decoupling.
    ):
        rom[offset:offset + 4] = placeholder_bl

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

    # patch_rom.py requires exactly eight direct calls to the retail
    # boss-already-owned reward function.
    for index in range(patch_rom.EXPECTED_BOSS_ALREADY_OWNED_REWARD_CALLSITES):
        put_bl(0x21000 + index * 4, patch_rom.ORIGINAL_BOSS_ALREADY_OWNED_REWARD_FN_ADDR)

    # Ordinary enemy / ability-star request path.
    put_bl(0x22000, patch_rom.ORIGINAL_ABILITY_TRANSITION_FN_ADDR)
    # Direct statue / scripted transitioningAbility path.
    put_bl(0x22004, patch_rom.ORIGINAL_ABILITY_TRANSITION_START_FN_ADDR)

    # The starting-color fix validates two retail single-player calls.
    for offset in patch_rom.STARTING_COLOR_START_GAME_CALL_OFFSETS:
        put_bl(offset, patch_rom.ORIGINAL_START_GAME_FN_ADDR)

    return rom


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "worlds" / "kirbyam" / "kirby_ap_payload" / "kirby.gba",
        help="destination path (defaults to the build tool's canonical ROM path)",
    )
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(build_dummy_rom())
    print(f"Wrote deterministic synthetic ROM ({ROM_SIZE:#x} bytes) to {args.output}")


if __name__ == "__main__":
    main()
