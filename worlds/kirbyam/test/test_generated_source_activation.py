"""Generated presence, activation, expiry and acquired equipment are distinct."""
from dataclasses import replace

import pytest

from ..traversal import Placement, Position, Route
from .test_traversal import run

LIFE = frozenset({'output-instance'})
SOURCE = Placement('post', 'ROCKY', identity='finite-output', lifetime='output-instance')
NEEDS_STONE = Route('post', 'other', required_equipment=frozenset({'Stone'}))


@pytest.mark.parametrize('gating', [False, True])
def test_permission_and_compartment_access_do_not_activate_generation(gating):
    owned = frozenset({'Stone Ability'})
    arrival = Route('pre', 'post')
    assert not run([arrival, NEEDS_STONE], [SOURCE], owned=owned, gating=gating).reaches('other')
    activated = replace(arrival, activates_lifetimes=LIFE)
    assert run([activated, NEEDS_STONE], [SOURCE], owned=owned, gating=gating).reaches('other')
    # A source behind its own activation barrier still cannot bootstrap access.
    blocked = replace(activated, required_equipment=frozenset({'Stone'}))
    assert not run([blocked, NEEDS_STONE], [SOURCE], owned=owned, gating=gating).reaches('other')


def test_activation_does_not_revive_expired_output():
    start = Position('pre', expired=LIFE)
    route = Route('pre', 'post', activates_lifetimes=LIFE)
    assert not run([route, NEEDS_STONE], [SOURCE], starts=[start], gating=False).reaches('other')


@pytest.mark.parametrize('activate', [False, True])
def test_explicit_revival_still_requires_generation(activate):
    route = Route('pre', 'post', room_transition=True, resets_room_instance=True,
                  revives_lifetimes=LIFE, activates_lifetimes=LIFE if activate else frozenset())
    start = Position('pre', expired=LIFE, consumed=frozenset({'finite-output'}))
    assert run([route, NEEDS_STONE], [SOURCE], starts=[start], gating=False).reaches('other') is activate


def test_room_reset_clears_activation_without_manufacturing_new_output():
    reset = Route('pre', 'post', room_transition=True, resets_room_instance=True)
    start = Position('pre', active=LIFE)
    assert not run([reset, NEEDS_STONE], [SOURCE], starts=[start], gating=False).reaches('other')


@pytest.mark.parametrize('revive', [False, True])
@pytest.mark.parametrize('gating', [False, True])
def test_reset_and_activation_do_not_recycle_consumed_output_without_revival(revive, gating):
    reset = Route('pre', 'post', room_transition=True, resets_room_instance=True,
                  activates_lifetimes=LIFE, revives_lifetimes=LIFE if revive else frozenset())
    # Swallowing consumes a finite object without necessarily ending its
    # controller lifetime. Reset must not bypass the separate revival proof.
    start = Position('pre', consumed=frozenset({'finite-output'}), active=LIFE)
    assert run([reset, NEEDS_STONE], [SOURCE], starts=[start], gating=gating,
               owned=frozenset({'Stone Ability'})).reaches('other') is revive


def test_revival_of_other_output_does_not_clear_consumption():
    other = replace(SOURCE, identity='other-output', lifetime='other-instance', source_key='WADDLE_DEE')
    reset = Route('pre', 'post', room_transition=True, resets_room_instance=True,
                  activates_lifetimes=LIFE, revives_lifetimes=frozenset({'other-instance'}))
    start = Position('pre', consumed=frozenset({'finite-output'}), active=LIFE)
    assert not run([reset, NEEDS_STONE], [SOURCE, other], starts=[start], gating=False).reaches('other')


def test_ordinary_source_reset_retains_existing_reacquisition_behavior():
    reset = Route('pre', 'post', room_transition=True, resets_room_instance=True)
    start = Position('pre', consumed=frozenset({'finite-output'}))
    assert run([reset, NEEDS_STONE], [replace(SOURCE, lifetime=None)],
               starts=[start], gating=False).reaches('other')


def test_expiry_preserves_equipment_but_prevents_loss_reacquisition():
    source = replace(SOURCE, node='pre')
    start = Position('pre', active=LIFE)
    expired = Route('pre', 'post', ends_lifetimes=LIFE)
    assert run([expired, NEEDS_STONE], [source], starts=[start], gating=False).reaches('other')
    assert not run([replace(expired, loses_equipment=True), NEEDS_STONE],
                   [source, SOURCE], starts=[start], gating=False).reaches('other')


