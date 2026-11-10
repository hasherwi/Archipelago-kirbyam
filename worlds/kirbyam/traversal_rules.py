"""Install reviewed fuse, rope, block and switch witnesses from the shared room catalog."""

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
            + room_traversal_targets("block") + room_traversal_targets("switch"))


def target_graphs(row: dict[str, Any], area_keys: bool) -> tuple[TraversalGraph, ...]:
    return tuple(room_traversal_graph(row["id"], witness, area_keys) for witness in row["graphs"])


def graph_succeeds(graph: TraversalGraph, policy: SourcePolicy, owned: frozenset[str], gating: bool,
                   *, retries: bool) -> bool:
    result = graph.evaluate(policy, owned, gating, allow_documented_retries=retries)
    return bool(graph.required_targets) and all(result.reaches(target) for target in graph.required_targets)


def target_applies(row: dict[str, Any], policy: SourcePolicy) -> bool:
    """Scope partial witnesses without rejecting unsupported source policies."""
    condition = row.get("requires_guaranteed_source")
    alternatives = row.get("requires_any_guaranteed_source")
    if condition is None and alternatives is None:
        return True
    conditions = alternatives if alternatives is not None else (condition,)
    return any(
        len(grant := policy.grant(entry["source_key"], lambda _: True).guaranteed) == 1
        and grant <= frozenset(entry.get("abilities", (entry.get("ability"),)))
        for entry in conditions
    )


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


def cabbage_missile_is_progression(world: Any) -> bool:
    """Only the enabled, guaranteed-Doo chest rule needs a Missile permission."""
    raw = getattr(world, "_enemy_copy_ability_policy", None)
    if not isinstance(raw, dict) or not world._ability_gating_enabled():
        return False
    try:
        world.multiworld.get_location(data.locations["MINOR_CHEST_SPRAY_PAINT_12"].label, world.player)
    except KeyError:
        return False
    return SourcePolicy(raw).grant("WADDLE_DOO", lambda _: True).guaranteed == frozenset({"Missile"})


def cabbage_parasol_is_progression(world: Any) -> bool:
    """Only the enabled, guaranteed-Doo chest rule needs a Parasol permission."""
    raw = getattr(world, "_enemy_copy_ability_policy", None)
    if not isinstance(raw, dict) or not world._ability_gating_enabled():
        return False
    try:
        world.multiworld.get_location(data.locations["MINOR_CHEST_SPRAY_PAINT_12"].label, world.player)
    except KeyError:
        return False
    return SourcePolicy(raw).grant("WADDLE_DOO", lambda _: True).guaranteed == frozenset({"Parasol"})


def rainbow_spark_is_progression(world: Any) -> bool:
    """Room8 and optional Green Paint share the guaranteed Sparky permission.

    Room8 remains enabled when minor chests are disabled, so Green Paint adds
    no new promotion condition. Inventory is still permission, not equipment.
    """
    raw = getattr(world, "_enemy_copy_ability_policy", None)
    return (isinstance(raw, dict) and world._ability_gating_enabled()
            and SourcePolicy(raw).grant("SPARKY", lambda _: True).guaranteed == frozenset({"Spark"}))


def mustard_crash_is_progression(world: Any) -> bool:
    """Promote only enforced guaranteed Crash routes; inventory is permission."""
    raw = getattr(world, "_enemy_copy_ability_policy", None)
    if not isinstance(raw, dict) or not world._ability_gating_enabled():
        return False
    policy = SourcePolicy(raw)
    if any(policy.grant(source, lambda _: True).guaranteed == frozenset({"Crash"})
           for source in ("FOLEY", "HOT_HEAD")):
        return True
    if policy.grant("TWISTER", lambda _: True).guaranteed != frozenset({"Crash"}):
        return False
    try:
        world.multiworld.get_location(data.locations["MAJOR_CHEST_MUSTARD_MOUNTAIN"].label, world.player)
    except KeyError:
        return False
    return True


def carrot_fighter_is_progression(world: Any) -> bool:
    """Only the enforced lower Room13 Fighter source needs this permission."""
    raw = getattr(world, "_enemy_copy_ability_policy", None)
    return (isinstance(raw, dict) and world._ability_gating_enabled()
            and SourcePolicy(raw).grant("WADDLE_DOO", lambda _: True).guaranteed == frozenset({"Fighter"}))


def mustard_magic_is_progression(world: Any) -> bool:
    """Only the enabled Room16 exit and guaranteed Foley need Magic permission."""
    raw = getattr(world, "_enemy_copy_ability_policy", None)
    if not isinstance(raw, dict) or not world._ability_gating_enabled():
        return False
    try:
        world.multiworld.get_entrance(
            "REGION_MUSTARD_MOUNTAIN/ROOM_4_15 -> REGION_MUSTARD_MOUNTAIN/ROOM_4_16", world.player)
    except KeyError:
        return False
    return SourcePolicy(raw).grant("FOLEY", lambda _: True).guaranteed == frozenset({"Magic"})


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
        # Existing surfaces keep their prior fallback, but a newly introduced
        # optional connection must never become free when source data is absent.
        for row in extra_traversal_targets():
            if row.get("new_connection"):
                target = world.multiworld.get_entrance(f"{row['region']} -> {row['exit']}", world.player)
                add_rule(target, lambda state: False)
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
