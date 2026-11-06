#!/usr/bin/env python3
"""Create a deterministic synthetic KirbyAM ROM for patch-builder smoke checks."""

from __future__ import annotations

import argparse
import importlib.util
import random
import runpy
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
PATCH_ROM_PATH = ROOT / "worlds" / "kirbyam" / "kirby_ap_payload" / "patch_rom.py"
ROM_BASE = 0x08000000
ROM_SIZE = 0x1000000


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

    # Shared save lifecycle requires exact loader and clear calls.
    for target, _key, offsets in patch_rom.SHARED_SAVE_NATIVE_CALLS:
        for offset in offsets:
            put_bl(offset, target)

    # Current main's delayed chest, lever, ability and health hooks.
    rom[0xB9A4:0xB9A8] = bytes.fromhex("D4 6C 20 1C")
    initializer = 0x351648 + 0x81 * 0x18 + 0x10
    rom[initializer:initializer + 4] = (0x0800BD4D).to_bytes(4, "little")
    put_bl(0xB9B0, 0x080029F4)
    for offset in (0x5C200, 0x5C400):
        rom[offset:offset + 4] = (0x0805C619).to_bytes(4, "little")
    put_bl(0x14380A, 0x08019F0C)
    rom[0x3EB0E:0x3EB14] = patch_rom.thumb_bl_bytes(0x0803EB0E, 0x08019F0C) + b"\x06\x30"
    for offset in (0x339B2, 0x33BF2, 0x35A62):
        put_bl(offset, 0x0803518C)
    # Hub switch initialization and dispatcher contract from current main.
    put_bl(0x2AD24, 0x08002888)
    put_bl(0x1193C4, 0x08002888)
    for index in range(15):
        offset = 0x34BDBC + index * 4
        rom[offset:offset + 4] = (0x08126405 + index * 12).to_bytes(4, "little")

    # Minny enemy ABI and native treasure-menu paint selection.
    rom[0x9C6A2:0x9C6AA] = bytes.fromhex("2c 1c 84 34 21 78 30 1c")
    put_bl(0x9C6AA, patch_rom.ORIGINAL_ABILITY_TRANSITION_FN_ADDR)
    put_bl(0x14406C, 0x081447E0)
    rom[0xD60820:0xD60824] = (0x08155401).to_bytes(4, "little")
    rom[0x3D21C:0x3D224] = bytes.fromhex("70 b5 04 1c 0d 1c 16 1c")

    # Mirror decoration and Warp Star lifecycle hooks require the original
    # native instruction/register contracts, just like the retail patch input.
    for offset, (_, expected) in patch_rom.AREA_OBJECT_SPAWN_SITES.items():
        rom[offset - 6:offset + 8] = expected
    for offset, (native, _) in patch_rom.AREA_OBJECT_TASK_POINTERS.items():
        rom[offset:offset + 4] = native.to_bytes(4, "little")
    for offset in patch_rom.AREA_DOOR_DECORATION_SITES:
        put_bl(offset, 0x0802B2F4)

    # Exact checked native hub excerpts are shared with the regression fixtures.
    hub_fixture = runpy.run_path(str(ROOT / "worlds/kirbyam/test/native/hub_transition_fixture.py"))
    hub_fixture["populate_hub_transition_fixture"](rom)
    single = runpy.run_path(str(ROOT / "worlds/kirbyam/test/native/single_save_fixture.py"))
    single["populate_single_save_fixture"](rom, patch_rom.thumb_bl_bytes)
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
