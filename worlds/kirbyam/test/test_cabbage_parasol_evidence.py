"""Retained Parasol evidence contracts; these tests do not replay a ROM."""

import hashlib
import json
from pathlib import Path

from ..client import KirbyAmClient
from ..enemy_ability_data import ABILITY_NAME_TO_ID
from ..enemy_ability_runtime_patch import build_enemy_copy_runtime_patch_writes, build_enemy_source_runtime_config
from ..traversal import CAPABILITY_CONSUMED_ABILITIES, SourcePolicy
from ..traversal_data import room_traversal_targets
from .test_cabbage_parasol import CHEST, EVIDENCE, TARGET, cabbage_row
from .test_yellow_ufo_upstream_evidence import lf_text_sha256


def test_production_policy_setup_and_exact_target():
    evidence = json.loads(EVIDENCE.read_text(encoding='utf-8'))
    assert evidence['private_manifest_sha256'] == 'b823ca0712cc3c73198f6cfd06770f99b1332dceb75872d5229f70fb5c2ab8eb'
    assert evidence['private_report_sha256'] == 'e7e89e52067695687786f53be509bbe5c7d2eb6499d1186c8dd185d0a6fd730a'
    raw = evidence['source_policy']
    assert evidence['generation_seed'] == 29 and raw['seed'] == 14642711172500888381
    assert raw['mode'] == 1 and raw['mapping_style'] == 'per_enemy_type'
    assert set(raw['allowed_abilities']) == set(ABILITY_NAME_TO_ID) - {'Normal', 'Master', 'Wait'}
    assert build_enemy_copy_runtime_patch_writes(raw)[0x3517FE] == 5
    assert int.from_bytes(build_enemy_source_runtime_config(raw)[4:8], 'little') & (1 << 18)
    assert SourcePolicy(raw).grant('WADDLE_DOO', lambda _: True).guaranteed == frozenset({'Parasol'})
    assert evidence['source']['template'] == '0x088CA04C' and evidence['source']['native_xy'] == [528, 264]
    assert evidence['target']['location'] == CHEST and evidence['target']['location_id'] == 3960511
    assert evidence['target']['f1'] == [14, 7] and evidence['target']['chest'] == 57
    assert KirbyAmClient()._build_minor_chest_source_ptr_map()[0x8CA0B8] == 3960511
    setup = evidence['setup']
    assert setup['native_gating'] == setup['native_area_keys'] == 0
    assert setup['later_harness_writes'] == setup['state_restores'] == 0
    assert setup['initial_state_serialized'] == 'None'
    assert len(setup['fixture_byte_diff']) == 15
    writes = setup['client_config_writes']
    assert len(writes) == 8
    assert all(w['frame'] == 1085 and w['size'] == 4 and not w['guard_failed']
               and w['origin'] == 'KirbyAmClient._sync_enemy_copy_ability_runtime_config' for w in writes)
    seed = raw['seed']
    expected = {0x0203B064: 1, 0x0203B068: seed & 0xFFFFFFFF, 0x0203B06C: seed >> 32,
                0x0203B070: 0, 0x0203B074: sum(1 << ABILITY_NAME_TO_ID[n] for n in raw['allowed_abilities']),
                0x0203B0B0: 0, 0x0203B0B4: 0, 0x0203B078: 0}
    assert {int(w['address'], 16): int.from_bytes(bytes.fromhex(w['value']), 'little') for w in writes} == expected
    assert 'No compare-and-write memory GUARD' in setup['write_qualification']


