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
# These are dedicated Boss Endurance rooms, not the shared boss arenas.
# Adventure's Copy Ability Room is 970 and must not be confused with 950.
BOSS_ENDURANCE_ROOMS = frozenset({950, 951, 955, 956, 957, 969})
STATUES = {0x92: (0x3538FC, 8), 0x93: (0x353904, 7),
           0x94: (0x35390B, 1), 0x95: (0x35390C, 3)}
# Native encounter controller translation units, not a guessed global grant map.
ENCOUNTERS = {
    0x38: "mr_frosty", 0x39: "bonkers", 0x3A: "phan_phan", 0x3B: "batafire",
    0x3C: "box_boxer", 0x3D: "boxy", 0x3E: "master_hand", 0x3F: "bombar",
    0x45: "kracko", 0x46: "king_golem", 0x47: "crazy_hand", 0x48: "gobbler",
    0x49: "wiz", 0x4A: "moley", 0x4B: "mega_titan", 0x4C: "mega_titan",
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
            'template_flags_22': unpack(rom, '<H', cursor + 0x22)[0],
            'spawn_conditions': {'state_bank': rom[cursor + 2],
                                 'bit_index': rom[cursor + 3],
                                 'test': 'bit_clear' if rom[cursor + 2] <= 2 else 'unconditional',
                                 'flags': rom[cursor + 5],
                                 'predicate': 'code_080023A4.c:CreateLevelObjects/sub_080027E8'},
        })
        cursor += size
    raise ValueError('Unterminated object list')


def spawner_output(rom: bytes, parent: dict) -> dict:
    """Decode a child prototype, not an accessible or renewable placement.

    Pinned asm/object_spawner.s:sub_0811BAAC copies coordinates and subtypes,
    creates a table-1 child from template +0x14's low byte, and tracks at most
    the high byte's count. sub_0811BE64 reclaims destroyed slots when enabled.
    """
    offset = int(parent['template_address'], 16) - 0x08000000
    typ, capacity = unpack(rom, '<BB', offset + 0x14)
    flags = unpack(rom, '<H', offset + 0x22)[0]
    return {
        'id': f"{parent['id']}/spawner-output", 'native_room': parent['native_room'],
        'parent_placement': parent['id'], 'spawn_table': 1, 'type_id': typ,
        'position_pixels': list(parent['position_pixels']),
        'subtype1': parent['subtype1'], 'subtype2': parent['subtype2'],
        'configured_child_capacity': capacity,
        'template_flags_22': 5 if 0x38 <= typ <= 0x52 else 0,
        'native_state_identity': {'state_bank': 0, 'bit_index': 31},
        'reclaims_destroyed_slots': not bool(flags & 1),
        'status': 'unresolved',
        'spawn_conditions': {
            'controller': parent['id'], 'status': 'decoded_predicates',
            'room_counter_bank': 1 if flags & 2 else 0,
            'room_counter_at_least': rom[offset + 0x19],
            'spawned_count_below': capacity,
            'delay_counter_bits': 8,
            'delay_counter_at_least': unpack(rom, '<H', offset + 0x12)[0],
            'startup_counter_initial': 0 if 0x38 <= typ <= 0x52 else 70,
            'startup_counter_previous_signed_value_above': 64,
            'global_slot_search_limit': 32,
            'exhausted_slot_behavior': 'not_certified',
            'reason': 'Decoded predicates do not prove room counters or acquisition; global slot exhaustion is not certified.'},
        'lifetime': {'identity': f"{parent['id']}/spawner-output",
                     'child_has_native_parent_attachment': False,
                     'reason': 'Construction has no parent attachment; destruction still needs child-specific evidence.'},
        'evidence': ('https://github.com/jiangzhengwenjz/katam/blob/' + DECOMP_REFERENCE_COMMIT
                     + '/asm/object_spawner.s#L364-L455'),
    }



