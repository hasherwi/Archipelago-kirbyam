"""Synthetic instruction/pointer sentinels for the single-save patch guards."""
def populate_single_save_fixture(rom, thumb_bl_bytes):
    rom[0x2D91FC:0x2D923C] = bytes.fromhex(
        "f08b020220000000108c020280000000a08c02023e0200006089030224000000"
        "d029020204000000d8290202040000002cad030202000000ffffffffffffffff")
    rom[0x14A802:0x14A806] = thumb_bl_bytes(0x0814A802, 0x08138B44)
    rom[0x26A:0x26C] = bytes.fromhex("022c")
    rom[0x278:0x27A] = bytes.fromhex("0f2e")
    for offset in (0xA9EC, 0xAA18, 0xAADC, 0xAB04, 0xABF4, 0xAD4C,
                   0x325DC, 0x32640, 0x3280C):
        rom[offset:offset + 4] = bytes.fromhex("fc912d08")
