"""Source rejection diagnostics never turn a generation rejection into success."""
import json
import logging
from types import SimpleNamespace

import pytest

from ..check_accessibility import _room16_source_rejection_evidence as evidence
from .test_traversal import policy
from .test_traversal_accessibility import replay_rejected_fuzz_case


def world(raw, *, advanced=0, accessibility=0):
    value = lambda n: SimpleNamespace(value=n)
    options = SimpleNamespace(room_sanity=value(1), accessibility=value(accessibility),
                              advanced_logic=value(advanced), ability_randomization_mode=value(raw['mode']))
    return SimpleNamespace(players=1, seed=123,
                           worlds={1: SimpleNamespace(options=options, _enemy_copy_ability_policy=raw)})


@pytest.mark.parametrize('ability', ['Bomb', 'UFO', 'Crash', 'Magic', 'Beam', 'Normal'])
@pytest.mark.parametrize('advanced', [0, 1])
@pytest.mark.parametrize('accessibility', [0, 2])
def test_only_intentional_source_or_option_exclusion_is_reported(ability, advanced, accessibility):
    raw = policy(1, pool=['Beam'] if ability == 'Normal' else [ability],
                 weight=100 if ability == 'Normal' else 0).policy
    mw = world(raw, advanced=advanced, accessibility=accessibility)
    result = evidence(mw, 1, [], ['Room 4-16'], [])
    excluded = ability not in {'Bomb', 'UFO'} | ({'Crash', 'Magic'} if advanced else set())
    assert (result is not None) is excluded
    if result:
        assert result == {'schema': 1, 'player': 1, 'seed': 123, 'room_sanity': 1,
                          'advanced_logic': advanced, 'source_policy': raw}


@pytest.mark.parametrize('pool,weight', [(['Bomb', 'Beam'], 0), (['Bomb'], 50), (['Bomb'], 100)])
def test_mixed_failable_sources_are_not_guaranteed(pool, weight):
    assert evidence(world(policy(2, pool=pool, weight=weight).policy), 1, [], ['Room 4-16'], [])


@pytest.mark.parametrize('change', ['missing_policy', 'wrong_mode', 'disabled', 'multiple_players',
                                   'other_infeasible', 'unfilled', 'full_placement', 'unknown_accessibility'])
def test_incomplete_or_broader_failures_are_not_classified(change):
    mw = world(policy(1, pool=['Beam']).policy)
    unfilled, infeasible, placed = [], ['Room 4-16'], []
    if change == 'missing_policy': mw.worlds[1]._enemy_copy_ability_policy = None
    elif change == 'wrong_mode': mw.worlds[1].options.ability_randomization_mode.value = 2
    elif change == 'disabled': mw.worlds[1].options.room_sanity.value = 0
    elif change == 'multiple_players': mw.players = 2
    elif change == 'other_infeasible': infeasible.append('Other check')
    elif change == 'unfilled': unfilled.append('Room 4-16')
    elif change == 'full_placement': placed.append('Other check')
    elif change == 'unknown_accessibility': mw.worlds[1].options.accessibility.value = 1
    assert evidence(mw, 1, unfilled, infeasible, placed) is None


def test_minimal_placement_diagnostics_remain_separate():
    assert evidence(world(policy(1, pool=['Beam']).policy, accessibility=2),
                    1, [], ['Room 4-16'], ['Other check'])


def test_exact_replay_emits_actual_policy_but_still_rejects(monkeypatch, tmp_path, caplog):
    caplog.set_level(logging.INFO)
    mw = replay_rejected_fuzz_case(monkeypatch, tmp_path, 95, inventory_unreachable=('Room 4-16',))
    prefix = 'KirbyAM Room16 rejection evidence: '
    messages = [record.getMessage() for record in caplog.records if record.getMessage().startswith(prefix)]
    assert len(messages) == 1
    proof = json.loads(messages[0][len(prefix):])
    assert proof['seed'] == mw.seed
    assert proof['source_policy'] == json.loads(json.dumps(mw.worlds[1]._enemy_copy_ability_policy))
    assert not tuple((tmp_path / 'output').glob('*.zip'))


@pytest.mark.parametrize('case', [3, 110, 230])
def test_exact_new_fuzz_replays_cover_source_and_advanced_exclusions(monkeypatch, tmp_path, caplog, case):
    from pathlib import Path
    from . import test_traversal_accessibility as replay
    root = Path(__file__).resolve().parents[1]
    record = json.loads((root / 'dev-docs/issue1099-fuzz-replay.json').read_text())
    seed, digest = record['fixtures'][str(case)]
    monkeypatch.setattr(replay, 'FIXTURES', Path(__file__).parent / 'data/room16_source_rejections')
    monkeypatch.setitem(replay.FUZZ_CASES, case, (seed, digest))
    caplog.set_level(logging.INFO)
    mw = replay.replay_rejected_fuzz_case(monkeypatch, tmp_path, case, inventory_unreachable=('Room 4-16',))
    prefix = 'KirbyAM Room16 rejection evidence: '
    messages = [r.getMessage() for r in caplog.records if r.getMessage().startswith(prefix)]
    assert len(messages) == 1
    proof = json.loads(messages[0][len(prefix):])
    assert proof['seed'] == seed == mw.seed
    assert proof['source_policy'] == json.loads(json.dumps(mw.worlds[1]._enemy_copy_ability_policy))
    assert proof['advanced_logic'] == (1 if case == 3 else 0)
