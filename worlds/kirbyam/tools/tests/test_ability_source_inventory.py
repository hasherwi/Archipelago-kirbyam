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
        data[0x14], data[0x15], data[0x22] = 0x39, 3, 3
        data[0x12], data[0x19] = 90, 2
        parent = {'id': 'room:1/template:0x08000000', 'template_address': '0x08000000',
                  'native_room': 1, 'position_pixels': [-12, 304], 'subtype1': 2, 'subtype2': 4}
        child = extract.spawner_output(data, parent)
        self.assertEqual((child['type_id'], child['configured_child_capacity']), (0x39, 3))
        self.assertEqual(child['position_pixels'], [-12, 304])
        self.assertEqual((child['subtype1'], child['subtype2']), (2, 4))
        self.assertFalse(child['reclaims_destroyed_slots'])
        self.assertEqual(child['status'], 'unresolved')
        conditions = child['spawn_conditions']
        self.assertEqual((conditions['room_counter_bank'], conditions['room_counter_at_least'],
                          conditions['delay_counter_at_least'], conditions['startup_counter_initial']),
                         (1, 2, 90, 0))
        self.assertEqual(conditions['spawned_count_below'], 3)
        self.assertEqual(conditions['global_slot_search_limit'], 32)
        self.assertEqual(conditions['exhausted_slot_behavior'], 'not_certified')
        self.assertFalse(child['lifetime']['child_has_native_parent_attachment'])
        data[0x22] = 0
        self.assertTrue(extract.spawner_output(data, parent)['reclaims_destroyed_slots'])

    def test_counter_events_distinguish_defeat_collection_and_dynamic_outputs(self):
        record = {'spawn_table': 1, 'type_id': 0x5E, 'template_flags_22': 1,
                  'spawn_conditions': {'state_bank': 0, 'bit_index': 3}}
        events = extract.counter_contributions(record)
        self.assertEqual([event['bank'] for event in events], [0, 1])
        self.assertIn('object HP <= 0', events[0]['requires'])
        record['template_flags_22'] = 0
        self.assertEqual([event['bank'] for event in extract.counter_contributions(record)], [1])
        record['native_state_identity'] = {'state_bank': 0, 'bit_index': 31}
        self.assertEqual(extract.counter_contributions(record), [])
        record.update(type_id=0x39, template_flags_22=5)
        self.assertEqual([event['bank'] for event in extract.counter_contributions(record)], [0])
        record['spawn_table'] = 2
        self.assertEqual(extract.counter_contributions(record), [])
        record.update(spawn_table=1, type_id=0x80)
        self.assertEqual(extract.counter_contributions(record)[0]['status'], 'unresolved')
        record['type_id'] = 0xA6
        self.assertEqual(extract.counter_contributions(record), [])

    def test_nested_expressions_are_preserved_not_evaluated(self):
        calls = list(extract.macro_calls('CreateObjTemplateAndObj(a, f(1, 2), (x + y));'))
        self.assertEqual(calls, [(1, ['a', 'f(1, 2)', '(x + y)'])])

    def test_wrong_rom_is_rejected_before_source_access(self):
        with self.assertRaisesRegex(ValueError, 'USA ROM'):
            extract.build_inventory(b'wrong', Path('/not-needed'), {}, {})


class NativeCandidateTests(unittest.TestCase):
    def test_frosty_branch_contract_is_conditional_and_hash_bound(self):
        small = extract.frostys_cube_contract(extract.FROSTY_REVIEW_SHA256, 166)
        large = extract.frostys_cube_contract(extract.FROSTY_REVIEW_SHA256, 167)
        self.assertNotEqual(small['branch'], large['branch'])
        self.assertEqual(small['alternative_types'], large['alternative_types'])
        self.assertEqual(small['alternative_source_keys'], ['MR_FROSTY_ICE_CUBE'])
        self.assertFalse(small['attack_entry_guaranteed'])
        self.assertEqual(small['repeatability'], 'not_certified')
        self.assertIsNone(extract.frostys_cube_contract('changed', 166))
        self.assertIsNone(extract.frostys_cube_contract(extract.FROSTY_REVIEW_SHA256, 168))

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
        inventory['ap_region_inventory'] = [
            {'region': 'mapped', 'mapping_evidence': 'native_door_list_alias'},
            {'region': 'unknown', 'mapping_evidence': 'unresolved'}]
        report = audit(inventory, rooms)
        self.assertEqual(report['declared_ap_regions'], 2)
        self.assertEqual(report['unmapped_ap_regions'], ['unknown'])


