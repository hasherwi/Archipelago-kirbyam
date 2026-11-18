"""Extract physical placement facts from the pinned USA ROM, never access rules.

The output contains decoded metadata, not ROM bytes. Dynamic encounter calls
are a candidate census: unresolved expressions and unproved acquisition remain
explicitly unresolved, and are never automatically admitted by traversal.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from extract_room_evidence import USA_SHA1, ROOM_COUNT, ROOM_PROPS, pointer, unpack
from enrich_native_object_room_usage import build_doors_idx_to_ap_room_keys

ROOT = Path(__file__).resolve().parents[1]
DECOMP_REFERENCE_COMMIT = "7d969fbce14fdc838d2c1ea01389717fb96c3189"
OBJECT_LISTS = 0xD637AC
STATUES = {0x92: (0x3538FC, 8), 0x93: (0x353904, 7),
           0x94: (0x35390B, 1), 0x95: (0x35390C, 3)}
# Native encounter controller translation units, not a guessed global grant map.
ENCOUNTERS = {
    0x38: "mr_frosty", 0x39: "bonkers", 0x3A: "phan_phan", 0x3B: "batafire",
    0x3C: "box_boxer", 0x3D: "boxy", 0x3E: "master_hand", 0x3F: "bombar",
    0x45: "kracko", 0x46: "king_golem", 0x47: "crazy_hand", 0x48: "gobbler",
    0x49: "wiz", 0x4A: "moley", 0x4B: "mega_titan", 0x4C: "titan_head",
    0x4D: "crazy_hand", 0x4E: "dark_meta_knight", 0x4F: "dark_mind",
    0x50: "dark_mind", 0x51: "dark_mind", 0x52: "dark_meta_knight",
}


def decode_records(rom: bytes, index: int) -> list[dict]:
    if not 0 <= index < 287:
        raise ValueError(f"Invalid object list index {index}")
    header = pointer(rom, OBJECT_LISTS + 4 * index)
    if unpack(rom, '<I', header)[0] == 0:
        return []
    cursor = pointer(rom, header)
    records = []
    for ordinal in range(4096):
        table, size = unpack(rom, '<BB', cursor)
        if not size:
            return records
        if table not in (1, 2) or size != 0x24:
            raise ValueError(f"Unsupported object record at {cursor:#x}: {table}/{size}")
        unpack(rom, '<36x', cursor)
        records.append({
            'template_address': f'0x{cursor + 0x08000000:08X}', 'ordinal': ordinal,
            'spawn_table': table, 'type_id': rom[cursor + 12],
            'position_pixels': list(unpack(rom, '<hh', cursor + 6)),
            'subtype1': rom[cursor + 14], 'subtype2': rom[cursor + 16],
            'spawn_conditions': {'state_bank': rom[cursor + 2],
                                 'bit_index': rom[cursor + 3],
                                 'test': 'bit_clear' if rom[cursor + 2] <= 2 else 'unconditional',
                                 'flags': rom[cursor + 5],
                                 'predicate': 'code_080023A4.c:CreateLevelObjects/sub_080027E8'},
        })
        cursor += size
    raise ValueError('Unterminated object list')


def macro_calls(text: str):
    """Split macro arguments with nesting; do not evaluate native expressions."""
    for match in re.finditer(r'CreateObjTemplateAndObj(?:WithSettingParent)?\s*\(', text):
        start = cursor = match.end()
        depth = 1
        args = []
        while cursor < len(text) and depth:
            char = text[cursor]
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            if (char == ',' and depth == 1) or depth == 0:
                args.append(text[start:cursor].strip())
                start = cursor + 1
            cursor += 1
        if depth:
            raise ValueError('Unterminated native creation macro')
        yield text.count('\n', 0, match.start()) + 1, args


def build_inventory(rom: bytes, decomp: Path, rooms: dict, enemies: dict) -> dict:
    if len(rom) != 0x1000000 or hashlib.sha1(rom).hexdigest() != USA_SHA1:
        raise ValueError('Expected unmodified USA ROM (size and SHA-1 mismatch)')
    header = (decomp / 'include/constants/object_types.h').read_text()
    names = {int(value, 16): name for name, value in
             re.findall(r'#define\s+(OBJ_\w+)\s+(0x[0-9A-Fa-f]+)', header)}
    source_types = {}
    for key, spec in enemies.items():
        for address in spec['addresses']:
            offset = int(address, 0) if isinstance(address, str) else address
            delta = offset - 0x35164E
            if delta >= 0 and delta % 24 == 0:
                source_types[delta // 24] = (key, spec)

    ability_names = {value['runtime_ability_id']: key for key, value in
                     json.loads((ROOT / 'data/abilities.json').read_text()).items()}

    def classify(record):
        typ = record['type_id']
        record.update(native_name=names.get(typ) if record['spawn_table'] == 1 else None,
                      source_key=None, native_grant=None, source_type='unclassified',
                      logic='standard', access={'status': 'unresolved', 'reason':
                      'Presence does not prove compartment access, acquisition, carry or repeatability.'},
                      repeatability='unresolved')
        if record['spawn_table'] != 1:
            return
        if typ in source_types:
            key, spec = source_types[typ]
            native_grant = ability_names[rom[0x35164E + 24 * typ]]
            if native_grant != spec['default_ability']:
                raise ValueError(f'Native grant disagrees with runtime policy table: {key}')
            record.update(source_key=key, native_grant=native_grant, source_type=spec['kind'],
                          can_be_swallowed=spec.get('can_be_swallowed', True))
            if spec['kind'] == 'boss_spawned':
                record['logic'] = 'advanced'
        elif typ in STATUES:
            base, count = STATUES[typ]
            if record['subtype1'] >= count:
                raise ValueError('Invalid statue subtype')
            address = base + record['subtype1']
            record.update(source_key=f'STATUE:{address:06X}', source_type='statue',
                          native_grant=ability_names[rom[address]], repeatability='retouch')
        elif typ in ENCOUNTERS:
            record['source_type'] = 'boss'
        elif typ in (0x96, 0x98):
            record['source_type'] = 'random_statue' if typ == 0x96 else 'master_stand'
        elif typ == 0x73:
            record['source_type'] = 'object_spawner'
        elif typ < 0x38 or typ == 0x70:
            record['source_type'] = 'enemy'
            record['grant_status'] = 'runtime source eligibility unresolved'
        else:
            record['source_type'] = 'other_object'

    aliases = build_doors_idx_to_ap_room_keys(rooms)
    lists = {index: decode_records(rom, index) for index in range(287)}
    native_rooms = []
    placements = []
    encounter_types = set()
    for room_id in range(ROOM_COUNT):
        props = ROOM_PROPS + room_id * 0x28
        index, doors = unpack(rom, '<H', props + 32)[0], unpack(rom, '<H', props + 36)[0]
        room = {'native_room': room_id, 'ap_room_keys': aliases.get(doors, []),
                'object_list_index': index, 'placements': [], 'static_inventory': 'complete',
                'encounter_inventory': 'unresolved',
                'unused_room_slot': index == 0xFFFF}
        for raw in ([] if index == 0xFFFF else lists[index]):
            record = dict(raw)
            record.update(id=f"room:{room_id}/template:{raw['template_address']}", native_room=room_id)
            classify(record)
            placements.append(record)
            room['placements'].append(record['id'])
            if record['spawn_table'] == 1 and record['type_id'] in ENCOUNTERS:
                encounter_types.add(record['type_id'])
        native_rooms.append(room)
    source_hashes = {'include/constants/object_types.h':
                     hashlib.sha256((decomp / 'include/constants/object_types.h').read_bytes()).hexdigest()}
    for relative in ('include/data.h', 'src/code_080023A4.c', 'src/ability_objects.c'):
        source_hashes[relative] = hashlib.sha256((decomp / relative).read_bytes()).hexdigest()
    calls = []
    for typ in sorted(encounter_types):
        filename = ENCOUNTERS[typ] + '.c'
        path = decomp / 'src' / filename
        if not path.exists():
            calls.append({'controller_type': typ, 'status': 'unresolved', 'logic': 'advanced',
                          'reason': f'Missing {filename}'})
            continue
        source_hashes[f'src/{filename}'] = hashlib.sha256(path.read_bytes()).hexdigest()
        for line, args in macro_calls(path.read_text()):
            calls.append({'controller_type': typ, 'evidence': f'src/{filename}:{line}',
                          'spawn_table_expression': args[1], 'type_expression': args[9],
                          'logic': 'advanced', 'status': 'unresolved',
                          'candidate_encounters': [p['id'] for p in placements
                              if p['spawn_table'] == 1 and p['type_id'] == typ],
                          'reason': ('Call-site census requires branch, helper and encounter-lifetime review; '
                                     'not an acquisition witness.')})
    for room in native_rooms:
        room['encounter_controllers'] = [p['id'] for p in placements
            if p['native_room'] == room['native_room'] and p['spawn_table'] == 1
            and p['type_id'] in ENCOUNTERS]
    generated_statues = []
    for parent in placements:
        if parent['source_type'] != 'random_statue':
            continue
        offset = int(parent['template_address'], 16) - 0x08000000
        x, y = parent['position_pixels']
        first_x = x + unpack(rom, '<h', offset + 0x1A)[0]
        second_x = first_x + unpack(rom, '<H', offset + 0x1E)[0]
        alternatives = []
        for index in range(19):
            group = rom[0x35390F + index]
            subtype = index - rom[0x353922 + group]
            base, count = STATUES[0x92 + group]
            if not 0 <= subtype < count:
                raise ValueError('Invalid native random-statue selector table')
            alternatives.append(f'STATUE:{base + subtype:06X}')
        for slot, child_x in enumerate((first_x, second_x)):
            generated_statues.append({
                'id': f"{parent['id']}/statue-slot:{slot}", 'native_room': parent['native_room'],
                'parent_placement': parent['id'], 'source_type': 'statue', 'logic': 'standard',
                'position_pixels': [child_x, y], 'source_key': None, 'native_grant': None,
                'possible_source_keys': alternatives,
                'selection': ('Two distinct native statue indices chosen when the controller spawns; '
                              'fixed for that instance.'),
                'repeatability': 'Retouch of the selected statue does not reroll its native index.',
                'access': {'status': 'unresolved',
                           'reason': 'Requires controller spawning and physical contact; no retry route inferred.'},
                'evidence': 'src/ability_objects.c:sub_080AA6F8/sub_080AA588',
            })
    bindings = {}
    by_template = {(p['native_room'], p['template_address'].lower()): p for p in placements}

    def bind(source, native_room):
        matches = re.findall(r'(?:0x)?(08[89][0-9a-fA-F]{5}|8[89][0-9a-fA-F]{5})', source.get('id', ''))
        if not matches:
            return
        address = f"0x{int(matches[-1], 16):08x}"
        placement = by_template.get((native_room, address))
        if placement is not None and placement['source_key'] == source['source_key']:
            bindings[f"{native_room}:{source['id']}"] = placement['id']

    for room in rooms.values():
        traversal = room.get('traversal', {})
        for definition in traversal.get('source_sets', {}).values():
            for source in definition['sources']:
                bind(source, definition['native_room'])
        graphs = list(traversal.get('graph_parts', {}).values()) + [
            graph for target in traversal.get('targets', []) for graph in target['graphs'].values()]
        for graph in graphs:
            nodes = {node['id']: node['native_room'] for node in graph.get('nodes', [])}
            for source in graph.get('sources', []):
                bind(source, nodes.get(source['node']))
    return {'version': 1, 'rom_sha1': USA_SHA1, 'decomp_reference_commit': DECOMP_REFERENCE_COMMIT,
            'decomp_file_sha256': source_hashes,
            'scope': 'All native room object lists, including empty and aliased rooms; dynamic census is unresolved.',
            'rooms': native_rooms, 'placements': placements, 'encounter_calls': calls,
            'reviewed_bindings': dict(sorted(bindings.items())),
            'generated_statue_slots': generated_statues,
            'dynamic_grant_types': [{'source_key': key, 'native_grant': spec['default_ability'],
                                    'logic': 'advanced', 'access': 'unresolved'}
                                   for key, spec in enemies.items() if spec['kind'] == 'boss_spawned']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--decomp', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build_inventory(args.rom.read_bytes(), args.decomp,
                             json.loads((ROOT / 'data/regions/rooms.json').read_text()),
                             json.loads((ROOT / 'data/enemies.json').read_text()))
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(f"{len(result['rooms'])} rooms, {len(result['placements'])} placements, "
          f"{len(result['encounter_calls'])} encounter call sites")


if __name__ == '__main__':
    main()
