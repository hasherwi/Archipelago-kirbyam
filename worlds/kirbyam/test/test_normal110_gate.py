"""Exact finite Normal payload/spray route, not generic Normal ammunition."""
from argparse import Namespace
from copy import deepcopy
from dataclasses import replace
from types import SimpleNamespace

import pytest
from BaseClasses import CollectionState, ItemClassification, MultiWorld
from Options import Accessibility

from .. import KirbyAmWorld, traversal_rules as rules
from ..data import data
from ..enemy_ability_data import GATEABLE_ENEMY_COPY_ABILITIES
from ..traversal import Node, Position, Route, compile_traversal_graph, reachable_positions
from ..traversal_data import room_traversal_graph, room_traversal_targets
from ..tools.build_ranged_completion_status import policy_profiles
from .support.normal110_history import before_normal110
from .test_mini_traversal import make_world
from .test_traversal import policy

TARGET = 'bomb_110_room9'
WITNESS = 'upper_entry_normal_water'
OWNER = 'REGION_RAINBOW_ROUTE/ROOM_1_08'
UPSTREAM = 'REGION_RAINBOW_ROUTE/ROOM_1_06_LOWER_MID'
DESTINATION = 'REGION_RAINBOW_ROUTE/ROOM_1_09'
SPIT = 'bomb_110_upper_normal_spit'
SPRAY = 'bomb_110_room9_underwater_normal_spray'


def target_row():
    return next(row for row in room_traversal_targets('block') if row['id'] == TARGET)


@pytest.mark.parametrize('profile', policy_profiles())
@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('keys', [False, True])
def test_full_public_policies_need_no_copy_permission_but_keep_finite_payload(profile, gating, keys):
    graph = room_traversal_graph(TARGET, WITNESS, keys)
    resolver = policy_profiles()[profile]
    assert len(resolver.policy['allowed_abilities']) == 25
    assert rules.target_applies(target_row(), resolver)
    assert graph.required_guaranteed_source is None and graph.access_region == UPSTREAM
    source, = graph.placements
    assert (source.source_key, source.identity, source.renewable, source.retry_evidence) == (
        'SWORD_KNIGHT', '0x088B74CC', False, None)
    assert all(p.equipped == 'Normal' for p in graph.starts)
    result = graph.evaluate(resolver, frozenset(), gating, allow_documented_retries=True)
    final = [p for p in result.positions if p.node in graph.required_targets]
    assert final and all(p.equipped == 'Normal' and p.consumed == {source.identity} and not p.opened for p in final)
    assert not result.retry_assumptions
    # Missing/relocated payload is invalid, not a free Normal projectile.
    with pytest.raises(ValueError, match='physical source'):
        replace(graph, placements=()).evaluate(resolver, frozenset(), gating)
    with pytest.raises(ValueError, match='physical source'):
        replace(graph, placements=(replace(source, node=next(iter(graph.required_targets))),)).evaluate(
            resolver, frozenset(), gating)
    spent = Position(source.node, consumed=frozenset({source.identity}))
    assert not rules.graph_succeeds(replace(graph, starts=(spent,)), resolver, frozenset(), gating, retries=True)


@pytest.mark.parametrize('profile', policy_profiles())
@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('keys', [False, True])
def test_installer_needs_independent_entry_and_preserves_base_rule(monkeypatch, profile, gating, keys):
    row = target_row()
    resolver = policy_profiles()[profile]
    monkeypatch.setattr(rules, 'extra_traversal_targets', lambda: (row,))
    target = SimpleNamespace(access_rule=lambda state: state.base)
    dependencies = []
    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy=resolver.policy,
        _ability_gating_enabled=lambda: gating, _area_keys_enabled=lambda: keys,
        options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=False),
                                accessibility=Accessibility(Accessibility.option_full)),
        multiworld=SimpleNamespace(get_entrance=lambda *_: target, get_region=lambda name, _: name,
                                   register_indirect_condition=lambda name, _: dependencies.append(name)),
    )
    rules.install_extra_traversal_rules(world)
    state = SimpleNamespace(base=True, has=lambda *_: False, can_reach_region=lambda *_: False)
    assert not target.access_rule(state)
    for wrong in (OWNER, 'REGION_RAINBOW_ROUTE/ROOM_1_06_UPPER', 'REGION_RAINBOW_ROUTE/ROOM_1_12'):
        state.can_reach_region = lambda name, _, wrong=wrong: name == wrong
        assert not target.access_rule(state)
    state.can_reach_region = lambda name, _: name == UPSTREAM
    assert target.access_rule(state)
    state.base = False
    assert not target.access_rule(state)
    assert dependencies == [UPSTREAM]


