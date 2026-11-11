"""Finite Doo-to-Sword acquisition and ordinary first slash for Chocolate only."""

from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path

import pytest
from BaseClasses import CollectionState, ItemClassification

from .support.source_policy import set_rule_test_policy
from .. import KirbyAmWorld, traversal_rules as rules
from ..data import data
from ..traversal import CAPABILITY_ABILITIES, CAPABILITY_CONSUMED_ABILITIES, Position, SourcePolicy
from ..traversal_data import room_traversal_graph, room_traversal_targets
from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive
from .test_cabbage_parasol import CHEST, OWNER, TARGET, UPSTREAM, cabbage_row
from .test_mini_traversal import make_world
from .test_traversal import policy

ROOT = Path(__file__).parents[1]
EVIDENCE = ROOT / 'dev-docs/cabbage-sword-acceptance.json'
CAPABILITY = 'bomb_517_sword_first_slash'


def document():
    return json.loads(EVIDENCE.read_text())


@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('area_keys', [False, True])
def test_finite_source_and_own_capability(gating, area_keys):
    graph = room_traversal_graph(TARGET, 'hub2_sword_entry', area_keys)
    resolver = SourcePolicy(document()['source_policy'])
    assert graph.access_region == UPSTREAM and graph.required_guaranteed_source == ('WADDLE_DOO', 'Sword')
    assert all(start.equipped == 'Normal' for start in graph.starts)
    assert [node.room for node in graph.nodes] == [591, 517, 517, 517]
    source, = graph.placements
    assert (source.identity, source.source_key, source.renewable, source.retry_evidence) == (
        '0x088CA04C', 'WADDLE_DOO', False, None)
    assert [route.resets_room_instance for route in graph.routes] == [True, False, False]
    assert all(not route.items and not route.opens and not route.recover_dropped_ability for route in graph.routes)
    assert graph.routes[-1].capability == CAPABILITY
    assert graph.routes[-1].allowed_abilities == CAPABILITY_ABILITIES[CAPABILITY] == frozenset({'Sword'})
    assert CAPABILITY not in CAPABILITY_CONSUMED_ABILITIES
    chest, = graph.required_targets
    owned = frozenset({'Sword Ability'})
    result = graph.evaluate(resolver, owned, gating, allow_documented_retries=True)
    assert result.reaches(chest) and not result.retry_assumptions
    assert any(p.equipped == 'Sword' and source.identity in p.consumed for p in result.positions if p.node == chest)
    assert graph.evaluate(resolver, frozenset(), gating).reaches(chest) is (not gating)
    assert not replace(graph, placements=()).evaluate(resolver, owned, gating).reaches(chest)
    assert not replace(graph, placements=(replace(source, node=chest),)).evaluate(
        resolver, owned, gating).reaches(chest)
    spent = replace(graph, starts=(Position(source.node, 'Normal', consumed=frozenset({source.identity})),))
    assert not spent.evaluate(resolver, owned, gating).reaches(chest)
    for ability in ('Beam', 'Smash', 'Fire', 'Missile', 'Parasol', 'Spark', 'Ice', 'Fighter'):
        assert not graph.evaluate(policy(1, pool=[ability]), owned, gating).positions


@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('pool,weight', [(['Sword', 'Beam'], 0), (['Sword'], 50), (['Sword'], 100), (None, 0)])
def test_uncertain_raw_policy_is_not_narrowed_by_permission(gating, pool, weight):
    resolver = policy(2, pool=pool, weight=weight)
    assert not rules.target_applies(cabbage_row(), resolver)
    graph = room_traversal_graph(TARGET, 'hub2_sword_entry')
    for owned in (frozenset(), frozenset({'Sword Ability'}), frozenset({'Sword Ability', 'Beam Ability'})):
        assert not graph.evaluate(resolver, owned, gating, allow_documented_retries=True).positions


@pytest.mark.parametrize('mode', [1, 2])
def test_excluded_source_retains_native_beam(mode):
    resolver = policy(mode, pool=['Sword'])
    resolver.writes.pop(0x3517FE, None)
    bitmap = bytearray(resolver.source_config)
    bitmap[4:8] = (int.from_bytes(bitmap[4:8], 'little') & ~(1 << 18)).to_bytes(4, 'little')
    resolver.source_config = bytes(bitmap)
    assert resolver.grant('WADDLE_DOO', lambda _: True).guaranteed == frozenset({'Beam'})
    assert not room_traversal_graph(TARGET, 'hub2_sword_entry').evaluate(
        resolver, frozenset({'Sword Ability'}), True).positions


