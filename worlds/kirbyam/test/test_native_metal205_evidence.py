"""Bounded205 evidence integrity, without promoting incomplete209 topology."""

import hashlib
import json
from pathlib import Path

from .evidence_helpers import canonical_text_bytes

import pytest


ROOT = Path(__file__).parents[1]


@pytest.mark.parametrize("filename,prefix,segments,frames", [
    ("ordinary-205-hammer-source-acceptance.json", "", 19, 4290),
    ("ordinary-205-hammer-all500-acceptance.json", "all500-", 18, 4184),
])
def test_layered_hammer_carrier_has_linked_no_loss_audit(
        filename: str, prefix: str, segments: int, frames: int) -> None:
    record = json.loads((ROOT / "dev-docs" / filename).read_text(encoding="utf-8"))
    assert record["original_usa_sha1"] == "274b102b6d940f46861a92b4e65f89a51815c12c"
    assert record["native_source_commit"] == "7d969fbce14fdc838d2c1ea01389717fb96c3189"
    assert "No runtime writes" in record["qualification"]
    assert "not full bonkers" in record["qualification"].lower()
    chains = record["chains"]
    assert set(chains) == {"normal_source_approach", "post_defeat_suffix"}
    audited_segments = []
    for chain in chains.values():
        previous = None
        for index, segment in enumerate(chain):
            assert segment["parent_state"] == previous
            assert all(point["hp"] == 6 for point in segment["checkpoints"])
            if index:
                audited_segments.append(segment)
            previous = segment["segment"]
    assert len(audited_segments) == segments
    audit = {row["segment"]: row for row in record["per_frame_hp_audit"]}
    assert len(audit) == len(record["per_frame_hp_audit"])
    assert set(audit) == {segment["segment"] for segment in audited_segments}
    assert sum(row["frames"] for row in audit.values()) == frames
    for segment in audited_segments:
        row = audit[segment["segment"]]
        assert row["frames"] == sum(step["frames"] for step in segment["inputs"])
        assert row["minimum_hp"] == 6 and row["decrease_frames"] == []
    for segment in chains["normal_source_approach"][1:]:
        assert audit[segment["segment"]]["abilities"] == [0]
    suffix = chains["post_defeat_suffix"]
    assert audit[suffix[1]["segment"]]["abilities"] == [0, 17]
    assert all(audit[segment["segment"]]["abilities"] == [17] for segment in suffix[2:])
    approach = chains["normal_source_approach"][-1]["checkpoints"][-1]
    assert (approach["room"], approach["x"], approach["y"], approach["ability"]) == (
        210, 393.140625, 232.99609375, 0)
    final = suffix[-1]["checkpoints"][-1]
    assert (final["room"], final["x"], final["y"], final["ability"]) == (
        209, 53.6171875, 56.99609375, 17)
    observations = record["observations"]
    before = observations[prefix + "hammer205plug"]
    after = observations[prefix + "hammer205floorbreak"]
    bank = {(21, 8), (22, 8), (21, 9), (22, 9)}
    for observation, expected in ((before, 245), (after, 0)):
        assert {(tile["x"], tile["y"]) for tile in observation["floor_tiles"]} == bank
        assert all(tile["tile"] == expected for tile in observation["floor_tiles"])
    assert observations[prefix + "hammer209collected"]["flag23_masked"] == 128
    assert suffix[-1]["inputs"][1] == {"frames": 1, "keys": 64}  # Up, not proximity.
    assert "A1, release8, B1, wait60 repeated twice" in record["attack"]
    assert "A6 high-jump attack was a rejected" in record["attack"]


