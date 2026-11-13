"""Private candidate contracts: fixed stand output is not reachability or native clear."""

from copy import deepcopy
from dataclasses import replace
from inspect import signature
from typing import Any, cast

import pytest

from .. import traversal_rules
from ..data import data
from ..enemy_ability_data import GATEABLE_ENEMY_COPY_ABILITIES
from ..master_source import (
    CARROT_HUB, CARROT_KEY, CENTRAL_MASTER_IDENTITY, CENTRAL_MASTER_SOURCE,
    CENTRAL_RETURN_EVENT, MASTER719_CAPABILITY, MASTER719_PREFIX, RAINBOW_WEST_HUB,
)
from ..peg_traversal import validate_peg_assignment
from ..traversal import (
    CAPABILITY_ABILITIES, Placement, Position, Route, TraversalGraph,
    compile_traversal_graph, validated_assignment,
)
from ..traversal_data import graph_items, load_room_traversal, room_traversal_graph, room_traversal_targets
from .test_traversal import policy
from .traversal_reference import reachable_positions as reference_positions

TARGET = 'bomb_719_room13'
END = MASTER719_PREFIX + 'left_door'


def master_graph(keys: bool = True) -> TraversalGraph:
    return room_traversal_graph(TARGET, 'central_master', keys)


def raw_graph() -> dict[str, Any]:
    row = next(row for row in room_traversal_targets('block') if row['id'] == TARGET)
    return deepcopy(row['graphs']['central_master'])


@pytest.mark.parametrize('mode', [0, 1, 2])
@pytest.mark.parametrize('statues', [False, True])
@pytest.mark.parametrize('weight', [0, 50, 100])
def test_exact_conditional_grant_is_not_ordinary_randomization(mode: int, statues: bool, weight: int) -> None:
    # Restrictive pools here are synthetic diagnostics, not a public option.
    resolver = policy(mode, statues=statues, weight=weight, pool=['Ice'])
    assert resolver.grant(CENTRAL_MASTER_SOURCE, lambda _: False).guaranteed == {'Master'}
    graph = master_graph()
    owned = graph_items(graph)
    assert graph.evaluate(resolver, owned, True).reaches(END)
    assert not graph.evaluate(resolver, owned - {CENTRAL_RETURN_EVENT}, False).reaches(END)
    assert not graph.evaluate(resolver, frozenset({'Master Ability', 'Defeat Dark Mind'}), False).reaches(END)


@pytest.mark.parametrize('keys', [False, True])
@pytest.mark.parametrize('mode,statues,weight', [(0, False, 0), (1, True, 0), (2, False, 100), (2, True, 100)])
def test_finite_graph_matches_unchanged_unoptimized_reference(
    keys: bool, mode: int, statues: bool, weight: int,
) -> None:
    graph = master_graph(keys)
    resolver = policy(mode, statues=statues, weight=weight)
    for owned in (graph_items(graph), graph_items(graph) - {CENTRAL_RETURN_EVENT}, frozenset()):
        expected = reference_positions(graph.nodes, graph.routes, graph.placements, graph.starts,
                                       resolver, owned, True)
        assert graph.evaluate(resolver, owned, True) == expected
        reordered = replace(graph, nodes=tuple(reversed(graph.nodes)), routes=tuple(reversed(graph.routes)))
        assert reordered.evaluate(resolver, owned, True) == expected
        assert graph.evaluate(resolver, owned, True) == expected  # no cross-evaluation grant cache
    result = graph.evaluate(resolver, graph_items(graph), True)
    assert Position(END, 'Master', consumed=frozenset({CENTRAL_MASTER_IDENTITY})) in result.positions
    assert not result.retry_assumptions
    assert all(p.node == graph.starts[0].node or p.equipped in ('Normal', 'Master') for p in result.positions)


@pytest.mark.parametrize('missing', [CENTRAL_RETURN_EVENT, RAINBOW_WEST_HUB, CARROT_HUB, CARROT_KEY])
def test_each_real_carrier_requirement_is_independent(missing: str) -> None:
    graph = master_graph()
    assert not graph.evaluate(policy(2, weight=100), graph_items(graph) - {missing}, True).reaches(END)
    if missing == CARROT_KEY:
        assert master_graph(False).evaluate(policy(2, weight=100), graph_items(graph) - {missing}, True).reaches(END)
    assert graph_items(master_graph(False)) == {CENTRAL_RETURN_EVENT, RAINBOW_WEST_HUB, CARROT_HUB}


