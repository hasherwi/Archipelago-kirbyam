"""Finite Frosty UFO825 alternative, separate from the unchanged Ice witness."""

from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace

import pytest

from .. import traversal_rules as rules
from ..traversal import Node, Position, Route, compile_traversal_graph, reachable_positions
from ..traversal_data import has_graph_access, load_room_traversal, room_traversal_graph, room_traversal_targets
from .test_traversal import policy

TARGET = 'frozen_825_sound_effects'
CAPABILITY = 'switch_825_ufo_top_charge'
PREFIX = TARGET + ':ufo_'


def row():
    return next(r for r in room_traversal_targets('block') if r['id'] == TARGET)


def graph(keys=False):
    return room_traversal_graph(TARGET, 'ufo_entry', keys)


def qualified_endpoint_graph(keys=False):
    return graph(keys)


@pytest.mark.parametrize('mode,minibosses,pool,weight,expected', [
    (0, True, None, 0, True), (1, True, ['UFO'], 0, True),
    (1, True, ['Ice'], 0, True), (1, True, ['Fire'], 0, False),
    (1, False, ['UFO'], 0, True), (2, True, ['UFO'], 0, True),
    (2, True, ['Ice', 'UFO'], 0, False), (2, True, ['UFO'], 1, False),
    (2, True, ['UFO'], 100, False),
])
def test_exact_singleton_applicability(mode, minibosses, pool, weight, expected):
    assert rules.target_applies(row(), policy(mode, minibosses=minibosses, pool=pool, weight=weight)) is expected


@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('keys', [False, True])
@pytest.mark.parametrize('statues', [False, True])
def test_endpoint_equipment_permission_finite_source(gating, keys, statues):
    g = qualified_endpoint_graph(keys)
    resolver = policy(1, pool=['UFO'], statues=statues)
    target, = g.required_targets
    owned = frozenset({'UFO Ability'})
    result = g.evaluate(resolver, owned, gating, allow_documented_retries=True)
    assert result.reaches(target)
    terminal = [p for p in result.positions if p.node == target]
    assert any(p.equipped == 'UFO' for p in terminal)
    assert all(not p.opened for p in terminal)  # Optional equipment drop is always allowed.
    assert all(p.consumed == frozenset({'0x088CD3F0'}) for p in terminal)
    assert not result.retry_assumptions
    assert all(p.equipped == 'Normal' for p in g.starts)
    assert len(g.placements) == 1 and not g.placements[0].renewable
    assert g.placements[0].source_key == 'MR_FROSTY'
    assert all(not r.opens for r in g.routes)
    assert g.evaluate(resolver, frozenset(), gating).reaches(target) is (not gating)
    assert not replace(g, placements=()).evaluate(resolver, owned, gating).reaches(target)
    assert not g.evaluate(policy(), owned, gating).reaches(target)
    spent = replace(g, starts=(Position(PREFIX + 'arena', 'Normal', consumed=frozenset({'0x088CD3F0'})),))
    assert not spent.evaluate(resolver, owned, gating, allow_documented_retries=True).reaches(target)


@pytest.mark.parametrize('room,water,opens', [
    (824, 'dry', None), (825, 'swimming', None), (825, 'dry', 'permanent'),
])
def test_exact_room_dry_attack_and_no_persistent_credit(room, water, opens):
    with pytest.raises(ValueError):
        reachable_positions([Node('a', room), Node('b', room)],
                            [Route('a', 'b', CAPABILITY, opens=opens, water_state=water)],
                            (), [Position('a', 'UFO')], policy())


def test_compiler_rejects_persistent_credit():
    payload = deepcopy(row()['graphs']['ufo_entry'])
    payload['routes'][-1]['opens'] = 'permanent'
    with pytest.raises(ValueError, match='persistent'):
        compile_traversal_graph(payload)


def test_partial_witness_cannot_be_reused_for_another_target():
    payload = deepcopy(row())
    payload['id'] = 'not_the_reviewed_chest'
    with pytest.raises(ValueError, match='only to its reviewed chest'):
        load_room_traversal({payload['region']: {'traversal': {'version': 1, 'targets': [payload]}}})


def test_entry_requires_independent_known831_arrival():
    g = graph()
    assert g.unavailable_reason is None
    world = SimpleNamespace(player=1)
    state = SimpleNamespace(can_reach_region=lambda name, _: name == g.access_region)
    assert has_graph_access(world, state, g)
    for region in ('REGION_OLIVE_OCEAN/ROOM_6_12', 'REGION_OLIVE_OCEAN/ROOM_6_GOAL_2'):
        state.can_reach_region = lambda name, _, region=region: name == region
        assert not has_graph_access(world, state, g)


