"""Repair a seeded Standard shuffle by exchanging existing grants.

A candidate is tested against the same directed acquisition witnesses as the
world. This preflight does not assume their entry regions are reachable in a
particular seed: Archipelago fill and Kirby's final accessibility audit do that.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import hashlib
from typing import Any, Callable

from .enemy_ability_runtime_patch import (
    MAX_SHUFFLE_SOURCE_SWAPS, MAX_SHUFFLE_STATUE_RESERVATIONS, SHUFFLE_SOURCE_SWAPS,
    SHUFFLE_STATUE_RESERVATIONS, shuffled_source_grants,
)
from .statue_seed import COPY_ABILITY_ROOM
from .traversal import CAPABILITY_ABILITIES, SourcePolicy, TraversalGraph
from .traversal_data import graph_items, room_traversal_targets

# Search assignments, not world seeds. Keep work bounded even for custom pools.
_MAX_CANDIDATES = 640
_MAX_DONORS_PER_GRANT = 3
_BRANCH_WIDTH = 4


@dataclass(frozen=True)
class Constraint:
    name: str
    source_keys: frozenset[str]
    wanted: frozenset[str]
    accepts: Callable[[SourcePolicy], bool]


def _graph_constraint(
        name: str, graphs: tuple[TraversalGraph, ...],
        applies: Callable[[SourcePolicy], bool] | None = None,
        condition_keys: frozenset[str] = frozenset(), *, must_apply: bool = False,
) -> Constraint:
    keys = set(condition_keys)
    wanted: set[str] = set()
    for graph in graphs:
        rooms = {node.key: node.room for node in graph.nodes}
        for source in graph.placements:
            if rooms[source.node] != COPY_ABILITY_ROOM:
                keys.update(source.source_choices or (source.source_key,))
        if graph.required_guaranteed_source:
            key, ability = graph.required_guaranteed_source
            keys.add(key)
            wanted.add(ability)
        for route in graph.routes:
            if route.capability:
                wanted.update(route.allowed_abilities or CAPABILITY_ABILITIES[route.capability])
            if route.required_equipment:
                wanted.update(route.required_equipment)

    def accepts(policy: SourcePolicy) -> bool:
        if applies is not None and not applies(policy):
            return not must_apply
        return any(graph.required_targets <= {p.node for p in graph.evaluate(
            policy, graph_items(graph), gating=False).positions} for graph in graphs)

    return Constraint(name, frozenset(keys), frozenset(wanted), accepts)


def _constraints(initial: SourcePolicy, require_all: bool, room16: bool, area_keys: bool) -> tuple[Constraint, ...]:
    from .peg_traversal import short_peg_graphs
    from .traversal_rules import extra_traversal_targets, target_applies, target_graphs

    results: list[Constraint] = []
    if room16:
        row = next(row for row in room_traversal_targets("switch") if row["id"] == "switch_533_room16")
        graphs = target_graphs(row, area_keys, advanced=False)
        results.append(_graph_constraint(
            row["id"], graphs, lambda policy: target_applies(row, policy), frozenset({"FOLEY"}), must_apply=True,
        ))
    if require_all:
        for row in (*room_traversal_targets("wheel"), *room_traversal_targets("peg"), *extra_traversal_targets()):
            if not row.get("required_for_generation", True) or any(c.name == row["id"] for c in results):
                continue
            condition = row.get("requires_guaranteed_source")
            alternatives = row.get("requires_any_guaranteed_source", (condition,) if condition else ())
            keys = frozenset(source["source_key"] for source in alternatives)
            graphs = target_graphs(row, area_keys, advanced=False) + short_peg_graphs(row["id"], area_keys)
            applies = lambda policy, target=row: target_applies(target, policy)
            probe = _graph_constraint(row["id"], graphs, applies, keys)
            # Once a bounded, source-backed target works, never deliberately
            # disable its scope and let legacy permissive fallback count as a fix.
            if alternatives and applies(initial):
                probe = _graph_constraint(row["id"], graphs, applies, keys, must_apply=True)
            results.append(probe)
    return tuple(results)


@dataclass(frozen=True)
class Assignment:
    grants: dict[str, str]
    origins: dict[str, str]
    swaps: tuple[tuple[str, str], ...] = ()
    reserves: dict[str, str] = field(default_factory=dict)

    def policy(self, base: dict[str, Any]) -> dict[str, Any]:
        return {**base, **({SHUFFLE_SOURCE_SWAPS: self.swaps} if self.swaps else {}),
                **({SHUFFLE_STATUE_RESERVATIONS: self.reserves} if self.reserves else {})}

    def swap(self, first: str, second: str) -> Assignment:
        return Assignment(
            {**self.grants, first: self.grants[second], second: self.grants[first]},
            {**self.origins, first: self.origins[second], second: self.origins[first]},
            (*self.swaps, (first, second)), self.reserves,
        )

    def reserve(self, key: str, ability: str) -> Assignment:
        # A reservation changes the initial roster choice, before the recorded
        # swaps. Trace the slot back through any moves already in the plan.
        return Assignment({**self.grants, key: ability}, self.origins, self.swaps,
                          {**self.reserves, self.origins[key]: ability})


def constrain_shuffled_abilities(
        raw: dict[str, Any], *, include_statues: bool, require_all: bool, room16: bool, area_keys: bool,
) -> dict[str, Any]:
    """Select a deterministic repair; never draw another seed.

    Preserve the drawn rosters unless the enabled world-statue pool is the
    only randomized ability source (enemy weight 100). In that narrow profile
    a missing required ability can be reserved before swaps.
    """
    if raw.get("mode") != 1 or {SHUFFLE_SOURCE_SWAPS, SHUFFLE_STATUE_RESERVATIONS} & raw.keys():
        raise ValueError("Logic-aware shuffle requires an unmodified Shuffled policy")
    initial = SourcePolicy(raw, include_statues)
    constraints = _constraints(initial, require_all, room16, area_keys)
    assignments = shuffled_source_grants(raw, include_statues)
    original_statue_abilities = {grant for key, grant in assignments.items() if key.startswith("STATUE:")}
    reserve_pool = (set(raw["allowed_abilities"]) - {"Mini"} - original_statue_abilities
                    if include_statues and raw.get("ability_randomization_no_ability_weight") == 100 else set())
    degree = Counter(key for rule in constraints for key in rule.source_keys)
    order = {key: hashlib.sha256(f'{raw["seed"]}:logic-aware:{key}'.encode()).digest() for key in assignments}
    priority = sorted(assignments, key=lambda key: (degree[key], order[key], key))
    keys_by_rule = [tuple(sorted(rule.source_keys & assignments.keys())) for rule in constraints]
    signature_cache: list[dict[tuple[str, ...], bool]] = [{} for _ in constraints]
    seen: set[tuple[tuple[str, ...], tuple[tuple[str, str], ...]]] = set()
    remaining = _MAX_CANDIDATES

    def passes(index: int, grants: dict[str, str], policy: SourcePolicy) -> bool:
        values = tuple(grants[key] for key in keys_by_rule[index])
        cache = signature_cache[index]
        if values not in cache:
            cache[values] = constraints[index].accepts(policy)
        return cache[values]

    failures = tuple(i for i in range(len(constraints)) if not passes(i, assignments, initial))

    def neighbors(assignment: Assignment, index: int, reserve: bool):
        rule = constraints[index]
        for first in sorted(keys_by_rule[index], key=lambda key: (order[key], key)):
            if len(assignment.swaps) < MAX_SHUFFLE_SOURCE_SWAPS:
                donors: Counter[str] = Counter()
                for second in priority:
                    ability = assignment.grants[second]
                    if (first == second or assignment.grants[first] == ability
                            or first.startswith("STATUE:") != second.startswith("STATUE:")
                            or (rule.wanted and ability not in rule.wanted)
                            or donors[ability] >= _MAX_DONORS_PER_GRANT):
                        continue
                    donors[ability] += 1
                    yield assignment.swap(first, second)
            if (reserve and first.startswith("STATUE:") and assignment.origins[first] not in assignment.reserves
                    and len(assignment.reserves) < MAX_SHUFFLE_STATUE_RESERVATIONS):
                for ability in sorted((reserve_pool & rule.wanted) - set(assignment.reserves.values()),
                                      key=lambda name: (hashlib.sha256(f'{raw["seed"]}:reserve:{name}'.encode()).digest(),
                                                        name)):
                    yield assignment.reserve(first, ability)

    def search(assignment: Assignment, unresolved: tuple[int, ...], reserve: bool) -> Assignment | None:
        nonlocal remaining
        if not unresolved:
            return assignment
        if remaining <= 0:
            return None
        identity = (tuple(assignment.grants[key] for key in priority), tuple(sorted(assignment.reserves.items())))
        if identity in seen:
            return None
        seen.add(identity)
        # First select a finite Room16 constraint, then favor fewer movable sources.
        # If a single move can't solve that target, another unmet bound may
        # expose the needed route without changing the source multiset.
        options: list[tuple[Assignment, tuple[int, ...]]] = []
        for index in sorted(unresolved, key=lambda i: (
                constraints[i].name != "switch_533_room16", len(keys_by_rule[i]), i)):
            for candidate in neighbors(assignment, index, reserve):
                if remaining <= 0:
                    break
                remaining -= 1
                p = SourcePolicy(candidate.policy(raw), include_statues)
                if not passes(index, candidate.grants, p):
                    continue
                pending = tuple(i for i in range(len(constraints)) if not passes(i, candidate.grants, p))
                if not pending:
                    return candidate
                options.append((candidate, pending))
            if options or remaining <= 0:
                break
        for candidate, pending in sorted(options, key=lambda option: (
                len(option[0].reserves), len(option[1])))[:_BRANCH_WIDTH]:
            selected = search(candidate, pending, reserve)
            if selected is not None:
                return selected
        return None

    start = Assignment(assignments, {key: key for key in assignments})
    selected = search(start, failures, reserve=False)
    if selected is None and reserve_pool:
        # Keep existing copies if they can satisfy the constraints. A separate,
        # bounded phase admits missing roster abilities only in the agreed mode.
        remaining = _MAX_CANDIDATES
        seen.clear()
        selected = search(start, failures, reserve=True)
    if selected is None:
        blocked = ", ".join(constraints[i].name for i in failures)
        raise ValueError(
            f"KirbyAM couldn't satisfy reviewed Standard Shuffle sources within the bounded assignment search "
            f"({blocked}). Try another seed, lower No Ability Weight, or choose different settings. "
            "This does not prove unreviewed routes impossible."
        )
    final = selected.policy(raw)
    repaired = SourcePolicy(final, include_statues)
    if not all(rule.accepts(repaired) for rule in constraints):
        raise ValueError("Logic-aware shuffle returned an unverified source assignment")
    return final