@pytest.mark.parametrize('key', ['FIXED:Master', 'STATUE:088B4C88', 'CENTRAL_MASTER_STAND:088B4C89', 'MASTER_STAND'])
def test_alternate_source_keys_are_rejected(key: str) -> None:
    raw = raw_graph()
    raw['sources'][0]['source_key'] = key
    with pytest.raises(ValueError, match='Unknown ability source'):
        compile_traversal_graph(raw)


@pytest.mark.parametrize('field,value', [('grant', 'Master'), ('fixed_ability', 26), ('permission', False),
                                         ('retry_evidence', 'retouch'), ('renewable_evidence', 'retouch')])
def test_stand_has_no_extension_fields(field: str, value: Any) -> None:
    raw = raw_graph()
    raw['sources'][0][field] = value
    with pytest.raises(ValueError, match='Unknown Central Master placement'):
        compile_traversal_graph(raw)


@pytest.mark.parametrize('change', [
    {'requirements': frozenset()}, {'identity': 'other'}, {'renewable': True},
    {'retry_evidence': 'again'}, {'node': MASTER719_PREFIX + 'left_pose'}, {'source_key': 'WADDLE_DOO'},
])
def test_direct_source_construction_is_equally_checked(change: dict[str, Any]) -> None:
    graph = master_graph()
    bad = replace(graph, placements=(replace(graph.placements[0], **change),))
    with pytest.raises(ValueError, match='sole original'):
        bad.evaluate(policy(), graph_items(graph), False)


@pytest.mark.parametrize('starts', [
    (Position(MASTER719_PREFIX + 'central_entry', 'Sword'),),
    (Position(MASTER719_PREFIX + 'central_entry', 'Master'),),
    (Position(MASTER719_PREFIX + 'central_entry', frozenset({'Normal', 'Sword'})),),
    (Position(MASTER719_PREFIX + 'central_entry', 'Sword'), Position(MASTER719_PREFIX + 'central_entry')),
    (Position(MASTER719_PREFIX + 'central_entry'), Position(MASTER719_PREFIX + 'central_entry', 'Sword')),
    (Position(MASTER719_PREFIX + 'stand'),),
])
def test_mixed_equipment_is_rejected_before_source_phase_dedup(starts: tuple[Position, ...]) -> None:
    graph = master_graph()
    with pytest.raises(ValueError, match='fresh Normal'):
        replace(graph, starts=starts).evaluate(policy(), graph_items(graph), False)


@pytest.mark.parametrize('mutation', ['wrong_room', 'second_source', 'missing_contact', 'loop', 'guarded_loop',
                                      'drop_return', 'recovery', 'ammo', 'missing_equipment', 'swimming',
                                      'wrong_capability', 'opens', 'alias', 'skip_room'])
def test_only_exact_single_acquisition_forward_graph_is_supported(mutation: str) -> None:
    graph = master_graph()
    if mutation == 'wrong_room':
        graph = replace(graph, nodes=(replace(graph.nodes[1], room=800), *graph.nodes[:1], *graph.nodes[2:]))
    elif mutation == 'second_source':
        graph = replace(graph, placements=(*graph.placements, Placement(graph.nodes[0].key, 'SPARKY')))
    elif mutation == 'missing_contact':
        graph = replace(graph, routes=graph.routes[1:])
    elif mutation in {'loop', 'guarded_loop', 'drop_return'}:
        graph = replace(graph, routes=(*graph.routes, Route(
            END, graph.placements[0].node, items=frozenset({'Later'}) if mutation == 'guarded_loop' else frozenset(),
            required_equipment=frozenset({'Normal'}) if mutation == 'drop_return' else None,
            room_transition=True, resets_room_instance=True)))
    elif mutation == 'alias':
        graph = replace(graph, placements=(*graph.placements, replace(graph.placements[0], identity='alias')))
    elif mutation == 'skip_room':
        graph = replace(graph, routes=(*graph.routes, Route(graph.nodes[1].key, END)))
    else:
        kwargs = cast(dict[str, Any], {
            'recovery': {'recover_dropped_ability': True}, 'ammo': {'uses_object': CENTRAL_MASTER_IDENTITY},
            'missing_equipment': {'required_equipment': None}, 'swimming': {'water_state': 'swimming'},
            'wrong_capability': {'capability': 'rope'}, 'opens': {'opens': 'forever'},
        }[mutation])
        graph = replace(graph, routes=(*graph.routes[:-1], replace(graph.routes[-1], **kwargs)))
    with pytest.raises(ValueError, match='Central Master'):
        graph.evaluate(policy(), graph_items(graph), False)


