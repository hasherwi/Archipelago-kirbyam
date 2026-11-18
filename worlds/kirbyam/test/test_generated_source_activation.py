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


@pytest.mark.parametrize('preserve', [False, True])
def test_uncertified_room_retention_does_not_keep_generated_output_active(preserve):
    travel = Route('pre', 'post', room_transition=True, preserves_room_instance=preserve)
    start = Position('pre', active=LIFE)
    assert run([travel, NEEDS_STONE], [SOURCE], starts=[start], gating=False).reaches('other') is preserve


def test_unknown_room_retention_preserves_acquired_equipment():
    travel = Route('pre', 'post', room_transition=True)
    start = Position('pre', equipped='Stone', active=LIFE)
    assert run([travel, NEEDS_STONE], [SOURCE], starts=[start], gating=False).reaches('other')


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


def test_a_possible_native_choice_is_not_a_guarantee_or_native_branch_retry():
    from ..traversal_data import compile_room_graph
    from .test_traversal import policy
    graph = compile_room_graph(statue_graph(), {})
    grant = policy().grant_choice(graph.placements[0].source_choices, lambda _: True)
    assert 'Cutter' in grant.abilities and not grant.guaranteed and not grant.randomized
    raw = statue_graph()
    raw['sources'][0].update(renewable=True, renewable_evidence='retouch', retry_evidence='reroll')
    compiled = compile_room_graph(raw, {})
    assert not compiled.evaluate(policy(), frozenset(), False, True).reaches('target')
    assert not compiled.evaluate(policy(1, pool=['Cutter', 'Beam'], statues=True),
                                 frozenset(), False, True).reaches('target')


@pytest.mark.parametrize('renewable,documented,opt_in,expected', [
    (False, False, True, False), (True, False, True, False),
    (True, True, False, False), (True, True, True, True),
])
def test_fixed_statue_branch_can_repeat_an_identical_live_runtime_draw(renewable, documented, opt_in, expected):
    from ..traversal_data import compile_room_graph
    from .test_traversal import policy
    raw = statue_graph()
    if renewable:
        raw['sources'][0].update(renewable=True, renewable_evidence='same statue retouch')
    if documented:
        raw['sources'][0]['retry_evidence'] = 'safe retouch; runtime rerolls, native statue stays fixed'
    graph = compile_room_graph(raw, {})
    source_policy = policy(2, pool=['Cutter', 'Beam'], statues=True)
    result = graph.evaluate(source_policy, frozenset(), False, opt_in)
    assert result.reaches('target') is expected
    # Locked desired equipment remains unavailable even with valid retries.
    assert not graph.evaluate(source_policy, frozenset({'Beam Ability'}), True, opt_in).reaches('target')


def test_mixed_fixed_and_live_branches_cannot_become_a_live_retry():
    from ..master_source import CENTRAL_MASTER_SOURCE
    from .test_traversal import policy
    grant = policy(2, pool=['Cutter', 'Beam']).grant_choice(
        ('SIR_KIBBLE', CENTRAL_MASTER_SOURCE), lambda _: True)
    assert not grant.randomized and not grant.guaranteed


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
    assert len(bound) == 4
    assert all(record['access']['status'] == 'unresolved' for record in bound)
    assert {r['native_room'] for r in bound if r.get('world_access', {}).get('status') == 'outside_adventure'} == {951, 955}
    assert {r['native_room'] for r in bound if 'world_access' not in r} == {825}


def test_boss_endurance_statue_fixture_cannot_be_installed_as_adventure_access():
    from ..traversal_data import compile_room_graph
    with pytest.raises(ValueError, match='outside Adventure'):
        compile_room_graph(statue_graph(), {}, require_inventory=True)


def test_adventure_cube_native_cases_preserve_failed_branches_and_runtime_controls():
    import json
    from pathlib import Path
    manifest = json.loads((Path(__file__).resolve().parents[1]
                           / 'dev-docs/generated-frosty825-native-acceptance.json').read_text())
    expected = {'live-singleton': [0, 2], 'vanilla': [0], 'no-ability': [0],
                'unowned': [0], 'wrong-grant': [0, 7]}
    assert len(manifest['cases']) == 9
    for case in manifest['cases']:
        key = case['case'].removeprefix('adventure825-control-')
        assert case['abilities'] == expected.get(key, [0, 2])
        assert case['minimum_hp'] == case['final']['hp'] == 1
        assert case['final']['room'] == 825 and case['final']['frame'] == 1729
        assert case['approach_normal_only'] and not case['restored_state']
        assert case['first_cube']['type_id'] == 166
        assert case['first_cube']['parent'] != '0x0'
        assert all(w['frame'] == 1085 and not w['guard_failed'] for w in case['runtime_writes'])
        if case['first_copy_frame'] is not None:
            assert case['frosty_at_copy']['hp'] == 30 * case['health_percent'] // 100
            assert case['frosty_at_copy']['template'] == '0x88cd3f0'
    assert len(manifest['rejected_timing_variants']) == 5
    assert all(r['ability_before_death'] == [0] for r in manifest['rejected_timing_variants'])
    assert not manifest['combat_suffix_probe']['accepted']


def test_native_live_statue_retry_keeps_native_objects_fixed():
    import json
    from pathlib import Path
    evidence = json.loads((Path(__file__).resolve().parents[1]
                           / 'dev-docs/generated-statue-live-retry-acceptance.json').read_text())
    assert len(evidence['cases']) == 2
    for case in evidence['cases']:
        snapshots = case['snapshots']
        contacts = [s for s in snapshots if s['label'] == 'contact' or s['label'].startswith('retouchwait')]
        assert len(contacts) == 10
        assert all(s['hp'] == 6 and s['room'] == 951 for s in snapshots)
        assert all(s['statues'] == snapshots[0]['statues'] for s in snapshots)
        assert all(s['ability'] == 0 for s in snapshots if s['label'].startswith('dropwait'))
        assert {s['ability'] for s in contacts} == ({2, 7} if case['statue_runtime_mask'] else {2})
        assert not case['restored_state']
        assert all(w['frame'] == 1085 and not w['guard_failed'] for w in case['runtime_writes'])
