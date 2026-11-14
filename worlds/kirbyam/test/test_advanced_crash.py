"""Crash routes are an opt-in logical assumption, never a source-policy rewrite."""
from types import SimpleNamespace

import pytest
from Options import Accessibility

from .. import traversal_rules as rules
from ..options import TraversalLogic
from ..traversal import CAPABILITY_ABILITIES
from ..traversal_data import room_traversal_graph
from .test_traversal import policy

ADVANCED = {('fuse_126', 'lower_entry_crash'),
            ('switch_533_room16', 'hub4_crash_entry'),
            ('switch_310_mustard_map', 'hub4_crash_entry')}


def test_default_standard_and_missing_option():
    assert TraversalLogic.default == TraversalLogic.option_standard
    assert not rules.advanced_traversal_enabled(SimpleNamespace(options=SimpleNamespace()))


def test_all_crash_capable_catalog_routes_explicitly_advanced():
    found = set()
    for row in rules.extra_traversal_targets():
        for name, payload in row['graphs'].items():
            graph = room_traversal_graph(row['id'], name)
            crash = any(
                (route.capability is not None
                 and 'Crash' in CAPABILITY_ABILITIES[route.capability]
                 and (route.allowed_abilities is None or 'Crash' in route.allowed_abilities))
                or 'Crash' in (route.required_equipment or ())
                for route in graph.routes)
            if crash:
                found.add((row['id'], name))
                assert name in row.get('advanced_graphs', ())
                assert graph not in rules.target_graphs(row, False)
            if name in row.get('advanced_graphs', ()):
                assert (row['id'], name) in ADVANCED
    assert found == ADVANCED


@pytest.mark.parametrize('target_id,witness', sorted(ADVANCED))
@pytest.mark.parametrize('advanced', [False, True])
def test_static_and_installed_rules_agree_without_fallback_leak(monkeypatch, target_id, witness, advanced):
    source = policy(1, pool=['Crash'])
    original = next(row for row in rules.extra_traversal_targets() if row['id'] == target_id)
    # Isolate the actual catalog Crash witness; no invented routes or source grants.
    row = dict(original, graphs={witness: original['graphs'][witness]})
    monkeypatch.setattr(rules, 'extra_traversal_targets', lambda: (row,))
    assert rules.target_applies(row, source)
    assert rules.static_extra_witness(source, advanced=advanced) is advanced
    target = SimpleNamespace(access_rule=lambda state: True)
    options = SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=False),
                              traversal_logic=TraversalLogic(int(advanced)),
                              accessibility=Accessibility(Accessibility.option_minimal))
    world = SimpleNamespace(player=1, options=options, _enemy_copy_ability_policy=source.policy,
                            _ability_gating_enabled=lambda: False, _area_keys_enabled=lambda: False,
                            multiworld=SimpleNamespace(get_location=lambda *args: target,
                              get_entrance=lambda *args: target, get_region=lambda *args: object(),
                              register_indirect_condition=lambda *args: None))
    rules.install_extra_traversal_rules(world)
    state = SimpleNamespace(has=lambda *args: True, can_reach_region=lambda *args: True)
    assert target.access_rule(state) is advanced
    # Under full accessibility the same unsupported assignment fails closed early.
    world.options.accessibility = Accessibility(Accessibility.option_full)
    if not advanced:
        with pytest.raises(ValueError, match='No reviewed source witness'):
            rules.install_extra_traversal_rules(world)


def test_live_random_pool_not_rewritten_into_guaranteed_fire():
    source = policy(2, pool=['Crash', 'Fire'])
    before = source.grant('HOT_HEAD', lambda _: True)
    for row in rules.extra_traversal_targets():
        rules.target_graphs(row, False, advanced=False)
    after = source.grant('HOT_HEAD', lambda _: True)
    assert after == before
    assert not after.guaranteed
    assert after.abilities == frozenset({'Crash', 'Fire'})


def test_crash_progression_requires_advanced():
    world = SimpleNamespace(options=SimpleNamespace(traversal_logic=TraversalLogic(0)),
                            _enemy_copy_ability_policy=policy(1, pool=['Crash']).policy,
                            _ability_gating_enabled=lambda: True)
    assert not rules.mustard_crash_is_progression(world)
    world.options.traversal_logic = TraversalLogic(1)
    assert rules.mustard_crash_is_progression(world)


@pytest.mark.parametrize('advanced', [False, True])
def test_assignment_resampling_uses_selected_logic(monkeypatch, advanced):
    from .. import peg_traversal, wheel_traversal
    first = dict(policy(1).policy, seed=1)
    second = dict(first, seed=2)
    monkeypatch.setattr(wheel_traversal, 'static_wheel_witness', lambda policy: True)
    monkeypatch.setattr(peg_traversal, '_assignment_has_witness', lambda row, policy: True)
    seen = []
    def witness(policy, *, advanced=False):
        seen.append((policy.policy['seed'], advanced))
        return advanced or policy.policy['seed'] == 2
    monkeypatch.setattr(rules, 'static_extra_witness', witness)
    chosen = peg_traversal.validate_peg_assignment(first, lambda: second, False,
                                                  max_attempts=2, advanced=advanced)
    assert chosen is (first if advanced else second)
    assert seen == ([(1, True)] if advanced else [(1, False), (2, False)])


def test_standard_preserves_every_non_crash_witness():
    for row in rules.extra_traversal_targets():
        standard = rules.target_graphs(row, False)
        assert len(standard) == len(row['graphs']) - len(row.get('advanced_graphs', ()))
        for name in row['graphs']:
            if name not in row.get('advanced_graphs', ()):
                assert room_traversal_graph(row['id'], name) in standard


@pytest.mark.parametrize('advanced', [False, True])
@pytest.mark.parametrize('mode', [0, 1, 2])
def test_real_world_option_survives_generation_and_slot_data(mode, advanced):
    from .test_mini_traversal import make_world
    world = make_world(mode, 1, traversal_logic=int(advanced))
    assert rules.advanced_traversal_enabled(world) is advanced
    assert world.fill_slot_data()['traversal_logic'] == int(advanced)


def test_invalid_advanced_graph_marker_rejected():
    from ..traversal_data import _validate_graphs
    row = {'id': 'bad', 'graphs': {'local': {}}, 'advanced_graphs': ['typo']}
    with pytest.raises(ValueError, match='Invalid advanced traversal graph list'):
        _validate_graphs(row, {}, {})


def test_historical_projection_only_removes_exact_logic_annotations():
    from copy import deepcopy
    from .support.advanced_crash_history import before_advanced_crash, MARKERS
    for row in rules.extra_traversal_targets():
        original = deepcopy(row)
        projected = before_advanced_crash(row)
        if row['id'] in MARKERS:
            projected['advanced_graphs'] = MARKERS[row['id']]
        assert projected == row == original
    for marker in ([], ['unknown'], ['hub4_crash_entry', 'hub4_crash_entry']):
        with pytest.raises(AssertionError):
            before_advanced_crash({'id': 'switch_533_room16', 'advanced_graphs': marker})
    with pytest.raises(AssertionError):
        before_advanced_crash({'id': 'unreviewed', 'advanced_graphs': []})