@pytest.mark.parametrize('change', [{'access_region': None}, {'access_region': 'elsewhere'},
                                    {'requires_all_hub_switches': True}, {'required_targets': frozenset({'other'})}])
def test_direct_graph_access_and_target_cannot_be_substituted(change: dict[str, Any]) -> None:
    graph = master_graph()
    with pytest.raises(ValueError, match='independent Central access'):
        replace(graph, **change).evaluate(policy(), graph_items(graph), False)


def test_target_owner_cannot_move_to_another_compartment() -> None:
    rooms = {name: {'traversal': deepcopy(region.traversal)} for name, region in data.regions.items()}
    row = next(row for row in rooms['REGION_CARROT_CASTLE/ROOM_5_07']['traversal']['targets']
               if row['id'] == TARGET)
    row['exit'] = 'REGION_CARROT_CASTLE/ROOM_5_08'
    with pytest.raises(ValueError, match='reviewed Carrot entry'):
        load_room_traversal(rooms)


@pytest.mark.parametrize('guard', [None, [], ['Mustard Mountain - Area Key']])
def test_enabled_key_cannot_disappear_in_raw_schema(guard: list[str] | None) -> None:
    raw = raw_graph()
    crossing = raw['routes'][2]
    if guard is None:
        crossing.pop('area_key_items')
    else:
        crossing['area_key_items'] = guard
    with pytest.raises(ValueError, match='Carrot Area Key'):
        compile_traversal_graph(raw)


def test_master_does_not_enter_pool_permissions_or_other_targets() -> None:
    assert 'Master' not in GATEABLE_ENEMY_COPY_ABILITIES
    assert not any('Master' in item.label for item in data.items.values())
    rows = traversal_rules.extra_traversal_targets()
    new_rows = [row['id'] for row in rows if any(
        source.source_key == CENTRAL_MASTER_SOURCE
        for graph in traversal_rules.target_graphs(row, True) for source in graph.placements)]
    assert new_rows == [TARGET]
    assert CAPABILITY_ABILITIES['bomb_719_room13'] == {'Beam'}
    assert CAPABILITY_ABILITIES[MASTER719_CAPABILITY] == {'Master'}
    assert signature(validated_assignment).parameters['max_attempts'].default == 128
    assert signature(validate_peg_assignment).parameters['max_attempts'].default == 8192


def test_early_applicability_moves_to_each_graph_and_remains_an_or() -> None:
    row = next(row for row in traversal_rules.extra_traversal_targets() if row['id'] == TARGET)
    assert 'requires_guaranteed_source' not in row
    assert 'requires_any_guaranteed_source' not in row
    for witness, ability in [('room5_entry', 'Beam'), ('room5_fighter_entry', 'Fighter'),
                             ('room5_sword_entry', 'Sword'), ('room5_fire_entry', 'Fire')]:
        graph = room_traversal_graph(TARGET, witness)
        assert graph.required_guaranteed_source == ('WADDLE_DOO', ability)
        assert CENTRAL_RETURN_EVENT not in graph_items(graph)
        resolver = policy(1, pool=[ability])  # synthetic deterministic output control
        owned = graph_items(graph) | {f'{ability} Ability'}
        assert traversal_rules.graph_succeeds(graph, resolver, owned, True, retries=False)
        assert not traversal_rules.graph_succeeds(
            graph, policy(2, pool=[ability], weight=50), owned, True, retries=True)