class BonkersNativeContractTests(unittest.TestCase):
    def test_branch_and_collision_contract_does_not_certify_access(self):
        contracts = [extract.bonkers_nut_contract(extract.BONKERS_REVIEW_SHA256, t) for t in (168, 169)]
        self.assertNotEqual(contracts[0]['branch'], contracts[1]['branch'])
        for contract in contracts:
            self.assertFalse(contract['attack_entry_guaranteed'])
            self.assertEqual(contract['repeatability'], 'not_certified')
            self.assertEqual(contract['parent_expiry_callback'], 'sub_0809F840')
            self.assertIn('one bounce', contract['collision_lifetime'])
        self.assertIsNone(extract.bonkers_nut_contract('changed', 168))
        self.assertIsNone(extract.bonkers_nut_contract(extract.BONKERS_REVIEW_SHA256, 166))

    def test_all_sixteen_physical_candidates_retain_non_source_status(self):
        import json
        inventory = json.loads((extract.ROOT / 'data/ability_source_inventory.json').read_text())
        rows = [r for r in inventory['encounter_sources'] if r['generation']['controller_type'] == 57]
        self.assertEqual(len(rows), 16)
        for row in rows:
            self.assertEqual(row['logic'], 'advanced')
            self.assertEqual(row['access']['status'], 'unresolved')
            self.assertIsNone(row['source_key'])
            self.assertEqual(row['native_grant'], 'Normal')
            self.assertEqual(row['native_contract'], extract.bonkers_nut_contract(
                inventory['decomp_file_sha256']['src/bonkers.c'], row['type_id']))


class BombarNativeContractTests(unittest.TestCase):
    def test_pair_and_subtype_are_not_a_branch_union_or_expiry_timer(self):
        bomb = extract.bombar_output_contract(extract.BOMBAR_REVIEW_SHA256, 178)
        missile = extract.bombar_output_contract(extract.BOMBAR_REVIEW_SHA256, 179)
        self.assertEqual(bomb['constructor_calls_per_helper_invocation'], 1)
        self.assertEqual(missile['constructor_calls_per_helper_invocation'], 2)
        self.assertIn('simultaneous', missile['output_relationship'])
        self.assertFalse(missile['behavior_counter_is_expiry'])
        self.assertEqual(missile['behavior_counter_initial'], 256)
        self.assertEqual(missile['homing_speed_caps'], {'subtype0': 416, 'subtype1': 512})
        for contract in (bomb, missile):
            self.assertFalse(contract['attack_entry_guaranteed'])
            self.assertEqual(contract['repeatability'], 'not_certified')
        self.assertIsNone(extract.bombar_output_contract('changed', 179))
        self.assertIsNone(extract.bombar_output_contract(extract.BOMBAR_REVIEW_SHA256, 168))

    def test_static_activation_rectangles_and_twelve_outputs_stay_conditional(self):
        import json
        inventory = json.loads((extract.ROOT / 'data/ability_source_inventory.json').read_text())
        controllers = [r for r in inventory['placements'] if r.get('native_activation') and r['type_id'] == 63]
        self.assertEqual({r['native_room'] for r in controllers}, {232, 326, 539})
        record = next(r for r in controllers if r['native_room'] == 232)
        self.assertEqual(record['native_activation']['rectangle'],
                         {'left_offset': -24, 'top_offset': -48, 'width': 240, 'height': 144})
        self.assertTrue(all(not r['native_activation']['access_certified'] for r in controllers))
        outputs = [r for r in inventory['encounter_sources'] if r['generation']['controller_type'] == 63]
        self.assertEqual(len(outputs), 12)
        for row in outputs:
            self.assertEqual(row['access']['status'], 'unresolved')
            self.assertEqual(row['logic'], 'advanced')
            self.assertEqual(row['native_contract'], extract.bombar_output_contract(
                inventory['decomp_file_sha256']['src/bombar.c'], row['type_id']))


