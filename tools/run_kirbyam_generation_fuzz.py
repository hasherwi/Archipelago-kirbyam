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
    parser.add_argument("--classify-room16-rejections", action="store_true",
                        help="Separately classify exact Room16 exclusions with structured source-policy proof. "
                             "Never counts rejections as playable generations.")
    parser.add_argument("--classify-shuffle-roster-rejections", action="store_true",
                        help="Separately classify proven fixed Standard Shuffle roster shortages, not search exhaustion.")
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
    context = _rejection_context(message, log)
    if context["rolled_options"]["accessibility"] != 2:
        raise ValueError("actual selected accessibility is not Kirby minimal")
    return {**context, "stranded_checks": checks}


TRACEBACK_HEADER = "Traceback (most recent call last):"
TRACEBACK_FRAME = re.compile(r'^  File "([^\n]+)", line (\d+), in (\w+)$', re.MULTILINE)
TRACEBACK_EXCEPTION = re.compile(r"^[\w.]+:.*$", re.MULTILINE)


def _is_relogged_early_exception(
    parts: list[str], error_type: str, message: str, frames: tuple[str, ...], files: tuple[str, ...],
) -> bool:
    """Require generation_stage to log precisely the same exception again."""
    preamble, stage_trace, terminal_trace = parts
    exception_line = error_type + ": " + message
    stage_marker = (
        r"\[P1\] Generation stage 'generate_early' failed after \d+\.\d{2}s: "
        + re.escape(error_type.rsplit(".", 1)[1] + ": " + message)
    )
    if not re.fullmatch(stage_marker, preamble.rstrip().splitlines()[-1] if preamble.strip() else ""):
        return False
    if not stage_trace.rstrip().endswith("\n" + exception_line):
        return False
    if any(TRACEBACK_EXCEPTION.findall(trace) != [exception_line] for trace in (stage_trace, terminal_trace)):
        return False
    stage_frames = TRACEBACK_FRAME.findall(stage_trace)
    terminal_frames = TRACEBACK_FRAME.findall(terminal_trace)
    if tuple(frame[2] for frame in stage_frames) != ("generation_stage", *frames):
        return False
    if tuple(frame[0].replace("\\", "/").rsplit("/", 1)[-1] for frame in stage_frames) != ("generation_logging.py", *files):
        return False
    return stage_frames[1:] == terminal_frames[-len(frames):]


