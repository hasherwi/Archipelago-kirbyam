"""Finite Missile carry and local dry detonation only for the Chocolate chest."""

import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from BaseClasses import CollectionState, ItemClassification

from .support.source_policy import set_rule_test_policy
from .. import KirbyAmWorld, traversal_rules as rules
from ..client import KirbyAmClient
from ..data import data
from ..enemy_ability_data import ABILITY_NAME_TO_ID, GATEABLE_ENEMY_COPY_ABILITIES
from ..enemy_ability_runtime_patch import build_enemy_copy_runtime_patch_writes, build_enemy_source_runtime_config
from ..traversal import Position, SourcePolicy
from ..traversal_data import load_room_traversal, room_traversal_graph, room_traversal_targets
from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive
from .test_mini_traversal import make_world
from .test_traversal import policy

TARGET = 'bomb_517_chocolate'
OWNER = 'REGION_CABBAGE_CAVERN/ROOM_3_06'
UPSTREAM = 'REGION_CABBAGE_CAVERN/ROOM_3_HUB_2'
CHEST = 'MINOR_CHEST_SPRAY_PAINT_12'
EVIDENCE = Path(__file__).parents[1] / 'dev-docs/cabbage-missile-acceptance.json'
POLICIES = [
    (0, None, 0, 'Beam'), (1, ['Beam'], 0, 'Beam'), (1, ['Smash'], 0, 'Smash'),
    (1, ['Missile'], 0, 'Missile'), (1, ['Fire'], 0, 'Fire'), (1, ['Spark'], 0, 'Spark'),
    (1, ['Ice'], 0, 'Ice'), (1, ['Sword'], 0, 'Sword'),
    (1, ['Fighter'], 0, 'Fighter'), (1, ['UFO'], 0, 'UFO'),
    (2, ['Missile'], 0, 'Missile'), (2, ['Missile', 'Smash'], 0, None),
    (2, ['Missile', 'Fire'], 0, None), (2, ['Missile', 'Ice'], 0, None),
    (2, ['Missile'], 50, None), (2, ['Missile'], 100, None),
    (2, None, 0, None),
]


def cabbage_row():
    return next(row for row in room_traversal_targets('block') if row['id'] == TARGET)


@pytest.mark.parametrize('mode,pool,weight,ability', POLICIES)
@pytest.mark.parametrize('statues', [False, True])
def test_independent_beam_smash_missile_or_policy(mode, pool, weight, ability, statues):
    resolver = policy(mode, pool=pool, weight=weight, statues=statues)
    row = cabbage_row()
    assert rules.target_applies(row, resolver) is (ability is not None)
    if ability:
        results = [rules.graph_succeeds(g, resolver, frozenset({f'{ability} Ability'}), True, retries=False)
                   for g in rules.target_graphs(row, False)]
        assert results == [ability == name for name in
                           ('Beam', 'Smash', 'Fire', 'Missile', 'Parasol', 'Spark', 'Ice', 'Sword', 'Fighter', 'UFO')]
    # The same enemy key does not widen Carrot's independently reviewed alternatives.
    carrot = next(r for r in room_traversal_targets('block') if r['id'] == 'bomb_719_room13')
    if ability == 'Missile':
        assert not rules.target_applies(carrot, resolver)


