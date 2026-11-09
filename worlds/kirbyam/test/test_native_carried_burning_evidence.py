"""Exact imported-source boundaries and independently replayed Burning continuations."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from .evidence_helpers import canonical_text_bytes


ROOT = Path(__file__).parents[1]
FILES = {
    "141": ("native-141-imported-burning-forward-acceptance.json", "e76bca0dca61c56f0594e1d88fe591b17d561644"),
    "742": ("ordinary-742-carried-burning-acceptance.json", "ffeaa093981dbc80e247e30311e87106ef9e124f"),
    "joint": ("ordinary-742-carried-burning-combined-checks.json", "8afdec9e787643ec79e3bdd8ce9daba7df592ae1"),
    "provenance": ("ordinary-742-parent707-provenance.json", "8853b1d78e5490c898b2a72d5ad25ac3e4cc7d37"),
}


def artifact(key: str) -> dict[str, Any]:
    name, sha = FILES[key]
    raw = canonical_text_bytes(ROOT / "dev-docs" / name)
    assert hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == sha
    result: dict[str, Any] = json.loads(raw)
    return result


@pytest.mark.parametrize("health", [100, 500])
def test_141_actual_source_contact_and_two_fresh_forward_banks(health: int) -> None:
    record = artifact("141")
    source = record["fixture"]["source_substitution"]
    assert (source["template_bus"], source["type"], source["original_subtype1"], source["fixture_subtype1"],
            source["original_native_ability"], source["fixture_ability"]) == ("0x088B7CEC", 146, 4, 1, 8, 3)
    assert record["fixture"]["no_runtime_writes"] and record["fixture"]["no_midrun_savestate_loads"]
    assert [(d["source"], d["destination"], d["spawn_tile"]) for d in record["doors"]] == [
        (190, 143, [3, 19]), (143, 141, [43, 19])]
    raw = canonical_text_bytes(ROOT / "enemy_health_scaling.py")
    assert hashlib.sha256(raw).hexdigest() == record["scaler"]["sha256"]
    run = record["runs"][str(health)]
    assert run["ram_writes"] == [] and record["audit_contract"]["start_frame"] == 1086
    previous = 0
    for segment in run["segments"]:
        final = segment["end"]
        assert final["frame"] - previous == sum(step[0] for step in segment["inputs"])
        assert segment["minimum_hp"] == final["hp"] == 6
        if previous >= 1202:
            assert segment["abilities"] == [3] and final["ability"] == 3
        if previous >= 1085:
            assert segment["grabs"] == [0]
        previous = final["frame"]
    assert previous == 3743
    segments = {s["label"]: s for s in run["segments"]}
    assert segments["touch"]["abilities"] == [0, 3]
    for label, room, x, y in (
        ("arrived143", 143, 40, 296.99609375), ("arrive141", 141, 680, 296.99609375),
        ("bankleft", 141, 176.703125, 131.55078125), ("east", 141, 529.9453125, 168.0234375),
    ):
        final = segments[label]["end"]
        assert (final["room"], final["x"], final["y"]) == (room, x, y)
    mutations = {s["segment"]: s["changed_cells"] for s in run["mutations"]}
    assert mutations["arrive141"] == []
    for label, expected in (("bankleft", {(x, y) for x in (5, 6) for y in (7, 8)}),
                            ("east", {(x, y) for x in (5, 6) for y in (7, 8)}
                             | {(x, y) for x in (27, 28) for y in (9, 10)})):
        assert {tuple(c["cell"]) for c in mutations[label] if c["native"] == 245} == expected
    assert all(c["native"] in (240, 245) and c["live"] == 0 for cells in mutations.values() for c in cells)


@pytest.mark.parametrize("health,prefix", [(100, "default"), (500, "exact500")])
@pytest.mark.parametrize("branch", ["chest", "warp"])
def test_742_matches_actual_707_endpoint_and_keeps_copy_through_each_target(
    health: int, prefix: str, branch: str,
) -> None:
    record = artifact("742")
    parent = record["parent_acceptances"][str(health)]
    provenance = artifact("provenance")
    assert provenance["relates_to_blob"] == FILES["742"][1]
    bridge = next(entry for entry in provenance["entries"] if entry["health_percent"] == health)
    assert bridge["filename"] == parent["filename"]
    # The immutable 742 record hashes its original Pi serialization. The additive
    # bridge pins the byte-distinct, parsed-JSON-equal published 707 artifact too.
    assert bridge["local_sha256"] == parent["sha256"]
    raw = canonical_text_bytes(ROOT / "dev-docs" / parent["filename"])
    assert hashlib.sha256(raw).hexdigest() == bridge["published_sha256"]
    assert len(raw) == bridge["published_size_bytes"]
    assert hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == (
        bridge["published_git_blob_sha1"])
    assert bridge["entire_parsed_json_equal"] and bridge["normalization_reproduces_exact_published_bytes"]
    assert bridge["published707_final_checkpoint_matches_live_state"]
    assert bridge["parent742_initial_state_hash_and_scalar_endpoint_match"]
    assert bridge["state_read_frames_advanced"] == 0 and bridge["state_read_writes"] == []
    assert parent["ending_segment"] == bridge["accepted_endpoint_segment"] == (
        "carrier712actual" if health == 100 else "all500-712final")
    run = record["audits"][prefix + "_" + branch]
    assert run["pct"] == health
    assert run["rom_sha256"] == bridge["actual_rom_sha256"]
    assert run["initial_state_sha256"] == bridge["private_endpoint_state_sha256"]
    start = run["start"]
    parent_final = json.loads(raw)["segments"][-1]["checkpoints"][-1]
    for key, value in bridge["read_only_live_endpoint"].items():
        assert value == start[key] == parent_final[key]
    assert (start["frame"], start["room"], start["x"], start["y"], start["hp"], start["ability"]) == (
        0, 712, 24, 456.99609375, 6, 3)
    other = record["audits"][prefix + ("_warp" if branch == "chest" else "_chest")]
    assert run["initial_state_sha256"] == other["initial_state_sha256"]
    assert run["rom_sha256"] == other["rom_sha256"]
    previous = 0
    for segment in run["segments"]:
        final = segment["final"]
        assert final["frame"] - previous == sum(step[0] for step in segment["inputs"])
        assert segment["minimum_hp"] == final["hp"] == 6
        assert segment["hp_decrease_frames"] == segment["grab_frames"] == []
        assert segment["abilities"] == ([3] if segment["inputs"] else [])
        assert final["ability"] == 3
        previous = final["frame"]
    final = run["segments"][-1]
    if branch == "chest":
        assert final["final"]["room"] == 742 and final["chest17"] == 2
    else:
        assert (final["final"]["room"], final["final"]["x"], final["final"]["y"], final["chest17"]) == (
            705, 56, 616.99609375, 0)
    observed = record["observations"][f"metal_{health}"]
    assert observed["writes"] == []
    assert {(t["x"], t["y"]): t["value"] for t in observed["tiles"]} == {
        (20, 6): 0, (21, 6): 0, (20, 7): 245, (21, 7): 245}


@pytest.mark.parametrize("prefix", ["default", "exact500"])
def test_742_same_visit_joint_result_is_explicitly_normal_not_reexported_burning(prefix: str) -> None:
    joint, parent = artifact("joint"), artifact("742")
    assert joint["parent_blob_sha"] == FILES["742"][1]
    parent_raw = canonical_text_bytes(ROOT / "dev-docs" / FILES["742"][0])
    assert hashlib.sha256(parent_raw).hexdigest() == joint["parent_sha256"]
    run = joint["audits"][prefix]
    chest = parent["audits"][prefix + "_chest"]
    assert run["rom_sha256"] == chest["rom_sha256"] and run["pct"] == chest["pct"]
    for key in ("room", "x", "y", "hp", "ability"):
        assert run["start"][key] == chest["segments"][-1]["final"][key]
    assert run["writes"] == [] and run["start_chest17"] == 2
    assert run["segments"][0]["inputs"][0] == {"frames": 1, "keys": 4}
    previous = 0
    for segment in run["segments"]:
        final = segment["final"]
        assert final["frame"] - previous == sum(step["frames"] for step in segment["inputs"])
        assert segment["minimum_hp"] == final["hp"] == 6
        assert segment["hp_decrease_frames"] == segment["grab_frames"] == []
        assert segment["abilities"] == [0] and final["ability"] == 0 and segment["chest17"] == 2
        if final["room"] == 742:
            assert {(t["x"], t["y"]): t["value"] for t in segment["tracked_tiles"]} == {
                (19, 12): 241, (26, 12): 241, (24, 8): 243, (25, 8): 243}
        previous = final["frame"]
    assert (previous, final["room"], final["x"], final["y"]) == (1079, 705, 56, 616.99609375)
