"""Finite native Sir Kibble is an OR alternative, never inventory equipment."""
from copy import deepcopy
from dataclasses import replace

import pytest

from ..traversal import Position, Route
from ..traversal_data import compile_room_graph, room_traversal_graph, room_traversal_targets, _validate_target
from ..traversal_rules import target_applies, graph_succeeds
from .test_traversal import policy

TARGET = 'switch_310_mustard_map'
WITNESS = 'hub4_kibble_cutter_entry'
PREFIX = TARGET + ':kibble_'
CAPABILITY = 'switch_310_kibble_cutter_roof_returns'
OWNED = frozenset({'Cutter Ability'})


def row():
    return next(r for r in room_traversal_targets('switch') if r['id'] == TARGET)


def graph(keys=False):
    return room_traversal_graph(TARGET, WITNESS, keys)


@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('keys', [False, True])
@pytest.mark.parametrize('mode,pool,weight,guaranteed', [
    (0, None, 0, True), (1, ['Cutter'], 0, True), (1, ['Beam'], 0, False),
    (2, ['Cutter'], 0, True), (2, ['Cutter', 'Beam'], 0, False),
    (2, ['Cutter'], 50, False), (2, ['Cutter'], 100, False)])
def test_actual_source_policy_and_permission(mode, pool, weight, guaranteed, gating, keys):
    resolver = policy(mode, pool=pool, weight=weight)
    g = graph(keys)
    assert target_applies(row(), resolver) is guaranteed
    assert graph_succeeds(g, resolver, OWNED, gating, retries=True) is guaranteed
    assert graph_succeeds(g, resolver, frozenset(), gating, retries=True) is (guaranteed and not gating)
    assert g.access_region == 'REGION_RAINBOW_ROUTE/ROOM_1_HUB_4'
    assert g.starts == (Position(PREFIX + 'hub4'),)
    source, = g.placements
    assert (source.node, source.identity, source.source_key, source.renewable, source.retry_evidence) == (
        PREFIX + 'source', '0x088C3FEC', 'SIR_KIBBLE', False, None)
    assert not any(r.opens for r in g.routes)


@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('mutation', ['absent', 'wrong', 'behind_barrier', 'self_gated', 'consumed', 'lost'])
def test_permission_cannot_manufacture_source_or_bootstrap_barrier(gating, mutation):
    g = graph()
    source, = g.placements
    if mutation == 'absent':g = replace(g, placements=())
    elif mutation == 'wrong':g = replace(g, placements=(replace(source, source_key='WADDLE_DOO'),))
    elif mutation == 'behind_barrier':g = replace(g, placements=(replace(source, node=PREFIX + 'crossed'),))
    elif mutation == 'self_gated':
        g = replace(g, routes=tuple(replace(r, required_equipment=frozenset({'Cutter'}))
                                   if r.target == source.node else r for r in g.routes))
    elif mutation == 'consumed':
        # Begin before the source with its one physical instance already spent.
        g = replace(g, starts=(Position(PREFIX + 'arrival', consumed=frozenset({source.identity})),))
    else:
        g = replace(g, routes=tuple(replace(r, loses_equipment=True) if r.target == PREFIX + 'roof' else r
                                   for r in g.routes))
    assert not graph_succeeds(g, policy(0), OWNED, gating, retries=True)


def test_loss_and_reacquisition_need_a_live_unconsumed_source():
    g = graph()
    source, = g.placements
    # Loss before first acquisition is harmless; loss after it cannot recycle the instance.
    g = replace(g, routes=tuple(replace(r, loses_equipment=True) if r.target == source.node else r
                               for r in g.routes))
    assert graph_succeeds(g, policy(0), OWNED, True, retries=False)
    g = replace(g, routes=(*g.routes, Route(PREFIX + 'roof', source.node, loses_equipment=True)))
    result = g.evaluate(policy(0), OWNED, True)
    assert any(p.node == source.node and p.equipped == 'Normal' and source.identity in p.consumed
               for p in result.positions)
    assert not any(p.node == source.node and p.equipped == 'Cutter' and not p.consumed
                   for p in result.positions)