@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('area_keys', [False, True])
def test_finite_source_permission_and_actual_equipment(gating, area_keys):
    graph = room_traversal_graph(TARGET, 'hub2_missile_entry', area_keys)
    resolver = SourcePolicy(json.loads(EVIDENCE.read_text())['source_policy'])
    assert graph.access_region == UPSTREAM
    assert graph.required_guaranteed_source == ('WADDLE_DOO', 'Missile')
    assert all(start.equipped == 'Normal' for start in graph.starts)
    assert [(n.key.rsplit(':', 1)[-1], n.room) for n in graph.nodes] == [
        ('hub2', 591), ('arrival', 517), ('source', 517), ('chest', 517)]
    source, = graph.placements
    assert (source.identity, source.source_key, source.renewable, source.retry_evidence) == (
        '0x088CA04C', 'WADDLE_DOO', False, None)
    assert [r.resets_room_instance for r in graph.routes] == [True, False, False]
    assert all(not r.items and not r.opens and not r.recover_dropped_ability for r in graph.routes)
    assert graph.routes[-1].capability == 'bomb_517_missile_blast'
    assert graph.routes[-1].allowed_abilities == frozenset({'Missile'})
    chest, = graph.required_targets
    owned = frozenset({'Missile Ability'})
    result = graph.evaluate(resolver, owned, gating, allow_documented_retries=True)
    assert result.reaches(chest) and not result.retry_assumptions
    arrivals = [p for p in result.positions if p.node == chest]
    assert any(p.equipped == 'Missile' for p in arrivals)
    assert all(p.equipped in {'Missile', 'Normal'} and source.identity in p.consumed for p in arrivals)
    assert graph.evaluate(resolver, frozenset(), gating).reaches(chest) is (not gating)
    assert not replace(graph, placements=()).evaluate(resolver, owned, gating).reaches(chest)
    assert not replace(graph, placements=(replace(source, node=chest),)).evaluate(
        resolver, owned, gating).reaches(chest)
    spent = replace(graph, starts=(Position(source.node, 'Normal', consumed=frozenset({source.identity})),))
    assert not spent.evaluate(resolver, owned, gating).reaches(chest)
    for ability in ('Beam', 'Smash', 'Spark', 'Ice', 'Fire'):
        assert not graph.evaluate(policy(1, pool=[ability]), owned, gating).reaches(chest)


@pytest.mark.parametrize('pool,weight', [
    (['Missile', 'Smash'], 0), (['Missile', 'Ice'], 0), (['Missile', 'Fire'], 0), (['Missile'], 50), (['Missile'], 100),
])
@pytest.mark.parametrize('owned', [frozenset(), frozenset({'Missile Ability'}),
                                   frozenset({'Missile Ability', 'Smash Ability', 'Ice Ability', 'Fire Ability'})])
@pytest.mark.parametrize('gating', [False, True])
def test_raw_policy_guard_prevents_permission_narrowing(pool, weight, owned, gating):
    graph = room_traversal_graph(TARGET, 'hub2_missile_entry')
    resolver = policy(2, pool=pool, weight=weight)
    assert not graph.evaluate(resolver, owned, gating, allow_documented_retries=True).positions


@pytest.mark.parametrize('update', [
    {'id': 'bomb_719_room13'}, {'kind': 'switch'}, {'native_room': 719},
    {'region': 'REGION_CARROT_CASTLE/ROOM_5_07'}, {'location': 'MINOR_CHEST_MUSIC_NOTE_10'},
    {'requires_guaranteed_source': {'source_key': 'HOT_HEAD', 'abilities': ['Beam', 'Smash', 'Missile']}},
    {'requires_guaranteed_source': {'source_key': 'WADDLE_DOO', 'abilities': ['Missile']}},
    {'requires_guaranteed_source': {'source_key': 'WADDLE_DOO', 'abilities': ['Beam', 'Smash', 'Missile', 'Ice']}},
])
def test_target_condition_cannot_spread(update):
    row = deepcopy(cabbage_row())
    row.update(update)
    region = row.pop('region')
    with pytest.raises(ValueError, match='applicability'):
        load_room_traversal({region: {'traversal': {'version': 1, 'targets': [row]}}})


