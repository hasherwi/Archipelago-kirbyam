"""Frozen scalar/hash native538 contracts; these tests do not replay the ROM."""

import hashlib
import json
from pathlib import Path

import pytest

from ..data import data, load_json_data
from ..enemy_ability_data import GATEABLE_ENEMY_COPY_ABILITIES
from ..tools.build_ranged_target_coverage import build_coverage
from ..traversal import CAPABILITY_ABILITIES, ROOM_SCOPED_CAPABILITIES
from ..traversal_data import room_traversal_targets
from .test_beam538_crossover import CAPABILITY, DESTINATION, OWNER, TARGET, UPSTREAM
from .test_yellow_ufo_upstream_evidence import lf_text_sha256
from .support.normal110_history import before_normal110
from .support.master719_history import before_master719

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'dev-docs/rainbow-beam538-acceptance.json'


def evidence():
    return json.loads(EVIDENCE.read_text(encoding='utf-8'))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def raw_targets(value):
    if isinstance(value, dict):
        yield from value.get('traversal', {}).get('targets', [])
        for child in value.values():
            yield from raw_targets(child)
    elif isinstance(value, list):
        for child in value:
            yield from raw_targets(child)


def before_reviewed_fire719_addition(rooms):
    """Compare frozen Beam538 snapshots without erasing the later reviewed Fire OR."""
    previous = json.loads(json.dumps(rooms))
    for row in raw_targets(previous):
        if row['id'] == 'bomb_110_room9':
            projected = before_normal110(row)
            row.clear()
            row.update(projected)
    target, = [row for row in raw_targets(previous) if row['id'] == 'bomb_719_room13']
    projected = before_master719(target)
    target.clear()
    target.update(projected)
    assert target['requires_guaranteed_source'] == {
        'source_key': 'WADDLE_DOO', 'abilities': ['Beam', 'Fighter', 'Sword', 'Fire']}
    graph = target['graphs'].pop('room5_fire_entry')
    assert digest(graph) == '3b2302e9a5279b590640ae82d4803d38dc039e1897103f25d447ef931f1a0d4f'
    assert graph['requires_guaranteed_source'] == {'source_key': 'WADDLE_DOO', 'ability': 'Fire'}
    assert graph['routes'][-1]['capability'] == 'bomb_719_fire_breath'
    target['requires_guaranteed_source']['abilities'].remove('Fire')
    target, = [row for row in raw_targets(previous) if row['id'] == 'bomb_517_chocolate']
    assert target['requires_guaranteed_source'] == {
        'source_key': 'WADDLE_DOO',
        'abilities': ['Beam', 'Smash', 'Fire', 'Missile', 'Parasol', 'Spark', 'Ice', 'Sword', 'Fighter', 'UFO']}
    for ability, sha256 in (
        ('Spark', '3a1c44ebb5f4aa00972240ce29ebed4d1dbf41de0c42695c015321ab16b94591'),
        ('Ice', '5e34628d8ec3d5e184a1c7b804ac3cef54f6e723a98d82f596d0db82e72a2f15'),
        ('Sword', '5ed43c0175b3f0c7eef920f50217a710b2d025e679c996c82e2dc6c808cf0b43'),
        ('Fighter', 'cfc3dead21e2dda844d11e4007f44e9f634f3115be4ca12a828117f6955aa01d'),
        ('UFO', '509cfb10498966a0448551e79c09bb0289bcea6fe8494ccdfed1e7d0073c6bf5'),
    ):
        assert digest(target['graphs'].pop(f'hub2_{ability.lower()}_entry')) == sha256
        target['requires_guaranteed_source']['abilities'].remove(ability)
    return previous


@pytest.mark.parametrize('mutation', ['access', 'placement', 'route'])
def test_historical_reconstruction_rejects_changed_fire719_graph(mutation):
    rooms = load_json_data('regions/rooms.json')
    # Do not mutate the shared loaded room data while probing this hash guard.
    rooms = json.loads(json.dumps(rooms))
    target, = [row for row in raw_targets(rooms) if row['id'] == 'bomb_719_room13']
    graph = target['graphs']['room5_fire_entry']
    if mutation == 'access':
        graph['access']['region'] = 'REGION_CARROT_CASTLE/ROOM_5_07'
    elif mutation == 'placement':
        graph['sources'][0]['node'] = 'bomb_719_room13:left_door'
    else:
        graph['routes'][2]['required_equipment'] = []
    with pytest.raises(AssertionError):
        before_reviewed_fire719_addition(rooms)


