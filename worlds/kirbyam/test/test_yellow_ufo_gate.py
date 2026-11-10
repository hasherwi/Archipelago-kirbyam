"""Entry-bound Yellow Paint requires two distinct finite UFO acquisitions."""

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
from .test_mini_traversal import make_world
from .test_traversal import policy

OWNER = 'REGION_CARROT_CASTLE/ROOM_5_16'
UPSTREAM = 'REGION_CARROT_CASTLE/ROOM_5_14'
TARGET = 'bomb_733_yellow'
CHEST = 'MINOR_CHEST_SPRAY_PAINT_02'
EVIDENCE = Path(__file__).parents[1] / 'dev-docs' / 'carrot-yellow-ufo-source-runtime.json'
POLICIES = [
    (0, None, 0, False), (1, ['UFO'], 0, True), (1, ['Spark'], 0, False),
    (2, ['UFO'], 0, True), (2, ['UFO', 'Spark'], 0, False),
    (2, ['UFO'], 50, False), (2, ['UFO'], 100, False), (2, None, 0, False),
]


def target_row():
    return next(row for row in room_traversal_targets('block') if row['id'] == TARGET)


@pytest.mark.parametrize('mode,pool,weight,applies', POLICIES)
@pytest.mark.parametrize('gating', [0, 1])
@pytest.mark.parametrize('statues', [0, 1])
def test_actual_world_guaranteed_source_policy(monkeypatch, mode, pool, weight, applies, gating, statues):
    resolver = policy(mode, pool=pool, weight=weight, statues=statues, minny=False)
    monkeypatch.setattr('worlds.kirbyam.build_enemy_copy_ability_policy', lambda *a, **kw: resolver.policy)
    world = make_world(mode, gating, accessibility='minimal', ability_randomization_statues=statues,
                       ability_randomization_no_ability_weight=weight)
    assert rules.target_applies(target_row(), SourcePolicy(world._enemy_copy_ability_policy, bool(statues))) is applies
    target = world.multiworld.get_location(data.locations[CHEST].label, 1)
    state = CollectionState(world.multiworld)
    # Neither owner nor generic719 nor the separate734 return compartment is
    # independent access to720. Inventory must not replace the physical entry.
    state.can_reach_region = lambda name, player: name in {
        OWNER, 'REGION_CARROT_CASTLE/ROOM_5_07',
        'REGION_CARROT_CASTLE/ROOM_5_13__LOGIC__ENTRY_FROM_5_07'}
    assert target.access_rule(state) is (not applies)
    state.collect(world.create_item('UFO Ability'), prevent_sweep=True)
    assert target.access_rule(state) is (not applies)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    assert target.access_rule(state)
    state.remove(world.create_item('UFO Ability'))
    assert target.access_rule(state) is (not applies or not gating)
    # UFO was already progression. No blanket new promotion or starting grant.
    assert world.create_item('UFO Ability').classification == ItemClassification.progression
    assert not state.has('UFO Ability', 1)


@pytest.mark.parametrize('grant', [
    Grant(frozenset()), Grant(frozenset({'Normal'})), Grant(frozenset({'Unknown'})),
    Grant(frozenset({'UFO', 'Spark'}), randomized=True),
    Grant(frozenset({'UFO'}), randomized=True, can_fail=True),
])
def test_uncertain_source_grants_retain_prior_partial_behavior(grant):
    assert not rules.target_applies(target_row(), SimpleNamespace(grant=lambda *args: grant))


