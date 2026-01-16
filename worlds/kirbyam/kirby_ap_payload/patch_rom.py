import sys

PAYLOAD_OFFSET = 0x0015E000
HOOK_OFFSET    = 0x00152696

# Thumb BL to 0x0815E000 from 0x08152696 (already computed)
BL_BYTES = bytes.fromhex("0B F0 B3 FC")

def main():
    if len(sys.argv) != 3:
        print("Usage: python patch_rom.py <in.gba> <out.gba>")
        sys.exit(1)

    in_path, out_path = sys.argv[1], sys.argv[2]

    with open("payload.bin", "rb") as f:
        payload = f.read()

    if len(payload) > 0x16A0:
        raise SystemExit(f"payload.bin too large: {len(payload)} bytes (max 0x16A0)")

    rom = bytearray(open(in_path, "rb").read())

    # Basic size sanity for a 4MB ROM
    if len(rom) != 0x400000:
        print(f"Warning: ROM size is {len(rom):#x}, expected 0x400000. Proceeding anyway.")

    # Insert payload
    rom[PAYLOAD_OFFSET:PAYLOAD_OFFSET+len(payload)] = payload

    # Patch hook site with BL
    rom[HOOK_OFFSET:HOOK_OFFSET+4] = BL_BYTES

    with open(out_path, "wb") as f:
        f.write(rom)

    print("Patched ROM written:", out_path)
    print("Payload inserted at file offset:", hex(PAYLOAD_OFFSET))
    print("Hook patched at file offset:", hex(HOOK_OFFSET), "with bytes:", BL_BYTES.hex(" "))

if __name__ == "__main__":
    main()
