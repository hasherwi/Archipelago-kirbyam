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
    "normal_warp": ("ordinary-229-normal-warp-acceptance.json", "eeaef7ebfeb06ca175e981a6545dfe51d4cf5c84"),
    "normal_food": ("ordinary-229-normal-food-acceptance.json", "ba9a355d1310eb506283f3c461673cdfc6373ae3"),
    "normal_spray": ("ordinary-229-normal-spray-acceptance.json", "631e98ce077825127401ad4150ff882ee2fd93c5"),
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


@pytest.mark.parametrize("health", [100, 500])
def test_normal_warp_frontier_preserves_metal_and_other_check_boundaries(health: int) -> None:
    record = artifact("normal_warp")
    assert record["schema"] == "ordinary-229-normal-warp-acceptance-v1"
    assert record["upstream_finite_blob"] == "d050d3a81c862617fc45cf8fde2a6c61d158d5bd"
    assert record["source_revision"] == "7d969fbce14fdc838d2c1ea01389717fb96c3189"
    assert "Does not certify Normal access through upstream205 or Spray32/food34" in record["claim"]
    assert "Actual Select discardsHammer in205 before228 entry" in record["qualification"]
    run, = (r for r in record["accepted"] if r["enemy_health_percent"] == health)
    segments = run["segments"]
    assert len(segments) == (8 if health == 100 else 9)
    previous_frame = 0
    for segment in segments:
        final = segment["final"]
        assert final["frame"] - previous_frame == sum(step[0] for step in segment["inputs"])
        assert segment["minimum_hp"] == final["hp"] == 6 and segment["grabs"] == [0]
        assert segment["flags23_30_32_33_34"] == [128, 0, 0, 0, 0]
        if segment["id"] == "jointHammer205spikegap":
            # Only the inherited approach to the independent Normal frontier still carries Hammer.
            assert health == 500 and final["room"] == 205
            assert segment["abilities"] == [17] and final["ability"] == 17
        else:
            assert segment["abilities"] == [0] and final["ability"] == 0
            if final["room"] == 228:
                assert segment["F5_27_23_24"] == [245, 245]
        previous_frame = final["frame"]
    normal_segments = [s for s in segments if s["id"] != "jointHammer205spikegap"]
    assert sum(step[0] for s in normal_segments for step in s["inputs"]) == 2538
    entry = normal_segments[0]
    assert entry["id"] == "normal228entry" and entry["inputs"][0] == [1, 4]
    assert (entry["final"]["room"], entry["final"]["x"], entry["final"]["y"]) == (228, 408, 456.99609375)
    final = normal_segments[-1]["final"]
    assert (final["room"], final["x"], final["y"]) == (230, 360, 277.00390625)
    assert set(record["unresolved"]) == {"Spray32", "food34", "boundary"}
    assert "do not prove permanent channel isolation" in record["unresolved"]["boundary"]


@pytest.mark.parametrize("kind", ["food", "spray"])
@pytest.mark.parametrize("health", [100, 500])
def test_normal_food_and_spray_keep_the_actual_frontier_and_own_check(kind: str, health: int) -> None:
    record = artifact("normal_" + kind)
    assert record["schema"] == f"ordinary-229-normal-{kind}-acceptance-v1"
    assert record["upstream_finite_blob"] == "d050d3a81c862617fc45cf8fde2a6c61d158d5bd"
    assert record["source_revision"] == "7d969fbce14fdc838d2c1ea01389717fb96c3189"
    assert "Actual Select discardsHammer in205 before228 entry" in record["qualification"]
    assert "no terrain or room228/229 object edits, no RAM writes" in record["qualification"]
    assert "flag23 is inherited and not part of independent access claim" in record["qualification"]
    run, = (r for r in record["accepted"] if r["enemy_health_percent"] == health)
    warp, = (r for r in artifact("normal_warp")["accepted"] if r["enemy_health_percent"] == health)
    assert (run["rom_sha256"], run["initial_checkpoint"]) == (warp["rom_sha256"], warp["initial_checkpoint"])
    # Both independently replay the same ordinary entrance, before the three paths diverge.
    prefix_length = 5 if health == 100 else 6
    assert run["segments"][:prefix_length] == warp["segments"][:prefix_length]
    previous_frame = 0
    for segment in run["segments"]:
        final = segment["final"]
        assert final["frame"] - previous_frame == sum(step[0] for step in segment["inputs"])
        assert segment["minimum_hp"] == final["hp"] == 6 and segment["grabs"] == [0]
        assert segment["flags23_30_32_33_34"][:2] == [128, 0]
        if segment["id"] == "jointHammer205spikegap":
            assert health == 500 and final["room"] == 205
            assert segment["abilities"] == [17] and final["ability"] == 17
        else:
            assert segment["abilities"] == [0] and final["ability"] == 0
            if final["room"] == 228:
                assert segment["F5_27_23_24"] == [245, 245]
        previous_frame = final["frame"]
    segments = [s for s in run["segments"] if s["id"] != "jointHammer205spikegap"]
    assert segments[0]["id"] == "normal228entry" and segments[0]["inputs"][0] == [1, 4]
    assert (segments[0]["final"]["room"], segments[0]["final"]["x"], segments[0]["final"]["y"]) == (
        228, 408, 456.99609375)
    assert all(s["flags23_30_32_33_34"] == [128, 0, 0, 0, 0] for s in segments[:-1])
    expected = (4847, 16, 150, 248.99609375, [128, 0, 0, 0, 4]) if kind == "food" else (
        3206 if health == 100 else 2976, 10 if health == 100 else 11,
        585.99609375, 136.99609375, [128, 0, 1, 0, 0])
    frames, count, x, y, flags = expected
    assert len(segments) == count and sum(step[0] for s in segments for step in s["inputs"]) == frames
    assert (segments[-1]["final"]["room"], segments[-1]["final"]["x"], segments[-1]["final"]["y"]) == (229, x, y)
    assert segments[-1]["flags23_30_32_33_34"] == flags


