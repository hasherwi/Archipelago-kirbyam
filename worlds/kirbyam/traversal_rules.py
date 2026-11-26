"""Install reviewed action witnesses from the shared room catalog."""

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
            + room_traversal_targets("block") + room_traversal_targets("switch")
            + room_traversal_targets("reinforced") + room_traversal_targets("metal"))


def advanced_traversal_enabled(world: Any) -> bool:
    """Missing settings in old fixtures/slots retain the safe standard baseline."""
    option = getattr(getattr(world, "options", None), "advanced_logic", None)
    return getattr(option, "value", 0) == 1


def target_graphs(row: dict[str, Any], area_keys: bool, *, advanced: bool = False) -> tuple[TraversalGraph, ...]:
    return tuple(room_traversal_graph(row["id"], witness, area_keys)
                 for witness in row["graphs"]
                 if advanced or witness not in row.get("advanced_graphs", ()))


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
    if alternatives is not None:
        conditions = alternatives
    else:
        assert condition is not None
        conditions = (condition,)
    return any(
        len(grant := policy.grant(entry["source_key"], lambda _: True).guaranteed) == 1
        and grant <= frozenset(entry.get("abilities", (entry.get("ability"),)))
        for entry in conditions
    )


def goal2_ice_is_progression(world: Any) -> bool:
    """Classify the enabled physical chest before region creation or precollection."""
    return (world._ability_gating_enabled()
            and bool(getattr(world, "ENABLE_MINOR_CHESTS", False))
            and data.locations["MINOR_CHEST_MUSIC_NOTE_10"].source_rom_offset is not None)


def candy912_source_is_progression(world: Any, ability: str) -> bool:
    """Promote a gated permission only when this chest uses its proven local source."""
    if (ability not in {"Spark", "Missile"} or not world._ability_gating_enabled()
            or not bool(getattr(world, "ENABLE_MINOR_CHESTS", False))
            or data.locations["MINOR_CHEST_CANDY_CONSTELLATION_9_12"].source_rom_offset is None):
        return False
    raw = getattr(world, "_enemy_copy_ability_policy", None)
    return (isinstance(raw, dict)
            and SourcePolicy(raw).grant("WADDLE_DOO", lambda _: True).guaranteed == frozenset({ability}))


def cabbage_source_is_progression(world: Any, ability: str) -> bool:
    """Use the enforced Chocolate graph's actual enemy and statue assignments."""
    raw = getattr(world, "_enemy_copy_ability_policy", None)
    if not isinstance(raw, dict) or not world._ability_gating_enabled():
        return False
    if (not bool(getattr(world, "ENABLE_MINOR_CHESTS", False))
            or data.locations["MINOR_CHEST_SPRAY_PAINT_12"].source_rom_offset is None):
        return False
    statue_option = getattr(getattr(world, "options", None), "ability_randomization_statues", None)
    policy = SourcePolicy(raw, bool(getattr(statue_option, "value", 0)))
    row = next(row for row in room_traversal_targets("block") if row["id"] == "bomb_517_chocolate")
    if not target_applies(row, policy):
        return False
    graphs = [room_traversal_graph("bomb_517_chocolate", name)
              for name in ("hub2_entry", "hub2_statues_entry")]
    for graph in graphs:
        rooms = {node.key: node.room for node in graph.nodes}
        for source in graph.placements:
            grant = policy.grant(source.source_key, lambda _: True, native_room=rooms[source.node])
            if ability in grant.guaranteed or (
                    source.renewable and source.retry_evidence and grant.randomized and ability in grant.abilities):
                return True
    return False


def cabbage_missile_is_progression(world: Any) -> bool:
    return cabbage_source_is_progression(world, "Missile")


def cabbage_parasol_is_progression(world: Any) -> bool:
    return cabbage_source_is_progression(world, "Parasol")


def cabbage_element_is_progression(world: Any, ability: str) -> bool:
    return ability in {"Spark", "Ice"} and cabbage_source_is_progression(world, ability)


def mustard_crash_is_progression(world: Any) -> bool:
    """Promote only enforced guaranteed Crash routes; inventory is permission."""
    if not advanced_traversal_enabled(world):
        return False
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
    """Only Advanced Logic with a guaranteed Foley needs Magic permission."""
    if not advanced_traversal_enabled(world):
        return False
    raw = getattr(world, "_enemy_copy_ability_policy", None)
    if not isinstance(raw, dict) or not world._ability_gating_enabled():
        return False
    try:
        world.multiworld.get_entrance(
            "REGION_MUSTARD_MOUNTAIN/ROOM_4_15 -> REGION_MUSTARD_MOUNTAIN/ROOM_4_16", world.player)
    except KeyError:
        return False
    return SourcePolicy(raw).grant("FOLEY", lambda _: True).guaranteed == frozenset({"Magic"})


