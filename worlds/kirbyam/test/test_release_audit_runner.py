"""Fast structural checks; these do not execute the bulk generation sample."""
from collections import Counter
from itertools import combinations
from pathlib import Path

import pytest
import json
import subprocess
from types import ModuleType
from typing import Any, NoReturn

from ..tools.audit_release_generation import append_record, digest, plan


def test_plan_is_fixed_finite_and_covers_core_axes() -> None:
    cases = plan()
    assert len(cases) == 112
    assert len({c['id'] for c in cases}) == 112
    assert plan() == cases
    assert {c['seed'] for c in cases} == {105100, 20261109}
    core = [c for c in cases if c['id'].startswith('core-')]
    assert len(core) == 72
    axes = ('ability_randomization_mode', 'ability_gating', 'accessibility',
            'ability_randomization_no_ability_weight')
    counts = Counter(tuple(c['players'][0][key] for key in axes) for c in core)
    assert len(counts) == 36 and set(counts.values()) == {2}
    assert len([c for c in cases if c['id'].startswith('mixed-')]) == 4
    assert len([c for c in cases if c['id'].startswith('itemlink-')]) == 4


def test_binary_profiles_are_pairwise_balanced_and_include_extrema() -> None:
    rows = [c['players'][0] for c in plan() if c['id'].startswith('orthogonal-') and c['seed'] == 105100]
    factors = ('ability_randomization_statues', 'ability_randomization_passive_enemies',
               'ability_randomization_minibosses', 'ability_randomization_boss_spawns',
               'room_sanity', 'area_keys', 'start_with_all_maps')
    for a, b in combinations(factors, 2):
        assert Counter((r[a], r[b]) for r in rows) == {(0, 0): 4, (0, 1): 4, (1, 0): 4, (1, 1): 4}
    assert {r['goal'] for r in rows} == {0, 1, 2, 4}
    assert {r['enemy_health_multiplier'] for r in rows} == {50, 100, 500}
    assert {r['minimum_health'] for r in rows} == {1, 6}
    assert {r['maximum_health'] for r in rows} == {1, 10}
    assert {r['configured_area_boss'] for r in rows} == set(range(8))


def test_journal_preserves_started_refused_and_success_as_distinct(tmp_path: Path) -> None:
    path = tmp_path / 'results.jsonl'
    records = [{'event': 'started', 'case_id': 'a'},
               {'event': 'completed', 'case_id': 'a', 'outcome': 'refused_all_check_guard'},
               {'event': 'started', 'case_id': 'b'},
               {'event': 'completed', 'case_id': 'b', 'outcome': 'accepted_archive'}]
    for row in records:
        append_record(path, row)
    assert [json.loads(line) for line in path.read_text().splitlines()] == records
    assert digest(plan()) == digest(plan())
    changed = plan()
    changed[0]['seed'] += 1
    assert digest(changed) != digest(plan())


