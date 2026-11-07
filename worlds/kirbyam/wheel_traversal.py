"""Rainbow108 closing-chain route with local and all-switch statue sources.

The carry detour uses a fresh, unoccupied108 reset. This is an explicit
single-player opportunity assumption, not every door transition or a bounded
AI-vacancy guarantee. Native level.c318-358 rebuilds collision only for a fresh
slot. The race itself has a Wheel emulator witness from110 arrival34,19.
"""
from __future__ import annotations

from typing import Any

from .traversal import SourcePolicy, TraversalGraph
from .traversal_data import (
    HUB_SWITCH_LABELS as HUB_SWITCH_LABELS,
    graph_access_regions, has_graph_access, room_traversal_graph, room_traversal_targets,
)

RACE = room_traversal_targets("wheel")[0]
RACE_ENTRANCE = f"{RACE['region']} -> {RACE['exit']}"


def wheel_graph(statue_room: bool) -> TraversalGraph:
    return room_traversal_graph(RACE["id"], "statues" if statue_room else "local")


LOCAL_SOURCE_REGION = str(wheel_graph(False).access_region)
CENTRAL_REGION = str(wheel_graph(True).access_region)
assert len(HUB_SWITCH_LABELS) == 15


def static_wheel_witness(policy: SourcePolicy) -> bool:
    return any(
        graph.evaluate(policy, frozenset(item for route in graph.routes for item in route.items), False)
        .reaches("chest")
        for graph in (room_traversal_graph(RACE["id"], witness) for witness in RACE["graphs"])
    )


def install_wheel_rules(world: Any) -> None:
    from worlds.generic.Rules import add_rule
    from .enemy_ability_data import GATEABLE_ENEMY_COPY_ABILITIES

    raw = getattr(world, "_enemy_copy_ability_policy", None)
    if not isinstance(raw, dict):
        return
    policy = SourcePolicy(raw, bool(world.options.ability_randomization_statues.value))
    graphs = tuple(room_traversal_graph(RACE["id"], witness, world._area_keys_enabled()) for witness in RACE["graphs"])
    gating = world._ability_gating_enabled()
    all_items = frozenset(f"{name} Ability" for name in GATEABLE_ENEMY_COPY_ABILITIES)
    all_items |= frozenset(item for graph in graphs for route in graph.routes for item in route.items)
    if not any(graph.evaluate(policy, all_items, gating, allow_documented_retries=True).reaches("chest")
               for graph in graphs):
        raise ValueError(
            "No reviewed non-970 Wheel source witness for these options. "
            "Room 970 is unavailable until patched-ROM access is independently verified."
        )

    def rule(state: Any) -> bool:
        owned = frozenset(f"{name} Ability" for name in GATEABLE_ENEMY_COPY_ABILITIES
                          if state.has(f"{name} Ability", world.player))
        for graph in graphs:
            if not has_graph_access(world, state, graph):
                continue
            items = owned | frozenset(item for route in graph.routes for item in route.items
                                      if state.has(item, world.player))
            if graph.evaluate(policy, items, gating, allow_documented_retries=True).reaches("chest"):
                return True
        return False

    entrance = world.multiworld.get_entrance(RACE_ENTRANCE, world.player)
    add_rule(entrance, rule)
    for name in {name for graph in graphs for name in graph_access_regions(graph)}:
        world.multiworld.register_indirect_condition(world.multiworld.get_region(name, world.player), entrance)
