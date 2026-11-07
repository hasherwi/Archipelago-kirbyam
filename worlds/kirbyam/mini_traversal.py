"""Source-aware Mini corridors with fixed Minny and gated raw-Mini star recovery."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from .data import data, load_json_data
from .enemy_ability_data import GATEABLE_ENEMY_COPY_ABILITIES
from .traversal import SourcePolicy, TraversalGraph, compile_traversal_graph


@lru_cache(maxsize=1)
def mini_routes() -> tuple[tuple[dict[str, Any], TraversalGraph], ...]:
    payload = load_json_data("mini_traversal.json")
    if not isinstance(payload, dict):
        raise TypeError("Mini traversal catalog must be an object")
    return tuple((row, compile_traversal_graph(row["graph"])) for row in payload["routes"])


def validate_mini_sources(policy_data: dict[str, Any], include_statues: bool) -> None:
    """Validate the fixed local sources without changing random assignments."""
    all_permissions = frozenset(f"{name} Ability" for name in GATEABLE_ENEMY_COPY_ABILITIES)
    policy = SourcePolicy(policy_data, include_statues)
    for row, graph in mini_routes():
        result = graph.evaluate(policy, all_permissions, True)
        if not all(result.reaches(target) for target in graph.required_targets):
            raise ValueError(f"Mini traversal contract has no fixed-source witness: {row['id']}")


def install_mini_rules(world: Any) -> None:
    from worlds.generic.Rules import add_rule

    raw_policy = getattr(world, "_enemy_copy_ability_policy", None)
    if not isinstance(raw_policy, dict):
        return
    policy = SourcePolicy(raw_policy, bool(world.options.ability_randomization_statues.value))
    gating = world._ability_gating_enabled()
    for row, graph in mini_routes():
        def rule(state: Any, graph: TraversalGraph = graph) -> bool:
            owned = frozenset(
                f"{name} Ability" for name in GATEABLE_ENEMY_COPY_ABILITIES
                if state.has(f"{name} Ability", world.player)
            )
            result = graph.evaluate(policy, owned, gating)
            return all(result.reaches(target) for target in graph.required_targets)

        if row["exit"]:
            entrance = world.multiworld.get_entrance(f"{row['region']} -> {row['exit']}", world.player)
            add_rule(entrance, rule)
        elif row["location"]:
            location_data = data.locations[row["location"]]
            # A disabled optional check does not need an AP access rule.
            try:
                location = world.multiworld.get_location(location_data.label, world.player)
            except KeyError:
                continue
            add_rule(location, rule)
