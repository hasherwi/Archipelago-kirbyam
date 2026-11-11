"""The renewable228 fixture proves a joint noncombat carrier, not a new source."""

import hashlib
import json
from itertools import groupby
from pathlib import Path

import pytest

from .evidence_helpers import canonical_text_bytes


ROOT = Path(__file__).parents[1]
PATH = ROOT / "dev-docs/ordinary-228-renewable-hammer-joint-acceptance.json"


@pytest.mark.parametrize("multiplier,frames,count", [("100", 12616, 36), ("500", 13017, 38)])
def test_fresh_joint_itinerary_never_loses_hammer_health_or_previous_check(
    multiplier: str, frames: int, count: int,
) -> None:
    raw = canonical_text_bytes(PATH)
    assert hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == (
        "a4cca011f7f5d2e3ada5600c116a1f6b5663e74c")
    record = json.loads(raw)
    assert record["original_rom_sha1"] == "274b102b6d940f46861a92b4e65f89a51815c12c"
    assert record["source_revision"] == "7d969fbce14fdc838d2c1ea01389717fb96c3189"
    run = record["runs"][multiplier]
    assert run["fresh_boot"] and run["audited_post_boot_frames"] == frames
    assert len(run["segments"]) == count
    assert [room for room, _ in groupby(s["final"]["room"] for s in run["segments"])] == [
        290, 210, 227, 204, 203, 205, 209, 205, 228]
    elapsed = 0
    previous_collected = False
    for index, segment in enumerate(run["segments"]):
        elapsed += sum(step[0] for step in segment["inputs"])
        assert segment["final"]["frame"] == elapsed
        if index:
            assert segment["minimum_hp"] == segment["final"]["hp"] == 6
            assert segment["hp_decrease_frames"] == [] and segment["grab_frames"] == []
            assert segment["abilities"] == ([0, 17] if index == 1 else [17])
            assert segment["final"]["ability"] == 17
        if previous_collected:
            assert segment["flags23_30_31"][0] == 128
        previous_collected |= segment["flags23_30_31"][0] == 128
    assert elapsed - run["segments"][0]["final"]["frame"] == frames
    assert run["final_flags"] == {
        "minor23_mask128": 128, "minor30_mask64": 64, "separate_rope_minor31_mask128": 0}
    final = run["segments"][-1]
    assert final["flags23_30_31"] == [128, 64, 0]
    assert final["inputs"] == [[22, 16], [30, 64], [90, 0]]
    assert (final["final"]["room"], final["final"]["x"], final["final"]["y"]) == (
        228, 472.35546875, 200.99609375)
    assert {(cell["x"], cell["y"]): cell["value"] for cell in final["tiles"]} == {
        (27, 23): 0, (27, 24): 0, (17, 23): 241, (17, 19): 243,
        (32, 15): 241, (32, 11): 243, (32, 12): 243}


def test_fixture_never_replaces_actual970_source_or_credits_boss_combat() -> None:
    record = json.loads(PATH.read_text(encoding="utf-8"))
    fixture = record["fixture"]
    assert fixture["startup_room"] == 290 and fixture["runtime_writes"] == []
    assert len(fixture["edits"]) == 3
    statue = fixture["edits"][-1]
    assert (statue["template"], statue["type"], statue["original_subtype"],
            statue["replacement_subtype"], statue["granted_ability"]) == ("0x088C0ED0", 147, 1, 6, 17)
    assert "All bosses and scroll locks" in fixture["unchanged"]
    assert "0x088D5FA0" in record["source_prefix_boundary"]["production_source"]
    assert "STATUE:35390A" in record["source_prefix_boundary"]["production_source"]
    assert "must not be credited" in record["source_prefix_boundary"]["fixture_not_production_source"]
    assert any("avoids its arena" in limit for limit in record["limitations"])
    assert "No checkpoint splicing" in record["audit_semantics"]
    assert [(door["source"], door["target"], door["record"]) for door in record["actual_transition_records"]] == [
        (210, 227, "0x08888D0E"), (227, 204, "0x0888A310"), (204, 203, "0x088870D4"),
        (203, 205, "0x08886F88"), (205, 228, "0x08887306")]
    source = canonical_text_bytes(ROOT / "enemy_health_scaling.py")
    scaler = record["max_health"]
    assert hashlib.sha1(b"blob " + str(len(source)).encode() + b"\0" + source).hexdigest() == scaler["module_git_blob"]
    assert hashlib.sha256(source).hexdigest() == scaler["module_sha256"]
    assert scaler["percent"] == 500 and scaler["sanity_readback"]["scaled_hp"] == 20
