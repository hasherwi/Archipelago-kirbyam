"""Confirmed local-source peg routes; remaining census is explicitly audited.

These conservative witnesses do not claim that carried abilities are impossible.
They seed explicit carried-source paths from an independently reachable hub and
never credit a source behind its own peg. Other peg routes await a reviewed carry/compartment graph.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Callable

from .data import data
from .special_route_data import SPECIAL_ROUTE_PROFILES
from .traversal import SourcePolicy, TraversalGraph
from .traversal_data import (
    compile_room_graph, graph_access_regions, graph_items, has_graph_access, requires_all_traversal_witnesses,
    room_traversal_graph, room_traversal_targets,
)


PEG_ROUTES = room_traversal_targets("peg")


def stone_carry_graph(row: dict[str, Any], area_keys: bool, statue_room: bool = False) -> TraversalGraph:
    """Compile the reviewed carrier, including option-dependent Area Keys."""
    return room_traversal_graph(row["id"], "statues" if statue_room else "carry", area_keys)


@lru_cache(maxsize=None)
def short_peg_graphs(target_id: str, area_keys: bool) -> tuple[TraversalGraph, ...]:
    record = SPECIAL_ROUTE_PROFILES["short_peg_witnesses"].get(target_id)
    if record is None:
        return ()
    return tuple(compile_room_graph(entry["witness"], {}, area_keys=area_keys, require_inventory=True)
                 for entry in (record, *record.get("alternatives", ())))


def carry_graphs(row: dict[str, Any], area_keys: bool) -> tuple[TraversalGraph, ...]:
    return tuple(room_traversal_graph(row["id"], name, area_keys)
                 for name in row["graphs"] if name != "local") + short_peg_graphs(row["id"], area_keys)


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

ROOM16_COMPLETION_LIVE_REJECTION = (
    "KirbyAM 100% Game Completion requires visiting Mustard Mountain Room 4-16, even with RoomSanity off, "
    "but Completely Random cannot guarantee equipment from the finite local source for any reviewed route. "
    "Use Shuffled or Off, or select a different goal and keep RoomSanity off."
)
ROOM16_COMPLETION_WEIGHT_REJECTION = (
    "KirbyAM 100% Game Completion requires visiting Mustard Mountain Room 4-16, even with RoomSanity off, "
    "but Shuffled with 100% no-ability weight provides no equipment from the finite local source. "
    "Lower the no-ability weight, use Off, or select a different goal and keep RoomSanity off."
)


def validate_peg_assignment(
    initial: dict[str, Any], factory: Callable[[], dict[str, Any]], include_statues: bool,
    max_attempts: int = 8192, *, require_all_witnesses: bool = True, advanced: bool = False,
    require_room16: bool = False, room16_for_completion: bool = False,
    allow_room16_shuffle_repair: bool = False, logic_aware_shuffle: bool = False, area_keys: bool = False,
) -> dict[str, Any]:
    """Select a valid deterministic assignment without rerolling generation.

    The bounded default allows rare joint Wheelie/peg-source assignments with fixed
    statues. If an ordinary Room16 shuffle is exhausted, try swapping two existing
    enemy grants while preserving grant counts and independently checking every witness. Rejection does not prove that no
    remote-carried solution exists. Live random statues use explicit retry semantics.
    RoomSanity and 100% Game Completion independently require the Room16
    witness, even under minimal accessibility. All witnesses share one policy.
    """
    if not isinstance(require_all_witnesses, bool):
        raise TypeError("require_all_witnesses must be a boolean")
    if max_attempts < 1:
        raise ValueError("assignment search budget must be positive")
    require_room16 = require_room16 or room16_for_completion
    validate_static = require_all_witnesses and peg_logic_enabled(initial)
    if not validate_static and not require_room16:
        return initial
    from .wheel_traversal import static_wheel_witness
    from .traversal_rules import static_extra_witness, static_room16_witness

    if require_room16 and not peg_logic_enabled(initial):
        if not static_room16_witness(SourcePolicy(initial, include_statues), advanced=advanced):
            raise KirbyAmRoom16SourceError(
                ROOM16_COMPLETION_LIVE_REJECTION if room16_for_completion else ROOM16_LIVE_REJECTION
            )
        return initial

    if (require_room16 and initial.get("mode") == 1
            and initial.get("ability_randomization_no_ability_weight") == 100
            and not static_room16_witness(SourcePolicy(initial, include_statues), advanced=advanced)):
        raise KirbyAmRoom16SourceError(
            ROOM16_COMPLETION_WEIGHT_REJECTION if room16_for_completion else ROOM16_WEIGHT_REJECTION
        )

    if initial.get("mode") == 1 and logic_aware_shuffle and not advanced:
        from .logic_aware_shuffle import constrain_shuffled_abilities

        return constrain_shuffled_abilities(
            initial, include_statues=include_statues, require_all=validate_static,
            room16=require_room16, area_keys=area_keys,
        )

    repair_candidates: list[dict[str, Any]] | None = (
        [] if allow_room16_shuffle_repair and require_room16 and initial.get("mode") == 1 else None
    )
    candidate = initial
    wheel_valid_candidate = None
    peg_valid_candidate = None
    extra_valid = False
    for attempt in range(max_attempts):
        policy = SourcePolicy(candidate, include_statues)
        # This independent prerequisite rejects most Room16-ineligible policies
        # before the costly catalog evaluation. It consumes no RNG and preserves
        # the first jointly valid assignment from the original candidate stream.
        room16_valid = not require_room16 or static_room16_witness(policy, advanced=advanced)
        if not room16_valid and repair_candidates is not None:
            repair_candidates.append(candidate)
        wheel_valid = room16_valid and (not validate_static or static_wheel_witness(policy))
        if wheel_valid and wheel_valid_candidate is None:
            wheel_valid_candidate = candidate
        if wheel_valid and (not validate_static or all(_assignment_has_witness(row, policy) for row in PEG_ROUTES)):
            peg_valid_candidate = candidate
            if not validate_static or static_extra_witness(policy, advanced=advanced):
                extra_valid = True
                return candidate
        if policy.mode != 1:
            break
        if attempt + 1 < max_attempts:
            candidate = factory()
    if repair_candidates:
        from .enemy_ability_runtime_patch import ROOM16_FOLEY_SWAP, room16_foley_swap_candidates

        room16 = next(row for row in room_traversal_targets("switch") if row["id"] == "switch_533_room16")
        reviewed = frozenset(room16["requires_guaranteed_source"]["abilities"])

        def other_witnesses(policy: SourcePolicy) -> bool:
            return not validate_static or (
                static_wheel_witness(policy)
                and all(_assignment_has_witness(row, policy) for row in PEG_ROUTES)
                and static_extra_witness(policy, advanced=advanced)
            )

        # Revisit only already-sampled candidates; no additional RNG draws. Prefer
        # a policy with all the other witnesses intact before changing Foley.
        for raw in repair_candidates:
            if not other_witnesses(SourcePolicy(raw, include_statues)):
                continue
            for donor in room16_foley_swap_candidates(raw, reviewed):
                corrected = {**raw, ROOM16_FOLEY_SWAP: donor}
                policy = SourcePolicy(corrected, include_statues)
                if static_room16_witness(policy, advanced=advanced) and other_witnesses(policy):
                    return corrected

    raise _assignment_search_failure(initial, attempt + 1, wheel_valid_candidate is not None,
                                     peg_valid_candidate is not None, extra_valid, room16_for_completion,
                                     room16_required=require_room16)


def _assignment_search_failure(initial: dict[str, Any], attempts: int, wheel_valid: bool,
                               peg_valid: bool, extra_valid: bool, room16_for_completion: bool = False,
                               *, room16_required: bool = False) -> ValueError:
    context = f"after {attempts} attempts (mode={initial.get('mode')}, initial seed={initial.get('seed')}). "
    if extra_valid or room16_required:
        # With the cheap Room16 filter first, skipped policies need not have
        # their other graphs evaluated. Report joint exhaustion, not impossibility.
        feature = "100% Game Completion" if room16_for_completion else "RoomSanity"
        return KirbyAmRoom16SourceError(
            f"KirbyAM {feature} requires Mustard Mountain Room 4-16, but no reviewed source "
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
    policy = SourcePolicy.for_world(world, raw_policy)
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
