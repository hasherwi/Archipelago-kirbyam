"""Bounded Cabbage Smash carry, source policy, and actual-world chest binding."""

import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from BaseClasses import CollectionState, ItemClassification
from test.general import setup_multiworld

from .. import KirbyAmWorld, traversal_rules as rules
from ..data import data
from ..traversal import Grant, SourcePolicy
from ..traversal_data import load_room_traversal, room_traversal_graph, room_traversal_targets
from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive
from .test_traversal import policy
from .test_mini_traversal import make_world

OWNER = 'REGION_CABBAGE_CAVERN/ROOM_3_06'
UPSTREAM = 'REGION_CABBAGE_CAVERN/ROOM_3_HUB_2'
TARGET = 'bomb_517_chocolate'
CHEST = 'MINOR_CHEST_SPRAY_PAINT_12'
EVIDENCE = Path(__file__).parents[1] / 'dev-docs' / 'cabbage-smash-source-runtime.json'


def cabbage_row():
    return next(row for row in room_traversal_targets('block') if row['id'] == TARGET)


@pytest.mark.parametrize('mode,pool,weight,applies', [
    (0, None, 0, True), (1, ['Beam'], 0, True), (1, ['Smash'], 0, True),
    (1, ['Spark'], 0, False), (1, ['Ice'], 0, False),
    (2, ['Beam'], 0, True), (2, ['Smash'], 0, True),
    (2, ['Beam', 'Smash'], 0, False), (2, ['Smash', 'Spark'], 0, False),
    (2, ['Smash'], 50, False), (2, ['Smash'], 100, False),
    (2, None, 0, False),
])
@pytest.mark.parametrize('statues', [False, True])
def test_only_guaranteed_singleton_beam_or_smash_applies(mode, pool, weight, applies, statues):
    resolver = policy(mode, pool=pool, weight=weight, statues=statues)
    row = cabbage_row()
    assert rules.target_applies(row, resolver) is applies
    # Existing Beam witness and new Smash witness are alternatives, not AND gates.
    if applies:
        ability, = resolver.grant('WADDLE_DOO', lambda _: True).guaranteed
        results = [rules.graph_succeeds(graph, resolver, frozenset({f'{ability} Ability'}), True,
                                        retries=False) for graph in rules.target_graphs(row, False)]
        assert results == ([True, False] if ability == 'Beam' else [False, True])
    # Same source key does not extend Carrot's independently proved Beam carry.
    carrot = next(row for row in room_traversal_targets('block') if row['id'] == 'bomb_719_room13')
    assert rules.target_applies(carrot, resolver) is (
        resolver.grant('WADDLE_DOO', lambda _: True).guaranteed == frozenset({'Beam'}))


@pytest.mark.parametrize('grant', [
    Grant(frozenset()), Grant(frozenset({'Normal'})), Grant(frozenset({'Unknown'})),
    Grant(frozenset({'Beam', 'Smash'}), randomized=True),
    Grant(frozenset({'Smash'}), randomized=True, can_fail=True),
])
def test_unknown_or_uncertain_grants_do_not_install_gate(grant):
    assert not rules.target_applies(cabbage_row(), SimpleNamespace(grant=lambda *args: grant))


@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('area_keys', [False, True])
def test_smash_graph_requires_finite_actual_source_not_inventory(gating, area_keys):
    graph = room_traversal_graph(TARGET, 'hub2_smash_entry', area_keys)
    resolver = SourcePolicy(json.loads(EVIDENCE.read_text())['source_policy'])
    assert graph.access_region == UPSTREAM
    assert all(start.equipped == 'Normal' for start in graph.starts)
    assert [(node.key.rsplit(':', 1)[-1], node.room) for node in graph.nodes] == [
        ('hub2', 591), ('arrival', 517), ('source', 517), ('chest', 517)]
    source, = graph.placements
    assert (source.identity, source.source_key, source.renewable, source.retry_evidence) == (
        '0x088CA04C', 'WADDLE_DOO', False, None)
    assert graph.routes[-1].allowed_abilities == frozenset({'Smash'})
    assert all(not route.items and not route.recover_dropped_ability for route in graph.routes)
    assert [route.resets_room_instance for route in graph.routes] == [True, False, False]
    assert graph.required_targets == frozenset({TARGET + ':chest'})
    chest, = graph.required_targets
    owned = frozenset({'Smash Ability'})
    assert graph.evaluate(resolver, frozenset(), gating).reaches(chest) is (not gating)
    assert graph.evaluate(resolver, owned, gating).reaches(chest)
    assert not replace(graph, placements=()).evaluate(resolver, owned, gating).reaches(chest)
    behind_gate = replace(graph, placements=(replace(source, node=chest),))
    assert not behind_gate.evaluate(resolver, owned, gating).reaches(chest)
    for ability in ('Beam', 'Spark', 'Ice'):
        assert not graph.evaluate(policy(1, pool=[ability]), owned, gating).reaches(chest)
    # A finite source never gains an eventual-draw promise from retry mode.
    for uncertain in (policy(2, pool=['Beam', 'Smash']), policy(2, pool=['Smash'], weight=50)):
        assert not graph.evaluate(uncertain, owned, gating, allow_documented_retries=True).reaches(chest)


