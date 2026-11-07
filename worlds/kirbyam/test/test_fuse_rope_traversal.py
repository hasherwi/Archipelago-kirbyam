"""Audited cannon/rope bindings, physical acquisition, and runtime policy contracts."""

from copy import deepcopy
from dataclasses import replace
import random
import re
from unittest.mock import patch

import pytest
from BaseClasses import CollectionState, ItemClassification

from ..ability_randomization import build_enemy_copy_ability_policy
from ..data import data
from ..enemy_ability_data import ABILITY_NAME_TO_ID, ABILITY_SOURCES, starting_copy_abilities
from ..enemy_ability_runtime_patch import build_enemy_copy_runtime_patch_writes
from ..traversal import CAPABILITY_ABILITIES, Grant, SourcePolicy
from ..traversal_data import room_traversal_graph, room_traversal_targets
from ..traversal_rules import graph_items, graph_succeeds, static_extra_witness
from .test_mini_traversal import make_world


FUSE_BINDINGS = {
    'fuse_126': ('REGION_RAINBOW_ROUTE/ROOM_1_32', 'REGION_RAINBOW_ROUTE/ROOM_1_33_LEFT'),
    'fuse_323': ('REGION_MUSTARD_MOUNTAIN/ROOM_4_13__LOGIC__CANNON_LEFT',
                 'REGION_MUSTARD_MOUNTAIN/ROOM_4_14__LOGIC__CANNON_LEFT'),
    'fuse_827': ('REGION_OLIVE_OCEAN/ROOM_6_07', 'REGION_OLIVE_OCEAN/ROOM_6_05__LOGIC__ENTRY_FROM_6_07'),
    'fuse_502': ('REGION_RADISH_RUINS/ROOM_8_16', 'REGION_RADISH_RUINS/ROOM_8_17'),
}
ROPE_BINDINGS = {
    'rope_143_23_14': ('REGION_RAINBOW_ROUTE/ROOM_1_42', 'exit', 'REGION_RAINBOW_ROUTE/ROOM_1_42_CUT'),
    'rope_316_35_5': ('REGION_MUSTARD_MOUNTAIN/ROOM_4_10', 'location',
                      'MINOR_CHEST_MUSTARD_MOUNTAIN_4_10_OBJECT_01'),
    'rope_553_26_7': ('REGION_OLIVE_OCEAN/ROOM_6_16', 'location', 'MINOR_CHEST_OLIVE_OCEAN_6_16'),
    'rope_227_20_12': ('REGION_PEPPERMINT_PALACE/ROOM_7_06', 'location',
                       'MINOR_CHEST_PEPPERMINT_PALACE_7_06_OBJECT_03'),
    'rope_228_11_21': ('REGION_PEPPERMINT_PALACE/ROOM_7_09', 'location',
                       'MINOR_CHEST_PEPPERMINT_PALACE_7_09_OBJECT_02'),
    'rope_217_6_5': ('REGION_PEPPERMINT_PALACE/ROOM_7_20', 'exit', 'REGION_PEPPERMINT_PALACE/ROOM_7_21'),
}
CANNON_PROVIDERS = frozenset({'Fire', 'Burning', 'Bomb', 'Laser', 'UFO', 'Master', 'Hammer'})


def live_policy(weight, statues=False, pool=('Fire', 'Cutter', 'Laser', 'Bomb', 'Sword', 'Stone')):
    raw = build_enemy_copy_ability_policy(random.Random(427), 2, True, True,
                                          whitelist=pool, include_passive_enemies=True, no_ability_weight=weight)
    return SourcePolicy(raw, statues)


def test_exact_ap_bindings_and_reviewed_census():
    fuse = room_traversal_targets('fuse')
    rope = room_traversal_targets('rope')
    assert {r['id']: (r['region'], r['exit']) for r in fuse} == FUSE_BINDINGS
    assert {r['id']: (r['region'], 'exit' if r.get('exit') else 'location', r.get('exit') or r['location'])
            for r in rope} == ROPE_BINDINGS
    # More independently audited carriers may be added without changing this census.
    assert sum(len(r['graphs']) for r in rope) >= 17


def test_cannon_traversal_is_narrower_than_ignition_and_never_persistent():
    assert CAPABILITY_ABILITIES['fuse'] == CANNON_PROVIDERS | {'Crash'}
    for row in room_traversal_targets('fuse'):
        local = room_traversal_graph(row['id'], 'local')
        assert next(r for r in local.routes if r.capability == 'fuse').allowed_abilities == CANNON_PROVIDERS
        for witness in row['graphs']:
            graph = room_traversal_graph(row['id'], witness)
            for route in graph.routes:
                if route.capability == 'fuse':
                    assert route.opens is None
                    assert route.allowed_abilities and route.allowed_abilities <= CANNON_PROVIDERS