@pytest.mark.parametrize("health", [100, 500])
def test_normal_food_uses_a_fresh_timed_plate_and_ordinary_interior_blocks(health: int) -> None:
    record = artifact("normal_food")
    run, = (r for r in record["accepted"] if r["enemy_health_percent"] == health)
    segments = {s["id"]: s for s in run["segments"]}
    switch = segments["normal228switchredash"]
    assert switch["inputs"][:5] == [[70, 32], [90, 0], [5, 16], [5, 0], [50, 16]]
    assert (switch["final"]["room"], switch["final"]["x"], switch["final"]["y"]) == (228, 170.953125, 136.99609375)
    arrival = segments["normal229leftdoor"]["final"]
    assert (arrival["room"], arrival["x"], arrival["y"]) == (229, 264, 456.99609375)
    assert segments["normal229foodapproach"]["F0_10_11_12_row15"] == [240, 240, 240]
    assert segments["normal229foodbreak"]["F0_10_11_12_row15"] == [240, 240, 0]
    assert segments["normal229foodhole"]["F0_10_11_12_row15"] == [0, 0, 0]
    assert segments["normal229foodhole"]["inputs"][-2:] == [[1, 64], [60, 0]]
    assert "actual ordinary body contact, not inherited Hammer trigger" in record["qualifications_additional"]
    assert "not permanent gate opening" in record["qualifications_additional"]


@pytest.mark.parametrize("health", [100, 500])
def test_normal_spray_destroys_mirra_at_the_exact_threat_boundary_before_actual_entry(health: int) -> None:
    record = artifact("normal_spray")
    assert "abs(dx)<48" in record["mirra"]["threat_boundary"]
    audit, = (a for a in record["mirra"]["actual_boundary_audits"] if a["enemy_health_percent"] == health)
    events = {e["frame"]: e for e in audit["events"]}
    assert all(e["hp"] == 6 and e["ability"] == 0 for e in events.values())
    assert all(e["x"] == 504 and abs(e["x"] - 456) == 48 for f, e in events.items() if f <= 161)
    assert events[101]["keys"] == 2 and events[101]["y"] == 60.47265625
    assert all(e["door_tile28_4"] == 0 for f, e in events.items() if f < 110)
    assert all(e["door_tile28_4"] == 255 for f, e in events.items() if 110 <= f < 213)
    assert (events[213]["room"], events[213]["x"], events[213]["y"]) == (229, 456, 456.99609375)
    run, = (r for r in record["accepted"] if r["enemy_health_percent"] == health)
    segments = {s["id"]: s for s in run["segments"]}
    assert segments["normal229mirrapuff"]["inputs"][:3] == [[60, 64], [40, 0], [1, 2]]
    assert ("normal229laserclear" in segments) == (health == 100)
    assert ("spray500jumpover" in segments) == (health == 500)
    if health == 500:
        assert segments["spray500jumpover"]["inputs"] == [[5, 32], [5, 0], [5, 32], [55, 33], [80, 64]]
    assert "default suffix cannot be reused unchanged at500" in record["qualifications_additional"]
    assert "top-corridor downward join is neither required nor inferred" in record["qualifications_additional"]


def test_normal_artifact_resolution_does_not_rewrite_historical_qualifications() -> None:
    # Each exact hashed artifact keeps its contemporary limitations. Later proof resolves only its stated target.
    assert set(artifact("normal_warp")["unresolved"]) == {"Spray32", "food34", "boundary"}
    assert set(artifact("normal_food")["unresolved"]) == {"Spray32"}
    assert artifact("normal_spray")["unresolved"] == {}
    assert "does not prove upstream Normal205 access" in artifact("normal_spray")["qualifications_additional"]