def test_exact_owner_native_rooms_and_unchanged_neighbor_contracts():
    e, rooms = evidence(), load_json_data('regions/rooms.json')
    assert e['target'] == {
        'id': TARGET, 'owner': OWNER, 'exit': DESTINATION, 'native_room': 538,
        'actual_exit_native_room': 537, 'independent_access': UPSTREAM}
    assert e['source'] == {'template': '0x088B6138', 'source_key': 'WADDLE_DOO', 'native_room': 542,
                           'native_type': 18, 'native_ability': 7, 'finite': True}
    assert CAPABILITY_ABILITIES[CAPABILITY] == frozenset({'Beam'})
    assert ROOM_SCOPED_CAPABILITIES[CAPABILITY] == 538
    assert 'Beam' not in GATEABLE_ENEMY_COPY_ABILITIES
    assert load_json_data('abilities.json')['Beam'] == {'runtime_ability_id': 7, 'safe_to_gate': False}
    union = json.loads((ROOT / 'dev-docs/main-ranged-union-catalog.json').read_text())
    for name, sha256 in e['preserved_region_sha256'].items():
        expected = union['adopted_main_region_spaced_sha256'].get(name, sha256)
        assert digest(rooms[name]) == expected
    # The main merge deliberately changes its reviewed targets. Keep the old native
    # record historical; compare those targets against the separate pinned union.
    union = json.loads((ROOT / 'dev-docs/main-ranged-union-catalog.json').read_text())
    current = {t['id']: t for t in raw_targets(rooms)}
    targets = {t['id']: t for t in raw_targets(before_reviewed_fire719_addition(rooms))}
    assert len(e['preserved_target_sha256']) == 37
    for name, sha256 in e['preserved_target_sha256'].items():
        if name in union['main_changed_targets']:
            assert digest(current[name]) == union['target_spaced_sha256'][name]
        else:
            assert digest(targets[name]) == sha256
    row, = [row for row in room_traversal_targets('block') if row['id'] == TARGET]
    assert row['new_connection'] and not row['required_for_generation']
    assert 'requires_guaranteed_source' not in row and 'requires_any_guaranteed_source' not in row
    assert row['region'] == OWNER and row['exit'] == DESTINATION
    assert set(data.regions[OWNER].exits) == {
        DESTINATION, 'REGION_RAINBOW_ROUTE/ROOM_1_35', 'REGION_RAINBOW_ROUTE/ROOM_1_37'}


def test_all_positive_and_matched_omission_boundaries():
    e = evidence()
    assert (len(e['positive']), len(e['controls'])) == (9, 4)
    assert {(c['hp'], c['options']['enemy_health_multiplier']) for c in e['positive']} == {
        (1, 100), (6, 100), (1, 500), (6, 500), (1, 124), (1, 125), (1, 349), (1, 350)}
    assert sum(c['options']['ability_gating'] for c in e['positive']) == 1
    by_name = {c['run']: c for c in e['positive']}
    for c in e['positive']:
        assert c['hp_min'] == c['hp_max'] == c['hp'] and c['final_ability'] == 7
        assert c['options']['ability_randomization_mode'] == c['options']['area_keys'] == 0
        assert [t['room'] for t in c['transitions']] == [544, 543, 542, 538, 537]
        assert c['transitions'][0]['xy'] == [40, e['startup']['first_logged_y_by_hp'][str(c['hp'])]]
        assert c['beam_acquired_frame'] < c['transitions'][3]['frame'] < c['first_scanner_frame']
        assert c['first_scanner_frame'] < c['chain_complete_frame'] < c['transitions'][-1]['frame']
        assert c['chain_change_count'] == 34 and len(c['chain_changes_sha256']) == 64
        assert c['source_first']['template'] == '0x88b6138' and c['source_first']['copy_field'] == 7
        assert c['source_last']['copy_field'] == 0 and c['source_last']['state'] == '0x809c48d'
        assert {tuple(x['xy']) for x in c['room542_changes']} == {(30, 17), (21, 8), (6, 3)}
    for c in e['controls']:
        matched = by_name[c['matched_positive']]
        assert c['hp'] == matched['hp'] and c['options'] == matched['options']
        assert c['transitions'] == matched['transitions'][:-1]
        assert c['frame_count'] == matched['frame_count'] and c['chain_unchanged']
        assert c['final_xy'] == [134, 168.99609375]
        assert c['hashes']['inputs.json'] != matched['hashes']['inputs.json']
        assert c['beam_acquired_frame'] == matched['beam_acquired_frame']
    for c in e['positive'] + e['controls']:
        assert all(len(h) == 64 and int(h, 16) >= 0 for h in c['hashes'].values())


