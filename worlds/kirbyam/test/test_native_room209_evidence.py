"""Directed native209 traces do not certify its coarse AP room alias."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from .evidence_helpers import canonical_text_bytes


ROOT = Path(__file__).parents[1]


def record(name: str) -> dict[str, Any]:
    result: dict[str, Any] = json.loads((ROOT / "dev-docs" / name).read_text(encoding="utf-8"))
    assert result["original_usa_sha1"] == "274b102b6d940f46861a92b4e65f89a51815c12c"
    assert result["native_source_commit"] == "7d969fbce14fdc838d2c1ea01389717fb96c3189"
    return result


def audited_normal_chain(run: dict[str, Any], count: int, frames: int) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = run["segments"]
    assert len(segments) == count + 1
    assert len({segment["id"] for segment in segments}) == len(segments)
    frame = 0
    for index, segment in enumerate(segments):
        frame += sum(step["frames"] for step in segment["inputs"])
        assert segment["final"]["frame"] == frame
        assert segment["final"]["hp"] == 6 and segment["final"]["ability"] == 0
        if index:
            assert segment["minimum_hp"] == 6 and segment["decrease_frames"] == []
            assert segment["abilities"] == [0]
    assert frame - segments[0]["final"]["frame"] == frames
    return segments


@pytest.mark.parametrize("multiplier", ["100", "500"])
def test_upper_arrival_snow_map_loop_is_normal_directed_and_collects_both(multiplier: str) -> None:
    data = record("ordinary-209-snow-map-loop-acceptance.json")
    segments = audited_normal_chain(data["runs"][multiplier], 9, 2714)
    assert (segments[0]["final"]["room"], segments[0]["final"]["x"], segments[0]["final"]["y"]) == (
        209, 24, 136.99609375)
    assert (segments[2]["final"]["room"], segments[2]["final"]["x"], segments[2]["final"]["y"]) == (
        210, 472, 376.99609375)
    assert (segments[5]["final"]["room"], segments[5]["final"]["x"], segments[5]["final"]["y"]) == (
        209, 24, 312.99609375)
    assert segments[3]["flag25_masked"] == 0 and segments[4]["flag25_masked"] == 2
    assert segments[-2]["flag22_masked"] == 0 and segments[-1]["flag22_masked"] == 64
    assert segments[-1]["flag25_masked"] == 2
    assert data["targets"] == [
        {"room": 210, "template": "0x088BF610", "position": [248, 456], "flag": 25, "mask": 2},
        {"room": 209, "template": "0x088BF338", "position": [288, 496], "flag": 22, "mask": 64},
    ]


@pytest.mark.parametrize("multiplier", ["100", "500"])
def test_map_uses_first_bomb_delayed_propagation_not_second_trigger_or_room_reset(multiplier: str) -> None:
    data = record("ordinary-209-snow-map-loop-acceptance.json")
    observed = {segment["id"]: {(row["x"], row["y"]): row["tile"] for row in segment["tiles"]}
                for segment in data["runs"][multiplier]["segments"] if "tiles" in segment}
    assert observed["snow210lower209"] == {
        (4, 17): 241, (12, 17): 243, (15, 23): 241, (17, 27): 242, (18, 28): 242}
    assert observed["lower209bomb"] == {
        (4, 17): 0, (12, 17): 0, (15, 23): 241, (17, 27): 242, (18, 28): 242}
    for key in ("lower209bandfly", "lower209secondapproach"):
        assert observed[key] == {(4, 17): 0, (12, 17): 0, (15, 23): 241, (17, 27): 0, (18, 28): 0}
    assert "historical" in data["bomb_note"]
    assert "not independent proof" in data["qualification"]
    assert "Objects, terrain, abilities and attacks unchanged" in data["qualification"]
    assert "No generic209/210 joins or cross-room Bomb persistence asserted" in data["route"]


@pytest.mark.parametrize("multiplier", ["100", "500"])
def test_minor24_has_actual_hub_and_bottom_transitions_with_collection_readback(multiplier: str) -> None:
    data = record("ordinary-208-bottom209-minor24-acceptance.json")
    segments = audited_normal_chain(data["runs"][multiplier], 6, 1253)
    assert [(row["final"]["room"], row["final"]["x"], row["final"]["y"]) for row in segments[:3]] == [
        (290, 232, 136.99609375), (208, 232, 40.99609375), (209, 40, 616.99609375)]
    assert segments[-2]["flag24_masked"] == 0 and segments[-1]["flag24_masked"] == 1
    assert "does not prove hub unlock/access" in data["qualification"]
    assert "No object, terrain or attack changes" in data["qualification"]


@pytest.mark.parametrize("name", [
    "ordinary-209-snow-map-loop-acceptance.json", "ordinary-208-bottom209-minor24-acceptance.json",
])
def test_fresh_max_health_scaler_matches_production_and_is_not_ap1hp(name: str) -> None:
    data = record(name)
    source = canonical_text_bytes(ROOT / "enemy_health_scaling.py")
    blob = hashlib.sha1(b"blob " + str(len(source)).encode() + b"\0" + source).hexdigest()
    assert blob == data["scaler"]["git_blob"]
    assert hashlib.sha256(source).hexdigest() == data["scaler"]["sha256"]
    assert "runtime writes" in data["qualification"]
    assert "1HP" in data["qualification"]
    assert data["runs"]["100"]["rom_sha256"] != data["runs"]["500"]["rom_sha256"]


def test_map_loop_health_table_readbacks_cover_native_enemies() -> None:
    data = record("ordinary-209-snow-map-loop-acceptance.json")
    assert data["health_sanity"] == {
        "0x34": {"offset": "0x351b2c", "default": 2, "max500": 10},
        "0x1a": {"offset": "0x3518bc", "default": 4, "max500": 20},
        "0xb": {"offset": "0x351754", "default": 2, "max500": 10},
    }


@pytest.mark.parametrize("multiplier", ["100", "500"])
def test_actual_bonkers_side_entry_reveals_door_by_bomb_not_unused_copy(multiplier: str) -> None:
    data = record("ordinary-210-bonkers-side209-entrance.json")
    segments = data["runs"][multiplier]["segments"]
    assert len(segments) == 4
    frame = 0
    for index, segment in enumerate(segments):
        frame += sum(step[0] for step in segment["inputs"])
        assert segment["final"]["frame"] == frame
        assert segment["final"]["hp"] == 6 and segment["final"]["ability"] == 0
        if index:
            assert segment["minimum_hp"] == 6 and segment["hp_decrease_frames"] == []
            assert segment["abilities"] == [0]
    assert frame - segments[0]["final"]["frame"] == 642
    assert segments[0]["bomb_chain_door_tiles"] == [241, 242, 242]
    assert segments[1]["bomb_chain_door_tiles"] == [0, 0, 255]
    assert segments[-2]["final"]["room"] == 210  # Historical segment name alone is not proof of arrival.
    final = segments[-1]["final"]
    assert (final["room"], final["x"], final["y"]) == (209, 24, 136.99609375)
    mechanism = data["mechanism"]
    assert mechanism["bomb_cell"] == [29, 12] and mechanism["chain_cell"] == [29, 13]
    assert mechanism["door_cell"] == [29, 14]
    assert mechanism["door_record_bus"] == "0x08888D00"
    assert mechanism["door_template_bus"] == "0x088BF6C4"
    assert "not directly from slot2" in data["qualification"]
    assert "Normal never acquires the fixture ability" in data["qualification"]
    assert "not a Bonkers defeat replay" in data["qualification"]


@pytest.mark.parametrize("mode,prefix", [("default", ""), ("all500", "all500-")])
def test_water_return_continuation_grants_only_actual203_exit(mode: str, prefix: str) -> None:
    data = json.loads((ROOT / "dev-docs/ordinary-205-water-return-outer-join.json").read_text(encoding="utf-8"))
    parent = json.loads((ROOT / "dev-docs/ordinary-205-normal-return-egress.json").read_text(encoding="utf-8"))
    assert data["extends_artifact_blob"] == "045568d8328eb6982a7adca4a5a58b2f9871f0a0"
    run = data["runs"][mode]
    assert run["parent_checkpoint"] == prefix + "normal205outerleft"
    assert (run["initial"]["room"], run["initial"]["x"], run["initial"]["y"]) == (
        205, 347.23046875, 21.00390625)
    assert run["rom_sha256"] in json.dumps(parent)
    frame = 0
    for segment in run["segments"]:
        frame += sum(step[0] for step in segment["inputs"])
        assert segment["final"]["frame"] == frame
        assert segment["minimum_hp"] == 6 and segment["hp_decrease_frames"] == []
        assert segment["abilities"] == [0] and segment["final"]["ability"] == 0
    assert frame == 919
    final = run["segments"][-1]["final"]
    assert (final["room"], final["x"], final["y"], final["hp"]) == (203, 936, 72.99609375, 6)
    assert data["door"]["record_bus"] == "0x088872F8"
    assert data["door"]["trigger"] == [1, 2]
    assert "does not prove every other outer exit" in data["qualification"]
