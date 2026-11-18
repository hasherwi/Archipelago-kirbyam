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

    def test_nested_expressions_are_preserved_not_evaluated(self):
        calls = list(extract.macro_calls('CreateObjTemplateAndObj(a, f(1, 2), (x + y));'))
        self.assertEqual(calls, [(1, ['a', 'f(1, 2)', '(x + y)'])])

    def test_wrong_rom_is_rejected_before_source_access(self):
        with self.assertRaisesRegex(ValueError, 'USA ROM'):
            extract.build_inventory(b'wrong', Path('/not-needed'), {}, {})
