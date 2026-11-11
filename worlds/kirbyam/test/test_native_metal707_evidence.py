"""707 carrier traces do not impersonate production statue acquisition."""

import hashlib
import json
from pathlib import Path

from .evidence_helpers import canonical_text_bytes

import pytest


ROOT = Path(__file__).parents[1]


@pytest.mark.parametrize("name,segments,frames", [
    ("ordinary-707-imported-burning-acceptance.json", 25, 5022),
    ("ordinary-707-all500-acceptance.json", 26, 5243),
])
def test_continuous_carrier_and_actual_exit(name: str, segments: int, frames: int) -> None:
    record = json.loads((ROOT / "dev-docs" / name).read_text(encoding="utf-8"))
    trace = record["segments"]
    assert len(trace) == segments
    previous = None
    for segment in trace:
        assert segment["parent_controller_state"] == previous
        assert not segment["writes"]
        if previous is not None:
            assert all(point["hp"] == 6 for point in segment["checkpoints"])
        else:
            # Cold title-screen records precede Kirby creation and have HP0.
            assert segment["checkpoints"][-1]["hp"] == 6
            assert segment["checkpoints"][-1]["ability"] == 3
        previous = segment["segment"]
    audit = {row["segment"]: row for row in record["per_frame_hp_audit"]}
    assert set(audit) == {segment["segment"] for segment in trace[1:]}
    assert sum(row["frames"] for row in audit.values()) == frames
    for segment in trace[1:]:
        assert audit[segment["segment"]]["frames"] == sum(step["frames"] for step in segment["inputs"])
    assert all(row["minimum_hp"] == 6 and not row["decrease_frames"] and row["abilities"] == [3]
               for row in audit.values())
    assert trace[-1]["checkpoints"][-1]["room"] == 712
    assert trace[-1]["checkpoints"][-1]["ability"] == 3
    observation = list(record["observations"].values())
    assert (observation[0]["room"], observation[0]["x"], observation[0]["y"]) == (707, 24, 152.99609375)
    assert {(tile["x"], tile["y"], tile["tile"]) for tile in observation[0]["F5_bank"]} == {
        (69, 4, 245), (70, 4, 245)}
    assert {(tile["x"], tile["y"], tile["tile"]) for tile in observation[1]["F5_bank"]} == {
        (69, 4, 0), (70, 4, 0)}
    assert (observation[-1]["room"], observation[-1]["x"], observation[-1]["y"]) == (712, 24, 456.99609375)
    mechanism = record["mechanism"]
    assert mechanism["button_template"] == "0x088BCD6C" and mechanism["door_template"] == "0x088BCD00"
    assert mechanism["slot"] == 1
    assert mechanism["template_u16_0x18"] == 0 and mechanism["template_u16_0x22"] == 8
    changes = " ".join(record["fixture"]["changes"])
    assert "0x8BDDF0 subtype6 changed to1" in changes
    assert "NOT a production Burning source" in changes
    assert "592" in record["fixture"]["qualification"]


def test_all500_pins_production_scaler_not_only_one_enemy() -> None:
    record = json.loads((ROOT / "dev-docs/ordinary-707-all500-acceptance.json").read_text(encoding="utf-8"))
    source = canonical_text_bytes(ROOT / "enemy_health_scaling.py")
    git_blob = hashlib.sha1(b"blob " + str(len(source)).encode() + b"\0" + source).hexdigest()
    assert git_blob == record["fixture"]["scaling_module_git_blob"]
    assert record["fixture"]["Doo_HP_check"] == {"original": 4, "scaled": 20}
    assert "applied once" in record["fixture"]["qualification"]
    assert any(segment["segment"] == "all500-knightpulse98" for segment in record["segments"])