def counter_contributions(record: dict) -> list[dict]:
    """Conditional native counter events, not AP access or repeatability proofs.

    Keep destruction separate from collection and never count a template twice
    merely because it supports both callbacks. Chest branches require runtime
    contents and patch evidence, so their contributions remain unresolved.
    """
    if record['spawn_table'] != 1:
        return []
    typ = record['type_id']
    result = []
    if typ <= 0x64 and record['template_flags_22'] & 1:
        result.append({'bank': 0, 'amount': 1, 'event': 'ObjectDestroy',
                       'requires': ['assigned room slot', 'object HP <= 0'],
                       'evidence': 'src/object.c:ObjectDestroy'})
    state = record.get('native_state_identity', record.get('spawn_conditions', {}))
    if 0x5E <= typ <= 0x64 and (state.get('state_bank'), state.get('bit_index')) != (0, 31):
        result.append({'bank': 1, 'amount': 1, 'event': 'BonusSetFunc',
                       'requires': ['living Kirby contact', 'Macro_0810B1F4 returns false'],
                       'evidence': 'src/bonus.c:BonusSetFunc'})
    if typ in (0x80, 0x81):
        result.append({'bank': 1, 'amount': 1, 'event': 'chest callback',
                       'requires': ['already collected chest or qualifying popup branch',
                                    'AP lever wall ownership or unsuppressed native popup contribution'],
                       'status': 'unresolved',
                       'evidence': 'src/chest.c:sub_0800B97C/sub_0800BD4C',
                       'runtime_evidence': 'kirby_ap_payload/ap_payload.c:ap_on_initialize_chest/ap_on_chest_popup_room_counter/ap_update_lever_wall',
                       'excludes': ['physical AP lever pull without wall item',
                                    'suppressed AP ordinary bonus popup']})
    return result


def macro_calls(text: str, pattern: str = r'CreateObjTemplateAndObj(?:WithSettingParent)?'):
    """Split macro arguments with nesting; do not evaluate native expressions."""
    for match in re.finditer(pattern + r'\s*\(', text):
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


# Audited variable-type branches. Hashes prevent applying these facts to changed
# native code; a different source snapshot stays visibly unresolved.
VARIABLE_TYPES = {
    ('kracko.c', 'type'): ('6085113c8f08b82b1433723fadfc4aa62d509fe7f36bd1d5653618513895bea8',
                          (0x12, 0x13, 0x1C)),
    ('king_golem.c', 'type'): ('ef358db61ff4189e9a158742ea2553a03f94aa2025174626cdfce1cde27ed3aa',
                              (0x9B, 0x9C)),
    ('king_golem.c', 'r + OBJ_GOLEM_1'): (
        'ef358db61ff4189e9a158742ea2553a03f94aa2025174626cdfce1cde27ed3aa', (0x1F, 0x20, 0x21)),
    ('dark_mind.c', 'OBJ_DARK_MIND_STAR_FIRE + r3'): (
        '841b204cd3edf9129b59207ff731cfc651917a529efede581569009bd3b7f158', (0xCB, 0xCC, 0xCD, 0xCE)),
    ('moley.c', 'type'): ('fbd225320d9f65cf65a8b358deba4144d2b908b17eac4cdb5380e0fd175f65e5',
                         tuple(range(0xC1, 0xC8))),
}

FROSTY_REVIEW_SHA256 = '6efd791e49aa53cc2b6c272007ecc1f2c69a28cb7e45193daa118a3871e0e209'


def frostys_cube_contract(source_hash: str, type_id: int) -> dict | None:
    """Conditional native facts, never a guarantee of reaching an attack state."""
    if source_hash != FROSTY_REVIEW_SHA256 or type_id not in (166, 167):
        return None
    return {
        'status': 'conditional_native_contract', 'source_sha256': source_hash,
        'generation_function': 'sub_080CCEE0',
        'attack_callbacks': ['sub_080CD47C', 'sub_080CD4D0', 'sub_080CD524'],
        'attack_selection': 'sub_080CD3FC: counter > 43, then RandLessThan3()',
        'attack_entry_guaranteed': False,
        'branch': 'RandLessThan3() != 0' if type_id == 166 else 'RandLessThan3() == 0',
        'alternative_types': [166, 167],
        'alternative_source_keys': ['MR_FROSTY_ICE_CUBE'],
        'parent_attachment': 'creating Frosty',
        'parent_expiry_callback': 'sub_0809F840',
        'phase_expiry': 'parent animation > 16; child collision mask0x1; before throw also collision mask0x4',
        'throw_transition': 'parent callback sub_080CC4C8 and animation 11',
        'initial_throw_protection_counter': 4,
        'repeatability': 'not_certified',
        'acquisition': 'not_implied_by_shared_grant; size, collision and attack timing differ',
    }


