"""Real world wiring and archive generation for the reviewed Mini corridors."""

from argparse import Namespace

import pytest
from BaseClasses import CollectionState, MultiWorld

from .. import KirbyAmWorld
from ..enemy_ability_data import STARTING_COPY_ABILITIES, starting_copy_abilities
from ..mini_traversal import mini_routes
from ..traversal import SourcePolicy
from .support.integration_generation import generate_archive_from_fixture, load_multidata_from_archive


def make_world(mode, gating):
    multiworld = MultiWorld(1)
    multiworld.game[1] = KirbyAmWorld.game
    multiworld.player_name = {1: "Mini traversal"}
    multiworld.set_seed(773)
    args = Namespace()
    overrides = {"ability_randomization_mode": mode, "ability_gating": gating}
    for name, option in KirbyAmWorld.options_dataclass.type_hints.items():
        setattr(args, name, {1: option.from_any(overrides.get(name, option.default))})
    multiworld.set_options(args)
    world = multiworld.worlds[1]
    multiworld.state = CollectionState(multiworld)
    world.generate_early()
    world.create_regions()
    world.set_rules()
    return world


@pytest.mark.parametrize("mode", [0, 1, 2])
@pytest.mark.parametrize("gating", [0, 1])
def test_all_four_exact_branches_and_bypasses(mode, gating):
    world = make_world(mode, gating)
    state = CollectionState(world.multiworld)
    assert not state.has("Mini Ability", 1)
    assert state.has("Stone Ability", 1) and state.has("Wheel Ability", 1)
    for row, graph in mini_routes():
        if row["exit"]:
            target = world.multiworld.get_entrance(f"{row['region']} -> {row['exit']}", 1)
        else:
            from ..data import data
            target = world.multiworld.get_location(data.locations[row["location"]].label, 1)
        assert target.access_rule(state) == (not gating), row["id"]
        state.collect(world.create_item("Mini Ability"), prevent_sweep=True)
        assert target.access_rule(state), row["id"]
        state.remove(world.create_item("Mini Ability"))
        # No room-wide gate: normal route remains independently available.
        result = graph.evaluate(SourcePolicy(world._enemy_copy_ability_policy), frozenset(), True)
        assert result.reaches(row["id"] + ":bypass")
        assert not result.reaches(row["id"] + ":target")


def test_only_minny_option_removed():
    options = KirbyAmWorld.options_dataclass.type_hints
    assert "ability_randomization_minny" not in options
    assert {"ability_randomization_mode", "ability_randomization_statues", "ability_gating",
            "ability_randomization_minibosses", "ability_randomization_boss_spawns"} <= options.keys()


def test_mini_removed_in_all_modes_without_changing_stone_or_wheel():
    assert starting_copy_abilities(0) == starting_copy_abilities(1)
    assert set(starting_copy_abilities(0)) == set(STARTING_COPY_ABILITIES) - {"Mini"}
    assert starting_copy_abilities(2) == starting_copy_abilities(0)


@pytest.mark.parametrize("mode,gating", [(0, 1), (1, 1), (1, 0), (2, 1)])
def test_full_generation_accessibility_and_slot_contract(tmp_path, mode, gating):
    player = tmp_path / "player.yaml"
    player.write_text(
        "name: Mini\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n"
        f"  ability_randomization_mode: {mode}\n  ability_gating: {gating}\n"
        "  ability_randomization_minny: 1\n",  # Old YAML must not re-enable source randomization.
        encoding="utf-8",
    )
    archive = generate_archive_from_fixture(player, tmp_path / "out", seed=773)
    decoded = load_multidata_from_archive(archive)
    slot = decoded["slot_data"][1]
    assert "ability_randomization_minny" not in slot
    assert slot["enemy_copy_ability_policy"]["ability_randomization_minny"] is False
    assert (3860123 in decoded["precollected_items"][1]) is False
    assert 3860108 in decoded["precollected_items"][1]  # Stone is never removed.
    assert (3860123 in [item[0] for item in decoded["locations"][1].values()]) == bool(gating)