class MinibossActivationContractTests(unittest.TestCase):
    def test_signed_offsets_unsigned_extents_and_distinct_anchors(self):
        raw = bytearray(36)
        struct.pack_into('<hhHH', raw, 0x1A, -24, -48, 40000, 65000)
        for typ, anchor in ((56, 'template position'), (63, 'live controller position')):
            source = {'spawn_table': 1, 'type_id': typ, 'template_address': '0x08000000'}
            native_hash = extract.MINIBOSS_ACTIVATION[typ][1]
            contract = extract.miniboss_activation(raw, source, native_hash,
                                                   extract.MINIBOSS_ACTIVATION_HEADER_SHA256)
            self.assertEqual(contract['rectangle'], {'left_offset': -24, 'top_offset': -48,
                                                      'width': 40000, 'height': 65000})
            self.assertEqual(contract['rectangle_anchor'], anchor)
            self.assertIn('integer target origin', contract['coordinate_test'])
            self.assertFalse(contract['access_certified'])
            self.assertIsNone(extract.miniboss_activation(raw, source, 'changed',
                                                          extract.MINIBOSS_ACTIVATION_HEADER_SHA256))
            self.assertIsNone(extract.miniboss_activation(raw, source, native_hash, 'changed'))

    def test_all_static_minibosses_bind_their_own_reviewed_callback(self):
        import json
        inventory = json.loads((extract.ROOT / 'data/ability_source_inventory.json').read_text())
        records = [r for r in inventory['placements'] if r.get('native_activation')]
        self.assertEqual(len(records), 36)
        self.assertEqual({r['type_id'] for r in records}, set(range(56, 64)))
        for row in records:
            contract = row['native_activation']
            file, source_hash, callback, macro = extract.MINIBOSS_ACTIVATION[row['type_id']]
            self.assertEqual(contract['source_sha256'], inventory['decomp_file_sha256']['src/' + file + '.c'])
            self.assertEqual(contract['callback'], callback)
            self.assertFalse(contract['access_certified'])
            self.assertEqual(row['access']['status'], 'unresolved')
            self.assertEqual(contract['header_sha256'], inventory['decomp_file_sha256']['include/object.h'])


class BoxyNativeContractTests(unittest.TestCase):
    def test_present_trajectory_and_contents_are_separate_selections(self):
        box = extract.boxy_output_contract(extract.BOXY_REVIEW_SHA256, 176, 'src/boxy.c:666')
        self.assertFalse(box['counter_is_wall_clock_expiry'])
        self.assertEqual(box['ground_contact_counter_initial'], 480)
        self.assertEqual(box['opening_counter_initial'], 60)
        self.assertEqual(box['parent_expiry_callback'], 'sub_0809F840')
        first = extract.boxy_output_contract(extract.BOXY_REVIEW_SHA256, 173, 'src/boxy.c:840')
        second = extract.boxy_output_contract(extract.BOXY_REVIEW_SHA256, 173, 'src/boxy.c:846')
        self.assertNotEqual(first['branch'], second['branch'])
        self.assertIn('tracked Minny', first['branch'])
        self.assertEqual(first['parent_attachment'], 'opening box')
        minny = extract.boxy_output_contract(extract.BOXY_REVIEW_SHA256, 39, 'src/boxy.c:835')
        self.assertEqual(minny['parent_attachment'], 'not assigned by generation helper')
        self.assertIn('mutually exclusive', minny['output_relationship'])
        self.assertIsNone(extract.boxy_output_contract('changed', 176, 'src/boxy.c:666'))
        self.assertIsNone(extract.boxy_output_contract(extract.BOXY_REVIEW_SHA256, 39, 'src/boxy.c:840'))

    def test_all_thirty_six_candidates_remain_conditional(self):
        import json
        inventory = json.loads((extract.ROOT / 'data/ability_source_inventory.json').read_text())
        rows = [r for r in inventory['encounter_sources'] if r['generation']['controller_type'] == 61]
        self.assertEqual(len(rows), 36)
        for row in rows:
            self.assertEqual(row['access']['status'], 'unresolved')
            self.assertEqual(row['logic'], 'advanced')
            self.assertEqual(row['native_contract'], extract.boxy_output_contract(
                inventory['decomp_file_sha256']['src/boxy.c'], row['type_id'], row['generation']['callsite']))
            self.assertFalse(row['native_contract']['attack_entry_guaranteed'])
            self.assertEqual(row['native_contract']['repeatability'], 'not_certified')


