"""Water-state attack dispatch and consumable frozen-enemy route witnesses."""

from dataclasses import replace

import pytest

from ..enemy_ability_data import ABILITY_NAME_TO_ID
from ..traversal import (
    CAPABILITY_ABILITIES, UNDERWATER_ATTACK_ABILITIES, Node, Placement, Position,
    Route, SourcePolicy, attack_provider, reachable_positions,
)
from .test_traversal import policy


NODES = (Node('launch', 825), Node('chest', 825), Node('return', 824))
DEE_ID = '0x088CD318'
DEE = Placement('launch', 'WADDLE_DEE', identity=DEE_ID)
FROZEN = Route('launch', 'chest', 'frozen_enemy_hit', uses_object=DEE_ID)


def run(route, sources=(), ability='Normal', owned=frozenset(), resolver=None, retries=False):
    return reachable_positions(NODES, [route], sources, [Position('launch', ability)],
                               resolver or SourcePolicy({'mode': 0}), owned, True, retries)


@pytest.mark.parametrize('ability', list(ABILITY_NAME_TO_ID))
def test_swimming_attack_dispatch_matches_native_ability_table(ability):
    assert attack_provider(ability, 'dry') == ability
    assert attack_provider(ability, 'swimming') == (
        None if ability == 'Mini' else ability if ability in UNDERWATER_ATTACK_ABILITIES else 'Normal'
    )


@pytest.mark.parametrize('ability', list(ABILITY_NAME_TO_ID))
def test_only_hammer_and_master_can_start_underwater_metal_attack(ability):
    route = Route('launch', 'chest', 'metal', water_state='swimming')
    assert run(route, ability=ability).reaches('chest') == (ability in {'Hammer', 'Master'})


@pytest.mark.parametrize('ability', ['Stone', 'Smash', 'Burning', 'Missile', 'UFO'])
def test_land_metal_providers_are_not_automatically_swimming_providers(ability):
    route = Route('launch', 'chest', 'metal')
    assert run(route, ability=ability).reaches('chest')
    assert not run(replace(route, water_state='swimming'), ability=ability).reaches('chest')


def test_swimming_preserves_carried_equipment_after_ordinary_movement():
    result = run(Route('launch', 'chest', water_state='swimming'), ability='Stone')
    assert Position('chest', 'Stone') in result.positions


@pytest.mark.parametrize('ability', ['Stone', 'Smash'])
def test_underwater_peg_cannot_use_unavailable_land_attack(ability):
    assert not run(Route('launch', 'chest', 'peg', water_state='swimming'), ability=ability).reaches('chest')


def test_frozen_hit_needs_both_ice_equipment_and_an_unconsumed_target():
    assert not run(FROZEN, [DEE], owned=frozenset({'Ice Ability'})).reaches('chest')
    result = run(FROZEN, [DEE], ability='Ice')
    assert any(p.node == 'chest' and DEE_ID in p.consumed for p in result.positions)
    assert not run(replace(FROZEN, water_state='swimming'), [DEE], ability='Ice').reaches('chest')


def test_ice_permission_does_not_freeze_without_an_acquirable_source():
    sources = [DEE, Placement('chest', 'MR_FROSTY')]
    assert not run(FROZEN, sources, owned=frozenset({'Ice Ability'})).reaches('chest')
    sources[-1] = Placement('launch', 'MR_FROSTY')
    assert run(FROZEN, sources, owned=frozenset({'Ice Ability'})).reaches('chest')


def test_copying_randomized_ice_from_the_target_cannot_also_freeze_it():
    resolver = policy(1, pool=['Ice'])
    assert resolver.grant('WADDLE_DEE', lambda _: True).guaranteed == {'Ice'}
    assert not run(FROZEN, [DEE], owned=frozenset({'Ice Ability'}), resolver=resolver).reaches('chest')
    spare = Placement('launch', 'WADDLE_DEE', identity='a-second-reviewed-enemy')
    assert run(FROZEN, [DEE, spare], owned=frozenset({'Ice Ability'}), resolver=resolver).reaches('chest')