def test_activation_does_not_recycle_a_consumed_finite_instance():
    route = Route('pre', 'post', activates_lifetimes=LIFE)
    start = Position('pre', consumed=frozenset({'finite-output'}))
    assert not run([route, NEEDS_STONE], [SOURCE], starts=[start], gating=False).reaches('other')


@pytest.mark.parametrize('active,expired', [(LIFE, LIFE), (frozenset({'unknown'}), frozenset())])
def test_invalid_start_lifetimes_rejected(active, expired):
    with pytest.raises(ValueError, match='lifetime state'):
        run([], [SOURCE], starts=[Position('pre', active=active, expired=expired)])


def test_one_edge_cannot_activate_and_end_the_same_output():
    with pytest.raises(ValueError, match='Invalid source lifetime'):
        run([Route('pre', 'post', activates_lifetimes=LIFE, ends_lifetimes=LIFE)], [SOURCE])


def statue_graph():
    from ..ability_source_inventory import _inventory_payload
    slot = _inventory_payload()['generated_statue_slots'][0]
    lifetime = slot['id']
    return {
        'version': 1, 'status': 'reviewed',
        'nodes': [{'id': 'pre', 'native_room': 951}, {'id': 'contact', 'native_room': 951},
                  {'id': 'target', 'native_room': 951}],
        'starts': ['pre'], 'required_targets': ['target'],
        'sources': [{'node': 'contact', 'inventory_id': lifetime,
                     'generation_evidence': 'fixture: controller created both fixed choices',
                     'lifetime_evidence': 'fixture: independent statue instance after controller destruction',
                     'acquisition_evidence': 'fixture contact compartment'}],
        'routes': [{'from': 'pre', 'to': 'contact', 'evidence': 'fixture approach',
                    'activates_lifetimes': [lifetime], 'activation_evidence': 'fixture controller execution'},
                   {'from': 'contact', 'to': 'target', 'required_equipment': ['Cutter'],
                    'evidence': 'fixture carried Cutter'}],
    }


@pytest.mark.parametrize('mode,pool,statues,expected', [
    (0, None, False, False), (1, ['Cutter'], True, True),
    (1, ['Cutter', 'Beam'], True, False), (2, ['Cutter'], True, True),
    (2, ['Cutter', 'Beam'], True, False), (1, ['Cutter'], False, False),
])
def test_native_statue_choice_uses_all_runtime_grants(mode, pool, statues, expected):
    from ..traversal_data import compile_room_graph
    from .test_traversal import policy
    # Isolated mechanics fixture, not a production Adventure graph.
    graph = compile_room_graph(statue_graph(), {})
    assert len(graph.placements[0].source_choices) == 19
    assert graph.evaluate(policy(mode, pool=pool, statues=statues), frozenset(), False, True).reaches('target') is expected


def test_a_possible_choice_is_not_a_guarantee_and_cannot_be_retried():
    from ..traversal_data import compile_room_graph
    from .test_traversal import policy
    graph = compile_room_graph(statue_graph(), {})
    grant = policy().grant_choice(graph.placements[0].source_choices, lambda _: True)
    assert 'Cutter' in grant.abilities and not grant.guaranteed and not grant.randomized
    raw = statue_graph()
    raw['sources'][0].update(renewable=True, renewable_evidence='retouch', retry_evidence='reroll')
    with pytest.raises(ValueError, match='cannot justify retry'):
        compile_room_graph(raw, {})


def test_choice_group_cannot_filter_unowned_or_empty_native_branches():
    from .test_traversal import policy
    grant = policy().grant_choice(('SIR_KIBBLE', 'WADDLE_DEE'), lambda _: True)
    assert grant.abilities == {'Cutter'} and grant.can_fail and not grant.guaranteed
    grant = policy().grant_choice(('SIR_KIBBLE', 'WADDLE_DOO'), lambda name: name == 'Cutter')
    assert grant.abilities == {'Cutter'} and grant.can_fail and not grant.guaranteed


def test_static_inventory_cannot_be_given_an_invented_choice_group():
    from ..ability_source_inventory import resolve_inventory_source
    with pytest.raises(ValueError, match='choices mismatch'):
        resolve_inventory_source({'inventory_id': 'room:401/template:0x088C5840',
                                  'source_choices': ['ROCKY', 'SIR_KIBBLE']}, 401)


