"""Independent permanent sources and directed retained Burning goal witnesses."""
import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from ..traversal import Position, SourcePolicy
from ..traversal_data import graph_items, room_traversal_graph, room_traversal_targets
from .test_metal_goal2 import simulate_burning_gating
from .test_traversal import policy

TARGETS = ('metal_176_goal2_drink', 'metal_557_goal1_tomato')
CASES = [(TARGETS[0], 'central_statues'), (TARGETS[0], 'cabbage592_statues'),
         (TARGETS[1], 'central_statues'), (TARGETS[1], 'rainbow190_statues')]
ROOT = Path(__file__).parents[1]


@pytest.mark.parametrize('target,witness', CASES)
@pytest.mark.parametrize('keys', [False, True])
def test_actual_source_minimal_guard_and_permission(
    monkeypatch: pytest.MonkeyPatch, target: str, witness: str, keys: bool
) -> None:
    simulate_burning_gating(monkeypatch)
    graph = room_traversal_graph(target, witness, keys)
    required = {'Burning Ability', 'Cabbage Cavern West - Hub Connection',
                ('Rainbow Route South' if '176' in target else 'Rainbow Route East') + ' - Hub Connection'}
    if keys and witness != 'cabbage592_statues':
        required.add('Cabbage Cavern - Area Key')
    resolver = SourcePolicy({'mode': 0})
    assert graph.evaluate(resolver, frozenset(required), True).reaches(next(iter(graph.required_targets)))
    for missing in required:
        assert not graph.evaluate(resolver, frozenset(required - {missing}), True).reaches(
            next(iter(graph.required_targets))), missing
    assert all(p.equipped == 'Normal' for p in graph.starts)
    assert graph.access_region
    assert not graph.requires_all_hub_switches
    assert all(p.node.startswith('hub_') or p.source_key.startswith('STATUE:') for p in graph.placements)


@pytest.mark.parametrize('target,witness', CASES)
@pytest.mark.parametrize('mode,statues,pool,weight,finite,retry', [
    (0, False, None, 0, True, True), (1, True, ['Burning'], 0, True, True),
    (1, True, ['Hammer'], 0, False, False),
    (2, True, ['Burning', 'Hammer'], 100, False, True),
    (2, True, ['Hammer'], 0, False, False),
])
def test_source_policy_and_documented_retry(
    target: str, witness: str, mode: int, statues: bool, pool: list[str] | None, weight: int, finite: bool, retry: bool
) -> None:
    graph = room_traversal_graph(target, witness)
    resolver = policy(mode, statues=statues, pool=pool, weight=weight)
    owned = graph_items(graph) | {'Burning Ability', 'Hammer Ability'}
    assert graph.evaluate(resolver, owned, True).reaches(next(iter(graph.required_targets))) is finite
    assert graph.evaluate(resolver, owned, True, allow_documented_retries=True).reaches(
        next(iter(graph.required_targets))) is retry


@pytest.mark.parametrize('target,witness', CASES)
def test_no_self_lock_recovery_export_or_wrong_attack(target: str, witness: str) -> None:
    graph = room_traversal_graph(target, witness)
    endpoint, = graph.required_targets
    final, = [r for r in graph.routes if r.target == endpoint]
    assert final.allowed_abilities == frozenset({'Burning'})
    assert not any(r.source == endpoint for r in graph.routes)
    resolver = SourcePolicy({'mode': 0})
    owned = graph_items(graph) | {'Burning Ability'}
    for broken in (replace(graph, placements=()),
                   replace(graph, placements=tuple(replace(p, node=endpoint) for p in graph.placements)),
                   replace(graph, starts=(Position(final.source),))):
        assert not broken.evaluate(resolver, owned, True).reaches(endpoint)
    # Every carried transition is directed and has no independently usable source.
    prefix = 'metal_' + ('176' if '176' in target else '557') + '_carried:'
    assert not any(p.node.startswith(prefix) for p in graph.placements)
    assert not any(r.target.startswith('hub_') and r.source.startswith(prefix) for r in graph.routes)


def test_original_graph_definitions_are_unchanged() -> None:
    from ..traversal_data import _room_catalog
    targets, _, _ = _room_catalog()
    current = {}
    for target in targets:
        for name, graph in target['graphs'].items():
            key = target['id'] + '/' + name
            assert key not in current
            current[key] = hashlib.sha256(json.dumps(graph, sort_keys=True).encode()).hexdigest()
    baseline = json.loads((ROOT / 'dev-docs/goal-burning-original-graph-fingerprints.json').read_text())
    assert len(baseline) == 108
    assert {'mini_321_right_lower/local', 'fuse_323/local'} <= set(baseline)
    assert set(baseline) | {target + "/" + witness for target, witness in CASES} <= set(current)
    assert {key: current[key] for key in baseline} == baseline
    for row in room_traversal_targets('metal'):
        if row['id'] in TARGETS:
            assert 'requires_guaranteed_source' not in row
            assert len(row['graphs']) == 3


@pytest.mark.parametrize('target,witness', CASES)
@pytest.mark.parametrize('keys', [False, True])
@pytest.mark.parametrize('retries', [False, True])
def test_frozen_reference_full_result(target: str, witness: str, keys: bool, retries: bool) -> None:
    from .traversal_reference import reachable_positions
    graph = room_traversal_graph(target, witness, keys)
    for resolver in (SourcePolicy({'mode': 0}), policy(2, statues=True, pool=['Burning', 'Hammer'], weight=100)):
        owned = graph_items(graph) | {'Burning Ability', 'Hammer Ability'}
        actual = graph.evaluate(resolver, owned, True, allow_documented_retries=retries)
        expected = reachable_positions(graph.nodes, graph.routes, graph.placements, graph.starts,
                                       resolver, owned, True, retries)
        assert actual == expected