@pytest.mark.parametrize('update', [
    {'id': 'bomb_719_room13'}, {'kind': 'switch'}, {'native_room': 719},
    {'region': 'REGION_CARROT_CASTLE/ROOM_5_07'}, {'location': 'MINOR_CHEST_MUSIC_NOTE_10'},
    {'requires_guaranteed_source': {'source_key': 'UNKNOWN_SOURCE', 'abilities': ['Beam', 'Smash']}},
    {'requires_guaranteed_source': {'source_key': 'WADDLE_DOO', 'abilities': ['Beam', 'Smash', 'Ice']}},
    {'requires_guaranteed_source': {'source_key': 'WADDLE_DOO', 'abilities': ['Smash']}},
])
def test_smash_applicability_schema_cannot_spread_to_other_targets(update):
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
def test_actual_world_only_chocolate_chest_uses_smash_permission(
        monkeypatch, gating, area_keys, statues, room_sanity, minor_chests):
    monkeypatch.setattr(KirbyAmWorld, 'ENABLE_MINOR_CHESTS', minor_chests)
    # The complete production policy is fixed while changing option wiring.
    # Minimal accessibility avoids unrelated statue-source feasibility for these
    # option fixtures; full accessibility is tested by the real generation below.
    raw = json.loads(EVIDENCE.read_text())['source_policy']
    monkeypatch.setattr('worlds.kirbyam.build_enemy_copy_ability_policy', lambda *args, **kwargs: raw)
    multiworld = setup_multiworld(KirbyAmWorld, steps=('generate_early',), seed=173, options={
        'ability_randomization_mode': 1, 'ability_gating': gating, 'area_keys': area_keys,
        'ability_randomization_statues': statues, 'room_sanity': room_sanity,
        'ability_randomization_no_ability_weight': 0, 'accessibility': 'minimal',
    })
    world = multiworld.worlds[1]
    world.create_regions()
    world.set_rules()
    state = CollectionState(multiworld)
    state.can_reach_region = lambda name, player: name == OWNER
    if minor_chests:
        target = multiworld.get_location(data.locations[CHEST].label, 1)
        assert target.address == 3960511 and target.parent_region.name == OWNER
        assert not target.access_rule(state)
        state.collect(world.create_item('Smash Ability'), prevent_sweep=True)
        assert not target.access_rule(state)  # Inventory cannot supply independent entry.
        state.remove(world.create_item('Smash Ability'))
        state.can_reach_region = lambda name, player: name == UPSTREAM
        assert target.access_rule(state) is (not gating)
        state.collect(world.create_item('Beam Ability'), prevent_sweep=True)
        assert target.access_rule(state) is (not gating)  # Source grants Smash, not Beam.
        state.collect(world.create_item('Smash Ability'), prevent_sweep=True)
        assert target.access_rule(state)
        state.remove(world.create_item('Smash Ability'))
        assert target.access_rule(state) is (not gating)
    else:
        with pytest.raises(KeyError):
            multiworld.get_location(data.locations[CHEST].label, 1)
    assert world.create_item('Smash Ability').classification == ItemClassification.progression
    assert world.create_item('Beam Ability').classification == ItemClassification.useful
    # Neither item ownership nor the chest's independent Hub2 entry changes
    # unrelated exits, the RoomSanity check, or the Area Key on outer area access.
    state.can_reach_region = lambda name, player: name == OWNER
    for entrance in multiworld.get_region(OWNER, 1).exits:
        assert entrance.access_rule(state)
    room_checks = [location for location in multiworld.get_region(OWNER, 1).locations
                   if location.address != 3960511]
    assert len(room_checks) == room_sanity
    assert all(location.access_rule(state) for location in room_checks)
    area = multiworld.get_entrance(
        'REGION_RAINBOW_ROUTE/ROOM_1_13_LOWER -> REGION_CABBAGE_CAVERN/ROOM_3_04', 1)
    assert area.access_rule(state) is (not area_keys)
    state.collect(world.create_item('Cabbage Cavern - Area Key'), prevent_sweep=True)
    assert area.access_rule(state)