def test_frozen_target_cannot_be_reused_without_an_explicit_room_reset():
    routes = [FROZEN, Route('chest', 'launch')]
    result = reachable_positions(NODES, routes, [DEE], [Position('launch', 'Ice')], SourcePolicy({'mode': 0}))
    assert Position('launch', 'Ice', consumed=frozenset({DEE_ID})) in result.positions
    # Starting after the consumed target cannot fabricate a second projectile.
    result = reachable_positions(NODES, [FROZEN], [DEE],
                                 [Position('launch', 'Ice', consumed=frozenset({DEE_ID}))],
                                 SourcePolicy({'mode': 0}))
    assert not result.reaches('chest')


@pytest.mark.parametrize('route,sources,message', [
    (replace(FROZEN, uses_object=None), [DEE], 'physical target'),
    (FROZEN, [], 'physical source'),
    (FROZEN, [replace(DEE, node='chest')], 'launch compartment'),
    (replace(FROZEN, water_state='unknown'), [DEE], 'water state'),
])
def test_unreviewed_or_misplaced_frozen_targets_fail_closed(route, sources, message):
    with pytest.raises(ValueError, match=message):
        run(route, sources, ability='Ice')


def test_frozen_projectile_is_not_a_direct_metal_attack():
    assert 'Ice' not in CAPABILITY_ABILITIES['metal']
    assert not run(Route('launch', 'chest', 'metal'), [DEE], ability='Ice').reaches('chest')


@pytest.mark.parametrize('ability', list(ABILITY_NAME_TO_ID))
def test_ordinary_underwater_blocks_need_no_copy_ability_and_preserve_carried_equipment(ability):
    route = Route('launch', 'chest', 'underwater_block_hit', water_state='swimming')
    result = run(route, ability=ability)
    assert (Position('chest', ability) in result.positions) == (ability != 'Mini')
    assert result.reaches('chest')  # Mini can explicitly drop to Normal first.


def test_water_gun_cannot_be_used_as_a_dry_attack_shortcut():
    with pytest.raises(ValueError, match='swimming attack state'):
        run(Route('launch', 'chest', 'underwater_block_hit'))


@pytest.mark.parametrize('ability', ['Hammer', 'Master'])
def test_swimming_attack_does_not_inherit_dry_fuse_move(ability):
    assert not run(Route('launch', 'chest', 'fuse', water_state='swimming'), ability=ability).reaches('chest')


def test_frozen_target_availability_requirements_are_not_bypassed():
    target = replace(DEE, requirements=frozenset({'Reviewed target access'}))
    assert not run(FROZEN, [target], ability='Ice').reaches('chest')
    assert run(FROZEN, [target], ability='Ice', owned=frozenset({'Reviewed target access'})).reaches('chest')


def test_frozen_target_cannot_be_marked_unconditionally_renewable():
    with pytest.raises(ValueError, match='one-use physical placement'):
        run(FROZEN, [replace(DEE, renewable=True)], ability='Ice')


def test_room21_normal_underwater_bypass_has_no_ability_source():
    from ..traversal_data import room_traversal_graph
    graph = room_traversal_graph('underwater_819_exit', 'local')
    assert not graph.placements
    assert graph.evaluate(SourcePolicy({'mode': 0}), frozenset(), True).reaches('underwater_819_exit:exit')
    assert graph.routes[0].water_state == 'swimming'


def test_room12_upper_left_arrival_cannot_leak_through_nondroppable_platforms():
    from ..data import data
    base = 'REGION_OLIVE_OCEAN/ROOM_6_12'
    upper = base + '__LOGIC__UPPER_LEFT'
    room13 = 'REGION_OLIVE_OCEAN/ROOM_6_13'
    assert upper in data.regions[room13].exits and base not in data.regions[room13].exits
    assert set(data.regions[upper].exits) == {room13, base + '__ROOM_CHECK'}
    assert not data.regions[base + '__ROOM_CHECK'].exits
    for origin in ('ROOM_6_11', 'ROOM_6_17'):
        assert base in data.regions['REGION_OLIVE_OCEAN/' + origin].exits


def test_room12_proven_normal_exits_do_not_require_metal():
    from ..data import data
    room = data.regions['REGION_OLIVE_OCEAN/ROOM_6_12']
    for destination in ('ROOM_6_13', 'ROOM_6_14', 'ROOM_6_17'):
        assert room.exit_requirements.get('REGION_OLIVE_OCEAN/' + destination) is None


