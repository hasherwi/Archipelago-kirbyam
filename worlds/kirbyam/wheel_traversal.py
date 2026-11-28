"""Rainbow108 closing-chain route with local and item-gated statue sources.

The carry detour uses a fresh, unoccupied108 reset. This is an explicit
single-player opportunity assumption, not every door transition or a bounded
AI-vacancy guarantee. Native level.c318-358 rebuilds collision only for a fresh
slot. The race itself has a Wheel emulator witness from110 arrival34,19.
"""
from __future__ import annotations

from functools import cache
from typing import Any

from .special_route_data import SPECIAL_ROUTE_PROFILES

from .traversal import SourcePolicy, TraversalGraph
from .traversal_data import (
    HUB_SWITCH_LABELS as HUB_SWITCH_LABELS,
    compile_room_graph,
    graph_access_regions, graph_items, has_graph_access, requires_all_traversal_witnesses,
    room_traversal_graph, room_traversal_targets,
)

RACE = room_traversal_targets("wheel")[0]
RACE_ENTRANCE = f"{RACE['region']} -> {RACE['exit']}"


def wheel_graph(statue_room: bool) -> TraversalGraph:
    return room_traversal_graph(RACE["id"], "statues" if statue_room else "local")


LOCAL_SOURCE_REGION = str(wheel_graph(False).access_region)
COPY_ROOM_REGION = str(wheel_graph(True).access_region)
CENTRAL_REGION = "REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE"
assert len(HUB_SWITCH_LABELS) == 15


def static_wheel_witness(policy: SourcePolicy) -> bool:
    return any(
        graph.evaluate(policy, graph_items(graph), False)
        .reaches("chest")
        for graph in (room_traversal_graph(RACE["id"], witness) for witness in RACE["graphs"])
    )


@cache
def missile_graph() -> TraversalGraph:
    """The independent, stock Bang-Bang carry and named Advanced exception."""
    profile = SPECIAL_ROUTE_PROFILES["rainbow_wheel_race_missile"]
    return compile_room_graph(profile["witness"], {}, advanced=True, require_inventory=True)


def missile_allowed(world: Any, policy: SourcePolicy) -> bool:
    from .traversal_rules import advanced_traversal_enabled

    profile = SPECIAL_ROUTE_PROFILES["rainbow_wheel_race_missile"]
    return (advanced_traversal_enabled(world) and policy.mode == profile["mode"]
            and world._area_keys_enabled() is profile["area_keys"]
            and world._ability_gating_enabled() is profile["ability_gating"])


def install_wheel_rules(world: Any) -> None:
    from worlds.generic.Rules import add_rule
    from .enemy_ability_data import GATEABLE_ENEMY_COPY_ABILITIES

    raw = getattr(world, "_enemy_copy_ability_policy", None)
    if not isinstance(raw, dict):
        return
    policy = SourcePolicy.for_world(world, raw)
    graphs = tuple(room_traversal_graph(RACE["id"], witness, world._area_keys_enabled()) for witness in RACE["graphs"])
    if missile_allowed(world, policy):
        graphs += (missile_graph(),)
    gating = world._ability_gating_enabled()
    all_items = frozenset(f"{name} Ability" for name in GATEABLE_ENEMY_COPY_ABILITIES)
    all_items |= frozenset(item for graph in graphs for item in graph_items(graph))
    if requires_all_traversal_witnesses(world) and not any(
        graph.required_targets <= {p.node for p in graph.evaluate(
            policy, all_items, gating, allow_documented_retries=True).positions}
        for graph in graphs
    ):
        raise ValueError(
            "No reviewed Wheel source witness for these options; "
            "unreviewed alternatives are not declared impossible. Try another seed."
        )

    def rule(state: Any) -> bool:
        owned = frozenset(f"{name} Ability" for name in GATEABLE_ENEMY_COPY_ABILITIES
                          if state.has(f"{name} Ability", world.player))
        for graph in graphs:
            if not has_graph_access(world, state, graph):
                continue
            items = owned | frozenset(item for item in graph_items(graph)
                                      if state.has(item, world.player))
            result = graph.evaluate(policy, items, gating, allow_documented_retries=True)
            if all(result.reaches(target) for target in graph.required_targets):
                return True
        return False

    entrance = world.multiworld.get_entrance(RACE_ENTRANCE, world.player)
    add_rule(entrance, rule)
    for name in {name for graph in graphs for name in graph_access_regions(graph)}:
        world.multiworld.register_indirect_condition(world.multiworld.get_region(name, world.player), entrance)