class DarkMindEnemyContractTests(unittest.TestCase):
    def test_weighted_tables_and_conditional_ufo_override_are_preserved(self):
        def contract(typ, line):
            return extract.dark_mind_enemy_contract(extract.DARK_MIND_REVIEW_SHA256,
                extract.OBJECT_REVIEW_SHA256, typ, f'src/dark_mind.c:{line}')
        third = contract(18, 8365)
        self.assertEqual(third['selection_table'].count(18), 4)
        self.assertIsNone(third['selection_override'])
        first = contract(27, 8391)
        self.assertEqual(first['initial_random_index_range'], [0, 9])
        self.assertEqual(first['selection_table'][10], 27)
        self.assertIn('selected Wheelie', first['selection_override'])
        self.assertIsNone(contract(27, 8365))
        self.assertIsNone(extract.dark_mind_enemy_contract('changed', extract.OBJECT_REVIEW_SHA256,
                                                          18, 'src/dark_mind.c:8365'))
        self.assertIsNone(extract.dark_mind_enemy_contract(extract.DARK_MIND_REVIEW_SHA256,
                                                          'changed', 18, 'src/dark_mind.c:8365'))

    def test_all_candidate_lineages_remain_unresolved_despite_shared_callback_review(self):
        import json
        inventory = json.loads((extract.ROOT / 'data/ability_source_inventory.json').read_text())
        rows = [r for r in inventory['encounter_sources']
                if r['generation']['callsite'] in extract.DARK_MIND_ENEMY_TABLES]
        self.assertEqual(len(rows), 253)
        for row in rows:
            contract = row['native_contract']
            self.assertEqual(row['access']['status'], 'unresolved')
            self.assertEqual(row['logic'], 'advanced')
            self.assertIn('unresolved', contract['root_to_phase_lineage'])
            self.assertFalse(contract['attack_entry_guaranteed'])
            self.assertIn('not assigned', contract['parent_attachment'])
            self.assertIn('interaction flag0x400', contract['cleanup'])
            self.assertEqual(contract, extract.dark_mind_enemy_contract(
                inventory['decomp_file_sha256']['src/dark_mind.c'],
                inventory['decomp_file_sha256']['src/object.c'], row['type_id'], row['generation']['callsite']))


