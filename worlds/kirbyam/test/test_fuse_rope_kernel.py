"""Fuse/rope providers and destructive equipment effects stay in the kernel."""

import pytest

from ..traversal import (
    CAPABILITY_ABILITIES, CAPABILITY_CONSUMED_ABILITIES, Node, Placement, Position, Route, SourcePolicy,
    compile_traversal_graph, reachable_positions,
)

FUSE = frozenset({'Fire', 'Burning', 'Bomb', 'Laser', 'UFO', 'Master', 'Hammer', 'Crash'})
ROPE = frozenset({'Cutter', 'Sword', 'Cupid', 'Smash', 'Master'})


def run(route, equipped, opened=frozenset()):
    return reachable_positions(
        [Node('pre', 108), Node('post', 108)], [route], [],
        [Position('pre', equipped, opened)], SourcePolicy({'mode': 0}), gating=False,
    )


def fuse_route():
    return Route('pre', 'post', 'fuse')


def test_provider_sets_are_exact():
    assert CAPABILITY_ABILITIES['fuse'] == FUSE
    assert CAPABILITY_ABILITIES['rope'] == ROPE


@pytest.mark.parametrize('capability,providers', [('fuse', FUSE), ('rope', ROPE)])
@pytest.mark.parametrize('ability', sorted(FUSE | ROPE | {'Normal', 'Stone', 'Mini', 'Wheel'}))
def test_equipment_provider_membership(capability, providers, ability):
    route = Route('pre', 'post', capability)
    assert run(route, ability).reaches('post') == (ability in providers)


def test_crash_consumed_only_when_lighting():
    route = fuse_route()
    result = run(route, 'Crash')
    arrivals = [p for p in result.positions if p.node == 'post']
    assert arrivals
    assert all(p.equipped == 'Normal' and not p.opened for p in arrivals)


@pytest.mark.parametrize('ability', sorted(FUSE - {'Crash'}))
def test_lighting_preserves_nonconsumed_providers(ability):
    assert any(p.node == 'post' and p.equipped == ability for p in run(fuse_route(), ability).positions)


def test_consumption_transforms_each_uncertain_outcome():
    result = run(fuse_route(), frozenset({'Crash', 'Fire'}))
    assert any(p.node == 'post' and p.equipped == frozenset({'Normal', 'Fire'}) for p in result.positions)
    assert not any(p.node == 'post' and 'Crash' in p.equipment_outcomes for p in result.positions)


def test_one_crash_cannot_light_two_fuses():
    routes = [fuse_route(), Route('post', 'end', 'fuse')]
    result = reachable_positions(
        [Node('pre', 108), Node('post', 108), Node('end', 108)], routes, [],
        [Position('pre', 'Crash')], SourcePolicy({'mode': 0}), gating=False,
    )
    assert result.reaches('post')
    assert not result.reaches('end')


@pytest.fixture
def payload():
    return {
        'version': 1, 'status': 'reviewed',
        'nodes': [{'id': 'pre', 'native_room': 108}, {'id': 'post', 'native_room': 108}],
        'routes': [{'from': 'pre', 'to': 'post', 'capability': 'fuse',
                    'evidence': 'audited fuse effect'}],
        'sources': [], 'starts': ['pre'], 'required_targets': ['post'],
    }


def test_consumption_policy_only_names_known_providers():
    assert CAPABILITY_CONSUMED_ABILITIES == {
        'fuse': frozenset({'Crash'}), 'switch_533_crash_viewport': frozenset({'Crash'}),
        'switch_310_crash_viewport': frozenset({'Crash'}),
        'switch_533_magic_meta_knight': frozenset({'Magic'}),
    }
    for capability, spent in CAPABILITY_CONSUMED_ABILITIES.items():
        assert spent <= CAPABILITY_ABILITIES[capability]