def test_exact_left_scanner_and_nine_new_solid_cells():
    e = evidence()
    cells = e['geometry']['targets']
    assert len(cells) == 34
    assert {old: sum(c['initial'] == old for c in cells) for old in (0xF1, 0xF2, 0xF3)} == {
        0xF1: 2, 0xF2: 12, 0xF3: 20}
    assert {(c['x'], c['y']) for c in cells if c['replacement'] == 13} == {
        (8, 9), (9, 9), (10, 9), (8, 12), (9, 12), (10, 12), (11, 12), (12, 12), (9, 13)}
    assert sum(c['replacement'] == 0 for c in cells) == 25
    for c in e['positive']:
        scanner = c['first_scanner']
        assert scanner['room'] == 538 and scanner['parent'] == '0x2020ee0'
        assert scanner['counter'] == scanner['segment_frame'] == 5
        assert scanner['bounds'] == [-2, -2, 2, 2] and scanner['damage_box'] == [-6, -6, 6, 6]
        assert scanner['state'] == '0x807d209' and scanner['flags'] == '0xa0084105'
        assert scanner['category'] == '0x20000403' and scanner['damage'] == 3
        assert [scanner['x'], scanner['y']] == [91.2578125, 185.99609375]
        assert [scanner['vx'], scanner['vy']] == [-1877, -768]


def test_provenance_is_compact_separate_from_integration_and_private_payloads():
    e = evidence()
    assert e['production_source_commit'] == '6948ac7295d3b3e8e1eaf08506338592d707254e'
    assert e['integration_base'] == '0c35d3203987a3153359fa609bc4aaa6bec7a275'
    assert e['native_source_commit'] == '7d969fbce14fdc838d2c1ea01389717fb96c3189'
    assert e['private_artifact_sha256']['validation.json'] == (
        '62cb8bffe233b06ff06f30a1341aacc998cc399591e9550f09868e9404d73243')
    assert e['private_artifact_sha256']['report.md'] == (
        '0417c0d764dbe1f862d23c891301fab3b6a24f14be208a41a46d3f367f41f8a2')
    assert e['setup']['client_config_writes'] == 8 and e['setup']['configuration_frame'] == 1085
    assert e['setup']['helpers_room'] == 101 and e['setup']['fresh_blank_battery_bytes'] == 32768
    forbidden = ('gameplay_ram_writes', 'runtime_rom_writes', 'state_restores',
                 'phone_inputs', 'helper_parent_attacks_in_route')
    assert not any(e['setup'][k] for k in forbidden)
    assert 'zero-frame snapshot at1541' in e['hash_semantics']
    assert any('continuous upstream1HP' in limit for limit in e['limitations'])
    union = json.loads((ROOT / 'dev-docs/main-ranged-union-catalog.json').read_text())
    for path, expected in e['tracked_source_sha256'].items():
        expected = union['adopted_main_source_sha256'].get(path, expected)
        assert lf_text_sha256((ROOT / path).read_bytes()) == expected
    for path in (EVIDENCE, EVIDENCE.with_name('rainbow-beam538-source-witness.md')):
        text = path.read_text(encoding='utf-8')
        assert all(private not in text for private in ('/home/', '/Users/', 'C:\\', 'D:\\'))
    assert not any(k in e for k in ('inputs', 'frames', 'replay', 'savestate'))


def test_historical_ownership_snapshot_and_current_union_are_separate():
    snapshot = evidence()['structural_snapshot']
    current = build_coverage()
    # Preserve the native record's actual earlier catalog and starting permissions.
    assert snapshot['counts'] == {
        'regions': 366, 'mapped_native_definitions': 343, 'locations': 384,
        'surfaces': 1059, 'room_sanity_locations': 263, 'installed_target_definitions': 38}
    assert current['counts'] == {
        'regions': 382, 'mapped_native_definitions': 352, 'locations': 384,
        'surfaces': 1083, 'room_sanity_locations': 263, 'installed_target_definitions': 57}
    assert set(snapshot['input_sha256']) == set(current['input_sha256'])
    # Exact current target/part/source bytes are pinned against both reviewed
    # parents by test_main_ranged_union, not labeled as fresh native evidence.
    assert snapshot['new_surface'] == {
        'owner': OWNER, 'kind': 'exit', 'target': DESTINATION, 'requirement': None, 'room_sanity': False}


