"""Confirmed local-source peg routes; remaining census is explicitly audited.

These conservative witnesses do not claim that carried abilities are impossible.
They seed explicit carried-source paths from an independently reachable hub and
never credit a source behind its own peg. Other peg routes await a reviewed carry/compartment graph.
"""

from __future__ import annotations

from typing import Any, Callable

from .data import data
from .traversal import SourcePolicy, TraversalGraph
from .traversal_data import (
    graph_access_regions, graph_items, has_graph_access, requires_all_traversal_witnesses,
    room_traversal_graph, room_traversal_targets,
)


PEG_ROUTES = room_traversal_targets("peg")


def stone_carry_graph(row: dict[str, Any], area_keys: bool, statue_room: bool = False) -> TraversalGraph:
    """Compile the reviewed carrier, including option-dependent Area Keys."""
    return room_traversal_graph(row["id"], "statues" if statue_room else "carry", area_keys)


def carry_graphs(row: dict[str, Any], area_keys: bool) -> tuple[TraversalGraph, ...]:
    return tuple(room_traversal_graph(row["id"], name, area_keys)
                 for name in row["graphs"] if name != "local")


def carrier_reachable(world: Any, state: Any, policy: SourcePolicy, graph: TraversalGraph,
                      owned: frozenset[str], gating: bool) -> bool:
    if not has_graph_access(world, state, graph):
        return False
    required = graph_items(graph)
    owned |= frozenset(item for item in required if state.has(item, world.player))
    return graph.evaluate(policy, owned, gating, allow_documented_retries=True).reaches("target")


def peg_graph(row: dict[str, Any]) -> TraversalGraph:
    return room_traversal_graph(row["id"], "local")


def peg_logic_enabled(policy: dict[str, Any]) -> bool:
    """Static assignments can be validated, including weight100 statue carriers."""
    mode = int(policy.get("mode", 0))
    return mode in (0, 1)


def _assignment_has_witness(row: dict[str, Any], policy: SourcePolicy) -> bool:
    local = peg_graph(row)
    if local.evaluate(policy, graph_items(local), False).reaches("target"):
        return True
    for graph in carry_graphs(row, False):
        items = graph_items(graph)
        if graph.evaluate(policy, items, False).reaches("target"):
            return True
    return False


class KirbyAmRoom16SourceError(ValueError):
    """Generation cannot certify equipment for the enabled Room16 visit."""


ROOM16_LIVE_REJECTION = (
    "KirbyAM RoomSanity requires Mustard Mountain Room 4-16, but Completely Random "
    "cannot guarantee equipment from the finite local source for any reviewed route. "
    "Use Shuffled or Off, or disable RoomSanity."
)
ROOM16_WEIGHT_REJECTION = (
    "KirbyAM RoomSanity requires Mustard Mountain Room 4-16, but Shuffled with "
    "100% no-ability weight provides no equipment from the finite local source. "
    "Lower the no-ability weight, use Off, or disable RoomSanity."
)


def validate_peg_assignment(
    initial: dict[str, Any], factory: Callable[[], dict[str, Any]], include_statues: bool,
    max_attempts: int = 8192, *, require_all_witnesses: bool = True, advanced: bool = False,
    require_room16: bool = False,
) -> dict[str, Any]:
    """Select a valid deterministic assignment; do not rewrite individual grants.

    The bounded default allows rare joint Wheelie/peg-source assignments with fixed
    statues. It never forces individual grants. Rejection does not prove that no
    remote-carried solution exists. Live random statues use explicit retry semantics.
    RoomSanity makes the otherwise optional Room16 witness mandatory, even
    under minimal accessibility. All selected witnesses must share one policy.
    """
    if not isinstance(require_all_witnesses, bool):
        raise TypeError("require_all_witnesses must be a boolean")
    if max_attempts < 1:
        raise ValueError("assignment search budget must be positive")
    validate_static = require_all_witnesses and peg_logic_enabled(initial)
    if not validate_static and not require_room16:
        return initial
    from .wheel_traversal import static_wheel_witness
    from .traversal_rules import static_extra_witness, static_room16_witness

    if require_room16 and not peg_logic_enabled(initial):
        if not static_room16_witness(SourcePolicy(initial, include_statues), advanced=advanced):
            raise KirbyAmRoom16SourceError(ROOM16_LIVE_REJECTION)
        return initial

    if (require_room16 and initial.get("mode") == 1
            and initial.get("ability_randomization_no_ability_weight") == 100
            and not static_room16_witness(SourcePolicy(initial, include_statues), advanced=advanced)):
        raise KirbyAmRoom16SourceError(ROOM16_WEIGHT_REJECTION)

    candidate = initial
    wheel_valid_candidate = None
    peg_valid_candidate = None
    extra_valid = False
    for attempt in range(max_attempts):
        policy = SourcePolicy(candidate, include_statues)
        wheel_valid = not validate_static or static_wheel_witness(policy)
        if wheel_valid and wheel_valid_candidate is None:
            wheel_valid_candidate = candidate
        if wheel_valid and (not validate_static or all(_assignment_has_witness(row, policy) for row in PEG_ROUTES)):
            peg_valid_candidate = candidate
            if not validate_static or static_extra_witness(policy, advanced=advanced):
                extra_valid = True
                if not require_room16 or static_room16_witness(policy, advanced=advanced):
                    return candidate
        if policy.mode != 1:
            break
        if attempt + 1 < max_attempts:
            candidate = factory()
    raise _assignment_search_failure(initial, attempt + 1, wheel_valid_candidate is not None,
                                     peg_valid_candidate is not None, extra_valid)