BONKERS_REVIEW_SHA256 = '10f5a98389ba5760df3ce46ca0bcb22d4c27d86eb4a54c00f0b4096daeb92e97'


def bonkers_nut_contract(source_hash: str, type_id: int) -> dict | None:
    """Shared native branch/lifetime facts; no automatic attack or access credit."""
    if source_hash != BONKERS_REVIEW_SHA256 or type_id not in (168, 169):
        return None
    return {
        'status': 'conditional_native_contract', 'source_sha256': source_hash,
        'generation_function': 'BonkersThrowNut',
        'attack_callback': 'BonkersNutAttack',
        'activation': 'throwing phase (animation != 0x12) and header.unk1 == 0x44',
        'attack_entry_guaranteed': False,
        'branch': 'RandLessThan3() != 0' if type_id == 168 else 'RandLessThan3() == 0',
        'alternative_types': [168, 169],
        'parent_attachment': 'creating Bonkers',
        'parent_expiry_callback': 'sub_0809F840',
        'collision_lifetime': 'one bounce on collision mask0x4; next such collision or mask0x1 destroys nut',
        'large_variant': 'larger collision bounds; half horizontal launch and bounce speeds',
        'repeatability': 'not_certified',
        'runtime_source': 'no configured source key; native Normal grant; retained as physical encounter output',
        'acquisition': 'not_certified; native projectile presence is not Copy Ability acquisition',
    }


BOMBAR_REVIEW_SHA256 = 'd148e12823ac6fb845c1a8de482460554c7efd3ae132631068a701d074a7af28'


def bombar_output_contract(source_hash: str, type_id: int) -> dict | None:
    """Distinguish paired missiles and subtype selection from output expiry."""
    if source_hash != BOMBAR_REVIEW_SHA256 or type_id not in (178, 179):
        return None
    result = {
        'status': 'conditional_native_contract', 'source_sha256': source_hash,
        'parent_attachment': 'creating Bombar',
        'parent_expiry_callback': 'sub_0809F840',
        'attack_entry_guaranteed': False, 'allocation_success_certified': False,
        'repeatability': 'not_certified',
        'acquisition': 'unresolved; attack presence and native grant do not prove safe contact or swallowing',
    }
    if type_id == 178:
        result.update(
            generation_function='sub_080D95A4', attack_callback='sub_080D8F34',
            activation='direction/subtype-specific horizontal threshold during bomb attack',
            constructor_calls_per_helper_invocation=1,
            collision_expiry='sub_080D9708: collision mask0x4 triggers destruction',
            native_grant_source_key='BOMBAR_BOMB',
        )
    else:
        result.update(
            generation_function='sub_080D9764', attack_callback='sub_080D9388',
            activation='animation6 and header.unk1 == 3',
            constructor_calls_per_helper_invocation=2,
            output_relationship='two simultaneous objects at separate offsets, not alternative outputs',
            native_subtype_branch='Rand16() & 1 selects subtype0; otherwise subtype1; same subtype for both missiles',
            retarget_interval=16, homing_speed_caps={'subtype0': 416, 'subtype1': 512},
            behavior_counter_initial=256, behavior_counter_is_expiry=False,
            counter_transition='at counter0 and abs(xspeed)+abs(yspeed)>=0x180, switches to trail callback sub_080D9E34',
            native_grant_source_key='BOMBAR_MISSILE',
        )
    return result


def encounter_calls(text: str, filename: str):
    for line, args in macro_calls(text):
        if 'typeVal' not in args[9]:  # Macro definition, not an instantiated call.
            yield line, args[1], args[9]
    if filename == 'dark_mind.c':
        for line, args in macro_calls(text, r'Macro_081059A8(?:_2|_3)?'):
            if args[3] != 'typeVal':
                yield line, '1', args[3]