def test_separate_health_supplement_preserves_exact_frozen_identity_and_scope():
    primary = evidence()
    reference = primary['health_supplement']
    raw = (EVIDENCE.parent / reference['file']).read_bytes()
    assert lf_text_sha256(raw) == reference['sha256'] == (
        '376fab1233e223f95974d611641defbf7b2a3bfdb23be6cdcfec1dfda4a9c2ae')
    assert reference['private_inventory_sha256'] == (
        'd8469923b3793d874b3a66c57d39f76b094c5b1ece2101fd9af3efc84a76e3b6')
    supplement = json.loads(raw)
    assert supplement['status'] == 'PASS_BOUNDED'
    assert (supplement['new_no_hit_1hp_runs'], supplement['known_tuple_classes'],
            supplement['primary_representatives']) == (26, 32, 6)
    assert len(supplement['positive_runs']) == 26
    assert all(private not in raw for private in (b'/home/', b'/Users/', b'C:\\', b'D:\\'))
    assert any('not all percentages or all RNG' in limit for limit in supplement['limits'])
    assert any('No full upstream1HP' in limit for limit in supplement['limits'])
    assert all(len(h) == 64 and int(h, 16) >= 0 for h in supplement['artifact_hashes'].values())


def test_all32_health_tuples_have_actual_native_representatives_not_interpolation():
    from ..enemy_health_scaling import scale_hp_value
    primary = evidence()
    supplement = json.loads((EVIDENCE.parent / primary['health_supplement']['file']).read_text(encoding='utf-8'))
    intervals = supplement['tuple_coverage']
    tuples = {tuple(scale_hp_value(base, h) for base in (1, 2, 4)) for h in range(50, 501)}
    assert len(intervals) == len(tuples) == 32
    assert {tuple(interval['tuple']) for interval in intervals} == tuples
    assert [h for interval in intervals for h in range(interval['lo'], interval['hi'] + 1)] == list(range(50, 501))
    packets = {'primary': {c['run']: c for c in primary['positive']},
               'supplement': {c['run']: c for c in supplement['positive_runs']}}
    for interval in intervals:
        expected = tuple(interval['tuple'])
        assert all(tuple(scale_hp_value(base, h) for base in (1, 2, 4)) == expected
                   for h in range(interval['lo'], interval['hi'] + 1))
        representative = interval['representative']
        case = packets[representative['packet']][representative['run']]
        assert case['hp'] == 1 and case['options']['enemy_health_multiplier'] == representative['percent']
        assert interval['lo'] <= representative['percent'] <= interval['hi']
        assert representative['input_sha256'] == case['hashes']['inputs.json']
        assert representative['state_sha256'] == case['hashes']['states.json']
    for case in supplement['positive_runs']:
        assert case['hp'] == case['options']['minimum_health'] == case['options']['maximum_health'] == 1
        assert case['options']['ability_randomization_mode'] == case['options']['ability_gating'] == 0
        assert case['options']['area_keys'] == 0
        assert [t['room'] for t in case['transitions']] == [544, 543, 542, 538, 537]
        h1, h2, h4 = case['rounded_hp_tuple']
        runtime = case['runtime_initial_health']
        assert runtime['0x88c30c0']['hp'] == h2  # Waddle before the Normal fall.
        assert runtime['0x88c3054']['hp'] == runtime['0x88b6138']['hp'] == h4  # Sparky and original Doo.
        assert runtime['0x88b6060']['hp'] == h1  # Scarfy.
        recipe = 'full05' if case['options']['enemy_health_multiplier'] < 125 else 'full500-04'
        assert case['hashes']['inputs.json'] == packets['primary'][recipe]['hashes']['inputs.json']


@pytest.mark.parametrize('ability', ['Spark', 'Ice', 'Sword', 'Fighter', 'UFO'])
@pytest.mark.parametrize('mutation', ['access', 'placement', 'route', 'applicability', 'unrelated'])
def test_historical_reconstruction_does_not_mask_cabbage_edits(ability, mutation):
    rooms = json.loads(json.dumps(load_json_data('regions/rooms.json')))
    target, = [row for row in raw_targets(rooms) if row['id'] == 'bomb_517_chocolate']
    graph = target['graphs'][f'hub2_{ability.lower()}_entry']
    if mutation == 'access':
        graph['access']['region'] = 'REGION_CABBAGE_CAVERN/ROOM_3_06'
    elif mutation == 'placement':
        graph['sources'][0]['node'] = 'bomb_517_chocolate:chest'
    elif mutation == 'route':
        graph['routes'][-1]['allowed_abilities'] = ['Beam']
    elif mutation == 'applicability':
        target['requires_guaranteed_source']['abilities'].remove(ability)
    else:
        target['graphs']['hub2_entry']['routes'][-1]['allowed_abilities'] = ['Ice']
        previous = before_reviewed_fire719_addition(rooms)
        restored, = [row for row in raw_targets(previous) if row['id'] == 'bomb_517_chocolate']
        assert digest(restored) != evidence()['preserved_target_sha256']['bomb_517_chocolate']
        return
    with pytest.raises(AssertionError):
        before_reviewed_fire719_addition(rooms)
