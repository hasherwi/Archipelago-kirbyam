"""Historical projections must reject new semantics rather than hide them."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from ..traversal_data import room_traversal_graph, room_traversal_targets
from .support.historical_graphs import historical_main_compiled, historical_main_raw


@pytest.mark.parametrize('condition', [None, ('MR_FROSTY', 'UFO'), ('WADDLE_DOO', 'Ice')])
def test_compiled_projection_rejects_missing_or_altered_825_condition(condition: tuple[str, str] | None) -> None:
    graph = room_traversal_graph('frozen_825_sound_effects', 'local')
    with pytest.raises(AssertionError):
        altered = replace(graph, required_guaranteed_source=condition)
        historical_main_compiled(altered, 'frozen_825_sound_effects', 'local')


def test_compiled_projection_rejects_new_conditions_elsewhere() -> None:
    graph = room_traversal_graph('fuse_126', 'local')
    with pytest.raises(AssertionError):
        historical_main_compiled(replace(graph, required_guaranteed_source=('HOT_HEAD', 'Fire')), 'fuse_126', 'local')


def test_compiled_projection_rejects_equipment_constraint() -> None:
    graph = room_traversal_graph('fuse_126', 'local')
    routes = (replace(graph.routes[0], required_equipment=frozenset({'Fire'})), *graph.routes[1:])
    with pytest.raises(AssertionError):
        historical_main_compiled(replace(graph, routes=routes), 'fuse_126', 'local')


@pytest.mark.parametrize('condition', [None, {'source_key': 'MR_FROSTY', 'ability': 'UFO'},
                                       {'source_key': 'MR_FROSTY', 'abilities': ['Ice']}])
def test_raw_projection_rejects_missing_or_altered_825_condition(condition: dict[str, Any] | None) -> None:
    row = next(row for row in room_traversal_targets('block') if row['id'] == 'frozen_825_sound_effects')
    graph = deepcopy(row['graphs']['local'])
    if condition is None:
        del graph['requires_guaranteed_source']
    else:
        graph['requires_guaranteed_source'] = condition
    with pytest.raises(AssertionError):
        historical_main_raw(graph, row['id'], 'local')


def test_raw_projection_requires_exact_reviewed_evidence_edit() -> None:
    row = next(row for row in room_traversal_targets('fuse') if row['id'] == 'fuse_126')
    graph = deepcopy(row['graphs']['local'])
    graph['routes'][0]['evidence'] += ' changed'
    with pytest.raises(AssertionError):
        historical_main_raw(graph, row['id'], 'local')


def test_compiled_projection_retains_physical_mutations() -> None:
    graph = room_traversal_graph('fuse_126', 'local')
    routes = (replace(graph.routes[0], target=graph.routes[0].source), *graph.routes[1:])
    altered = historical_main_compiled(replace(graph, routes=routes), 'fuse_126', 'local')
    baseline = json.loads((Path(__file__).parents[1] / 'dev-docs/goal-burning-original-compiled-fingerprints.json')
                          .read_text())
    digest = hashlib.sha256(json.dumps(altered, default=sorted, sort_keys=True).encode()).hexdigest()
    assert digest != baseline['fuse_126/local/False']


def test_raw_projection_retains_physical_mutations_and_original_input() -> None:
    row = next(row for row in room_traversal_targets('fuse') if row['id'] == 'fuse_126')
    original = deepcopy(row['graphs']['local'])
    graph = deepcopy(original)
    graph['routes'][0]['to'] = 'altered_target'
    altered = historical_main_raw(graph, row['id'], 'local')
    assert original == row['graphs']['local']
    assert graph['routes'][0]['evidence'] == original['routes'][0]['evidence']
    path = Path(__file__).parents[1] / 'dev-docs/goal-burning-original-graph-fingerprints.json'
    baseline = json.loads(path.read_text())
    digest = hashlib.sha256(json.dumps(altered, sort_keys=True).encode()).hexdigest()
    assert digest != baseline['fuse_126/local']


@pytest.mark.parametrize('mutation', [
    'access', 'source', 'route', 'reset', 'equipment', 'target', 'extra_graph',
    'missing_condition', 'wrong_condition', 'target_condition', 'target_any_condition',
])
def test_green_projection_rejects_changes_to_removed_semantics(mutation: str) -> None:
    from .support.green138_history import before_green138
    row = deepcopy(next(r for r in room_traversal_targets('block') if r['id'] == 'bomb_138_green'))
    normal = row['graphs']['upper_left_normal_slide']
    spark = row['graphs']['upper_left_entry']
    if mutation == 'access':
        normal['access']['region'] = 'REGION_RAINBOW_ROUTE/ROOM_1_27'
    elif mutation == 'source':
        normal['sources'].append({'id': 'unreviewed'})
    elif mutation == 'route':
        normal['routes'][-1]['capability'] = 'bomb_138_green'
    elif mutation == 'reset':
        del normal['routes'][0]['room_instance']
    elif mutation == 'equipment':
        normal['routes'][-1]['required_equipment'] = ['Spark']
    elif mutation == 'target':
        normal['required_targets'] = [normal['starts'][0]]
    elif mutation == 'extra_graph':
        row['graphs']['unreviewed'] = deepcopy(normal)
    elif mutation == 'missing_condition':
        del spark['requires_guaranteed_source']
    elif mutation == 'wrong_condition':
        spark['requires_guaranteed_source']['ability'] = 'Beam'
    elif mutation == 'target_condition':
        row['requires_guaranteed_source'] = {'source_key': 'SPARKY', 'ability': 'Spark'}
    else:
        row['requires_any_guaranteed_source'] = []
    with pytest.raises((AssertionError, KeyError)):
        before_green138(row)


@pytest.mark.parametrize('mutation', ['source', 'route', 'access', 'owner', 'location'])
def test_green_projection_keeps_original_spark_and_ownership_mutations(mutation: str) -> None:
    from .support.green138_history import before_green138
    row = deepcopy(next(r for r in room_traversal_targets('block') if r['id'] == 'bomb_138_green'))
    spark = row['graphs']['upper_left_entry']
    if mutation == 'source':
        spark['sources'][0]['id'] = 'wrong-source'
    elif mutation == 'route':
        spark['routes'][-1]['to'] = 'wrong-chest'
    elif mutation == 'access':
        spark['access']['region'] = 'REGION_RAINBOW_ROUTE/ROOM_1_27_UPPER_RIGHT'
    elif mutation == 'owner':
        row['region'] = 'wrong-owner'
    else:
        row['location'] = 'wrong-location'
    original = deepcopy(row)
    projected = before_green138(row)
    pins = json.loads((Path(__file__).parents[1] / 'dev-docs/main-ranged-union-catalog.json').read_text())
    digest = hashlib.sha256(json.dumps(projected, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert digest != pins['targets']['bomb_138_green']
    assert row == original


@pytest.mark.parametrize('mutation', ['source', 'equipment', 'condition', 'provider', 'count'])
def test_compiled_green_catalog_projection_rejects_removed_semantic_mutations(mutation: str) -> None:
    from .support.green138_history import catalog_before_green138
    catalog = json.loads((Path(__file__).parents[1]
                          / 'dev-docs/supported-source-monotonicity-catalog.json').read_text())
    row = next(row for row in catalog['graphs'] if row['witness'] == 'upper_left_normal_slide')
    if mutation == 'source':
        row['source_ids'] = ['unreviewed']
    elif mutation == 'equipment':
        row['equipment_routes'] = []
    elif mutation == 'condition':
        old = next(row for row in catalog['graphs'] if row['target'] == 'bomb_138_green'
                   and row['witness'] == 'upper_left_entry')
        old['graph_source_condition'] = ['SPARKY', 'Beam']
    elif mutation == 'provider':
        catalog['capability_providers']['bomb_138_green_normal_lower_slide'] = ['Normal', 'Spark']
    else:
        catalog['witnesses'] += 1
    with pytest.raises(AssertionError):
        catalog_before_green138(catalog)