def test_recover_finished_child_validates_inputs_and_archive(tmp_path: Path) -> None:
    import hashlib
    pytest.importorskip('fcntl')
    from ..tools.audit_release_generation import recover_completed_result
    case = plan()[0]
    assert recover_completed_result(tmp_path, case) is None
    (tmp_path / 'case.json').write_text(json.dumps(case))
    (tmp_path / 'output').mkdir()
    archive = tmp_path / 'output' / 'fixture.zip'
    archive.write_bytes(b'structural-test-only')
    result = {'case_id': case['id'], 'seed': case['seed'], 'options': case['players'],
              'outcome': 'accepted_archive', 'archive_count': 1, 'archive_name': archive.name,
              'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}
    (tmp_path / 'result.json').write_text(json.dumps(result))
    assert recover_completed_result(tmp_path, case) == result
    archive.write_bytes(b'changed')
    with pytest.raises(ValueError, match='hash mismatch'):
        recover_completed_result(tmp_path, case)
    wrong_case = dict(case, seed=case['seed'] + 1)
    with pytest.raises(ValueError, match='result/case mismatch'):
        recover_completed_result(tmp_path, wrong_case)


def test_mixed_plan_omits_empty_inventory_for_yaml_helper() -> None:
    # _generate emits dict values as nested YAML. An empty mapping would become
    # a bare key/null, not the semantic default empty inventory. Omit it instead.
    mixed = [case for case in plan() if case['id'].startswith('mixed-')]
    assert len(mixed) == 4
    for case in mixed:
        first, second, third = case['players']
        assert 'start_inventory' not in first
        assert second['start_inventory'] == {'Ice Ability': 3}
        assert 'start_inventory' not in third
    assert all(not isinstance(value, dict) or value for case in plan()
               for player in case['players'] for value in player.values())


def test_full_defined_product_has_exact_2304_unique_combinations() -> None:
    from ..tools.audit_release_generation import product_plan
    cases = product_plan()
    assert len(cases) == len({c['id'] for c in cases}) == 2304
    assert {c['seed'] for c in cases} == {105100}
    assert len({json.dumps(c['players'], sort_keys=True) for c in cases}) == 2304
    assert all(len(c['players']) == 1 and len(c['players'][0]) == 10 for c in cases)
    counts = Counter((c['players'][0]['ability_randomization_mode'],
                      c['players'][0]['ability_gating'],
                      c['players'][0]['accessibility'],
                      c['players'][0]['ability_randomization_no_ability_weight']) for c in cases)
    assert len(counts) == 36 and set(counts.values()) == {64}
    assert len(plan()) == 112  # Default plan is independent and unchanged.


def test_bounded_jobs_have_parent_only_journal_writes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import threading
    import time
    from ..tools import audit_release_generation as runner
    parent_thread = threading.get_ident()
    mutex = threading.Lock()
    active = 0
    maximum = 0
    called = []
    writers = []
    original_append = runner.append_record

    def append(path: Path, record: dict[str, Any]) -> None:
        writers.append(threading.get_ident())
        original_append(path, record)

    def fake_run(case: dict[str, Any], directory: Path, timeout: int) -> dict[str, Any]:
        nonlocal active, maximum
        with mutex:
            active += 1
            maximum = max(maximum, active)
            called.append(case['id'])
        time.sleep(0.02)
        with mutex:
            active -= 1
        return {'case_id': case['id'], 'outcome': 'fixture_completed'}
    monkeypatch.setattr(runner, 'append_record', append)
    monkeypatch.setattr(runner, 'run_attempt', fake_run)
    cases = plan()[:7]
    journal = tmp_path / 'results.jsonl'
    runner.run_pending(cases, tmp_path, journal, [], 'fixture', 2, 60)
    assert maximum == 2 and active == 0
    assert Counter(called) == Counter(c['id'] for c in cases)
    assert set(writers) == {parent_thread}
    rows = [json.loads(line) for line in journal.read_text().splitlines()]
    assert Counter(r['event'] for r in rows) == {'started': 7, 'completed': 7}
    for case in cases:
        assert [r['event'] for r in rows if r['case_id'] == case['id']] == ['started', 'completed']


def test_live_worker_lease_prevents_recovery_or_retry(tmp_path: Path) -> None:
    import pytest
    pytest.importorskip('fcntl')
    from ..tools.audit_release_generation import exclusive_lock, recover_completed_result
    with exclusive_lock(tmp_path / 'worker.lease'):
        with pytest.raises(RuntimeError, match='still running'):
            recover_completed_result(tmp_path, plan()[0])
    assert recover_completed_result(tmp_path, plan()[0]) is None


def test_child_inherits_lease_after_coordinator_closes_copy(tmp_path: Path) -> None:
    import subprocess
    import sys
    import pytest
    pytest.importorskip('fcntl')
    from ..tools.audit_release_generation import exclusive_lock, assert_attempt_idle
    child = None
    try:
        with exclusive_lock(tmp_path / 'worker.lease') as lease:
            child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'],
                                     pass_fds=(lease.fileno(),))
        with pytest.raises(RuntimeError, match='still running'):
            assert_attempt_idle(tmp_path)
    finally:
        if child is not None:
            child.terminate()
            child.wait(timeout=5)
    assert_attempt_idle(tmp_path)


