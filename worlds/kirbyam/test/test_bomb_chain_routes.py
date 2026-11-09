"""Keep reviewed Bomb approaches directional without adding metal ability gates.

These are AP topology/rule regressions, not native movement acceptance. See
dev-docs/bomb-chain-route-audit.md for the source and visual review boundaries.
"""

from types import SimpleNamespace
from typing import cast

from BaseClasses import CollectionState

import pytest

from ..data import data
from ..rules import evaluate_room_logic_requirement


MANSION = "REGION_MOONLIGHT_MANSION/"
RAINBOW = "REGION_RAINBOW_ROUTE/"


def test_mansion_11_right_arrival_does_not_enter_the_machine_or_lever_compartment() -> None:
    main = MANSION + "ROOM_2_11"
    dead_end = main + "_DEAD_END"
    left = data.regions[MANSION + "ROOM_2_01_BOTTOM_LEFT"]
    right = data.regions[MANSION + "ROOM_2_01_BOTTOM_RIGHT"]
    assert main in left.exits and dead_end not in left.exits
    assert dead_end in right.exits and main not in right.exits
    assert data.regions[dead_end].exits == [MANSION + "ROOM_2_01_BOTTOM_RIGHT"]
    assert not data.regions[dead_end].locations
    assert "LEVER_MOONLIGHT_MANSION_2_11" in data.regions[main].locations


def test_mansion_11_machine_does_not_replace_the_ap_lever_wall_item() -> None:
    main = MANSION + "ROOM_2_11"
    after = main + "_AFTER_LEVER"
    requirement = data.regions[main].exit_requirements[after]
    queried = []
    owned = set()

    def has(item: str, player: int) -> bool:
        queried.append((item, player))
        return item in owned

    state = cast(CollectionState, SimpleNamespace(has=has))
    assert not evaluate_room_logic_requirement(requirement, state, 1)
    owned.add("Activate Lever - Moonlight Mansion 2-11")
    assert not evaluate_room_logic_requirement(requirement, state, 1)
    owned.add("Moonlight Mansion 2-11 - Lever Wall")
    assert evaluate_room_logic_requirement(requirement, state, 1)
    assert set(queried) == {("Moonlight Mansion 2-11 - Lever Wall", 1)}


@pytest.mark.parametrize("source,target", [
    (RAINBOW + "ROOM_1_06_LOWER_RIGHT", RAINBOW + "ROOM_1_06_LOWER_MID"),
    (RAINBOW + "ROOM_1_06_LOWER_MID", RAINBOW + "ROOM_1_06_LOWER_RIGHT"),
    (RAINBOW + "ROOM_1_06_LOWER_MID", RAINBOW + "ROOM_1_06_UPPER"),
])
def test_existing_ordinary_bomb_passages_do_not_query_copy_ability_unlocks(source: str, target: str) -> None:
    def has(item: str, player: int) -> bool:
        pytest.fail(f"Ordinary Bomb passage unexpectedly queried {item!r} for player {player}")

    region = data.regions[source]
    assert target in region.exits
    assert evaluate_room_logic_requirement(region.exit_requirements.get(target),
                                           cast(CollectionState, SimpleNamespace(has=has)), 1)


def test_rainbow_6_upper_arrival_cannot_inherit_the_lower_bomb_approach() -> None:
    upper = data.regions[RAINBOW + "ROOM_1_06_UPPER"]
    assert set(upper.exits) == {RAINBOW + "ROOM_1_05"}
    lower_mid = data.regions[RAINBOW + "ROOM_1_06_LOWER_MID"]
    assert RAINBOW + "ROOM_1_06_UPPER" in lower_mid.exits
    # The optional chest remains a separate Wheel witness, not an ordinary Bomb opening.
    from ..traversal_data import room_traversal_targets
    assert any(row["id"] == "wheel_108_chest"
               and row["exit"] == RAINBOW + "ROOM_1_06_LOWER_CHEST"
               for row in room_traversal_targets("wheel"))


def test_mansion_machine_does_not_grant_an_unproved_normal_dead_end_join() -> None:
    # The new native trace retains Burning through this maze. It does not
    # establish the old generic Normal alias; source-backed C-right access is separate.
    assert MANSION + "ROOM_2_11_DEAD_END" not in data.regions[MANSION + "ROOM_2_11"].exits
