"""Run the pinned Archipelago generation fuzzer against KirbyAM."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
FUZZER_PATH = REPO_ROOT / "tools" / "third_party" / "archipelago_fuzzer" / "fuzz.py"
FUZZER_REPOSITORY = "https://github.com/ionium-ap/Archipelago-fuzzer"
FUZZER_COMMIT = "ebe01d5523f04a2a0a1de5eb7229d10ef12b8fc2"
FUZZER_VERSION = "0.6.2"
FUZZER_SHA256 = "fbb3c0f19e1dc5a85c6e7f561a4f2cdc2d18c773f48238b4df0923b3c68ea35b"
OUTPUT_DIR = REPO_ROOT / "fuzz_output"
REPORT_PATH = OUTPUT_DIR / "report.json"
METADATA_PATH = OUTPUT_DIR / "metadata.json"


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return parsed


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the pinned Archipelago generation fuzzer against Kirby & The Amazing Mirror.",
    )
    parser.add_argument("--runs", type=positive_int, default=100, help="Generation attempts (default: 100).")
    parser.add_argument("--jobs", type=positive_int, default=min(4, os.cpu_count() or 1),
                        help="Parallel workers (default: min(4, CPU count)).")
    parser.add_argument("--timeout", type=nonnegative_int, default=60,
                        help="Per-generation timeout in seconds; zero disables it (default: 60).")
    parser.add_argument("--with-output", action="store_true",
                        help="Generate output archives and patches instead of stopping after fill/rules.")
    parser.add_argument("--sample-from", type=Path,
                        help="Replay YAML files from a directory instead of generating random KirbyAM YAMLs.")
    parser.add_argument("--allow-ignored", action="store_true",
                        help="Do not fail when the fuzzer reports ignored OptionError cases.")
    return parser.parse_args(argv)


def fuzzer_checksum(path: Path | None = None) -> str:
    path = FUZZER_PATH if path is None else path
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_vendored_fuzzer(path: Path | None = None, expected_sha256: str | None = None) -> None:
    path = FUZZER_PATH if path is None else path
    expected_sha256 = FUZZER_SHA256 if expected_sha256 is None else expected_sha256
    if not path.is_file():
        raise RuntimeError(f"Vendored fuzzer is missing: {path}")
    actual_sha256 = fuzzer_checksum(path)
    if actual_sha256 != expected_sha256:
        raise RuntimeError(
            "Vendored fuzzer checksum mismatch: "
            f"expected {expected_sha256}, got {actual_sha256}. "
            "Review the change and update the pinned provenance intentionally."
        )


def build_fuzzer_command(args: argparse.Namespace) -> list[str]:
    command = [
        sys.executable,
        str(FUZZER_PATH),
        "--runs",
        str(args.runs),
        "--jobs",
        str(args.jobs),
        "--timeout",
        str(args.timeout),
        "--dump-ignored",
    ]
    if args.sample_from is None:
        command.extend(("--game", "kirbyam"))
    else:
        command.extend(("--sample-from", str(args.sample_from.resolve())))
    if not args.with_output:
        command.append("--skip-output")
    return command


def load_report(path: Path | None = None) -> dict[str, Any]:
    path = REPORT_PATH if path is None else path
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read fuzzer report {path}: {exc}") from exc
    if not isinstance(report, dict):
        raise RuntimeError(f"Fuzzer report {path} is not a JSON object")
    return report


def validate_report(
    report: dict[str, Any],
    *,
    expected_runs: int,
    allow_ignored: bool,
) -> list[str]:
    stats = report.get("stats")
    if not isinstance(stats, dict):
        return ["report is missing a stats object"]

    required_keys = ("total", "success", "failure", "timeout", "ignored")
    invalid_keys = [key for key in required_keys if type(stats.get(key)) is not int or stats[key] < 0]
    if invalid_keys:
        return [f"report has invalid nonnegative integer stats: {', '.join(invalid_keys)}"]

    total = stats["total"]
    failure = stats["failure"]
    timeouts = stats["timeout"]
    ignored = stats["ignored"]
    messages: list[str] = []
    if total != expected_runs:
        messages.append(f"expected {expected_runs} completed runs, report contains {total}")
    if stats["success"] + failure + timeouts + ignored != total:
        messages.append("success + failure + timeout + ignored does not equal total")
    if failure:
        messages.append(f"{failure} generation failure(s)")
    if timeouts:
        messages.append(f"{timeouts} generation timeout(s)")
    if ignored and not allow_ignored:
        messages.append(f"{ignored} ignored OptionError case(s); use --allow-ignored only after review")
    return messages


def resolve_ap_commit() -> str:
    github_sha = os.environ.get("GITHUB_SHA")
    if github_sha:
        return github_sha
    completed = subprocess.run(
        ["git", "-c", f"safe.directory={REPO_ROOT.as_posix()}", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unknown"


def write_metadata(args: argparse.Namespace, command: Sequence[str], fuzzer_return_code: int) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    metadata = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "archipelago_commit": resolve_ap_commit(),
        "fuzzer": {
            "repository": FUZZER_REPOSITORY,
            "commit": FUZZER_COMMIT,
            "version": FUZZER_VERSION,
            "sha256": FUZZER_SHA256,
            "master_seed": None,
        },
        "python": sys.version,
        "platform": platform.platform(),
        "arguments": {
            "runs": args.runs,
            "jobs": args.jobs,
            "timeout": args.timeout,
            "skip_output": not args.with_output,
            "sample_from": str(args.sample_from.resolve()) if args.sample_from else None,
            "allow_ignored": args.allow_ignored,
        },
        "command": list(command),
        "fuzzer_return_code": fuzzer_return_code,
    }
    METADATA_PATH.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


def run(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.sample_from is not None and not args.sample_from.is_dir():
        print(f"Sample directory does not exist: {args.sample_from}", file=sys.stderr)
        return 2

    try:
        verify_vendored_fuzzer()
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 2

    command = build_fuzzer_command(args)
    environment = os.environ.copy()
    existing_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = os.pathsep.join(
        part for part in (str(REPO_ROOT), existing_pythonpath) if part
    )

    print(f"Archipelago-fuzzer {FUZZER_VERSION} ({FUZZER_COMMIT})", flush=True)
    print("Running:", " ".join(command), flush=True)
    try:
        completed = subprocess.run(command, cwd=REPO_ROOT, env=environment, check=False)
    except OSError as exc:
        print(f"Could not start generation fuzzer: {exc}", file=sys.stderr)
        return 2

    write_metadata(args, command, completed.returncode)
    try:
        report = load_report()
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return completed.returncode if completed.returncode else 2

    validation_messages = validate_report(
        report,
        expected_runs=args.runs,
        allow_ignored=args.allow_ignored,
    )
    stats = report.get("stats")
    if not isinstance(stats, dict):
        stats = {}
    print(
        "Result: "
        f"{stats.get('success', '?')} succeeded, "
        f"{stats.get('failure', '?')} failed, "
        f"{stats.get('timeout', '?')} timed out, "
        f"{stats.get('ignored', '?')} ignored"
    )
    for message in validation_messages:
        print(f"ERROR: {message}", file=sys.stderr)

    if completed.returncode not in (0, 1):
        return completed.returncode
    if validation_messages or completed.returncode:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
