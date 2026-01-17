import sys
import os
import subprocess

PAYLOAD_OFFSET = 0x0015E000
HOOK_OFFSET    = 0x00152696

# Thumb BL to 0x0815E000 from 0x08152696 (already computed)
BL_BYTES = bytes.fromhex("0B F0 B3 FC")

def run_make():
    """Run `make clean` then `make` in the current working directory."""
    for cmd in (["make", "clean"], ["make"]):
        print("Running:", " ".join(cmd))
        try:
            # Capture output so failures show useful context
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
            # e.stdout contains combined stdout+stderr due to STDERR->STDOUT
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

def main():
    # Usage:
    #   python patch_rom.py <in.gba> <out.gba> [base_patch.bsdiff4]
    if len(sys.argv) not in (3, 4):
        print("Usage: python patch_rom.py <in.gba> <out.gba> [base_patch.bsdiff4]")
        sys.exit(1)

    in_path, out_path = sys.argv[1], sys.argv[2]
    patch_path = sys.argv[3] if len(sys.argv) == 4 else "base_patch.bsdiff4"

    # As requested, your canonical clean ROM is kirby.gba.
    if os.path.basename(in_path).lower() != "kirby.gba":
        print(f"Note: You specified input ROM '{in_path}'.")
        print("      Your canonical clean ROM is 'kirby.gba'.")
        print("      For consistency, consider running: python patch_rom.py kirby.gba <out.gba> [patch]")

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
    with open(in_path, "rb") as f:
        rom = bytearray(f.read())

    # Basic size sanity for a 4MB ROM
    if len(rom) != 0x400000:
        print(f"Warning: ROM size is {len(rom):#x}, expected 0x400000. Proceeding anyway.")

    # 4) Insert payload
    rom[PAYLOAD_OFFSET:PAYLOAD_OFFSET + len(payload)] = payload

    # 5) Patch hook site with BL
    rom[HOOK_OFFSET:HOOK_OFFSET + 4] = BL_BYTES

    # 6) Write the baseline patched ROM
    with open(out_path, "wb") as f:
        f.write(rom)

    print("Patched ROM written:", out_path)
    print("Payload inserted at file offset:", hex(PAYLOAD_OFFSET))
    print("Hook patched at file offset:", hex(HOOK_OFFSET), "with bytes:", BL_BYTES.hex(" "))

    # 7) Generate base_patch.bsdiff4: clean kirby.gba -> baseline out.gba
    bsdiff4 = require_bsdiff4()
    try:
        bsdiff4.file_diff(in_path, out_path, patch_path)
    except Exception as e:
        raise SystemExit(f"Error generating bsdiff patch '{patch_path}': {e}") from e

    print("BSdiff patch generated:", patch_path)
    print("Patch source (clean):", in_path)
    print("Patch target (baseline):", out_path)

if __name__ == "__main__":
    main()