@pytest.mark.parametrize('witness,ability,source', [
    ('upper_entry', 'Spark', 'SPARKY'), ('upper_entry_sword', 'Sword', 'SWORD_KNIGHT'),
])
def test_old_graphs_retain_raw_guaranteed_sources_even_if_permissions_filter_pool(witness, ability, source):
    graph = room_traversal_graph(TARGET, witness)
    assert graph.required_guaranteed_source == (source, ability)
    for resolver in (policy(1, pool=['Beam']), policy(2, pool=['Spark', 'Sword']),
                     policy(2, pool=[ability], weight=99), policy(2, pool=[ability], weight=100)):
        for owned in (frozenset({ability + ' Ability'}),
                      frozenset(name + ' Ability' for name in GATEABLE_ENEMY_COPY_ABILITIES)):
            assert not graph.evaluate(resolver, owned, True, allow_documented_retries=True).positions


@pytest.mark.parametrize('capability,medium', [(SPIT, 'dry'), (SPRAY, 'swimming')])
@pytest.mark.parametrize('mutation', ['medium', 'source_room', 'target_room', 'equipment', 'opens', 'transition'])
def test_new_actions_reject_unreviewed_geometry_and_state(capability, medium, mutation):
    graph = room_traversal_graph(TARGET, WITNESS)
    route = next(r for r in graph.routes if r.capability == capability)
    nodes = graph.nodes
    if mutation == 'medium':
        route = replace(route, water_state='dry' if medium == 'swimming' else 'swimming')
    elif mutation in ('source_room', 'target_room'):
        key = route.source if mutation == 'source_room' else route.target
        nodes = tuple(replace(n, room=503) if n.key == key else n for n in nodes)
    elif mutation == 'equipment':
        route = replace(route, required_equipment=None)
    elif mutation == 'opens':
        route = replace(route, opens='invented-persistence')
    else:
        route = replace(route, room_transition=True)
    with pytest.raises(ValueError):
        reachable_positions(nodes, (route,), graph.placements, graph.starts, policy())


@pytest.mark.parametrize('mutation', ['wrong_identity', 'wrong_species', 'renewable', 'predicate', 'missing_attack'])
def test_payload_and_normal_branch_mutation_guards(mutation):
    payload = deepcopy(target_row()['graphs'][WITNESS])
    if mutation == 'wrong_identity':
        payload['sources'][0]['id'] = 'another-enemy'
        payload['routes'][2]['uses_object'] = 'another-enemy'
    elif mutation == 'wrong_species':
        payload['sources'][0]['source_key'] = 'WADDLE_DEE'
    elif mutation == 'renewable':
        payload['sources'][0].update(renewable=True, renewable_evidence='invented refresh')
    elif mutation == 'predicate':
        payload['requires_guaranteed_source'] = {'source_key': 'SWORD_KNIGHT', 'ability': 'Normal'}
    else:
        payload['routes'] = [r for r in payload['routes'] if r.get('capability') != SPRAY]
        graph = compile_traversal_graph(payload)
        assert not rules.graph_succeeds(graph, policy(), frozenset(), True, retries=True)
        return
    with pytest.raises(ValueError):
        compile_traversal_graph(payload)


def test_normal_spray_does_not_grant_old_attacks_or_carried_equipment():
    graph = room_traversal_graph(TARGET, WITNESS)
    result = graph.evaluate(policy(), frozenset({'Sword Ability', 'Spark Ability'}), True)
    assert all(p.equipped == 'Normal' for p in result.positions if p.node in graph.required_targets)
    for capability, medium in [(TARGET, 'dry'), ('bomb_110_room9_underwater_sword', 'swimming')]:
        result = reachable_positions((Node('a', 110), Node('b', 110)),
                                     (Route('a', 'b', capability, water_state=medium),), (),
                                     (Position('a'),), policy(), frozenset({'Spark Ability', 'Sword Ability'}))
        assert not result.reaches('b')


@pytest.mark.parametrize('mutation', ['new_access', 'new_source', 'new_route', 'finite_predicate'])
def test_exact_history_projection_rejects_changed_accepted_addition(mutation):
    row = deepcopy(target_row())
    if mutation == 'finite_predicate':
        row['graphs']['upper_entry']['requires_guaranteed_source']['ability'] = 'Sword'
    else:
        graph = row['graphs'][WITNESS]
        if mutation == 'new_access':
            graph['access']['region'] = OWNER
        elif mutation == 'new_source':
            graph['sources'][0]['id'] = 'wrong'
        else:
            graph['routes'][0]['evidence'] += ' changed'
    with pytest.raises(AssertionError):
        before_normal110(row)


