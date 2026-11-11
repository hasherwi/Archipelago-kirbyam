"""Pin the forward carrier and alternative C branches without inventing return state."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from .evidence_helpers import canonical_text_bytes


ROOT = Path(__file__).parents[1]
ARTIFACTS = {
    "forward": ("ordinary-708-forward-burning-706-acceptance.json", "961677da5e29f459cf18e9e043654c76f9f1ff17"),
    "branches": ("ordinary-708-c-743-alternative-acceptance.json", "caab63f385a0837fa70fe9d9c49ac65ca1b93fcb"),
    "scalar": ("native-708-complete-bomb-scalar-audit.json", "f752cfdec944273a4537163ecbc7990d42063aa7"),
    "joint": ("ordinary-743-joint-lever-acceptance.json", "da16f59c09fd1ce7ae882538a40ba6cf09dba787"),
}


def artifact(kind: str) -> dict[str, Any]:
    name, sha = ARTIFACTS[kind]
    raw = canonical_text_bytes(ROOT / "dev-docs" / name)
    assert hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == sha
    result: dict[str, Any] = json.loads(raw)
    return result


@pytest.mark.parametrize("health,total", [(100, 4732), (500, 5007)])
def test_fresh_forward_and_exact706_lower_endpoint_are_continuous(health: int, total: int) -> None:
    record = artifact("forward")
    audit = record["default_audit" if health == 100 else "max_health_audit"]
    previous = 0
    for index, segment in enumerate(audit["segments"]):
        assert segment["final"]["frame"] - previous == sum(step[0] for step in segment["inputs"])
        assert segment["minimum_hp"] == segment["final"]["hp"] == 6
        assert segment["abilities"] == ([0, 3] if index == 0 else [3])
        assert segment["hp_decrease_frames"] == segment["grab_frames"] == []
        previous = segment["final"]["frame"]
    final = audit["segments"][-1]["final"]
    assert (previous, final["room"], final["x"], final["y"], final["ability"]) == (
        total, 708, 697.99609375, 456.99609375, 3)
    previous = 0
    for segment in record["exit_706_branches"][str(health)]:
        assert segment["final"]["frame"] - previous == sum(step[0] for step in segment["inputs"])
        assert segment["minhp"] == segment["final"]["hp"] == 6
        assert segment["abilities"] == [3] and segment["grabs"] == []
        previous = segment["final"]["frame"]
    assert (previous, segment["final"]["room"], segment["final"]["x"], segment["final"]["y"]) == (
        855, 706, 40, 296.99609375)
    assert record["bank_readback"]["values_before_exit_both_variants"] == [0, 0]
    assert record["bank_readback"]["exit_record"] == "0x883C72"
    assert record["fixture"]["runtime_writes"] == []
    assert record["fixture"]["imported_equipment_template"] == "0x088BDDF0"
    assert "not credited as a production Burning source" in record["fixture"]["edit"]


@pytest.mark.parametrize("health", [100, 500])
@pytest.mark.parametrize("branch,frames,x", [("main", 557, 88), ("dead_end", 569, 184)])
def test_c_alternatives_end_on_their_own_sides(health: int, branch: str, frames: int, x: int) -> None:
    record = artifact("branches")
    assert record["status"] == "accepted_alternative_endpoints_not_joint_itinerary"
    assert record["parent_blob"] == ARTIFACTS["forward"][1]
    assert "stale" in record["correction"]
    assert record["bank_provenance"]["before_values"] == [245, 245]
    assert record["bank_provenance"]["after_values"] == [0, 0]
    assert "never substitute other durability or reset state" in record["bank_provenance"]["all_exit_branches_start"]
    previous = 0
    segments = record["branches"][branch][str(health)]
    for segment in segments:
        assert segment["final"]["frame"] - previous == sum(step[0] for step in segment["inputs"])
        assert segment["minhp"] == segment["final"]["hp"] == 6
        assert segment["abilities"] == [3] and segment["grabs"] == []
        previous = segment["final"]["frame"]
    # Both plans activate C, but one stops left and the other right of the solid divider.
    assert segments[0]["c_boundary"] == [13, 13, 255]
    assert (segments[0]["final"]["x"] < 416) is (branch == "main")
    final = segments[-1]["final"]
    assert (previous, final["room"], final["x"], final["y"]) == (frames, 743, x, 40.99609375)
    assert "not a C-free dead-end proof" in record["limitations"][0]
    assert "do not prove joint completion or a return/reset" in record["limitations"][1]


def test_scaler_is_production_and_scalar_c_closes_the_divider() -> None:
    scaler = artifact("branches")["scaler"]
    raw = canonical_text_bytes(ROOT / "enemy_health_scaling.py")
    assert hashlib.sha256(raw).hexdigest() == scaler["sha256"]
    assert hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == scaler["git_blob"]
    assert scaler["applications"] == 1 and scaler["function"] == "scale_enemy_health_tables(rom_bytes,500)"
    scalar = artifact("scalar")
    mutations = {(m["x"], m["y"]): m for m in scalar["all_mutations"]}
    assert len(mutations) == 51 and all(m["kind"] == 1 for m in mutations.values())
    assert len(scalar["components"]) == 4
    for cell in ((26, 27), (26, 28)):
        assert mutations[cell]["initial_collision"] == 243 and mutations[cell]["replacement"] == 13
    assert mutations[(22, 28)]["replacement"] == 255
    rows = scalar["lower_junction_collision_rows_x18_to31_y20_to30"]
    for row in rows:
        if 24 <= row["y"] <= 26:
            assert row["values"] == [13] * 14
            assert not any((x, row["y"]) in mutations for x in range(18, 32))
    assert scalar["button_gate"][0]["timer_candidate_unk18"] == 100


@pytest.mark.parametrize("health", [100, 500])
@pytest.mark.parametrize("branch", ["joint", "lever"])
def test_743_native_continuations_preserve_lineage_and_separate_postconditions(health: int, branch: str) -> None:
    record = artifact("joint")
    assert record["parent_artifact_blobs"] == [ARTIFACTS["forward"][1], ARTIFACTS["branches"][1]]
    assert all(value == artifact("branches")["scaler"][key] for key, value in record["scaler"].items())
    arrival = artifact("branches")["branches"]["main"][str(health)][-1]["final"]
    assert (arrival["room"], arrival["x"], arrival["y"], arrival["hp"], arrival["ability"]) == (
        743, 88, 40.99609375, 6, 3)
    run = record["results"][branch][str(health)]
    # Each exact durability lineage starts at that earned main arrival, not an
    # arbitrary Normal placement or a state copied from the other health setting.
    parent = artifact("forward")["default_audit" if health == 100 else "max_health_audit"]
    assert run["fixture_rom_sha256"] == parent["rom_sha256"]
    previous = 0
    dropped = False
    for segment in run["segments"]:
        final = segment["final"]
        assert final["frame"] - previous == sum(step[0] for step in segment["inputs"])
        assert segment["minhp"] == final["hp"] == 6
        assert segment["grabs"] == segment["hp_decrease_frames"] == []
        if final["ability"] == 0:
            dropped = True
        assert final["ability"] == (0 if dropped else 3)
        assert segment["abilities"] == ([0] if dropped else [3])
        assert final["room"] == 743 or segment is run["segments"][-1]
        previous = final["frame"]
    assert previous == run["audited_frames"]
    if branch == "joint":
        assert not dropped and final["ability"] == 3
        assert (final["room"], final["x"], final["y"], segment["flag18_mask4"]) == (
            708, 472, 456.99609375, 0)
    else:
        assert dropped and final["ability"] == 0
        assert (final["room"], final["x"], final["y"], segment["flag18_mask4"]) == (
            180, 72, 40.99609375, 4)