@pytest.mark.parametrize('mode,pool,weight,gating,owned,expected', [
    (0, None, 0, False, frozenset(), False),
    (1, ['Cutter'], 0, False, frozenset(), True),
    (1, ['Cutter'], 0, True, frozenset(), False),
    (1, ['Cutter'], 0, True, frozenset({'Cutter Ability'}), True),
    (1, ['Beam'], 0, False, frozenset(), False),
    (2, ['Cutter'], 0, False, frozenset(), True),
    (2, ['Cutter'], 50, False, frozenset(), False),
    (2, ['Cutter'], 100, False, frozenset(), False),
])
def test_frosty_projectile_is_advanced_and_obeys_actual_runtime(mode, pool, weight, gating, owned, expected):
    from ..traversal_data import compile_room_graph
    from .test_traversal import policy
    raw = statue_graph()
    identity = 'room:955/template:0x088D5CD0/encounter:56/src/mr_frosty.c:762/type:166'
    for node in raw['nodes']:
        node['native_room'] = 955
    raw['sources'][0]['inventory_id'] = identity
    raw['routes'][0]['activates_lifetimes'] = [identity]
    with pytest.raises(ValueError, match='Advanced Logic'):
        compile_room_graph(raw, {})
    graph = compile_room_graph(raw, {}, advanced=True)
    assert graph.placements[0].source_key == 'MR_FROSTY_ICE_CUBE'
    assert graph.evaluate(policy(mode, pool=pool, weight=weight), owned, gating, True).reaches('target') is expected
    raw['routes'][0].pop('activates_lifetimes')
    assert not compile_room_graph(raw, {}, advanced=True).evaluate(
        policy(mode, pool=pool, weight=weight), owned, gating, True).reaches('target')


def test_retouched_fixed_statue_does_not_turn_branch_choice_into_retry():
    from ..traversal_data import compile_room_graph
    from .test_traversal import policy
    raw = statue_graph()
    raw['sources'][0].update(renewable=True, renewable_evidence='native same-instance retouch')
    graph = compile_room_graph(raw, {})
    assert not graph.evaluate(policy(), frozenset(), False, True).reaches('target')
    assert graph.evaluate(policy(1, pool=['Cutter'], statues=True), frozenset(), False, True).reaches('target')


def test_native_statue_manifest_records_conditional_contact_and_retouch():
    import json
    from pathlib import Path
    evidence = json.loads((Path(__file__).resolve().parents[1]
                           / 'dev-docs/generated-statue-native-acceptance.json').read_text())
    expected = {'vanilla-d': (0, 0), 'lower-vanilla': (7, 7),
                'lower-shuffled': (6, 6), 'lower-shuffled-unowned': (0, 0)}
    assert len(evidence['cases']) == 4
    for case in evidence['cases']:
        rows = {row['label']: row for row in case['snapshots']}
        assert (rows['contact']['ability'], rows['retouchwait']['ability']) == expected[case['case']]
        assert rows['dropwait']['ability'] == 0
        assert not case['runtime_write_count'] and not case['restored_state']
        for row in rows.values():
            assert row['hp'] == 6 and row['room'] == 951
            assert len(row['statues']) == 2 and all(s['parent'] == '0x0' for s in row['statues'])
            assert row['statues'] == rows['startup']['statues']


def test_native_frosty_manifest_separates_projectile_from_boss_and_permission():
    import json
    from pathlib import Path
    evidence = json.loads((Path(__file__).resolve().parents[1]
                           / 'dev-docs/generated-frosty-native-acceptance.json').read_text())
    assert len(evidence['cases']) == 3
    for case in evidence['cases']:
        assert case['minimum_hp'] == 5 and case['final']['frame'] == 1765
        assert case['final']['room'] == 955 and case['runtime_write_count'] == 0
        assert case['first_projectile']['type_id'] == 166
        assert case['first_projectile']['parent'] != '0x0'
        if case['case'] == 'frosty-shuffled':
            assert case['abilities'] == [0, 6] and case['first_copy_frame'] == 1752
            assert case['frosty_hp_at_copy'] == 30
            assert case['last_projectile']['frame'] < case['first_copy_frame']
        else:
            assert case['abilities'] == [0] and case['first_copy_frame'] is None


def test_bounded_evidence_bindings_do_not_mark_unknown_world_access_reviewed():
    from ..ability_source_inventory import source_inventory
    bound = [record for record in source_inventory().values() if 'bounded_native_evidence' in record]
    assert len(bound) == 3
    assert all(record['access']['status'] == 'unresolved' for record in bound)
    assert all(record['world_access']['status'] == 'outside_adventure' for record in bound)


def test_boss_endurance_statue_fixture_cannot_be_installed_as_adventure_access():
    from ..traversal_data import compile_room_graph
    with pytest.raises(ValueError, match='outside Adventure'):
        compile_room_graph(statue_graph(), {}, require_inventory=True)
