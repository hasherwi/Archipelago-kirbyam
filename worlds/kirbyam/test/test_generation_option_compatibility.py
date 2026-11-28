"""Kirby-only unsupported option combinations fail at the real generation entry point."""

from pathlib import Path

import pytest

from Options import OptionError
from test.general import setup_multiworld

from .. import KirbyAmWorld
from ..options import validate_generation_options
from .support.integration_generation import generate_archive_from_fixture


@pytest.mark.parametrize("room_sanity", [0, 1])
@pytest.mark.parametrize("accessibility", ["full", "minimal"])
def test_full_completion_with_completely_random_weight_100_is_rejected(
        tmp_path: Path, room_sanity: int, accessibility: str) -> None:
    player = tmp_path / "player.yaml"
    player.write_text(
        "name: KirbyProbe\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n"
        "  goal: full_completion\n  ability_randomization_mode: completely_random\n"
        "  ability_randomization_no_ability_weight: 100\n"
        f"  room_sanity: {room_sanity}\n  accessibility: {accessibility}\n",
        encoding="utf-8",
    )
    output = tmp_path / "out"
    with pytest.raises(OptionError, match=r"KirbyAM \(KirbyProbe\): 100% Game Completion "
                                         r".*required Mustard Mountain Map.*below 100"):
        generate_archive_from_fixture(player, output, seed=1197)
    assert not tuple(output.iterdir())


@pytest.mark.parametrize(("goal", "mode", "weight"), [
    ("full_completion", "completely_random", 99),
    ("full_completion", "off", 100),
    ("full_completion", "shuffled", 100),
    ("dark_mind", "completely_random", 100),
    ("defeat_any_area_boss", "completely_random", 100),
])
def test_neighboring_profiles_do_not_trigger_this_guard(goal: str, mode: str, weight: int) -> None:
    world = setup_multiworld(KirbyAmWorld, steps=(), seed=1197, options={
        "goal": goal, "ability_randomization_mode": mode, "ability_randomization_no_ability_weight": weight,
    }).worlds[1]
    assert isinstance(world, KirbyAmWorld)
    validate_generation_options(world.options, world.player_name)


@pytest.mark.parametrize(("goal", "weight", "goal_id"), [
    ("full_completion", 99, 5), ("dark_mind", 100, 0),
])
def test_neighboring_completely_random_profiles_generate_an_archive(
        tmp_path: Path, goal: str, weight: int, goal_id: int) -> None:
    from .support.integration_generation import load_multidata_from_archive

    player = tmp_path / "player.yaml"
    player.write_text(
        "name: KirbyProbe\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n"
        f"  goal: {goal}\n  ability_randomization_mode: completely_random\n"
        f"  ability_randomization_no_ability_weight: {weight}\n",
        encoding="utf-8",
    )
    archive = generate_archive_from_fixture(player, tmp_path / "out", seed=1197)
    slot = load_multidata_from_archive(archive)["slot_data"][1]
    assert slot["goal"] == goal_id
    assert slot["ability_randomization_no_ability_weight"] == weight