def test_four_positives_and_four_full_length_controls():
    evidence = json.loads(EVIDENCE.read_text(encoding='utf-8'))
    runs = evidence['runs']
    assert {(r['hp'], r['enemy_health'], r['positive']) for r in runs.values()} == {
        (hp, health, positive) for hp in (1, 6) for health in (100, 500) for positive in (False, True)}
    assert len(runs) == 8
    assert len({r['input_sha256'] for r in runs.values() if r['positive']}) == 1
    assert len({r['input_sha256'] for r in runs.values() if not r['positive']}) == 1
    for name, run in runs.items():
        assert run['frames'] == 4217 and run['health_samples'] == 3133
        assert run['hp_min'] == run['hp_max'] == run['hp']
        assert run['helper_rooms'] == [[101, 101, 101]]
        assert run['source']['hp'] == (4 if run['enemy_health'] == 100 else 20)
        assert int(run['source']['template'], 16) == 0x088CA04C
        assert run['source']['type'] == 18 and run['source']['copy'] == 7
        assert run['transition_frame'] == 1109 and run['arrival_ability'] == 0
        assert run['acquisition_frame'] == 1939 and run['abilities_after_acquisition'] == [5]
        assert (run['corridor_f1_frame'], run['corridor_chain_done_frame']) == (2015, 2039)
        assert run['final']['ability'] == 5 and run['client']['server_submission'] is False
        if run['positive']:
            assert (run['f1_frame'], run['f2_frame'], run['chest_frame']) == (3078, 3108, 3979)
            assert run['final']['chest57'] and run['final']['event_counter'] == 1
            assert run['final']['target_f1'] == 0 and run['final']['linked_f2'] == [0] * 7
            assert int(run['final']['event_ring'][0], 16) == 0x088CA0B8
            assert run['client']['messages'] == [{'cmd': 'LocationChecks', 'locations': [3960511]}]
            swing, chain = run['target_swing'], run['chain']
            assert int(swing['task_fn'], 16) == 0x08077575 and swing['kind'] == 2 and swing['room'] == 517
            assert int(swing['parent'], 16) == 0x02020EE0
            assert swing['scan_box'] == swing['sprite_box'] == [16, -11, 48, 11]
            assert int(swing['flags'], 16) == 0xA00C0100 and int(swing['mask'], 16) == 0x30000043
            assert [swing['x'], swing['y']] == [185.99609375, 120.99609375]
            assert int(chain['task_fn'], 16) == 0x0800E27D and chain['parent'] == swing['object']
            assert [chain['x'], chain['y']] == [232, 120]
            deltas = [(d['frame'], c['x'], c['y'], c['before'], c['after'])
                      for d in run['target_tile_deltas'] for c in d['changes']]
            assert deltas == [(3078, 14, 7, 241, 0), (3084, 15, 7, 242, 0), (3090, 15, 8, 242, 0),
                              (3096, 16, 8, 242, 0), (3096, 15, 9, 242, 0), (3102, 17, 8, 242, 0),
                              (3102, 16, 9, 242, 0), (3108, 17, 9, 242, 0)]
            control = runs[name.replace('positive', 'control')]
            assert control['rom_sha256'] == run['rom_sha256']
        else:
            assert run['f1_frame'] is run['f2_frame'] is run['chest_frame'] is None
            assert run['target_swing'] is run['chain'] is None and not run['target_tile_deltas']
            assert run['final']['target_f1'] == 241 and run['final']['linked_f2'] == [242] * 7
            assert not run['final']['chest57'] and run['final']['event_counter'] == 0
            assert not run['client']['messages']
    control = evidence['control']
    assert control['common_state_through'] == 3069 and control['cutoff_frame'] == 4217
    assert control['only_input_change'] == {
        'positive': {'start': 3069, 'frames': 30, 'keys': 2},
        'control': {'start': 3069, 'frames': 30, 'keys': 0}}


def test_active_swing_contract_and_prior_graphs_are_unchanged():
    evidence = json.loads(EVIDENCE.read_text(encoding='utf-8'))
    attack = evidence['attack']
    assert attack['animation'] == 0x35 and attack['tile_scan_box'] == [16, -11, 48, 11]
    assert attack['integer_tile_rect'] == [201, 109, 233, 131] and attack['preceding_box'] == [7, -11, 31, 11]
    assert int(attack['held_flags'], 16) & 0x80000000 == 0
    assert attack['source_contract']['scanner_dispatch'] == 'asm/code_08032E98.s:8630-8636'
    assert attack['source_contract']['tile_category_filters'] == 'asm/code_08032E98.s:7238-7333'
    assert 'bomb_517_parasol_swing' not in CAPABILITY_CONSUMED_ABILITIES
    owners = [(r['id'], key) for r in room_traversal_targets('block') for key, g in r['graphs'].items()
              if any(route.get('capability') == 'bomb_517_parasol_swing' for route in g['routes'])]
    assert owners == [(TARGET, 'hub2_parasol_entry')]
    preserved = evidence['prior_graphs_sha256']
    assert set(preserved) == {'hub2_entry', 'hub2_smash_entry', 'hub2_fire_entry', 'hub2_missile_entry'}
    graphs = cabbage_row()['graphs']
    for name, digest in preserved.items():
        raw = json.dumps(graphs[name], sort_keys=True, separators=(',', ':')).encode()
        assert hashlib.sha256(raw).hexdigest() == digest


def test_canonical_tracked_text_and_private_packet_hashes_stay_separate():
    evidence = json.loads(EVIDENCE.read_text(encoding='utf-8'))
    assert evidence['tracked_text_hash_format'] == 'UTF-8 text with LF line endings (Git blob content)'
    root = Path(__file__).parents[1]
    assert evidence['preserved_source_text_sha256'] == {
        'data/abilities.json': 'ef5f85b8d44fea48bb325209bee3cd599c56b3b840f23e0b796c686499a30d27',
        'data/items.json': '97b2760dcb8d42d64671e91c353674f83f7639da9a65f19961363390ea21b72a',
        'data/enemies.json': '802474ec871dc4fad66f789456d069f426ed1dfa6301fe248bd2c88ab145e7c8',
        'data/minor_chest_manifest.json': 'aaf761f9941a23278e6654d71667a96857846ac2934eba8b7a68735800ad95c3',
    }
    # The native packet keeps its historical hashes; main deliberately changes
    # the client/catalog. Their current hashes come from the pinned main input.
    union = json.loads((root / 'dev-docs/main-ranged-union-catalog.json').read_text())
    for name, digest in evidence['preserved_source_text_sha256'].items():
        digest = union['adopted_main_source_sha256'].get(name, digest)
        raw = (root / name).read_bytes()
        assert lf_text_sha256(raw) == lf_text_sha256(raw.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')) == digest
    assert all(private not in EVIDENCE.read_text(encoding='utf-8') for private in ('/home/', '/Users/', 'C:\\'))
