"""Protect the reviewed Normal baseline from losing or overclaiming evidence."""
import json

import pytest

from ..tools.audit_normal_baseline import BASELINE, read_baseline


def test_normal_baseline_matches_every_addressed_check():
    raw = read_baseline()
    groups = raw["addressed_checks"]
    assert len(groups["proven"]) == 334
    assert len(groups["not_normal_in_reviewed_layout"]) == 59
    assert set(groups["not_normal_in_reviewed_layout"]) >= {3960205, 3960567, 3960587}
    assert not groups["unproven"]
    assert {row["id"]: row["patch_condition"] for row in groups["proven_with_patch"]} == {
        3960575: "candy_linked_west_fuse",
        3961117: "mustard_room_16_timer_600",
    }
    assert raw["goal_events"]["requires_independent_completion_requirements"] == ["GOAL_100_PERCENT"]


@pytest.mark.parametrize("defect", ["duplicate", "missing", "invented_goal", "unknown_patch"])
def test_baseline_rejects_coverage_and_scope_drift(tmp_path, defect):
    raw = json.loads(BASELINE.read_text(encoding="utf-8"))
    checks = raw["addressed_checks"]
    if defect == "duplicate":
        checks["proven"].append(checks["not_normal_in_reviewed_layout"][0])
    elif defect == "missing":
        checks["not_normal_in_reviewed_layout"].pop()
    elif defect == "invented_goal":
        raw["goal_events"]["combat_feasible_not_goal_completion"].append("GOAL_UNKNOWN")
    else:
        checks["proven_with_patch"][0]["patch_condition"] = "unknown_profile"
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError, match="Normal baseline"):
        read_baseline(bad)


@pytest.mark.parametrize("keys", [False, True])
@pytest.mark.parametrize("mode", [0, 2])
def test_all_proven_normal_examples_are_possible_in_applicable_probes(keys, mode):
    from ..tools.audit_normal_baseline import compare

    report = compare(area_keys=keys, randomize=mode)
    assert not report["applicable_positive_ids_unreachable"]
    assert not report["unproven"]


def test_moonlight_normal_backfeed_retains_lever_and_compartment_boundaries():
    from BaseClasses import CollectionState
    from test.general import setup_multiworld

    from .. import KirbyAmWorld
    from ..data import data

    mw = setup_multiworld(KirbyAmWorld, steps=("generate_early", "create_regions", "set_rules"), seed=1197,
                          options={"room_sanity": True, "area_keys": False})
    world = mw.worlds[1]
    moon = "REGION_MOONLIGHT_MANSION/"
    wall = moon + "ROOM_2_11_AFTER_LEVER"
    dead_end = moon + "ROOM_2_11_DEAD_END"
    bottom = moon + "ROOM_2_01_BOTTOM_RIGHT"
    upper = moon + "ROOM_2_01__LOGIC__RIGHT_TOP"
    lower_706 = moon + "ROOM_2_03_LOWER"
    allowed = {wall, dead_end, bottom, upper, lower_706,
               *(moon + room for room in ("ROOM_2_05", "ROOM_2_05_LOWER",
                                          "ROOM_2_06", "ROOM_2_GOAL_1"))}
    allowed |= {key for key in data.regions if key.endswith("__ROOM_CHECK")}
    for region in mw.get_regions(1):
        region.exits = [edge for edge in region.exits
                        if region.name in allowed and edge.connected_region.name in allowed]
    mw.get_region("Menu", 1).connect(mw.get_region(wall, 1))
    assert not CollectionState(mw).can_reach_region(dead_end, 1)
    state = CollectionState(mw)
    state.collect(world.create_item(data.items[data.item_key_to_id["LEVER_WALL_MOONLIGHT_MANSION_2_11"]].label),
                  prevent_sweep=True)
    assert all(state.can_reach_region(key, 1) for key in (dead_end, bottom, upper, lower_706))
    assert not state.can_reach_region(moon + "ROOM_2_01", 1)
    assert not state.can_reach_region(moon + "ROOM_2_01_PAST_METAL_BLOCKS", 1)
    assert {loc.address for loc in mw.get_locations(1) if loc.address in {
        3960703, 3961071, 3961073, 3961074,
    } and loc.can_reach(state)} == {3960703, 3961071, 3961073, 3961074}
    assert bottom not in data.regions[upper].exits
    assert wall not in data.regions[dead_end].exits