@pytest.mark.parametrize('target', TARGETS)
def test_independent_source_access_cannot_bootstrap_chest(monkeypatch: pytest.MonkeyPatch, target: str) -> None:
    from types import SimpleNamespace
    from .. import traversal_rules as rules
    row = next(row for row in room_traversal_targets('metal') if row['id'] == target)
    monkeypatch.setattr(rules, 'extra_traversal_targets', lambda: (row,))
    # Every miniboss grants Hammer: the unchanged finite local witness cannot help.
    resolver = policy(1, minibosses=True, statues=False, pool=['Hammer'])
    chest = SimpleNamespace(access_rule=lambda state: state.base_rule)
    world = SimpleNamespace(player=1, _enemy_copy_ability_policy=resolver.policy,
                            _ability_gating_enabled=lambda: True, _area_keys_enabled=lambda: False,
                            options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=False)),
                            multiworld=SimpleNamespace(get_location=lambda *args: chest))
    rules.install_extra_traversal_rules(world)
    owned = set().union(*(graph_items(room_traversal_graph(target, witness)) for witness in row['graphs']))
    owned.add('Burning Ability')
    access = set()
    state = SimpleNamespace(base_rule=True, has=lambda item, player: item in owned,
                            can_reach_region=lambda region, player: region in access)
    assert not chest.access_rule(state)  # The permission/source item set does not grant source-region reachability.
    access.add('REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE')
    assert chest.access_rule(state)
    state.base_rule = False
    assert not chest.access_rule(state)


def test_native_evidence_hashes_are_pinned() -> None:
    rows = json.loads((ROOT / 'dev-docs/goal-burning-native-evidence-manifest.json').read_text())
    assert {r['filename']: r['sha256'] for r in rows} == {
        'ordinary-176-solo-burning-acceptance.json':
            'c3dfdd87c5902a8ffeda525f8f1a82ec7509078022c0e6d66a4d3475842584f7',
        'ordinary-194-176-burning-carrier-acceptance.json':
            '3c295062809d796ed907d8eb1c11fd7c277aa4cb90714b45bbf49c79525ae41f',
        'ordinary-592-hub-conditional-burning-prefix.json':
            'dadb3b23be04527e4bfd68d8af1d681d0c7182fff3de6bbb00cdc784745418cc',
        'carrier-reviewed-100.json': '0aeb5349cae89cbbd3a807c5721c380add7249ecc1592b2283bebba6398eaee0',
        'carrier-reviewed-500.json': 'e6a7f8cf9fa84021d8a415991a0a7ff83a5007ec99b70b1a34b726021cf2b940',
        'ordinary-557-carried-burning-combined-acceptance.json':
            'c8dbe9d1bb2f7a5ed0e556dd3cae4eae024a0129762501797cd2d33a101b1724',
    }


def test_original_compiled_graphs_unchanged_in_both_key_modes() -> None:
    import dataclasses

    def normalize(value: Any) -> Any:
        if dataclasses.is_dataclass(value) and not isinstance(value, type):
            return normalize(dataclasses.asdict(value))
        if isinstance(value, dict):
            return {k: normalize(v) for k, v in sorted(value.items())}
        if isinstance(value, (set, frozenset)):
            return sorted((normalize(v) for v in value), key=lambda x: json.dumps(x, sort_keys=True))
        if isinstance(value, (tuple, list)):
            return [normalize(v) for v in value]
        return value

    baseline = json.loads((ROOT / 'dev-docs/goal-burning-original-compiled-fingerprints.json').read_text())
    assert len(baseline) == 216
    assert all(target + '/local/' + str(keys) in baseline
               for target in ('mini_321_right_lower', 'fuse_323') for keys in (False, True))
    for key, expected in baseline.items():
        target, witness, keys = key.split('/')
        graph = room_traversal_graph(target, witness, keys == 'True')
        assert hashlib.sha256(json.dumps(normalize(graph), sort_keys=True).encode()).hexdigest() == expected, key


@pytest.mark.parametrize('target,rooms', [(TARGETS[0], (127, 504, 174, 173, 175, 176)),
                                          (TARGETS[1], (140, 108, 110, 554, 555, 556, 557))])
def test_exact_directed_carrier_and_atomic_boss_suffix(target: str, rooms: tuple[int, ...]) -> None:
    graph = room_traversal_graph(target, 'central_statues')
    prefix = 'metal_' + str(rooms[-1]) + '_carried:'
    nodes = {node.key: node.room for node in graph.nodes if node.key.startswith(prefix)}
    assert set(nodes) == {prefix + str(room) for room in rooms} | {prefix + 'chest'}
    assert tuple(nodes[prefix + str(room)] for room in rooms) == rooms
    route_pairs = {(route.source, route.target): route for route in graph.routes if route.source.startswith(prefix)}
    expected = {(prefix + str(a), prefix + str(b)) for a, b in zip(rooms, rooms[1:])}
    expected.add((prefix + str(rooms[-1]), prefix + 'chest'))
    assert set(route_pairs) == expected
    for (source, destination), route in route_pairs.items():
        if destination.endswith(':chest'):
            assert route.capability == 'metal' and route.water_state == 'dry'
            assert not route.room_transition
        else:
            assert route.room_transition and route.capability is None
        assert route.opens is None
