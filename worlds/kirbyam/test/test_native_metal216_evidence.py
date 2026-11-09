"""The216 imported-equipment fixture proves movement, not a new Burning source."""

import hashlib
import json
from pathlib import Path

from .evidence_helpers import canonical_text_bytes

import pytest


ROOT = Path(__file__).parents[1]


@pytest.mark.parametrize("multiplier", ["100", "500"])
def test_actual_entry_low_dash_and_collection_have_continuous_no_loss_audit(multiplier: str) -> None:
    record = json.loads((ROOT / "dev-docs/ordinary-216-imported-burning-acceptance.json").read_text(encoding="utf-8"))
    assert record["original_usa_sha1"] == "274b102b6d940f46861a92b4e65f89a51815c12c"
    assert record["native_source_commit"] == "7d969fbce14fdc838d2c1ea01389717fb96c3189"
    run = record["runs"][multiplier]
    segments = run["segments"]
    assert len(segments) == 11
    assert len({segment["id"] for segment in segments}) == len(segments)
    frame = 0
    for index, segment in enumerate(segments):
        frame += sum(step["frames"] for step in segment["inputs"])
        assert segment["final"]["frame"] == frame
        assert segment["final"]["hp"] == 6
        if index:
            assert segment["minimum_hp"] == 6 and segment["decrease_frames"] == []
            assert segment["abilities"] == ([0, 3] if index == 1 else [3])
            assert segment["final"]["ability"] == 3
    assert frame - segments[0]["final"]["frame"] == 1305
    arrival = segments[2]["final"]
    assert (arrival["room"], arrival["x"], arrival["y"]) == (216, 696, 280.99609375)
    final = segments[-1]["final"]
    assert (final["room"], final["x"], final["y"], final["ability"]) == (
        216, 608.39453125, 72.99609375, 3)
    assert segments[-1]["inputs"] == [{"frames": 30, "keys": 64}, {"frames": 90, "keys": 0}]
    assert run["flag36_masked"] == 16
    assert {(tile["x"], tile["y"], tile["tile"]) for tile in run["metal_tiles"]} == {
        (x, y, 0) for x in (28, 29, 30) for y in (5, 6)}
    inventory = json.loads((ROOT / "docs/metal-tile-inventory.json").read_text(encoding="utf-8"))
    room = next(row for row in inventory["rooms"] if row["room"] == 216)
    assert {(tile["x"], tile["y"]) for tile in room["tiles"] if tile["tile"] == "0xf5"} == {
        (x, y) for x in (28, 29, 30) for y in (5, 6)}
    assert record["target"] == {"template": "0x088C1380", "position": [608, 72], "flag": 36}
    assert "441.996,104.996" in record["attack"] and "no downward Burning claim" in record["attack"]


def test_fixture_is_disclosed_and_scaler_matches_production() -> None:
    record = json.loads((ROOT / "dev-docs/ordinary-216-imported-burning-acceptance.json").read_text(encoding="utf-8"))
    qualification = record["qualification"]
    assert "No production source credit" in qualification
    assert "Native216 objects unchanged" in qualification
    assert "No runtime writes, terrain or attack changes" in qualification
    assert "Real291 Burning statue0x088C263C" in qualification
    assert "Not an actual AP patch or direct1HP fixture" in qualification
    mutations = {int(row["offset"], 16): row for row in record["fixture_changes"]}
    assert set(mutations) == {0x2D8CB8, 0x2D8CD0, 0x8C1042, 0x8C1048, 0x8C104A}
    assert (mutations[0x8C1048]["before"], mutations[0x8C1048]["after"]) == ("12", "92")
    assert (mutations[0x8C104A]["before"], mutations[0x8C104A]["after"]) == ("00", "01")
    source = canonical_text_bytes(ROOT / "enemy_health_scaling.py")
    blob = hashlib.sha1(b"blob " + str(len(source)).encode() + b"\0" + source).hexdigest()
    assert blob == record["scaler"]["git_blob"]
    assert hashlib.sha256(source).hexdigest() == record["scaler"]["sha256"]
    assert record["health_sanity"] == {
        "enemy_type": "0x22", "hp_file_offset": "0x35197c", "default": 2, "max500": 10}