def test_frozen_hit_never_grants_permanent_switch_credit():
    with pytest.raises(ValueError, match='persistent opens'):
        run(replace(FROZEN, opens='timed-switch'), [DEE], ability='Ice')


def test_projectile_identity_cannot_be_used_for_unrelated_capability():
    with pytest.raises(ValueError, match='unrelated capability'):
        run(replace(FROZEN, capability='peg'), [DEE], ability='Hammer')


def test_conflicting_identity_cannot_alias_another_compartment():
    with pytest.raises(ValueError, match='Conflicting physical source identity'):
        run(FROZEN, [DEE, replace(DEE, node='chest', renewable=True)], ability='Ice')


def test_two_frozen_hits_require_two_distinct_physical_targets():
    nodes = [Node('a', 825), Node('b', 825), Node('c', 825)]
    sources = [Placement('a', 'WADDLE_DEE', identity='one'),
               Placement('b', 'WADDLE_DEE', identity='two')]
    routes = [Route('a', 'b', 'frozen_enemy_hit', uses_object='one'),
              Route('b', 'c', 'frozen_enemy_hit', uses_object='two')]
    result = reachable_positions(nodes, routes, sources, [Position('a', 'Ice')], SourcePolicy({'mode': 0}))
    assert result.reaches('c')
    assert all(p.consumed == frozenset({'one', 'two'}) for p in result.positions if p.node == 'c')


@pytest.fixture
def projectile_payload():
    return {
        'version': 1, 'status': 'reviewed',
        'nodes': [{'id': 'launch', 'native_room': 825}, {'id': 'chest', 'native_room': 825}],
        'routes': [{'from': 'launch', 'to': 'chest', 'capability': 'frozen_enemy_hit',
                    'uses_object': 'dee', 'evidence': 'reviewed trajectory',
                    'frozen_enemy_evidence': 'distinct freezable target and timed sequence'}],
        'sources': [{'id': 'dee', 'node': 'launch', 'source_key': 'WADDLE_DEE',
                    'acquisition_evidence': 'reviewed physical placement'}],
        'starts': ['launch'], 'required_targets': ['chest'],
    }


@pytest.mark.parametrize('evidence', [None, '', '   ', True, 123])
def test_compiler_requires_freeze_kick_evidence(projectile_payload, evidence):
    from ..traversal import compile_traversal_graph
    projectile_payload['routes'][0]['frozen_enemy_evidence'] = evidence
    with pytest.raises(ValueError, match='freeze/kick evidence'):
        compile_traversal_graph(projectile_payload)


def test_compiler_keeps_finite_identity_and_rejects_refresh(projectile_payload):
    from ..traversal import compile_traversal_graph
    graph = compile_traversal_graph(projectile_payload)
    assert graph.routes[0].uses_object == 'dee'
    projectile_payload['routes'][0]['refresh_object'] = True
    with pytest.raises(ValueError, match='Unknown traversal route field'):
        compile_traversal_graph(projectile_payload)


def test_compiler_rejects_permanent_frozen_hit(projectile_payload):
    from ..traversal import compile_traversal_graph
    projectile_payload['routes'][0]['opens'] = 'switch'
    with pytest.raises(ValueError, match='persistent opens'):
        compile_traversal_graph(projectile_payload)


def test_ice_base_classification_stays_useful_with_conditional_goal2_witness():
    import json
    import pkgutil
    from ..traversal_data import room_traversal_targets
    assert {row['id'] for row in room_traversal_targets('block')} == {
        'underwater_819_exit', 'frozen_825_sound_effects',
        'normal_208_to_209_bottom', 'normal_210_to_209_upper',
    }
    items = json.loads(pkgutil.get_data('worlds.kirbyam', 'data/items.json'))
    assert items['ABILITY_UNLOCK_ICE']['classification'] == 'USEFUL'


def test_implicit_renewable_source_cannot_alias_explicit_projectile():
    target = replace(DEE, identity='launch:PENGY')
    implicit_source = Placement('launch', 'PENGY', renewable=True)
    with pytest.raises(ValueError, match='Conflicting physical source identity'):
        run(replace(FROZEN, uses_object=target.identity), [target, implicit_source], ability='Normal')
