"""CI case202: preserve the policy stream while allowing the rare Room16 conjunction."""
from pathlib import Path

import pytest
from .. import check_accessibility
from ..peg_traversal import KirbyAmRoom16SourceError
from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive
from .support.check_accessibility import audit_local_checks


@pytest.mark.parametrize(
    'historical_statues,cap,attempts,winning_seed',
    [
        pytest.param(True, 8192, 8192, None, id='historical-cap-exhaustion'),
        pytest.param(False, 3353, 3353, None, id='fixed-statues-before-first-witness'),
        pytest.param(False, None, 3354, 9372867150608014686, id='fixed-statues-full-archive'),
    ],
)
def test_exact_ci_seed_exhaustion_and_full_archive(monkeypatch, tmp_path, historical_statues, cap,
                                                  attempts, winning_seed):
    import worlds.kirbyam as kirby
    from ..traversal import SourcePolicy

    if historical_statues:
        # Replay the original native-room-independent grant behavior only for
        # the historical failure control, not for the current archive.
        grant = SourcePolicy.grant

        def historical_grant(self, key, permitted, native_grants=(), *, native_room=None):
            return grant(self, key, permitted, native_grants)

        monkeypatch.setattr(SourcePolicy, 'grant', historical_grant)

    original = kirby.validate_peg_assignment
    validate = check_accessibility.validate_all_checks
    draws = 0
    last = None
    audited = []

    def select(initial, factory, statues, **kwargs):
        nonlocal draws, last
        assert initial['seed'] == 2450128862376293350
        assert kwargs['max_attempts'] == 16384
        assert kwargs['require_room16'] and not kwargs['advanced']
        draws, last = 1, initial

        def counted():
            nonlocal draws, last
            last = factory()
            draws += 1
            return last

        if cap is not None:
            kwargs['max_attempts'] = cap
        return original(initial, counted, statues, **kwargs)

    def audit(world, players):
        audited.append(world)
        return validate(world, players)

    monkeypatch.setattr(kirby, 'validate_peg_assignment', select)
    monkeypatch.setattr(check_accessibility, 'validate_all_checks', audit)
    fixture = Path(__file__).parent / 'data/fuzz_room16_source_budget_202.yaml'
    if winning_seed is None:
        with pytest.raises(KirbyAmRoom16SourceError, match=f'after {cap} attempts'):
            generate_archive_from_fixture(fixture, tmp_path, seed=587276755)
        assert draws == attempts and not audited
        assert not list(tmp_path.glob('*.zip'))
    else:
        archive = generate_archive_from_fixture(fixture, tmp_path, seed=587276755)
        assert draws == attempts
        assert last is not None and last['seed'] == winning_seed
        world, = audited
        actual = audit_local_checks(world, 1)
        assert actual.unfilled == actual.inventory_unreachable == actual.progression_unreachable == ()
        selected = load_multidata_from_archive(archive)['slot_data'][1]['enemy_copy_ability_policy']
        assert {**selected, 'allowed_abilities': list(selected['allowed_abilities'])} == last
        assert selected['mode'] == 1 and selected['ability_randomization_no_ability_weight'] == 71
        assert 'room16_switch_timer_frames' not in selected
        assert len(list(tmp_path.glob('*.zip'))) == 1


def test_room16_prerequisite_short_circuits_without_reordering_candidates(monkeypatch):
    from types import SimpleNamespace
    from .. import peg_traversal as peg, traversal_rules as rules, wheel_traversal as wheel
    policies = [{'mode': 1, 'seed': index} for index in range(3)]
    monkeypatch.setattr(peg, 'SourcePolicy', lambda raw, statues: SimpleNamespace(mode=1, policy=raw))
    checked = []
    monkeypatch.setattr(rules, 'static_room16_witness', lambda p, **kwargs: p.policy['seed'] > 0)
    def wheel_check(p):
        checked.append(p.policy['seed'])
        return p.policy['seed'] == 2
    monkeypatch.setattr(wheel, 'static_wheel_witness', wheel_check)
    monkeypatch.setattr(peg, '_assignment_has_witness', lambda *args: True)
    monkeypatch.setattr(rules, 'static_extra_witness', lambda *args, **kwargs: True)
    stream = iter(policies[1:])
    result = peg.validate_peg_assignment(policies[0], lambda: next(stream), False,
                                       max_attempts=3, require_room16=True)
    assert result is policies[2]
    assert checked == [1, 2]
