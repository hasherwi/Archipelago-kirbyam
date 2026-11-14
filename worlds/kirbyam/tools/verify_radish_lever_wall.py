"""Verify native room 619's two sides from a private USA ROM; emit no ROM assets."""
import argparse
import hashlib
import json
from pathlib import Path
from importlib import import_module
v = import_module('.verify_radish_compartments', __package__) if __package__ else import_module('verify_radish_compartments')
e = v.evidence


def verify(rom):
    assert hashlib.sha1(rom).hexdigest() == e.USA_SHA1
    fields = e.unpack(rom, '<20H', e.ROOM_PROPS + 619 * 40)
    assert fields[13] == fields[16] == fields[18] == 239
    foreground = e.pointer(rom, 0xD64520 + fields[12] * 4)
    assert e.unpack(rom, '<HH', foreground) == (32, 26)
    header = e.pointer(rom, e.SOLIDITY_TABLE + fields[13] * 4)
    grid = v.decompress_rl(rom, e.pointer(rom, header), 16 * 13)
    walls = [(i % 16, i // 16) for i, tile in enumerate(grid) if tile == 0xF2]
    assert walls == [(5, 1), (5, 2), (5, 3)]
    # Same solid flag as ordinary solid tiles, plus the 0x40 break-chain flag.
    assert e.unpack(rom, '<I', 0x2D88B8 + 0xF2 * 4)[0] == 0x240
    assert e.unpack(rom, '<I', 0x2D88B8 + 13 * 4)[0] == 0x200
    blocked = bytes(13 if tile == 0xF2 else tile for tile in grid)
    left = v.component(blocked, 16, (3, 3))
    right = v.component(blocked, 16, (11, 6))
    assert not left & right
    assert (2, 3) in left and (12, 7) in right and (12, 3) in right
    opened = bytes(0 if tile == 0xF2 else tile for tile in grid)
    assert (12, 7) in v.component(opened, 16, (3, 3))
    incoming = [row for row in e.extract_room(rom, 181, {})['transitions'] if row['destination_room'] == 619]
    assert incoming and all(row['destination_spawn_tiles'] == [4, 4] for row in incoming)
    outgoing = e.extract_room(rom, 619, {})['transitions']
    assert [(row['source_tiles'], row['destination_room']) for row in outgoing] == [([2, 3], 181), ([12, 7], 608)]
    assert rom[0x8D1478 + 12] == 0x91
    assert e.unpack(rom, '<hh', 0x8D1478 + 6) == (88, 56)
    return {'native_room': 619, 'doors_idx': 239, 'rom_sha1': e.USA_SHA1,
            'carrot_arrival_spawn_tiles': [4, 4], 'wall_tiles': walls,
            'closed_component_sizes': [len(left), len(right)],
            'lever_tiles': [12, 3], 'carrot_exit_tiles': [2, 3],
            'radish_exit_tiles': [12, 7], 'wall_object_offset': '0x008D1478',
            'scope': 'Static collision separation and opened-grid connectivity; not native gameplay or tester seed completion.'}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.rom.read_bytes()), indent=2))