@pytest.mark.parametrize('gating', [0, 1])
@pytest.mark.parametrize('area_keys', [0, 1])
def test_full_generation_seed173_keeps_production_smash_assignment(tmp_path, monkeypatch, gating, area_keys):
    import Main

    generated = []
    main = Main.main

    def capture_world(*args, **kwargs):
        multiworld = main(*args, **kwargs)
        generated.append(multiworld)
        return multiworld

    monkeypatch.setattr(Main, 'main', capture_world)
    player = tmp_path / 'player.yaml'
    player.write_text(
        'name: Cabbage\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n'
        f'  ability_randomization_mode: 1\n  ability_gating: {gating}\n  area_keys: {area_keys}\n'
        '  ability_randomization_no_ability_weight: 0\n  minimum_health: 1\n  maximum_health: 1\n'
        '  accessibility: full\n', encoding='utf-8')
    archive = generate_archive_from_fixture(player, tmp_path / 'out', seed=173)
    decoded = load_multidata_from_archive(archive)
    raw = decoded['slot_data'][1]['enemy_copy_ability_policy']
    assert {**raw, 'allowed_abilities': list(raw['allowed_abilities'])} == (
        json.loads(EVIDENCE.read_text())['source_policy'])
    assert SourcePolicy(raw).grant('WADDLE_DOO', lambda _: True).guaranteed == frozenset({'Smash'})
    assert 3960511 in decoded['locations'][1]
    assert decoded['locations'][1][3960511]  # Actual filled optional check, not an unbound graph.
    multiworld, = generated
    assert not multiworld.get_unfilled_locations()
    assert multiworld.can_beat_game()
    assert multiworld.fulfills_accessibility()
    world = multiworld.worlds[1]
    state = CollectionState(multiworld)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    target = multiworld.get_location(data.locations[CHEST].label, 1)
    assert target.access_rule(state) is (not gating)
    state.collect(world.create_item('Smash Ability'), prevent_sweep=True)
    assert target.access_rule(state)


@pytest.mark.parametrize('mode,pool,weight,applies', [
    (0, None, 0, True), (1, ['Smash'], 0, True), (1, ['Beam'], 0, True),
    (1, ['Spark'], 0, False), (1, ['Ice'], 0, False),
    (2, ['Smash'], 0, True), (2, ['Beam', 'Smash'], 0, False),
    (2, ['Smash'], 50, False), (2, ['Smash'], 100, False), (2, None, 0, False),
])
@pytest.mark.parametrize('gating', [0, 1])
def test_actual_world_policy_applicability_preserves_unproved_assignments(
        monkeypatch, mode, pool, weight, applies, gating):
    resolver = policy(mode, pool=pool, weight=weight, minny=False)
    # Restricted pools are rule-layer fixtures, not successful full generations.
    # Minimal accessibility skips unrelated source feasibility, not access rules.
    monkeypatch.setattr('worlds.kirbyam.build_enemy_copy_ability_policy', lambda *args, **kwargs: resolver.policy)
    world = make_world(mode, gating, accessibility='minimal', ability_randomization_no_ability_weight=weight)
    chest = world.multiworld.get_location(data.locations[CHEST].label, 1)
    state = CollectionState(world.multiworld)
    state.can_reach_region = lambda name, player: name == OWNER
    assert chest.access_rule(state) is (not applies)
    for ability in ('Beam', 'Smash'):
        state.collect(world.create_item(f'{ability} Ability'), prevent_sweep=True)
    assert chest.access_rule(state) is (not applies)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    assert chest.access_rule(state)
    state.remove(world.create_item('Smash Ability'))
    requires_smash = resolver.grant('WADDLE_DOO', lambda _: True).guaranteed == frozenset({'Smash'})
    assert chest.access_rule(state) is (not (applies and requires_smash and gating))
