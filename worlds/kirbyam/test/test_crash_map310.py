"""Only the complete, guaranteed-Twister Crash carry gates the native310 map."""

from dataclasses import replace
from types import SimpleNamespace

from .test_beam538_evidence import historical_client_before_ice_start

import pytest
from BaseClasses import CollectionState, ItemClassification
from Options import Accessibility

from .support.source_policy import set_rule_test_policy
from .. import traversal_rules as rules
from ..data import data
from ..traversal_data import room_traversal_graph, room_traversal_targets
from .test_mini_traversal import make_world as _make_world
from .test_traversal import policy


def make_world(*args, **kwargs):
    """Historical Crash route fixtures explicitly select advanced traversal."""
    return _make_world(*args, traversal_logic=1, **kwargs)

TARGET = 'switch_310_mustard_map'
OWNER = 'REGION_MUSTARD_MOUNTAIN/ROOM_4_CHEST'
UPSTREAM = 'REGION_RAINBOW_ROUTE/ROOM_1_HUB_4'
SOURCE_ROOM = 'REGION_RAINBOW_ROUTE/ROOM_1_34'
LOCATION = 'MAJOR_CHEST_MUSTARD_MOUNTAIN'
POLICIES = [
    (0, None, 0, False),  # Native Twister is Tornado, not Crash.
    (1, ['Crash'], 0, True), (1, ['Bomb'], 0, False),
    (2, ['Crash'], 0, True), (2, ['Crash', 'Bomb'], 0, False),
    (2, ['Crash'], 50, False), (2, ['Crash'], 100, False),
]


def target_row():
    return next(row for row in room_traversal_targets('switch') if row['id'] == TARGET)


@pytest.mark.parametrize('mode,pool,weight,applies', POLICIES)
@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('area_keys', [False, True])
@pytest.mark.parametrize('statues', [False, True])
def test_map_conditional_policy_and_independent_entry_matrix(
        monkeypatch, mode, pool, weight, applies, gating, area_keys, statues):
    resolver = policy(mode, pool=pool, weight=weight, statues=statues, minny=False)
    row = target_row()
    monkeypatch.setattr(rules, 'extra_traversal_targets', lambda: (row,))
    assert rules.target_applies(row, resolver) is applies
    assert rules.static_extra_witness(resolver, advanced=True)

    def original_rule(state):
        return state.base_rule

    target = SimpleNamespace(access_rule=original_rule)
    looked_up = []

    def get_location(name, player):
        looked_up.append((name, player))
        return target

    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy=resolver.policy,
        _ability_gating_enabled=lambda: gating, _area_keys_enabled=lambda: area_keys,
        options=SimpleNamespace(traversal_logic=SimpleNamespace(value=1), ability_randomization_statues=SimpleNamespace(value=statues),
                                accessibility=Accessibility(Accessibility.option_full)),
        multiworld=SimpleNamespace(get_location=get_location),
    )
    rules.install_extra_traversal_rules(world)
    assert looked_up == ([(data.locations[LOCATION].label, 1)] if applies else [])
    if not applies:
        assert target.access_rule is original_rule
    owned = set()
    state = SimpleNamespace(base_rule=True, has=lambda item, player: item in owned)
    # Reaching either the target room or the source room does not prove this approach.
    state.can_reach_region = lambda name, player: name in {OWNER, SOURCE_ROOM}
    assert target.access_rule(state) is (not applies)
    owned.add('Crash Ability')
    assert target.access_rule(state) is (not applies)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    assert target.access_rule(state)
    owned.clear()
    assert target.access_rule(state) is (not applies or not gating)
    state.base_rule = False
    assert not target.access_rule(state)


