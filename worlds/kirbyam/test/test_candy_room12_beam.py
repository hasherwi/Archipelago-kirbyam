"""The source-backed Bomb Block belongs to the Candy 9-12 chest only."""

from pathlib import Path

import pytest

from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive
from .support.source_policy import set_rule_test_policy
from .test_mini_traversal import make_world
from .test_traversal import policy
from ..data import data
from ..traversal import CAPABILITY_ABILITIES
from ..traversal_data import room_traversal_graph, room_traversal_targets
from ..traversal_rules import target_applies


ROOM = "REGION_CANDY_CONSTELLATION/ROOM_9_12"
EXIT = ROOM + " -> REGION_CANDY_CONSTELLATION/ROOM_9_13"
LOCATION = "MINOR_CHEST_CANDY_CONSTELLATION_9_12"
TARGET = "bomb_402_candy_chest"


@pytest.mark.parametrize("area_keys", [False, True])
def test_requires_actual_local_beam_not_normal_or_permission(area_keys):
    row = next(row for row in room_traversal_targets("block") if row["id"] == TARGET)
    graph = room_traversal_graph(TARGET, "local_beam", area_keys)
    chest, = graph.required_targets
    normal = policy(0, minny=False)
    wrong_source = policy(1, pool=["Sword"], minny=False)
    assert CAPABILITY_ABILITIES[TARGET] == {"Beam"}
    assert target_applies(row, normal)
    assert not target_applies(row, wrong_source)
    for gating in (False, True):
        assert graph.evaluate(normal, frozenset(), gating).reaches(chest)
        assert not graph.evaluate(wrong_source, frozenset({"Beam Ability"}), gating).reaches(chest)
    assert data.locations[LOCATION].location_id == 3960575


@pytest.mark.parametrize("mode,pool,supported", [(0, None, True), (1, ["Beam"], True), (1, ["Sword"], False)])
def test_world_rule_only_adds_witness_to_this_chest(monkeypatch, mode, pool, supported):
    resolved = policy(mode, pool=pool, minny=False)
    set_rule_test_policy(monkeypatch, lambda *args, **kwargs: resolved.policy)
    world = make_world(mode, False, accessibility="minimal", room_sanity=1, area_keys=0)
    mw = world.multiworld
    state = mw.state
    chest = mw.get_location(data.locations[LOCATION].label, 1)
    visit, = [location for location in mw.get_region(ROOM, 1).locations if location.address == 3961232]
    exit_ = mw.get_entrance(EXIT, 1)
    monkeypatch.setattr(state, "can_reach_region", lambda region, player: False)
    assert chest.access_rule(state) is not supported
    assert visit.access_rule(state)
    assert exit_.access_rule(state)
    monkeypatch.setattr(state, "can_reach_region", lambda region, player: region == ROOM)
    assert chest.access_rule(state)
    assert visit.access_rule(state)
    assert exit_.access_rule(state)


def test_vanilla_source_seed_keeps_candy_chest_in_full_accessibility(tmp_path: Path):
    fixture = tmp_path / "player.yaml"
    fixture.write_text(
        "name: Candy\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n"
        "  ability_randomization_mode: 0\n  ability_gating: 1\n  room_sanity: 1\n"
        "  accessibility: full\n",
        encoding="utf-8",
    )
    archive = generate_archive_from_fixture(fixture, tmp_path / "out", seed=912)
    locations = load_multidata_from_archive(archive)["locations"][1]
    assert 3960575 in locations and 3961232 in locations
