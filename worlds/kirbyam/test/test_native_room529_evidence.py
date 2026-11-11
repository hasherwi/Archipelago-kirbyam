"""Fresh Normal529 passages leave both ordinary-metal banks intact."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from .evidence_helpers import canonical_text_bytes


ROOT = Path(__file__).parents[1]
ARTIFACTS = {
    "lower-upper-right": "ffeb53b93c51f61789d05d4ef85fe44008c61c77",
    "upper-right-lower": "a2b390e35d0ae0f34b3dd0e4783b4b703d34e0e1",
}
F5 = {(x, y) for x in (8, 9) for y in (5, 6)} | {(x, y) for x in (12, 13) for y in (18, 19)}


def checked_record(filename: str, blob: str) -> dict[str, Any]:
    raw = canonical_text_bytes(ROOT / "dev-docs" / filename)
    assert hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == blob
    record: dict[str, Any] = json.loads(raw)
    return record


def check_fresh_left_run(run: dict[str, Any], multiplier: str, frames: int, samples: int) -> None:
    assert run["success"] and run["enemy_health_percent"] == int(multiplier)
    assert run["original_usa_sha1"] == "274b102b6d940f46861a92b4e65f89a51815c12c"
    assert run["native_source_commit"] == "7d969fbce14fdc838d2c1ea01389717fb96c3189"
    assert "Blank battery save" in run["fixture"] and "No runtime writes" in run["fixture"]
    assert "object/terrain/attack patches" in run["fixture"]
    scaler = canonical_text_bytes(ROOT / "enemy_health_scaling.py")
    assert hashlib.sha1(b"blob " + str(len(scaler)).encode() + b"\0" + scaler).hexdigest() == run["scaler_git_blob"]
    audit = run["audit"]
    assert audit["frames"] == frames == audit["to_frame"] - audit["from_frame"] + 1
    assert audit["minimum_hp"] == 6 and audit["hp_drop_frames"] == []
    assert audit["abilities"] == [0] and audit["runtime_write_count"] == 0
    assert audit["529_frames_sampled"] == audit["529_all8_f5_frames"] == samples
    assert audit["529_non_f5_samples"] == []
    assert {tuple(point) for point in audit["f5_coordinates"]} == F5
    assert audit["fresh_entry"]["f5"] == audit["last529_collision"]["f5"] == [245] * 8
    assert len(run["bomb_replacements"]) == 90
    assert audit["fresh_entry"]["bombs"] == [cell["attribute"] for cell in run["bomb_replacements"]]
    frame = 0
    assert len(run["inputs"]) == len(run["segments"])
    for inputs, segment in zip(run["inputs"], run["segments"]):
        assert inputs["label"] == segment["label"]
        assert inputs["frames"] == sum(step["frames"] for step in inputs["inputs"])
        assert segment["start"] == frame
        frame += inputs["frames"]
        assert segment["end"] == segment["final"]["frame"] == frame
        assert segment["minimum_hp"] == segment["final"]["hp"] == 6
        assert segment["hp_drop_frames"] == [] and segment["abilities"] == [0]
        assert segment["final"]["ability"] == 0
    assert frame == audit["to_frame"]


@pytest.mark.parametrize("multiplier", ["100", "500"])
def test_lower_to_upper_left_opens_exactly_four_components_from_below(multiplier: str) -> None:
    record = checked_record("native529-lower-to-upperleft-acceptance.json",
                            "173f7910fb3a2c81878c8362c503368e09d98b7f")
    run = record["runs"][multiplier]
    check_fresh_left_run(run, multiplier, 1263, 1200)
    entry, final = run["audit"]["fresh_entry"], run["audit"]["final"]
    assert (entry["room"], entry["x"], entry["y"]) == (529, 72, 456.99609375)
    assert (final["room"], final["x"], final["y"]) == (512, 152, 296.99609375)
    components = run["left_bomb_components"]
    assert [c["cell_count"] for c in components] == [10, 12, 19, 12]
    assert [(c["first_water_frame"], c["all_water_frame"]) for c in components] == [
        (1207, 1237), (1333, 1369), (1581, 1629), (1999, 2041)]
    changed: set[int] = set()
    for component in components:
        assert not changed.intersection(component["indices"])
        changed.update(component["indices"])
        assert len(component["indices"]) == len(component["mutation_frames"]) == component["cell_count"]
        times = [cell["first_water_frame"] for cell in component["mutation_frames"]]
        assert min(times) == component["first_water_frame"] and max(times) == component["all_water_frame"]
    assert len(changed) == 53
    final_cells = run["audit"]["last529_collision"]["bombs"]
    for index, cell in enumerate(run["bomb_replacements"]):
        assert final_cells[index] == (72 if index in changed else cell["attribute"])


@pytest.mark.parametrize("multiplier", ["100", "500"])
@pytest.mark.parametrize("section,frames,samples", [("return_runs", 178, 107), ("bounded_negative_runs", 311, 300)])
def test_fresh_upper_left_returns_without_opening_or_borrowing_lower_layout(
    multiplier: str, section: str, frames: int, samples: int,
) -> None:
    record = checked_record("native529-fresh-upperleft-return-and-boundary.json",
                            "93c7ac88f27a61feb55d751676a25faa38821f75")
    run = record[section][multiplier]
    check_fresh_left_run(run, multiplier, frames, samples)
    entry, final = run["audit"]["fresh_entry"], run["audit"]["final"]
    assert (entry["room"], entry["x"], entry["y"]) == (529, 104, 40.99609375)
    assert entry["bombs"] == run["audit"]["last529_collision"]["bombs"]
    for component in run["left_bomb_components"]:
        assert component["first_water_frame"] is None and component["all_water_frame"] is None
        assert all(cell["first_water_frame"] is None for cell in component["mutation_frames"])
    if section == "return_runs":
        assert (final["room"], final["x"], final["y"]) == (512, 152, 296.99609375)
    else:
        assert final["room"] == 529 and final["y"] == 120.99609375
    geometry = record["sealed_pocket_geometry"]
    assert geometry["exposed_lower_trigger"]["pixel_rectangle"] == [48, 176, 64, 192]
    puff = geometry["downward_water_puff"]
    assert puff["maximum_bottom_y_at_floor"] == 160.49609375 < 176
    assert puff["gap_to_trigger_top_pixels"] == 15.50390625
    assert "do not infer symmetry" in geometry["interpretation"]


@pytest.mark.parametrize("direction", ARTIFACTS)
@pytest.mark.parametrize("multiplier", ["100", "500"])
def test_fresh_directed_replay_is_normal_no_loss_and_keeps_all_f5(direction: str, multiplier: str) -> None:
    path = ROOT / f"dev-docs/ordinary-529-{direction}-acceptance.json"
    raw = canonical_text_bytes(path)
    assert hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == ARTIFACTS[direction]
    record = json.loads(raw)
    assert record["accepted_enemy_health_percent"] == [100, 500]
    run = record["runs"][multiplier]
    assert run["success"]
    assert run["enemy_health_percent"] == int(multiplier)
    assert run["original_usa_sha1"] == "274b102b6d940f46861a92b4e65f89a51815c12c"
    assert run["native_source_commit"] == "7d969fbce14fdc838d2c1ea01389717fb96c3189"
    assert "Blank battery save" in run["fixture"] and "No runtime writes" in run["fixture"]
    assert "object/terrain/attack patches" in run["fixture"]
    scaler = canonical_text_bytes(ROOT / "enemy_health_scaling.py")
    assert hashlib.sha1(b"blob " + str(len(scaler)).encode() + b"\0" + scaler).hexdigest() == run["scaler_git_blob"]

    audit = run["audit"]
    assert audit["minimum_hp"] == 6 and audit["hp_drop_frames"] == []
    assert audit["abilities"] == [0] and audit["runtime_write_count"] == 0
    assert audit["frames"] == audit["to_frame"] - audit["from_frame"] + 1
    assert len(audit["per_frame_sha256"]) == 64
    assert {tuple(point) for point in audit["f5_coordinates"]} == F5
    assert audit["529_frames_sampled"] == audit["529_all8_f5_frames"] > 0
    assert audit["529_non_f5_samples"] == []
    assert audit["last529_collision"]["f5"] == [245] * 8
    assert audit["visible_bottom_crossing"]["minimum_hp"] == 6
    assert audit["visible_bottom_crossing"]["y_range"][1] < 480

    frame = 0
    assert len(run["inputs"]) == len(run["segments"])
    for inputs, segment in zip(run["inputs"], run["segments"]):
        assert inputs["label"] == segment["label"]
        assert inputs["frames"] == sum(step["frames"] for step in inputs["inputs"])
        assert segment["start"] == frame
        frame += inputs["frames"]
        assert segment["end"] == segment["final"]["frame"] == frame
        assert segment["minimum_hp"] == segment["final"]["hp"] == 6
        assert segment["hp_drop_frames"] == [] and segment["abilities"] == [0]
        assert segment["final"]["ability"] == 0
    assert frame == audit["to_frame"] == audit["final"]["frame"]

    arrival = run["segments"][0]["final"]
    final = audit["final"]
    if direction == "lower-upper-right":
        assert (arrival["room"], arrival["x"], arrival["y"]) == (529, 72, 456.99609375)
        assert (final["room"], final["x"], final["y"]) == (512, 360, 296.99609375)
        assert "0x89E3F8" in run["route"] and "0x89EB0E" in run["route"]
    else:
        assert (arrival["room"], arrival["x"], arrival["y"]) == (529, 376, 40.99609375)
        assert (final["room"], final["x"], final["y"]) == (523, 296, 40.99609375)
        assert "0x89D364" in run["route"] and "0x89F236" in run["route"]
        assert audit["fresh_entry_bombs"] == [tile["attribute"] for tile in run["bomb_replacements"]]
        assert set(audit["fresh_entry_bombs"]) == {241, 242}
    assert audit["last529_collision"]["bombs"] == [tile["replacement"] for tile in run["bomb_replacements"]]
    assert len(run["bomb_replacements"]) == 25


def test_ordinary_topology_does_not_install_a_metal_provider_or_source() -> None:
    rooms = json.loads((ROOT / "data/regions/rooms.json").read_text(encoding="utf-8"))
    row = rooms["REGION_CABBAGE_CAVERN/ROOM_3_03"]
    assert "traversal" not in row
    assert "traversal" not in row["logical_subregions"]["UPPER_LEFT"]
