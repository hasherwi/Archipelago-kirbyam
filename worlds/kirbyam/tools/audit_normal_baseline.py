"""Compare playthrough evidence to the compiled rules without changing those rules."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ..data import LocationCategory, data

BASELINE = Path(__file__).resolve().parents[1] / "dev-docs" / "normal-baseline-1059.json"
NO_COPY_OR_PHONE = {"Abilities", "Phone", "RoomAccess"}
PATCH_CONDITIONS = {"candy_linked_west_fuse", "mustard_room_16_timer_600"}


def read_baseline(path: Path = BASELINE) -> dict:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if type(raw.get("schema")) is not int or raw["schema"] != 1:
        raise ValueError("Unsupported Normal baseline schema")
    catalog = {row.location_id for row in data.locations.values() if row.category != LocationCategory.GOAL}
    groups = raw["addressed_checks"]
    if set(groups) != {"proven", "proven_with_patch", "not_normal_in_reviewed_layout", "unproven"}:
        raise ValueError("Unknown Normal baseline evidence group")
    ids = groups["proven"] + groups["not_normal_in_reviewed_layout"] + groups["unproven"]
    for row in groups["proven_with_patch"]:
        if row["patch_condition"] not in PATCH_CONDITIONS:
            raise ValueError("Unknown patch condition in Normal baseline")
        ids.append(row["id"])
    if any(type(item) is not int for item in ids) or set(ids) != catalog or len(ids) != len(catalog):
        raise ValueError("Normal baseline must cover each addressed check exactly once")
    goals = raw["goal_events"]
    expected_goals = {key for key, row in data.locations.items() if row.category == LocationCategory.GOAL}
    named = [key for keys in goals.values() for key in keys]
    if set(named) != expected_goals or len(named) != len(expected_goals):
        raise ValueError("Normal baseline goal evidence must match the canonical addressless goal catalog")
    return raw


def compare(*, area_keys: bool, randomize: int) -> dict:
    from BaseClasses import CollectionState
    from test.general import setup_multiworld

    from .. import KirbyAmWorld, room16_timer
    from ..traversal import SourcePolicy

    raw = read_baseline()
    areas = raw["addressed_checks"]
    mw = setup_multiworld(KirbyAmWorld, steps=("generate_early", "create_regions", "set_rules"), seed=1197,
                          options={"room_sanity": True, "area_keys": area_keys, "ability_gating": True,
                                   "random_starting_mirror": False, "goal": "dark_mind",
                                   "ability_randomization_mode": randomize,
                                   "ability_randomization_no_ability_weight": 100})
    world = mw.worlds[1]
    state = CollectionState(mw, allow_partial_entrances=False)
    forbidden_labels = {row.label for row in data.items.values() if row.tags & NO_COPY_OR_PHONE}
    for item in mw.precollected_items[1]:
        if item.name in forbidden_labels:
            state.remove(item)
    for row in data.items.values():
        if row.label not in forbidden_labels:
            state.collect(world.create_item(row.label), prevent_sweep=True)
    state.sweep_for_advancements()
    reachable = {loc.address for loc in mw.get_locations(1) if loc.address is not None and loc.can_reach(state)}
    patch_state = {
        "candy_linked_west_fuse": world._candy912_linked_west_fuse,
        "mustard_room_16_timer_600": room16_timer.enabled(SourcePolicy(world._enemy_copy_ability_policy)),
    }
    with_patch = [row["id"] for row in areas["proven_with_patch"] if patch_state[row["patch_condition"]]]
    without_patch = [row["id"] for row in areas["proven_with_patch"] if not patch_state[row["patch_condition"]]]
    return {
        "area_keys": area_keys, "ability_randomization_mode": randomize,
        "applicable_positive_ids_unreachable": sorted(set(areas["proven"] + with_patch) - reachable),
        "reviewed_negative_ids_reachable_without_copy_items": sorted(set(areas["not_normal_in_reviewed_layout"]) & reachable),
        "unproven": {loc: loc in reachable for loc in areas["unproven"]},
        "patch_qualified_not_compared": without_patch,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", type=Path, help="Optional file for the comparison report.")
    out = parser.parse_args().json
    rows = [compare(area_keys=keys, randomize=mode) for mode in (0, 2) for keys in (False, True)]
    report = json.dumps(rows, indent=2) + "\n"
    if out:
        out.write_text(report, encoding="utf-8")
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