@pytest.mark.parametrize('mode,pool,weight,applies', POLICIES)
@pytest.mark.parametrize('gating', [0, 1])
@pytest.mark.parametrize('area_keys', [0, 1])
@pytest.mark.parametrize('statues', [0, 1])
@pytest.mark.parametrize('room_sanity', [0, 1])
@pytest.mark.parametrize('start_with_all_maps', [0, 1])
def test_actual_world_wires_only_map_and_preserves_crash_progression(
        monkeypatch, mode, pool, weight, applies, gating, area_keys, statues, room_sanity, start_with_all_maps):
    resolver = policy(mode, pool=pool, weight=weight, statues=statues, minny=False)
    # A controlled production policy exercises the real generate/create/set-rules
    # lifecycle. Minimal accessibility keeps unrelated finite-source gates from
    # rejecting these deliberately restricted assignment pools.
    set_rule_test_policy(monkeypatch, lambda *args, **kwargs: resolver.policy)
    world = make_world(mode, gating, accessibility='minimal', area_keys=area_keys,
                       ability_randomization_statues=statues, room_sanity=room_sanity,
                       ability_randomization_no_ability_weight=weight, start_with_all_maps=start_with_all_maps)
    target = world.multiworld.get_location(data.locations[LOCATION].label, 1)
    assert target.parent_region.name == OWNER
    state = CollectionState(world.multiworld)
    state.can_reach_region = lambda name, player: name == UPSTREAM
    incoming = world.multiworld.get_entrance(f'{SOURCE_ROOM} -> {OWNER}', 1)
    assert incoming.access_rule(state) is (not area_keys)
    state.collect(world.create_item('Mustard Mountain - Area Key'), prevent_sweep=True)
    assert incoming.access_rule(state)
    assert target.access_rule(state) is (not applies or not gating)
    item = world.create_item('Crash Ability')
    assert item.classification == (ItemClassification.progression if gating and applies
                                   else ItemClassification.useful)
    state.collect(item, prevent_sweep=True)
    assert state.has('Crash Ability', 1) is bool(gating and applies)
    assert target.access_rule(state)
    if gating and applies:
        state.remove(item)
        assert not target.access_rule(state)
        state.collect(item, prevent_sweep=True)
    for accessible in (OWNER, SOURCE_ROOM):
        state.can_reach_region = lambda name, player, accessible=accessible: name == accessible
        assert target.access_rule(state) is (not applies)
        assert world.multiworld.get_entrance(f'{OWNER} -> {SOURCE_ROOM}', 1).access_rule(state)
        assert world.multiworld.get_entrance(f'{SOURCE_ROOM} -> {OWNER}', 1).access_rule(state)
        # RoomSanity is normalized into its own sink, never this chest rule.
        owner = world.multiworld.get_region(OWNER, 1)
        room_checks = [location for location in world.multiworld.get_locations(1)
                       if location.parent_region.name.startswith(OWNER) and location is not target]
        assert len(room_checks) == room_sanity
        assert all(location.access_rule(state) for location in room_checks)
        assert all(exit.access_rule(state) for exit in owner.exits)


@pytest.mark.parametrize('area_keys', [False, True])
@pytest.mark.parametrize('gating', [False, True])
def test_map_graph_requires_finite_source_and_carries_equipment(area_keys, gating):
    row = target_row()
    assert row['region'] == OWNER and row['location'] == LOCATION and not row.get('exit')
    graph = room_traversal_graph(TARGET, 'hub4_crash_entry', area_keys)
    assert graph.access_region == UPSTREAM
    assert len(graph.starts) == 1 and graph.starts[0].equipped == 'Normal'
    native_rooms = {node.key: node.room for node in graph.nodes}
    assert native_rooms[graph.starts[0].node] == 590
    source, = graph.placements
    assert native_rooms[source.node] == 534
    assert (source.identity, source.source_key, source.renewable) == ('0x088B59B4', 'TWISTER', False)
    assert not source.retry_evidence
    assert [(native_rooms[route.source], native_rooms[route.target]) for route in graph.routes
            if route.room_transition] == [(590, 534), (534, 310)]
    assert [route.capability for route in graph.routes if route.capability] == ['switch_310_crash_viewport']
    assert all(route.opens is None for route in graph.routes)
    resolver = policy(1, pool=['Crash'], minny=False)
    owned = frozenset({'Crash Ability'})
    target, = graph.required_targets
    result = graph.evaluate(resolver, owned, gating)
    assert result.reaches(target)
    assert any(position.node == target and position.equipped == 'Normal' for position in result.positions)
    assert not result.retry_assumptions
    assert graph.evaluate(resolver, frozenset(), gating).reaches(target) is (not gating)
    assert not replace(graph, placements=()).evaluate(resolver, owned, gating).reaches(target)
    # Inventory cannot replace the acquisition leg, even with the real placement retained.
    without_acquisition = replace(graph, routes=tuple(route for route in graph.routes if route.target != source.node))
    assert not without_acquisition.evaluate(resolver, owned, gating).reaches(target)
    assert not graph.evaluate(policy(), owned, gating).reaches(target)
    bomb_result = graph.evaluate(policy(1, pool=['Bomb']), frozenset({'Crash Ability', 'Bomb Ability'}), gating)
    assert not bomb_result.reaches(target)


