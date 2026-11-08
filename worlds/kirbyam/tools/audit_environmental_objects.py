"""Associate F7 collision tiles with native objects; no ROM assets are emitted.
Run beside scan_metal_tiles.py: python audit_environmental_objects.py ROM OUTPUT
Object association is not a traversal proof or a graphical tile classification.
"""
import argparse
import json
from pathlib import Path
import scan_metal_tiles as s

OBJECT_TABLE = 0xD637AC


def audit(rom):
    inventory = s.build_inventory(rom)
    result = {'sha1': s.USA_SHA1, 'rooms': [], 'scope': 'F7 environmental collision class; not all visually reinforced blocks'}
    for room in inventory['rooms']:
        tiles = {(v['x'], v['y']) for v in room['tiles'] if v['tile'] == '0xf7'}
        if not tiles:
            continue
        props = s.unpack(rom, '<20H', s.ROOM_PROPS + room['room'] * 40)
        cursor = s.pointer(rom, s.pointer(rom, OBJECT_TABLE + props[16] * 4))
        objects = []
        crumble = set()
        for _ in range(4096):
            kind, size = s.unpack(rom, '<BB', cursor)
            if kind == 0:
                break
            if size < 2 or cursor + size > len(rom):
                raise ValueError('Invalid object record')
            if kind == 1:
                if size < 36:
                    raise ValueError('Short object template')
                x, y = s.unpack(rom, '<hh', cursor + 6)
                typ = rom[cursor + 12]
                if typ in (0x74, 0x79, 0x7D, 0x7E, 0x88, 0x89, 0x8B):
                    objects.append({'offset': cursor, 'type': hex(typ), 'x': x, 'y': y})
                if typ == 0x74:
                    crumble.add((x // 16, y // 16))
            cursor += size
        else:
            raise ValueError('Unterminated object list')
        overlaps = tiles & crumble
        if overlaps == tiles:
            association = 'exact_destroyable_rock_block_overlay'
        elif any(o['type'] == '0x79' for o in objects):
            association = 'nearby_heave_ho_object'
        elif any(o['type'] == '0x8b' for o in objects):
            association = 'cannon_room_geometry_not_runtime_verified'
        else:
            association = 'unclassified'
        result['rooms'].append({'room': room['room'], 'f7_count': len(tiles),
            'f7_coordinates': sorted(map(list, tiles)), 'crumble_overlap_count': len(overlaps),
            'association': association, 'objects': objects})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = audit(args.rom.read_bytes())
    args.output.write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