@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('area_keys', [False, True])
def test_two_finite_sources_forced_drop_and_reacquisition(gating, area_keys):
    graph = room_traversal_graph(TARGET, 'room14_entry', area_keys)
    resolver = SourcePolicy(json.loads(EVIDENCE.read_text())['source_policy'])
    row = target_row()
    assert (row['region'], row['native_room'], row['location']) == (OWNER, 733, CHEST)
    assert 'exit' not in row and list(row['graphs']) == ['room14_entry']
    assert graph.access_region == UPSTREAM
    assert [(start.node, start.equipped) for start in graph.starts] == [(TARGET + ':far_right', 'Normal')]
    assert [(node.key.rsplit(':', 1)[-1], node.room) for node in graph.nodes] == [
        ('far_right', 720), ('upper734', 734), ('left720', 720), ('top730', 730),
        ('upper_source', 730), ('ladder_top', 730), ('lower_source', 730),
        ('lower_carry', 730), ('arrival733', 733), ('chest', 733)]
    upper, lower = graph.placements
    assert [(p.identity, p.source_key, p.renewable, p.retry_evidence) for p in graph.placements] == [
        ('0x088D4FC0', 'SPARKY', False, None), ('0x088D4F9C', 'SPARKY', False, None)]
    assert [r.required_equipment for r in graph.routes] == [
        frozenset({name}) for name in ('Normal', 'Normal', 'Normal', 'Normal', 'UFO', 'Normal', 'UFO', 'UFO', 'UFO')]
    assert [r.capability for r in graph.routes] == [None] * 8 + ['bomb_733_yellow_ufo_top_charge']
    assert all(r.opens is None and not r.items and not r.recover_dropped_ability for r in graph.routes)
    assert [r.resets_room_instance for r in graph.routes] == [True, True, True, False, False, False, False, True, False]
    target, = graph.required_targets
    owned = frozenset({'UFO Ability'})
    assert graph.evaluate(resolver, frozenset(), gating).reaches(target) is (not gating)
    result = graph.evaluate(resolver, owned, gating)
    assert result.reaches(target) and not result.retry_assumptions
    # No source-less shortcut, upper-only carry or lower-only direct access.
    for placements in ((), (upper,), (lower,), (upper, replace(lower, identity=upper.identity))):
        assert not replace(graph, placements=placements).evaluate(resolver, owned, gating).reaches(target)
    for source in (upper, lower):
        behind = tuple(replace(p, node=target) if p == source else p for p in graph.placements)
        assert not replace(graph, placements=behind).evaluate(resolver, owned, gating).reaches(target)
    # Lower source is reached Normal only, with upper source already consumed.
    lower_positions = [p for p in result.positions if p.node == lower.node and p.equipped == 'Normal']
    assert lower_positions and all(upper.identity in p.consumed for p in lower_positions)
    assert all(lower.identity in p.consumed for p in result.positions if p.node == TARGET + ':lower_carry')
    for unsupported in (policy(), policy(1, pool=['Spark']), policy(2, pool=['UFO', 'Spark']),
                        policy(2, pool=['UFO'], weight=50), policy(2, pool=['UFO'], weight=100)):
        evaluated = graph.evaluate(unsupported, owned | {'Spark Ability'}, gating, allow_documented_retries=True)
        assert not evaluated.reaches(target) and not evaluated.retry_assumptions


@pytest.mark.parametrize('update', [
    {'id': 'bomb_138_green'}, {'kind': 'switch'}, {'native_room': 730},
    {'region': 'REGION_CARROT_CASTLE/ROOM_5_15'}, {'location': 'MINOR_CHEST_MUSIC_NOTE_06'},
    {'requires_guaranteed_source': {'source_key': 'UNKNOWN', 'ability': 'UFO'}},
    {'requires_guaranteed_source': {'source_key': 'SPARKY', 'abilities': ['UFO']}},
    {'requires_guaranteed_source': {'source_key': 'SPARKY', 'abilities': ['UFO', 'Spark']}},
])
def test_ufo_applicability_cannot_spread_to_another_target(update):
    row = deepcopy(target_row())
    row.update(update)
    region = row.pop('region')
    with pytest.raises(ValueError, match='applicability'):
        load_room_traversal({region: {'traversal': {'version': 1, 'targets': [row]}}})


@pytest.mark.parametrize('gating', [0, 1])
@pytest.mark.parametrize('area_keys', [0, 1])
@pytest.mark.parametrize('statues', [0, 1])
@pytest.mark.parametrize('room_sanity', [0, 1])
@pytest.mark.parametrize('minor_chests', [False, True])
def test_only_optional_yellow_chest_changes(monkeypatch, gating, area_keys, statues, room_sanity, minor_chests):
    monkeypatch.setattr(KirbyAmWorld, 'ENABLE_MINOR_CHESTS', minor_chests)
    raw = json.loads(EVIDENCE.read_text())['source_policy']
    monkeypatch.setattr('worlds.kirbyam.build_enemy_copy_ability_policy', lambda *a, **kw: raw)
    mw = setup_multiworld(KirbyAmWorld, steps=('generate_early',), seed=8, options={
        'ability_randomization_mode': 1, 'ability_gating': gating, 'area_keys': area_keys,
        'ability_randomization_statues': statues, 'room_sanity': room_sanity, 'accessibility': 'minimal',
    })
    world = mw.worlds[1]
    world.create_regions()
    world.set_rules()
    state = CollectionState(mw)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    if minor_chests:
        target = mw.get_location(data.locations[CHEST].label, 1)
        assert (target.address, target.parent_region.name) == (3960501, OWNER)
        assert target.access_rule(state) is (not gating)
        state.collect(world.create_item('Spark Ability'), prevent_sweep=True)
        assert target.access_rule(state) is (not gating)
        state.collect(world.create_item('UFO Ability'), prevent_sweep=True)
        assert target.access_rule(state)
        state.remove(world.create_item('UFO Ability'))
        assert target.access_rule(state) is (not gating)
    else:
        with pytest.raises(KeyError):
            mw.get_location(data.locations[CHEST].label, 1)
    assert world.create_item('UFO Ability').classification == ItemClassification.progression
    for name in (OWNER, UPSTREAM, 'REGION_CARROT_CASTLE/ROOM_5_15'):
        assert all(exit_.access_rule(state) for exit_ in mw.get_region(name, 1).exits)
    checks = [loc for loc in mw.get_locations(1) if loc.parent_region.name.startswith(OWNER) and loc.address != 3960501]
    assert len(checks) == room_sanity and all(loc.access_rule(state) for loc in checks)
    # Keep exact upstream labels and logical compartment ownership. Their
    # currently permissive implementations are not newly proved native routes.
    upstream_owner = 'REGION_CARROT_CASTLE/ROOM_5_07'
    assert data.regions[upstream_owner].exit_requirements[UPSTREAM] == {'all': ['can_climb', 'can_break_block']}
    assert mw.get_entrance(f'{upstream_owner} -> {UPSTREAM}', 1).access_rule(state)
    area = mw.get_entrance('REGION_RAINBOW_ROUTE/ROOM_1_13_LOWER -> REGION_CABBAGE_CAVERN/ROOM_3_04', 1)
    assert area.access_rule(state) is (not area_keys)
    state.collect(world.create_item('Cabbage Cavern - Area Key'), prevent_sweep=True)
    assert area.access_rule(state)