def test_normal_worker_completion_checks_identity_and_archive(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import hashlib
    from types import SimpleNamespace
    import pytest
    pytest.importorskip('fcntl')
    from ..tools import audit_release_generation as runner
    case = plan()[0]
    (tmp_path / 'case.json').write_text(json.dumps(case))
    (tmp_path / 'output').mkdir()
    archive = tmp_path / 'output' / 'fixture.zip'
    archive.write_bytes(b'structural-test-only')
    result = {'case_id': case['id'], 'seed': case['seed'], 'options': case['players'],
              'outcome': 'accepted_archive', 'archive_count': 1, 'archive_name': archive.name,
              'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}
    result_path = tmp_path / 'result.json'
    result_path.write_text(json.dumps(result))
    monkeypatch.setattr(subprocess, 'run', lambda *args, **kwargs: SimpleNamespace(returncode=0))
    assert runner.run_attempt(case, tmp_path, 10) == result
    archive.write_bytes(b'changed')
    with pytest.raises(ValueError, match='archive hash mismatch'):
        runner.run_attempt(case, tmp_path, 10)
    result['case_id'] = 'another-case'
    result_path.write_text(json.dumps(result))
    with pytest.raises(ValueError, match='result/case mismatch'):
        runner.run_attempt(case, tmp_path, 10)


def test_result_validator_is_portable_without_posix_lease(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins
    from ..tools.audit_release_generation import validate_completed_result
    original = builtins.__import__

    def no_fcntl(name: str, *args: Any, **kwargs: Any) -> ModuleType:
        if name == 'fcntl':
            raise ImportError('simulated Windows')
        return original(name, *args, **kwargs)
    monkeypatch.setattr(builtins, '__import__', no_fcntl)
    case = plan()[0]
    assert validate_completed_result(tmp_path, case) is None
    (tmp_path / 'case.json').write_text(json.dumps(case))
    result = {'case_id': case['id'], 'seed': case['seed'], 'options': case['players'],
              'outcome': 'refused_all_check_guard', 'archive_count': 0}
    (tmp_path / 'result.json').write_text(json.dumps(result))
    assert validate_completed_result(tmp_path, case) == result


def test_parallel_start_requires_existing_settings_without_writing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import pytest
    from ..tools import audit_release_generation as runner
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    runner.require_parallel_settings(1)
    for jobs in (2, 3, 4):
        with pytest.raises(SystemExit, match='Initialize sequentially with --jobs 1 --limit 1'):
            runner.require_parallel_settings(jobs)
    assert list(tmp_path.iterdir()) == []
    for name in ('options.yaml', 'host.yaml'):
        path = tmp_path / name
        original = b'# existing settings, never rewritten by preflight\n'
        path.write_bytes(original)
        runner.require_parallel_settings(4)
        assert path.read_bytes() == original
        path.unlink()


def test_candidate_normalizes_dotdot_script_invocation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from ..tools import audit_release_generation as runner
    script = tmp_path / 'worlds' / 'kirbyam' / 'tools' / 'audit_release_generation.py'
    script.parent.mkdir(parents=True)
    script.write_text('# structural fixture only\n')
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    monkeypatch.setattr(runner, '__file__', str(script.parent / '..' / 'tools' / script.name))

    def git_output(args: list[str], **kwargs: Any) -> bytes:
        if args[1] == 'ls-files':
            return b''  # Untracked harness is included explicitly.
        return b'fixture-git-hash\n'
    monkeypatch.setattr(subprocess, 'check_output', git_output)
    result = runner.candidate()
    assert set(result['source_files']) == {'worlds/kirbyam/tools/audit_release_generation.py'}


def test_parallel_main_preflight_precedes_dispatch_but_not_plan_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sys
    import pytest
    from ..tools import audit_release_generation as runner
    monkeypatch.setattr(runner, 'ROOT', tmp_path)
    output = tmp_path / 'audit'
    monkeypatch.setattr(sys, 'argv', ['audit', '--output', str(output), '--jobs', '2'])

    def unexpected(*args: Any, **kwargs: Any) -> NoReturn:
        raise AssertionError('must not dispatch workers during preflight or planning')
    monkeypatch.setattr(runner, 'run_pending', unexpected)
    with pytest.raises(SystemExit, match='Parallel audit requires existing'):
        runner.main()
    assert not output.exists()
    monkeypatch.setattr(runner, 'candidate', lambda: {'source_digest': 'fixture'})
    monkeypatch.setattr(sys, 'argv', ['audit', '--output', str(output), '--jobs', '2', '--plan-only'])
    runner.main()
    assert (output / 'manifest.json').is_file()
    assert not (tmp_path / 'host.yaml').exists()
    assert not (tmp_path / 'options.yaml').exists()
