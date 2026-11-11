"""537 evidence includes actual Stone acquisition, not an imported-equipment fixture."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from .evidence_helpers import canonical_text_bytes


ROOT = Path(__file__).parents[1]
BLOB = "657c7651a7441c58c02d2718c73ded38daa57fc4"


def artifact() -> dict[str, Any]:
    raw = canonical_text_bytes(ROOT / "dev-docs/native-537-stone-source-carrier-acceptance.json")
    assert hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == BLOB
    record: dict[str, Any] = json.loads(raw)
    return record


@pytest.mark.parametrize("health,total,segments", [("100", 8141, 43), ("500", 8395, 50)])
def test_real_source_and_six_actual_doors_preserve_stone_to_collected_chest(
    health: str, total: int, segments: int,
) -> None:
    record = artifact()
    run = record["runs"][health]
    assert run["frames"] == total and len(run["segments"]) == segments
    frame, acquired = 0, False
    for index, segment in enumerate(run["segments"]):
        frame += sum(step[0] for step in segment["inputs_frames_keys"])
        end = segment["end"]
        assert end["frame"] == frame and end["hp"] == end["minhp"] == 6
        assert end["grab"] == 0
        if index:
            assert end["grabs"] == [0]
            if acquired:
                assert end["abilities"] == [8] and end["ability"] == 8
            else:
                assert set(end["abilities"]) <= {0, 8}
                acquired = end["ability"] == 8
        if end["room"] == 141:
            assert len(end["f5"]) == 8 and all(cell[2] == 245 for cell in end["f5"])
    assert acquired and frame == total
    events = run["transition_and_flag_events"]
    assert [event["room"] for event in events] == [190, 143, 141, 543, 542, 536, 537, 537]
    assert [(d["source"], d["destination"]) for d in record["doors"]] == [
        (190, 143), (143, 141), (141, 543), (543, 542), (542, 536), (536, 537)]
    assert events[-2]["f5"] == [[30, 6, 245], [31, 6, 245], [30, 7, 245], [31, 7, 245]]
    final = run["segments"][-1]["end"]
    assert final["room"] == 537 and final["ability"] == 8 and final["chest_byte0"] == 2
    assert final["f5"] == [[30, 6, 0], [31, 6, 0], [30, 7, 0], [31, 7, 0]]
    assert record["target"] == "MINOR_CHEST_MUSIC_NOTE_01" and record["location_id"] == 3960514
    assert record["room537"]["native_flag"] == 1
    assert record["room537"]["chest_template_bus"] == "0x088B5FA8"


def test_startup_only_fixture_preserves_real190_source_and_production_scaler() -> None:
    record = artifact()
    source = record["source"]
    assert (source["room"], source["template_bus"], source["source_key"], source["native_ability"],
            source["type"], source["subtype1"]) == (190, "0x088B7CEC", "STATUE:353900", 8, 0x92, 4)
    fixture = record["fixture"]
    assert fixture["native_objects_terrain_abilities_unchanged"]
    offsets = {int(offset, 16) for offset in fixture["changed_rom_byte_offsets"]}
    assert offsets <= set(range(0x2D8CB8, 0x2D8CC0)) | set(range(0x2D8CD0, 0x2D8CF0))
    assert "separate logical obligation" in fixture["startup_scope"]
    assert record["audit_contract"]["postboot_frame_start"] == 1086
    audit = record["audit_contract"]
    assert audit["ram_writes"] == audit["savestate_loads_during_final_replay"] == 0
    raw = canonical_text_bytes(ROOT / "enemy_health_scaling.py")
    assert hashlib.sha256(raw).hexdigest() == record["scaler"]["sha256"]
    assert hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == record["scaler"]["git_blob"]


@pytest.mark.parametrize("health", ["100", "500"])
def test_ordinary_mutations_do_not_silently_open141_metal_or_skip542_door(health: str) -> None:
    mutations = artifact()["carrier_mutation_audit"]["runs"][health]
    assert {(tuple(c["cell"]), c["native"], c["live"]) for c in mutations["141"]["changed_cells"]} == {
        ((10, 17), 240, 0), ((9, 16), 240, 0)}
    for room in (190, 143, 543, 536):
        assert mutations[str(room)]["changed_cells"] == []
    changed = mutations["542"]["changed_cells"]
    assert len(changed) == 19
    assert sum(c["native"] in (241, 242) for c in changed) == 11
    assert sum(c["native"] == 240 for c in changed) == 8
    door, = (c for c in changed if c["cell"] == [3, 8])
    assert (door["native"], door["live"]) == (240, 255)
