"""Native Hub endpoints gate traversal independently of physical switch checks."""
import json
from pathlib import Path

import pytest

from BaseClasses import CollectionState, MultiWorld
from test.general import setup_multiworld
from .. import KirbyAmWorld
from ..data import data
from ..area_keys import AREA_KEY_LABELS
from .test_rules import _make_collection_state_room_graph

EVIDENCE = json.loads((Path(__file__).parent / 'data/hub_native_edges.json').read_text())
CENTRAL = 'REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE'


def _with_area_keys(world: MultiWorld, state: CollectionState) -> CollectionState:
    # Isolate native Hub shortcut and compartment predicates from destination keys.
    for label in AREA_KEY_LABELS:
        state.collect(world.worlds[1].create_item(label), True)
    return state


@pytest.mark.parametrize('edge', EVIDENCE)
def test_each_native_edge_requires_its_own_item(edge):
    world, state = _make_collection_state_room_graph()
    _with_area_keys(world, state)
    source, destination = edge['source_keys'][0], edge['destination_keys'][0]
    if edge['room'] == 801 and edge['destination'] in (590, 490):
        source += '_UPPER_PLATFORMS'
    if edge['room'] == 590 and edge['destination'] == 801:
        destination += '_UPPER_PLATFORMS'
    entrance = world.get_entrance(f'{source} -> {destination}', 1)
    assert not entrance.access_rule(state)
    label = data.items[edge['item']].label
    state.add_item(label, 1)
    assert entrance.access_rule(state)
    state.remove_item(label, 1)
    assert not entrance.access_rule(state)


@pytest.mark.parametrize('room_sanity', [0, 1])
def test_hub_receipt_shortcuts_and_eight_distinct_shards(room_sanity):
    world = setup_multiworld(KirbyAmWorld, seed=932, options={
        'room_sanity': room_sanity, 'ability_gating': 0})
    trial = _with_area_keys(world, CollectionState(world))
    # Receipt milestones describe shortcuts, not global room-access phases.
    # Physical Moonlight is ID 402; ID 401 is the Rainbow East central shortcut.
    for item_id, label, destination in (
        (3860401, 'Rainbow Route East - Hub Connection',
         'REGION_RAINBOW_ROUTE/ROOM_1_HUB_1'),
        (3860402, 'Moonlight Mansion - Hub Connection',
         'REGION_MOONLIGHT_MANSION/ROOM_2_HUB'),
    ):
        assert data.items[item_id].label == label
        entrance = world.get_entrance(f'{CENTRAL} -> {destination}', 1)
        assert not entrance.access_rule(trial)
        received = trial.copy()
        received.collect(world.worlds[1].create_item(label), True)
        assert entrance.access_rule(received)
    dimension = world.get_entrance('REGION_RAINBOW_ROUTE/MAIN -> REGION_DIMENSION_MIRROR/MAIN', 1)
    shards = [item for item in world.itempool if 'Mirror Shard' in item.name]
    assert len(shards) == 8
    for item in shards[:-1]:
        trial.collect(item, True)
    trial.collect(shards[0], True)  # duplicates cannot substitute for the eighth
    assert not dimension.access_rule(trial)
    trial.collect(shards[-1], True)
    assert dimension.access_rule(trial)


