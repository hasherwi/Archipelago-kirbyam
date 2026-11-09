"""229 acceptance is a joint Hammer suffix, not a generic room/channel rule."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from .evidence_helpers import canonical_text_bytes


ROOT = Path(__file__).parents[1]
ARTIFACTS = {
    "renewable": ("ordinary-229-renewable-hammer-left1up-acceptance.json",
                  "9f96dfb3a558f59efe130d8b2abb6aecb0d94291"),
    "finite": ("ordinary-229-finite-hammer-left1up-acceptance.json",
               "8d1c41e11c8ccb1f8d83e2aa143e6491f3140b7a"),
    "ownership": ("ordinary-229-static-channel-ownership.json", "ee6df89296c52c7f61b7853075450d40a6fad3b4"),
}


def artifact(kind: str) -> dict[str, Any]:
    name, sha = ARTIFACTS[kind]
    raw = canonical_text_bytes(ROOT / "dev-docs" / name)
    assert hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == sha
    result: dict[str, Any] = json.loads(raw)
    return result


@pytest.mark.parametrize("kind", ["finite", "renewable"])
@pytest.mark.parametrize("health", [100, 500])
def test_actual_joint_prefix_continuation_is_continuous_and_terminal(kind: str, health: int) -> None:
    record = artifact(kind)
    run, = (r for r in record["acceptances"] if r["health_percent"] == health)
    assert run["accepted_left1up"] and run["runtime_writes"] == []
    assert len(run["segments"]) == 20
    previous = run["initial"]
    assert previous == {
        "frame": 0, "room": 228, "x": 472.35546875, "y": 200.99609375,
        "hp": 6, "ability": 17, "flag23": 128, "flag30": 64,
        "flag32": 0, "flag33": 0, "flag34": 0, "room_slot1": 0,
    }
    for segment in run["segments"]:
        assert segment["initial"] == previous
        assert segment["final"]["frame"] - previous["frame"] == sum(step[0] for step in segment["inputs"])
        assert segment["minimum_hp"] == segment["final"]["hp"] == 6
        assert segment["abilities"] == [17] and segment["grab_values"] == [0]
        assert segment["final"]["flag23"] == 128 and segment["final"]["flag30"] == 64
        assert segment["final"]["flag32"] == segment["final"]["flag34"] == 0
        previous = segment["final"]
    assert previous == run["final"]
    assert (previous["frame"], previous["room"], previous["x"], previous["y"], previous["flag33"]) == (
        3829, 229, 105.99609375, 440.99609375, 2)
    segments = {s["name"]: s for s in run["segments"]}
    arrival = segments["leftdoorapproach"]["final"]
    assert (arrival["room"], arrival["x"], arrival["y"]) == (229, 264, 456.99609375)
    assert segments["recovermetal"]["collision_changes"] == [
        {"x": 4, "y": 27, "before": 245, "after": 0},
        {"x": 5, "y": 27, "before": 245, "after": 0},
    ]
    assert any(e.get("frame") == 3511 and e.get("values") == [0, 0, 0, 0, 0]
               for e in segments["recovermetal"]["room_slot_events"])
    assert any(e.get("frame") == 3682 and e.get("flags32_34_masked") == 2
               for e in segments["collect229"]["room_slot_events"])
    # The native switch is already off while a slide passes the moving door.
    events = segments["slidegate"]["room_slot_events"]
    assert {"frame": 1318, "room": 228, "room_slot1": 0} in events
    crossing = [e for e in events if e.get("event") == "gate_crossing"]
    assert [e["threshold"] for e in crossing] == [214, 208, 200, 192, 186, 170]
    assert all(e["animation"] == 13 and e["room_slot1"] == 0 for e in crossing)


def test_source_fixture_qualifications_are_inherited_not_replaced() -> None:
    finite, renewable = artifact("finite"), artifact("renewable")
    assert renewable["inherited_prefix_blob"] == "a4cca011f7f5d2e3ada5600c116a1f6b5663e74c"
    assert finite["parent_finite_228_blob"] == "d050d3a81c862617fc45cf8fde2a6c61d158d5bd"
    assert finite["matching_renewable_229_suffix_blob"] == ARTIFACTS["renewable"][1]
    qualification = finite["inherited_finite_source_qualification"]
    assert "not a new combined Bonkers fight/capture replay" in qualification["source"]
    assert "not a full generated AP seed or direct1HP replay" in qualification["health"]
    scaler = qualification["max_health_scaler"]
    raw = canonical_text_bytes(ROOT / "enemy_health_scaling.py")
    assert hashlib.sha256(raw).hexdigest() == scaler["sha256"]
    assert hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == scaler["git_blob"]
    assert renewable["source"]["original_sha1"] == "274b102b6d940f46861a92b4e65f89a51815c12c"
    assert renewable["source"]["source_revision"] == "7d969fbce14fdc838d2c1ea01389717fb96c3189"
    for comparison in finite["endpoint_comparison"]:
        assert comparison["bridge_additional_inputs"] == []
        assert comparison["initial_scalar_readbacks_equal"]
        assert comparison["all_segment_final_scalar_readbacks_equal"]
        assert comparison["all_segment_collision_changes_equal"] and comparison["identical_controller_inputs"]
        assert comparison["enemy_state_equality"].startswith("Not asserted")
    switch = renewable["switch_source_semantics"]
    assert (switch["switch_template"], switch["sliding_door_template"], switch["timer_u16_at_0x18"],
            switch["room_state_slot"]) == ("0x088C04B4", "0x088C0490", 60, 1)


def test_static_channels_identify_other_checks_without_certifying_joins() -> None:
    record = artifact("ownership")
    assert record["kind"] == "static_ownership_not_additional_route_acceptance"
    assert record["accepted_left1up_blob"] == ARTIFACTS["renewable"][1]
    assert [(d["trigger"], d["spawn_tile"]) for d in record["source_doors_from_228"]] == [
        ([16, 4], [17, 29]), ([22, 4], [23, 29]), ([28, 4], [29, 29])]
    checks = {c["flag"]: c for row in record["ownership"] for c in row["checks"]}
    assert {flag: (c["ap_id"], c["template"], c["position"]) for flag, c in checks.items()} == {
        33: (3960593, "0x088C06B4", [104, 440]),
        34: (3960594, "0x088C06D8", [152, 248]),
        32: (3960508, "0x088C0648", [584, 136]),
    }
    grid = record["native_geometry"]["collision_rows"]
    assert grid[27][4:6] == [245, 245] and grid[15][10:13] == [240, 240, 240]
    assert record["warp"]["native_destination"] == 230
    assert record["warp"]["door_record"]["trigger"] == [22, 3]
    assert "not accepted" in record["internal_join_boundary"]["unverified"]
