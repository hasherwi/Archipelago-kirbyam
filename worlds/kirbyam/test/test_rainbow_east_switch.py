"""The Rainbow East shortcut's switch is in Moonlight, not at its endpoint."""
import pytest

from BaseClasses import CollectionState
from test.general import setup_multiworld
from .. import KirbyAmWorld
from ..data import data

SWITCH = 'Rainbow Route East - Big Switch'
SWITCH_ROOM = 'REGION_MOONLIGHT_MANSION/ROOM_2_09'
EAST_HUB = 'REGION_RAINBOW_ROUTE/ROOM_1_HUB_1'


@pytest.mark.parametrize('room_sanity', [0, 1])
@pytest.mark.parametrize('ability_gating', [0, 1])
def test_rainbow_east_endpoint_does_not_grant_physical_switch(room_sanity, ability_gating):
    world = setup_multiworld(KirbyAmWorld, seed=1017, options={
        'room_sanity': room_sanity, 'ability_gating': ability_gating,
        'area_keys': 1})
    state = CollectionState(world)
    for item in world.precollected_items[1]:
        if item.name.endswith(" - Area Key"):
            state.remove(item)
    # Isolate the area boundary from ability acquisition. Even the shortcut
    # itself cannot put the player at a switch in a different area.
    for item in world.itempool:
        if item.name.endswith(' Ability'):
            state.collect(item, True)
    state.collect(world.worlds[1].create_item('Rainbow Route East - Hub Connection'), True)
    state.sweep_for_advancements()
    assert world.get_region(EAST_HUB, 1).can_reach(state)
    assert not world.get_region(SWITCH_ROOM, 1).can_reach(state)
    assert not world.get_location(SWITCH, 1).can_reach(state)
    assert world.get_location(SWITCH, 1).parent_region.name == SWITCH_ROOM


def test_switch_transport_identity_is_unchanged():
    switch = data.locations['HUB_SWITCH_RAINBOW_ROUTE_EAST']
    assert (switch.location_id, switch.bit_index) == (3960411, 11)


@pytest.mark.parametrize('room_sanity', [0, 1])
@pytest.mark.parametrize('ability_gating', [0, 1])
@pytest.mark.parametrize('area_keys', [0, 1])
@pytest.mark.parametrize('moonlight_shortcut', [False, True])
def test_moonlight_routes_reach_the_switch_without_rainbow_shortcut(
        room_sanity, ability_gating, area_keys, moonlight_shortcut):
    world = setup_multiworld(KirbyAmWorld, seed=1017, options={
        'room_sanity': room_sanity, 'ability_gating': ability_gating,
        'area_keys': area_keys})
    state = CollectionState(world)
    for item in world.itempool:
        if item.name.endswith(' Ability'):
            state.collect(item, True)
    if area_keys:
        state.collect(world.worlds[1].create_item('Moonlight Mansion - Area Key'), True)
    if moonlight_shortcut:
        state.collect(world.worlds[1].create_item('Moonlight Mansion - Hub Connection'), True)
    state.sweep_for_advancements()
    assert not state.has('Rainbow Route East - Hub Connection', 1)
    assert world.get_region(SWITCH_ROOM, 1).can_reach(state)
    assert world.get_location(SWITCH, 1).can_reach(state)


def test_moonlight_key_is_not_a_substitute_for_reaching_switch_room():
    world = setup_multiworld(KirbyAmWorld, seed=1017, options={'ability_gating': 0})
    state = CollectionState(world)
    state.collect(world.worlds[1].create_item('Moonlight Mansion - Area Key'), True)
    # A missing route to the room must still block the check even with the key.
    for entrance in world.get_region(SWITCH_ROOM, 1).entrances:
        entrance.access_rule = lambda state: False
    state.sweep_for_advancements()
    assert world.get_region('REGION_MOONLIGHT_MANSION/ROOM_2_HUB', 1).can_reach(state)
    assert not world.get_location(SWITCH, 1).can_reach(state)


def test_switch_does_not_require_later_antechamber_or_boss():
    world = setup_multiworld(KirbyAmWorld, seed=1045, options={'ability_gating': 0})
    state = CollectionState(world)
    state.collect(world.worlds[1].create_item('Moonlight Mansion - Area Key'), True)
    for entrance in world.get_region('REGION_MOONLIGHT_MANSION/ROOM_2_10', 1).entrances:
        entrance.access_rule = lambda state: False
    state.sweep_for_advancements()
    assert world.get_region(SWITCH_ROOM, 1).can_reach(state)
    assert world.get_location(SWITCH, 1).can_reach(state)
    assert not world.get_region('REGION_MOONLIGHT_MANSION/ROOM_2_10', 1).can_reach(state)
    assert not world.get_region('REGION_MOONLIGHT_MANSION/ROOM_2_BOSS', 1).can_reach(state)