@pytest.mark.parametrize('gating', [0, 1])
@pytest.mark.parametrize('area_keys', [0, 1])
@pytest.mark.parametrize('statues', [0, 1])
@pytest.mark.parametrize('room_sanity', [0, 1])
@pytest.mark.parametrize('minor_chests', [False, True])
def test_actual_world_scope_and_existing_progression(
        monkeypatch, gating, area_keys, statues, room_sanity, minor_chests):
    raw = document()['source_policy']
    monkeypatch.setattr(KirbyAmWorld, 'ENABLE_MINOR_CHESTS', minor_chests)
    set_rule_test_policy(monkeypatch, lambda *args, **kwargs: raw)
    world = make_world(1, gating, accessibility='minimal', area_keys=area_keys,
                       ability_randomization_statues=statues, room_sanity=room_sanity)
    state = CollectionState(world.multiworld)
    item = world.create_item('Sword Ability')
    # Sword already has an independent progression classification; no new factory reason is needed.
    assert item.classification == ItemClassification.progression
    if minor_chests:
        chest = world.multiworld.get_location(data.locations[CHEST].label, 1)
        assert chest.address == 3960511 and chest.parent_region.name == OWNER
        state.can_reach_region = lambda name, player: name == OWNER
        state.collect(item, prevent_sweep=True)
        assert not chest.access_rule(state)
        state.remove(item)
        state.can_reach_region = lambda name, player: name == UPSTREAM
        assert chest.access_rule(state) is (not gating)
        state.collect(world.create_item('Missile Ability'), prevent_sweep=True)
        assert chest.access_rule(state) is (not gating)
        state.collect(item, prevent_sweep=True)
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
    assert len(room_checks) == room_sanity and all(loc.access_rule(state) for loc in room_checks)
    entrance = world.multiworld.get_entrance(
        'REGION_RAINBOW_ROUTE/ROOM_1_13_LOWER -> REGION_CABBAGE_CAVERN/ROOM_3_04', 1)
    assert entrance.access_rule(state) is (not area_keys)
    state.collect(world.create_item('Cabbage Cavern - Area Key'), prevent_sweep=True)
    assert entrance.access_rule(state)


@pytest.mark.parametrize('gating,area_keys,health,count', [
    (0, 0, 100, 0), (1, 0, 100, 0), (0, 1, 500, 0), (1, 1, 500, 0),
    (0, 0, 100, 3), (1, 0, 100, 1), (1, 1, 500, 3),
])
def test_full_seed4_fill_and_start_inventory(tmp_path, monkeypatch, gating, area_keys, health, count):
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
        'name: Sword517\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n'
        '  ability_randomization_mode: 1\n  ability_randomization_no_ability_weight: 0\n'
        f'  ability_gating: {gating}\n  area_keys: {area_keys}\n  enemy_health_multiplier: {health}\n'
        '  minimum_health: 1\n  maximum_health: 1\n  accessibility: full\n'
        + (f'  start_inventory:\n    Sword Ability: {count}\n' if count else ''), encoding='utf-8')
    archive = generate_archive_from_fixture(player, tmp_path / 'out', seed=4)
    decoded = load_multidata_from_archive(archive)
    raw = decoded['slot_data'][1]['enemy_copy_ability_policy']
    assert {**raw, 'allowed_abilities': list(raw['allowed_abilities'])} == document()['source_policy']
    assert SourcePolicy(raw).grant('WADDLE_DOO', lambda _: True).guaranteed == frozenset({'Sword'})
    assert decoded['locations'][1][3960511]
    assert decoded['precollected_items'][1].count(3860118) == count
    multiworld, = generated
    assert not multiworld.get_unfilled_locations()
    assert multiworld.can_beat_game() and multiworld.fulfills_accessibility()
    world = multiworld.worlds[1]
    assert all(item.classification == ItemClassification.progression
               for item in multiworld.precollected_items[1] if item.name == 'Sword Ability')
    assert multiworld.state.count('Sword Ability', 1) == count
    assert CollectionState(multiworld).count('Sword Ability', 1) == count
    state = CollectionState(multiworld)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    chest = multiworld.get_location(data.locations[CHEST].label, 1)
    assert chest.access_rule(state) is (not gating or bool(count))
    state.collect(world.create_item('Sword Ability'), prevent_sweep=True)
    assert chest.access_rule(state)


def test_prior_catalog_and_graphs_unchanged():
    doc = document()
    rooms = json.loads((ROOT / 'data/regions/rooms.json').read_text())
    row = rooms[OWNER]['traversal']['targets'][0]

    def digest(value):
        return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

    assert len(doc['prior_graphs_sha256']) == 7
    for name, expected in doc['prior_graphs_sha256'].items():
        assert digest(row['graphs'][name]) == expected
    stripped = deepcopy(rooms)
    target = stripped[OWNER]['traversal']['targets'][0]
    assert digest(target['graphs'].pop('hub2_ufo_entry')) == (
        '6ef3439b8a90da73387bdc7e9d4372baae9e889eb936c82508b5a0e74e15986a')
    target['requires_guaranteed_source']['abilities'].remove('UFO')
    # Fighter has its own later full-catalog preservation contract against the Sword checkpoint.
    target['graphs'].pop('hub2_fighter_entry')
    target['requires_guaranteed_source']['abilities'].remove('Fighter')
    target['graphs'].pop('hub2_sword_entry')
    target['requires_guaranteed_source']['abilities'].remove('Sword')
    # Whole-catalog hash in native evidence is historical after the main merge.
    # Preserve this exact historical target; the union catalog guards other targets.
    assert digest(target) == 'ce3d579238309e6c778f9776595b48ae253a2406d00a4d9e3d9a69d2a644f51f'
    owners = [(row['id'], name) for row in room_traversal_targets('block') for name, graph in row['graphs'].items()
              if any(route.get('capability') == CAPABILITY for route in graph['routes'])]
    assert owners == [(TARGET, 'hub2_sword_entry')]
