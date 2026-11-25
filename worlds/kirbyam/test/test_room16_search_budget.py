"""CI case202: preserve the policy stream while allowing the rare Room16 conjunction."""
from pathlib import Path

import pytest
from .. import check_accessibility
from ..peg_traversal import KirbyAmRoom16SourceError
from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive
from .support.check_accessibility import audit_local_checks


@pytest.mark.parametrize('historical_cap', [True, False])
def test_exact_ci_seed_exhaustion_and_full_archive(monkeypatch, tmp_path, historical_cap):
    import worlds.kirbyam as kirby
    original = kirby.validate_peg_assignment
    validate = check_accessibility.validate_all_checks
    draws = []
    audited = []

    def select(initial, factory, statues, **kwargs):
        assert initial['seed'] == 2450128862376293350
        assert kwargs['max_attempts'] == 16384
        assert kwargs['require_room16'] and not kwargs['advanced']
        draws.append(initial)
        def counted():
            candidate = factory()
            draws.append(candidate)
            return candidate
        if historical_cap:
            kwargs['max_attempts'] = 8192
            kwargs['allow_room16_shuffle_repair'] = False
        return original(initial, counted, statues, **kwargs)

    def audit(world, players):
        audited.append(world)
        return validate(world, players)

    monkeypatch.setattr(kirby, 'validate_peg_assignment', select)
    monkeypatch.setattr(check_accessibility, 'validate_all_checks', audit)
    fixture = Path(__file__).parent / 'data/fuzz_room16_source_budget_202.yaml'
    if historical_cap:
        with pytest.raises(KirbyAmRoom16SourceError, match='after 8192 attempts'):
            generate_archive_from_fixture(fixture, tmp_path, seed=587276755)
        assert len(draws) == 8192 and not audited
        assert not list(tmp_path.glob('*.zip'))
    else:
        archive = generate_archive_from_fixture(fixture, tmp_path, seed=587276755)
        assert len(draws) == 8552
        assert draws[-1]['seed'] == 884389559316697767
        world, = audited
        actual = audit_local_checks(world, 1)
        assert actual.unfilled == actual.inventory_unreachable == actual.progression_unreachable == ()
        selected = load_multidata_from_archive(archive)['slot_data'][1]['enemy_copy_ability_policy']
        assert {**selected, 'allowed_abilities': list(selected['allowed_abilities'])} == draws[-1]
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



def test_exact_high_weight_room16_seed_uses_validated_swap(monkeypatch, tmp_path):
    from collections import Counter
    from io import BytesIO
    from zipfile import ZipFile

    import worlds.kirbyam as kirby
    from ..enemy_ability_data import ABILITY_NAME_TO_ID, ABILITY_SOURCES
    from ..enemy_ability_runtime_patch import (
        ROOM16_FOLEY_SWAP, build_enemy_copy_spoiler_rows,
    )
    from ..rom import KirbyAmPatchExtension, KirbyAmProcedurePatch
    from ..room16_timer import ROM_OFFSET
    from ..traversal import SourcePolicy
    from ..traversal_rules import static_room16_witness

    select = kirby.validate_peg_assignment
    validate = check_accessibility.validate_all_checks
    audited = []

    def capture(initial, *args, **kwargs):
        assert initial['seed'] == 16414413953470095692
        assert not kwargs['require_room16'] and kwargs['room16_for_completion']
        return select(initial, *args, **kwargs)

    def audit(world, players):
        audited.append(world)
        return validate(world, players)

    monkeypatch.setattr(kirby, 'validate_peg_assignment', capture)
    monkeypatch.setattr(check_accessibility, 'validate_all_checks', audit)
    archive = generate_archive_from_fixture(
        Path(__file__).parent / 'data/fuzz_room16_source_budget_497.yaml', tmp_path, seed=353521934,
    )
    world, = audited
    actual = audit_local_checks(world, 1)
    assert actual.unfilled == actual.inventory_unreachable == actual.progression_unreachable == ()
    policy = load_multidata_from_archive(archive)['slot_data'][1]['enemy_copy_ability_policy']
    donor = policy[ROOM16_FOLEY_SWAP]
    assert policy['mode'] == 1 and policy['ability_randomization_no_ability_weight'] == 96
    assert 'room16_switch_timer_frames' not in policy
    base = {key: value for key, value in policy.items() if key != ROOM16_FOLEY_SWAP}
    old = {(kind, key): ability for kind, key, ability in build_enemy_copy_spoiler_rows(base, True)}
    new = {(kind, key): ability for kind, key, ability in build_enemy_copy_spoiler_rows(policy, True)}
    assert Counter(old.values()) == Counter(new.values())
    changed = {key for key in old if old[key] != new[key]}
    assert {key for _, key in changed} == {'FOLEY', donor}
    assert all(kind != 'statue' for kind, _ in changed)
    foley, = (key for key in changed if key[1] == 'FOLEY')
    other, = (key for key in changed if key[1] == donor)
    assert (new[foley], new[other]) == (old[other], old[foley])
    assert not static_room16_witness(SourcePolicy(base, True))
    assert static_room16_witness(SourcePolicy(policy, True))
    with ZipFile(archive) as generated:
        patch_name, = (name for name in generated.namelist() if name.endswith('.apkirbyam'))
        patch = KirbyAmProcedurePatch()
        patch.read(BytesIO(generated.read(patch_name)))
    untouched = b'\xff' * 0x1010000
    patched = KirbyAmPatchExtension.apply_tokens(patch, untouched, 'token_data.bin')
    for _, source_key in changed:
        source, = (row for row in ABILITY_SOURCES if row.key == source_key)
        patched_id = ABILITY_NAME_TO_ID[new[source.kind, source_key]]
        assert all(patched[address] == patched_id for address in source.addresses)
    assert patched[ROM_OFFSET:ROM_OFFSET + 2] == b'\x00\x00'