@pytest.mark.parametrize('gating', [0, 1])
@pytest.mark.parametrize('area_keys', [0, 1])
@pytest.mark.parametrize('statues', [0, 1])
@pytest.mark.parametrize('room_sanity', [0, 1])
@pytest.mark.parametrize('minor_chests', [False, True])
def test_actual_world_binds_only_chest_and_preserves_progression(
        monkeypatch, gating, area_keys, statues, room_sanity, minor_chests):
    raw = json.loads(EVIDENCE.read_text())['source_policy']
    monkeypatch.setattr(KirbyAmWorld, 'ENABLE_MINOR_CHESTS', minor_chests)
    set_rule_test_policy(monkeypatch, lambda *args, **kwargs: raw)
    world = make_world(1, gating, accessibility='minimal', area_keys=area_keys,
                       ability_randomization_statues=statues, room_sanity=room_sanity,
                       ability_randomization_no_ability_weight=0)
    state = CollectionState(world.multiworld)
    state.can_reach_region = lambda name, player: name == OWNER
    item = world.create_item('Missile Ability')
    assert 'Missile' in GATEABLE_ENEMY_COPY_ABILITIES
    assert item.classification == (ItemClassification.progression if gating and minor_chests
                                   else ItemClassification.useful)
    if minor_chests:
        chest = world.multiworld.get_location(data.locations[CHEST].label, 1)
        assert chest.address == 3960511 and chest.parent_region.name == OWNER
        assert not chest.access_rule(state)
        state.collect(item, prevent_sweep=True)
        assert not chest.access_rule(state)  # Permission does not supply Hub2 access.
        state.remove(item)
        state.can_reach_region = lambda name, player: name == UPSTREAM
        assert chest.access_rule(state) is (not gating)
        for wrong in ('Beam Ability', 'Smash Ability', 'Fire Ability'):
            state.collect(world.create_item(wrong), prevent_sweep=True)
        assert chest.access_rule(state) is (not gating)
        state.collect(item, prevent_sweep=True)
        assert state.has('Missile Ability', 1) is bool(gating)
        assert chest.access_rule(state)
        state.remove(item)
        assert chest.access_rule(state) is (not gating)
    else:
        with pytest.raises(KeyError):
            world.multiworld.get_location(data.locations[CHEST].label, 1)
    state.can_reach_region = lambda name, player: name == OWNER
    owner = world.multiworld.get_region(OWNER, 1)
    assert all(exit.access_rule(state) for exit in owner.exits)
    room_checks = [loc for loc in owner.locations if loc.address != 3960511]
    assert len(room_checks) == room_sanity
    assert all(loc.access_rule(state) for loc in room_checks)
    area = world.multiworld.get_entrance(
        'REGION_RAINBOW_ROUTE/ROOM_1_13_LOWER -> REGION_CABBAGE_CAVERN/ROOM_3_04', 1)
    assert area.access_rule(state) is (not area_keys)
    state.collect(world.create_item('Cabbage Cavern - Area Key'), prevent_sweep=True)
    assert area.access_rule(state)


@pytest.mark.parametrize('mode,pool,weight,ability', POLICIES)
@pytest.mark.parametrize('gating', [0, 1])
def test_actual_world_uncertain_policies_keep_prior_rule(monkeypatch, mode, pool, weight, ability, gating):
    resolver = policy(mode, pool=pool, weight=weight, minny=False)
    set_rule_test_policy(monkeypatch, lambda *args, **kwargs: resolver.policy)
    world = make_world(mode, gating, accessibility='minimal', ability_randomization_no_ability_weight=weight)
    chest = world.multiworld.get_location(data.locations[CHEST].label, 1)
    assert world.create_item('Missile Ability').classification == (
        ItemClassification.progression if gating and ability == 'Missile' else ItemClassification.useful)
    state = CollectionState(world.multiworld)
    state.can_reach_region = lambda name, player: name == OWNER
    assert chest.access_rule(state) is (ability is None)
    for name in ('Beam', 'Smash', 'Fire', 'Missile', 'Spark', 'Ice', 'Sword', 'Fighter', 'UFO'):
        state.collect(world.create_item(f'{name} Ability'), prevent_sweep=True)
    assert chest.access_rule(state) is (ability is None)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    assert chest.access_rule(state)
    state.remove(world.create_item('Missile Ability'))
    assert chest.access_rule(state) is (not (ability == 'Missile' and gating))


@pytest.mark.parametrize('gating,area_keys,health', [(0, 0, 100), (1, 0, 100), (0, 1, 500), (1, 1, 500)])
def test_full_seed5_fill_uses_actual_policy_and_progression(tmp_path, monkeypatch, gating, area_keys, health):
    import Main

    generated = []
    main = Main.main

    def capture(*args, **kwargs):
        multiworld = main(*args, **kwargs)
        generated.append(multiworld)
        return multiworld

    monkeypatch.setattr(Main, 'main', capture)
    player = tmp_path / 'player.yaml'
    player.write_text(
        'name: Missile517\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n'
        '  ability_randomization_mode: 1\n  ability_randomization_no_ability_weight: 0\n'
        f'  ability_gating: {gating}\n  area_keys: {area_keys}\n  enemy_health_multiplier: {health}\n'
        '  minimum_health: 1\n  maximum_health: 1\n  accessibility: full\n', encoding='utf-8')
    archive = generate_archive_from_fixture(player, tmp_path / 'out', seed=5)
    decoded = load_multidata_from_archive(archive)
    raw = decoded['slot_data'][1]['enemy_copy_ability_policy']
    assert {**raw, 'allowed_abilities': list(raw['allowed_abilities'])} == (
        json.loads(EVIDENCE.read_text())['source_policy'])
    assert SourcePolicy(raw).grant('WADDLE_DOO', lambda _: True).guaranteed == frozenset({'Missile'})
    assert decoded['locations'][1][3960511]
    multiworld, = generated
    assert not multiworld.get_unfilled_locations()
    assert multiworld.can_beat_game() and multiworld.fulfills_accessibility()
    world = multiworld.worlds[1]
    state = CollectionState(multiworld)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    chest = multiworld.get_location(data.locations[CHEST].label, 1)
    assert chest.access_rule(state) is (not gating)
    state.collect(world.create_item('Missile Ability'), prevent_sweep=True)
    assert chest.access_rule(state)