@pytest.mark.parametrize('mutation', ['room', 'grant', 'inventory', 'persistent', 'water'])
def test_physical_binding_and_bounded_capability_cannot_widen(mutation):
    raw = deepcopy(row()['graphs'][WITNESS])
    if mutation == 'room':
        next(n for n in raw['nodes'] if n['id'] == PREFIX + 'source')['native_room'] = 533
    elif mutation == 'grant':raw['sources'][0]['source_key'] = 'TWISTER'
    elif mutation == 'inventory':raw['sources'][0]['inventory_id'] = 'missing'
    elif mutation == 'persistent':raw['routes'][4]['opens'] = 'permanent'
    else:raw['routes'][4]['water_state'] = 'swimming'
    with pytest.raises(ValueError):compile_room_graph(raw, {}, require_inventory=True)


@pytest.mark.parametrize('field,value', [('id', 'other'), ('native_room', 533),
                                        ('location', 'MAJOR_CHEST_RAINBOW_ROUTE')])
def test_two_source_applicability_remains_scoped(field, value):
    modified = deepcopy(row());modified[field] = value
    with pytest.raises(ValueError, match='target'):_validate_target(modified)


def test_native_evidence_matrix_and_controls():
    import json
    from pathlib import Path
    evidence = json.loads((Path(__file__).resolve().parents[1]
                           / 'dev-docs/mustard-map-kibble-acceptance.json').read_text())
    positives = evidence['positive']
    assert len(positives) == 66 and len(evidence['controls']) == 5
    vanilla = [r for r in positives if r['mode'] == 0 and r['hp'] == 1]
    assert {(r['gated'], r['enemy_health_percent']) for r in vanilla} == {
        (g, h) for g in (False, True) for h in evidence['health_percentages']}
    assert len(evidence['health_percentages']) == 28
    for r in positives:
        assert r['minimum_hp'] == r['hp'] and r['abilities'] == [0, 6]
        assert r['source_first_observation']['template'] == '0x88c3fec'
        assert r['source_last_seen_before_acquisition'] < r['cutter_acquired_frame'] == 2753
        assert r['switch_contacts'] and r['full_crossing']['player_xy'][0] > 454
        assert r['full_crossing']['gate_bounds'] == [-8, -32, 8, -20]
        assert r['full_crossing']['knight']['hp'] > 0
        assert r['native_chest39'] and r['major_check4'] and not r['native_map4']
        assert r['final']['ability'] == 6 and r['helper_rooms'] == [[101, 101, 101]]
        assert r['captured_client_messages'] == [{'cmd': 'LocationChecks', 'locations': [3960205]}]
    full_pool = [r for r in positives if len(r['allowed_abilities']) == 25 and r['mode'] == 1]
    assert len(full_pool) == 2 and {r['gated'] for r in full_pool} == {False, True}
    for r in evidence['controls']:
        assert not r['native_chest39'] and not r['major_check4'] and not r['captured_client_messages']
    for r in positives + evidence['controls']:
        assert r['runtime_write_frames'] in ([], [1085])
        assert r['runtime_write_count'] in (0, 8)
        for name in ('private_evidence_sha256', 'runtime_sha256', 'input_sha256', 'script_sha256'):
            assert len(r[name]) == 64
    for name, expected in evidence['preserved_graph_sha256'].items():
        import hashlib
        assert hashlib.sha256(json.dumps(row()['graphs'][name], sort_keys=True).encode()).hexdigest() == expected


@pytest.mark.parametrize('mutation', ['source', 'carry', 'condition'])
def test_historical_projection_rejects_semantic_changes(mutation):
    from .support.kibble310_history import before_kibble310
    raw = deepcopy(row())
    if mutation == 'source':raw['graphs'][WITNESS]['sources'][0]['renewable'] = True
    elif mutation == 'carry':raw['graphs'][WITNESS]['routes'][3]['required_equipment'] = ['Normal', 'Cutter']
    else:raw['requires_any_guaranteed_source'][1]['ability'] = 'Beam'
    with pytest.raises(AssertionError):before_kibble310(raw)
