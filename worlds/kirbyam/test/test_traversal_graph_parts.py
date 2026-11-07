"""Reusable graph fragments and unavailable physical-source safety contracts."""

from copy import deepcopy
from types import SimpleNamespace

import pytest

from ..data import data
from ..traversal import SourcePolicy
from ..traversal_data import compile_room_graph, has_graph_access, load_room_traversal, room_traversal_graph

HUB = 'REGION_RAINBOW_ROUTE/ROOM_1_HUB_1'


@pytest.fixture
def bundle():
    payload = {
        'version': 1, 'status': 'reviewed', 'nodes': [{'id': 'target', 'native_room': 190}],
        'routes': [{'from': 'source', 'to': 'target', 'capability': 'wheel_race', 'evidence': 'reviewed'}],
        'starts': ['source'], 'required_targets': ['target'], 'graph_parts': ['shared'],
        'access': {'region': HUB},
    }
    parts = {'shared': {
        'version': 1, 'status': 'reviewed',
        'nodes': [{'id': 'source', 'native_room': 190}, {'id': 'other', 'native_room': 191}],
        'routes': [{'from': 'source', 'to': 'other', 'items': ['Hub Connection'],
                    'area_key_items': ['Area Key'], 'evidence': 'reviewed'}],
        'source_sets': [{'id': 'physical', 'node': 'source'}],
    }}
    sources = {'physical': {'native_room': 190, 'sources': [
        {'id': 'physical-wheelie', 'source_key': 'WHEELIE', 'acquisition_evidence': 'reviewed'},
    ]}}
    return payload, sources, parts


def compile_bundle(bundle, **kwargs):
    payload, sources, parts = bundle
    return compile_room_graph(payload, sources, graph_parts=parts, **kwargs)


def test_fragment_resolves_sources_keeps_area_keys_and_does_not_mutate(bundle):
    original = deepcopy(bundle)
    for enabled in (True, False, True):
        graph = compile_bundle(bundle, area_keys=enabled)
        route = next(r for r in graph.routes if r.target == 'other')
        assert route.items == {'Hub Connection'} | ({'Area Key'} if enabled else set())
        assert [(p.identity, p.node, p.source_key) for p in graph.placements] == [
            ('physical-wheelie', 'source', 'WHEELIE'),
        ]
        assert graph.access_region == HUB
        assert graph.required_targets == {'target'}
        assert graph.evaluate(SourcePolicy({'mode': 0}), frozenset(), False).reaches('target')
    assert bundle == original


@pytest.mark.parametrize('references', [['unknown'], ['shared', 'shared'], 'shared', [3]])
def test_invalid_part_references(bundle, references):
    bundle[0]['graph_parts'] = references
    with pytest.raises(ValueError):
        compile_bundle(bundle)


@pytest.mark.parametrize('field,value', [
    ('version', 2), ('status', 'draft'), ('graph_parts', ['nested']),
    ('access', {'region': HUB}), ('starts', ['other']), ('required_targets', ['other']),
])
def test_fragment_cannot_override_graph_policy(bundle, field, value):
    bundle[2]['shared'][field] = value
    with pytest.raises(ValueError, match='Unsupported traversal graph part'):
        compile_bundle(bundle)


def test_node_collision_rejected(bundle):
    bundle[2]['shared']['nodes'].append({'id': 'target', 'native_room': 190})
    with pytest.raises(ValueError, match='Duplicate traversal compartment'):
        compile_bundle(bundle)


def test_fragment_source_native_room_mismatch_rejected(bundle):
    bundle[1]['physical']['native_room'] = 970
    with pytest.raises(ValueError, match='native room'):
        compile_bundle(bundle)


def test_catalog_returns_parts_and_validates_unused_parts(bundle):
    _, sources, parts = bundle
    rooms = {HUB: {'traversal': {'version': 1, 'source_sets': sources, 'graph_parts': parts}}}
    original = deepcopy(rooms)
    targets, loaded_sources, loaded_parts = load_room_traversal(rooms)
    assert targets == ()
    assert loaded_sources == sources
    assert loaded_parts == parts
    assert rooms == original
    parts['shared']['status'] = 'draft'
    with pytest.raises(ValueError, match='Unsupported traversal graph part'):
        load_room_traversal(rooms)


def test_duplicate_part_definitions_rejected(bundle):
    _, sources, parts = bundle
    rooms = {
        HUB: {'traversal': {'version': 1, 'source_sets': sources, 'graph_parts': parts}},
        'REGION_RAINBOW_ROUTE/ROOM_1_HUB_2': {'traversal': {'version': 1, 'graph_parts': deepcopy(parts)}},
    }
    with pytest.raises(ValueError, match='Duplicate traversal graph part'):
        load_room_traversal(rooms)


@pytest.mark.parametrize('reason', ['', '  ', None, True, []])
def test_unavailable_source_needs_concrete_reason(bundle, reason):
    bundle[1]['physical']['unavailable'] = reason
    with pytest.raises(ValueError, match='concrete reason'):
        compile_bundle(bundle)


def test_unavailable_source_blocks_all_inventory_and_region_access(bundle):
    bundle[1]['physical']['unavailable'] = 'Physical source absent in patched room'
    graph = compile_bundle(bundle)
    assert graph.unavailable_reason == 'Physical source absent in patched room'
    state = SimpleNamespace(can_reach_region=lambda *_: True)
    world = SimpleNamespace(player=1)
    assert not has_graph_access(world, state, graph)
    owned = frozenset({'Wheel Ability', 'Hub Connection', 'Area Key'})
    result = graph.evaluate(SourcePolicy({'mode': 0}), owned, False, allow_documented_retries=True)
    assert not result.positions
    assert not result.retry_assumptions


