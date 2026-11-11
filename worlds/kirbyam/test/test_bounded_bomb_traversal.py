"""Room-specific native bomb witnesses must not become global attack classes."""

from dataclasses import replace

import pytest

from ..enemy_ability_data import ABILITY_NAME_TO_ID
from ..traversal import Node, Placement, Position, Route, SourcePolicy, reachable_positions


CASES = (
    (110, 'bomb_110_room9', {'Spark'}),
    (138, 'bomb_138_green', {'Spark'}),
    (538, 'bomb_538_beam_left_crossover', {'Beam'}),
    (733, 'bomb_733_yellow_ufo_top_charge', {'UFO'}),
    (517, 'bomb_517_chocolate', {'Beam', 'Spark', 'Ice', 'Smash'}),
    (517, 'bomb_517_fire_breath', {'Fire'}),
    (517, 'bomb_517_missile_blast', {'Missile'}),
    (517, 'bomb_517_parasol_swing', {'Parasol'}),
    (719, 'bomb_719_room13', {'Beam'}),
    (719, 'bomb_719_fighter_first_combo', {'Fighter'}),
    (719, 'bomb_719_sword_repeated_slash', {'Sword'}),
    (719, 'bomb_719_fire_breath', {'Fire'}),
    (533, 'switch_533_bomb_placement', {'Bomb'}),
    (533, 'switch_533_ufo_top_charge', {'UFO'}),
    (533, 'switch_533_crash_viewport', {'Crash'}),
    (310, 'switch_310_ufo_top_charge', {'UFO'}),
    (310, 'switch_310_crash_viewport', {'Crash'}),
)


def evaluate(room, capability, *, ability='Normal', sources=(), owned=frozenset(), gating=True):
    return reachable_positions(
        (Node('approach', room), Node('opened', room)),
        (Route('approach', 'opened', capability),), sources,
        (Position('approach', ability),), SourcePolicy({'mode': 0}), owned, gating,
    )


@pytest.mark.parametrize('room,capability,providers', CASES)
@pytest.mark.parametrize('ability', list(ABILITY_NAME_TO_ID))
def test_only_target_specific_witnessed_moves_are_admitted(room, capability, providers, ability):
    assert evaluate(room, capability, ability=ability).reaches('opened') == (ability in providers)


@pytest.mark.parametrize('room,capability,providers', CASES)
@pytest.mark.parametrize('gating', [True, False])
def test_permissions_never_equip_a_bomb_witness(room, capability, providers, gating):
    owned = frozenset(f'{ability} Ability' for ability in providers)
    assert not evaluate(room, capability, owned=owned, gating=gating).reaches('opened')


@pytest.mark.parametrize('room,capability,providers', CASES)
@pytest.mark.parametrize('water_state,source_room,target_room', [
    ('swimming', None, None), ('dry', 999, None), ('dry', None, 999),
])
def test_room_witness_cannot_be_reused_in_another_geometry(
        room, capability, providers, water_state, source_room, target_room):
    with pytest.raises(ValueError, match='native room and dry attack pose'):
        reachable_positions(
            (Node('a', source_room or room), Node('b', target_room or room)),
            (Route('a', 'b', capability, water_state=water_state),), (),
            (Position('a', next(iter(providers))),), SourcePolicy({'mode': 0}),
        )


def test_beam_source_after_carrot_gate_cannot_bootstrap_it():
    source = Placement('opened', 'WADDLE_DOO', identity='test-source')
    assert not evaluate(719, 'bomb_719_room13', sources=(source,),
                        owned=frozenset({'Beam Ability'})).reaches('opened')
    assert evaluate(719, 'bomb_719_room13', sources=(replace(source, node='approach'),),
                    owned=frozenset({'Beam Ability'})).reaches('opened')
    # Beam is not gateable in the ROM; permission inventory is irrelevant.
    assert evaluate(719, 'bomb_719_room13', sources=(replace(source, node='approach'),)).reaches('opened')


@pytest.mark.parametrize('mode', [0, 1, 2])
@pytest.mark.parametrize('statues', [False, True])
@pytest.mark.parametrize('gating', [False, True])
@pytest.mark.parametrize('ability,needs_permission', [('Beam', False), ('Spark', True), ('Ice', True), ('Smash', True)])
def test_bounded_moves_follow_rom_permission_and_source_policy(mode, statues, gating, ability, needs_permission):
    from .test_traversal import policy
    resolver = policy(mode, statues=statues, pool=[ability])
    # Synthetic placements test the kernel, not a claimed natural source path.
    source_key = {'Beam': 'WADDLE_DOO', 'Spark': 'SPARKY', 'Ice': 'PENGY', 'Smash': 'MASTER_HAND'}[ability]
    sources = (Placement('approach', source_key, identity='test-source'),)

    def run(owned):
        return reachable_positions(
            (Node('approach', 517), Node('opened', 517)),
            (Route('approach', 'opened', 'bomb_517_chocolate'),), sources,
            (Position('approach'),), resolver, owned, gating,
        ).reaches('opened')
    assert run(frozenset({f'{ability} Ability'}))
    assert run(frozenset()) == (not gating or not needs_permission)
