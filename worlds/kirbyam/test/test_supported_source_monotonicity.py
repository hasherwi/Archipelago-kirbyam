"""Supported public pools retain Beam; custom narrow pools are not monotone."""
import ast
import inspect
import random
import textwrap
from typing import cast
from itertools import product

import pytest

from .. import KirbyAmWorld
from ..ability_randomization import build_enemy_copy_ability_policy
from ..enemy_ability_data import GATEABLE_ENEMY_COPY_ABILITIES, VALID_ENEMY_COPY_ABILITIES
from ..traversal import CAPABILITY_ABILITIES, SourcePolicy, ability_permission, attack_provider
from ..traversal_data import _room_catalog, room_traversal_graph, graph_items


def test_public_generation_cannot_remove_beam_from_the_pool() -> None:
    assert 'Beam' in VALID_ENEMY_COPY_ABILITIES
    assert 'Beam' not in GATEABLE_ENEMY_COPY_ABILITIES
    assert ability_permission('Beam', frozenset(), True)
    assert (inspect.signature(build_enemy_copy_ability_policy).parameters['whitelist'].default
            == VALID_ENEMY_COPY_ABILITIES)
    assert not any('whitelist' in name or 'ability_pool' in name
                   for name in KirbyAmWorld.options_dataclass.type_hints)
    tree = ast.parse(textwrap.dedent(inspect.getsource(KirbyAmWorld.generate_early)))
    builders = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name) and node.func.id == 'build_enemy_copy_ability_policy']
    assert len(builders) == 2  # Initial draw and bounded whole-policy redraw.
    assert all(not any(keyword.arg in ('whitelist', None) for keyword in call.keywords) for call in builders)
    # Positional arguments must not reach the optional whitelist parameter either.
    assert all(len(call.args) <= 5 for call in builders)


def test_live_supported_source_and_statue_pools_always_retain_beam() -> None:
    targets, _, _ = _room_catalog()
    keys = {source.source_key for target in targets for witness in target['graphs']
            for source in room_traversal_graph(target['id'], witness).placements}
    all_owned = frozenset(name + ' Ability' for name in GATEABLE_ENEMY_COPY_ABILITIES)
    for boss, miniboss, passive, statues, weight in product((False, True), (False, True),
                                                            (False, True), (False, True), (0, 99, 100)):
        raw = build_enemy_copy_ability_policy(random.Random(17), 2, boss, miniboss,
                                              include_passive_enemies=passive, no_ability_weight=weight)
        assert set(raw['allowed_abilities']) == set(VALID_ENEMY_COPY_ABILITIES)
        resolver = SourcePolicy(raw, include_statues=statues)
        minny = resolver.grant('MINNY', lambda _: True)
        assert not minny.randomized and minny.guaranteed == {'Mini'}
        for key in keys:
            for owned in (frozenset(), frozenset({'Hammer Ability', 'Stone Ability'}), all_owned):
                grant = resolver.grant(key, lambda name: ability_permission(name, owned, True))
                if grant.randomized and grant.abilities:
                    assert 'Beam' in grant.abilities, (key, weight, owned)
                if grant.randomized:
                    assert not (grant.guaranteed - {'Beam'}), (key, grant)


