"""Tests for the pinned KirbyAM generation-fuzzer launcher."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest


LAUNCHER_PATH = Path(__file__).resolve().parents[3] / "tools" / "run_kirbyam_generation_fuzz.py"


def load_launcher() -> ModuleType:
    spec = importlib.util.spec_from_file_location("run_kirbyam_generation_fuzz", LAUNCHER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {LAUNCHER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def launcher_args(**overrides: object) -> argparse.Namespace:
    values: dict[str, object] = {
        "runs": 10,
        "jobs": 2,
        "timeout": 60,
        "with_output": False,
        "sample_from": None,
        "allow_ignored": False,
        "classify_minimal_rejections": False,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def successful_report(total: int = 10, ignored: int = 0) -> dict[str, object]:
    return {
        "stats": {
            "total": total,
            "success": total - ignored,
            "failure": 0,
            "timeout": 0,
            "ignored": ignored,
        },
        "errors": {},
    }


def test_vendored_fuzzer_matches_pinned_checksum() -> None:
    launcher = load_launcher()
    launcher.verify_vendored_fuzzer()


def test_default_command_targets_only_kirbyam_and_skips_output() -> None:
    launcher = load_launcher()
    command = launcher.build_fuzzer_command(launcher_args())

    assert command[0]
    assert command[1] == str(launcher.FUZZER_PATH)
    assert command[command.index("--game") + 1] == "kirbyam"
    assert "--skip-output" in command
    assert command[command.index("--meta") + 1] == str(launcher.FUZZER_META_PATH)
    assert "--dump-ignored" in command


def test_sample_command_uses_samples_instead_of_game_selector(tmp_path: Path) -> None:
    launcher = load_launcher()
    command = launcher.build_fuzzer_command(launcher_args(sample_from=tmp_path, with_output=True))

    assert "--game" not in command
    assert "--meta" not in command
    assert command[command.index("--sample-from") + 1] == str(tmp_path.resolve())
    assert "--skip-output" not in command


def test_report_validation_rejects_ignored_option_errors_by_default() -> None:
    launcher = load_launcher()

    messages = launcher.validate_report(successful_report(ignored=2), expected_runs=10, allow_ignored=False)

    assert messages == ["2 ignored OptionError case(s); use --allow-ignored only after review"]
    assert launcher.validate_report(successful_report(ignored=2), expected_runs=10, allow_ignored=True) == []


def test_report_validation_rejects_failures_timeouts_and_bad_totals() -> None:
    launcher = load_launcher()
    report = {
        "stats": {"total": 9, "success": 5, "failure": 1, "timeout": 1, "ignored": 1},
        "errors": {},
    }

    messages = launcher.validate_report(report, expected_runs=10, allow_ignored=False)

    assert "expected 10 completed runs, report contains 9" in messages
    assert "success + failure + timeout + ignored does not equal total" in messages
    assert "1 generation failure(s)" in messages
    assert "1 generation timeout(s)" in messages
    assert "1 ignored OptionError case(s); use --allow-ignored only after review" in messages


def test_run_writes_metadata_and_returns_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    launcher = load_launcher()
    fuzzer_path = tmp_path / "fuzz.py"
    fuzzer_path.write_text("# test fuzzer\n", encoding="utf-8")
    output_dir = tmp_path / "fuzz_output"
    report_path = output_dir / "report.json"
    metadata_path = output_dir / "metadata.json"
    expected_sha = hashlib.sha256(fuzzer_path.read_bytes()).hexdigest()

    monkeypatch.setattr(launcher, "FUZZER_PATH", fuzzer_path)
    monkeypatch.setattr(launcher, "FUZZER_SHA256", expected_sha)
    monkeypatch.setattr(launcher, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(launcher, "REPORT_PATH", report_path)
    monkeypatch.setattr(launcher, "METADATA_PATH", metadata_path)
    monkeypatch.setenv("GITHUB_SHA", "abc123")

    def fake_run(*_args: object, **_kwargs: object) -> SimpleNamespace:
        output_dir.mkdir()
        report_path.write_text(json.dumps(successful_report(total=2)), encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(launcher.subprocess, "run", fake_run)

    assert launcher.run(["--runs", "2", "--jobs", "1"]) == 0
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["archipelago_commit"] == "abc123"
    assert metadata["fuzzer"]["commit"] == launcher.FUZZER_COMMIT
    assert metadata["fuzzer"]["master_seed"] is None
    assert metadata["arguments"]["runs"] == 2


def test_run_returns_failure_for_ignored_option_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    launcher = load_launcher()
    fuzzer_path = tmp_path / "fuzz.py"
    fuzzer_path.write_text("# test fuzzer\n", encoding="utf-8")
    output_dir = tmp_path / "fuzz_output"
    report_path = output_dir / "report.json"
    expected_sha = hashlib.sha256(fuzzer_path.read_bytes()).hexdigest()

    monkeypatch.setattr(launcher, "FUZZER_PATH", fuzzer_path)
    monkeypatch.setattr(launcher, "FUZZER_SHA256", expected_sha)
    monkeypatch.setattr(launcher, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(launcher, "REPORT_PATH", report_path)
    monkeypatch.setattr(launcher, "METADATA_PATH", output_dir / "metadata.json")
    monkeypatch.setenv("GITHUB_SHA", "abc123")

    def fake_run(*_args: object, **_kwargs: object) -> SimpleNamespace:
        output_dir.mkdir()
        report_path.write_text(json.dumps(successful_report(total=2, ignored=1)), encoding="utf-8")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(launcher.subprocess, "run", fake_run)

    assert launcher.run(["--runs", "2", "--jobs", "1"]) == 1


@pytest.mark.parametrize("minimum", range(1, 11))
def test_health_fuzz_triggers_select_only_supported_maximum_range(minimum: int) -> None:
    import yaml
    from Generate import roll_triggers
    from worlds.kirbyam.options import MaximumHealth

    launcher = load_launcher()
    meta = yaml.safe_load(launcher.FUZZER_META_PATH.read_text(encoding="utf-8"))
    game = "Kirby & The Amazing Mirror"
    # Even an initially invalid independently-randomized maximum is replaced.
    weights = {game: {"minimum_health": minimum, "maximum_health": 1}}
    resolved = roll_triggers(weights, meta["triggers"], set())[game]
    assert resolved["minimum_health"] == minimum
    expected_end = min(minimum + 4, 10)
    assert resolved["maximum_health"] == f"random-range-{minimum}-{expected_end}"
    for _ in range(20):
        maximum = MaximumHealth.from_any(resolved["maximum_health"]).value
        assert minimum <= maximum <= expected_end


def rejection_artifact(launcher: ModuleType, root: Path) -> dict[str, object]:
    """Small synthetic fixture with the same strict envelope as saved CI logs."""
    message = (launcher.CHECK_ERROR_PREFIX + "\nPlayer 1 (1-0): unfilled=[]; "
               "unavailable even with all inventory=[]; unreachable from placed progression=['A chest']")
    log = (
        "Generating for 1 player, 123 Seed 456 with plando: items, connections, texts, bosses\n"
        'P1 Rolled options (1-0/Kirby & The Amazing Mirror): '
        '{"game": "Kirby & The Amazing Mirror", "accessibility": 2}\n'
        'Traceback (most recent call last):\n  File "world.py", line 1, in stage_pre_output\n'
        '  File "check_accessibility.py", line 2, in validate_all_checks\n'
        + launcher.CHECK_ERROR_TYPE + ": " + message + "\n\n"
    )
    case = root / "error" / "kirbyam" / "1"
    case.mkdir(parents=True)
    (case / "1.log").write_text(log, encoding="utf-8")
    (case / "1-0.yaml").write_text("game: Kirby & The Amazing Mirror\n", encoding="utf-8")
    return {"stats": {"total": 4, "success": 3, "failure": 1, "timeout": 0, "ignored": 0},
            "errors": {"kirbyam": {message: [1]}}}


def test_classification_is_opt_in_and_never_changes_raw_success(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str],
) -> None:
    launcher = load_launcher()
    report = rejection_artifact(launcher, tmp_path)
    before = json.dumps(report)
    monkeypatch.setattr(launcher, "OUTPUT_DIR", tmp_path)
    args = launcher_args(runs=4, classify_minimal_rejections=False)
    assert launcher.report_result(args, report, 1) == 1
    args.classify_minimal_rejections = True
    assert launcher.report_result(args, report, 1) == 0
    assert json.dumps(report) == before
    outcomes = json.loads((tmp_path / launcher.CLASSIFICATION_FILENAME).read_text())
    assert outcomes["raw_stats"]["success"] == 3
    assert outcomes["unsafe_rejected"][0]["seed"] == 456
    assert outcomes["unsafe_rejected"][0]["stranded_checks"] == ["A chest"]
    assert outcomes["unsafe_rejected"][0]["yaml_sha256"]
    assert outcomes["unclassified"] == outcomes["errors"] == []
    assert "3 succeeded, 1 raw failures (1 classified unsafe rejections)" in capsys.readouterr().out


@pytest.mark.parametrize("change", [
    "full", "wrong_game", "missing_options", "multiple_players", "unfilled", "source_closed", "no_checks",
    "wrong_exception", "trailing_error", "chained_error", "chain_marker", "exception_group", "bad_checks",
    "missing_stack",
    "missing_seed", "missing_yaml", "multiple_yamls", "missing_log", "bad_json", "no_traceback",
])
def test_classification_rejects_unexpected_and_incomplete_evidence(tmp_path: Path, change: str) -> None:
    launcher = load_launcher()
    report = rejection_artifact(launcher, tmp_path)
    path = tmp_path / "error/kirbyam/1/1.log"
    log = path.read_text()
    replacements = {
        "full": ('"accessibility": 2', '"accessibility": 0'),
        "wrong_game": ('"game": "Kirby & The Amazing Mirror"', '"game": "Another game"'),
        "missing_options": ("P1 Rolled options", "Options"),
        "multiple_players": ("P1 Rolled options", "P2 Rolled options"),
        "unfilled": ("unfilled=[]", "unfilled=['A chest']"),
        "source_closed": ("unavailable even with all inventory=[]", "unavailable even with all inventory=['A chest']"),
        "no_checks": ("progression=['A chest']", "progression=[]"),
        "wrong_exception": (launcher.CHECK_ERROR_TYPE, "RuntimeError"),
        "bad_checks": ("progression=['A chest']", "progression=[broken]"),
        "missing_stack": ("in stage_pre_output", "in generate_early"),
        "missing_seed": ("Generating for 1 player", "Generating for 2 players"),
        "bad_json": ('"accessibility": 2', '"accessibility": nope'),
        "no_traceback": ("Traceback (most recent call last):", ""),
    }
    if change in replacements:
        old, new = replacements[change]
        log = log.replace(old, new)
        # Keep the report consistent: rejecting theoretical failures cannot rely
        # merely on a deliberately mismatched log and report.
        errors = report["errors"]
        assert isinstance(errors, dict)
        errors["kirbyam"] = {message.replace(old, new): ids for message, ids in errors["kirbyam"].items()}
    elif change == "trailing_error":
        log += "RuntimeError: unexpected\n"
    elif change == "chained_error":
        log = "Traceback (most recent call last):\nRuntimeError: prior\n" + log
    elif change == "chain_marker":
        log = "During handling of the above exception, another exception occurred:\n" + log
    elif change == "exception_group":
        log = "ExceptionGroup: mixed errors\n" + log
    elif change == "missing_yaml":
        (path.parent / "1-0.yaml").unlink()
    elif change == "multiple_yamls":
        (path.parent / "1-1.yaml").write_text("game: Another game\n")
    path.write_text(log)
    if change == "missing_log":
        path.unlink()
    outcomes = launcher.classify_minimal_rejections(report, tmp_path)
    assert outcomes["unsafe_rejected"] == []
    assert len(outcomes["unclassified"]) == 1
    assert launcher.validate_report(report, expected_runs=4, allow_ignored=False) == ["1 generation failure(s)"]


@pytest.mark.parametrize("case_ids", [[1, 1], [True], [-1], ["1"], [], [1, 2]])
def test_ambiguous_case_mapping_cannot_subtract_failures(tmp_path: Path, case_ids: list[object]) -> None:
    launcher = load_launcher()
    report = rejection_artifact(launcher, tmp_path)
    errors = report["errors"]
    assert isinstance(errors, dict)
    message, = errors["kirbyam"]
    errors["kirbyam"][message] = case_ids
    outcomes = launcher.classify_minimal_rejections(report, tmp_path)
    assert outcomes["unsafe_rejected"] == []
    assert outcomes["errors"]


@pytest.mark.parametrize("success,rejections,allowed", [(0, 500, False), (1, 499, False), (249, 251, False),
                                                        (250, 250, True), (395, 105, True)])
def test_rejection_policy_requires_successful_generation_fraction(success: int, rejections: int, allowed: bool) -> None:
    launcher = load_launcher()
    report = {"stats": {"total": 500, "success": success, "failure": rejections, "timeout": 0, "ignored": 0}}
    messages = launcher.validate_report(report, expected_runs=500, allow_ignored=False, unsafe_rejected=rejections)
    assert (not messages) is allowed


def test_classified_rejection_does_not_hide_other_failure_timeout_or_crash(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    launcher = load_launcher()
    report = rejection_artifact(launcher, tmp_path)
    monkeypatch.setattr(launcher, "OUTPUT_DIR", tmp_path)
    args = launcher_args(runs=4, classify_minimal_rejections=True)
    assert launcher.report_result(args, report, 2) == 2
    stats = report["stats"]
    errors = report["errors"]
    assert isinstance(stats, dict) and isinstance(errors, dict)
    stats.update(success=2, failure=2)
    errors["kirbyam"]["RuntimeError: unexpected"] = [2]
    assert launcher.report_result(args, report, 1) == 1
    stats.update(failure=1, timeout=1)
    errors["kirbyam"].pop("RuntimeError: unexpected")
    errors["kirbyam"]["TimeoutError"] = [2]
    assert launcher.report_result(args, report, 1) == 1


@pytest.mark.parametrize("room_sanity", ("false", "true"))
def test_unconditional_phone_does_not_override_fuzz_profiles(room_sanity: str) -> None:
    import yaml
    from Generate import roll_triggers

    game = "Kirby & The Amazing Mirror"
    meta = yaml.safe_load(load_launcher().FUZZER_META_PATH.read_text(encoding="utf-8"))
    original = {"minimum_health": 2,
                "maximum_health": 1, "enemy_health_multiplier": 200,
                "ability_gating": "true", "ability_randomization_mode": "shuffled",
                "one_hit_mode": "include_vitality_counters", "room_sanity": room_sanity}
    resolved = roll_triggers({game: original}, meta["triggers"], set())[game]
    assert resolved == {**original, "maximum_health": "random-range-2-6"}


@pytest.mark.parametrize("gating,expected", [("false", 0), ("true", 9)])
def test_fuzz_random_starts_follow_ability_gating(gating: str, expected: int) -> None:
    import yaml
    from Generate import roll_triggers

    game = "Kirby & The Amazing Mirror"
    meta = yaml.safe_load(load_launcher().FUZZER_META_PATH.read_text(encoding="utf-8"))
    options = {"ability_gating": gating, "random_starting_abilities": 9, "minimum_health": 2}
    resolved = roll_triggers({game: options}, meta["triggers"], set())[game]
    assert resolved["random_starting_abilities"] == expected
    assert resolved["ability_gating"] == gating


def room16_artifact(launcher: ModuleType, root: Path, *, ability: str | None = None,
                    advanced: int = 0, accessibility: int = 0, placed: list[str] | None = None,
                    weight: int = 0) -> tuple[dict[str, object], dict[str, object]]:
    from .test_traversal import policy
    from ..traversal import SourcePolicy
    raw = policy(2 if ability is None else 1, weight=weight).policy
    if ability is not None:
        for seed in range(1000):
            raw['seed'] = seed
            if SourcePolicy(raw).grant('FOLEY', lambda _: True).guaranteed == {ability}:
                break
        else:
            raise AssertionError('No assigned Foley test seed')
    options = {'game': 'Kirby & The Amazing Mirror', 'accessibility': accessibility,
               'room_sanity': 1, 'advanced_logic': advanced, 'ability_randomization_mode': raw['mode']}
    for key in ('ability_randomization_boss_spawns', 'ability_randomization_minibosses',
                'ability_randomization_passive_enemies', 'ability_randomization_no_ability_weight'):
        options[key] = int(raw[key])
    proof = {'schema': 1, 'player': 1, 'seed': 456, 'room_sanity': 1,
             'advanced_logic': advanced, 'source_policy': raw}
    message = (launcher.CHECK_ERROR_PREFIX + '\nPlayer 1 (1-0): unfilled=[]; '
               "unavailable even with all inventory=['Room 4-16']; "
               f'unreachable from placed progression={placed or []!r}')
    log = ('Generating for 1 player, 123 Seed 456 with plando: items, connections, texts, bosses\n'
           'P1 Rolled options (1-0/Kirby & The Amazing Mirror): ' + json.dumps(options) + '\n'
           + launcher.ROOM16_EVIDENCE_PREFIX + json.dumps(proof) + '\n'
           'Traceback (most recent call last):\n  File "world.py", line 1, in stage_pre_output\n'
           '  File "check_accessibility.py", line 2, in validate_all_checks\n'
           + launcher.CHECK_ERROR_TYPE + ': ' + message + '\n')
    case = root / 'error/kirbyam/1'
    case.mkdir(parents=True)
    (case / '1.log').write_text(log)
    (case / '1-0.yaml').write_text('game: Kirby & The Amazing Mirror\n')
    return {'stats': {'total': 4, 'success': 3, 'failure': 1, 'timeout': 0, 'ignored': 0},
            'errors': {'kirbyam': {message: [1]}}}, proof


@pytest.mark.parametrize('ability,advanced,weight,accepted', [
    (None, 0, 0, True), (None, 1, 50, True), (None, 0, 100, True),
    ('Beam', 0, 0, True), ('Crash', 0, 0, True), ('Magic', 0, 0, True), ('Ice', 0, 0, False),
    ('Bomb', 0, 0, False), ('UFO', 0, 0, False),
    ('Crash', 1, 0, False), ('Magic', 1, 0, False), ('Ice', 1, 0, False),
])
@pytest.mark.parametrize('accessibility', [0, 2])
def test_room16_proof_reconstructs_actual_source_and_advanced_exclusion(
    tmp_path: Path, ability: str | None, advanced: int, weight: int, accepted: bool, accessibility: int,
) -> None:
    launcher = load_launcher()
    report, _ = room16_artifact(launcher, tmp_path, ability=ability, advanced=advanced,
                               weight=weight, accessibility=accessibility)
    outcomes = launcher.classify_minimal_rejections(report, tmp_path, minimal=False, room16=True)
    assert bool(outcomes['unsafe_rejected']) is accepted
    assert bool(outcomes['unclassified']) is not accepted
    if accepted:
        assert outcomes['unsafe_rejected'][0]['inventory_unreachable'] == ['Room 4-16']
        assert outcomes['unsafe_rejected'][0]['source_policy_sha256']


@pytest.mark.parametrize('accessibility,accepted', [(0, False), (2, True)])
def test_room16_other_placement_failures_only_allowed_under_existing_minimal_contract(
    tmp_path: Path, accessibility: int, accepted: bool,
) -> None:
    launcher = load_launcher()
    report, _ = room16_artifact(launcher, tmp_path, accessibility=accessibility, placed=['A chest'])
    outcomes = launcher.classify_minimal_rejections(report, tmp_path, room16=True)
    assert bool(outcomes['unsafe_rejected']) is accepted


@pytest.mark.parametrize('change', [
    'no_proof', 'duplicate_proof', 'after_traceback', 'schema', 'player', 'seed', 'seed_bool',
    'room_sanity', 'advanced_logic', 'advanced_bool', 'no_policy', 'missing_mode', 'unknown_policy_field',
    'mode', 'mode_bool', 'missing_seed', 'seed_range', 'mapping', 'bad_pool', 'duplicate_pool', 'narrow_pool',
    'eligibility', 'eligibility_type', 'weight', 'minny', 'extra_check', 'unfilled',
    'wrong_exception', 'trailing_error', 'missing_stack', 'missing_yaml', 'multiple_options',
])
def test_room16_source_proof_fails_closed_on_incomplete_or_mismatched_evidence(tmp_path: Path, change: str) -> None:
    launcher = load_launcher()
    report, proof = room16_artifact(launcher, tmp_path)
    path = tmp_path / 'error/kirbyam/1/1.log'
    log = path.read_text()
    old = launcher.ROOM16_EVIDENCE_PREFIX + json.dumps(proof)
    raw = proof['source_policy']
    assert isinstance(raw, dict)
    if change in ('schema', 'player', 'seed', 'room_sanity', 'advanced_logic'):
        proof[change] = 9
    elif change == 'seed_bool': proof['seed'] = True
    elif change == 'advanced_bool': proof['advanced_logic'] = False
    elif change == 'no_policy': proof['source_policy'] = None
    elif change == 'missing_mode': raw.pop('mode')
    elif change == 'unknown_policy_field': raw['unreviewed'] = True
    elif change == 'mode': raw['mode'] = 1
    elif change == 'mode_bool': raw['mode'] = True
    elif change == 'missing_seed': raw.pop('seed')
    elif change == 'seed_range': raw['seed'] = -1
    elif change == 'mapping': raw['mapping_style'] = 'wrong'
    elif change == 'bad_pool': raw['allowed_abilities'] = ['Invalid']
    elif change == 'duplicate_pool': raw['allowed_abilities'].append(raw['allowed_abilities'][0])
    elif change == 'narrow_pool': raw['allowed_abilities'] = ['Beam']
    elif change == 'eligibility': raw['ability_randomization_boss_spawns'] = False
    elif change == 'eligibility_type': raw['ability_randomization_boss_spawns'] = 1
    elif change == 'weight': raw['ability_randomization_no_ability_weight'] = 100
    elif change == 'minny': raw['ability_randomization_minny'] = True
    log = log.replace(old, launcher.ROOM16_EVIDENCE_PREFIX + json.dumps(proof))
    current = launcher.ROOM16_EVIDENCE_PREFIX + json.dumps(proof)
    if change == 'no_proof': log = log.replace(current + '\n', '')
    elif change == 'duplicate_proof': log = log.replace(current, current + '\n' + current)
    elif change == 'after_traceback':
        log = log.replace(current + '\n', '').replace('Traceback (most recent call last):',
                                                      'Traceback (most recent call last):\n' + current)
    elif change == 'trailing_error': log += 'RuntimeError: extra\n'
    elif change == 'missing_yaml': (path.parent / '1-0.yaml').unlink()
    elif change == 'multiple_options':
        line = next(line for line in log.splitlines() if line.startswith('P1 Rolled options'))
        log = line + '\n' + log
    replacements = {
        'extra_check': ("inventory=['Room 4-16']", "inventory=['Room 4-16', 'Another']"),
        'unfilled': ('unfilled=[]', "unfilled=['Room 4-16']"),
        'wrong_exception': (launcher.CHECK_ERROR_TYPE, 'RuntimeError'),
        'missing_stack': ('in stage_pre_output', 'in generate_early'),
    }
    if change in replacements:
        before, after = replacements[change]
        log = log.replace(before, after)
        report['errors']['kirbyam'] = {message.replace(before, after): cases
                                       for message, cases in report['errors']['kirbyam'].items()}
    path.write_text(log)
    outcomes = launcher.classify_minimal_rejections(report, tmp_path, room16=True)
    assert not outcomes['unsafe_rejected']
    assert len(outcomes['unclassified']) == 1


@pytest.mark.parametrize('key,value', [
    ('fail_closed', False), ('required_for_generation', True), ('advanced_graphs', ['hub4_crash_entry']),
    ('requires_guaranteed_source', {'source_key': 'FOLEY', 'abilities': ['Beam']}),
    ('graphs', {}), ('exit', 'OTHER'), ('requires_any_guaranteed_source', []),
])
def test_room16_classifier_rejects_changed_catalog_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, key: str, value: object,
) -> None:
    from copy import deepcopy
    from .. import traversal_data
    launcher = load_launcher()
    report, _ = room16_artifact(launcher, tmp_path)
    rows = deepcopy(traversal_data.room_traversal_targets('switch'))
    row = next(row for row in rows if row['id'] == 'switch_533_room16')
    row[key] = value
    monkeypatch.setattr(traversal_data, 'room_traversal_targets', lambda kind: rows)
    assert not launcher.classify_minimal_rejections(report, tmp_path, room16=True)['unsafe_rejected']


def test_room16_opt_in_is_separate_and_preserves_raw_report_and_success_floor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    launcher = load_launcher()
    assert not launcher.parse_args([]).classify_room16_rejections
    assert launcher.parse_args(['--classify-room16-rejections']).classify_room16_rejections
    report, _ = room16_artifact(launcher, tmp_path)
    before = json.dumps(report)
    monkeypatch.setattr(launcher, 'OUTPUT_DIR', tmp_path)
    args = launcher_args(runs=4, classify_minimal_rejections=True)
    assert launcher.report_result(args, report, 1) == 1
    args.classify_room16_rejections = True
    args.classify_minimal_rejections = False
    assert launcher.report_result(args, report, 1) == 0
    assert json.dumps(report) == before
    report['stats'].update(total=3, success=1, failure=2)
    assert launcher.validate_report(report, expected_runs=3, allow_ignored=False,
                                    unsafe_rejected=2) == ['fewer than 50% of attempts succeeded; safety rejections are not playable generations']


def test_classifier_consumes_actual_validator_proof_schema(tmp_path: Path) -> None:
    from ..check_accessibility import _room16_source_rejection_evidence
    launcher = load_launcher()
    report, expected = room16_artifact(launcher, tmp_path)
    raw = expected['source_policy']
    value = lambda n: SimpleNamespace(value=n)
    options = SimpleNamespace(room_sanity=value(1), accessibility=value(0), advanced_logic=value(0),
                              ability_randomization_mode=value(raw['mode']))
    mw = SimpleNamespace(players=1, seed=456,
                         worlds={1: SimpleNamespace(options=options, _enemy_copy_ability_policy=raw)})
    actual = _room16_source_rejection_evidence(mw, 1, [], ['Room 4-16'], [])
    assert actual == expected
    path = tmp_path / 'error/kirbyam/1/1.log'
    path.write_text(path.read_text().replace(json.dumps(expected),
                                            json.dumps(actual, sort_keys=True, separators=(',', ':'))))
    result = launcher.classify_minimal_rejections(report, tmp_path, minimal=False, room16=True)
    assert len(result['unsafe_rejected']) == 1 and not result['unclassified']
    assert result['unsafe_rejected'][0]['source_proof'] == actual


def test_room16_flag_alone_does_not_enable_minimal_placement_classification(tmp_path: Path) -> None:
    launcher = load_launcher()
    report = rejection_artifact(launcher, tmp_path)
    result = launcher.classify_minimal_rejections(report, tmp_path, minimal=False, room16=True)
    assert not result['unsafe_rejected'] and len(result['unclassified']) == 1



def test_room16_classifier_direct_script_import_path(tmp_path: Path) -> None:
    """Exercise script-path isolation without importing unrelated world plugins."""
    import os
    import subprocess
    import sys
    launcher = load_launcher()
    report, _ = room16_artifact(launcher, tmp_path)
    report_path = tmp_path / 'report.json'
    report_path.write_text(json.dumps(report))
    code = (
        # unittest activates the existing AP_TEST_WORLDS loader filter; it
        # supplies no repository path. Keep -I and the pre-import path check.
        'import json, runpy, sys, unittest; from pathlib import Path; '
        'assert "pytest" not in sys.modules; '
        'assert str(Path(sys.argv[1]).resolve().parents[1]) not in sys.path; '
        'module = runpy.run_path(sys.argv[1]); '
        'root = Path(sys.argv[2]); '
        'report = json.loads((root / "report.json").read_text()); '
        'result = module["classify_minimal_rejections"](report, root, minimal=False, room16=True); '
        'assert len(result["unsafe_rejected"]) == 1, result; '
        'assert not result["unclassified"], result'
    )
    completed = subprocess.run([sys.executable, '-I', '-c', code, str(LAUNCHER_PATH), str(tmp_path)],
                               cwd=tmp_path, capture_output=True, text=True, timeout=60,
                               env={**os.environ, "AP_TEST_WORLDS": "kirbyam"})
    assert completed.returncode == 0, completed.stdout + completed.stderr


@pytest.mark.parametrize("profile", ["live", "all_normal", "completion_live", "completion_all_normal"])
@pytest.mark.parametrize("mutation", ["none", "autoworld_note", "other_note", "disabled", "wrong_mode", "wrong_weight",
                                      "wrong_type", "wrong_stack", "budget", "missing_yaml", "duplicate_options", "other_goal"])
def test_early_room16_rejection_requires_exact_profile_and_terminal_error(
    tmp_path: Path, profile: str, mutation: str,
) -> None:
    from ..options import Goal
    from ..peg_traversal import (
        ROOM16_LIVE_REJECTION, ROOM16_WEIGHT_REJECTION,
        ROOM16_COMPLETION_LIVE_REJECTION, ROOM16_COMPLETION_WEIGHT_REJECTION,
    )

    launcher = load_launcher()
    live = profile.endswith("live")
    completion = profile.startswith("completion")
    messages = ([ROOM16_COMPLETION_WEIGHT_REJECTION, ROOM16_COMPLETION_LIVE_REJECTION] if completion
                else [ROOM16_WEIGHT_REJECTION, ROOM16_LIVE_REJECTION])
    message = messages[live]
    options = {"game": "Kirby & The Amazing Mirror", "accessibility": 2,
               "room_sanity": int(not completion), "advanced_logic": 0,
               "goal": Goal.option_full_completion if completion else Goal.option_dark_mind,
               "ability_randomization_mode": 2 if live else 1,
               "ability_randomization_no_ability_weight": 55 if live else 100}
    last_frame = "validate_peg_assignment"
    error_type = "worlds.kirbyam.peg_traversal.KirbyAmRoom16SourceError"
    if mutation == "disabled":
        options["room_sanity"] = 0
        options["goal"] = Goal.option_dark_mind
    elif mutation == "other_goal":
        options["room_sanity"] = 1
        options["goal"] = Goal.option_dark_mind
    elif mutation == "wrong_mode":
        options["ability_randomization_mode"] = 0
    elif mutation == "wrong_weight":
        options["ability_randomization_no_ability_weight"] = -1 if live else 99
    elif mutation == "wrong_type":
        error_type = "ValueError"
    elif mutation == "wrong_stack":
        last_frame = "validate_all_checks"
    elif mutation == "budget":
        message = "KirbyAM RoomSanity requires Mustard Mountain Room 4-16, but the assignment budget expired."
    rolled = "P1 Rolled options (1-0/Kirby & The Amazing Mirror): " + json.dumps(options) + "\n"
    log = ('Generating for 1 player, 123 Seed 456 with plando: items, connections\n'
           + rolled * (2 if mutation == "duplicate_options" else 1)
           + 'Traceback (most recent call last):\n  File "world.py", line 1, in generate_early\n'
           + f'  File "peg_traversal.py", line 2, in {last_frame}\n'
           + error_type + ": " + message + "\n")
    if mutation in ("autoworld_note", "other_note"):
        player = 1 if mutation == "autoworld_note" else 2
        log += ("Exception in <bound method KirbyAmWorld.generate_early of "
                "<worlds.kirbyam.KirbyAmWorld object at 0xabcdef>> "
                f"for player {player}, named 1-0.\n")
    case = tmp_path / "error/kirbyam/1"
    case.mkdir(parents=True)
    (case / "1.log").write_text(log)
    if mutation != "missing_yaml":
        (case / "1-0.yaml").write_text("game: Kirby & The Amazing Mirror\n")
    report = {"stats": {"total": 4, "success": 3, "failure": 1, "timeout": 0, "ignored": 0},
              "errors": {"kirbyam": {message: [1]}}}
    classified = launcher.classify_minimal_rejections(report, tmp_path, minimal=False, room16=True)
    accepted = mutation in ("none", "autoworld_note") or (mutation == "other_goal" and not completion)
    assert len(classified["unsafe_rejected"]) == accepted
    if accepted:
        assert classified["unsafe_rejected"][0]["rejection_kind"] == (
            "room16_live_random_unsupported" if live else "room16_shuffled_no_ability"
        )
        assert classified["unsafe_rejected"][0]["stranded_checks"] == []
        assert report["stats"]["failure"] == 1
        opted_out = launcher.classify_minimal_rejections(report, tmp_path, room16=False)
        assert opted_out["unclassified"] and not opted_out["unsafe_rejected"]


@pytest.mark.parametrize("mutation", [
    "none", "missing_stage_marker", "wrong_player", "different_exception",
    "different_frame", "third_trace", "explicit_chain", "mixed_terminal",
])
def test_duplicate_early_room16_trace_must_be_identical_staged_relogging(
    tmp_path: Path, mutation: str,
) -> None:
    """Match the double traceback actually emitted by Actions run 44661585788."""
    from ..peg_traversal import ROOM16_LIVE_REJECTION as message

    launcher = load_launcher()
    options = {"game": "Kirby & The Amazing Mirror", "accessibility": 0, "advanced_logic": 1,
               "room_sanity": 1, "ability_randomization_mode": 2, "ability_randomization_no_ability_weight": 32}
    header = "Traceback (most recent call last):\n"
    marker = ("[P1] Generation stage 'generate_early' failed after 0.00s: "
              f"KirbyAmRoom16SourceError: {message}\n")
    last = ('  File "/repo/worlds/kirbyam/__init__.py", line 524, in generate_early\n'
            '  File "/repo/worlds/kirbyam/peg_traversal.py", line 104, in validate_peg_assignment\n')
    exc = "worlds.kirbyam.peg_traversal.KirbyAmRoom16SourceError: " + message + "\n"
    stage = ('  File "/repo/worlds/kirbyam/generation_logging.py", line 62, in generation_stage\n'
             '    yield stage_logger\n' + last + exc)
    terminal = ('  File "/repo/Main.py", line 76, in main\n'
                '  File "/repo/worlds/AutoWorld.py", line 193, in call_single\n'
                + last + exc + "Exception in <bound method KirbyAmWorld.generate_early of "
                "<worlds.kirbyam.KirbyAmWorld object at 0xabcdef>> for player 1, named 10-0.\n")
    if mutation == "missing_stage_marker":
        marker = ""
    elif mutation == "wrong_player":
        marker = marker.replace("[P1]", "[P2]")
    elif mutation == "different_exception":
        stage = stage.replace(exc, "RuntimeError: different failure\n")
    elif mutation == "different_frame":
        stage = stage.replace("line 104", "line 105")
    elif mutation == "third_trace":
        stage += header + stage
    elif mutation == "explicit_chain":
        stage += "\nThe above exception was the direct cause of the following exception:\n\n"
    elif mutation == "mixed_terminal":
        terminal = "Exception: different failure\n" + terminal
    log = ("Generating for 1 player, 27396741778576445969 Seed 344859219 with plando: items, connections\n"
           "P1 Rolled options (10-0/Kirby & The Amazing Mirror): " + json.dumps(options) + "\n"
           + marker + header + stage + header + terminal)
    case = tmp_path / "error/kirbyam/10"
    case.mkdir(parents=True)
    (case / "10.log").write_text(log)
    (case / "10-0.yaml").write_text("game: Kirby & The Amazing Mirror\n")
    report = {"stats": {"total": 4, "success": 3, "failure": 1, "timeout": 0, "ignored": 0},
              "errors": {"kirbyam": {message: [10]}}}
    classified = launcher.classify_minimal_rejections(report, tmp_path, room16=True)
    assert bool(classified["unsafe_rejected"]) is (mutation == "none")
    assert bool(classified["unclassified"]) is (mutation != "none")


@pytest.mark.parametrize("mutation", ["none", "budget", "advanced", "wrong_roster", "wrong_cut", "omitted_proof"])
def test_fixed_shuffle_roster_requires_reconstructed_cut(tmp_path: Path, mutation: str) -> None:
    from ..ability_randomization import build_enemy_copy_ability_policy
    from ..logic_aware_shuffle import ROSTER_EVIDENCE, ROSTER_REJECTION
    from ..options import Goal
    import random

    launcher = load_launcher()
    # Hosted case 141: Peppermint can use Missile, but two other targets
    # still require separate copies of the sole movable enemy Burning grant.
    raw = build_enemy_copy_ability_policy(random.Random(0), 1, True, True,
                                         include_passive_enemies=False, no_ability_weight=65)
    raw["seed"] = 8307571545629204188
    options = {"game": "Kirby & The Amazing Mirror", "accessibility": 2, "area_keys": 1, "room_sanity": 0,
               "goal": Goal.option_dark_mind, "advanced_logic": 0, "ability_randomization_mode": 1,
               "ability_randomization_statues": 1, "ability_randomization_no_ability_weight": 65,
               "ability_randomization_boss_spawns": 1, "ability_randomization_minibosses": 1,
               "ability_randomization_passive_enemies": 0}
    cut = {"ability": "Burning", "pool": "enemy", "available": 1,
           "targets": {"metal_141_left_forward": ["FLAMER"], "metal_176_goal2_drink": ["BATAFIRE"]}}
    if mutation == "advanced":
        options["advanced_logic"] = 1
    if mutation == "wrong_roster":
        raw["ability_randomization_no_ability_weight"] = 66
    if mutation == "wrong_cut":
        cut["ability"] = "Fire"
    message = ROSTER_REJECTION if mutation != "budget" else "KirbyAM bounded assignment search exhausted"
    trace = (
        '  File "/repo/worlds/kirbyam/__init__.py", line 475, in generate_early\n'
        '  File "/repo/worlds/kirbyam/peg_traversal.py", line 144, in validate_peg_assignment\n'
        '  File "/repo/worlds/kirbyam/logic_aware_shuffle.py", line 310, in constrain_shuffled_abilities\n'
        f"worlds.kirbyam.logic_aware_shuffle.KirbyAmShuffleRosterError: {message}\n"
    )
    log = (
        'Generating for 1 player, 123 Seed 313799105 with plando: items, connections\n'
        'P1 Rolled options (141-0/Kirby & The Amazing Mirror): ' + json.dumps(options) + "\n"
    )
    if mutation != "omitted_proof":
        log += ROSTER_EVIDENCE + json.dumps({"source_policy": raw, "shortage": cut}) + "\n"
    log += (
        f"[P1] Generation stage 'generate_early' failed after 0.70s: KirbyAmShuffleRosterError: {message}\n"
        'Traceback (most recent call last):\n'
        '  File "/repo/worlds/kirbyam/generation_logging.py", line 62, in generation_stage\n'
        + trace + 'Traceback (most recent call last):\n' + trace
    )
    case = tmp_path / "error/kirbyam/141"
    case.mkdir(parents=True)
    (case / "141.log").write_text(log)
    (case / "141-0.yaml").write_text("game: Kirby & The Amazing Mirror\n")
    report = successful_report(4)
    report["stats"].update(success=3, failure=1)
    report["errors"] = {"kirbyam": {message: [141]}}
    outcomes = launcher.classify_minimal_rejections(report, tmp_path, shuffle_roster=True)
    assert bool(outcomes["unsafe_rejected"]) is (mutation == "none")
    assert bool(outcomes["unclassified"]) is (mutation != "none")
    assert report["stats"]["failure"] == 1
    if mutation == "none":
        assert outcomes["unsafe_rejected"][0]["source_proof"]["shortage"] == cut
        assert launcher.classify_minimal_rejections(report, tmp_path)["unclassified"]