def _rejection_context(
    message: str, log: str, *, error_type: str = CHECK_ERROR_TYPE,
    frames: tuple[str, ...] = ("stage_pre_output", "validate_all_checks"),
    early_files: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Validate the shared terminal exception and actual generation envelope."""
    mixed_markers = ("ExceptionGroup", "During handling of the above exception",
                     "The above exception was the direct cause")
    parts = log.split(TRACEBACK_HEADER)
    has_single_trace = len(parts) == 2
    same_early_exception_logged_twice = (
        early_files and len(parts) == 3 and _is_relogged_early_exception(parts, error_type, message, frames, early_files)
    )
    if (not has_single_trace and not same_early_exception_logged_twice
            or any(marker in log for marker in mixed_markers)):
        raise ValueError("missing, mixed, or chained exception traceback")
    terminal = log.rstrip()
    if early_files:
        # AutoWorld.call_single attaches exactly one player/method note on Python 3.11+.
        terminal = re.sub(
            r"\nException in <bound method KirbyAmWorld\.generate_early of "
            r"<worlds\.kirbyam\.KirbyAmWorld object at 0x[0-9A-Fa-f]+>> "
            r"for player 1, named [^\n]+\.\Z",
            "", terminal, count=1,
        )
    if not terminal.endswith(error_type + ": " + message):
        raise ValueError("terminal exception does not match report and guard type")
    trace_frames = [frame[2] for frame in TRACEBACK_FRAME.findall(parts[-1])]
    if tuple(trace_frames[-len(frames):]) != frames:
        raise ValueError("missing expected validation stack")
    rolled = re.findall(r"^P(\d+) Rolled options \([^\n]+\): (.+)$", log, re.MULTILINE)
    if len(rolled) != 1 or rolled[0][0] != "1":
        raise ValueError("not a single-player rolled-options record")
    options = json.loads(rolled[0][1])
    if (not isinstance(options, dict) or options.get("game") != "Kirby & The Amazing Mirror"
            or type(options.get("accessibility")) is not int or options["accessibility"] not in (0, 2)):
        raise ValueError("actual selected accessibility is not supported Kirby full/minimal")
    seeds = re.findall(r"^Generating for 1 player, \d+ Seed (\d+) with plando: .+$", log, re.MULTILINE)
    if len(seeds) != 1:
        raise ValueError("missing single-player generation seed")
    return {"seed": int(seeds[0]), "rolled_options": options}


ROOM16_EVIDENCE_PREFIX = "KirbyAM Room16 rejection evidence: "


def _room16_rejection_evidence(message: str, log: str) -> dict[str, Any]:
    """Reconstruct only explicit source exclusions, never infer one from a closed edge."""
    # Direct ``python tools/run_kirbyam_generation_fuzz.py`` starts sys.path at
    # tools/, unlike pytest. The classifier intentionally imports the checked-out
    # production resolver, not an installed world or the fuzzer subprocess.
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from worlds.kirbyam.enemy_ability_data import VALID_ENEMY_COPY_ABILITIES
    from worlds.kirbyam.traversal import SourcePolicy
    from worlds.kirbyam.traversal_data import room_traversal_targets

    diagnostic = re.fullmatch(
        re.escape(CHECK_ERROR_PREFIX) + r"\nPlayer 1 \([^\n]+\): unfilled=\[\]; "
        r"unavailable even with all inventory=\['Room 4-16'\]; "
        r"unreachable from placed progression=(\[[^\n]*\])", message)
    if diagnostic is None:
        raise ValueError("not an exact filled single-player Room16 rejection")
    checks = ast.literal_eval(diagnostic[1])
    if not isinstance(checks, list) or not all(isinstance(check, str) and check for check in checks):
        raise ValueError("invalid placed-progression diagnostics")
    context = _rejection_context(message, log)
    options = context["rolled_options"]
    if options["accessibility"] == 0 and checks:
        raise ValueError("full accessibility has additional placed-progression failures")
    lines = [line for line in log.splitlines() if line.startswith(ROOM16_EVIDENCE_PREFIX)]
    if len(lines) != 1 or log.index(lines[0]) > log.index("Traceback (most recent call last):"):
        raise ValueError("missing, duplicated, or misplaced Room16 source proof")
    proof = json.loads(lines[0][len(ROOM16_EVIDENCE_PREFIX):])
    if not isinstance(proof, dict) or set(proof) != {
        "schema", "player", "seed", "room_sanity", "advanced_logic", "source_policy"
    }:
        raise ValueError("invalid Room16 source proof schema")
    for key, expected in (("schema", 1), ("player", 1), ("seed", context["seed"]), ("room_sanity", 1)):
        if type(proof[key]) is not int or proof[key] != expected:
            raise ValueError("Room16 source proof identity mismatch")
    for key in ("room_sanity", "advanced_logic"):
        if type(options.get(key)) is not int or options[key] not in (0, 1) or proof[key] != options[key]:
            raise ValueError("Room16 proof does not match rolled options")
    if type(proof["advanced_logic"]) is not int:
        raise ValueError("invalid Advanced Logic proof")
    raw = proof["source_policy"]
    if not isinstance(raw, dict) or type(raw.get("mode")) is not int or raw["mode"] not in (0, 1, 2):
        raise ValueError("missing or invalid source policy")
    if type(options.get("ability_randomization_mode")) is not int or raw["mode"] != options["ability_randomization_mode"]:
        raise ValueError("source mode differs from rolled options")
    keys = {"mode", "allowed_abilities", "ability_randomization_boss_spawns", "ability_randomization_minibosses",
            "ability_randomization_minny", "ability_randomization_passive_enemies", "ability_randomization_no_ability_weight"}
    keys |= {"identity_map"} if raw["mode"] == 0 else {"seed", "mapping_style"}
    if set(raw) != keys:
        raise ValueError("source policy is incomplete or has unreviewed fields")
    pool = raw["allowed_abilities"]
    if (not isinstance(pool, list) or not pool or not all(isinstance(name, str) for name in pool)
            or pool != sorted(VALID_ENEMY_COPY_ABILITIES)):
        raise ValueError("invalid source ability pool")
    for key in ("ability_randomization_boss_spawns", "ability_randomization_minibosses",
                "ability_randomization_passive_enemies"):
        if (type(raw[key]) is not bool or type(options.get(key)) is not int
                or options[key] not in (0, 1) or raw[key] != bool(options[key])):
            raise ValueError("source eligibility differs from rolled options")
    weight = raw["ability_randomization_no_ability_weight"]
    if (type(weight) is not int or not 0 <= weight <= 100
            or type(options.get("ability_randomization_no_ability_weight")) is not int
            or weight != options["ability_randomization_no_ability_weight"]
            or raw["ability_randomization_minny"] is not False):
        raise ValueError("source weight or legacy policy differs")
    if raw["mode"] == 0:
        if raw["identity_map"] != {name: name for name in pool}:
            raise ValueError("invalid native policy")
    elif (type(raw["seed"]) is not int or not 0 <= raw["seed"] < 2**64
          or raw["mapping_style"] != {1: "per_enemy_type", 2: "per_grant_event"}[raw["mode"]]):
        raise ValueError("invalid source mapping seed/style")
    rows = [row for row in room_traversal_targets("switch") if row["id"] == "switch_533_room16"]
    if len(rows) != 1:
        raise ValueError("Room16 catalog target changed")
    row = rows[0]
    if (row.get("fail_closed") is not True or row.get("required_for_generation") is not False
            or row.get("region") != "REGION_MUSTARD_MOUNTAIN/ROOM_4_15"
            or row.get("exit") != "REGION_MUSTARD_MOUNTAIN/ROOM_4_16" or row.get("native_room") != 533
            or "requires_any_guaranteed_source" in row
            or row.get("requires_guaranteed_source") != {"source_key": "FOLEY", "abilities": ["Bomb", "UFO", "Crash", "Magic", "Ice"]}
            or set(row["graphs"]) != {"hub4_entry", "hub4_ufo_entry", "hub4_crash_entry", "hub4_magic_entry", "hub4_ice_entry"}
            or row.get("advanced_graphs") != ["hub4_crash_entry", "hub4_magic_entry"]):
        raise ValueError("Room16 source/Advanced catalog contract changed")
    grant = SourcePolicy(raw).grant("FOLEY", lambda _: True).guaranteed
    if len(grant) != 1 or not grant <= {"Bomb", "UFO", "Crash", "Magic", "Ice"}:
        reason = "unqualified_foley_source"
    elif not proof["advanced_logic"] and grant <= {"Crash", "Magic"}:
        reason = "advanced_route_disabled"
    else:
        raise ValueError("qualified Room16 source failure requires investigation")
    return {**context, "stranded_checks": checks, "inventory_unreachable": ["Room 4-16"],
            "rejection_kind": reason, "source_proof": proof,
            "source_policy_sha256": hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest()}


def _early_room16_rejection_evidence(message: str, log: str) -> dict[str, Any]:
    """Classify only exact unsupported profiles requiring Room16."""
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from worlds.kirbyam.options import Goal
    from worlds.kirbyam.peg_traversal import (
        ROOM16_LIVE_REJECTION, ROOM16_WEIGHT_REJECTION,
        ROOM16_COMPLETION_LIVE_REJECTION, ROOM16_COMPLETION_WEIGHT_REJECTION,
    )

    room_sanity_messages = (ROOM16_LIVE_REJECTION, ROOM16_WEIGHT_REJECTION)
    completion_messages = (ROOM16_COMPLETION_LIVE_REJECTION, ROOM16_COMPLETION_WEIGHT_REJECTION)
    if message not in (*room_sanity_messages, *completion_messages):
        raise ValueError("not an exact unsupported Room16 configuration")
    context = _rejection_context(
        message, log,
        error_type="worlds.kirbyam.peg_traversal.KirbyAmRoom16SourceError",
        frames=("generate_early", "validate_peg_assignment"), early_files=("__init__.py", "peg_traversal.py"),
    )
    options = context["rolled_options"]
    sanity = options.get("room_sanity")
    mode = options.get("ability_randomization_mode")
    weight = options.get("ability_randomization_no_ability_weight")
    advanced = options.get("advanced_logic")
    goal = options.get("goal")
    if (type(sanity) is not int or sanity not in (0, 1) or type(mode) is not int
            or type(advanced) is not int or advanced not in (0, 1)
            or type(weight) is not int or not 0 <= weight <= 100):
        raise ValueError("invalid rolled Room16 options")
    if message in completion_messages:
        if type(goal) is not int or goal != Goal.option_full_completion:
            raise ValueError("rolled goal does not require completing Room16")
    elif sanity != 1:
        raise ValueError("rolled RoomSanity does not require Room16")
    if message in (ROOM16_LIVE_REJECTION, ROOM16_COMPLETION_LIVE_REJECTION) and mode == 2:
        reason = "room16_live_random_unsupported"
    elif message in (ROOM16_WEIGHT_REJECTION, ROOM16_COMPLETION_WEIGHT_REJECTION) and mode == 1 and weight == 100:
        reason = "room16_shuffled_no_ability"
    else:
        raise ValueError("rolled options do not match early Room16 rejection")
    return {**context, "stranded_checks": [], "rejection_kind": reason}


def _shuffle_roster_rejection_evidence(message: str, log: str) -> dict[str, Any]:
    """Check exact error, options and an independently reconstructed source cut."""
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from worlds.kirbyam.enemy_ability_data import VALID_ENEMY_COPY_ABILITIES
    from worlds.kirbyam.logic_aware_shuffle import ROSTER_EVIDENCE, ROSTER_REJECTION, proven_roster_shortage
    from worlds.kirbyam.options import Goal

    if message != ROSTER_REJECTION:
        raise ValueError("not the exact Standard Shuffle roster rejection")
    context = _rejection_context(
        message, log, error_type="worlds.kirbyam.logic_aware_shuffle.KirbyAmShuffleRosterError",
        frames=("generate_early", "validate_peg_assignment", "constrain_shuffled_abilities"),
        early_files=("__init__.py", "peg_traversal.py", "logic_aware_shuffle.py"),
    )
    proof_lines = [line for line in log.splitlines() if line.startswith(ROSTER_EVIDENCE)]
    if len(proof_lines) != 1 or log.index(proof_lines[0]) > log.index(TRACEBACK_HEADER):
        raise ValueError("missing, duplicated, or misplaced Shuffle roster proof")
    proof = json.loads(proof_lines[0][len(ROSTER_EVIDENCE):])
    if not isinstance(proof, dict) or set(proof) != {"source_policy", "shortage"}:
        raise ValueError("invalid Shuffle roster proof")
    raw = proof["source_policy"]
    options = context["rolled_options"]
    expected = {"ability_randomization_mode": 1, "advanced_logic": 0, "ability_randomization_statues": 1}
    if any(type(options.get(key)) is not int or options[key] != value for key, value in expected.items()):
        raise ValueError("rolled options are not Standard Shuffle with enabled world statues")
    flags = ("ability_randomization_boss_spawns", "ability_randomization_minibosses",
             "ability_randomization_passive_enemies")
    weight = "ability_randomization_no_ability_weight"
    if (not isinstance(raw, dict)
            or set(raw) != {"mode", "seed", "allowed_abilities", "mapping_style", "ability_randomization_minny",
                            weight, *flags}
            or type(raw["seed"]) is not int or not 0 <= raw["seed"] < 2**64
            or raw["allowed_abilities"] != sorted(VALID_ENEMY_COPY_ABILITIES)
            or raw["mapping_style"] != "per_enemy_type" or raw["ability_randomization_minny"] is not False
            or type(raw["mode"]) is not int or raw["mode"] != 1
            or type(options.get(weight)) is not int or type(raw[weight]) is not int
            or not 0 <= raw[weight] < 100 or raw[weight] != options[weight]):
        raise ValueError("invalid Shuffle source policy or mismatch with rolled weight")
    for key in flags:
        if (type(options.get(key)) is not int or options[key] not in (0, 1)
                or type(raw[key]) is not bool or raw[key] != bool(options[key])):
            raise ValueError("Shuffle source eligibility differs from rolled options")
    for key in ("room_sanity", "area_keys"):
        if type(options.get(key)) is not int or options[key] not in (0, 1):
            raise ValueError("invalid rolled Shuffle route options")
    if type(options.get("goal")) is not int or options["goal"] not in Goal.name_lookup:
        raise ValueError("invalid rolled Shuffle goal")
    cut = proven_roster_shortage(
        raw, include_statues=True, require_all=True, area_keys=bool(options["area_keys"]),
        room16=bool(options["room_sanity"]) or options["goal"] == Goal.option_full_completion,
    )
    if cut is None or cut != proof["shortage"]:
        raise ValueError("fixed roster shortage could not be reconstructed")
    return {**context, "stranded_checks": [], "rejection_kind": "shuffle_fixed_roster_shortage",
            "source_proof": proof,
            "source_policy_sha256": hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest()}


def classify_minimal_rejections(report: dict[str, Any], output_dir: Path, *,
                                minimal: bool = True, room16: bool = False,
                                shuffle_roster: bool = False) -> dict[str, Any]:
    """Keep raw failures unchanged and add an auditable, narrowly scoped outcome."""
    result: dict[str, Any] = {
        "schema_version": 3 if shuffle_roster else 2 if room16 else 1,
        "policy": ("single_player_explicit_fixed_shuffle_roster_exclusions" if shuffle_roster else
                   "single_player_explicit_room16_source_exclusions" if room16 else
                   "single_player_minimal_placed_progression_only"),
        "enabled_classifications": {"minimal_placement": minimal, "room16_source": room16,
                                    **({"shuffle_fixed_roster": True} if shuffle_roster else {})},
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
            if room16 and "unavailable even with all inventory=['Room 4-16']" in message:
                evidence = _room16_rejection_evidence(message, log)
            elif room16 and message.startswith((
                    "KirbyAM RoomSanity requires Mustard Mountain Room 4-16,",
                    "KirbyAM 100% Game Completion requires visiting Mustard Mountain Room 4-16,",
            )):
                evidence = _early_room16_rejection_evidence(message, log)
            elif shuffle_roster and message.startswith("KirbyAM Standard Shuffle cannot supply"):
                evidence = _shuffle_roster_rejection_evidence(message, log)
            elif minimal:
                evidence = _minimal_rejection_evidence(message, log)
            else:
                raise ValueError("rejection category was not opted in")
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
        except (OSError, ValueError, SyntaxError, TypeError, KeyError, IndexError, OverflowError) as exc:
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
            "classify_room16_rejections": getattr(args, "classify_room16_rejections", False),
            "classify_shuffle_roster_rejections": getattr(args, "classify_shuffle_roster_rejections", False),
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
    room16 = getattr(args, "classify_room16_rejections", False)
    shuffle_roster = getattr(args, "classify_shuffle_roster_rejections", False)
    if args.classify_minimal_rejections or room16 or shuffle_roster:
        outcomes = classify_minimal_rejections(report, OUTPUT_DIR, minimal=args.classify_minimal_rejections,
                                               room16=room16, shuffle_roster=shuffle_roster)
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
