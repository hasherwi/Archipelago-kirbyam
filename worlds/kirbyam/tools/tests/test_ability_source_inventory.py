"""ROM-free decoder and native call-census boundary tests."""
import importlib
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
extract = importlib.import_module('extract_ability_source_inventory')


def rom(records):
    data = bytearray(24)
    struct.pack_into('<I', data, 0, 0x08000008)
    struct.pack_into('<I', data, 8, 0x08000018)
    for table, kind in records:
        entry = bytearray(36)
        entry[0], entry[1], entry[12] = table, 36, kind
        struct.pack_into('<hh', entry, 6, -12, 304)
        data.extend(entry)
    return data + b'\0\0'


class InventoryDecoderTests(unittest.TestCase):
    def test_preserves_duplicate_placements_and_table_namespaces(self):
        with patch.object(extract, 'OBJECT_LISTS', 0):
            records = extract.decode_records(rom([(1, 0), (1, 0), (2, 0)]), 0)
        self.assertEqual(len(records), 3)
        self.assertEqual(len({row['template_address'] for row in records}), 3)
        self.assertEqual(records[-1]['spawn_table'], 2)
        self.assertEqual(records[0]['position_pixels'], [-12, 304])

    def test_rejects_malformed_stream_and_index(self):
        with patch.object(extract, 'OBJECT_LISTS', 0):
            with self.assertRaises(ValueError):
                extract.decode_records(rom([(3, 0)]), 0)
            with self.assertRaises(ValueError):
                extract.decode_records(rom([(1, 0)])[:-5], 0)
            with self.assertRaises(ValueError):
                extract.decode_records(rom([]), -1)

    def test_empty_list_is_explicit(self):
        with patch.object(extract, 'OBJECT_LISTS', 0):
            self.assertEqual(extract.decode_records(rom([]), 0), [])

    def test_spawner_type_and_capacity_are_not_confused_with_parent_or_flags(self):
        data = bytearray(36)
        data[0x14], data[0x15], data[0x22] = 0x39, 3, 1
        parent = {'id': 'room:1/template:0x08000000', 'template_address': '0x08000000',
                  'native_room': 1, 'position_pixels': [-12, 304], 'subtype1': 2, 'subtype2': 4}
        child = extract.spawner_output(data, parent)
        self.assertEqual((child['type_id'], child['configured_child_capacity']), (0x39, 3))
        self.assertEqual(child['position_pixels'], [-12, 304])
        self.assertEqual((child['subtype1'], child['subtype2']), (2, 4))
        self.assertFalse(child['reclaims_destroyed_slots'])
        self.assertEqual(child['status'], 'unresolved')
        data[0x22] = 0
        self.assertTrue(extract.spawner_output(data, parent)['reclaims_destroyed_slots'])

    def test_nested_expressions_are_preserved_not_evaluated(self):
        calls = list(extract.macro_calls('CreateObjTemplateAndObj(a, f(1, 2), (x + y));'))
        self.assertEqual(calls, [(1, ['a', 'f(1, 2)', '(x + y)'])])

    def test_wrong_rom_is_rejected_before_source_access(self):
        with self.assertRaisesRegex(ValueError, 'USA ROM'):
            extract.build_inventory(b'wrong', Path('/not-needed'), {}, {})


class NativeCandidateTests(unittest.TestCase):
    def test_logical_subroom_traversals_are_not_dropped(self):
        root = {'room': {'traversal': {'version': 1},
                         'logical_regions': {'entry': {'traversal': {'version': 2}}}}}
        self.assertEqual([item['version'] for item in extract.iter_traversals(root)], [1, 2])

    def test_variable_type_review_is_bound_to_native_source_hash(self):
        names = {0x12: 'OBJ_WADDLE_DOO', 0x13: 'OBJ_FLAMER', 0x1C: 'OBJ_TWISTER'}
        expected_hash, expected_types = extract.VARIABLE_TYPES['kracko.c', 'type']
        self.assertEqual(extract.possible_types('kracko.c', 'type', expected_hash, '', names),
                         list(expected_types))
        self.assertEqual(extract.possible_types('kracko.c', 'type', 'changed', '', names), [])
        star_expression = 'OBJ_DARK_MIND_STAR_FIRE + r3'
        star_hash = extract.VARIABLE_TYPES['dark_mind.c', star_expression][0]
        self.assertEqual(extract.possible_types('dark_mind.c', star_expression, star_hash, '', {}),
                         [0xCB, 0xCC, 0xCD, 0xCE])
        self.assertEqual(extract.possible_types('dark_mind.c', star_expression, 'changed', '', {}), [])

    def test_dark_mind_wrapper_calls_are_not_mistaken_for_the_macro_definition(self):
        text = ('#define Macro_081059A8(obj, xVal, yVal, typeVal, a, b)\n'
                'Macro_081059A8(obj, 1, 2, OBJ_SHADOW_KIRBY_BOMB, 0, 0);')
        self.assertEqual(list(extract.encounter_calls(text, 'dark_mind.c')),
                         [(2, '1', 'OBJ_SHADOW_KIRBY_BOMB')])


class CoverageAuditTests(unittest.TestCase):
    def test_nested_policy_targets_and_explicit_references_remain_visible(self):
        audit = importlib.import_module('audit_ability_source_coverage').audit
        inventory = {'reviewed_bindings': {}, 'rooms': [],
                     'placements': [{'id': 'native', 'source_type': 'enemy'}],
                     'encounter_calls': [], 'dynamic_grant_types': [],
                     'generated_statue_slots': [], 'spawner_outputs': []}
        rooms = {'room': {'logical_regions': {'sub': {'traversal': {
            'targets': [{'id': 'nested', 'graphs': {}, 'requires_guaranteed_source': {}}]}}},
            'sources': [{'inventory_id': 'native'}, {'inventory_id': 'missing'}]}}
        report = audit(inventory, rooms)
        self.assertEqual(report['policy_scoped_targets'], [{'id': 'nested', 'fail_closed': False}])
        self.assertEqual(report['distinct_referenced_placements'], 1)
        self.assertEqual(report['unknown_inventory_references'], ['missing'])
        self.assertEqual(report['unbound_source_or_encounter_placements'], [])