@pytest.mark.parametrize('pool,weight', [(['Crash', 'Bomb'], 0), (['Crash'], 50), (['Crash'], 100)])
@pytest.mark.parametrize('retries', [False, True])
def test_map_finite_random_source_has_no_retry_or_selected_outcome(pool, weight, retries):
    graph = room_traversal_graph(TARGET, 'hub4_crash_entry')
    target, = graph.required_targets
    result = graph.evaluate(policy(2, pool=pool, weight=weight), frozenset({'Crash Ability', 'Bomb Ability'}),
                            True, allow_documented_retries=retries)
    assert not result.reaches(target)
    assert not result.retry_assumptions


def test_preserves_ufo_graph_and_exact_target_scope():
    import hashlib
    import json
    from copy import deepcopy
    from ..traversal_data import _validate_target
    row = target_row()
    assert set(row['graphs']) == {'hub4_ufo_entry', 'hub4_crash_entry', 'hub4_cupid_entry', 'hub4_cutter_entry'}
    assert hashlib.sha256(json.dumps(row['graphs']['hub4_ufo_entry'], sort_keys=True).encode()).hexdigest() == (
        '035e9268c78e83bbf68f546ee602d5e7fed5e936e782abe81eb9123c98919671')
    assert room_traversal_graph(TARGET, 'hub4_crash_entry').required_guaranteed_source == ('TWISTER', 'Crash')
    for key, wrong in [('id', 'switch_other'), ('native_room', 533), ('kind', 'block'),
                       ('region', SOURCE_ROOM), ('location', 'MAJOR_CHEST_RAINBOW_ROUTE')]:
        altered = deepcopy(row)
        altered[key] = wrong
        with pytest.raises(ValueError, match='reviewed chest target'):
            _validate_target(altered)


def test_mixed_pool_inventory_filter_and_persistent_credit_are_rejected():
    from copy import deepcopy
    from ..traversal import compile_traversal_graph
    graph = room_traversal_graph(TARGET, 'hub4_crash_entry')
    for owned in (frozenset({'Crash Ability'}), frozenset({'Crash Ability', 'UFO Ability'})):
        for gating in (False, True):
            assert not graph.evaluate(policy(2, pool=['Crash', 'UFO']), owned, gating,
                                      allow_documented_retries=True).positions
    raw = deepcopy(target_row()['graphs']['hub4_crash_entry'])
    next(r for r in raw['routes'] if r.get('capability'))['opens'] = 'switch'
    with pytest.raises(ValueError, match='persistent'):
        compile_traversal_graph(raw)


def test_consumption_and_normal_continuation():
    from ..traversal import Position
    graph = room_traversal_graph(TARGET, 'hub4_crash_entry')
    resolver = policy(1, pool=['Crash'])
    source, = graph.placements
    owned = frozenset({'Crash Ability'})
    result = graph.evaluate(resolver, owned, True)
    for node in ('switch_310_mustard_map:crash_crossed', 'switch_310_mustard_map:crash_chest'):
        positions = [p for p in result.positions if p.node == node]
        assert positions and all(p.equipped == 'Normal' and not p.opened for p in positions)
    spent = replace(graph, starts=(Position(source.node, 'Normal', consumed=frozenset({source.identity})),))
    assert not spent.evaluate(resolver, owned, True).reaches(next(iter(graph.required_targets)))
    continuation = graph.routes[-1]
    assert continuation.required_equipment == frozenset({'Normal'})


def test_twister_promotion_requires_actual_location():
    from ..traversal import SourcePolicy
    import json
    from pathlib import Path
    raw = json.loads((Path(__file__).resolve().parents[1] /
                      'dev-docs/mustard-map-crash-acceptance.json').read_text())['source_policy']
    resolver = SourcePolicy(raw)
    assert resolver.grant('TWISTER', lambda _: True).guaranteed == frozenset({'Crash'})
    assert all(resolver.grant(s, lambda _: True).guaranteed != frozenset({'Crash'})
               for s in ('FOLEY', 'HOT_HEAD'))
    world = SimpleNamespace(options=SimpleNamespace(traversal_logic=SimpleNamespace(value=1)), player=1, _enemy_copy_ability_policy=raw, _ability_gating_enabled=lambda: True,
                            multiworld=SimpleNamespace(get_location=lambda *args: object()))
    assert rules.mustard_crash_is_progression(world)

    def absent(*args):
        raise KeyError('disabled')

    world.multiworld.get_location = absent
    assert not rules.mustard_crash_is_progression(world)


