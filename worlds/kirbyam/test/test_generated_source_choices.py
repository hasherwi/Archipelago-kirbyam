"""A native branch selects one physical occurrence; every branch must qualify."""
from dataclasses import replace

import pytest

from ..ability_source_inventory import resolve_inventory_source, source_inventory
from ..traversal_data import compile_room_graph
from .test_traversal import policy

SMALL = 'room:825/template:0x088CD3F0/encounter:56/src/mr_frosty.c:762/type:166'
LARGE = 'room:825/template:0x088CD3F0/encounter:56/src/mr_frosty.c:765/type:167'
GROUP = 'room:825/template:0x088CD3F0/choice:mr_frosty_cube_size'


def source():
    return {'inventory_alternatives': [SMALL, LARGE], 'node': 'live',
            'generation_evidence': 'isolated conditional attack entry',
            'lifetime_evidence': 'isolated finite output before parent death',
            'alternatives_acquisition_evidence': 'isolated evidence for both sizes',
            'acquisition_evidence': 'isolated single intake', 'renewable': False}


def payload():
    return {'version': 1, 'status': 'reviewed',
            'nodes': [{'id': n, 'native_room': 825} for n in ('pre', 'live', 'goal')],
            'starts': ['pre'], 'required_targets': ['goal'], 'sources': [source()],
            'routes': [{'from': 'pre', 'to': 'live', 'evidence': 'isolated generation',
                        'activates_lifetimes': [GROUP], 'activation_evidence': 'isolated event'},
                       {'from': 'live', 'to': 'goal', 'required_equipment': ['Ice'],
                        'evidence': 'isolated held-equipment requirement'}]}


@pytest.mark.parametrize('mode', [0, 1, 2])
@pytest.mark.parametrize('gating', [False, True])
def test_exclusive_sizes_use_one_finite_runtime_grant(mode, gating):
    g = compile_room_graph(payload(), {}, advanced=True, require_inventory=True)
    p, = g.placements
    assert (p.identity, p.lifetime, p.source_key) == (GROUP, GROUP, 'MR_FROSTY_ICE_CUBE')
    result = g.evaluate(policy(mode, pool=['Ice']), frozenset({'Ice Ability'}), gating)
    assert result.reaches('goal') is bool(mode)
    assert not result.retry_assumptions
    assert all(pos.consumed == {GROUP} for pos in result.positions if pos.node == 'goal')
    if gating:
        assert not g.evaluate(policy(mode, pool=['Ice']), frozenset(), True).reaches('goal')


@pytest.mark.parametrize('change', ['subset','duplicate','foreign','direct','evidence','renewable','grant'])
def test_selection_cannot_pick_a_favorable_branch_or_invent_supply(change):
    s = source()
    if change == 'subset': s['inventory_alternatives'] = [SMALL]
    if change == 'duplicate': s['inventory_alternatives'] = [SMALL, SMALL]
    if change == 'foreign': s['inventory_alternatives'] = [SMALL, LARGE.replace('825', '955').replace('0x088CD3F0','0x088D5CD0')]
    if change == 'direct': s['inventory_id'] = SMALL
    if change == 'evidence': s.pop('alternatives_acquisition_evidence')
    if change == 'renewable': s['renewable'] = True
    if change == 'grant': s['source_key'] = 'MR_FROSTY'
    with pytest.raises(ValueError): resolve_inventory_source(s, 825, advanced=True, require_inventory=True)


@pytest.mark.parametrize('first', [False, True])
@pytest.mark.parametrize('named', [False, True])
def test_group_cannot_coexist_with_an_independently_consumable_member(first, named):
    p = payload()
    single = {k:v for k,v in source().items() if k not in ('inventory_alternatives','alternatives_acquisition_evidence')}
    single['inventory_id'] = SMALL
    if named:
        single.update(generation_instance='one', instance_evidence='isolated occurrence')
    p['sources'].insert(0 if first else 1, single)
    with pytest.raises(ValueError, match='physical|alternatives|implicit'):
        compile_room_graph(p, {}, advanced=True, require_inventory=True)


def test_standard_mode_and_unactivated_or_spent_group_do_not_acquire():
    with pytest.raises(ValueError, match='Advanced'):
        compile_room_graph(payload(), {}, require_inventory=True)
    g = compile_room_graph(payload(), {}, advanced=True, require_inventory=True)
    inactive = replace(g, routes=tuple(replace(r, activates_lifetimes=frozenset()) for r in g.routes))
    assert not inactive.evaluate(policy(1, pool=['Ice']), frozenset(), False).reaches('goal')
    spent = replace(g, starts=(replace(g.starts[0], consumed=frozenset({GROUP})),))
    assert not spent.evaluate(policy(1, pool=['Ice']), frozenset(), False).reaches('goal')


def test_native_groups_preserve_the_complete_conditional_census():
    records = [r for r in source_inventory().values() if 'exclusive_generation_group' in r]
    assert len(records) == 8
    groups = {r['exclusive_generation_group']['id'] for r in records}
    assert len(groups) == 4
    for record in records:
        group = record['exclusive_generation_group']
        assert group['outputs_per_call'] == 1 and len(group['members']) == 2
        assert group['source_sha256'] == record['native_contract']['source_sha256']
        assert record['native_contract']['attack_entry_guaranteed'] is False
        assert record['access']['status'] == 'unresolved'


def test_exhaustive_group_requires_the_grant_from_every_native_branch(monkeypatch):
    # Synthetic second grant exercises the shared mechanism without claiming a
    # different Frosty runtime key in the native inventory.
    from .. import ability_source_inventory as inventory_module
    records = dict(source_inventory())
    records[LARGE] = {**records[LARGE], 'source_key': 'SIR_KIBBLE'}
    monkeypatch.setattr(inventory_module, 'source_inventory', lambda: records)
    g = compile_room_graph(payload(), {}, advanced=True, require_inventory=True)
    assert set(g.placements[0].source_choices) == {'MR_FROSTY_ICE_CUBE', 'SIR_KIBBLE'}
    assert not g.evaluate(policy(0), frozenset(), False).reaches('goal')
    assert g.evaluate(policy(1, pool=['Ice']), frozenset(), False).reaches('goal')
    assert not g.evaluate(policy(2, pool=['Ice', 'Sword']), frozenset(), False,
                          allow_documented_retries=True).reaches('goal')