def test_compiled_fuse_uses_shared_consumption_policy(payload):
    graph = compile_traversal_graph(payload)
    assert graph.routes[0].capability == 'fuse'
    result = run(graph.routes[0], 'Crash')
    assert result.reaches('post')
    assert all(p.equipped == 'Normal' for p in result.positions if p.node == 'post')


@pytest.mark.parametrize('field', ['consumed_abilities', 'consume_ability', 'unknown_effect'])
def test_route_cannot_silently_override_kernel_effects(payload, field):
    payload['routes'][0][field] = ['Crash']
    with pytest.raises(ValueError, match='Unknown traversal route'):
        compile_traversal_graph(payload)


@pytest.mark.parametrize('capability', ['unknown', 'Fuse'])
def test_unknown_capabilities_fail_closed(payload, capability):
    payload['routes'][0]['capability'] = capability
    with pytest.raises(ValueError):
        compile_traversal_graph(payload)


@pytest.mark.parametrize('allowed', [[], ['UNKNOWN'], ['Stone'], ['Crash', 'Stone']])
def test_compiled_provider_narrowing_fails_closed(payload, allowed):
    payload['routes'][0]['allowed_abilities'] = allowed
    with pytest.raises(ValueError):
        compile_traversal_graph(payload)


@pytest.mark.parametrize('allowed', [frozenset(), frozenset({'UNKNOWN'}), frozenset({'Stone'})])
def test_direct_route_provider_narrowing_fails_closed(allowed):
    with pytest.raises(ValueError):
        run(Route('pre', 'post', 'fuse', allowed_abilities=allowed), 'Crash')


def test_inventory_permission_without_source_is_not_equipment():
    result = reachable_positions(
        [Node('pre', 108), Node('post', 108)], [fuse_route()], [],
        [Position('pre')], SourcePolicy({'mode': 0}), frozenset({'Crash Ability'}), True,
    )
    assert not result.reaches('post')


def test_fuse_does_not_make_one_shot_source_renewable():
    from ..traversal import Grant

    class CrashPolicy:
        def grant(self, key, permitted):
            return Grant(frozenset({'Crash'}))

    result = reachable_positions(
        [Node('pre', 108), Node('post', 108), Node('end', 108)],
        [fuse_route(), Route('post', 'pre'), Route('post', 'end', 'fuse')],
        [Placement('pre', 'CRASH_TEST', identity='one_shot')],
        [Position('pre')], CrashPolicy(), gating=False,
    )
    assert result.reaches('post')
    assert not result.reaches('end')
    assert all('one_shot' in p.consumed for p in result.positions if p.node == 'post')


def test_mixed_grant_cannot_use_nonuniversal_provider():
    assert not run(fuse_route(), frozenset({'Crash', 'Stone'})).reaches('post')


@pytest.mark.parametrize('opens', ['fuse_a', ''])
def test_compiler_rejects_persistent_fuse_state(payload, opens):
    payload['routes'][0]['opens'] = opens
    with pytest.raises(ValueError, match='Timed fuse ignition cannot have a persistent opens event'):
        compile_traversal_graph(payload)


@pytest.mark.parametrize('opens', ['fuse_a', ''])
def test_direct_kernel_rejects_persistent_fuse_state(opens):
    with pytest.raises(ValueError, match='Timed fuse ignition cannot have a persistent opens event'):
        run(Route('pre', 'post', 'fuse', opens), 'Crash', frozenset({opens}))


def test_opened_other_barrier_preserves_crash():
    result = run(Route('pre', 'post', 'peg', 'peg_a'), 'Crash', frozenset({'peg_a'}))
    assert any(p.node == 'post' and p.equipped == 'Crash' for p in result.positions)


def test_unrelated_opened_event_cannot_bypass_fuse_ignition():
    result = run(fuse_route(), 'Normal', frozenset({'fuse_a'}))
    assert not result.reaches('post')
    crash = run(fuse_route(), 'Crash', frozenset({'fuse_a'}))
    assert crash.reaches('post')
    assert all(p.equipped == 'Normal' for p in crash.positions if p.node == 'post')