def _assignment_search_failure(initial: dict[str, Any], attempts: int, wheel_valid: bool,
                               peg_valid: bool, extra_valid: bool) -> ValueError:
    context = f"after {attempts} attempts (mode={initial.get('mode')}, initial seed={initial.get('seed')}). "
    if extra_valid:
        return KirbyAmRoom16SourceError(
            "KirbyAM RoomSanity requires Mustard Mountain Room 4-16, but no reviewed source "
            f"witness met all assignment constraints {context}Try another seed or use Ability Randomization Off."
        )
    feature = "Wheel" if not wheel_valid else "fuse/rope/block" if peg_valid else "peg"
    return ValueError(
        f"Reviewed {feature}-source search budget exhausted {context}"
        "This does not prove the configuration or unreviewed alternatives impossible; try another seed."
    )


def install_peg_rules(world: Any) -> None:
    from worlds.generic.Rules import add_rule
    from .enemy_ability_data import GATEABLE_ENEMY_COPY_ABILITIES

    raw_policy = getattr(world, "_enemy_copy_ability_policy", None)
    if not isinstance(raw_policy, dict):
        return
    policy = SourcePolicy(raw_policy, bool(world.options.ability_randomization_statues.value))
    gating = world._ability_gating_enabled()
    for row in PEG_ROUTES:
        graph = peg_graph(row)
        carriers = carry_graphs(row, world._area_keys_enabled())
        all_items = frozenset(f"{name} Ability" for name in GATEABLE_ENEMY_COPY_ABILITIES)
        all_items |= frozenset(item for candidate in (graph, *carriers) for item in graph_items(candidate))
        if requires_all_traversal_witnesses(world) and not any(
            candidate.evaluate(policy, all_items, gating, allow_documented_retries=True).reaches("target")
            for candidate in (graph, *carriers)
        ):
            raise ValueError(
                f"No reviewed source witness for {row['id']} in mode {policy.mode}; "
                "unreviewed alternatives are not declared impossible. Try another seed."
            )

        def rule(state: Any, graph: TraversalGraph = graph,
                 carriers: tuple[TraversalGraph, ...] = carriers) -> bool:
            owned = frozenset(
                f"{name} Ability" for name in GATEABLE_ENEMY_COPY_ABILITIES
                if state.has(f"{name} Ability", world.player)
            )
            local_owned = owned | frozenset(item for item in graph_items(graph) if state.has(item, world.player))
            if (has_graph_access(world, state, graph)
                    and graph.evaluate(policy, local_owned, gating, allow_documented_retries=True).reaches("target")):
                return True
            return any(carrier_reachable(world, state, policy, carrier, owned, gating)
                       for carrier in carriers)

        if row["exit"]:
            target = world.multiworld.get_entrance(f"{row['region']} -> {row['exit']}", world.player)
            for witness in (graph, *carriers):
                for name in graph_access_regions(witness):
                    dependency = world.multiworld.get_region(name, world.player)
                    world.multiworld.register_indirect_condition(dependency, target)
        else:
            location_data = data.locations[row["location"]]
            try:
                target = world.multiworld.get_location(location_data.label, world.player)
            except KeyError:
                continue
        add_rule(target, rule)