def mustard_ice_is_progression(world: Any) -> bool:
    """Guaranteed Foley Ice needs permission in both normal and Advanced Logic."""
    raw = getattr(world, "_enemy_copy_ability_policy", None)
    if not isinstance(raw, dict) or not world._ability_gating_enabled():
        return False
    try:
        world.multiworld.get_entrance(
            "REGION_MUSTARD_MOUNTAIN/ROOM_4_15 -> REGION_MUSTARD_MOUNTAIN/ROOM_4_16", world.player)
    except KeyError:
        return False
    return SourcePolicy(raw).grant("FOLEY", lambda _: True).guaranteed == frozenset({"Ice"})


def static_room16_witness(policy: SourcePolicy, *, advanced: bool = False) -> bool:
    """Check source feasibility for the RoomSanity visit, not world reachability."""
    from . import room16_timer
    if room16_timer.enabled(policy):
        return graph_succeeds(room16_timer.graph(), policy, frozenset(), False, retries=False)
    row = next(row for row in room_traversal_targets("switch") if row["id"] == "switch_533_room16")
    return target_applies(row, policy) and any(
        graph_succeeds(graph, policy, graph_items(graph), False, retries=False)
        for graph in target_graphs(row, False, advanced=advanced)
    )


def static_extra_witness(policy: SourcePolicy, *, advanced: bool = False) -> bool:
    """Check the same assignment as the ROM, without assuming source access.

    This is a source-feasibility filter, not a fill/reachability proof. Optional
    alternative routes can remain closed when their reviewed sources cannot
    supply the capability; they must document the independent ordinary bypass.
    """
    return all(
        not target_applies(row, policy) or not row.get("required_for_generation", True)
        or any(graph_succeeds(graph, policy, graph_items(graph), False, retries=False)
               for graph in target_graphs(row, False, advanced=advanced))
        for row in extra_traversal_targets()
    )


def install_extra_traversal_rules(world: Any) -> None:
    from worlds.generic.Rules import add_rule
    from . import candy912_fuse, yellow_cupid, room16_timer

    yellow_cupid.validate_profile(world, install=True)
    raw = getattr(world, "_enemy_copy_ability_policy", None)
    if not isinstance(raw, dict):
        # Preserve legacy fallbacks except for new optional connections and
        # existing exits explicitly migrated to fail-closed source-backed logic.
        for row in extra_traversal_targets():
            if (row.get("id"), row.get("location")) == (yellow_cupid.TARGET, yellow_cupid.LOCATION):
                # Missing policy data is not a source-independent solution.
                # Real unsupported policies retain their documented fallback.
                try:
                    yellow = world.multiworld.get_location(data.locations[row["location"]].label, world.player)
                except KeyError:
                    pass  # Minor chests are disabled.
                else:
                    add_rule(yellow, lambda state: False)
            if row.get("new_connection") or row.get("fail_closed"):
                target = world.multiworld.get_entrance(f"{row['region']} -> {row['exit']}", world.player)
                add_rule(target, lambda state: False)
        return
    policy = SourcePolicy(raw, bool(world.options.ability_randomization_statues.value))
    gating = world._ability_gating_enabled()
    for row in extra_traversal_targets():
        profile_graphs = (yellow_cupid.target_graphs(world, row) + room16_timer.target_graphs(row, policy)
                          + candy912_fuse.target_graphs(row, getattr(world, "_candy912_linked_west_fuse", False), policy))
        applies = target_applies(row, policy)
        if not applies and not profile_graphs:
            if row.get("fail_closed"):
                target = world.multiworld.get_entrance(f"{row['region']} -> {row['exit']}", world.player)
                add_rule(target, lambda state: False)
            continue
        if row.get("exit"):
            target = world.multiworld.get_entrance(f"{row['region']} -> {row['exit']}", world.player)
        else:
            try:
                target = world.multiworld.get_location(data.locations[row["location"]].label, world.player)
            except KeyError:
                continue  # This optional location category is disabled.
        graphs = ((target_graphs(row, world._area_keys_enabled(), advanced=advanced_traversal_enabled(world))
                   if applies else ()) + profile_graphs)
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