def test_actual_bonkers_identity_is_separate_from_post_defeat_fixture() -> None:
    record = json.loads((ROOT / "dev-docs/ordinary-205-hammer-source-acceptance.json").read_text(encoding="utf-8"))
    source = record["source"]
    assert (source["room"], source["template"], source["position"], source["type"]) == (
        210, "0x088BF730", [440, 232], 0x39)
    assert source["copy_table_ability"] == 17
    enemies = json.loads((ROOT / "data/enemies.json").read_text(encoding="utf-8"))
    assert enemies["BONKERS"]["default_ability"] == "Hammer"
    assert int(enemies["BONKERS"]["addresses"][0], 16) == 0x351648 + source["type"] * 24 + 6
    lock = source["scroll_lock"]
    assert (lock["template"], lock["position"], lock["unk4"], lock["unk22"]) == (
        "0x088BF5C8", [384, 192], 2, 6)
    assert source["unk4"] == lock["unk4"]
    assert source["unk2"] or source["unk3"] != 31
    fixture = record["fixtures"]["suffix"]
    assert "Bonkers template changed toHammerstatue0x93 subtype6" in fixture
    assert "scrolllock template x384→2000" in fixture
    assert "This essence is not credited as production source" in fixture
    assert "Combat availability remains existing world assumption" in source["contract"]


def test_all500_pins_unchanged_production_scaler_and_prompt_exit() -> None:
    record = json.loads((ROOT / "dev-docs/ordinary-205-hammer-all500-acceptance.json").read_text(encoding="utf-8"))
    assert "a062278eea84ce3c2a6a7bbc601262cda0f3fab2" in record["qualification"]
    assert "applied once to both fixtures before fresh boot" in record["qualification"]
    # Git blob at the pinned revision, independently resolved from the repository.
    source = canonical_text_bytes(ROOT / "enemy_health_scaling.py")
    blob = hashlib.sha1(b"blob " + str(len(source)).encode() + b"\0" + source).hexdigest()
    assert blob == "bbae3fc5368eddecc7183590ce7f4defaf7effa4"
    assert "no kill assumption or new source" in record["max_health_timing_note"]
    assert any(segment["segment"] == "all500-hammer209prompt"
               for segment in record["chains"]["post_defeat_suffix"])


@pytest.mark.parametrize("variant,frames", [("default", 1403), ("all500", 1663)])
def test_normal_return_is_directed_egress_with_intact_metal(variant: str, frames: int) -> None:
    record = json.loads((ROOT / "dev-docs/ordinary-205-normal-return-egress.json").read_text(encoding="utf-8"))
    assert "does not independently prove access to209" in record["qualification"]
    assert "No runtime state writes" in record["qualification"]
    assert record["scaler"]["git_blob"] == "bbae3fc5368eddecc7183590ce7f4defaf7effa4"
    assert record["scaler"]["sha256"] == "cff04ec15000178c220ea4a3774cebc4412ceb386275faefe85d46e1d72c8098"
    chain = record["chains"][variant]["segments"]
    assert len(chain) == 7
    previous = None
    audits = {row["segment"]: row for row in record["audits"]}
    assert len(audits) == len(record["audits"]) == 12
    assert set(audits) == {
        segment["id"] for branch in record["chains"].values() for segment in branch["segments"][1:]}
    relevant = []
    for index, segment in enumerate(chain):
        assert segment["parent_state"] == previous
        assert all(point["hp"] == 6 and point["ability"] == 0 for point in segment["checkpoints"])
        if index:
            row = audits[segment["id"]]
            assert row["frames"] == sum(step["frames"] for step in segment["inputs"])
            assert row["minimum_hp"] == 6 and row["decrease_frames"] == [] and row["abilities"] == [0]
            relevant.append(row)
        previous = segment["id"]
    assert sum(row["frames"] for row in relevant) == frames
    arrival = chain[1]["checkpoints"][-1]
    assert (arrival["room"], arrival["x"], arrival["y"]) == (205, 456, 280.99609375)
    observation = record["observations"][variant]
    final = observation["final"]
    assert (final["room"], final["x"], final["y"], final["ability"]) == (
        205, 347.23046875, 21.00390625, 0)
    metal = {(tile["x"], tile["y"]): tile["tile"] for tile in observation["metal_tiles"]}
    assert set(metal) == {(x, y) for x in (21, 22) for y in (8, 9)} | {
        (x, y) for x in (24, 25, 26) for y in (3, 4)}
    assert set(metal.values()) == {245}
    assert {(tile["x"], tile["y"]): tile["tile"] for tile in observation["shaft_tiles"]} == {
        (23, 12): 0x48, (24, 12): 0x48, (25, 12): 0x48, (25, 11): 0x48, (25, 10): 0x48, (25, 9): 0x0F}
