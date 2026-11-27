"""Phone admits one tested cooperation opportunity, never helper abilities."""
from types import SimpleNamespace as NS

import pytest

from .. import phone_traversal as p
from .test_traversal import policy


def world(keys=True, goal_games=None):
    options = dict(ability_randomization_mode=0,
                   ability_gating=0, minimum_health=6, maximum_health=10,
                   enemy_health_multiplier=100, room_sanity=0, one_hit_mode=0)
    edge = NS(access_rule=lambda state: True)
    other = NS(access_rule=lambda state: True)
    indirect = []
    w = NS(player=1, options=NS(**{k: NS(value=v) for k,v in options.items()}),
           _enemy_copy_ability_policy=policy().policy, _area_keys_enabled=lambda: keys)
    source = RegionRef(p.SOURCE_REGION)
    default_game_region = RegionRef("Goal Room")
    if goal_games is None:
        goal_games = (NS(key="GOAL_GAME_1_GOAL_1", parent_region=default_game_region,
                         can_reach=lambda state: state.goal_reachable),)
    def get_entrance(name, player):
        assert player == 1
        assert name == p.ENTRANCE
        return edge
    w.multiworld = NS(get_entrance=get_entrance, get_region=lambda name, player: source,
                      get_locations=lambda player: goal_games,
                      register_indirect_condition=lambda region, entrance: indirect.append((region, entrance)))
    return w, edge, other, indirect


class RegionRef:
    def __init__(self, name):
        self.name = name


def state(items=(), source=True, goal=True):
    return NS(has=lambda name, player, count=1: list(items).count(name) >= count,
              goal_reachable=goal,
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
    assert [(r.name, e) for r, e in indirect] == [("Goal Room", edge), (p.SOURCE_REGION, edge)]


@pytest.mark.parametrize('field,value', [('ability_randomization_mode',1),('ability_gating',1),
    ('enemy_health_multiplier',101)])
def test_unsupported_profile_keeps_ownership_and_charge_constraint(field,value):
    w, edge, other, indirect = world()
    getattr(w.options,field).value=value
    if field == 'ability_randomization_mode':
        w._enemy_copy_ability_policy=policy(1,pool=['Sword']).policy
    assert not p.validate_phone_profile(w)
    p.install_phone_rules(w)
    assert not edge.access_rule(state())
    assert not edge.access_rule(state({p.PHONE}, source=False, goal=False))
    assert edge.access_rule(state({p.PHONE}, source=False))
    assert other.access_rule(state())
    assert [(r.name, e) for r, e in indirect] == [("Goal Room", edge)]


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
    ('enemy_health_multiplier',100.0),('room_sanity',False)])
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


@pytest.mark.parametrize('field,value', [('ability_gating',1),('enemy_health_multiplier',500),('room_sanity',1)])
def test_installed_profile_cannot_change_before_publication(field,value):
    w,*_=world()
    p.install_phone_rules(w)
    getattr(w.options,field).value=value
    with pytest.raises(ValueError,match='changed after'):
        p.validate_phone_profile(w, require_policy=True)


@pytest.mark.parametrize("minimum,maximum,one_hit", [(1, 1, 0), (1, 10, 1), (6, 10, 2)])
def test_player_health_does_not_replace_physical_phone_resources(minimum, maximum, one_hit):
    w, edge, _, _ = world()
    p.install_phone_rules(w)
    w.options.minimum_health.value = minimum
    w.options.maximum_health.value = maximum
    w.options.one_hit_mode.value = one_hit
    assert p.validate_phone_profile(w, require_policy=True)
    items = {p.PHONE, p.EAST_HUB, p.MOONLIGHT_KEY}
    assert edge.access_rule(state(items))
    assert not edge.access_rule(state(items, source=False))
    for item in items:
        assert not edge.access_rule(state(items - {item}))


def test_repeatable_goal_game_required_even_if_battery_is_owned():
    game = NS(key="GOAL_GAME_1_GOAL_1", parent_region=RegionRef("Goal Room"),
              can_reach=lambda state: state.goal_reachable)
    other_location = NS(key=p.PHONE_CHECK, parent_region=RegionRef("Unrelated room"),
                        can_reach=lambda state: True)
    w, edge, _, indirect = world(goal_games=(game, other_location))
    p.install_phone_rules(w)
    items = {p.PHONE, p.EAST_HUB, p.MOONLIGHT_KEY}
    assert edge.access_rule(state(items, goal=True))
    assert not edge.access_rule(state(items, goal=False))
    assert not edge.access_rule(state(items | {p.BATTERY}, goal=False))
    assert not edge.access_rule(state(items - {p.PHONE}, goal=True))
    assert not edge.access_rule(state(items, source=False, goal=True))
    assert [region.name for region, _ in indirect] == ["Goal Room", p.SOURCE_REGION]


def test_actual_graph_does_not_credit_battery_or_goal_game_behind_the_phone_gate():
    from BaseClasses import CollectionState
    from test.general import setup_multiworld
    from worlds.generic.Rules import set_rule
    from .. import KirbyAmWorld
    mw = setup_multiworld(KirbyAmWorld, seed=1086, options={
        "ability_gating": 0, "area_keys": 0,
        "ability_randomization_mode": 0, "enemy_health_multiplier": 100,
    })
    w = mw.worlds[1]
    games = [loc for loc in mw.get_locations(1) if "Goal Game" in loc.name]
    assert games
    for game in games:
        set_rule(game, lambda state: False)
    # Deliberately make one refill candidate depend on the Phone pocket.
    set_rule(games[0], lambda state: state.can_reach_region(p.POCKET, 1))
    chalk = next(loc for loc in mw.get_locations(1) if loc.key == p.PHONE_CHECK)
    battery = w.create_item(p.BATTERY)
    chalk.place_locked_item(battery)
    KirbyAmWorld.stage_post_fill(mw)
    assert battery.useful and not battery.advancement

    def fresh():
        state = CollectionState(mw)
        for item in mw.itempool:
            if item.name != p.BATTERY:
                state.collect(item, prevent_sweep=True)
        state.sweep_for_advancements()
        return state

    state = fresh()
    assert state.can_reach_region(p.MAIN, 1)
    assert not state.has(p.BATTERY, 1)
    assert not chalk.can_reach(state)
    state.collect(w.create_item(p.BATTERY), prevent_sweep=True)
    assert not chalk.can_reach(state)
    set_rule(games[0], lambda state: True)
    state = fresh()
    assert games[0].can_reach(state)
    assert chalk.can_reach(state)


def test_battery_rewards_are_useful_without_becoming_fill_progression():
    from test.general import setup_multiworld
    from .. import KirbyAmWorld
    mw = setup_multiworld(KirbyAmWorld, seed=1086, options={"ability_randomization_mode": 0})
    battery = mw.worlds[1].create_item(p.BATTERY)
    assert battery.filler and not battery.advancement
    mw.get_unfilled_locations(1)[0].place_locked_item(battery)
    KirbyAmWorld.stage_post_fill(mw)
    assert battery.useful and not battery.advancement

    trapped = setup_multiworld(KirbyAmWorld, seed=1086, options={
        "ability_randomization_mode": 0, "enable_traps": 1, "trap_fill_percentage": 100,
    })
    assert any(item.trap for item in trapped.itempool)
    assert not any(item.name == p.BATTERY for item in trapped.itempool)
