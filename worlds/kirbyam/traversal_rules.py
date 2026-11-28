"""Install reviewed action witnesses from the shared room catalog."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from .data import LocationCategory, data, load_json_data
from .enemy_ability_data import ABILITY_SOURCES, GATEABLE_ENEMY_COPY_ABILITIES
from .traversal import SourcePolicy, TraversalGraph
from .traversal_data import (
    _room_catalog, graph_access_regions, graph_items, has_graph_access, requires_all_traversal_witnesses,
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


@lru_cache(maxsize=1)
def _progression_permissions() -> tuple[dict[str, Any], dict[int, tuple[str, ...]]]:
    return _compile_progression_permissions(load_json_data("regions/rooms.json"),
                                            load_json_data("abilities.json"))


def _compile_progression_permissions(
    rooms: Any, abilities: Any,
) -> tuple[dict[str, Any], dict[int, tuple[str, ...]]]:
    if not isinstance(rooms, dict) or not isinstance(abilities, dict):
        raise ValueError("Invalid Kirby permission catalogs")
    routes: dict[str, Any] = {}
    for owner, room in rooms.items():
        if not isinstance(room, dict) or "permission_progression_routes" not in room:
            continue
        declarations = room["permission_progression_routes"]
        if owner not in data.regions or not isinstance(declarations, dict) or not declarations:
            raise ValueError(f"Invalid Kirby permission route owner: {owner!r}")
        for name, predicate in declarations.items():
            if not isinstance(name, str) or not name.strip() or name in routes:
                raise ValueError(f"Duplicate or invalid Kirby permission route: {name!r}")
            routes[name] = predicate
    sources = {source.key for source in ABILITY_SOURCES}
    targets = {row["id"]: row for row in _room_catalog()[0]}

    def validate(clause: Any, active: frozenset[str]) -> None:
        if clause == "advanced_logic":
            return
        if not isinstance(clause, dict) or len(clause) != 1:
            raise ValueError(f"Invalid Kirby permission predicate: {clause!r}")
        kind, value = next(iter(clause.items()))
        if kind in ("all_of", "any_of") and isinstance(value, list) and value:
            for child in value:
                validate(child, active)
            return
        if kind == "route" and isinstance(value, str) and value in routes and value not in active:
            validate(routes[value], active | {value})
            return
        if kind == "guaranteed_source" and isinstance(value, str) and value in sources:
            return
        if kind in ("check_exists", "physical_minor_check") and isinstance(value, str):
            loc = data.locations.get(value)
            if loc is not None and (kind == "check_exists" or loc.category == LocationCategory.MINOR_CHEST):
                return
        if kind == "entrance_exists" and isinstance(value, dict) and set(value) == {"from_region", "to_region"}:
            source, destination = value["from_region"], value["to_region"]
            region = data.regions.get(source) if isinstance(source, str) else None
            if region is not None and isinstance(destination, str) and destination in region.exits:
                return
        if kind == "reviewed_graph_sources" and isinstance(value, dict) and set(value) == {"target", "witnesses"}:
            target_id = value["target"]
            target = targets.get(target_id) if isinstance(target_id, str) else None
            witnesses = value["witnesses"]
            if target is not None and isinstance(witnesses, list) and witnesses and all(
                isinstance(name, str) and name in target["graphs"] for name in witnesses
            ):
                return
        raise ValueError(f"Invalid Kirby permission predicate: {clause!r}")

    for route, clause in routes.items():
        validate(clause, frozenset({route}))
    by_code: dict[int, tuple[str, ...]] = {}
    for ability, row in abilities.items():
        if not isinstance(row, dict) or "progression_permission" not in row:
            continue
        binding = row["progression_permission"]
        if not isinstance(binding, dict) or set(binding) != {"item", "routes"}:
            raise ValueError(f"Invalid Kirby permission promotion: {ability!r}")
        key, names = binding["item"], binding["routes"]
        code = data.item_key_to_id.get(key) if isinstance(key, str) else None
        if (code is None or code in by_code or "Abilities" not in data.items[code].tags
                or data.items[code].label != f"{ability} Ability"
                or not isinstance(names, list) or not names
                or any(not isinstance(name, str) or name not in routes for name in names)
                or len(set(names)) != len(names)):
            raise ValueError(f"Invalid Kirby permission promotion: {ability!r}")
        by_code[code] = tuple(names)
    return routes, by_code


def _permission_predicate(world: Any, ability: str, clause: Any, routes: dict[str, Any]) -> bool:
    if clause == "advanced_logic":
        return advanced_traversal_enabled(world)
    kind, value = next(iter(clause.items()))
    if kind in ("all_of", "any_of"):
        checks = (_permission_predicate(world, ability, child, routes) for child in value)
        return all(checks) if kind == "all_of" else any(checks)
    if kind == "route":
        return _permission_predicate(world, ability, routes[value], routes)
    if kind == "physical_minor_check":
        return bool(getattr(world, "ENABLE_MINOR_CHESTS", False)) and data.locations[value].source_rom_offset is not None
    if kind in ("check_exists", "entrance_exists"):
        try:
            if kind == "check_exists":
                world.multiworld.get_location(data.locations[value].label, world.player)
            else:
                world.multiworld.get_entrance(f"{value['from_region']} -> {value['to_region']}", world.player)
        except KeyError:
            return False
        return True
    raw = getattr(world, "_enemy_copy_ability_policy", None)
    if not isinstance(raw, dict):
        return False
    if kind == "guaranteed_source":
        return SourcePolicy(raw).grant(value, lambda _: True).guaranteed == frozenset({ability})
    if kind == "reviewed_graph_sources":
        statues = getattr(getattr(world, "options", None), "ability_randomization_statues", None)
        policy = SourcePolicy(raw, bool(getattr(statues, "value", 0)))
        row = next(row for row in _room_catalog()[0] if row["id"] == value["target"])
        if not target_applies(row, policy):
            return False
        for name in value["witnesses"]:
            graph = room_traversal_graph(row["id"], name)
            rooms = {node.key: node.room for node in graph.nodes}
            for source in graph.placements:
                grant = policy.grant(source.source_key, lambda _: True, native_room=rooms[source.node])
                if ability in grant.guaranteed or (
                    source.renewable and source.retry_evidence and grant.randomized and ability in grant.abilities
                ):
                    return True
        return False
    raise ValueError(f"Unknown Kirby permission predicate: {kind!r}")


def permission_is_progression(world: Any, item_code: int) -> bool:
    routes, by_code = _progression_permissions()
    names = by_code.get(item_code)
    if names is None or not world._ability_gating_enabled():
        return False
    ability = data.items[item_code].label.removesuffix(" Ability")
    return any(_permission_predicate(world, ability, routes[name], routes) for name in names)


def _route_is_progression(world: Any, ability: str, route: str, *, require_binding: bool = False) -> bool:
    if not world._ability_gating_enabled():
        return False
    routes, by_code = _progression_permissions()
    if require_binding and not any(
        route in names and data.items[code].label == f"{ability} Ability" for code, names in by_code.items()
    ):
        return False
    return _permission_predicate(world, ability, routes[route], routes)


# Named compatibility helpers retain the existing test and diagnostic API.
def goal2_ice_is_progression(world: Any) -> bool:
    return _route_is_progression(world, "Ice", "olive_goal_2_ice")


def candy912_source_is_progression(world: Any, ability: str) -> bool:
    return _route_is_progression(world, ability, "candy_9_12_local_source", require_binding=True)


def cabbage_source_is_progression(world: Any, ability: str) -> bool:
    return _route_is_progression(world, ability, "cabbage_chocolate_carry")


def cabbage_missile_is_progression(world: Any) -> bool:
    return cabbage_source_is_progression(world, "Missile")


def cabbage_parasol_is_progression(world: Any) -> bool:
    return cabbage_source_is_progression(world, "Parasol")


def cabbage_element_is_progression(world: Any, ability: str) -> bool:
    return ability in {"Spark", "Ice"} and cabbage_source_is_progression(world, ability)


def mustard_crash_is_progression(world: Any) -> bool:
    return _route_is_progression(world, "Crash", "mustard_advanced_crash")


def carrot_fighter_is_progression(world: Any) -> bool:
    return _route_is_progression(world, "Fighter", "carrot_5_13_local_source")


def mustard_magic_is_progression(world: Any) -> bool:
    return _route_is_progression(world, "Magic", "mustard_4_16_advanced_source")


def mustard_ice_is_progression(world: Any) -> bool:
    return _route_is_progression(world, "Ice", "mustard_4_16_local_source")


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
    from . import conditional_routes, yellow_cupid, room16_timer

    yellow_enabled = yellow_cupid.validate_profile(world, install=True)
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
    active_contracts = frozenset(name for name, enabled in (
        (conditional_routes.CANDY_FUSE.CONTRACT, getattr(world, "_candy912_linked_west_fuse", False)),
        (room16_timer.CONTRACT, room16_timer.enabled(policy)),
        (yellow_cupid.CONTRACT, yellow_enabled),
    ) if enabled)
    for row in extra_traversal_targets():
        profile_graphs = conditional_routes.active_graphs(row, active_contracts, policy)
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
