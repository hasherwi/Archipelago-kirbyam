"""Run the pinned Archipelago generation fuzzer against KirbyAM."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import platform
import re
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
FUZZER_META_PATH = REPO_ROOT / "tools" / "kirbyam_generation_fuzz_meta.yaml"
OUTPUT_DIR = REPO_ROOT / "fuzz_output"
REPORT_PATH = OUTPUT_DIR / "report.json"
METADATA_PATH = OUTPUT_DIR / "metadata.json"
CLASSIFICATION_FILENAME = "classified_outcomes.json"
CHECK_ERROR_TYPE = "worlds.kirbyam.check_accessibility.KirbyAmCheckAccessibilityError"
CHECK_ERROR_PREFIX = (
    "KirbyAM all-check validation failed. Every enabled Kirby check must be reachable, "
    "including with minimal accessibility. Generation stopped before the normal output/archive stage. "
    "Try full accessibility or another seed; source/route restrictions may still require review."
)


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
    parser.add_argument("--classify-minimal-rejections", action="store_true",
                        help="Separately classify evidenced minimal placed-progression safety rejections. "
                             "Requires at least 50%% successful generations; never counts rejections as success.")
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
        command.extend(("--game", "kirbyam", "--meta", str(FUZZER_META_PATH)))
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


def _reported_failures(report: dict[str, Any]) -> list[tuple[str, str, int]]:
    """Reject ambiguous report mappings rather than subtracting guessed counts."""
    errors = report.get("errors")
    if not isinstance(errors, dict):
        raise ValueError("missing errors object")
    result = []
    seen: set[int] = set()
    for game, messages in errors.items():
        if not isinstance(game, str) or not isinstance(messages, dict):
            raise ValueError("invalid game error mapping")
        for message, cases in messages.items():
            if not isinstance(message, str) or not isinstance(cases, list) or not cases:
                raise ValueError("invalid error case mapping")
            for case in cases:
                if type(case) is not int or case < 0 or case in seen:
                    raise ValueError("invalid or duplicate error case ID")
                seen.add(case)
                result.append((game, message, case))
    stats = report.get("stats", {})
    if len(result) != stats.get("failure", 0) + stats.get("timeout", 0):
        raise ValueError("error case count does not match failure + timeout")
    return sorted(result, key=lambda row: row[2])


def _minimal_rejection_evidence(message: str, log: str) -> dict[str, Any]:
    """Accept only a terminal, sole guard exception with single-player evidence.

    The pinned fuzzer erases exception types in report.json. Its untouched log
    supplies the exact type/trace and actual rolled options, not guessed YAML
    defaults. A changed format fails closed and needs deliberate review.
    """
    diagnostic = re.fullmatch(
        re.escape(CHECK_ERROR_PREFIX) + r"\nPlayer 1 \([^\n]+\): unfilled=\[\]; "
        r"unavailable even with all inventory=\[\]; unreachable from placed progression=(\[[^\n]+\])",
        message,
    )
    if diagnostic is None:
        raise ValueError("not a single-player, filled, all-inventory-feasible safety rejection")
    checks = ast.literal_eval(diagnostic[1])
    if not isinstance(checks, list) or not checks or not all(isinstance(check, str) and check for check in checks):
        raise ValueError("missing stranded check names")
    mixed_markers = ("ExceptionGroup", "During handling of the above exception",
                     "The above exception was the direct cause")
    if log.count("Traceback (most recent call last):") != 1 or any(marker in log for marker in mixed_markers):
        raise ValueError("missing, mixed, or chained exception traceback")
    if not log.rstrip().endswith(CHECK_ERROR_TYPE + ": " + message):
        raise ValueError("terminal exception does not match report and guard type")
    if "in stage_pre_output" not in log or "in validate_all_checks" not in log:
        raise ValueError("missing final all-check validation stack")
    rolled = re.findall(r"^P(\d+) Rolled options \([^\n]+\): (.+)$", log, re.MULTILINE)
    if len(rolled) != 1 or rolled[0][0] != "1":
        raise ValueError("not a single-player rolled-options record")
    options = json.loads(rolled[0][1])
    if (not isinstance(options, dict) or options.get("game") != "Kirby & The Amazing Mirror"
            or type(options.get("accessibility")) is not int or options["accessibility"] != 2):
        raise ValueError("actual selected accessibility is not Kirby minimal")
    seeds = re.findall(r"^Generating for 1 player, \d+ Seed (\d+) with plando: .+$", log, re.MULTILINE)
    if len(seeds) != 1:
        raise ValueError("missing single-player generation seed")
    return {"seed": int(seeds[0]), "rolled_options": options, "stranded_checks": checks}


def classify_minimal_rejections(report: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    """Keep raw failures unchanged and add an auditable, narrowly scoped outcome."""
    result: dict[str, Any] = {
        "schema_version": 1, "policy": "single_player_minimal_placed_progression_only",
        "raw_stats": report.get("stats"), "unsafe_rejected": [], "unclassified": [], "errors": [],
    }
    try:
        cases = _reported_failures(report)
    except (ValueError, TypeError, AttributeError) as exc:
        result["errors"].append(str(exc))
        return result
    for game, message, case in cases:
        try:
            if game != "kirbyam":
                raise ValueError("not a KirbyAM failure")
            case_dir = output_dir / "error" / "kirbyam" / str(case)
            log_path = case_dir / f"{case}.log"
            log = log_path.read_text(encoding="utf-8-sig")
            evidence = _minimal_rejection_evidence(message, log)
            yamls = sorted(case_dir.glob("*.yaml"))
            if len(yamls) != 1 or not yamls[0].read_bytes():
                raise ValueError("missing single-player YAML reproducer")
            result["unsafe_rejected"].append({
                "case": case, **evidence,
                "log": log_path.relative_to(output_dir).as_posix(),
                "log_sha256": hashlib.sha256(log_path.read_bytes()).hexdigest(),
                "yaml": yamls[0].relative_to(output_dir).as_posix(),
                "yaml_sha256": hashlib.sha256(yamls[0].read_bytes()).hexdigest(),
            })
        except (OSError, ValueError, SyntaxError, TypeError) as exc:
            result["unclassified"].append({"case": case, "reason": str(exc)})
    return result


def validate_report(
    report: dict[str, Any],
    *,
    expected_runs: int,
    allow_ignored: bool,
    unsafe_rejected: int = 0,
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
    if type(unsafe_rejected) is not int or not 0 <= unsafe_rejected <= failure:
        messages.append("invalid unsafe rejection count")
        unsafe_rejected = 0
    if failure > unsafe_rejected:
        messages.append(f"{failure - unsafe_rejected} generation failure(s)")
    if unsafe_rejected and (not stats["success"] or stats["success"] * 2 < total):
        messages.append("fewer than 50% of attempts succeeded; safety rejections are not playable generations")
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
            "classify_minimal_rejections": args.classify_minimal_rejections,
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

    return report_result(args, report, completed.returncode)


def report_result(args: argparse.Namespace, report: dict[str, Any], returncode: int) -> int:
    unsafe_rejected = 0
    classification_errors: list[str] = []
    if args.classify_minimal_rejections:
        outcomes = classify_minimal_rejections(report, OUTPUT_DIR)
        unsafe_rejected = len(outcomes["unsafe_rejected"])
        classification_errors = outcomes["errors"]
        (OUTPUT_DIR / CLASSIFICATION_FILENAME).write_text(json.dumps(outcomes, indent=2) + "\n", encoding="utf-8")

    validation_messages = validate_report(
        report,
        expected_runs=args.runs,
        allow_ignored=args.allow_ignored,
        unsafe_rejected=unsafe_rejected,
    ) + classification_errors
    stats = report.get("stats")
    if not isinstance(stats, dict):
        stats = {}
    print(
        "Result: "
        f"{stats.get('success', '?')} succeeded, "
        f"{stats.get('failure', '?')} raw failures ({unsafe_rejected} classified unsafe rejections), "
        f"{stats.get('timeout', '?')} timed out, "
        f"{stats.get('ignored', '?')} ignored"
    )
    for message in validation_messages:
        print(f"ERROR: {message}", file=sys.stderr)

    if returncode not in (0, 1):
        return returncode
    explained_failure_exit = unsafe_rejected > 0 and unsafe_rejected == stats.get("failure")
    if validation_messages or (returncode and not explained_failure_exit):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
