import sys
import os
import subprocess
import argparse

PAYLOAD_OFFSET = 0x0015E000
HOOK_OFFSET    = 0x00152696

# Thumb BL to 0x0815E000 from 0x08152696 (already computed)
BL_BYTES = bytes.fromhex("0B F0 B3 FC")

ROM_PATH_TMP = "rom_path.tmp"
INTERMEDIARY_ROM = "baseline_patched.tmp.gba"


def run_make():
    """Run `make clean` then `make` in the current working directory."""
    for cmd in (["make", "clean"], ["make"]):
        print("Running:", " ".join(cmd))
        try:
            result = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            if result.stdout:
                print(result.stdout.rstrip())
        except FileNotFoundError as e:
            raise SystemExit(
                "Error: 'make' was not found on PATH.\n"
                "Install build tools (e.g., GNU Make) or run this script in an environment where `make` is available."
            ) from e
        except subprocess.CalledProcessError as e:
            output = (e.stdout or "").rstrip()
            raise SystemExit(
                f"Error: command failed: {' '.join(cmd)}\n"
                f"{output}"
            ) from e


def require_bsdiff4():
    try:
        import bsdiff4  # noqa: F401
        return bsdiff4
    except ModuleNotFoundError as e:
        raise SystemExit(
            "Error: Python package 'bsdiff4' is not installed.\n"
            "Install it in the SAME environment you run this script with:\n"
            "  python -m pip install bsdiff4\n"
        ) from e


def read_rom_path_from_tmp(tmp_path: str) -> str:
    try:
        with open(tmp_path, "r", encoding="utf-8") as f:
            for line in f:
                candidate = line.strip()
                if candidate:
                    candidate = candidate.strip('"').strip("'").strip()
                    return candidate
    except FileNotFoundError as e:
        raise SystemExit(
            f"Error: '{tmp_path}' not found.\n"
            f"Create '{tmp_path}' with a single line pointing to your clean base ROM."
        ) from e

    raise SystemExit(
        f"Error: '{tmp_path}' exists but contains no usable ROM path.\n"
        "Put the full path to the ROM on the first line."
    )


def safe_unlink(path: str) -> None:
    try:
        os.remove(path)
        print("Deleted intermediary ROM:", path)
    except FileNotFoundError:
        return
    except Exception as e:
        print(f"Warning: failed to delete intermediary ROM '{path}': {e}")


def parse_args(argv):
    """
    New interface (no user-provided out.gba):
      - Default (file):
          python patch_rom.py [base_patch.bsdiff4]
      - Explicit:
          python patch_rom.py --source-type file [base_patch.bsdiff4]
          python patch_rom.py --source-type arg <in.gba> [base_patch.bsdiff4]

    Legacy compatibility:
      - python patch_rom.py <in.gba> <out.gba> [base_patch.bsdiff4]
        This is treated as arg mode; <out.gba> is ignored with a warning.
    """
    # Legacy mode: <in> <out> [patch] and no flags
    if len(argv) in (3, 4) and not any(a.startswith("-") for a in argv[1:]):
        in_path = argv[1]
        ignored_out = argv[2]
        patch_path = argv[3] if len(argv) == 4 else "base_patch.bsdiff4"
        return {
            "source_type": "arg",
            "in_path": in_path,
            "patch_path": patch_path,
            "legacy_ignored_out": ignored_out,
        }

    parser = argparse.ArgumentParser(
        prog=os.path.basename(argv[0]),
        description="Build payload, patch ROM, and generate a bsdiff4 patch.",
    )
    parser.add_argument(
        "--source-type",
        choices=("file", "arg"),
        default="file",
        help="Where to get the base ROM path: 'file' reads rom_path.tmp, 'arg' uses positional IN_ROM.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Paths depend on --source-type. Default is 'file': [PATCH].",
    )

    ns = parser.parse_args(argv[1:])

    legacy_ignored_out = None

    if ns.source_type == "file":
        # Expect: [PATCH]
        if len(ns.paths) not in (0, 1):
            raise SystemExit(
                "Usage (default --source-type file):\n"
                "  python patch_rom.py [base_patch.bsdiff4]\n"
                "Or explicitly:\n"
                "  python patch_rom.py --source-type file [base_patch.bsdiff4]\n"
                f"Reads input ROM from '{ROM_PATH_TMP}'."
            )
        in_path = read_rom_path_from_tmp(ROM_PATH_TMP)
        patch_path = ns.paths[0] if len(ns.paths) == 1 else "base_patch.bsdiff4"
    else:
        # Expect: IN_ROM [PATCH]
        if len(ns.paths) not in (1, 2):
            raise SystemExit(
                "Usage with --source-type arg:\n"
                "  python patch_rom.py --source-type arg <in.gba> [base_patch.bsdiff4]"
            )
        in_path = ns.paths[0]
        patch_path = ns.paths[1] if len(ns.paths) == 2 else "base_patch.bsdiff4"

    return {
        "source_type": ns.source_type,
        "in_path": in_path,
        "patch_path": patch_path,
        "legacy_ignored_out": legacy_ignored_out,
    }


