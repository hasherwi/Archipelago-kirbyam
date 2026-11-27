"""Protect the reviewed Normal baseline from losing or overclaiming evidence."""
import json

import pytest

from ..tools.audit_normal_baseline import BASELINE, read_baseline


def test_normal_baseline_matches_every_addressed_check():
    raw = read_baseline()
    groups = raw["addressed_checks"]
    assert len(groups["proven"]) == 334
    assert len(groups["not_normal_in_reviewed_layout"]) == 56
    assert groups["unproven"] == [3960205, 3960567, 3960587]
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
        checks["proven"].append(checks["unproven"][0])
    elif defect == "missing":
        checks["unproven"].pop()
    elif defect == "invented_goal":
        raw["goal_events"]["combat_feasible_not_goal_completion"].append("GOAL_UNKNOWN")
    else:
        checks["proven_with_patch"][0]["patch_condition"] = "unknown_profile"
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ValueError, match="Normal baseline"):
        read_baseline(bad)
