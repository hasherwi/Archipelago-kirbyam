"""Finite Fire carry and neutral traveling breath only for the Chocolate chest."""

import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest
from BaseClasses import CollectionState, ItemClassification

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
EVIDENCE = Path(__file__).parents[1] / 'dev-docs/cabbage-fire-acceptance.json'
POLICIES = [
    (0, None, 0, 'Beam'), (1, ['Beam'], 0, 'Beam'), (1, ['Smash'], 0, 'Smash'),
    (1, ['Fire'], 0, 'Fire'), (1, ['Spark'], 0, 'Spark'), (1, ['Ice'], 0, 'Ice'),
    (2, ['Fire'], 0, 'Fire'), (2, ['Fire', 'Smash'], 0, None),
    (2, ['Fire', 'Ice'], 0, None), (2, ['Fire'], 50, None), (2, ['Fire'], 100, None),
    (2, None, 0, None),
]


def cabbage_row():
    return next(row for row in room_traversal_targets('block') if row['id'] == TARGET)


@pytest.mark.parametrize('mode,pool,weight,ability', POLICIES)
@pytest.mark.parametrize('statues', [False, True])
def test_independent_beam_smash_fire_or_policy(mode, pool, weight, ability, statues):
    resolver = policy(mode, pool=pool, weight=weight, statues=statues)
    row = cabbage_row()
    assert rules.target_applies(row, resolver) is (ability is not None)
    if ability:
        results = [rules.graph_succeeds(g, resolver, frozenset({f'{ability} Ability'}), True, retries=False)
                   for g in rules.target_graphs(row, False)]
        assert results == [ability == name for name in ('Beam', 'Smash', 'Fire', 'Missile', 'Parasol', 'Spark', 'Ice')]
    # Carrot now has its own reviewed Fire graph, not a reuse of the517 effect.
    carrot = next(r for r in room_traversal_targets('block') if r['id'] == 'bomb_719_room13')
    if ability == 'Fire':
        assert rules.target_applies(carrot, resolver)
        graph = room_traversal_graph('bomb_719_room13', 'room5_fire_entry')
        assert graph.routes[-1].capability == 'bomb_719_fire_breath'
        assert graph.routes[-1].capability != room_traversal_graph(TARGET, 'hub2_fire_entry').routes[-1].capability


@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('area_keys', [False, True])
def test_finite_source_permission_and_actual_equipment(gating, area_keys):
    graph = room_traversal_graph(TARGET, 'hub2_fire_entry', area_keys)
    resolver = SourcePolicy(json.loads(EVIDENCE.read_text())['source_policy'])
    assert graph.access_region == UPSTREAM
    assert graph.required_guaranteed_source == ('WADDLE_DOO', 'Fire')
    assert all(start.equipped == 'Normal' for start in graph.starts)
    assert [(n.key.rsplit(':', 1)[-1], n.room) for n in graph.nodes] == [
        ('hub2', 591), ('arrival', 517), ('source', 517), ('chest', 517)]
    source, = graph.placements
    assert (source.identity, source.source_key, source.renewable, source.retry_evidence) == (
        '0x088CA04C', 'WADDLE_DOO', False, None)
    assert [r.resets_room_instance for r in graph.routes] == [True, False, False]
    assert all(not r.items and not r.opens and not r.recover_dropped_ability for r in graph.routes)
    assert graph.routes[-1].capability == 'bomb_517_fire_breath'
    assert graph.routes[-1].allowed_abilities == frozenset({'Fire'})
    chest, = graph.required_targets
    owned = frozenset({'Fire Ability'})
    result = graph.evaluate(resolver, owned, gating, allow_documented_retries=True)
    assert result.reaches(chest) and not result.retry_assumptions
    arrivals = [p for p in result.positions if p.node == chest]
    assert any(p.equipped == 'Fire' for p in arrivals)
    assert all(p.equipped in {'Fire', 'Normal'} and source.identity in p.consumed for p in arrivals)
    assert graph.evaluate(resolver, frozenset(), gating).reaches(chest) is (not gating)
    assert not replace(graph, placements=()).evaluate(resolver, owned, gating).reaches(chest)
    assert not replace(graph, placements=(replace(source, node=chest),)).evaluate(
        resolver, owned, gating).reaches(chest)
    spent = replace(graph, starts=(Position(source.node, 'Normal', consumed=frozenset({source.identity})),))
    assert not spent.evaluate(resolver, owned, gating).reaches(chest)
    for ability in ('Beam', 'Smash', 'Spark', 'Ice', 'Missile'):
        assert not graph.evaluate(policy(1, pool=[ability]), owned, gating).reaches(chest)


