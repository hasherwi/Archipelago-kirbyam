"""The adventure testing chamber is a gated sink, never a new room check."""
import pytest

from BaseClasses import CollectionState
from test.general import setup_multiworld
from .. import KirbyAmWorld
from ..data import data, LocationCategory

ITEM = "Copy Ability Room Access"
CENTRAL = "REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE"
ROOM = "REGION_COPY_ABILITY_ROOM/MAIN"


@pytest.mark.parametrize("room_sanity", [0, 1])
@pytest.mark.parametrize("ability_gating", [0, 1])
@pytest.mark.parametrize("area_keys", [0, 1])
def test_access_is_independent_of_other_unlocks(room_sanity, ability_gating, area_keys):
    multiworld = setup_multiworld(KirbyAmWorld, seed=1002, options={
        "room_sanity": room_sanity,
        "ability_gating": ability_gating,
        "area_keys": area_keys,
    })
    world = multiworld.worlds[1]
    room = multiworld.get_region(ROOM, 1)
    gate = multiworld.get_entrance(f"{CENTRAL} -> {ROOM}", 1)
    state = CollectionState(multiworld)
    assert not room.locations
    assert not gate.access_rule(state)
    assert not any(item.name == ITEM for item in multiworld.precollected_items[1])
    assert sum(item.name == ITEM for item in multiworld.itempool) == 1
    assert len(multiworld.itempool) == len(multiworld.get_unfilled_locations())

    # Owning every other item must not substitute for the access item.
    for item in multiworld.itempool:
        if item.name != ITEM:
            state.collect(item, True)
    assert not gate.access_rule(state)
    state.collect(world.create_item(ITEM), True)
    assert gate.access_rule(state)

    # Conversely access alone suffices, including legitimate precollection.
    multiworld.push_precollected(world.create_item(ITEM))
    starting = CollectionState(multiworld)
    assert gate.access_rule(starting)
    assert not starting.has("Fire Ability", 1)
    assert all(exit.connected_region.name == CENTRAL for exit in room.exits)


def test_no_additional_room_sanity_check():
    assert sum(location.category == LocationCategory.ROOM_SANITY
               for location in data.locations.values()) == 263
    assert data.items[3860500].label == ITEM
