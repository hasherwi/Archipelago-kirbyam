"""Optional private-ROM meter/audio-request probe; requires bsdiff4 and Unicorn.

Runs original Thumb instructions, intercepting rendering and audio playback.
This counts sound requests; it does not certify audible/full-gameplay behavior.
No ROM or save is written or uploaded.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

import bsdiff4
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_THUMB, UC_HOOK_CODE
from unicorn.arm_const import (
    UC_ARM_REG_R0, UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R12,
    UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC,
)

WORLD = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("enemy_health_scaling", WORLD / "enemy_health_scaling.py")
assert spec is not None and spec.loader is not None
scaling = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scaling)
scale_enemy_health_tables = scaling.scale_enemy_health_tables

def probe(rom: bytes, percent: int, kind: int) -> dict[str, int]:
    rom = scale_enemy_health_tables(rom, percent)
    cpu = Uc(UC_ARCH_ARM, UC_MODE_THUMB)
    for address, size in ((0x02000000, 0x40000), (0x03000000, 0x10000), (0x08000000, len(rom))):
        cpu.mem_map(address, size)
    cpu.mem_write(0x08000000, rom)
    obj, hud = 0x02001000, 0x02002000
    hp = struct.unpack_from("<h", rom, 0x351648 + kind * 24 + 4)[0]
    cpu.mem_write(obj + 0x80, struct.pack("<hB", hp, kind))
    for reg, value in ((UC_ARM_REG_R12, obj), (UC_ARM_REG_R4, obj + 0x82), (UC_ARM_REG_R5, hud)):
        cpu.reg_write(reg, value)
    cpu.emu_start(0x08034F69, 0x08034F92, count=100)
    initial = struct.unpack("b", cpu.mem_read(hud + 10, 1))[0]
    cpu.mem_write(hud + 9, bytes([initial & 255, initial & 255]))
    cpu.mem_write(hud + 0x1C, struct.pack("<I", obj))
    # Controlled damage-to-zero fixture: use the native target calculation,
    # without claiming an end-to-end collision/gameplay reproduction.
    cpu.mem_write(obj + 0x80, bytes(2))
    cpu.reg_write(UC_ARM_REG_R0, hud)
    cpu.reg_write(UC_ARM_REG_SP, 0x03007000)
    cpu.emu_start(0x0803533D, 0x080353DA, count=100)
    frame_pointer = struct.unpack_from("<I", rom, 0x35690)[0]
    sounds = []

    def hook(machine: Uc, address: int, size: int, data: object) -> None:
        if address == 0x0803567C:
            sounds.append(machine.reg_read(UC_ARM_REG_R0))
            machine.reg_write(UC_ARM_REG_PC, 0x08035681)  # skip m4aSongNumStart
        elif address == 0x08035682:
            machine.reg_write(UC_ARM_REG_PC, 0x08035687)  # skip rendering

    cpu.hook_add(UC_HOOK_CODE, hook)
    frame = 0
    while cpu.mem_read(hud + 9, 1) != bytes(1) and frame < 200:
        frame += 1
        cpu.mem_write(frame_pointer, struct.pack("<I", frame))
        for reg, value in ((UC_ARM_REG_R0, hud), (UC_ARM_REG_SP, 0x03007000),
                           (UC_ARM_REG_LR, 0x03006001)):
            cpu.reg_write(reg, value)
        cpu.emu_start(0x0803557D, 0x03006000, count=1000)
    return {"percent": percent, "type": kind, "initial_meter": initial,
            "sound_calls": len(sounds), "final_meter": struct.unpack("b", cpu.mem_read(hud + 9, 1))[0]}


def meter(hp: int, coefficient: int) -> int:
    product = (hp * coefficient + 32768) % 65536 - 32768
    return (((product >> 8) + bool(product & 255)) + 128) % 256 - 128


def sweep_tables(rom: bytes) -> dict[str, int]:
    entries = [(hp + index * stride, coefficient + index * 2)
               for hp, coefficient, count, stride in (
                   (0x35164C, 0x3513E8, 56, 24), (0x351530, 0x351458, 108, 2),
                   (0x351608, 0x351628, 16, 2)) for index in range(count)]
    cases = samples = max_loss = 0
    for percent in range(50, 501):
        scaled = scale_enemy_health_tables(rom, percent)
        if percent == 100:
            assert scaled is rom
        for hp_address, coefficient_address in entries:
            hp = struct.unpack_from("<h", rom, hp_address)[0]
            coefficient = struct.unpack_from("<H", rom, coefficient_address)[0]
            scaled_hp = struct.unpack_from("<h", scaled, hp_address)[0]
            scaled_coefficient = struct.unpack_from("<H", scaled, coefficient_address)[0]
            cases += 1
            assert scaled_hp == scaling.scale_hp_value(hp, percent)
            if hp <= 0 or coefficient == 0:
                assert scaled_coefficient == coefficient
                continue
            assert scaled_hp * scaled_coefficient <= 127 * 256
            original_fill = meter(hp, coefficient)
            scaled_fill = meter(scaled_hp, scaled_coefficient)
            assert 0 < scaled_fill <= original_fill
            assert original_fill - scaled_fill <= (scaled_hp + 255) // 256
            max_loss = max(max_loss, original_fill - scaled_fill)
            previous = 0
            for current_hp in range(scaled_hp + 1):
                fill = meter(current_hp, scaled_coefficient)
                assert previous <= fill <= original_fill
                previous = fill
                samples += 1
    return {"table_entry_percentage_cases": cases, "current_hp_samples": samples,
            "max_full_health_pixel_loss": max_loss}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", required=True, type=Path, help="Private clean USA ROM")
    args = parser.parse_args()
    clean = args.rom.read_bytes()
    if hashlib.sha1(clean).hexdigest() != "274b102b6d940f46861a92b4e65f89a51815c12c":
        raise SystemExit("Expected the verified clean USA ROM")
    rom = bsdiff4.patch(clean, (WORLD / "data/base_patch.bsdiff4").read_bytes())
    # These address-specific instruction slices must still be native code.
    for start, end in ((0x34F68, 0x34F92), (0x3533C, 0x353DA), (0x3557C, 0x356AC)):
        assert rom[start:end] == clean[start:end]
    table_results = sweep_tables(rom)
    results = [probe(rom, percent, kind) for percent in range(50, 501) for kind in (5, 36, 40)]
    assert all(r["initial_meter"] == 64 and r["sound_calls"] == 0 and r["final_meter"] == 0
               for r in results)
    print(json.dumps({**table_results, "instruction_cases": len(results), "sound_requests": 0, "passed": True}, indent=2))


if __name__ == "__main__":
    main()