@pytest.mark.parametrize('room_sanity', [0, 1])
@pytest.mark.parametrize('ability_gating', [0, 1])
def test_moonlight_arrival_cannot_cross_olive_lever_wall(room_sanity, ability_gating):
    world = setup_multiworld(KirbyAmWorld, seed=932, options={
        'room_sanity': room_sanity, 'ability_gating': ability_gating})
    # Isolate the downstream arrival proved by the 743 lever departure. The
    # new 708 source gate is tested separately; adding hub-source items here
    # could open an unrelated Olive route and invalidate this negative test.
    menu = world.get_region('Menu', 1)
    menu.exits.clear()
    menu.connect(world.get_region('REGION_MOONLIGHT_MANSION/ROOM_2_12_LEFT', 1),
                 'Begin Olive entry fixture at native180')
    state = _with_area_keys(world, CollectionState(world))
    for name in ('Moonlight Mansion - Hub Connection',
                 'Moonlight Mansion 2-11 - Lever Wall',
                 'Olive Ocean - Hub Connection'):
        state.collect(world.worlds[1].create_item(name), True)
    state.sweep_for_advancements()

    olive = 'REGION_OLIVE_OCEAN/ROOM_6_13'
    entry = world.get_region(olive + '__LOGIC__ENTRY_FROM_MOONLIGHT', 1)
    assert entry.can_reach(state)
    assert not world.get_region(olive, 1).can_reach(state)
    assert not world.get_region('REGION_OLIVE_OCEAN/ROOM_6_12', 1).can_reach(state)
    assert not world.get_region('REGION_OLIVE_OCEAN/ROOM_6_HUB', 1).can_reach(state)
    assert not world.get_region('REGION_CABBAGE_CAVERN/ROOM_3_HUB_1', 1).can_reach(state)
    assert not world.get_location(data.locations['LEVER_OLIVE_OCEAN_6_13'].label, 1).can_reach(state)
    # Entering the physical room does set its one RoomSanity bit. The shared
    # check must remain a sink, not an escape into the other compartment.
    check = world.get_region(olive + '__ROOM_CHECK', 1)
    assert check.can_reach(state)
    assert not data.regions[check.name].exits
    assert all(exit.connected_region.name == 'REGION_OLIVE_OCEAN/MAIN' for exit in check.exits)
    assert len(check.locations) == room_sanity
    assert world.get_region('REGION_MOONLIGHT_MANSION/ROOM_2_12_RIGHT', 1).can_reach(state)

    state.collect(world.worlds[1].create_item('Olive Ocean 6-13 - Lever Wall'), True)
    state.sweep_for_advancements()
    assert world.get_region(olive, 1).can_reach(state)
    # Room 13 enters native 814 at (40, 40), above nondroppable 0x0F floors.
    # Opening the Room 13 lever grants this upper-left compartment, not the
    # lower Room 12 corridors (see block-hit-acceptance.json and traversal docs).
    room12 = 'REGION_OLIVE_OCEAN/ROOM_6_12'
    upper_left = world.get_region(room12 + '__LOGIC__UPPER_LEFT', 1)
    assert upper_left.can_reach(state)
    assert not world.get_region(room12, 1).can_reach(state)
    room12_check = world.get_region(room12 + '__ROOM_CHECK', 1)
    assert room12_check.can_reach(state)
    assert not data.regions[room12_check.name].exits
    assert all(exit.connected_region.name == 'REGION_OLIVE_OCEAN/MAIN' for exit in room12_check.exits)
    assert len(room12_check.locations) == room_sanity
    # The former Room 12 -> 11 -> 10 -> Olive hub -> Cabbage hub escape also
    # requires the inaccessible lower compartment; the lever alone cannot grant it.
    assert not world.get_region('REGION_OLIVE_OCEAN/ROOM_6_HUB', 1).can_reach(state)
    assert not world.get_region('REGION_CABBAGE_CAVERN/ROOM_3_HUB_1', 1).can_reach(state)


@pytest.mark.parametrize('room_sanity', [0, 1])
@pytest.mark.parametrize('ability_gating', [0, 1])
def test_candy_overland_arrival_does_not_grant_its_central_connection(room_sanity, ability_gating):
    """Preserve the emulator-proven 705->409->427->404->407->401->407->490 route."""
    world = setup_multiworld(KirbyAmWorld, seed=932, options={
        'room_sanity': room_sanity, 'ability_gating': ability_gating})
    route = ('REGION_MOONLIGHT_MANSION/ROOM_2_WARP', *(
        f'REGION_CANDY_CONSTELLATION/ROOM_9_{suffix}'
        for suffix in ('04', '02', '01', '07', '06', '07', 'HUB')))
    # Isolate the accepted downstream topology at 705. Ability permissions do
    # not supply the actual 707 carrier, and adding source Hub items can open
    # unrelated routes into Candy instead of exercising this continuation.
    menu = world.get_region('Menu', 1)
    menu.exits.clear()
    menu.connect(world.get_region(route[0], 1), 'Begin Candy overland fixture at 705')
    state = _with_area_keys(world, CollectionState(world))
    state.sweep_for_advancements()
    for source, destination in zip(route, route[1:]):
        assert world.get_entrance(f'{source} -> {destination}', 1).can_reach(state)
    hub = route[-1]
    assert world.get_region(hub, 1).can_reach(state)
    assert not state.has('Candy Constellation - Hub Connection', 1)
    connection = world.get_entrance(f'{hub} -> {CENTRAL}', 1)
    assert not connection.access_rule(state)
    state.collect(world.worlds[1].create_item('Candy Constellation - Hub Connection'), True)
    assert connection.access_rule(state)