@pytest.mark.parametrize('gating,minor_chests,count', [
    (1, True, 1), (1, True, 3), (0, True, 1), (1, False, 1), (1, False, 3),
])
def test_full_seed5_start_inventory_is_reconciled_after_regions(
        tmp_path, monkeypatch, gating, minor_chests, count):
    import Main

    generated, region_states = [], []
    main, create_regions = Main.main, KirbyAmWorld.create_regions

    def capture_regions(world):
        create_regions(world)
        region_states.append(world.multiworld.state.count('Missile Ability', world.player))

    def capture_main(*args, **kwargs):
        multiworld = main(*args, **kwargs)
        generated.append(multiworld)
        return multiworld

    monkeypatch.setattr(KirbyAmWorld, 'ENABLE_MINOR_CHESTS', minor_chests)
    monkeypatch.setattr(KirbyAmWorld, 'create_regions', capture_regions)
    monkeypatch.setattr(Main, 'main', capture_main)
    player = tmp_path / 'player.yaml'
    player.write_text(
        'name: Starting Missile\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n'
        '  ability_randomization_mode: 1\n  ability_randomization_no_ability_weight: 0\n'
        f'  ability_gating: {gating}\n  start_inventory:\n    Missile Ability: {count}\n'
        f'  room_sanity: {int(not minor_chests)}\n'  # Supply slots when minor chests are disabled.
        '  minimum_health: 1\n  maximum_health: 1\n  accessibility: full\n', encoding='utf-8')
    archive = generate_archive_from_fixture(player, tmp_path / 'out', seed=5)
    decoded = load_multidata_from_archive(archive)
    raw = decoded['slot_data'][1]['enemy_copy_ability_policy']
    assert SourcePolicy(raw).grant('WADDLE_DOO', lambda _: True).guaranteed == frozenset({'Missile'})
    assert decoded['precollected_items'][1].count(3860125) == count
    multiworld, = generated
    assert not multiworld.get_unfilled_locations()
    assert multiworld.can_beat_game() and multiworld.fulfills_accessibility()
    expected_count = count if gating and minor_chests else 0
    assert region_states == [expected_count]  # Existing state repaired once, before fill.
    starting = [item for item in multiworld.precollected_items[1] if item.name == 'Missile Ability']
    assert len(starting) == count
    assert all(item.classification == (ItemClassification.progression if expected_count else ItemClassification.useful)
               for item in starting)
    state = CollectionState(multiworld)
    assert state.count('Missile Ability', 1) == expected_count  # Fresh states see the same permissions.
    if not minor_chests:
        with pytest.raises(KeyError):
            multiworld.get_location(data.locations[CHEST].label, 1)
        return
    chest = multiworld.get_location(data.locations[CHEST].label, 1)
    state.can_reach_region = lambda name, player: name == OWNER
    assert not chest.access_rule(state)  # Starting permission still does not equip or supply Hub2.
    state.can_reach_region = lambda name, player: name == UPSTREAM
    assert chest.access_rule(state)
    for item in starting:
        state.remove(item)
    assert not state.has('Missile Ability', 1)
    assert chest.access_rule(state) is (not gating)


