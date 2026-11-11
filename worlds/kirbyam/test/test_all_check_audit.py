"""A beatable minimal seed and an all-inventory state do not prove all checks."""

from types import SimpleNamespace
from typing import cast

import pytest
from BaseClasses import CollectionState, Item, ItemClassification, Location, MultiWorld, Region
from Options import Accessibility, PerGameCommonOptions
from test.general import TestWorld

from .support.check_accessibility import audit_local_checks


def fixture_world(players: int = 1) -> MultiWorld:
    multiworld = MultiWorld(players)
    multiworld.player_name = {player: f"Player {player}" for player in multiworld.player_ids}
    for player in multiworld.player_ids:
        world = TestWorld(multiworld, player)
        # Other loaded worlds' CollectionState mixins inspect every world's game.
        multiworld.game[player] = world.game
        world.options = cast(PerGameCommonOptions, SimpleNamespace(accessibility=Accessibility.from_any("minimal")))
        multiworld.worlds[player] = world
        multiworld.regions.append(Region("Menu", player, multiworld))
        multiworld.completion_condition[player] = lambda state: True
    multiworld.state = CollectionState(multiworld)
    return multiworld


def test_fixture_world_has_game_identity_for_global_logic_mixins() -> None:
    multiworld = fixture_world(2)
    assert {player: world.game for player, world in multiworld.worlds.items()} == multiworld.game


def add_check(multiworld: MultiWorld, name: str, player: int = 1) -> Location:
    region = multiworld.get_region("Menu", player)
    location = Location(player, name, 100 + len(multiworld.get_locations()), region)
    region.locations.append(location)
    return location


def place(multiworld: MultiWorld, location: Location, name: str, player: int = 1,
          classification: ItemClassification = ItemClassification.progression) -> Item:
    item = Item(name, classification, 1, player)
    multiworld.itempool.append(item)
    multiworld.push_item(location, item, collect=False)
    return item


def test_self_locked_permission_is_not_hidden_by_all_inventory_or_minimal_goal() -> None:
    multiworld = fixture_world()
    locked = add_check(multiworld, "Locked check")
    locked.access_rule = lambda state: state.has("Permission", 1)
    place(multiworld, locked, "Permission")
    place(multiworld, add_check(multiworld, "Reachable advancement"), "Unrelated progress")
    audit = audit_local_checks(multiworld, 1)
    assert multiworld.can_beat_game()
    assert multiworld.fulfills_accessibility()
    assert audit.inventory_unreachable == ()
    assert audit.progression_unreachable == ("Locked check",)
    assert audit.unfilled == ()
    assert multiworld.worlds[1].options.accessibility.current_key == "minimal"


@pytest.mark.parametrize("remote_reachable", [False, True])
def test_foreign_deliveries_require_an_independently_reachable_location(remote_reachable: bool) -> None:
    multiworld = fixture_world(2)
    target = add_check(multiworld, "Local target")
    target.access_rule = lambda state: state.has("Permission", 1)
    place(multiworld, target, "Filler", classification=ItemClassification.filler)
    remote = add_check(multiworld, "Foreign source", 2)
    remote.access_rule = lambda state: remote_reachable
    place(multiworld, remote, "Permission")
    unrelated = add_check(multiworld, "Unrelated unreachable", 2)
    unrelated.access_rule = lambda state: False
    place(multiworld, unrelated, "Filler", 2, ItemClassification.filler)
    audit = audit_local_checks(multiworld, 1)
    assert audit.inventory_unreachable == ()
    assert audit.progression_unreachable == (() if remote_reachable else ("Local target",))
    assert audit.unfilled == ()


def test_unreachable_without_any_assignment_is_a_separate_failure() -> None:
    multiworld = fixture_world()
    impossible = add_check(multiworld, "No source witness")
    impossible.access_rule = lambda state: False
    place(multiworld, impossible, "Filler", classification=ItemClassification.filler)
    audit = audit_local_checks(multiworld, 1)
    assert audit.inventory_unreachable == audit.progression_unreachable == ("No source witness",)


def test_useful_permission_is_not_promoted_by_the_audit() -> None:
    multiworld = fixture_world()
    source = add_check(multiworld, "Source")
    place(multiworld, source, "Misclassified permission", classification=ItemClassification.useful)
    target = add_check(multiworld, "Target")
    target.access_rule = lambda state: state.has("Misclassified permission", 1)
    place(multiworld, target, "Filler", classification=ItemClassification.filler)
    audit = audit_local_checks(multiworld, 1)
    assert audit.inventory_unreachable == audit.progression_unreachable == ("Target",)


