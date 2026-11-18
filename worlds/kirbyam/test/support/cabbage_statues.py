"""Expected independent statue permission for legacy Doo rule integration tests."""
from ...enemy_ability_data import GATEABLE_ENEMY_COPY_ABILITIES
from ...traversal import SourcePolicy

PROVIDERS = frozenset({'Beam', 'Smash', 'Fire', 'Missile', 'Parasol', 'Spark', 'Ice', 'Sword', 'Fighter', 'UFO'})


def statue_alternative_available(world, state):
    """Known Hub2 route, using actual runtime assignment rather than the Doo grant."""
    if not state.can_reach_region('REGION_CABBAGE_CAVERN/ROOM_3_HUB_2', world.player):
        return False
    policy = SourcePolicy(world._enemy_copy_ability_policy,
                          bool(world.options.ability_randomization_statues.value))
    def permitted(ability):
        return (not world._ability_gating_enabled() or ability not in GATEABLE_ENEMY_COPY_ABILITIES
                or state.has(ability + ' Ability', world.player))
    for key in ('STATUE:353906', 'STATUE:353901'):
        grant = policy.grant(key, permitted)
        if grant.guaranteed & PROVIDERS or grant.randomized and grant.abilities & PROVIDERS:
            return True
    return False


def chocolate_policy_applies(policy):
    return any(policy.grant(key, lambda _: True).guaranteed & PROVIDERS
               for key in ('WADDLE_DOO', 'STATUE:353906', 'STATUE:353901'))


def finite_doo_graphs(row):
    from ...traversal_rules import target_graphs
    graphs = tuple(g for g in target_graphs(row, False)
                   if len(g.placements) == 1 and g.placements[0].source_key == 'WADDLE_DOO'
                   and not g.placements[0].renewable)
    assert len(graphs) == 10
    return graphs


def chocolate_permission_is_progression(policy, ability):
    if not chocolate_policy_applies(policy):
        return False
    if ability in policy.grant('WADDLE_DOO', lambda _: True).guaranteed:
        return True
    return any(ability in (g.abilities if g.randomized else g.guaranteed)
               for g in (policy.grant(key, lambda _: True)
                         for key in ('STATUE:353906', 'STATUE:353901')))
