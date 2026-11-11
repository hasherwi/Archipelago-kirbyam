"""Original records recovered by hash; this does not execute native gameplay."""
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).parents[1] / "dev-docs"
MANIFEST = json.loads((ROOT / "recovered-environmental-evidence-manifest.json").read_text())


def read(name: str) -> dict[str, Any]:
    value: dict[str, Any] = json.loads((ROOT / name).read_text())
    return value


@pytest.mark.parametrize("record", MANIFEST["files"], ids=lambda row: row["path"])
def test_original_hash_and_private_path_exclusion(record: dict[str, Any]) -> None:
    raw = (ROOT / record["path"]).read_bytes()
    assert len(raw) == record["bytes"]
    assert hashlib.sha256(raw).hexdigest() == record["sha256"]
    assert b"/home/" not in raw and b"/workspace/" not in raw
    assert isinstance(json.loads(raw), dict)


@pytest.mark.parametrize("name", [
    "ordinary-502-normal-left-overhead-acceptance.json",
    "ordinary-510-stone-peg-chest-acceptance.json",
    "ordinary-532-normal-cannon-exit-acceptance.json",
    "ordinary-736-normal-nw-exit-acceptance.json",
    "ordinary-736-mini-chest-acceptance.json",
])
def test_both_health_variants_have_continuous_safe_segments(name: str) -> None:
    audit = read(name)["audits"]
    assert set(audit) == {"100", "500"}
    for run in audit.values():
        assert run["segments"] and run["ai_global_ability_frames"] == []
        for segment in run["segments"]:
            assert segment["minhp"] >= 6
            assert segment["hp_decreases"] == [] and segment["grabs"] == []


def test_cannon_532_is_not_a_copy_ability_gate() -> None:
    record = read("ordinary-532-normal-cannon-exit-acceptance.json")
    assert record["exit"]["destination"] == 138
    for run in record["audits"].values():
        assert run["segments"][0]["f5"] == [245] * 16
        assert run["segments"][-1]["final"]["room"] == 138
        assert all(segment["abilities"] == [0] for segment in run["segments"])
        assert any(segment["f5"] == [0] * 16 for segment in run["segments"])


def test_peg_510_chest_and_mini_736_keep_their_source_boundaries() -> None:
    peg = read("ordinary-510-stone-peg-chest-acceptance.json")
    for run in peg["audits"].values():
        assert run["segments"][-1]["flag53"] == 32
        assert run["segments"][-1]["final"]["ability"] == 8
        assert all(segment["f5"] == [245] * 10 for segment in run["segments"])
    mini = read("ordinary-736-mini-chest-acceptance.json")
    assert mini["source"]["template"] == "0x088D41A0"
    assert mini["route"]["destination"] == 739
    assert mini["chest"]["native_flag"] == 83
    for run in mini["audits"].values():
        assert any(segment["final"]["ability"] == 23 for segment in run["segments"])
        final = run["segments"][-1]
        assert final["final"]["room"] == 739
        assert final["final"]["ability"] == 0 and final["final"]["hp"] == 7
        assert final["flag83"][-1]["mask"] == 8


@pytest.mark.parametrize("health", ["100", "500"])
def test_return_502_uses_its_actual_entry_without_metal_destruction(health: str) -> None:
    run = read("ordinary-502-normal-return-overhead-acceptance.json")["runs"][health]
    assert run["ai_global_ability_frames"] == []
    assert run["segments"][0]["final"]["room"] == 502
    assert run["segments"][-1]["final"]["room"] == 525
    for segment in run["segments"]:
        assert segment["abilities"] == [0]
        assert segment["minhp"] == 6
        assert segment["hp_decreases"] == segment["grabs"] == []
        if segment["final"]["room"] == 502:
            assert segment["f5"] == [245] * 3


@pytest.mark.parametrize("health", ["100", "500"])
@pytest.mark.parametrize("direction,rooms", [
    ("forward", [509, 510, 501]), ("reverse", [501, 510, 509]),
])
def test_510_exits_do_not_borrow_the_stone_chest_witness(health: str, direction: str, rooms: list[int]) -> None:
    record = read("ordinary-510-normal-exits-acceptance-sanitized.json")
    run = record["routes"][direction]["audits"][health]
    assert [row["room"] for row in run["room_transitions"]] == rooms
    assert run["abilities"] == [0] and run["min_hp"] == 6
    assert run["grabs"] == 0 and not run["AI_co_residency"]
    assert run["metal_intact"] == 10 and run["peg_intact"]
    assert run["chest_flag53"] == 0


@pytest.mark.parametrize("health", ["100", "500"])
@pytest.mark.parametrize("direction,destination,breaks_metal", [
    ("138_to_571", 571, False), ("571_to_138", 138, True),
])
def test_532_fresh_directions_do_not_share_a_cleared_bank(
    health: str, direction: str, destination: int, breaks_metal: bool
) -> None:
    record = read("ordinary-532-fresh-direction-737-return-audit.json")
    run = record["routes"][direction]["audits"][health]
    assert run["ai_global_ability_frames"] == []
    assert run["segments"][0]["f5"] == [245] * 16
    assert run["segments"][-1]["final"]["room"] == destination
    assert any(segment["f5"] == [0] * 16 for segment in run["segments"]) is breaks_metal
    for segment in run["segments"]:
        assert segment["abilities"] == [0] and segment["minhp"] == 6
        assert segment["hp_decreases"] == segment["grabs"] == []


def test_737_cannot_create_an_unwitnessed_736_return() -> None:
    record = read("ordinary-532-fresh-direction-737-return-audit.json")
    assert {door["destination"] for door in record["737_reverse_audit"]["doors"]} == {600}
    rooms = json.loads((ROOT.parent / "data/regions/rooms.json").read_text())
    assert set(rooms["REGION_CARROT_CASTLE/ROOM_5_11"]["exits"]) == {
        "REGION_CARROT_CASTLE/ROOM_5_12",
    }
