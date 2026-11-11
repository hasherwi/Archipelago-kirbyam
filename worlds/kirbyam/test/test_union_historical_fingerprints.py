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
