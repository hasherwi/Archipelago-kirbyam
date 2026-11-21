"""Fresh-world retries preserve options, reject structural failures and publish once."""
from argparse import Namespace
from copy import deepcopy
import json
from pathlib import Path
import zipfile

import pytest
from Utils import output_path
from .. import generation_retry as retry
from ..check_accessibility import KirbyAmCheckAccessibilityError


def arguments(tmp_path, **overrides):
    return Namespace(**({'multi': 1, 'game': {1: retry.GAME}, 'race': False,
                         'outputpath': str(tmp_path), 'csv_output': False,
                         'spoiler_only': False, 'skip_output': False,
                         'options': {'pool': ['Fire', 'Ice'], 'weight': 55}} | overrides))


def placement_error():
    error = KirbyAmCheckAccessibilityError('controlled placed-progression lock')
    error.retryable_placement = True
    return error


def archive(args):
    with zipfile.ZipFile(Path(args.outputpath) / 'AP_test.zip', 'w') as output:
        output.writestr('original.txt', 'validated')
    return Namespace()


def test_failure_success_is_fresh_repeatable_and_transactional(monkeypatch, tmp_path):
    import Main
    results = []
    for folder in ('first', 'repeat'):
        args = arguments(tmp_path / folder)
        original = deepcopy(args)
        seen = []
        def run(current, seed, server):
            seen.append((seed, deepcopy(current.options)))
            current.options['pool'].clear()  # Main/world option mutation cannot leak into the next attempt.
            output_path.cached_path = current.outputpath
            if len(seen) == 1:
                (Path(current.outputpath) / 'partial.txt').write_text('discard')
                raise placement_error()
            assert not list(Path(args.outputpath).glob('*.zip'))
            return archive(current)
        monkeypatch.setattr(Main, 'main', run)
        before = getattr(output_path, 'cached_path', None)
        world = retry.generate(args, 1129)
        assert getattr(output_path, 'cached_path', None) == before
        assert vars(args) == vars(original)
        assert seen == [(1129, original.options), (retry.attempt_seed(1129, 1), original.options)]
        assert list(Path(args.outputpath).iterdir()) == [Path(args.outputpath) / 'AP_test.zip']
        with zipfile.ZipFile(Path(args.outputpath) / 'AP_test.zip') as output:
            receipt = json.loads(output.read('kirbyam-generation-attempts.json'))
            assert output.read('original.txt') == b'validated'
        assert receipt == world.kirbyam_generation_retry
        results.append(receipt)
    assert results[0] == results[1]


def test_exhaustion_publishes_nothing_and_keeps_reasons(monkeypatch, tmp_path):
    import Main
    seeds = []
    def run(args, seed, server):
        seeds.append(seed)
        raise placement_error()
    monkeypatch.setattr(Main, 'main', run)
    with pytest.raises(retry.KirbyAmGenerationRetryExhausted, match='8 deterministic.*1129') as caught:
        retry.generate(arguments(tmp_path), 1129)
    assert 'controlled placed-progression lock' in str(caught.value)
    assert seeds == [retry.attempt_seed(1129, i) for i in range(8)]
    assert len(set(seeds)) == 8
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('error', [ValueError('invalid options'),
                                  KirbyAmCheckAccessibilityError('structurally unreachable')])
def test_nonretryable_failure_stops_immediately(monkeypatch, tmp_path, error):
    import Main
    calls = []
    def run(*args):
        calls.append(args)
        raise error
    monkeypatch.setattr(Main, 'main', run)
    with pytest.raises(type(error), match=str(error)):
        retry.generate(arguments(tmp_path), 7)
    assert len(calls) == 1
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('overrides', [{'multi': 2}, {'game': {1: 'Other'}}, {'race': True},
                                      {'csv_output': True}, {'spoiler_only': True}])
def test_unsupported_modes_never_mutate_shared_generation(monkeypatch, tmp_path, overrides):
    import Main
    monkeypatch.setattr(Main, 'main', lambda *args: pytest.fail('unsupported generation invoked'))
    with pytest.raises(ValueError):
        retry.generate(arguments(tmp_path, **overrides), 7)
    assert not list(tmp_path.iterdir())


def test_success_retains_first_attempt_and_never_overwrites(monkeypatch, tmp_path):
    import Main
    seeds = []
    def run(args, seed, server):
        seeds.append(seed)
        return archive(args)
    monkeypatch.setattr(Main, 'main', run)
    result = retry.generate(arguments(tmp_path), 42)
    assert seeds == [42] and result.kirbyam_generation_retry['failures'] == []
    before = (tmp_path / 'AP_test.zip').read_bytes()
    with pytest.raises(FileExistsError):
        retry.generate(arguments(tmp_path), 42)
    assert (tmp_path / 'AP_test.zip').read_bytes() == before
    assert len(list(tmp_path.iterdir())) == 1


def test_real_minimal_fill_failure_then_success_repeats(monkeypatch, tmp_path):
    from .test_cutter_progression import _generate
    options = {'ability_randomization_mode': 2, 'ability_gating': 1, 'accessibility': 'minimal',
               'ability_randomization_no_ability_weight': 0, 'ability_randomization_statues': 0,
               'ability_randomization_passive_enemies': 0, 'ability_randomization_minibosses': 0,
               'ability_randomization_boss_spawns': 0, 'room_sanity': 0, 'area_keys': 1}
    results = []
    placements = []
    for name in ('first', 'repeat'):
        root = tmp_path / name
        root.mkdir()
        world, decoded, path = _generate(monkeypatch, root, 105103, [options], generator=retry.generate)
        from .support.check_accessibility import audit_local_checks
        audit = audit_local_checks(world, 1)
        assert audit.unfilled == audit.inventory_unreachable == audit.progression_unreachable == ()
        receipt = world.kirbyam_generation_retry
        assert receipt['attempt'] > 1 and receipt['failures'][0]['seed'] == 105103
        assert 'unavailable even with all inventory=[]' in receipt['failures'][0]['reason']
        results.append(receipt)
        placements.append(decoded['locations'])
    assert results[0] == results[1]
    assert placements[0] == placements[1]


@pytest.mark.parametrize('filled,inventory_reachable,expected', [(True, True, True),
                                                              (False, True, False),
                                                              (True, False, False),
                                                              (False, False, False)])
def test_audit_classifies_only_actual_placement_failures(monkeypatch, filled, inventory_reachable, expected):
    from .. import check_accessibility as audit
    inventory = object()
    progression = Namespace(sweep_for_advancements=lambda: None)
    monkeypatch.setattr(audit, 'CollectionState', lambda world: progression)
    monkeypatch.setattr(audit, '_room16_source_rejection_evidence', lambda *args: None)
    location = Namespace(name='controlled check', address=1, item=object() if filled else None,
                         can_reach=lambda state: state is inventory and inventory_reachable)
    world = Namespace(get_locations=lambda player: [location], get_all_state=lambda: inventory,
                      get_player_name=lambda player: 'Kirby')
    with pytest.raises(KirbyAmCheckAccessibilityError) as caught:
        audit.validate_all_checks(world, (1,))
    assert caught.value.retryable_placement is expected
