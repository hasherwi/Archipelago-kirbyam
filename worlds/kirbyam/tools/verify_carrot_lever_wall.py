"""Check Carrot's chute pocket using a private USA ROM, emitting no ROM bytes.

Closed-grid separation proves a barrier; opened-grid connectivity is not proof
of gameplay traversal. All non-solid cells deliberately overapproximate motion.
"""
import argparse
import hashlib
import json
from pathlib import Path
from importlib import import_module
v = import_module('.verify_radish_compartments', __package__) if __package__ else import_module('verify_radish_compartments')
e = v.evidence


def verify(rom):
    assert hashlib.sha1(rom).hexdigest() == e.USA_SHA1
    fields = e.unpack(rom, '<20H', e.ROOM_PROPS + 170 * 40)
    assert fields[13] == fields[16] == fields[18] == 252
    foreground = e.pointer(rom, 0xD64520 + fields[12] * 4)
    assert e.unpack(rom, '<HH', foreground) == (92, 26)
    header = e.pointer(rom, e.SOLIDITY_TABLE + fields[13] * 4)
    grid = v.decompress_rl(rom, e.pointer(rom, header), 46 * 13)
    walls = [(i % 46, i // 46) for i, tile in enumerate(grid) if tile == 0xF2]
    assert walls == [(4, 6), (4, 7), (4, 8)]
    assert e.unpack(rom, '<I', 0x2D88B8 + 0xF2 * 4)[0] == 0x240
    closed = bytes(13 if tile == 0xF2 else tile for tile in grid)
    pocket = v.component(closed, 46, (1, 8))
    main = v.component(closed, 46, (12, 5))
    assert (len(pocket), len(main)) == (6, 327) and not pocket & main
    assert (2, 8) in pocket and (3, 5) in main and (44, 8) in main
    incoming = [row for row in e.extract_room(rom, 181, {})['transitions']
                if row['destination_room'] == 170]
    assert len(incoming) == 12 and all(row['destination_spawn_tiles'] == [3, 9] for row in incoming)
    opened = bytes(0 if tile == 0xF2 else tile for tile in grid)
    assert (3, 5) in v.component(opened, 46, (1, 8))
    return {'native_room': 170, 'rom_sha1': e.USA_SHA1, 'wall_tiles': walls,
            'closed_component_sizes': [6, 327], 'chute_spawn_tiles': [3, 9],
            'spawn_collision_cell': [2, 8], 'lever_tiles': [3, 5],
            'scope': 'Static geometry only; not native gameplay or seed completion.'}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.rom.read_bytes()), indent=2))