class DarkMindProjectileContractTests(unittest.TestCase):
    def test_star_selection_and_distinct_expiry_behaviors(self):
        contracts = [extract.dark_mind_projectile_contract(extract.DARK_MIND_REVIEW_SHA256,
                     203, f'src/dark_mind.c:{line}') for line in (3824, 3856, 3877)]
        self.assertEqual([c['constructor_calls_per_helper_invocation'] for c in contracts], [2, 1, 1])
        for contract in contracts:
            self.assertEqual(contract['native_selection_by_subtype']['0'], [203])
            self.assertEqual(contract['native_selection_by_subtype']['other'], [203, 204, 205, 206])
            self.assertEqual(contract['native_mix_type'], 206)
            self.assertFalse(contract['attack_entry_guaranteed'])
        self.assertFalse(contracts[2]['phase_transition_is_expiry'])
        bomb = extract.dark_mind_projectile_contract(extract.DARK_MIND_REVIEW_SHA256, 48, 'src/dark_mind.c:4172')
        self.assertFalse(bomb['counter_is_wall_clock_expiry'])
        self.assertEqual(bomb['initial_counter'], 200)
        self.assertIsNone(extract.dark_mind_projectile_contract('changed', 203, 'src/dark_mind.c:3824'))
        self.assertIsNone(extract.dark_mind_projectile_contract(extract.DARK_MIND_REVIEW_SHA256, 48, 'src/dark_mind.c:3824'))

    def test_all_star_and_bomb_lineages_remain_conditional(self):
        import json
        inventory = json.loads((extract.ROOT / 'data/ability_source_inventory.json').read_text())
        rows = [r for r in inventory['encounter_sources'] if r['generation']['callsite'] in
                ('src/dark_mind.c:3824', 'src/dark_mind.c:3856', 'src/dark_mind.c:3877', 'src/dark_mind.c:4172')]
        self.assertEqual(len(rows), 143)
        for row in rows:
            self.assertEqual(row['access']['status'], 'unresolved')
            self.assertEqual(row['logic'], 'advanced')
            self.assertEqual(row['native_contract'], extract.dark_mind_projectile_contract(
                inventory['decomp_file_sha256']['src/dark_mind.c'], row['type_id'], row['generation']['callsite']))


class RemainingConfiguredEncounterContractTests(unittest.TestCase):
    def test_linked_constructors_and_non_source_branches_are_not_discarded(self):
        hashes = {'src/' + name + '.c': digest for name, digest in extract.OTHER_ENCOUNTER_REVIEW_SHA256.items()}
        hand = extract.other_encounter_contract(hashes, 200, 'src/master_hand.c:2456')
        self.assertIn('src/crazy_hand.c', hand['dependency_sha256'])
        self.assertEqual(hand['bullet_constructor'], 'crazy_hand.c:CreateMasterHandBullet')
        changed = dict(hashes, **{'src/crazy_hand.c': 'changed'})
        self.assertIsNone(extract.other_encounter_contract(changed, 200, 'src/master_hand.c:2456'))
        golem = extract.other_encounter_contract(hashes, 31, 'src/king_golem.c:439')
        self.assertEqual(golem['child_subtype1'], 128)
        self.assertIn('controller HP <=', golem['entry_prerequisites'])
        self.assertIn('no tracked enemy', golem['entry_prerequisites'])
        self.assertIn('destructor clears', golem['tracked_child_release'])
        self.assertIn('src/golem.c', golem['dependency_sha256'])
        moley = extract.other_encounter_contract(hashes, 195, 'src/moley.c:754')
        self.assertEqual(moley['native_alternative_types'], list(range(193, 200)))
        self.assertIn('unconfigured rock and screw', moley['output_relationship'])
        bronto = extract.other_encounter_contract(hashes, 1, 'src/wiz.c:1161')
        self.assertIsNone(bronto['initial_parent_expiry_callback'])
        self.assertIn('src/bronto_burt.c', bronto['dependency_sha256'])
        changed = dict(hashes, **{'src/bronto_burt.c': 'changed'})
        self.assertIsNone(extract.other_encounter_contract(changed, 1, 'src/wiz.c:1161'))
        gobbler = extract.other_encounter_contract(hashes, 159, 'src/gobbler.c:2378')
        self.assertEqual(gobbler['tracked_child_capacity'], 3)
        self.assertIn('only NULL slots', gobbler['slot_generation'])
        self.assertIn('HP0 alone is not', gobbler['tracked_child_release'])
        self.assertIsNone(extract.other_encounter_contract(hashes, 200, 'src/wiz.c:1161'))

    def test_all_configured_candidates_have_conditional_generation_facts_not_access(self):
        import json
        inventory = json.loads((extract.ROOT / 'data/ability_source_inventory.json').read_text())
        configured = [r for r in inventory['encounter_sources'] if r['source_key'] is not None]
        self.assertEqual(len(configured), 431)
        for row in configured:
            self.assertEqual(row['native_contract']['status'], 'conditional_native_contract')
            self.assertFalse(row['native_contract']['attack_entry_guaranteed'])
            self.assertEqual(row['access']['status'], 'unresolved')
            self.assertEqual(row['logic'], 'advanced')
        remaining = [r for r in inventory['encounter_sources']
                     if r['generation']['callsite'] in extract.OTHER_ENCOUNTER_CALLS]
        self.assertEqual(len(remaining), 26)
        for row in remaining:
            self.assertEqual(row['native_contract'], extract.other_encounter_contract(
                inventory['decomp_file_sha256'], row['type_id'], row['generation']['callsite']))