def physical_exits(region):
    exits = set(data.regions[region].exits)
    for name in exits:
        if name.endswith('__ROOM_CHECK'):
            assert not data.regions[name].exits
    return {name for name in exits if not name.endswith('__ROOM_CHECK')}


def test_mustard_compartments_and_olive_cannon_arrival_do_not_leak():
    mustard = 'REGION_MUSTARD_MOUNTAIN/'
    assert physical_exits(mustard + 'ROOM_4_13') == {mustard + 'ROOM_4_14'}
    assert physical_exits(mustard + 'ROOM_4_13__LOGIC__CANNON_LEFT') == {
        mustard + 'ROOM_4_14__LOGIC__CANNON_LEFT',
    }
    assert physical_exits(mustard + 'ROOM_4_14__LOGIC__CANNON_LEFT') == {mustard + 'ROOM_4_BOSS'}
    olive = 'REGION_OLIVE_OCEAN/'
    assert physical_exits(olive + 'ROOM_6_05__LOGIC__ENTRY_FROM_6_07') == {olive + 'ROOM_6_06'}
    assert olive + 'ROOM_6_17' in data.regions[olive + 'ROOM_6_16'].exits
    assert not any(r.get('exit') == olive + 'ROOM_6_17' for r in room_traversal_targets('rope'))


def test_radish_normal_bypass_needs_neither_fuse_nor_equipment():
    graph = replace(room_traversal_graph('fuse_502', 'local'), placements=())
    assert any(route.capability is None for route in graph.routes)
    assert graph_succeeds(graph, SourcePolicy({'mode': 0}), frozenset(), True, retries=False)


def test_olive_chest_does_not_invent_a_behind_rope_kibble_source():
    row = next(r for r in room_traversal_targets('rope') if r['id'] == 'rope_553_26_7')
    for witness in row['graphs']:
        graph = room_traversal_graph(row['id'], witness)
        rooms = {n.key: n.room for n in graph.nodes}
        assert not any(p.source_key == 'SIR_KIBBLE' and rooms[p.node] == 553 for p in graph.placements)
        assert not graph_succeeds(replace(graph, placements=()), SourcePolicy({'mode': 0}),
                                  graph_items(graph) | {'Sword Ability', 'Cutter Ability'}, True, retries=True)
    sword = room_traversal_graph(row['id'], 'sword_811')
    assert [(p.identity, p.source_key, p.node) for p in sword.placements] == [
        ('0x088CC904', 'SWORD_KNIGHT', '811'),
    ]


def test_all_physical_source_identities_are_explicit_and_shared_consistently():
    identities = {}
    for kind in ('fuse', 'rope'):
        for row in room_traversal_targets(kind):
            for witness in row['graphs']:
                graph = room_traversal_graph(row['id'], witness)
                native = {node.key: node.room for node in graph.nodes}
                for source in graph.placements:
                    assert source.identity and re.fullmatch(r'(?:\d+:)?0x[0-9A-Fa-f]+', source.identity)
                    physical = (int(source.identity.split(':')[-1], 16), native[source.node])
                    assert identities.setdefault(physical, source.source_key) == source.source_key
                    if source.retry_evidence:
                        assert source.renewable


@pytest.mark.parametrize('ability', ['Fire', 'Bomb', 'Laser', 'UFO', 'Sword', 'Cupid'])
def test_new_provider_permission_items_are_progression(ability):
    item = next(item for item in data.items.values() if item.label == ability + ' Ability')
    assert item.classification & ItemClassification.progression
    assert ability not in starting_copy_abilities(0)


@pytest.mark.parametrize('mode', [0, 1, 2])
def test_burning_and_cutter_permissions_remain_starting(mode):
    assert {'Burning', 'Cutter'} <= set(starting_copy_abilities(mode))


@pytest.mark.parametrize('target', ['fuse_126', 'fuse_323', 'fuse_827'])
@pytest.mark.parametrize('weight', [0, 99, 100])
def test_ordinary_renewable_fuse_sources_need_positive_live_support(target, weight):
    graph = room_traversal_graph(target, 'local')
    assert any(p.renewable and p.retry_evidence for p in graph.placements)
    policy = live_policy(weight, pool=('Fire', 'Stone'))
    assert graph_succeeds(graph, policy, frozenset(), False, retries=True) == (weight < 100)
    if weight > 0:
        assert not graph_succeeds(graph, policy, frozenset(), False, retries=False)


@pytest.mark.parametrize('statues', [False, True])
@pytest.mark.parametrize('target,witness', [
    ('fuse_126', 'rainbow_hub194_statue'), ('fuse_827', 'olive_hub890_statue'),
    ('rope_143_23_14', 'statues_194'), ('rope_553_26_7', 'statues_191'),
    ('rope_227_20_12', 'statues_290_lower'), ('rope_228_11_21', 'statues_290'),
])
def test_statue_carriers_survive_weight100_with_positive_provider_pool(target, witness, statues):
    graph = room_traversal_graph(target, witness)
    assert graph_succeeds(graph, live_policy(100, statues), graph_items(graph), False, retries=True)