def main():
    args = parse_args(sys.argv)

    in_path = args["in_path"]
    patch_path = args["patch_path"]
    source_type = args["source_type"]
    legacy_ignored_out = args.get("legacy_ignored_out")

    if legacy_ignored_out is not None:
        print("Warning: legacy invocation detected (<in> <out> [patch]).")
        print(f"         Ignoring provided out ROM name: {legacy_ignored_out}")
        print(f"         Using intermediary ROM name: {INTERMEDIARY_ROM}")

    if source_type == "file":
        print(f"Source type: file (reading base ROM from '{ROM_PATH_TMP}')")
    else:
        print("Source type: arg")

    print("Base ROM path:", in_path)

    if os.path.basename(in_path).lower() != "kirby.gba":
        print(f"Note: You specified input ROM '{in_path}'.")
        print("      Your canonical clean ROM is 'kirby.gba'.")
        print("      For consistency, consider using a file named 'kirby.gba' as the clean base.")

    # 1) Build step: make clean; make
    run_make()

    # 2) Load payload
    try:
        with open("payload.bin", "rb") as f:
            payload = f.read()
    except FileNotFoundError as e:
        raise SystemExit(
            "Error: payload.bin not found. Ensure your build produces payload.bin in the current directory."
        ) from e

    if len(payload) > 0x16A0:
        raise SystemExit(f"payload.bin too large: {len(payload)} bytes (max 0x16A0)")

    # 3) Load ROM
    try:
        with open(in_path, "rb") as f:
            rom = bytearray(f.read())
    except FileNotFoundError as e:
        raise SystemExit(f"Error: input ROM not found: {in_path}") from e

    # Basic size sanity for a 4MB ROM
    if len(rom) != 0x400000:
        print(f"Warning: ROM size is {len(rom):#x}, expected 0x400000. Proceeding anyway.")

    # 4) Insert payload
    rom[PAYLOAD_OFFSET:PAYLOAD_OFFSET + len(payload)] = payload

    # 5) Patch hook site with BL
    rom[HOOK_OFFSET:HOOK_OFFSET + 4] = BL_BYTES

    # 6) Write the intermediary patched ROM
    with open(INTERMEDIARY_ROM, "wb") as f:
        f.write(rom)

    print("Intermediary patched ROM written:", INTERMEDIARY_ROM)
    print("Payload inserted at file offset:", hex(PAYLOAD_OFFSET))
    print("Hook patched at file offset:", hex(HOOK_OFFSET), "with bytes:", BL_BYTES.hex(" "))

    # 7) Generate base_patch.bsdiff4: clean base -> intermediary patched ROM
    bsdiff4 = require_bsdiff4()
    try:
        bsdiff4.file_diff(in_path, INTERMEDIARY_ROM, patch_path)
    except Exception as e:
        raise SystemExit(f"Error generating bsdiff patch '{patch_path}': {e}") from e

    print("BSdiff patch generated:", patch_path)
    print("Patch source (clean):", in_path)
    print("Patch target (baseline):", INTERMEDIARY_ROM)

    # 8) Delete intermediary ROM now that patch exists
    safe_unlink(INTERMEDIARY_ROM)


if __name__ == "__main__":
    main()
