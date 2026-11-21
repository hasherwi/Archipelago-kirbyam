"""Exact Advanced Fire route: finite Hot Head, retained equipment, native dry825."""
from copy import deepcopy
from dataclasses import replace

import pytest
from ..traversal import Node, Position, Route, reachable_positions, compile_traversal_graph
from ..traversal_data import room_traversal_graph
from ..traversal_rules import target_graphs, graph_succeeds
from .test_olive_ufo_gate import row
from .test_traversal import policy

TARGET = 'frozen_825_sound_effects'
CAPABILITY = 'switch_825_fire_breath'


@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('keys', [False, True])
def test_finite_hot_head_is_required_and_advanced_only(gating, keys):
    g = room_traversal_graph(TARGET, 'fire_entry', keys)
    owned = frozenset({'Fire Ability'})
    assert g not in target_graphs(row(), keys, advanced=False)
    assert g in target_graphs(row(), keys, advanced=True)
    assert g.access_region == 'REGION_OLIVE_OCEAN/ROOM_6_14'
    assert g.placements[0].source_key == 'HOT_HEAD'
    assert not g.placements[0].renewable
    for p in (policy(0), policy(1, pool=['Fire'])):
        assert graph_succeeds(g, p, owned, gating, retries=True)
        assert graph_succeeds(g, p, frozenset(), gating, retries=True) is (not gating)
        assert not graph_succeeds(replace(g, placements=()), p, owned, gating, retries=True)
        spent = replace(g, starts=(Position('frozen_825_sound_effects:fire_hot_head', 'Normal',
                                           consumed=frozenset({'0x088CD3A8'})),))
        assert not graph_succeeds(spent, p, owned, gating, retries=True)
    for p in (policy(1, pool=['Ice']), policy(2, pool=['Fire', 'Ice']), policy(2, pool=['Fire'], weight=1)):
        assert not graph_succeeds(g, p, owned, gating, retries=True)
    result = g.evaluate(policy(0), owned, gating)
    assert not result.retry_assumptions
    assert any(p.equipped == 'Fire' for p in result.positions if p.node in g.required_targets)
    assert all(not p.opened for p in result.positions)


@pytest.mark.parametrize('room,water,opens', [(824, 'dry', None), (825, 'swimming', None), (825, 'dry', 'permanent')])
def test_fire_is_not_generic_range_or_persistent_switch(room, water, opens):
    with pytest.raises(ValueError):
        reachable_positions([Node('a', room), Node('b', room)],
                            [Route('a', 'b', CAPABILITY, opens=opens, water_state=water)],
                            (), [Position('a', 'Fire')], policy())


def test_physical_binding_and_source_condition_are_exact():
    payload = deepcopy(row()['graphs']['fire_entry'])
    assert payload['sources'][0]['inventory_id'] == 'room:825/template:0x088CD3A8'
    assert payload['requires_guaranteed_source'] == {'source_key': 'HOT_HEAD', 'ability': 'Fire'}
    payload['routes'][-1]['opens'] = 'permanent'
    with pytest.raises(ValueError, match='persistent'):
        compile_traversal_graph(payload)


@pytest.mark.parametrize('advanced,grant,access,expected', [
    (False, 'Fire', True, False), (True, 'Fire', True, True),
    (True, 'Beam', True, False), (True, 'Fire', False, False),
])
def test_installed_fire_or_needs_option_source_and_independent_access(monkeypatch, advanced, grant, access, expected):
    from types import SimpleNamespace as NS
    from .. import traversal_rules as rules
    r = row()
    monkeypatch.setattr(rules, 'extra_traversal_targets', lambda: (r,))
    resolver = policy(1, pool=[grant])
    target = NS(access_rule=lambda state: True)
    world = NS(player=1, _enemy_copy_ability_policy=resolver.policy,
               _ability_gating_enabled=lambda: True, _area_keys_enabled=lambda: False,
               options=NS(advanced_logic=NS(value=int(advanced)), ability_randomization_statues=NS(value=0),
                          accessibility=NS(value=2)),
               multiworld=NS(get_location=lambda *args: target))
    rules.install_extra_traversal_rules(world)
    state = NS(has=lambda item, player: item == 'Fire Ability',
               can_reach_region=lambda region, player: access and region == 'REGION_OLIVE_OCEAN/ROOM_6_14')
    assert target.access_rule(state) is expected