class NativeGolemGrantContractTests(unittest.TestCase):
    def test_unreviewed_native_revision_cannot_assert_phase_outputs(self):
        with self.assertRaisesRegex(ValueError, 'source hash'):
            extract.golem_grant_contract({'source_key': 'GOLEM', 'type_id': 32, 'subtype1': 0}, 'unknown')

    def test_constructor_subtype_controls_native_phase_alternatives(self):
        sha='8399d5f2bad9211e186e7c9a2374ca09de65867d10a8cc35ec28c4ecaac0ed31'
        record={'source_key': 'GOLEM', 'type_id': 32, 'native_contract': {'child_subtype1': 128}}
        self.assertEqual(extract.golem_grant_contract(record, sha)['options'], ['Stone', 'Wheel'])
        record['native_contract']['child_subtype1']=129
        self.assertEqual(set(extract.golem_grant_contract(record, sha)['options']), {'Stone', 'Wheel', 'Fighter'})
        del record['native_contract']
        self.assertEqual(set(extract.golem_grant_contract(record, sha)['options']), {'Stone', 'Wheel', 'Fighter'})


class ParasolParentContractTests(unittest.TestCase):
    def test_only_reviewed_template_variants_and_pinned_dependencies(self):
        hashes = extract.PARASOL_PARENT_HASHES
        for kind, subtype, expected in [(0, 3, ['Parasol', 'Normal']), (0, 4, ['Parasol']),
                                        (18, 1, ['Parasol', 'Beam'])]:
            record = {'type_id': kind, 'subtype1': subtype}
            contract = extract.parasol_parent_grant_contract(record, hashes)
            self.assertEqual(contract['options'], expected)
            for name in hashes:
                with self.assertRaisesRegex(ValueError, 'reviewed source hashes'):
                    extract.parasol_parent_grant_contract(record, dict(hashes, **{name: 'changed'}))
        for kind, subtype in [(0, 0), (0, 1), (0, 2), (18, 0), (18, 2), (18, 3), (17, 4), (37, 4), (18, None)]:
            self.assertIsNone(extract.parasol_parent_grant_contract({'type_id': kind, 'subtype1': subtype}, hashes))


class APRegionInventoryTests(unittest.TestCase):
    def test_all_compartments_are_explicit_without_prefix_inference_or_source_access(self):
        rooms = {'area/room': {'logical_subregions': {'lower': {}}},
                 'area/room_UPPER': {}, 'area/empty': {}}
        native = [{'native_room': 12, 'ap_room_keys': ['area/room']},
                  {'native_room': 13, 'ap_room_keys': ['area/room']},
                  {'native_room': 14, 'ap_room_keys': ['area/empty']}]
        rows = {r['region']: r for r in extract.build_ap_region_inventory(rooms, native)}
        self.assertEqual(set(rows), {'area/room', 'area/room__LOGIC__lower', 'area/room_UPPER', 'area/empty'})
        self.assertEqual(rows['area/room']['native_rooms'], [12, 13])
        self.assertEqual(rows['area/room__LOGIC__lower']['native_rooms'], [12, 13])
        self.assertEqual(rows['area/room__LOGIC__lower']['parent_region'], 'area/room')
        self.assertEqual(rows['area/room_UPPER']['native_rooms'], [])
        self.assertEqual(rows['area/room_UPPER']['mapping_evidence'], 'unresolved')
        self.assertTrue(all(r['compartment_placement_membership'].startswith('unresolved') for r in rows.values()))

    def test_declared_alias_collision_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Duplicate declared AP compartment'):
            extract.build_ap_region_inventory({'r': {'logical_subregions': {'x': {}}}, 'r__LOGIC__x': {}}, [])
