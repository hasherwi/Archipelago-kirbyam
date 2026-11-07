"""Rainbow108 closing-chain route with local and all-switch statue sources.

The carry detour uses a fresh, unoccupied108 reset. This is an explicit
single-player opportunity assumption, not every door transition or a bounded
AI-vacancy guarantee. Native level.c318-358 rebuilds collision only for a fresh
slot. The race itself has a Wheel emulator witness from110 arrival34,19.
"""
from __future__ import annotations

from typing import Any

from .data import LocationCategory, data
from .traversal import Node, Placement, Position, Route, SourcePolicy, TraversalGraph

RACE_ENTRANCE = ("REGION_RAINBOW_ROUTE/ROOM_1_06_LOWER_MID -> "
                 "REGION_RAINBOW_ROUTE/ROOM_1_06_LOWER_CHEST")
LOCAL_SOURCE_REGION = "REGION_RAINBOW_ROUTE/ROOM_1_07"
CENTRAL_REGION = "REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE"
HUB_SWITCH_LABELS = tuple(row.label for row in data.locations.values()
                          if row.category == LocationCategory.HUB_SWITCH)
assert len(HUB_SWITCH_LABELS) == 15
RESET_ASSUMPTION = "A fresh unoccupied108 return from110 is possible; no unlimited forced AI vacancy assumed"
# All19 permanent statues are accessible by ordinary flight from970 entry15,6.
STATUE_OBJECTS = (
    "0x088D6054", "0x088D6150", "0x088D612C", "0x088D6108", "0x088D60E4",
    "0x088D60C0", "0x088D5EEC", "0x088D5EC8", "0x088D6078", "0x088D609C",
    "0x088D6030", "0x088D600C", "0x088D5FE8", "0x088D5FC4", "0x088D5FA0",
    "0x088D5F7C", "0x088D5F58", "0x088D5F34", "0x088D5F10",
)


def wheel_graph(statue_room: bool) -> TraversalGraph:
    prefix = (970, 801, 190) if statue_room else ()
    rooms = prefix + (140, 108, 110, 108)
    nodes = tuple(Node(f"step{index}", room) for index, room in enumerate(rooms))
    routes = tuple(Route(
        nodes[index].key, nodes[index + 1].key,
        items=(frozenset({"Rainbow Route East - Hub Connection"})
               if room == 801 else frozenset()),
        # Only the audited final return represents a fresh unoccupied instance.
        resets_room_instance=index == len(rooms) - 2,
    ) for index, room in enumerate(rooms[:-1]))
    target = Node("chest", 108)
    routes += (Route(nodes[-1].key, target.key, "wheel_race"),)
    if statue_room:
        sources = tuple(Placement(
            nodes[0].key, f"STATUE:{0x3538FC + index:06X}", identity=address,
            renewable=True,
            retry_evidence="Permanent970 statue retouch; eventual eligible Wheel draw assumed",
        ) for index, address in enumerate(STATUE_OBJECTS))
    else:
        sources = (Placement(nodes[0].key, "WHEELIE", identity="0x088B765C"),)
    return TraversalGraph(nodes + (target,), routes, sources,
                          (Position(nodes[0].key),), frozenset({target.key}))


def static_wheel_witness(policy: SourcePolicy) -> bool:
    if wheel_graph(False).evaluate(policy, frozenset(), False).reaches("chest"):
        return True
    return wheel_graph(True).evaluate(
        policy, frozenset({"Rainbow Route East - Hub Connection"}), False,
    ).reaches("chest")


def install_wheel_rules(world: Any) -> None:
    from worlds.generic.Rules import add_rule
    from .enemy_ability_data import GATEABLE_ENEMY_COPY_ABILITIES

    raw = getattr(world, "_enemy_copy_ability_policy", None)
    if not isinstance(raw, dict):
        return
    policy = SourcePolicy(raw, bool(world.options.ability_randomization_statues.value))
    local, statues = wheel_graph(False), wheel_graph(True)
    gating = world._ability_gating_enabled()
    switches = tuple(world.multiworld.get_location(name, world.player) for name in HUB_SWITCH_LABELS)

    def rule(state: Any) -> bool:
        owned = frozenset(f"{name} Ability" for name in GATEABLE_ENEMY_COPY_ABILITIES
                          if state.has(f"{name} Ability", world.player))
        if state.can_reach_region(LOCAL_SOURCE_REGION, world.player):
            if local.evaluate(policy, owned, gating).reaches("chest"):
                return True
        # Area-wide events and received Hub Connection items do not establish
        # the15 physical switch activations required by native WORLD slots1..15.
        if not state.can_reach_region(CENTRAL_REGION, world.player):
            return False
        if not all(location.can_reach(state) for location in switches):
            return False
        if state.has("Rainbow Route East - Hub Connection", world.player):
            owned |= {"Rainbow Route East - Hub Connection"}
        return statues.evaluate(policy, owned, gating, allow_documented_retries=True).reaches("chest")

    entrance = world.multiworld.get_entrance(RACE_ENTRANCE, world.player)
    add_rule(entrance, rule)
    dependencies = {world.multiworld.get_region(name, world.player)
                    for name in (LOCAL_SOURCE_REGION, CENTRAL_REGION)}
    dependencies.update(location.parent_region for location in switches)
    for region in dependencies:
        world.multiworld.register_indirect_condition(region, entrance)
