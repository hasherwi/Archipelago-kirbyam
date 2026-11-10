"""Production-normalized coverage must not omit compartments or synthetic sinks."""
import unittest

from worlds.kirbyam.data import data
from worlds.kirbyam.tools.build_ranged_target_coverage import build_coverage


class TestRangedTargetCoverage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.coverage = build_coverage()

    def test_all_production_regions(self):
        self.assertEqual({r['region'] for r in self.coverage['regions']}, set(data.regions))
        self.assertEqual(len(data.regions), 366)
        self.assertEqual(self.coverage['counts']['mapped_native_definitions'], 343)

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
        self.assertEqual(len(targets), 34)
        self.assertTrue(targets['mini_321_right_lower']['owner'].endswith('__LOGIC__RIGHT_ENTRY'))
        self.assertTrue(targets['fuse_323']['owner'].endswith('__LOGIC__CANNON_LEFT'))

    def test_room_sanity_is_separate(self):
        self.assertEqual(self.coverage['counts']['room_sanity_locations'], 263)
        sinks = [r for r in self.coverage['regions'] if r['kind'] == 'room_sanity_sink']
        self.assertTrue(sinks)
        self.assertTrue(all(r['native_room'] is not None for r in sinks))

    def test_exits_match_normalized_adjacency(self):
        actual = {(s['owner'], s['target']) for s in self.coverage['surfaces'] if s['kind'] == 'exit'}
        expected = {(key, target) for key, region in data.regions.items() for target in region.exits}
        self.assertEqual(actual, expected)

    def test_three_far_switch_placeholders_are_exposed(self):
        rows = [s for s in self.coverage['surfaces'] if 'can_hit_far_switch' in str(s['requirement'])]
        self.assertEqual(len(rows), 3)

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