@pytest.mark.parametrize('pool,weight', [
    (['Fire', 'Smash'], 0), (['Fire', 'Ice'], 0), (['Fire', 'Missile'], 0), (['Fire'], 50), (['Fire'], 100),
])
@pytest.mark.parametrize('owned', [frozenset(), frozenset({'Fire Ability'}),
                                   frozenset({'Fire Ability', 'Smash Ability', 'Ice Ability', 'Missile Ability'})])
@pytest.mark.parametrize('gating', [False, True])
def test_raw_policy_guard_prevents_permission_narrowing(pool, weight, owned, gating):
    graph = room_traversal_graph(TARGET, 'hub2_fire_entry')
    resolver = policy(2, pool=pool, weight=weight)
    assert not graph.evaluate(resolver, owned, gating, allow_documented_retries=True).positions


@pytest.mark.parametrize('update', [
    {'id': 'bomb_719_room13'}, {'kind': 'switch'}, {'native_room': 719},
    {'region': 'REGION_CARROT_CASTLE/ROOM_5_07'}, {'location': 'MINOR_CHEST_MUSIC_NOTE_10'},
    {'requires_guaranteed_source': {'source_key': 'HOT_HEAD', 'abilities': ['Beam', 'Smash', 'Fire']}},
    {'requires_guaranteed_source': {'source_key': 'WADDLE_DOO', 'abilities': ['Fire']}},
    {'requires_guaranteed_source': {'source_key': 'WADDLE_DOO', 'abilities': ['Beam', 'Smash', 'Fire', 'Ice']}},
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
    monkeypatch.setattr('worlds.kirbyam.build_enemy_copy_ability_policy', lambda *args, **kwargs: raw)
    world = make_world(1, gating, accessibility='minimal', area_keys=area_keys,
                       ability_randomization_statues=statues, room_sanity=room_sanity,
                       ability_randomization_no_ability_weight=0)
    state = CollectionState(world.multiworld)
    state.can_reach_region = lambda name, player: name == OWNER
    item = world.create_item('Fire Ability')
    assert 'Fire' in GATEABLE_ENEMY_COPY_ABILITIES
    assert item.classification == ItemClassification.progression
    if minor_chests:
        chest = world.multiworld.get_location(data.locations[CHEST].label, 1)
        assert chest.address == 3960511 and chest.parent_region.name == OWNER
        assert not chest.access_rule(state)
        state.collect(item, prevent_sweep=True)
        assert not chest.access_rule(state)  # Permission does not supply Hub2 access.
        state.remove(item)
        state.can_reach_region = lambda name, player: name == UPSTREAM
        assert chest.access_rule(state) is (not gating)
        for wrong in ('Beam Ability', 'Smash Ability'):
            state.collect(world.create_item(wrong), prevent_sweep=True)
        assert chest.access_rule(state) is (not gating)
        state.collect(item, prevent_sweep=True)
        assert state.has('Fire Ability', 1) and chest.access_rule(state)
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
    monkeypatch.setattr('worlds.kirbyam.build_enemy_copy_ability_policy', lambda *args, **kwargs: resolver.policy)
    world = make_world(mode, gating, accessibility='minimal', ability_randomization_no_ability_weight=weight)
    chest = world.multiworld.get_location(data.locations[CHEST].label, 1)
    state = CollectionState(world.multiworld)
    state.can_reach_region = lambda name, player: name == OWNER
    assert chest.access_rule(state) is (ability is None)
    for name in ('Beam', 'Smash', 'Fire', 'Spark', 'Ice'):
        state.collect(world.create_item(f'{name} Ability'), prevent_sweep=True)
    assert chest.access_rule(state) is (ability is None)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    assert chest.access_rule(state)
    state.remove(world.create_item('Fire Ability'))
    assert chest.access_rule(state) is (not (ability == 'Fire' and gating))


@pytest.mark.parametrize('gating,area_keys,health', [(0, 0, 100), (1, 0, 100), (0, 1, 500), (1, 1, 500)])
def test_full_seed18_fill_uses_actual_policy_and_progression(tmp_path, monkeypatch, gating, area_keys, health):
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
        'name: Fire517\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n'
        '  ability_randomization_mode: 1\n  ability_randomization_no_ability_weight: 0\n'
        f'  ability_gating: {gating}\n  area_keys: {area_keys}\n  enemy_health_multiplier: {health}\n'
        '  minimum_health: 1\n  maximum_health: 1\n  accessibility: full\n', encoding='utf-8')
    archive = generate_archive_from_fixture(player, tmp_path / 'out', seed=18)
    decoded = load_multidata_from_archive(archive)
    raw = decoded['slot_data'][1]['enemy_copy_ability_policy']
    assert {**raw, 'allowed_abilities': list(raw['allowed_abilities'])} == (
        json.loads(EVIDENCE.read_text())['source_policy'])
    assert SourcePolicy(raw).grant('WADDLE_DOO', lambda _: True).guaranteed == frozenset({'Fire'})
    assert decoded['locations'][1][3960511]
    multiworld, = generated
    assert not multiworld.get_unfilled_locations()
    assert multiworld.can_beat_game() and multiworld.fulfills_accessibility()
    world = multiworld.worlds[1]
    state = CollectionState(multiworld)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    chest = multiworld.get_location(data.locations[CHEST].label, 1)
    assert chest.access_rule(state) is (not gating)
    state.collect(world.create_item('Fire Ability'), prevent_sweep=True)
    assert chest.access_rule(state)


def test_public_evidence_source_and_exact_target_contract():
    evidence = json.loads(EVIDENCE.read_text())
    assert evidence['private_manifest_sha256'] == '00de8748d04e3f678f5282cbde26bc8b15370efe549cae80b67f6e6c4c5f9bde'
    raw = evidence['source_policy']
    assert evidence['generation_seed'] == 18 and raw['seed'] == 2395008880317811979
    assert raw['mode'] == 1 and raw['mapping_style'] == 'per_enemy_type'
    assert set(raw['allowed_abilities']) == set(ABILITY_NAME_TO_ID) - {'Normal', 'Master', 'Wait'}
    assert build_enemy_copy_runtime_patch_writes(raw)[0x3517FE] == 1
    assert int.from_bytes(build_enemy_source_runtime_config(raw)[4:8], 'little') & (1 << 18)
    assert SourcePolicy(raw).grant('WADDLE_DOO', lambda _: True).guaranteed == frozenset({'Fire'})
    assert evidence['source']['template'] == '0x088CA04C'
    assert evidence['source']['native_xy'] == [528, 264]
    assert evidence['target']['location'] == CHEST and evidence['target']['location_id'] == 3960511
    assert KirbyAmClient()._build_minor_chest_source_ptr_map()[0x8CA0B8] == 3960511
    assert evidence['target']['f1'] == [14, 7] and evidence['target']['chest'] == 57
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


def test_public_evidence_four_positive_and_four_matched_controls():
    evidence = json.loads(EVIDENCE.read_text())
    runs = evidence['runs']
    assert len(runs) == 8
    positives = [r for r in runs.values() if r['positive']]
    assert {(r['hp'], r['enemy_health']) for r in positives} == {(1, 100), (6, 100), (1, 500), (6, 500)}
    assert len({r['input_sha256'] for r in positives}) == 1
    delta = evidence['control_input_difference']
    assert delta['positive'] == {'start': 3326, 'frames': 30, 'keys': 2}
    assert delta['control'] == {'start': 3326, 'frames': 30, 'keys': 0} and delta['otherwise_identical']
    for name, run in runs.items():
        assert run['hp_min'] == run['hp_max'] == run['hp']
        assert run['hp_samples'] == 3406 and run['helper_rooms'] == [101, 101, 101]
        assert run['acquisition']['frame'] == 1939 and run['acquisition']['ability'] == 1
        assert run['final']['frame'] == 4490 and run['final']['ability'] == 1
        assert run['final']['spray11'] is False
        if run['positive']:
            assert run['first_packet_hit']['frame'] == 3341
            assert int(run['first_packet_hit']['fn'], 16) == 0x080737D9
            assert int(run['first_packet_hit']['parent'], 16) == 0x02020EE0
            assert int(run['first_packet_hit']['flags'], 16) == 0xA0084100
            assert run['chest_open_frame'] == 4252 and run['final']['chest57']
            assert run['final']['target_f1'] == 0 and run['final']['linked_f2'] == [0] * 7
            assert run['final']['minor_event_counter'] == 1 and int(run['event_ring'][0], 16) == 0x088CA0B8
            assert run['client_messages'] == [{'cmd': 'LocationChecks', 'locations': [3960511]}]
            control = runs[name.replace('positive', 'control')]
            assert control['rom_sha256'] == run['rom_sha256']
        else:
            assert run['first_packet_hit'] is None and run['chest_open_frame'] is None
            assert run['final']['target_f1'] == 241 and run['final']['linked_f2'] == [242] * 7
            assert not run['final']['chest57'] and run['final']['minor_event_counter'] == 0
            assert not run['client_messages'] and all(int(x, 16) == 0 for x in run['event_ring'])
    owners = [(r['id'], key) for r in room_traversal_targets('block') for key, g in r['graphs'].items()
              if any(route.get('capability') == 'bomb_517_fire_breath' for route in g['routes'])]
    assert owners == [(TARGET, 'hub2_fire_entry')]
