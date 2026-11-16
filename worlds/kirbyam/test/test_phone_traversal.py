"""Phone admits one tested cooperation opportunity, never helper abilities."""
from types import SimpleNamespace as NS

import pytest

from .. import phone_traversal as p
from .test_traversal import policy


def world(keys=True):
    options = dict(ability_randomization_mode=0,
                   ability_gating=0, minimum_health=6, maximum_health=10,
                   enemy_health_multiplier=100, room_sanity=0, one_hit_mode=0)
    edge = NS(access_rule=lambda state: True)
    other = NS(access_rule=lambda state: True)
    indirect = []
    w = NS(player=1, options=NS(**{k: NS(value=v) for k,v in options.items()}),
           _enemy_copy_ability_policy=policy().policy, _area_keys_enabled=lambda: keys)
    def get_entrance(name, player):
        assert player == 1
        assert name == p.ENTRANCE
        return edge
    w.multiworld = NS(get_entrance=get_entrance, get_region=lambda name, player: name,
                      register_indirect_condition=lambda region, entrance: indirect.append((region, entrance)))
    return w, edge, other, indirect


def state(items=(), source=True):
    return NS(has=lambda name, player: name in items,
              can_reach_region=lambda name, player: source and name == p.SOURCE_REGION)


@pytest.mark.parametrize('keys', [False, True])
def test_installed_witness_and_each_missing_resource(keys):
    w, edge, other, indirect = world(keys=keys)
    p.install_phone_rules(w)
    items = {p.PHONE, p.EAST_HUB} | ({p.MOONLIGHT_KEY} if keys else set())
    assert edge.access_rule(state(items))
    for item in items:
        assert not edge.access_rule(state(items - {item}))
    assert not edge.access_rule(state(items, source=False))
    assert not edge.access_rule(state({'Cutter Ability', 'Sword Ability', 'Beam Ability'}))
    assert other.access_rule(state())  # No companion compartment/return rewrite.
    assert indirect == [(p.SOURCE_REGION, edge)]


@pytest.mark.parametrize('field,value', [('ability_randomization_mode',1),('ability_gating',1),
    ('minimum_health',1),('maximum_health',9),('enemy_health_multiplier',101),('one_hit_mode',1)])
def test_unsupported_profile_gets_only_ownership_constraint(field,value):
    w, edge, other, indirect = world()
    getattr(w.options,field).value=value
    if field == 'ability_randomization_mode':
        w._enemy_copy_ability_policy=policy(1,pool=['Sword']).policy
    assert not p.validate_phone_profile(w)
    p.install_phone_rules(w)
    assert not edge.access_rule(state())
    assert edge.access_rule(state({p.PHONE}, source=False))
    assert other.access_rule(state()) and not indirect


def test_missing_or_inconsistent_policy_does_not_publish_or_install():
    w,*_=world()
    del w._enemy_copy_ability_policy
    assert not p.validate_phone_profile(w)
    with pytest.raises(ValueError,match="resolved"):
        p.validate_phone_profile(w, require_policy=True)
    with pytest.raises(ValueError,match='resolved'):
        p.install_phone_rules(w)
    w._enemy_copy_ability_policy=policy(1,pool=['Sword']).policy
    with pytest.raises(ValueError,match='source policy'):
        p.validate_phone_profile(w)


def test_only_declared_146_edge_is_installed_and_source_is_independent():
    # Source acquisition is on the pre-rope143 side, not the target or Chalk.
    assert p.SOURCE_REGION == 'REGION_RAINBOW_ROUTE/ROOM_1_42'
    assert p.ENTRANCE == ('REGION_MOONLIGHT_MANSION/ROOM_2_18 -> '
                          'REGION_MOONLIGHT_MANSION/ROOM_2_18_BOTTOM_RIGHT')
    w, edge,*_=world()
    p.install_phone_rules(w)  # fixture rejects every other entrance name
    assert edge.access_rule(state({p.PHONE,p.EAST_HUB,p.MOONLIGHT_KEY}))

@pytest.mark.parametrize('keys', [0, 1])
@pytest.mark.parametrize('room_sanity', [0, 1])
def test_actual_generated_graph_phone_has_progression_without_source_self_lock(keys, room_sanity):
    from BaseClasses import CollectionState
    from test.general import setup_multiworld
    from .. import KirbyAmWorld
    mw = setup_multiworld(KirbyAmWorld, seed=1086, options={
        'ability_gating':0, 'area_keys':keys,
        'ability_randomization_mode':0, 'minimum_health':6, 'maximum_health':10,
        'enemy_health_multiplier':100, 'room_sanity':room_sanity})
    w = mw.worlds[1]
    s = CollectionState(mw)
    for item in mw.itempool:
        if item.name != p.PHONE:
            s.collect(item, prevent_sweep=True)
    for item in mw.precollected_items[1]:
        s.collect(item, prevent_sweep=True)
    s.sweep_for_advancements()
    assert s.can_reach_region(p.SOURCE_REGION, 1)
    assert s.can_reach_region(p.MAIN, 1)
    edge = mw.get_entrance(p.ENTRANCE, 1)
    assert not edge.access_rule(s)
    chalk = next(loc for loc in mw.get_locations(1) if loc.address == 3960513)
    assert not chalk.can_reach(s)
    s.collect(w.create_item(p.PHONE))
    assert edge.access_rule(s)
    assert chalk.can_reach(s)

@pytest.mark.parametrize('field,value', [('ability_gating',False),
    ('minimum_health',6.0),('enemy_health_multiplier',100.0),('room_sanity',False)])
def test_noncanonical_profile_values_rejected(field,value):
    w,*_=world()
    getattr(w.options,field).value=value
    with pytest.raises(ValueError):
        p.validate_phone_profile(w)


def test_existing_constraint_is_not_overwritten_by_phone_witness():
    w, edge, *_ = world()
    edge.access_rule = lambda state: False
    p.install_phone_rules(w)
    assert not edge.access_rule(state({p.PHONE,p.EAST_HUB,p.MOONLIGHT_KEY}))


@pytest.mark.parametrize('qualified', [False, True])
def test_prior_constraint_survives_ownership_and_qualified_rules(qualified):
    w, edge, _, indirect = world()
    w.options.ability_gating.value = int(not qualified)
    edge.access_rule = lambda state: False
    p.install_phone_rules(w)
    assert not edge.access_rule(state({p.PHONE,p.EAST_HUB,p.MOONLIGHT_KEY}))


@pytest.mark.parametrize('field,value', [('ability_gating',1),('minimum_health',1),('room_sanity',1)])
def test_installed_profile_cannot_change_before_publication(field,value):
    w,*_=world()
    p.install_phone_rules(w)
    getattr(w.options,field).value=value
    with pytest.raises(ValueError,match='changed after'):
        p.validate_phone_profile(w, require_policy=True)