def test_same_location_or_graph_and_ice_classification_unchanged():
    r = row()
    assert set(r['graphs']) == {'local', 'ufo_entry'}
    assert r['location'] == 'MINOR_CHEST_MUSIC_NOTE_10'
    assert r['region'] == 'REGION_OLIVE_OCEAN/ROOM_6_GOAL_2'
    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy=policy(1, pool=['UFO']).policy,
        _ability_gating_enabled=lambda: True,
        multiworld=SimpleNamespace(get_location=lambda *_: object()),
    )
    assert not rules.goal2_ice_is_progression(world)
    ice = room_traversal_graph(TARGET, 'local')
    target, = ice.required_targets
    assert ice.evaluate(policy(), frozenset({'Ice Ability'}), True).reaches(target)
    assert not ice.evaluate(policy(1, pool=['UFO']), frozenset({'UFO Ability'}), True).reaches(target)


@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('keys', [False, True])
@pytest.mark.parametrize('enabled', [False, True])
@pytest.mark.parametrize('statues', [False, True])
def test_real_world_conditional_binding_under_explicit_entry_qualification(monkeypatch, gating, keys, enabled, statues):
    from BaseClasses import CollectionState, ItemClassification
    from .. import KirbyAmWorld
    from ..data import data
    from .test_mini_traversal import make_world

    generate = KirbyAmWorld.generate_early

    def generated_policy(world):
        generate(world)
        world._enemy_copy_ability_policy = policy(1, pool=['UFO']).policy

    monkeypatch.setattr(KirbyAmWorld, 'generate_early', generated_policy)
    monkeypatch.setattr(KirbyAmWorld, 'ENABLE_MINOR_CHESTS', enabled)
    world = make_world(1, gating, area_keys=keys, ability_randomization_statues=statues,
                       accessibility='minimal', room_sanity=not enabled)
    label = data.locations['MINOR_CHEST_MUSIC_NOTE_10'].label
    item = world.create_item('UFO Ability')
    assert item.classification == ItemClassification.progression
    assert not rules.goal2_ice_is_progression(world)
    if not enabled:
        with pytest.raises(KeyError):
            world.multiworld.get_location(label, 1)
        return
    target = world.multiworld.get_location(label, 1)
    assert target.address == 3960523
    state = CollectionState(world.multiworld)
    state.can_reach_region = lambda name, player: name == graph().access_region
    assert target.access_rule(state) is (not gating)
    state.collect(item, prevent_sweep=True)
    assert target.access_rule(state)
    state.can_reach_region = lambda name, player: name == row()['region']
    assert not target.access_rule(state)


def test_compact_native_endpoint_evidence_and_health_boundaries():
    import json
    from pathlib import Path

    evidence = json.loads((Path(__file__).resolve().parents[1]
                           / 'dev-docs/olive-sound-effects-ufo-acceptance.json').read_text())
    assert evidence['source']['grant'] == 'UFO'
    assert evidence['source']['ability_gating'] is False and evidence['source']['area_keys'] is False
    assert evidence['source']['allowed_ability_count'] == 25
    assert evidence['target']['client_location'] == 3960523
    assert evidence['target']['attack_damage'] == 18
    assert len(evidence['native_runs']) == 8
    combinations = set()
    for run in evidence['native_runs']:
        positive = run['name'].endswith('-positive')
        combinations.add((run['enemy_health_percent'], run['kirby_hp'], positive))
        assert run['passed']
        assert run['configuration_writes'] == 8
        assert run['gameplay_writes'] == run['restores'] == 0
        assert run['frosty_initial_hp'] == {100: 30, 500: 150}[run['enemy_health_percent']]
        assert run['frosty_first_zero_frame'] < run['ufo_acquired_frame']
        assert bool(run['client_messages']) is positive
        if positive:
            assert run['client_messages'] == [{'cmd': 'LocationChecks', 'locations': [3960523]}]
            assert run['ufo_acquired_frame'] < run['top_shot_first_frame'] < run['activation_frame']
            assert run['activation_frame'] < run['chest66_frame']
        else:
            assert run['activation_frame'] is None and run['chest66_frame'] is None
    assert combinations == {(health, hp, positive) for health in (100, 500)
                            for hp in (1, 6) for positive in (False, True)}
    for run in evidence['interception_runs']:
        assert run['waddle_hp_before'] - run['waddle_hp_after'] == 18
        assert run['waddle_hp_after'] < 0
        assert run['hit_frame'] < run['switch_frame']
        for field in ('task', 'object', 'parent', 'mask'):
            assert run['shot'][field] == run['same_live_projectile_at_switch'][field]