@pytest.mark.parametrize('enabled', [False, True])
def test_real_area_key_option_preserves_olive_source_path(enabled):
    graph = room_traversal_graph('rope_553_26_7', 'statues_191', area_keys=enabled)
    expected = {'Olive Ocean - Hub Connection'} | ({'Olive Ocean - Area Key'} if enabled else set())
    assert graph_items(graph) == expected
    policy = SourcePolicy({'mode': 0})
    assert graph_succeeds(graph, policy, frozenset(expected), False, retries=False)
    if enabled:
        assert not graph_succeeds(graph, policy, frozenset({'Olive Ocean - Hub Connection'}), False, retries=False)


@pytest.fixture(scope='module')
def vanilla_world():
    return make_world(0, True)


def test_all_four_chests_are_installed_and_require_physical_sources(vanilla_world):
    world = vanilla_world
    state = CollectionState(world.multiworld)
    for item in data.items.values():
        state.collect(world.create_item(item.label), prevent_sweep=True)
    chests = [row for row in room_traversal_targets('rope') if row.get('location')]
    assert len(chests) == 4
    with patch.object(state, 'can_reach_region', return_value=True), \
            patch.object(SourcePolicy, 'grant', return_value=Grant(frozenset())):
        for row in chests:
            target = world.multiworld.get_location(data.locations[row['location']].label, 1)
            assert not target.access_rule(state), row['id']


def test_static_policy_uses_rom_assignments_without_forcing_sources():
    raw = build_enemy_copy_ability_policy(random.Random(73), 1, True, True,
                                          whitelist=('Stone',), include_passive_enemies=True)
    before = deepcopy(raw)
    policy = SourcePolicy(raw, True)
    writes = build_enemy_copy_runtime_patch_writes(raw, True)
    hot_head = next(source for source in ABILITY_SOURCES if source.key == 'HOT_HEAD')
    assert writes[hot_head.addresses[0]] == ABILITY_NAME_TO_ID['Stone']
    assert policy.grant('HOT_HEAD', lambda _: True).guaranteed == {'Stone'}
    assert not static_extra_witness(policy)
    assert raw == before


@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('statues', [False, True])
def test_real_world_live_options_and_local_permission(gating, statues):
    world = make_world(2, gating, ability_randomization_statues=statues,
                       ability_randomization_no_ability_weight=100)
    assert bool(world.options.ability_randomization_statues.value) is statues
    assert world._ability_gating_enabled() is gating
    policy = SourcePolicy(world._enemy_copy_ability_policy, statues)
    assert policy.policy['ability_randomization_no_ability_weight'] == 100
    local = room_traversal_graph('fuse_126', 'local')
    assert not graph_succeeds(local, policy, frozenset({'Fire Ability'}), gating, retries=True)
    carrier = room_traversal_graph('fuse_126', 'rainbow_hub194_statue')
    permissions = frozenset(ability + ' Ability' for ability in ABILITY_NAME_TO_ID)
    assert graph_succeeds(carrier, policy, graph_items(carrier) | permissions, gating, retries=True)


def test_real_local_fuse_rule_needs_fire_permission_and_retains_ordinary_paths(vanilla_world):
    world = vanilla_world
    state = CollectionState(world.multiworld)
    source, destination = FUSE_BINDINGS['fuse_126']
    entrance = world.multiworld.get_entrance(f'{source} -> {destination}', 1)
    with patch.object(state, 'can_reach_region', return_value=False):
        assert not entrance.access_rule(state)
        state.collect(world.create_item('Fire Ability'), prevent_sweep=True)
        assert entrance.access_rule(state)
        state.remove(world.create_item('Fire Ability'))
        assert not entrance.access_rule(state)
    for source, destination in (
        ('REGION_MUSTARD_MOUNTAIN/ROOM_4_13', 'REGION_MUSTARD_MOUNTAIN/ROOM_4_14'),
        ('REGION_OLIVE_OCEAN/ROOM_6_16', 'REGION_OLIVE_OCEAN/ROOM_6_17'),
        ('REGION_RADISH_RUINS/ROOM_8_16', 'REGION_RADISH_RUINS/ROOM_8_17'),
    ):
        assert world.multiworld.get_entrance(f'{source} -> {destination}', 1).access_rule(state)


def test_joint_static_validation_rejects_bad_actual_assignment_without_rewriting():
    from ..peg_traversal import validate_peg_assignment

    raw = build_enemy_copy_ability_policy(random.Random(73), 1, True, True,
                                          whitelist=('Stone',), include_passive_enemies=True)
    before = deepcopy(raw)
    with pytest.raises(ValueError, match='Reviewed Wheel-source search budget exhausted'):
        validate_peg_assignment(raw, lambda: pytest.fail('One-attempt budget must not draw another assignment'),
                                include_statues=True, max_attempts=1)
    assert raw == before
