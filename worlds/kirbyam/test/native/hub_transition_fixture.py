"""Small verified USA transition-contract excerpts for the synthetic ROM fixture.

Only the 206 bytes checked by the hub patcher's independent SHA256 guards are
included, not a ROM image. See dev-docs/hub-teleport-trap.md for source evidence.
"""
from __future__ import annotations

CONTRACT_BYTES = {
    0x551FC: bytes.fromhex(
        "70b5844609040c0c251c1206160e1b061b0e2248027961465631012009788840102108430240002a"
        "3cd1802040006044007800060016002834dd6046d430008827282fd07a282dd88820400060440068"
        "002827d16146886811490840002821d1604660300088a0421cd06146c868802149010840002815d0"
        "832040006044058084204000604406808520400060440380604600f0e5f8012005e0000010050003"
        "000b8003002070bc02bc0847"
    ),
    0x2D40: bytes.fromhex(
        "10b50004054cc00b03191b780b70013400190078107010bc01bc004744cb9308"
    ),
    0x93D186: bytes.fromhex(
        "0e0f"
    ),
}


def populate_hub_transition_fixture(rom: bytearray) -> None:
    if len(rom) != 0x1000000:
        raise ValueError('Expected a synthetic 16 MiB fixture')
    # Exact native GameLoop BL to TasksExec.
    rom[0x151CF4:0x151CF8] = bytes.fromhex('00 f0 fe ff')
    for offset, data in CONTRACT_BYTES.items():
        rom[offset:offset + len(data)] = data
