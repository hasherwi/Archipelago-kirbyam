"""Attribute all four lever-controlled break chains in a private USA ROM.

Static chain ownership only. Does not claim new native play or full seed proof.
"""
import argparse
import hashlib
import json
from pathlib import Path
from importlib import import_module
v = import_module('.verify_radish_compartments', __package__) if __package__ else import_module('verify_radish_compartments')
e = v.evidence
EXPECTED = {
    170: [(4, 6), (4, 7), (4, 8)],
    619: [(5, 1), (5, 2), (5, 3)],
    743: [(8, 5), (8, 6), (8, 7), (9, 5), (9, 6), (9, 7)],
    824: [(9, 1), (9, 2), (9, 3)],
}


def verify(rom):
    assert hashlib.sha1(rom).hexdigest() == e.USA_SHA1
    rows = []
    for room, expected in EXPECTED.items():
        fields = e.unpack(rom, '<20H', e.ROOM_PROPS + room * 40)
        fg = e.pointer(rom, 0xD64520 + fields[12] * 4)
        width, height = (n // 2 for n in e.unpack(rom, '<HH', fg))
        header = e.pointer(rom, e.SOLIDITY_TABLE + fields[13] * 4)
        grid = v.decompress_rl(rom, e.pointer(rom, header), width * height)
        cursor = e.pointer(rom, e.pointer(rom, 0xD637AC + fields[16] * 4))
        triggers = []
        for _ in range(4096):
            kind, size = e.unpack(rom, '<BB', cursor)
            if kind == 0:
                break
            assert size >= 2 and cursor + size <= len(rom)
            if kind == 1:
                assert size >= 36
                if rom[cursor + 12] == 0x91:
                    assert tuple(rom[cursor + 14:cursor + 17]) == (1, 1, 0)
                    x, y = e.unpack(rom, '<hh', cursor + 6)
                    triggers.append((cursor, (x // 16, y // 16)))
            cursor += size
        else:
            raise AssertionError('Unterminated object list')
        assert len(triggers) == 1
        offset, start = triggers[0]
        chain, pending = {start}, [start]
        for x, y in pending:
            for a, b in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if not (0 <= a < width and 0 <= b < height) or (a, b) in chain:
                    continue
                attr = e.unpack(rom, '<I', 0x2D88B8 + grid[b * width + a] * 4)[0]
                if attr & 0x40:
                    chain.add((a, b))
                    pending.append((a, b))
        assert sorted(chain) == expected
        rows.append({'native_room': room, 'trigger_offset': hex(offset),
                     'counter_selector': 1, 'counter_value': 1,
                     'trigger_cell': start, 'controlled_chain': sorted(chain),
                     'other_f2_cells': sorted((i % width, i // width) for i, tile in enumerate(grid)
                                              if tile == 0xF2 and (i % width, i // width) not in chain)})
    return {'rom_sha1': e.USA_SHA1, 'scope': 'Static trigger and connected-chain attribution, not gameplay.', 'rooms': rows}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.rom.read_bytes()), indent=2))
