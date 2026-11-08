"""Install reviewed fuse, rope and block witnesses from the shared room catalog."""

from __future__ import annotations

from typing import Any

from .data import data
from .enemy_ability_data import GATEABLE_ENEMY_COPY_ABILITIES
from .traversal import SourcePolicy, TraversalGraph
from .traversal_data import (
    graph_access_regions, graph_items, has_graph_access, requires_all_traversal_witnesses,
    room_traversal_graph, room_traversal_targets,
)


def extra_traversal_targets() -> tuple[dict[str, Any], ...]:
    return (room_traversal_targets("fuse") + room_traversal_targets("rope")
            + room_traversal_targets("block") + room_traversal_targets("reinforced"))


def target_graphs(row: dict[str, Any], area_keys: bool) -> tuple[TraversalGraph, ...]:
    return tuple(room_traversal_graph(row["id"], witness, area_keys) for witness in row["graphs"])


def graph_succeeds(graph: TraversalGraph, policy: SourcePolicy, owned: frozenset[str], gating: bool,
                   *, retries: bool) -> bool:
    result = graph.evaluate(policy, owned, gating, allow_documented_retries=retries)
    return bool(graph.required_targets) and all(result.reaches(target) for target in graph.required_targets)


def target_applies(row: dict[str, Any], policy: SourcePolicy) -> bool:
    """Scope partial witnesses without rejecting unsupported source policies."""
    condition = row.get("requires_guaranteed_source")
    return condition is None or policy.grant(
        condition["source_key"], lambda _: True,
    ).guaranteed == frozenset({condition["ability"]})


def goal2_ice_is_progression(world: Any) -> bool:
    """Only the enabled, guaranteed-Frosty chest rule needs an Ice permission."""
    raw = getattr(world, "_enemy_copy_ability_policy", None)
    if not isinstance(raw, dict) or not world._ability_gating_enabled():
        return False
    try:
        world.multiworld.get_location(data.locations["MINOR_CHEST_MUSIC_NOTE_10"].label, world.player)
    except KeyError:
        return False
    return SourcePolicy(raw).grant("MR_FROSTY", lambda _: True).guaranteed == frozenset({"Ice"})


def static_extra_witness(policy: SourcePolicy) -> bool:
    """Check the same assignment as the ROM, without assuming source access.

    This is a source-feasibility filter, not a fill/reachability proof. Optional
    alternative routes can remain closed when their reviewed sources cannot
    supply the capability; they must document the independent ordinary bypass.
    """
    return all(
        not target_applies(row, policy) or not row.get("required_for_generation", True)
        or any(graph_succeeds(graph, policy, graph_items(graph), False, retries=False)
               for graph in target_graphs(row, False))
        for row in extra_traversal_targets()
    )


def install_extra_traversal_rules(world: Any) -> None:
    from worlds.generic.Rules import add_rule

    raw = getattr(world, "_enemy_copy_ability_policy", None)
    if not isinstance(raw, dict):
        return
    policy = SourcePolicy(raw, bool(world.options.ability_randomization_statues.value))
    gating = world._ability_gating_enabled()
    for row in extra_traversal_targets():
        if not target_applies(row, policy):
            continue
        if row.get("exit"):
            target = world.multiworld.get_entrance(f"{row['region']} -> {row['exit']}", world.player)
        else:
            try:
                target = world.multiworld.get_location(data.locations[row["location"]].label, world.player)
            except KeyError:
                continue  # This optional location category is disabled.
        graphs = target_graphs(row, world._area_keys_enabled())
        required_items = frozenset(f"{name} Ability" for name in GATEABLE_ENEMY_COPY_ABILITIES)
        required_items |= frozenset(item for graph in graphs for item in graph_items(graph))
        if requires_all_traversal_witnesses(world) and row.get("required_for_generation", True) and not any(
            graph_succeeds(graph, policy, required_items, gating, retries=True) for graph in graphs
        ):
            raise ValueError(
                f"No reviewed source witness for {row['id']} in mode {policy.mode}; "
                "unreviewed alternatives are not declared impossible. Try another seed."
            )

        def rule(state: Any, graphs: tuple[TraversalGraph, ...] = graphs,
                 required_items: frozenset[str] = required_items) -> bool:
            owned = frozenset(item for item in required_items if state.has(item, world.player))
            return any(
                has_graph_access(world, state, graph)
                and graph_succeeds(graph, policy, owned, gating, retries=True)
                for graph in graphs
            )

        add_rule(target, rule)
        if row.get("exit"):
            for name in {name for graph in graphs for name in graph_access_regions(graph)}:
                world.multiworld.register_indirect_condition(world.multiworld.get_region(name, world.player), target)