@pytest.mark.parametrize('gating,area_keys,health,maps', [(1, 0, 100, 0), (1, 1, 500, 1), (0, 0, 100, 1)])
def test_normal_full_pool_seed15_one_hp_fill(tmp_path, gating, area_keys, health, maps):
    from ..traversal import SourcePolicy
    from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive
    player = tmp_path / 'player.yaml'
    player.write_text('name: Crash310\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n'
                      '  traversal_logic: advanced\n  ability_randomization_mode: 1\n  minimum_health: 1\n  maximum_health: 1\n'
                      f'  ability_gating: {gating}\n  area_keys: {area_keys}\n'
                      f'  enemy_health_multiplier: {health}\n  start_with_all_maps: {maps}\n', encoding='utf-8')
    archive = generate_archive_from_fixture(player, tmp_path / 'out', seed=15)
    raw = load_multidata_from_archive(archive)['slot_data'][1]['enemy_copy_ability_policy']
    assert len(raw['allowed_abilities']) == 25
    assert SourcePolicy(raw).grant('TWISTER', lambda _: True).guaranteed == frozenset({'Crash'})


def lf_text_sha256(raw):
    """Hash tracked UTF-8 source as LF text; private evidence hashes stay raw."""
    import hashlib
    text = raw.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def test_tracked_client_source_hash_accepts_crlf_but_rejects_content_changes():
    import hashlib
    lf = 'def client_poll():\n    """Kirby → AP."""\n    return [3960205]\n'.encode('utf-8')
    crlf = lf.replace(b'\n', b'\r\n')
    assert lf_text_sha256(crlf) == lf_text_sha256(lf) == hashlib.sha256(lf).hexdigest()
    assert lf_text_sha256(crlf + b' ') != lf_text_sha256(lf)


def test_public_evidence_and_single_capability_owner():
    import json
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    evidence = json.loads((root / 'dev-docs/mustard-map-crash-acceptance.json').read_text())
    assert evidence['source_abi'] == {'table_offset': '0x3518EE', 'source_bit': 28}
    assert evidence['generation_seed'] == 15
    assert evidence['private_manifest_sha256'] == '4f620650a0a67621b70365eac6bbc8155565beb30fed223445feeb5f693675d4'
    runs = evidence['runs']
    positives = [r for n, r in runs.items() if n.endswith('positive')]
    assert len(positives) == 4
    for run in positives:
        assert run['hp_min'] == run['hp_max'] in (1, 6)
        assert run['events']['first_damage'] is None
        assert run['final']['chest39'] and run['final']['mustard_map_check']
        assert not run['final']['native_map_ownership']
        assert run['events']['consumed_to_normal'] == 2960
    for name, run in runs.items():
        if name.endswith('no-trigger'):
            assert run['events']['first_damage'] == 2847
            assert run['events']['switch_hit'] is None
        elif name.endswith('short'):
            assert run['final']['frame'] == 2846 and run['hp_min'] == 1
        elif name.endswith('offscreen'):
            assert run['hp_min'] == 1 and run['events']['switch_hit'] is None
            assert run['final']['ability'] == 0
    client = evidence['client_poll']
    assert client['no_server_transmission']
    # The native record keeps its historical client; the union adopts main's client.
    assert client['client_sha256'] == 'b32450357cfbd9486ce71ad1c5dfd9000e5b0aca770422722e62a235408251f9'
    union = json.loads((root / 'dev-docs/main-ranged-union-catalog.json').read_text())
    expected = union['adopted_main_source_sha256']['client.py']
    raw = (root / 'client.py').read_bytes()
    assert lf_text_sha256(historical_client_before_ice_start(raw, expected)) == expected
    with pytest.raises(AssertionError):
        historical_client_before_ice_start(raw + b' ', expected)
    assert client['runs']['positive']['captured_client_messages'] == [{'cmd': 'LocationChecks', 'locations': [3960205]}]
    owners = [(row['id'], key) for row in room_traversal_targets('switch') for key, g in row['graphs'].items()
              if any(r.get('capability') == 'switch_310_crash_viewport' for r in g['routes'])]
    assert owners == [(TARGET, 'hub4_crash_entry')]
