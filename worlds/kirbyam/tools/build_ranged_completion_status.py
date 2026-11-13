"""Report bounded ranged source-policy coverage, not gameplay completion.

Run as a module from the repository root. --check detects declaration drift;
no generated report needs to be checked in. The installer is exercised by the
companion tests, not by this read-only report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any, cast

from ..ability_randomization import build_enemy_copy_ability_policy
from ..enemy_ability_data import VALID_ENEMY_COPY_ABILITIES
from ..traversal import SourcePolicy
from ..traversal_data import _room_catalog
from ..traversal_rules import target_applies
from .build_ranged_target_coverage import ROOT, build_coverage

CONTRACT = ROOT / "dev-docs/ranged-completion-scope.json"


def policy_profiles(*, synthetic: bool = False) -> dict[str, SourcePolicy]:
    """Public option shapes are samples, not generation-accepted seed claims."""
    def make(mode: int, weight: int = 0, *, passive: bool = True,
             pool: list[str] | None = None) -> SourcePolicy:
        kwargs: dict[str, Any] = {} if pool is None else {"whitelist": pool}
        return SourcePolicy(build_enemy_copy_ability_policy(
            random.Random(427), mode, True, True, include_passive_enemies=passive,
            no_ability_weight=weight, **kwargs,
        ))

    if synthetic:
        # These narrow pools are internal diagnostics. No public custom-whitelist
        # option exists, and a singleton fixture is not an accepted seed.
        return {
            **{f"singleton_{ability}": make(1, pool=[ability]) for ability in sorted(VALID_ENEMY_COPY_ABILITIES)},
            "mixed_Beam_Spark": make(2, pool=["Beam", "Spark"]),
            "failure_Beam_50": make(2, 50, pool=["Beam"]),
        }
    return {
        "native": make(0),
        "shuffled_seed427": make(1),
        "full_live_normal0": make(2),
        "full_live_normal99": make(2, 99),
        "full_live_normal100": make(2, 100),
        "full_live_passive_excluded": make(2, passive=False),
    }


def load_contract() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(CONTRACT.read_text()))


def source_conditions(row: dict[str, Any]) -> list[dict[str, Any]]:
    return row.get("requires_any_guaranteed_source", []) or (
        [row["requires_guaranteed_source"]] if row.get("requires_guaranteed_source") else []
    )


def build_status() -> dict[str, Any]:
    contract = load_contract()
    coverage = build_coverage()
    targets, _, _ = _room_catalog()
    by_id = {row["id"]: row for row in targets}
    profiles = policy_profiles()
    diagnostics = policy_profiles(synthetic=True)
    rows = []
    errors = []
    for target_id in contract["bounded_targets"]:
        if target_id not in by_id:
            errors.append(f"Declared bounded target is absent: {target_id}")
            continue
        row = by_id[target_id]
        conditions = source_conditions(row)
        rows.append({
            "id": target_id, "native_room": row["native_room"], "owner": row["region"],
            "surface_kind": "exit" if row.get("exit") else "location",
            "surface": row.get("exit") or row["location"],
            "witnesses": list(row["graphs"]), "target_source_conditions": conditions,
            "coverage": "partial_source_policy" if conditions else "bounded_installed",
            "public_fallback_profiles": [name for name, policy in profiles.items() if not target_applies(row, policy)],
            "synthetic_applicable_profiles": [name for name, policy in diagnostics.items()
                                              if target_applies(row, policy)],
        })
    actual_conditional = sorted(row["id"] for row in targets if source_conditions(row))
    if actual_conditional != sorted(contract["policy_fallback_targets"]):
        errors.append("Conditional target inventory changed; review and update the declared coverage.")
    actual_fallbacks = {
        name: sorted(row["id"] for row in targets if not target_applies(row, policy))
        for name, policy in profiles.items()
    }
    if actual_fallbacks != contract["public_profile_fallbacks"]:
        errors.append("Public-profile fallback coverage changed; review and update the declaration and tests together.")
    if contract["completion_claim"] != "partial" or not contract["unresolved_evidence"]:
        errors.append("This bounded inventory cannot certify completion; an evidence review is required.")
    if not set(actual_conditional) <= set(contract["bounded_targets"]):
        errors.append("A conditional target is absent from the bounded scope.")
    inputs = dict(coverage["input_sha256"])
    for name in (
        "ability_randomization.py", "enemy_ability_data.py", "enemy_ability_runtime_patch.py", "options.py",
        "traversal.py", "traversal_data.py", "traversal_rules.py", "rules.py", "master_source.py",
        "tools/build_ranged_completion_status.py", "tools/build_ranged_target_coverage.py",
        "dev-docs/ranged-completion-scope.json", "dev-docs/ranged-static-target-census.json",
        "dev-docs/small-switch-inventory.json", "dev-docs/main-ranged-union-catalog.json",
    ):
        inputs[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    fingerprint = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
    census = json.loads((ROOT / "dev-docs/ranged-static-target-census.json").read_text())
    union = json.loads((ROOT / "dev-docs/main-ranged-union-catalog.json").read_text())
    switches = json.loads((ROOT / "dev-docs/small-switch-inventory.json").read_text())
    return {
        "schema_version": 1, "completion": "partial", "declaration_errors": errors,
        "scope": "Bounded target installation/source-policy inventory; not all move-by-surface acceptance.",
        "limits": contract["unresolved_evidence"],
        "input_fingerprint_sha256": fingerprint, "input_sha256": inputs,
        "counts": {**coverage["counts"], "normalized_targets": len(targets),
                   "top_level_union_targets": len(union["targets"]),
                   "witnesses": sum(len(row["graphs"]) for row in targets),
                   "static_F1_F6_cells": sum(len(row["targets"]) for row in census["tile_targets"]),
                   "static_small_switches": switches["scan"]["switch_instances"]},
        "public_profiles": {
            name: {"mode": policy.mode, "pool_size": len(policy.policy["allowed_abilities"]),
                   "normal_weight": policy.policy["ability_randomization_no_ability_weight"],
                   "passive_enemies": policy.policy["ability_randomization_passive_enemies"],
                   "fallback_targets": actual_fallbacks[name]}
            for name, policy in profiles.items()
        },
        "profile_boundary": "Public option shapes built with seed 427, not generation acceptance or all seeds/options.",
        "synthetic_boundary": "Internal narrowed pools only; there is no public custom-whitelist option.",
        "fallback_boundary": ("The extra installer leaves the base rule unchanged; "
                              "this does not prove a physical softlock."),
        "targets": rows,
    }


def format_summary(status: dict[str, Any]) -> str:
    counts = status["counts"]
    lines = [
        "Ranged completion: PARTIAL (bounded source-policy report, not native acceptance)",
        f"Inputs SHA-256: {status['input_fingerprint_sha256']}",
        f"AP structure: {counts['regions']} regions, {counts['locations']} locations, {counts['surfaces']} surfaces; "
        f"{counts['normalized_targets']} targets / {counts['witnesses']} witnesses.",
        f"Static inventory: {counts['static_F1_F6_cells']} F1/F6 cells, "
        f"{counts['static_small_switches']} small switches; these are not counts of missing gates.",
    ]
    for row in status["targets"]:
        fallback = ", ".join(row["public_fallback_profiles"]) or "none in sampled profiles"
        lines.append(f"{row['id']}: {row['coverage']}; base-rule fallback: {fallback}.")
    lines.extend([status["profile_boundary"], status["synthetic_boundary"], status["fallback_boundary"]])
    lines.extend(f"Unresolved: {limit}" for limit in status["limits"])
    lines.extend(f"DECLARATION ERROR: {error}" for error in status["declaration_errors"])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Write JSON; otherwise print a concise status summary.")
    parser.add_argument("--check", action="store_true", help="Fail on coverage declaration drift, not known open gaps.")
    args = parser.parse_args()
    status = build_status()
    if args.output:
        args.output.write_text(json.dumps(status, indent=2) + "\n")
    else:
        print(format_summary(status), end="")
    if args.check and status["declaration_errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