def possible_types(filename: str, expression: str, file_hash: str,
                   text: str, names: dict[int, str]) -> list[int]:
    by_name = {name: value for value, name in names.items()}
    if expression in by_name:
        return [by_name[expression]]
    audited = VARIABLE_TYPES.get((filename, expression))
    if audited is not None and file_hash == audited[0]:
        return list(audited[1])
    array = re.fullmatch(r'(gDarkMindForm2Enemy[123]Types)\[r4\]', expression)
    if array is not None and filename == 'dark_mind.c':
        declaration = re.search(r'static const u8 ' + array[1] + r'\[\]\s*=\s*\{([^}]+)\}', text)
        if declaration is not None:
            tokens = [token.strip() for token in declaration[1].split(',') if token.strip()]
            if all(token in by_name for token in tokens):
                return sorted({by_name[token] for token in tokens})
    return []


def generated_encounter_sources(calls, controllers):
    """Index candidate outputs by physical encounter; never certify a branch."""
    parents = {row['id']: row for row in controllers}
    result = []
    for call in calls:
        for parent_id in call.get('candidate_root_encounters', []):
            parent = parents[parent_id]
            for output in call.get('possible_outputs', []):
                result.append({
                    'id': (f"{parent_id}/encounter:{call['controller_type']}/"
                           f"{call['evidence']}/type:{output['type_id']}"),
                    'native_room': parent['native_room'], 'source_type': 'encounter_spawn',
                    'logic': 'advanced', 'parent_placement': parent_id,
                    'source_key': output['source_key'], 'native_grant': output['native_grant'],
                    'native_grant_id': output['native_grant_id'], 'type_id': output['type_id'],
                    'native_name': output['native_name'], 'position_pixels': None,
                    'generation': {'controller_type': call['controller_type'],
                                   'callsite': call['evidence'],
                                   'candidate_types': [o['type_id'] for o in call['possible_outputs']],
                                   'status': 'unresolved'},
                    'access': {'status': 'unresolved', 'reason':
                               'Requires branch/activation, acquisition and encounter-lifetime evidence.'},
                    'repeatability': 'unresolved',
                })
    if len({row['id'] for row in result}) != len(result):
        raise ValueError('Duplicate generated encounter source identity')
    return result