@pytest.mark.parametrize('mutation', ['endpoint', 'capability', 'source', 'proof', 'start'])
def test_unavailable_graph_still_validates_malformed_content(bundle, mutation):
    bundle[1]['physical']['unavailable'] = 'Physical source absent in patched room'
    if mutation == 'endpoint':
        bundle[0]['routes'][0]['to'] = 'missing'
    elif mutation == 'capability':
        bundle[0]['routes'][0]['capability'] = 'unknown'
    elif mutation == 'source':
        bundle[1]['physical']['sources'][0]['source_key'] = 'UNKNOWN'
    elif mutation == 'proof':
        bundle[0]['routes'][0]['evidence'] = ''
    else:
        bundle[0]['starts'] = ['missing']
    with pytest.raises(ValueError):
        compile_bundle(bundle)


def production_catalog():
    return load_room_traversal({name: {'traversal': region.traversal} for name, region in data.regions.items()})


def test_ordinary_hub_network_physical_census_and_directed_guards():
    _, sources, parts = production_catalog()
    payload = {'version': 1, 'status': 'reviewed', 'nodes': [], 'routes': [],
               'starts': ['hub_801'], 'required_targets': ['hub_890'], 'graph_parts': ['ordinary_hub_statues']}
    graph = compile_room_graph(payload, sources, graph_parts=parts)
    assert len(graph.placements) == 30
    assert len({p.identity for p in graph.placements}) == 30
    assert len({p.source_key for p in graph.placements}) == 15
    assert len(graph.routes) == 30
    portals = [
        (801, 190, 'Rainbow Route East'), (801, 191, 'Cabbage Cavern East'),
        (801, 192, 'Rainbow Route West'), (192, 193, 'Carrot Castle'),
        (801, 194, 'Rainbow Route South'), (194, 591, 'Cabbage Cavern Center'),
        (801, 290, 'Peppermint Palace East'), (290, 291, 'Peppermint Palace West'),
        (801, 590, 'Rainbow Route North'), (590, 390, 'Mustard Mountain'),
        (801, 490, 'Candy Constellation'), (801, 592, 'Cabbage Cavern West'),
        (592, 690, 'Radish Ruins'), (801, 790, 'Moonlight Mansion'), (191, 890, 'Olive Ocean'),
    ]
    assert {(r.source, r.target, r.items) for r in graph.routes} == {
        (f'hub_{a}', f'hub_{b}', frozenset({label + ' - Hub Connection'}))
        for left, right, label in portals for a, b in ((left, right), (right, left))
    }
    assert all(r.room_transition for r in graph.routes)
    assert all(p.renewable and p.retry_evidence for p in graph.placements)
    assert all(node.room != 970 for node in graph.nodes)
    keyed = compile_room_graph(payload, sources, graph_parts=parts, area_keys=True)
    forward = next(r for r in keyed.routes if (r.source, r.target) == ('hub_191', 'hub_890'))
    reverse = next(r for r in keyed.routes if (r.source, r.target) == ('hub_890', 'hub_191'))
    assert forward.items == {'Olive Ocean - Hub Connection', 'Olive Ocean - Area Key'}
    assert reverse.items == {'Olive Ocean - Hub Connection', 'Cabbage Cavern - Area Key'}


def test_every_970_source_reference_uses_copy_room_item_and_independent_region():
    from ..traversal_data import graph_items
    targets, sources, _ = production_catalog()
    assert sources['statues_970']['items'] == ['Copy Ability Room Access']
    assert 'unavailable' not in sources['statues_970']
    assert 'statues_970' in data.regions['REGION_COPY_ABILITY_ROOM/MAIN'].traversal['source_sets']
    checked = 0
    for row in targets:
        for witness, payload in row['graphs'].items():
            if any(ref['id'] == 'statues_970' for ref in payload.get('source_sets', [])):
                checked += 1
                graph = room_traversal_graph(row['id'], witness)
                assert graph.unavailable_reason is None
                assert graph.access_region == 'REGION_COPY_ABILITY_ROOM/MAIN'
                assert not graph.requires_all_hub_switches
                assert all('Copy Ability Room Access' in p.requirements for p in graph.placements)
                owned = graph_items(graph)
                assert all(graph.evaluate(SourcePolicy({'mode': 0}), owned, False).reaches(target)
                           for target in graph.required_targets)
                assert not any(graph.evaluate(SourcePolicy({'mode': 0}),
                                              owned - {'Copy Ability Room Access'}, False).reaches(target)
                               for target in graph.required_targets)
    assert checked == 2


def test_source_set_item_requirements_union_without_replacing_placement_items(bundle):
    bundle[1]['physical']['items'] = ['Room item']
    bundle[1]['physical']['sources'][0]['items'] = ['Source item']
    before = deepcopy(bundle)
    graph = compile_bundle(bundle)
    assert graph.placements[0].requirements == {'Room item', 'Source item'}
    policy = SourcePolicy({'mode': 0})
    assert graph.evaluate(policy, frozenset({'Room item', 'Source item'}), False).reaches('target')
    for owned in (frozenset(), frozenset({'Room item'}), frozenset({'Source item'})):
        assert not graph.evaluate(policy, owned, False).reaches('target')
    assert bundle == before
