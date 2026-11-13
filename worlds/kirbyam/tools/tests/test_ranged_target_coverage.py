"""Production-normalized coverage must not omit compartments or synthetic sinks."""
import hashlib
import unittest
from pathlib import PurePosixPath, PureWindowsPath

from worlds.kirbyam.data import data
from worlds.kirbyam.tools.build_ranged_target_coverage import ROOT, _input_path_key, build_coverage


class TestRangedTargetCoverage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.coverage = build_coverage()

    def test_all_production_regions(self):
        self.assertEqual({r['region'] for r in self.coverage['regions']}, set(data.regions))
        self.assertEqual(len(data.regions), 384)
        self.assertEqual(self.coverage['counts']['mapped_native_definitions'], 353)

    def test_locations_owned_once_after_moves(self):
        rows = [s for s in self.coverage['surfaces'] if s['kind'] == 'location']
        self.assertEqual(len(rows), len(data.locations))
        self.assertEqual({s['target'] for s in rows}, set(data.locations))
        for row in rows:
            self.assertEqual(row['owner'].removesuffix('__ROOM_CHECK'),
                             data.locations[row['target']].parent_region)
        moved = next(s for s in rows if s['target'] == 'MINOR_CHEST_MUSTARD_MOUNTAIN_4_05')
        self.assertTrue(moved['owner'].endswith('__LOGIC__RIGHT_ENTRY'))

    def test_nested_targets_are_present(self):
        targets = {r['target']['id']: r for r in self.coverage['installed_targets']}
        self.assertEqual(len(targets), 57)
        self.assertTrue(targets['mini_321_right_lower']['owner'].endswith('__LOGIC__RIGHT_ENTRY'))
        self.assertTrue(targets['fuse_323']['owner'].endswith('__LOGIC__CANNON_LEFT'))
        rainbow = targets['bomb_110_room9']
        self.assertEqual(rainbow['owner'], 'REGION_RAINBOW_ROUTE/ROOM_1_08')
        self.assertEqual(rainbow['target']['exit'], 'REGION_RAINBOW_ROUTE/ROOM_1_09')
        self.assertEqual(set(rainbow['target']['graphs']),
                         {'upper_entry', 'upper_entry_sword', 'upper_entry_normal_water'})
        green_target = targets['bomb_138_green']
        self.assertEqual(green_target['owner'], 'REGION_RAINBOW_ROUTE/ROOM_1_28')
        self.assertEqual(green_target['target']['location'], 'MINOR_CHEST_SPRAY_PAINT_04')
        self.assertNotIn('exit', green_target['target'])
        self.assertNotIn('requires_guaranteed_source', green_target['target'])
        self.assertEqual(set(green_target['target']['graphs']),
                         {'upper_left_entry', 'upper_left_normal_slide'})
        self.assertEqual(green_target['target']['graphs']['upper_left_entry']['requires_guaranteed_source'],
                         {'source_key': 'SPARKY', 'ability': 'Spark'})
        yellow_target = targets['bomb_733_yellow']
        self.assertEqual(yellow_target['owner'], 'REGION_CARROT_CASTLE/ROOM_5_16')
        self.assertEqual(yellow_target['target']['location'], 'MINOR_CHEST_SPRAY_PAINT_02')
        self.assertNotIn('exit', yellow_target['target'])
        map_target = targets['switch_310_mustard_map']
        self.assertEqual(map_target['owner'], 'REGION_MUSTARD_MOUNTAIN/ROOM_4_CHEST')
        self.assertEqual(map_target['target']['location'], 'MAJOR_CHEST_MUSTARD_MOUNTAIN')
        self.assertNotIn('exit', map_target['target'])
        beam = targets['bomb_538_beam_left_exit']
        self.assertEqual(beam['owner'], 'REGION_RAINBOW_ROUTE/ROOM_1_36_VERTICAL')
        self.assertEqual(beam['target']['exit'], 'REGION_RAINBOW_ROUTE/ROOM_1_39')
        self.assertEqual(beam['target']['native_room'], 538)
        self.assertTrue(beam['target']['new_connection'])
        self.assertFalse(beam['target']['required_for_generation'])

    def test_room_sanity_is_separate(self):
        self.assertEqual(self.coverage['counts']['room_sanity_locations'], 263)
        sinks = [r for r in self.coverage['regions'] if r['kind'] == 'room_sanity_sink']
        self.assertTrue(sinks)
        self.assertTrue(all(r['native_room'] is not None for r in sinks))

    def test_exits_match_normalized_adjacency(self):
        actual = {(s['owner'], s['target']) for s in self.coverage['surfaces'] if s['kind'] == 'exit'}
        expected = {(key, target) for key, region in data.regions.items() for target in region.exits}
        self.assertEqual(actual, expected)

    def test_remaining_far_switch_placeholders_are_exposed(self):
        rows = [s for s in self.coverage['surfaces'] if 'can_hit_far_switch' in str(s['requirement'])]
        self.assertEqual({(row['owner'], row['target']) for row in rows}, {
            ('REGION_MUSTARD_MOUNTAIN/ROOM_4_15', 'REGION_MUSTARD_MOUNTAIN/ROOM_4_16'),
            ('REGION_MUSTARD_MOUNTAIN/ROOM_4_CHEST', 'MAJOR_CHEST_MUSTARD_MOUNTAIN'),
        })

    def test_every_target_binds_to_exact_owner_surface(self):
        surfaces = {(s['owner'], s['kind'], s['target']) for s in self.coverage['surfaces']}
        for row in self.coverage['installed_targets']:
            target = row['target']
            kind = 'exit' if target.get('exit') else 'location'
            self.assertIn((row['owner'], kind, target[kind]), surfaces)
        carrot = next(r for r in self.coverage['installed_targets']
                      if r['target']['id'] == 'bomb_719_room13')
        self.assertTrue(carrot['target']['exit'].endswith('__LOGIC__ENTRY_FROM_5_07'))

    def test_provenance_hashes_cover_normalizer_and_region_inputs(self):
        hashes = self.coverage['input_sha256']
        for name in ('data.py', 'data/regions/rooms.json', 'data/regions/areas.json',
                     'data/locations.json', 'dev-docs/native-room-wikirby-map.json'):
            self.assertEqual(len(hashes[name]), 64)
            self.assertEqual(hashes[name], hashlib.sha256((ROOT / name).read_bytes()).hexdigest())

    def test_input_path_keys_are_portable(self):
        for root in (PurePosixPath('/repo/worlds/kirbyam'), PureWindowsPath('C:/repo/worlds/kirbyam')):
            for name in ('data.py', 'data/regions/rooms.json', 'dev-docs/native-room-wikirby-map.json'):
                with self.subTest(root=root, name=name):
                    self.assertEqual(_input_path_key(root / name, root), name)