def test_reconciliation_does_not_recollect_already_progression_missile(monkeypatch):
    from test.general import setup_multiworld

    raw = json.loads(EVIDENCE.read_text())['source_policy']
    set_rule_test_policy(monkeypatch, lambda *args, **kwargs: raw)
    multiworld = setup_multiworld(KirbyAmWorld, steps=('generate_early',), seed=5, options={
        'ability_randomization_mode': 1, 'ability_gating': 1, 'accessibility': 'minimal',
    })
    world = multiworld.worlds[1]
    ready = world.create_item('Missile Ability')
    ready.classification = ItemClassification.progression
    multiworld.push_precollected(ready)
    for _ in range(2):
        early = world.create_item('Missile Ability')
        assert early.classification == ItemClassification.useful
        multiworld.push_precollected(early)
    assert multiworld.state.count('Missile Ability', 1) == 1
    world.create_regions()
    assert multiworld.state.count('Missile Ability', 1) == 3
    assert CollectionState(multiworld).count('Missile Ability', 1) == 3


def test_promotion_requires_actual_chest_and_source_policy():
    raw = json.loads(EVIDENCE.read_text())['source_policy']
    world = SimpleNamespace(player=1, _enemy_copy_ability_policy=raw, _ability_gating_enabled=lambda: True,
                            multiworld=SimpleNamespace(get_location=lambda *args: object()))
    assert rules.cabbage_missile_is_progression(world)

    def absent(*args):
        raise KeyError('disabled')

    world.multiworld.get_location = absent
    assert not rules.cabbage_missile_is_progression(world)
    world._enemy_copy_ability_policy = None
    assert not rules.cabbage_missile_is_progression(world)


def test_public_evidence_source_setup_and_target_contract():
    evidence = json.loads(EVIDENCE.read_text())
    assert evidence['private_acceptance_sha256'] == 'bdedb0129195e13436670fe4ec14c12f1d5ffd607163e9010ef9f1102bc1f22e'
    assert evidence['private_review_hashes_sha256'] == (
        'c811ff2c5c64ce45092dffda5045fde737cb1e62cc45cef1c658cc66797f3238')
    raw = evidence['source_policy']
    assert evidence['generation_seed'] == 5 and raw['seed'] == 2089474284528698192
    assert raw['mode'] == 1 and raw['mapping_style'] == 'per_enemy_type'
    assert set(raw['allowed_abilities']) == set(ABILITY_NAME_TO_ID) - {'Normal', 'Master', 'Wait'}
    assert build_enemy_copy_runtime_patch_writes(raw)[0x3517FE] == 25
    assert int.from_bytes(build_enemy_source_runtime_config(raw)[4:8], 'little') & (1 << 18)
    assert SourcePolicy(raw).grant('WADDLE_DOO', lambda _: True).guaranteed == frozenset({'Missile'})
    assert evidence['source']['template'] == '0x088CA04C' and evidence['source']['native_xy'] == [528, 264]
    assert evidence['target']['location'] == CHEST and evidence['target']['location_id'] == 3960511
    assert KirbyAmClient()._build_minor_chest_source_ptr_map()[0x8CA0B8] == 3960511
    setup = evidence['setup']
    assert setup['native_gating'] == setup['native_area_keys'] == 0
    assert setup['later_harness_writes'] == setup['state_restores'] == 0
    assert len(setup['fixture_byte_diff']) == 15
    assert len(setup['client_config_writes']) == 8
    assert all(w['frame'] == 1085 and w['size'] == 4 and not w['guard_failed']
               and w['origin'] == 'KirbyAmClient._sync_enemy_copy_ability_runtime_config'
               for w in setup['client_config_writes'])
    seed = raw['seed']
    expected = {0x0203B064: 1, 0x0203B068: seed & 0xFFFFFFFF, 0x0203B06C: seed >> 32,
                0x0203B070: 0, 0x0203B074: sum(1 << ABILITY_NAME_TO_ID[n] for n in raw['allowed_abilities']),
                0x0203B0B0: 0, 0x0203B0B4: 0, 0x0203B078: 0}
    assert {int(w['address'], 16): int.from_bytes(bytes.fromhex(w['value']), 'little')
            for w in setup['client_config_writes']} == expected


