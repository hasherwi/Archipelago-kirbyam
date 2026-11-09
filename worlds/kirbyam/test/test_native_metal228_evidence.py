"""Joint209/228 Hammer proof keeps the original finite-source qualification."""

import hashlib
import json
from pathlib import Path

import pytest

from .evidence_helpers import canonical_text_bytes


ROOT = Path(__file__).parents[1]
ARTIFACT = ROOT / "dev-docs/ordinary-228-joint-hammer-acceptance.json"


@pytest.mark.parametrize("mode,frames,parent_file,parent_checkpoint", [
    ("100", 3634, "ordinary-205-hammer-source-acceptance.json", "hammer209collected"),
    ("500", 3934, "ordinary-205-hammer-all500-acceptance.json", "all500-hammer209collected"),
])
def test_joint_hammer_chain_extends_the_actual_collected209_state(
    mode: str, frames: int, parent_file: str, parent_checkpoint: str,
) -> None:
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    parent = json.loads((ROOT / "dev-docs" / parent_file).read_text(encoding="utf-8"))
    run = data["runs"][mode]
    assert run["parent_checkpoint"] == parent_checkpoint
    assert run["rom_sha256"] in json.dumps(parent)
    parent_final = parent["chains"]["post_defeat_suffix"][-1]["checkpoints"][-1]
    assert {key: parent_final[key] for key in run["initial"]} == run["initial"]
    assert run["initial_flags"] == [128, 0]
    assert run["initial"]["ability"] == 17 and run["initial"]["hp"] == 6
    segments = run["segments"]
    assert len(segments) == 10 and len({s["id"] for s in segments}) == 10
    elapsed = 0
    for segment in segments:
        elapsed += sum(step[0] for step in segment["inputs"])
        assert segment["final"]["frame"] == elapsed
        assert segment["minimum_hp"] == segment["final"]["hp"] == 6
        assert segment["hp_decrease_frames"] == []
        assert segment["abilities"] == [17] and segment["final"]["ability"] == 17
        assert segment["flags"][0] == 128 and segment["flags"][2] == 0
    assert elapsed == frames == run["audited_frame_count"]
    assert (segments[0]["final"]["room"], segments[0]["final"]["x"], segments[0]["final"]["y"]) == (
        205, 456, 280.99609375)
    assert (segments[3]["final"]["room"], segments[3]["final"]["x"], segments[3]["final"]["y"]) == (
        228, 408, 456.99609375)
    assert all(segment["final"]["room"] == 228 for segment in segments[3:])
    assert segments[-2]["flags"] == [128, 0, 0]
    assert segments[-1]["flags"] == [128, 64, 0]
    assert [30, 64] in segments[-1]["inputs"]  # Actual Up, not a proximity-only claim.
    assert (segments[-1]["final"]["x"], segments[-1]["final"]["y"]) == (472.35546875, 200.99609375)


@pytest.mark.parametrize("mode", ["100", "500"])
def test_metal_action_does_not_assume_closing_bombs_or_room_reset(mode: str) -> None:
    record = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    segments = record["runs"][mode]["segments"]
    unchanged = {(17, 23): 241, (17, 19): 243, (32, 15): 241, (32, 11): 243, (32, 12): 243}
    for segment in segments[3:]:
        tiles = {(t["x"], t["y"]): t["value"] for t in segment["tiles"]}
        assert {cell: tiles[cell] for cell in unchanged} == unchanged
        value = 245 if segment["id"] in {"jointHammer228entry", "jointHammer228lowerwalk"} else 0
        assert [tiles[(27, 23)], tiles[(27, 24)]] == [value, value]
    assert record["target"]["template"] == "0x088C046C"
    assert record["target"]["position"] == [480, 200]
    assert record["target"]["ap_location"] == "MINOR_CHEST_PEPPERMINT_PALACE_7_09"
    assert record["target"]["joint_readbacks"] == {"flag23": 128, "flag30": 64, "flag31": 0}
    assert "Separate rope chest" in record["target"]["excluded"]
    assert "No room exit/reset occurs after entering228" in record["bomb_order"]["note"]


def test_joint_artifact_hash_source_boundary_and_portable_scaler_identity() -> None:
    payload = canonical_text_bytes(ARTIFACT)
    blob = hashlib.sha1(b"blob " + str(len(payload)).encode() + b"\0" + payload).hexdigest()
    assert blob == "d050d3a81c862617fc45cf8fde2a6c61d158d5bd"
    record = json.loads(payload)
    assert record["native_source_commit"] == "7d969fbce14fdc838d2c1ea01389717fb96c3189"
    assert record["original_rom_sha1"] == "274b102b6d940f46861a92b4e65f89a51815c12c"
    qualifier = record["qualification"]
    assert qualifier["parent_artifact_blobs"] == {
        "100": "7c1c78f3eb0abb18b89e474f70f2c46a976722fc", "500": "ea041dfe45f124b0f9893c1780ea19cb693426b3"}
    assert "not a new combined Bonkers fight/capture replay" in qualifier["source"]
    assert "scroll-lock file0x8BF5C8 moved x384 to2000" in qualifier["inherited_fixture"]
    assert "not a new source or room reset" in qualifier["inherited_fixture"]
    assert "No runtime state writes" in qualifier["extension"]
    assert "dropped-star recovery, or source reacquisition" in qualifier["extension"]
    source = canonical_text_bytes(ROOT / "enemy_health_scaling.py")
    assert hashlib.sha1(b"blob " + str(len(source)).encode() + b"\0" + source).hexdigest() == (
        qualifier["max_health_scaler"]["git_blob"])
    assert hashlib.sha256(source).hexdigest() == qualifier["max_health_scaler"]["sha256"]
    assert "not a full generated AP seed or direct1HP replay" in qualifier["health"]
