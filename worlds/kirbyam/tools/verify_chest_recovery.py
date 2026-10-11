"""Verify the complete saved-check inventory against an owner-provided USA ROM."""
import argparse
import hashlib
import json
from pathlib import Path
import struct


def verify(rom: bytes, inventory: dict) -> None:
    if len(rom) != 0x1000000 or hashlib.sha1(rom).hexdigest() != '274b102b6d940f46861a92b4e65f89a51815c12c':
        raise ValueError('requires the unmodified USA ROM')
    def pointer(offset):
        value = struct.unpack_from('<I', rom, offset)[0] - 0x08000000
        if not 0 <= value < len(rom) - 4:
            raise ValueError('invalid native object-list pointer')
        return value
    found = {}
    for slot in range(287):
        cursor = pointer(pointer(0xD637AC + 4 * slot))
        for _ in range(4096):
            if cursor + 2 > len(rom):
                raise ValueError('truncated object record')
            size = rom[cursor + 1]
            if size == 0:
                break
            if size < 14 or cursor + size > len(rom):
                raise ValueError('invalid object record size')
            if rom[cursor] == 1 and rom[cursor + 12] in (0x80, 0x81):
                if size < 0x24:
                    raise ValueError('truncated chest object')
                found[cursor] = (rom[cursor + 12], rom[cursor + 14], rom[cursor + 17])
            cursor += size
        else:
            raise ValueError('unterminated object list')
    expected = {int(row['source'], 0): (row['type'], row['reward'], row['flag'])
                for row in inventory['records']}
    if found != expected or len(found) != 84 or {r[2] for r in found.values()} != set(range(84)):
        raise ValueError('complete native chest inventory differs from recovery mapping')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rom', type=Path)
    args = parser.parse_args()
    inventory = json.loads((Path(__file__).resolve().parents[1] / 'data/chest_recovery.json').read_text())
    verify(args.rom.read_bytes(), inventory)
    print('Verified all 287 object lists: 84 unique chest flags, 80 mapped physical reward checks.')