def test_720_cycle_cannot_supply_its_own_independent_entry():
    incoming = {name for name, region in data.regions.items() if UPSTREAM in region.exits}
    assert incoming == {'REGION_CARROT_CASTLE/ROOM_5_07', 'REGION_CARROT_CASTLE/ROOM_5_13_UPPER',
                        'REGION_CARROT_CASTLE/ROOM_5_13__LOGIC__ENTRY_FROM_5_14'}
    alias = 'REGION_CARROT_CASTLE/ROOM_5_13_UPPER'
    assert not any(alias in region.exits for region in data.regions.values())
    compartment = 'REGION_CARROT_CASTLE/ROOM_5_13__LOGIC__ENTRY_FROM_5_14'
    assert {name for name, region in data.regions.items() if compartment in region.exits} == {UPSTREAM}
    assert set(data.regions[compartment].exits) == {
        UPSTREAM, 'REGION_CARROT_CASTLE/ROOM_5_13__ROOM_CHECK'}


@pytest.mark.parametrize('gating,area_keys,statues,room_sanity', [
    (0, 0, 0, 0), (1, 0, 0, 0), (1, 1, 0, 1), (1, 1, 1, 1),
])
@pytest.mark.parametrize('mode,applies', [(1, True), (0, False)])
def test_actual_full_generation_seed8_at_one_hp(
        tmp_path, monkeypatch, gating, area_keys, statues, room_sanity, mode, applies):
    import Main

    generated = []
    main = Main.main

    def capture(*args, **kwargs):
        mw = main(*args, **kwargs)
        generated.append(mw)
        return mw

    monkeypatch.setattr(Main, 'main', capture)
    player = tmp_path / 'player.yaml'
    player.write_text(
        'name: Yellow\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n'
        f'  ability_randomization_mode: {mode}\n  ability_gating: {gating}\n  area_keys: {area_keys}\n'
        f'  ability_randomization_statues: {statues}\n  room_sanity: {room_sanity}\n'
        '  ability_randomization_no_ability_weight: 0\n  minimum_health: 1\n  maximum_health: 1\n'
        '  accessibility: full\n', encoding='utf-8')
    archive = generate_archive_from_fixture(player, tmp_path / 'out', seed=8)
    decoded = load_multidata_from_archive(archive)
    raw = decoded['slot_data'][1]['enemy_copy_ability_policy']
    # Enabling statues legitimately rerolls seed8's source feasibility. The
    # resulting Cutter assignment is unsupported here, rather than pretending
    # every option combination keeps the native UFO policy.
    applies = applies and not statues
    if applies:
        assert {**raw, 'allowed_abilities': list(raw['allowed_abilities'])} == (
            json.loads(EVIDENCE.read_text())['source_policy'])
    expected_ability = 'Spark' if mode == 0 else ('Cutter' if statues else 'UFO')
    assert SourcePolicy(raw).grant('SPARKY', lambda _: True).guaranteed == frozenset({expected_ability})
    assert rules.target_applies(target_row(), SourcePolicy(raw)) is applies
    assert decoded['locations'][1][3960501]
    mw, = generated
    assert not mw.get_unfilled_locations() and mw.can_beat_game() and mw.fulfills_accessibility()
    world = mw.worlds[1]
    state = CollectionState(mw)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    target = mw.get_location(data.locations[CHEST].label, 1)
    assert target.access_rule(state) is (not applies or not gating)
    state.collect(world.create_item('UFO Ability'), prevent_sweep=True)
    assert target.access_rule(state)