def test_four_complete_positives_and_bounded_no_attack_controls():
    evidence = json.loads(EVIDENCE.read_text())
    runs = evidence['runs']
    assert len(runs) == 8
    positives = [r for r in runs.values() if r['positive']]
    assert {(r['hp'], r['enemy_health']) for r in positives} == {(1, 100), (6, 100), (1, 500), (6, 500)}
    assert len({r['input_sha256'] for r in positives}) == 1
    for name, run in runs.items():
        assert run['hp_min'] == run['hp_max'] == run['hp']
        assert run['helper_rooms'] == [[101, 101, 101]]
        assert run['source']['hp'] == (4 if run['enemy_health'] == 100 else 20)
        assert int(run['source']['template'], 16) == 0x088CA04C
        assert run['source']['type'] == 18 and run['source']['copy'] == 7
        assert run['acquisition_frame'] == 1939 and run['abilities_after_acquisition'] == [25]
        assert run['final']['ability'] == 25 and run['client']['server_submission'] is False
        if run['positive']:
            assert run['frames'] == 5123 and run['health_samples'] == 4039
            assert (run['f1_frame'], run['f2_frame'], run['chest_frame']) == (3771, 3801, 4885)
            assert run['final']['chest57'] and run['final']['event_counter'] == 1
            assert run['final']['target_f1'] == 0 and run['final']['linked_f2'] == [0] * 7
            assert run['client']['messages'] == [{'cmd': 'LocationChecks', 'locations': [3960511]}]
            blast, chain = run['target_blast'], run['chain']
            assert blast['frame'] == 3771 and int(blast['task_fn'], 16) == 0x08074745
            assert int(blast['parent'], 16) == 0x02020EE0 and blast['scan_box'] == [-24, -24, 24, 24]
            assert [blast['x'], blast['y']] == [201.99609375, 88.99609375]
            assert int(chain['task_fn'], 16) == 0x0800E27D and chain['parent'] == blast['object']
            assert [chain['x'], chain['y']] == [232, 120]
            control = runs[name.replace('final', 'window').replace('positive', 'control')]
            assert control['rom_sha256'] == run['rom_sha256']
        else:
            assert run['frames'] == 3813 and run['health_samples'] == 2729
            assert run['f1_frame'] is run['f2_frame'] is run['chest_frame'] is None
            assert run['target_blast'] is run['chain'] is None
            assert run['final']['target_f1'] == 241 and run['final']['linked_f2'] == [242] * 7
            assert not run['final']['chest57'] and run['final']['event_counter'] == 0
            assert not run['client']['messages']
    control = evidence['control']
    assert control['common_state_through'] == 3742 and control['cutoff_frame'] == 3813
    assert control['only_input_change'] == {
        'positive': {'start': 3742, 'frames': 1, 'keys': 2},
        'control': {'start': 3742, 'frames': 1, 'keys': 0}}
    excluded = evidence['excluded_later_controls']
    assert len(excluded) == 4 and all(r['hp_min'] == 0 and r['frames'] == 5123 for r in excluded.values())


def test_exact_blast_medium_retention_and_neutral_direction_negative():
    from ..traversal import CAPABILITY_CONSUMED_ABILITIES

    evidence = json.loads(EVIDENCE.read_text())
    attack = evidence['attack']
    assert attack['tile_scan_box'] == [-24, -24, 24, 24]
    assert attack['later_damage_box'] == [-30, -30, 30, 30]
    assert attack['integer_scan_extreme'] == [225, 112]
    assert attack['inputs'] == [{'start': 3742, 'frames': 1, 'keys': 2},
                                {'start': 3743, 'frames': 70, 'keys': 144}]
    assert attack['ability_retained'] == 25
    assert 'bomb_517_missile_blast' not in CAPABILITY_CONSUMED_ABILITIES
    neutral = evidence['neutral_control']
    assert neutral['cutoff'] == 3813 and neutral['hp_min'] == neutral['hp_max'] == 1
    assert neutral['first_blast']['y'] == 77.60546875
    assert neutral['first_blast']['scan_box'] == [-24, -24, 24, 24]
    assert neutral['target_f1'] == 241 and neutral['linked_f2'] == [242] * 7
    assert not neutral['chest57'] and not neutral['client']['messages']
    owners = [(r['id'], key) for r in room_traversal_targets('block') for key, g in r['graphs'].items()
              if any(route.get('capability') == 'bomb_517_missile_blast' for route in g['routes'])]
    assert owners == [(TARGET, 'hub2_missile_entry')]