def test_precollected_permission_works_without_modifying_global_state() -> None:
    multiworld = fixture_world()
    target = add_check(multiworld, "Target")
    target.access_rule = lambda state: state.has("Permission", 1)
    place(multiworld, target, "Filler", classification=ItemClassification.filler)
    multiworld.push_precollected(Item("Permission", ItemClassification.progression, 1, 1))
    before = multiworld.state.copy()
    first = audit_local_checks(multiworld, 1)
    assert first == audit_local_checks(multiworld, 1)
    assert first.inventory_unreachable == first.progression_unreachable == first.unfilled == ()
    assert multiworld.state.prog_items == before.prog_items
    assert multiworld.state.locations_checked == before.locations_checked


def test_unfilled_check_never_counts_as_valid_completed_generation() -> None:
    multiworld = fixture_world()
    add_check(multiworld, "Unfilled")
    audit = audit_local_checks(multiworld, 1)
    assert audit.inventory_unreachable == audit.progression_unreachable == ()
    assert audit.unfilled == ("Unfilled",)


@pytest.mark.parametrize("break_cycle", [False, True])
def test_cross_player_cycle_and_valid_remote_unlock_chain(break_cycle: bool) -> None:
    multiworld = fixture_world(2)
    first = add_check(multiworld, "Player one locked", 1)
    first.access_rule = lambda state: state.has("First permission", 1)
    place(multiworld, first, "Second permission", 2)
    second = add_check(multiworld, "Player two locked", 2)
    second.access_rule = lambda state: state.has("Second permission", 2)
    place(multiworld, second, "First permission", 1)
    if break_cycle:
        place(multiworld, add_check(multiworld, "Independent remote unlock", 2), "First permission", 1)
    for player, target in ((1, first), (2, second)):
        audit = audit_local_checks(multiworld, player)
        assert audit.inventory_unreachable == ()
        assert audit.progression_unreachable == (() if break_cycle else (target.name,))


def test_excluded_physical_check_is_still_a_check_but_addressless_event_is_not() -> None:
    from BaseClasses import LocationProgressType

    multiworld = fixture_world()
    excluded = add_check(multiworld, "Excluded physical check")
    excluded.progress_type = LocationProgressType.EXCLUDED
    excluded.access_rule = lambda state: False
    place(multiworld, excluded, "Filler", classification=ItemClassification.filler)
    event = Location(1, "Unreachable event", None, multiworld.get_region("Menu", 1))
    event.access_rule = lambda state: False
    multiworld.get_region("Menu", 1).locations.append(event)
    audit = audit_local_checks(multiworld, 1)
    assert audit.inventory_unreachable == audit.progression_unreachable == (excluded.name,)
    assert audit.unfilled == ()


def test_production_validator_catches_cycle_without_state_mutation() -> None:
    from ..check_accessibility import KirbyAmCheckAccessibilityError, validate_all_checks

    multiworld = fixture_world(2)
    for player, other in ((1, 2), (2, 1)):
        target = add_check(multiworld, f"Locked {player}", player)

        def rule(state: CollectionState, player: int = player) -> bool:
            return state.has("Permission", player)
        target.access_rule = rule
        place(multiworld, target, "Permission", other)
    before = multiworld.state.copy()
    with pytest.raises(KirbyAmCheckAccessibilityError, match="unreachable from placed progression") as error:
        validate_all_checks(multiworld, multiworld.player_ids)
    assert "Locked 1" in str(error.value) and "Locked 2" in str(error.value)
    assert "unavailable even with all inventory=[]" in str(error.value)
    assert multiworld.state.prog_items == before.prog_items
    assert multiworld.state.locations_checked == before.locations_checked
    assert all(world.options.accessibility.current_key == "minimal" for world in multiworld.worlds.values())


def test_production_validator_ignores_non_target_player_checks() -> None:
    from ..check_accessibility import validate_all_checks

    multiworld = fixture_world(2)
    target = add_check(multiworld, "Target")
    target.access_rule = lambda state: state.has("Permission", 1)
    place(multiworld, target, "Filler", classification=ItemClassification.filler)
    place(multiworld, add_check(multiworld, "Remote source", 2), "Permission", 1)
    unrelated = add_check(multiworld, "Remote closed check", 2)
    unrelated.access_rule = lambda state: False
    place(multiworld, unrelated, "Filler", 2, ItemClassification.filler)
    validate_all_checks(multiworld, (1,))


def test_successful_production_audit_never_constructs_all_inventory(monkeypatch: pytest.MonkeyPatch) -> None:
    from ..check_accessibility import validate_all_checks

    multiworld = fixture_world()
    place(multiworld, add_check(multiworld, "Open check"), "Filler", classification=ItemClassification.filler)
    monkeypatch.setattr(multiworld, "get_all_state", lambda: pytest.fail("Success needs only the actual fill sweep"))
    validate_all_checks(multiworld, (1,))