@pytest.mark.parametrize('mutation', ['source', 'route', 'requirement'])
def test_historical_projection_cannot_hide_a_changed_master_candidate(mutation: str) -> None:
    from .support.master719_history import before_master719

    row = deepcopy(next(row for row in room_traversal_targets('block') if row['id'] == TARGET))
    graph = row['graphs']['central_master']
    if mutation == 'source':
        graph['sources'][0]['id'] = 'other'
    elif mutation == 'route':
        graph['routes'][-1]['capability'] = 'rope'
    else:
        graph['sources'][0]['items'] = []
    with pytest.raises(AssertionError):
        before_master719(row)


@pytest.mark.parametrize('field,value', [('initial_equipment', 'Master'), ('grant', 'Master')])
def test_unknown_special_graph_effects_fail_closed(field: str, value: str) -> None:
    raw = raw_graph()
    raw[field] = value
    with pytest.raises(ValueError, match='Unknown Central Master graph'):
        compile_traversal_graph(raw)


def test_current_catalog_changes_only_exact_master719_contract() -> None:
    import hashlib
    import json
    from pathlib import Path

    catalog = json.loads((Path(__file__).parents[1]
                          / 'dev-docs/supported-source-monotonicity-catalog.json').read_text())
    # Compare a strict reverse projection to the complete baseline structure.
    # Source hashes are separately derived from current files; native evidence
    # bytes are never refreshed by this structural projection.
    from .support.green138_history import catalog_before_green138
    catalog = catalog_before_green138(catalog)
    catalog.pop('source_sha256')
    assert catalog['witnesses'] == 145 and catalog['variants'] == 290
    catalog['witnesses'], catalog['variants'] = 144, 288
    assert catalog['capability_providers'].pop(MASTER719_CAPABILITY) == ['Master']
    source = catalog['sources'].pop(CENTRAL_MASTER_SOURCE + '@' + CENTRAL_MASTER_IDENTITY)
    assert source == [{'source_key': CENTRAL_MASTER_SOURCE, 'identity': CENTRAL_MASTER_IDENTITY,
                       'renewable': False, 'documented_retry': False}]
    new = [row for row in catalog['graphs'] if row['witness'] == 'central_master']
    assert len(new) == 2 and {row['area_keys'] for row in new} == {False, True}
    assert all(row['target'] == TARGET for row in new)
    catalog['graphs'] = [row for row in catalog['graphs'] if row['witness'] != 'central_master']
    for row in catalog['graphs']:
        if row['target'] != TARGET:
            continue
        assert row['target_source_condition'] is None
        row['target_source_condition'] = {
            'source_key': 'WADDLE_DOO', 'abilities': ['Beam', 'Fighter', 'Sword', 'Fire']}
        if row['witness'] in {'room5_entry', 'room5_fighter_entry'}:
            ability = 'Beam' if row['witness'] == 'room5_entry' else 'Fighter'
            assert row['graph_source_condition'] == ['WADDLE_DOO', ability]
            row['graph_source_condition'] = None
    assert hashlib.sha256(json.dumps(catalog, sort_keys=True, separators=(',', ':')).encode()).hexdigest() == (
        "dd5eec552fce4ecc410c3c7f14508ed84b6e7ada6d7c9ab931937a491fc45fb8")


@pytest.mark.parametrize('route_index', range(7))
def test_every_contact_and_carrier_edge_has_exact_equipment_guard(route_index: int) -> None:
    graph = master_graph()
    routes = list(graph.routes)
    routes[route_index] = replace(routes[route_index], required_equipment=None)
    with pytest.raises(ValueError, match='equipment'):
        replace(graph, routes=tuple(routes)).evaluate(policy(), graph_items(graph), True)


def test_stand_cannot_substitute_generic_global_master_attacks() -> None:
    graph = master_graph()
    for capability in ('metal', 'rope', 'peg', 'fuse', 'underwater_block_hit', 'bomb_719_room13'):
        routes = (*graph.routes[:-1], replace(graph.routes[-1], capability=capability))
        with pytest.raises(ValueError, match='charged-wave'):
            replace(graph, routes=routes).evaluate(policy(), graph_items(graph), False)