def test_installed_beam_routes_require_raw_source_scope_or_source_free_water_gun() -> None:
    targets, _, _ = _room_catalog()
    seen = set()
    beam_capabilities = set()
    recovery = set()
    for target in targets:
        for witness in target['graphs']:
            for area_keys in (False, True):
                identity = target['id'], witness, area_keys
                assert identity not in seen
                seen.add(identity)
                graph = room_traversal_graph(*identity)
                assert all(position.equipped == 'Normal' for position in graph.starts)
                for route in graph.routes:
                    if route.recover_dropped_ability:
                        assert route.capability == 'mini_corridor'
                        recovery.add(target['id'])
                    if not route.capability:
                        assert route.uses_object is None
                        continue
                    allowed = (CAPABILITY_ABILITIES[route.capability]
                               if route.allowed_abilities is None else route.allowed_abilities)
                    if attack_provider('Beam', route.water_state) in allowed:
                        beam_capabilities.add((target['id'], witness, route.capability))
                        if route.water_state == 'dry':
                            condition = target.get('requires_guaranteed_source')
                            assert (graph.required_guaranteed_source == ('WADDLE_DOO', 'Beam')
                                    or condition is not None and condition['source_key'] == 'WADDLE_DOO')
                            # Applicability uses the unfiltered physical policy, not
                            # a transient Beam-only permission-filtered live draw.
                            if condition is not None:
                                from ..traversal_rules import target_applies
                                live = SourcePolicy(build_enemy_copy_ability_policy(random.Random(17), 2, True, True))
                                assert not target_applies(target, live)
                            else:
                                live = SourcePolicy(build_enemy_copy_ability_policy(random.Random(17), 2, True, True))
                                assert not graph.evaluate(live, graph_items(graph), True).positions
                            continue
                        assert route.water_state == 'swimming'
                        assert attack_provider('Normal', route.water_state) in allowed
                        assert not route.uses_object and not route.opens
                        if route.capability == 'bomb_110_room9_underwater_normal_spray':
                            assert (target['id'], witness) == ('bomb_110_room9', 'upper_entry_normal_water')
                            payload, = graph.placements
                            assert (payload.source_key, payload.identity, payload.renewable) == (
                                'SWORD_KNIGHT', '0x088B74CC', False)
                            spit, = [edge for edge in graph.routes if edge.uses_object]
                            assert spit.uses_object == payload.identity
                            assert spit.capability == 'bomb_110_upper_normal_spit'
                        else:
                            assert not graph.placements
                        assert graph.evaluate(SourcePolicy({'mode': 0}), frozenset(), True).reaches(route.target)
    assert beam_capabilities == {
        ('underwater_819_exit', 'local', 'underwater_block_hit'),
        ('bomb_110_room9', 'upper_entry_normal_water', 'bomb_110_room9_underwater_normal_spray'),
        ('bomb_538_beam_left_exit', 'normal544_beam_entry', 'bomb_538_beam_left_crossover'),
        ('bomb_517_chocolate', 'hub2_entry', 'bomb_517_chocolate'),
        ('bomb_719_room13', 'room5_entry', 'bomb_719_room13'),
    }
    assert recovery == {'mini_321_cross_to_right', 'mini_134_ocean_spray'}
    assert len(seen) == 290  # All145 witnesses, both key modes, including logical subregions.


@pytest.mark.parametrize('target,witness', [('metal_176_goal2_drink', 'local'),
                                            ('metal_557_goal1_tomato', 'local'),
                                            ('metal_228_chest', 'bonkers_joint')])
def test_supported_finite_metal_sources_do_not_gain_transient_guarantees(target: str, witness: str) -> None:
    # Select the finite witness; no renewable statue OR alternative.
    graph = room_traversal_graph(target, witness)
    resolver = SourcePolicy(build_enemy_copy_ability_policy(random.Random(17), 2, True, True))
    for owned in (frozenset(), frozenset({'Hammer Ability'}), frozenset({'Stone Ability'}),
                  frozenset({'Smash Ability'}), frozenset({'Burning Ability'}),
                  frozenset({'Hammer Ability', 'Stone Ability', 'Smash Ability', 'Burning Ability'}),
                  frozenset(name + ' Ability' for name in GATEABLE_ENEMY_COPY_ABILITIES)):
        result = graph.evaluate(resolver, owned | graph_items(graph), True, allow_documented_retries=True)
        assert not all(result.reaches(endpoint) for endpoint in graph.required_targets)


@pytest.mark.parametrize('mode', [0, 1])
def test_supported_static_assignments_only_gain_permission(mode: int) -> None:
    targets, _, _ = _room_catalog()
    keys = {source.source_key for target in targets for witness in target['graphs']
            for source in room_traversal_graph(target['id'], witness).placements}
    for statues in (False, True):
        raw = build_enemy_copy_ability_policy(random.Random(19), mode, True, True,
                                              include_passive_enemies=True)
        resolver = SourcePolicy(raw, include_statues=statues)
        for key in keys:
            full = resolver.grant(key, lambda _: True)
            assert not full.randomized and len(full.abilities) <= 1
            for owned in (frozenset(), frozenset({'Stone Ability'}), frozenset({'Burning Ability'})):
                small = resolver.grant(key, lambda name: ability_permission(name, owned, True))
                larger = resolver.grant(key, lambda name: ability_permission(
                    name, owned | {'Stone Ability', 'Burning Ability', 'Smash Ability', 'Hammer Ability'}, True))
                assert small.guaranteed <= larger.guaranteed <= full.guaranteed