@pytest.mark.parametrize('gating', [0, 1])
@pytest.mark.parametrize('keys', [0, 1])
@pytest.mark.parametrize('room_sanity', [0, 1])
def test_actual_target_preserves_other_exits_checks_and_keys(gating, keys, room_sanity):
    world = make_world(0, gating, area_keys=keys, room_sanity=room_sanity)
    state = CollectionState(world.multiworld)
    state.can_reach_region = lambda name, _: name == UPSTREAM
    assert world.multiworld.get_entrance(f'{OWNER} -> {DESTINATION}', 1).access_rule(state)
    for destination in (UPSTREAM, 'REGION_RAINBOW_ROUTE/ROOM_1_12'):
        assert world.multiworld.get_entrance(f'{OWNER} -> {destination}', 1).access_rule(state)
    assert all(loc.access_rule(state) for loc in world.multiworld.get_region(OWNER, 1).locations)
    state.can_reach_region = lambda name, _: name == 'REGION_RAINBOW_ROUTE/ROOM_1_12'
    assert not world.multiworld.get_entrance(f'{OWNER} -> {DESTINATION}', 1).access_rule(state)
    area = world.multiworld.get_entrance(
        'REGION_RAINBOW_ROUTE/ROOM_1_13_LOWER -> REGION_CABBAGE_CAVERN/ROOM_3_04', 1)
    assert area.access_rule(state) is (not keys)
    state.collect(world.create_item('Cabbage Cavern - Area Key'), prevent_sweep=True)
    assert area.access_rule(state)


@pytest.mark.parametrize('count', [0, 1, 3])
@pytest.mark.parametrize('minor', [False, True])
@pytest.mark.parametrize('gating', [False, True])
def test_spark_precollection_follows_enabled_green_and_is_collected_once(monkeypatch, count, minor, gating):
    monkeypatch.setattr(KirbyAmWorld, 'ENABLE_MINOR_CHESTS', minor)
    mw = MultiWorld(1)
    mw.game[1] = KirbyAmWorld.game
    mw.player_name = {1: 'Normal110 Spark lifecycle'}
    mw.set_seed(110)
    args = Namespace()
    options = {'ability_randomization_mode': 0, 'ability_gating': gating,
               'start_inventory': {'Spark Ability': count}, 'accessibility': 'minimal'}
    for name, option in KirbyAmWorld.options_dataclass.type_hints.items():
        setattr(args, name, {1: option.from_any(options.get(name, option.default))})
    mw.set_options(args)
    world = mw.worlds[1]
    mw.state = CollectionState(mw)
    world.generate_early()
    for _ in range(count):
        item = world.create_item('Spark Ability')
        assert item.classification == ItemClassification.useful
        mw.push_precollected(item)
    assert mw.state.count('Spark Ability', 1) == 0
    world.create_regions()
    world.set_rules()
    assert mw.state.count('Spark Ability', 1) == (count if minor and gating else 0)
    assert len([i for i in mw.precollected_items[1] if i.name == 'Spark Ability']) == count
    assert world.create_item('Spark Ability').classification == (
        ItemClassification.progression if minor and gating else ItemClassification.useful)


def test_green_and_chocolate_spark_reasons_stay_independent():
    enabled = set()

    def get_location(name, _):
        if name not in enabled:
            raise KeyError(name)
        return SimpleNamespace()
    world = SimpleNamespace(player=1, _enemy_copy_ability_policy=policy(1, pool=['Spark']).policy,
                            _ability_gating_enabled=lambda: True,
                            multiworld=SimpleNamespace(get_location=get_location))
    assert not rules.rainbow_spark_is_progression(world)
    assert not rules.cabbage_element_is_progression(world, 'Spark')
    enabled.add(data.locations['MINOR_CHEST_SPRAY_PAINT_12'].label)
    assert rules.cabbage_element_is_progression(world, 'Spark')
    assert not rules.rainbow_spark_is_progression(world)
    enabled.clear()
    enabled.add(data.locations['MINOR_CHEST_SPRAY_PAINT_04'].label)
    assert rules.rainbow_spark_is_progression(world)
    assert not rules.cabbage_element_is_progression(world, 'Spark')
    world._enemy_copy_ability_policy = policy(1, pool=['Beam']).policy
    assert not rules.rainbow_spark_is_progression(world)


@pytest.mark.parametrize('witness,field', [
    ('upper_entry', 'source'), ('upper_entry_sword', 'route'), ('upper_entry', 'access'),
])
def test_history_projection_does_not_hide_original_graph_mutations(witness, field):
    import hashlib
    import json
    row = deepcopy(target_row())
    graph = row['graphs'][witness]
    if field == 'source':
        graph['sources'][0]['acquisition_evidence'] += ' changed'
    elif field == 'route':
        graph['routes'][0]['to'] = graph['routes'][0]['from']
    else:
        graph['access']['region'] = OWNER
    projected = before_normal110(row)
    assert hashlib.sha256(json.dumps(projected, sort_keys=True, separators=(',', ':')).encode()).hexdigest() != (
        'b263b1731156283c0aa5e8a97358cb5c42a1ca1a440dfd66585d476871d3b9f4')
