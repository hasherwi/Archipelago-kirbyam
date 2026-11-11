"""Exact imported-Stone controller proof, separate from real190 source access."""

import hashlib
import json
from pathlib import Path

import pytest

from .evidence_helpers import canonical_text_bytes


ROOT = Path(__file__).parents[1]
ARTIFACT = ROOT / "dev-docs/ordinary-205-imported-stone-acceptance.json"


@pytest.mark.parametrize("mode,frames,count,boss_hp", [("100", 8097, 23, 40), ("500", 19542, 70, 200)])
def test_linked_stone_carrier_has_continuous_health_and_actual_defeat(
    mode: str, frames: int, count: int, boss_hp: int,
) -> None:
    record = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    run = record["runs"][mode]
    segments = run["segments"]
    assert len(segments) == count
    elapsed = 0
    for index, segment in enumerate(segments):
        elapsed += sum(step[0] for step in segment["inputs"])
        assert segment["final"]["frame"] == elapsed
        assert segment["final"]["hp"] == 6 and segment["hp_decrease_frames"] == []
        if index:
            assert segment["minimum_hp"] == 6
            assert segment["abilities"] == ([0, 8] if index == 1 else [8])
            assert segment["final"]["ability"] == 8
        else:
            assert segment["minimum_hp"] is None  # Boot/menu is not a gameplay audit.
    assert elapsed - segments[0]["final"]["frame"] == frames == run["post_boot_frame_count"]
    lookup = {segment["id"]: segment for segment in segments}
    assert len(lookup) == count
    assert segments[1]["boss_hp_slot_readback"] == boss_hp
    defeat_id = "boxcycle3" if mode == "100" else "box500-hit26"
    defeat = lookup[defeat_id]
    assert defeat["boss_hp_slot_readback"] == 0 and defeat["final"]["room"] == 210
    release = lookup["boxDefeatedWaitExit"]
    assert release["final"]["frame"] > defeat["final"]["frame"]
    assert (release["final"]["room"], release["final"]["y"]) == (210, 16)
    assert [600, 0] in release["inputs"]  # Safe transformed wait before untransforming.
    arrival = lookup["stone210actual205"]["final"]
    assert (arrival["room"], arrival["x"], arrival["y"]) == (205, 152, 296.99609375)
    assert lookup["stone205snooterjump"]["floor_tiles"] == [245] * 4
    assert lookup["stone205floor"]["floor_tiles"] == [0] * 4
    floor = lookup["stone205floor"]["final"]
    assert (floor["room"], floor["x"], floor["y"]) == (205, 350.3828125, 232.99609375)
    assert lookup["stone205waterintercept"]["floor_tiles"] == [0] * 4
    arrival = lookup["stone209entry"]["final"]
    assert (arrival["room"], arrival["x"], arrival["y"]) == (209, 168, 40.99609375)
    final = segments[-1]
    assert final["id"] == "stone209collect" and final["flag23_masked"] == 128
    assert [1, 64] in final["inputs"]  # Actual Up interaction, not proximity.
    assert (final["final"]["room"], final["final"]["x"], final["final"]["y"]) == (
        209, 53.6171875, 56.99609375)


def test_stone_artifact_identity_fixture_boundaries_and_exact_scaler() -> None:
    payload = canonical_text_bytes(ARTIFACT)
    assert hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest() == (
        "d718181f8fe97aa99d698ea41ed7d55d0f88af62")
    record = json.loads(payload)
    assert record["original_usa_sha1"] == "274b102b6d940f46861a92b4e65f89a51815c12c"
    assert record["native_source_commit"] == "7d969fbce14fdc838d2c1ea01389717fb96c3189"
    qualification = record["qualification"]
    assert "not proof of access to the real Stone statue in190" in qualification
    assert "0x088C0ED0 changed from type0x93 subtype1 to type0x92 subtype4" in qualification
    assert "Do not credit this synthetic290 statue as a production source" in qualification
    assert "No other object changes, terrain edits, attack edits, boss defeat substitutions" in qualification
    assert "scroll-lock relocation, runtime writes or dropped-star recovery" in qualification
    assert "not a full AP patch or direct1HP option replay" in qualification
    boss = record["boss"]
    assert (boss["template_bus"], boss["type"], boss["scroll_lock_template_bus"], boss["shared_slot"]) == (
        "0x088BF7E4", 0x3C, "0x088BF5EC", 1)
    assert "Actual Box Boxer combat" in boss["mechanism"]
    assert record["floor"]["cells"] == [[21, 8], [22, 8], [21, 9], [22, 9]]
    assert record["target"] == {"room": 209, "native_flag": 23, "mask": 128,
                                "readback_address": "0x02038962"}
    assert [(door["source"], door["destination"], door["stored_arrival"]) for door in record["doors"]] == [
        (290, 210, [27, 49]), (210, 205, [10, 19]), (205, 209, [11, 3])]
    source = canonical_text_bytes(ROOT / "enemy_health_scaling.py")
    assert hashlib.sha1(b"blob " + str(len(source)).encode() + b"\0" + source).hexdigest() == (
        record["scaler"]["git_blob"])
    assert hashlib.sha256(source).hexdigest() == record["scaler"]["sha256"]
    sanity = record["scaler"]["sanity"]
    assert sanity["box_boxer_dedicated_health_row_file_offset"] == "0x00351550"
    assert sanity["default"] == [40, 60, 80, 90]
    assert sanity["scaled500"] == [200, 300, 400, 450]
    assert sanity["single_human_runtime_initial_hp"] == [40, 200]
