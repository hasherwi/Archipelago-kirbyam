"""Optional ROM-free machine-code ABI probe using the shipping ARM build and mGBA.

Requires arm-none-eabi-{gcc,objcopy,nm} on PATH and an installed mGBA development
prefix in MGBA_PREFIX. Set MGBA_LIBRARY_DIR when its library is not in prefix/lib.
Missing optional tools skip this probe; configured but broken tools fail it.
The predicate is an ABI-conforming adversarial stand-in, not a gate-logic test.
"""
from pathlib import Path
import os
import shutil
import subprocess

import pytest

from ..kirby_ap_payload.patch_rom import build_phone_gate_writes


def test_phone_thumb_wrapper_abi(tmp_path: Path) -> None:
    prefix = os.environ.get("MGBA_PREFIX")
    required = ("cc", "arm-none-eabi-gcc", "arm-none-eabi-objcopy", "arm-none-eabi-nm")
    if not prefix or any(not shutil.which(tool) for tool in required):
        pytest.skip("mGBA development prefix (MGBA_PREFIX), C and ARM toolchains required")
    payload = Path(__file__).resolve().parents[1] / "kirby_ap_payload"
    flags = ["-mthumb", "-mcpu=arm7tdmi", "-Os", "-ffreestanding", "-fno-builtin",
             "-fno-jump-tables", "-fno-tree-switch-conversion", "-nostdlib", "-Wall", "-Wextra"]
    objects = []
    for source in ("ap_payload.c", "ap_hook.s", "color_payload.c", "copy_room.c", "phone.c"):
        obj = tmp_path / (Path(source).stem + ".o")
        subprocess.run(["arm-none-eabi-gcc", *flags, "-I", str(payload), "-c",
                        str(payload / source), "-o", str(obj)], check=True)
        objects.append(str(obj))
    elf = tmp_path / "payload.elf"
    # The production linker script selects color_payload.o by basename.
    subprocess.run(["arm-none-eabi-gcc", *flags, "-T", str(payload / "linker.ld"),
                    "-o", str(elf), *(Path(obj).name for obj in objects), "-lgcc"],
                   cwd=tmp_path, check=True)
    symbols = {}
    for line in subprocess.check_output(["arm-none-eabi-nm", str(elf)], text=True).splitlines():
        fields = line.split()
        if len(fields) == 3:
            symbols[fields[2]] = int(fields[0], 16)
    # A synthetic address space only: no retail ROM, copyrighted assets, or saves.
    rom = bytearray(0x1010000)
    for section, address in ((".text", 0x0815DC00), (".apcolors", 0x09000000)):
        binary = tmp_path / (section + ".bin")
        subprocess.run(["arm-none-eabi-objcopy", "-O", "binary", "--only-section=" + section,
                        str(elf), str(binary)], check=True)
        data = binary.read_bytes()
        offset = address - 0x08000000
        rom[offset:offset + len(data)] = data
    rom[0x56C2C:0x56C34] = bytes.fromhex("f0 b5 47 46 80 b4 81 b0")
    for offset, data in build_phone_gate_writes(rom, symbols["ap_phone_call_entry"] & ~1).items():
        rom[offset:offset + len(data)] = data
    library_dir = Path(os.environ.get("MGBA_LIBRARY_DIR", str(Path(prefix) / "lib")))
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = str(library_dir) + os.pathsep + env.get("LD_LIBRARY_PATH", "")
    executable = tmp_path / "phone-arm-wrapper-probe"
    subprocess.run(["cc", "-std=gnu99", "-Wall", "-Wextra", "-I", str(Path(prefix) / "include"),
                    str(Path(__file__).with_name("native") / "phone_arm_wrapper_probe.c"),
                    "-L", str(library_dir), "-Wl,-rpath," + str(library_dir), "-lmgba",
                    "-o", str(executable)], check=True, env=env)
    result = subprocess.run([str(executable), hex(symbols["ap_phone_call_blocked"] & ~1)],
                            input=rom, capture_output=True, check=False, env=env, timeout=30)
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    assert b"Phone Thumb ABI: 24 cases passed" in result.stdout