def test_continuous_composition_preserves_exact_entry_and_helper_qualification():
    import json
    from pathlib import Path
    from ..data import data

    evidence = json.loads((Path(__file__).resolve().parents[1]
                           / 'dev-docs/olive-sound-effects-ufo-composition.json').read_text())
    assert graph().access_region == evidence['access_region'] == 'REGION_OLIVE_OCEAN/ROOM_6_14'
    incoming = [key for key, region in data.regions.items() if graph().access_region in region.exits]
    assert incoming == [evidence['incoming_region']]
    assert {p.node for p in graph().starts} == {PREFIX + 'entry831'}
    assert all(p.equipped == 'Normal' for p in graph().starts)
    matrix = set()
    for run in evidence['runs']:
        positive = run['name'].endswith('-positive')
        matrix.add((run['enemy_health_percent'], run['kirby_hp'], positive))
        assert run['passed']
        assert [(r['room'], r['frame']) for r in run['room_history']] == [(814, 1085), (831, 1137), (825, 3613)]
        assert (run['room_history'][1]['x'], run['room_history'][1]['y']) == (40, 280.99609375)
        assert run['frosty_zero_frame'] < run['ufo_frame']
        assert bool(run['client_messages']) is positive
        if positive:
            assert run['ufo_frame'] < run['beam_frame'] < run['switch_frame'] < run['chest_frame']
            assert run['client_messages'] == [{'cmd': 'LocationChecks', 'locations': [3960523]}]
        else:
            assert run['switch_frame'] is None and run['chest_frame'] is None
        assert all(set(h['rooms']) <= {101, 106} for h in run['helper_room_history'])
        if run['enemy_health_percent'] == 500:
            assert run['helper_room_history'][-1]['rooms'] == [106, 106, 106]
    assert matrix == {(health, hp, positive) for health in (100, 500)
                      for hp in (1, 6) for positive in (False, True)}
    for run, hits in zip(evidence['attribution_runs'], (3, 15)):
        assert run['baseline_exact_route_state_match']
        assert len(run['frosty_damage_events']) == hits
        assert not run['helper_parent_projectiles_seen']
        for event in run['frosty_damage_events']:
            assert event['hp_before'] - event['hp_after'] == 10
            shot = event['previous_frame_live_shot']
            assert shot['damage'] == 10 and shot['parent'] == '0x2020ee0'
            assert shot['mask'] == '0x20000043'
        beam = run['live_player_beam_at_activation']
        assert beam['parent'] == '0x2020ee0' and beam['damage'] == 18


@pytest.mark.parametrize('gating,keys,health', [(1, 0, 100), (1, 1, 500), (0, 1, 100)])
def test_natural_full_pool_seed5_one_hp_fill(tmp_path, gating, keys, health):
    from ..traversal import SourcePolicy
    from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive

    fixture = tmp_path / 'player.yaml'
    fixture.write_text('name: OliveUFO\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n'
                       '  ability_randomization_mode: 1\n  minimum_health: 1\n  maximum_health: 1\n'
                       f'  ability_gating: {gating}\n  area_keys: {keys}\n'
                       f'  enemy_health_multiplier: {health}\n', encoding='utf-8')
    archive = generate_archive_from_fixture(fixture, tmp_path / 'out', seed=5)
    decoded = load_multidata_from_archive(archive)
    raw = decoded['slot_data'][1]['enemy_copy_ability_policy']
    assert len(raw['allowed_abilities']) == 25
    assert SourcePolicy(raw).grant('MR_FROSTY', lambda _: True).guaranteed == frozenset({'UFO'})
    assert 3960523 in decoded['locations'][1]


def test_native_full_pool_policy_matches_finite_graph_source():
    import json
    from pathlib import Path
    from ..traversal import SourcePolicy

    evidence = json.loads((Path(__file__).resolve().parents[1]
                           / 'dev-docs/olive-sound-effects-ufo-composition.json').read_text())
    resolver = SourcePolicy(evidence['source_policy'])
    assert resolver.grant('MR_FROSTY', lambda _: True).guaranteed == frozenset({'UFO'})
    g = qualified_endpoint_graph()
    target, = g.required_targets
    assert g.evaluate(resolver, frozenset({'UFO Ability'}), True).reaches(target)
    assert not g.evaluate(resolver, frozenset(), True).reaches(target)


def test_original_ice_payload_is_unchanged():
    import hashlib
    import json

    digest = hashlib.sha256(json.dumps(row()['graphs']['local'], sort_keys=True).encode()).hexdigest()
    assert digest == '0877c16ae5f777b0bf6961c4ea89d6f7c7e165b6f5358dd8157a444ff3557622'
