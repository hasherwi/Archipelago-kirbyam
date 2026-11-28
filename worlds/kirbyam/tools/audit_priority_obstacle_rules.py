"""Trace compact metal, peg, rope, and fuse declarations to exact solver targets."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from ..conditional_routes import CANDY_FUSE
from ..data import data
from ..rules import normal_movement_satisfies_requirement
from ..traversal_data import _room_catalog
from .audit_legacy_ability_surfaces import tokens

CANDY_FUSE_FALLBACK = CANDY_FUSE.TARGET

KINDS = {
    "metal": {"can_break_metal", "can_break_metal_throw"},
    "peg": {"can_pound_pegs", "CanPoundPegs"},
    "fuse": {"can_light_fuses", "CanLightFuses"},
    "rope": {"can_cut_ropes", "CanCutRopes"},
}


def _target_identity(row: dict) -> tuple[str, str, str]:
    kind = "exit" if row.get("exit") else "location"
    return row["region"], kind, row[kind]


def _target_name(identity: tuple[str, str, str]) -> str:
    owner, kind, target = identity
    dest = (f"`{target.removeprefix('REGION_')}`" if kind == "exit"
            else f"{data.locations[target].label} ({data.locations[target].location_id})")
    return f"`{owner.removeprefix('REGION_')}` → {dest}"


def audit() -> str:
    all_targets, _, _ = _room_catalog()
    compact = defaultdict(dict)
    targets = defaultdict(list)
    for row in all_targets:
        family = "fuse" if row["id"] == CANDY_FUSE_FALLBACK else row["kind"]
        if family in KINDS:
            targets[family].append(row)

    for owner, region in data.regions.items():
        for kind, rules in (("exit", region.exit_requirements), ("location", region.location_requirements)):
            for destination, requirement in rules.items():
                terms = set(tokens(requirement))
                for family, aliases in KINDS.items():
                    if matched := terms & aliases:
                        compact[family][owner, kind, destination] = ", ".join(sorted(matched))

    output = [
        "# Metal, peg, fuse, and rope solver targets",
        "",
        "Generated from the compiled room and traversal catalogs. Region names below omit the common",
        "`REGION_` prefix; the arrow is directional. A check row includes its AP location ID.",
        "An exact match uses the same obstacle family, AP owner, and exit or location—not merely the same native room.",
        "",
        "| Family | Explicit compact sites | Same-family exact matches | Catalog targets |",
        "| --- | ---: | ---: | ---: |",
    ]
    sections = []
    for family in KINDS:
        counts: Counter[str] = Counter()
        declared = compact[family]
        matched = set()
        section = [f"## {family.title()}", "",
                   "| Door / check | Catalog target and witness notes | Compact token |",
                   "| --- | --- | --- |"]
        for row in sorted(targets[family], key=lambda item: item["id"]):
            identity = _target_identity(row)
            if identity in declared:
                matched.add(identity)
            flags = []
            if row.get("advanced_graphs"):
                flags.append("has Advanced-only variants")
            if row.get("requires_guaranteed_source") or row.get("requires_any_guaranteed_source"):
                flags.append("conditional on source policy")
            if row.get("fail_closed"):
                flags.append("fails closed when unsupported")
            if row["id"] == CANDY_FUSE_FALLBACK:
                flags.append("block-family target with a profile-specific linked-fuse fallback")
            if row.get("new_connection"):
                flags.append("explicit new connection")
            notes = "" if not flags else "; " + "; ".join(flags)
            counts[identity[1]] += 1
            token = declared.get(identity, "—")
            if token != "—":
                token = f"`{token}`"
            section.append(f"| {_target_name(identity)} | `{row['id']}`{notes} | {token} |")
        for identity, token in sorted(declared.items()):
            if identity not in matched:
                section.append(f"| {_target_name(identity)} | No exact same-family target | `{token}` |")
        exits, checks = counts["exit"], counts["location"]
        output.append(f"| {family.title()} | {len(declared)} | {len(matched)} | {exits + checks} "
                      f"({exits} {'exit' if exits == 1 else 'exits'}, "
                      f"{checks} {'check' if checks == 1 else 'checks'}) |")
        sections.extend(["", *section])

    output.extend(sections)
    return "\n".join(output) + "\n"


def audit_generic_blocks() -> str:
    aliases = {"CanBreakBlocks", "can_break_block", "can_break_floating_block"}
    overlay_by_target = defaultdict(list)
    for row in _room_catalog()[0]:
        overlay_by_target[_target_identity(row)].append(row["id"])
    buckets = {
        "Exact catalog overlay": [],
        "Declared Normal alternative (not physical proof)": [],
        "No direct overlay or declared Normal alternative": [],
    }
    for owner, region in data.regions.items():
        for kind, rules in (("exit", region.exit_requirements), ("location", region.location_requirements)):
            for destination, requirement in rules.items():
                if not aliases.intersection(tokens(requirement)):
                    continue
                identity = owner, kind, destination
                overlays = overlay_by_target.get(identity, [])
                if overlays:
                    bucket = "Exact catalog overlay"
                elif normal_movement_satisfies_requirement(requirement):
                    bucket = "Declared Normal alternative (not physical proof)"
                else:
                    bucket = "No direct overlay or declared Normal alternative"
                buckets[bucket].append((identity, requirement, overlays))

    output = [
        "# Generic block labels: door and check inventory",
        "",
        "One row per compiled solver surface using a generic or floating block token.",
        "The arrow is directional; room keys omit `REGION_`. The exact compact expression is preserved.",
        "A matching overlay may enforce a different obstacle or be conditional. A missing direct",
        "overlay does not rule out an upstream gate, a verified Normal route, or a bypass.",
        "",
        "| Classification | Entrances | Checks |",
        "| --- | ---: | ---: |",
    ]
    for heading, rows in buckets.items():
        counts = Counter(identity[1] for identity, _, _ in rows)
        output.append(f"| {heading} | {counts['exit']} | {counts['location']} |")

    for heading, rows in buckets.items():
        output.extend(["", f"## {heading}", "",
                       "| Door / check | Compact expression | Exact overlay |",
                       "| --- | --- | --- |"])
        for identity, requirement, overlays in sorted(rows, key=lambda row: (row[0][1] != "location", row[0])):
            expression = json.dumps(requirement, separators=(",", ": "))
            names = ", ".join(f"`{name}`" for name in overlays) or "—"
            output.append(f"| {_target_name(identity)} | `{expression}` | {names} |")
    return "\n".join(output) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--generic-blocks", action="store_true", help="Audit generic and floating block labels")
    args = parser.parse_args()
    report = audit_generic_blocks() if args.generic_blocks else audit()
    args.output.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
