"""Finite generated equipment joins the existing arena suffix only in Advanced."""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

import pytest
from BaseClasses import CollectionState

from ..data import data
from ..traversal import SourcePolicy, Position
from ..traversal_data import room_traversal_graph, room_traversal_targets
from ..traversal_rules import target_graphs
from .test_traversal import policy

TARGET = 'frozen_825_sound_effects'
WITNESS = 'generated_ice'
LIFE = 'room:825/template:0x088CD3F0/choice:mr_frosty_cube_size'
END = 'frozen_825_generated:chest'


def graph():
    return room_traversal_graph(TARGET, WITNESS)


@pytest.mark.parametrize('mode', [1, 2])
@pytest.mark.parametrize('gating', [False, True])
def test_finite_cube_then_retained_ice_and_distinct_waddle(mode, gating):
    g = graph()
    result = g.evaluate(policy(mode, pool=['Ice']), frozenset({'Ice Ability'}), gating)
    assert result.reaches(END) and not result.retry_assumptions
    ends = [p for p in result.positions if p.node == END]
    assert any(p.equipped == 'Ice' for p in ends)
    assert all({LIFE, '0x088CD318'} <= p.consumed and LIFE in p.expired for p in ends)
    assert all(not p.renewable and not p.retry_evidence for p in g.placements)
    if gating:
        assert not g.evaluate(policy(mode, pool=['Ice']), frozenset(), True).reaches(END)


@pytest.mark.parametrize('mode,pool,weight', [(0,None,0),(1,['Sword'],0),(2,['Ice','Sword'],0),(2,['Ice'],50),(2,['Ice'],100)])
def test_native_wrong_possible_and_failed_grants_do_not_manufacture_ice(mode, pool, weight):
    assert not graph().evaluate(policy(mode, pool=pool, weight=weight), frozenset({'Ice Ability'}), False,
                                allow_documented_retries=True).reaches(END)


@pytest.mark.parametrize('mutation', ['no_activation', 'expired', 'spent_cube', 'spent_waddle', 'loss', 'missing_cube'])
def test_physical_lifetime_and_finite_resources_remain_required(mutation):
    g = graph()
    if mutation == 'no_activation':
        g = replace(g, routes=tuple(replace(r, activates_lifetimes=frozenset()) for r in g.routes))
    elif mutation == 'expired':
        g = replace(g, starts=(replace(g.starts[0], expired=frozenset({LIFE})),))
    elif mutation == 'spent_cube':
        # Enter after the existing maze, so no unrelated room reset can affect this check.
        g = replace(g, starts=(Position('frozen_825_generated:arena', consumed=frozenset({LIFE})),))
    elif mutation == 'spent_waddle':
        g = replace(g, starts=(Position('frozen_825_generated:arena', consumed=frozenset({'0x088CD318'})),))
    elif mutation == 'loss':
        g = replace(g, routes=tuple(replace(r, loses_equipment=True) if r.target.endswith(':launch') else r for r in g.routes))
    else:
        # Keep the lifetime declaration but put the source behind its own Ice barrier.
        g = replace(g, placements=tuple(replace(p, node=END) if p.lifetime else p for p in g.placements))
    assert not g.evaluate(policy(1, pool=['Ice']), frozenset({'Ice Ability'}), True).reaches(END)


def test_standard_excludes_the_generated_graph():
    row = next(r for r in room_traversal_targets('block') if r['id'] == TARGET)
    assert row['advanced_graphs'] == [WITNESS]
    assert len(target_graphs(row, False)) == 4
    assert len(target_graphs(row, False, advanced=True)) == 5
    assert all(not any(p.lifetime == LIFE for p in g.placements) for g in target_graphs(row, False))


@pytest.mark.parametrize('advanced', [0, 1])
@pytest.mark.parametrize('gating', [0, 1])
def test_actual_rule_requires_child_grant_and_independent_831_access(monkeypatch, advanced, gating):
    from .test_conditional_mustard_map_gate import make_world
    from .support.source_policy import set_rule_test_policy
    raw = deepcopy(policy(1, pool=['Ice', 'Sword']).policy)
    for seed in range(1000):
        raw['seed'] = seed
        resolver = SourcePolicy(raw)
        if (resolver.grant('MR_FROSTY_ICE_CUBE', lambda _: True).guaranteed == {'Ice'}
                and resolver.grant('MR_FROSTY', lambda _: True).guaranteed == {'Sword'}):
            break
    else:
        raise AssertionError('No distinct child/parent assignment')
    set_rule_test_policy(monkeypatch, lambda *args, **kwargs: deepcopy(raw))
    world = make_world(1, gating, accessibility='minimal', advanced_logic=advanced)
    target = world.multiworld.get_location(data.locations['MINOR_CHEST_MUSIC_NOTE_10'].label, 1)
    state = CollectionState(world.multiworld)
    while state.has('Ice Ability', 1):
        state.remove(world.create_item('Ice Ability'))
    state.can_reach_region = lambda name, player: name == 'REGION_OLIVE_OCEAN/ROOM_6_GOAL_2'
    state.collect(world.create_item('Ice Ability'), prevent_sweep=True)
    assert not target.access_rule(state)
    state.can_reach_region = lambda name, player: name == 'REGION_OLIVE_OCEAN/ROOM_6_14'
    assert target.access_rule(state) is bool(advanced)
    state.remove(world.create_item('Ice Ability'))
    assert target.access_rule(state) is bool(advanced and not gating)


def test_fresh_prefix_preserves_original_ammunition_and_mechanisms():
    record = json.loads((Path(__file__).resolve().parents[1] / 'dev-docs/frosty825-composition-prefix.json').read_text())
    assert record['inventory_id'] == 'room:825/template:0x088CD3F0/encounter:56/src/mr_frosty.c:762/type:166'
    assert record['suffix_addendum_sha256'] == 'a8407e9ce462385f260f5ef06b08cbcf0b719aae96b5d6527a8981e685840bd6'
    assert [c['health_percent'] for c in record['cases']] == [100, 500]
    for case in record['cases']:
        assert (case['first_frame'], case['last_frame'], case['audited_frames']) == (1085, 1729, 645)
        assert case['rooms'] == [825] and case['endpoint']['ability'] == 2
        assert case['boss']['hp'] == 30 * case['health_percent'] // 100
        assert case['waddle_bit_clear_in_all_four_slots'] and case['waddle_live_observations'] == 0
        assert len(case['mechanisms_unchanged']) == 3
        assert case['runtime_write_frames'] == [1085]
