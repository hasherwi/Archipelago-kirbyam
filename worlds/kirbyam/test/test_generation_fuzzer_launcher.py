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
    assert "--dump-ignored" in command


def test_sample_command_uses_samples_instead_of_game_selector(tmp_path: Path) -> None:
    launcher = load_launcher()
    command = launcher.build_fuzzer_command(launcher_args(sample_from=tmp_path, with_output=True))

    assert "--game" not in command
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