def iter_traversals(value):
    """Include logical subregions as well as top-level native rooms."""
    if isinstance(value, dict):
        if isinstance(value.get('traversal'), dict):
            yield value['traversal']
        for child in value.values():
            yield from iter_traversals(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_traversals(child)


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
            record['native_grant'] = ability_names.get(rom[0x35164E + 24 * typ])
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
    spawner_outputs = []
    for parent in placements:
        if parent['source_type'] == 'object_spawner':
            child = spawner_output(rom, parent)
            classify(child)
            spawner_outputs.append(child)
            if child['type_id'] in ENCOUNTERS:
                encounter_types.add(child['type_id'])
    # Bombar's waiting callback tests a live-parent-relative native rectangle;
    # being somewhere in the same AP room does not activate the encounter.
    bombar_hash = hashlib.sha256((decomp / 'src/bombar.c').read_bytes()).hexdigest()
    if bombar_hash == BOMBAR_REVIEW_SHA256:
        for record in placements:
            if record['spawn_table'] == 1 and record['type_id'] == 63:
                offset = int(record['template_address'], 16) - 0x08000000
                record['native_activation'] = {
                    'status': 'conditional_native_contract', 'source_sha256': bombar_hash,
                    'callback': 'sub_080D7A6C', 'rectangle_anchor': 'live Bombar position',
                    'rectangle_offsets': list(unpack(rom, '<hhhh', offset + 0x1A)),
                    'requires': ['selected target in same native room', 'target unkC mask0x8000 clear',
                                 'Macro_08039430_1 target hitbox intersection'],
                    'access_certified': False,
                }
    controllers = placements + spawner_outputs
    for record in controllers:
        events = counter_contributions(record)
        if events:
            record['conditional_room_counter_events'] = events
    for child in spawner_outputs:
        bank = child['spawn_conditions']['room_counter_bank']
        child['spawn_conditions']['candidate_counter_contributors'] = [
            record['id'] for record in controllers
            if record['native_room'] == child['native_room']
            and any(event['bank'] == bank for event in record.get('conditional_room_counter_events', []))]
        child['spawn_conditions']['counter_reset'] = 'new room slot clears both banks; occupied room slot is reused'
        child['spawn_conditions']['counter_access_certified'] = False
        contributors = [record for record in controllers
                        if record['id'] in child['spawn_conditions']['candidate_counter_contributors']]
        if (child['spawn_conditions']['room_counter_at_least'] > 0 and contributors
                and all(record['source_type'] in ('boss', 'miniboss') for record in contributors)):
            child['logic'] = 'advanced'
            child['logic_reason'] = 'Native counter contributors are encounter defeats; access remains unresolved.'
    for room in native_rooms:
        room['spawner_outputs'] = [p['id'] for p in spawner_outputs
                                   if p['native_room'] == room['native_room']]
    source_hashes = {'include/constants/object_types.h':
                     hashlib.sha256((decomp / 'include/constants/object_types.h').read_bytes()).hexdigest()}
    for relative in ('include/data.h', 'src/code_080023A4.c', 'src/ability_objects.c',
                     'src/object.c', 'src/bonus.c', 'src/chest.c', 'src/level.c'):
        source_hashes[relative] = hashlib.sha256((decomp / relative).read_bytes()).hexdigest()
    calls = []
    pending_types = set(encounter_types)
    scanned_types = set()
    while pending_types:
        typ = min(pending_types)
        pending_types.remove(typ)
        scanned_types.add(typ)
        filename = ENCOUNTERS[typ] + '.c'
        path = decomp / 'src' / filename
        if not path.exists():
            calls.append({'controller_type': typ, 'status': 'unresolved', 'logic': 'advanced',
                          'reason': f'Missing {filename}'})
            continue
        source_hashes[f'src/{filename}'] = hashlib.sha256(path.read_bytes()).hexdigest()
        native_text = path.read_text()
        for line, table_expression, type_expression in encounter_calls(native_text, filename):
            types = (possible_types(filename, type_expression, source_hashes[f'src/{filename}'], native_text, names)
                     if table_expression == '1' else [])
            outputs = []
            for native_type in types:
                if native_type in ENCOUNTERS and native_type not in scanned_types:
                    pending_types.add(native_type)
                grant_entry = source_types.get(native_type)
                native_grant_id = rom[0x35164E + 24 * native_type]
                native_grant = ability_names.get(native_grant_id)
                if grant_entry is not None and native_grant != grant_entry[1]['default_ability']:
                    raise ValueError(f'Native encounter grant disagrees with runtime policy: {grant_entry[0]}')
                outputs.append({'type_id': native_type, 'native_name': names[native_type],
                                'source_key': grant_entry[0] if grant_entry is not None else None,
                                'native_grant_id': native_grant_id, 'native_grant': native_grant})
            calls.append({'controller_type': typ, 'evidence': f'src/{filename}:{line}',
                          'spawn_table_expression': table_expression, 'type_expression': type_expression,
                          'possible_outputs': outputs,
                          'source_key': outputs[0]['source_key'] if len(outputs) == 1 else None,
                          'logic': 'advanced', 'status': 'unresolved',
                          'candidate_encounters': [p['id'] for p in controllers
                              if p['spawn_table'] == 1 and p['type_id'] == typ],
                          'reason': ('Call-site census requires branch, helper and encounter-lifetime review; '
                                     'not an acquisition witness.')})
    # A type-level closure terminates even when a phase file can create its
    # own controller type. These are possible roots, never acquisition paths.
    roots = {typ: {p['id'] for p in controllers if p['spawn_table'] == 1 and p['type_id'] == typ}
             for typ in scanned_types}
    changed = True
    while changed:
        changed = False
        for call in calls:
            for output in call.get('possible_outputs', []):
                child = output['type_id']
                if child in roots:
                    before = len(roots[child])
                    roots[child].update(roots[call['controller_type']])
                    changed |= len(roots[child]) != before
    for call in calls:
        call['candidate_root_encounters'] = sorted(roots[call['controller_type']])
        call['controller_parent_calls'] = sorted({
            f"{parent['controller_type']}:{parent['evidence']}" for parent in calls
            if any(output['type_id'] == call['controller_type'] for output in parent.get('possible_outputs', []))})
    encounter_sources = generated_encounter_sources(calls, controllers)
    for record in encounter_sources:
        if record['generation']['controller_type'] == 56:
            contract = frostys_cube_contract(source_hashes.get('src/mr_frosty.c', ''), record['type_id'])
            if contract is not None:
                record['native_contract'] = contract
        if record['generation']['controller_type'] == 57:
            contract = bonkers_nut_contract(source_hashes.get('src/bonkers.c', ''), record['type_id'])
            if contract is not None:
                record['native_contract'] = contract
        if record['generation']['controller_type'] == 63:
            contract = bombar_output_contract(source_hashes.get('src/bombar.c', ''), record['type_id'])
            if contract is not None:
                record['native_contract'] = contract
    for room in native_rooms:
        room['encounter_controllers'] = [p['id'] for p in controllers
            if p['native_room'] == room['native_room'] and p['spawn_table'] == 1
            and p['type_id'] in ENCOUNTERS]
        room['encounter_sources'] = [p['id'] for p in encounter_sources
                                     if p['native_room'] == room['native_room']]
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
                'lifetime': {'identity': f"{parent['id']}/statue-slot:{slot}",
                             'controller_death_implies_child_death': False,
                             'reason': 'Controller marks itself destroyed after creating two independent statues.'},
                'access': {'status': 'unresolved',
                           'reason': 'Requires controller spawning and physical contact; no retry route inferred.'},
                'evidence': 'src/ability_objects.c:sub_080AA6F8/sub_080AA588',
            })
    for record in generated_statues:
        record['bounded_native_evidence'] = {
            'record': 'dev-docs/generated-statue-native-acceptance.json',
            'compartment': 'room951 lower statue floor',
            'scope': 'Configured local contact and retouch in a Boss Endurance room; not Adventure access.'}
    for record in encounter_sources:
        if record['id'] == 'room:825/template:0x088CD3F0/encounter:56/src/mr_frosty.c:762/type:166':
            record['bounded_native_evidence'] = {
                'record': 'dev-docs/generated-frosty825-native-acceptance.json',
                'compartment': 'room825 lower arrival to upper arena, live original Frosty',
                'scope': 'Nine matched 1 HP cases; conditional small-cube acquisition only. Other attack timings and safe combat/carry suffix remain uncertified.'}
        if record['id'] == 'room:955/template:0x088D5CD0/encounter:56/src/mr_frosty.c:762/type:166':
            record['bounded_native_evidence'] = {
                'record': 'dev-docs/generated-frosty-native-acceptance.json',
                'compartment': 'room955 arena, live original Frosty',
                'scope': 'Configured Boss Endurance room fixture; 6 HP arrival and one hit before finite small-cube acquisition. Not Adventure access or a safe 1 HP route.'}
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

    for traversal in iter_traversals(rooms):
        for definition in traversal.get('source_sets', {}).values():
            for source in definition['sources']:
                bind(source, definition['native_room'])
        graphs = list(traversal.get('graph_parts', {}).values()) + [
            graph for target in traversal.get('targets', []) for graph in target['graphs'].values()]
        for graph in graphs:
            nodes = {node['id']: node['native_room'] for node in graph.get('nodes', [])}
            for source in graph.get('sources', []):
                bind(source, nodes.get(source['node']))
    for record in native_rooms + placements + generated_statues + spawner_outputs + encounter_sources:
        if record['native_room'] in BOSS_ENDURANCE_ROOMS:
            record['world_access'] = {
                'status': 'outside_adventure', 'mode': 'boss_endurance',
                'evidence': 'dev-docs/native-room-wikirby-map.md#native-969-boss-endurance-nonparticipant-holding-room',
                'reason': 'Dedicated Boss Endurance room; local configured fixtures are not Adventure entries.'}
    return {'version': 1, 'rom_sha1': USA_SHA1, 'decomp_reference_commit': DECOMP_REFERENCE_COMMIT,
            'decomp_file_sha256': source_hashes,
            'scope': 'All native room object lists, including empty and aliased rooms; dynamic census is unresolved.',
            'rooms': native_rooms, 'placements': placements, 'encounter_calls': calls,
            'reviewed_bindings': dict(sorted(bindings.items())),
            'generated_statue_slots': generated_statues, 'spawner_outputs': spawner_outputs,
            'encounter_sources': encounter_sources,
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
          f"{len(result['encounter_calls'])} controller/call-site candidate pairs")


if __name__ == '__main__':
    main()