def test_supported_installed_rule_cannot_cache_a_transient_source_or_bootstrap_alternative() -> None:
    from unittest.mock import patch
    from BaseClasses import CollectionState
    from .. import traversal_rules as rules
    from ..data import data
    from .test_mini_traversal import make_world
    from .test_metal_room205 import OUTER, TOP, SIDES, MINOR23, TARGET

    # Actual generated policy and actual native205/209/210 graph, in a bounded
    # topology fixture. No custom whitelist, copied equipment or synthetic source.
    with patch.object(rules, 'install_extra_traversal_rules'):
        world = make_world(2, True, area_keys=False, room_sanity=True,
                           ability_randomization_no_ability_weight=0)
    row = next(row for row in _room_catalog()[0] if row['id'] == TARGET)
    with patch.object(rules, 'extra_traversal_targets', return_value=(row,)):
        rules.install_extra_traversal_rules(world)
    mw = world.multiworld
    central = 'REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE'
    east = 'Peppermint Palace East - Hub Connection'
    rainbow = 'Rainbow Route East - Hub Connection'
    for region in mw.get_regions(1):
        region.exits = [edge for edge in region.exits if region.name in SIDES
                        and edge.connected_region and edge.connected_region.name in SIDES]
    menu = mw.get_region('Menu', 1)
    menu.connect(mw.get_region(OUTER, 1))
    menu.connect(mw.get_region(central, 1))
    location = mw.get_location(data.locations[MINOR23].label, 1)
    location.place_locked_item(world.create_item(east))
    edge = mw.get_entrance(f'{OUTER} -> {TOP}', 1)

    def initial(*items: str) -> CollectionState:
        state = CollectionState(mw)
        for name in items:
            state.collect(world.create_item(name), prevent_sweep=True)
        return state

    cached = initial('Hammer Ability', rainbow)
    assert not edge.access_rule(cached) and not location.can_reach(cached)
    cached.collect(world.create_item('Stone Ability'), prevent_sweep=True)
    fresh = initial('Hammer Ability', 'Stone Ability', rainbow)
    for state in (cached, fresh):
        assert not edge.access_rule(state)
        assert not state.can_reach_region(TOP, 1) and not location.can_reach(state)
        state.sweep_for_advancements(locations=[location])
        assert not state.has(east, 1) and not edge.access_rule(state)
        # An independently acquired connection genuinely enables the reviewed
        # permanent Stone alternative; the negative is not an impossible fixture.
        state.collect(world.create_item(east), prevent_sweep=True)
        assert edge.access_rule(state) and location.can_reach(state)


def test_saved_catalog_enumerates_every_source_and_provider_variant() -> None:
    import json
    from pathlib import Path
    record = json.loads((Path(__file__).parents[1] / 'dev-docs/supported-source-monotonicity-catalog.json').read_text())
    actual = {(target['id'], witness, keys): room_traversal_graph(target['id'], witness, keys)
              for target in _room_catalog()[0] for witness in target['graphs'] for keys in (False, True)}
    saved = {(row['target'], row['witness'], row['area_keys']): row for row in record['graphs']}
    assert len(saved) == len(record['graphs']) == record['variants'] == 290
    assert record['witnesses'] == 145 and set(saved) == set(actual)
    assert record['ungated_pool_abilities'] == ['Beam']
    assert record['capability_providers'] == {key: sorted(values) for key, values in CAPABILITY_ABILITIES.items()}
    source_ids = set()
    targets = {target['id']: target for target in _room_catalog()[0]}
    for identity, graph in actual.items():
        target, witness, _ = identity
        raw = targets[target]
        assert saved[identity]['target_source_condition'] == raw.get('requires_guaranteed_source')
        assert saved[identity]['target_source_alternatives'] == raw.get('requires_any_guaranteed_source')
        assert saved[identity]['graph_source_condition'] == (
            list(graph.required_guaranteed_source) if graph.required_guaranteed_source else None)
        assert saved[identity]['equipment_routes'] == [
            {'from': route.source, 'to': route.target, 'required_equipment': sorted(route.required_equipment)}
            for route in graph.routes if route.required_equipment is not None]
        assert all(source.identity is not None for source in graph.placements)
        expected = sorted({source.source_key + '@' + cast(str, source.identity) for source in graph.placements})
        assert saved[identity]['source_ids'] == expected
        source_ids.update(expected)
        for source in graph.placements:
            assert source.identity is not None
            assert {
                'source_key': source.source_key, 'identity': source.identity,
                'renewable': source.renewable, 'documented_retry': bool(source.retry_evidence)
            } in record['sources'][source.source_key + '@' + source.identity]
        expected_routes = []
        for route in graph.routes:
            if not route.capability:
                continue
            allowed = (CAPABILITY_ABILITIES[route.capability]
                       if route.allowed_abilities is None else route.allowed_abilities)
            expected_routes.append({
                'from': route.source, 'to': route.target, 'capability': route.capability,
                'water_state': route.water_state, 'allowed_abilities': sorted(allowed),
                'beam_provider': attack_provider('Beam', route.water_state),
                'beam_accepted': attack_provider('Beam', route.water_state) in allowed,
                'normal_accepted': attack_provider('Normal', route.water_state) in allowed,
                'recover_dropped_ability': route.recover_dropped_ability})
        assert saved[identity]['capability_routes'] == expected_routes
    assert source_ids == set(record['sources']) and len(source_ids) == 109
