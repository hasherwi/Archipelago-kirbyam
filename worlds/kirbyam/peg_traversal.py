"""Confirmed local-source peg routes; remaining census is explicitly audited.

These conservative witnesses do not claim that carried abilities are impossible.
They seed explicit carried-source paths from an independently reachable hub and
never credit a source behind its own peg. Other peg routes await a reviewed carry/compartment graph.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from .data import data
from .traversal import Node, Placement, Position, Route, SourcePolicy, TraversalGraph


PEG_ROUTES: tuple[dict[str, Any], ...] = (
    {
        "id": "peg_411_4_3", "room": 411,
        "region": "REGION_CANDY_CONSTELLATION/ROOM_9_08",
        "exit": "REGION_CANDY_CONSTELLATION/ROOM_9_09", "location": None,
        "sources": (),
    },
    {
        "id": "peg_401_28_30", "room": 401,
        "region": "REGION_CANDY_CONSTELLATION/ROOM_9_06",
        "exit": "REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_1", "location": None,
        "sources": (("ROCKY", "0x088C5840"), ("ROCKY", "0x088C5864")),
    },
    {
        "id": "peg_221_41_12", "room": 221,
        "region": "REGION_PEPPERMINT_PALACE/ROOM_7_22",
        "exit": None, "location": "MINOR_CHEST_SPRAY_PAINT_01",
        "sources": (("GIANT_ROCKY", "0x088C192C"), ("GIANT_ROCKY", "0x088C1A4C")),
    },
)

_STONE_HUB = "REGION_RAINBOW_ROUTE/ROOM_1_HUB_1"
_CARRY_PATHS = {
    "peg_411_4_3": (190, 801, 490, 411),
    "peg_401_28_30": (190, 801, 490, 407, 401),
    "peg_221_41_12": (190, 801, 290, 291, 215, 212, 216, 217, 221),
}
_CARRY_ITEMS = {
    "peg_411_4_3": frozenset({
        "Rainbow Route East - Hub Connection", "Candy Constellation - Hub Connection",
    }),
    "peg_401_28_30": frozenset({
        "Rainbow Route East - Hub Connection", "Candy Constellation - Hub Connection",
    }),
    "peg_221_41_12": frozenset({
        "Rainbow Route East - Hub Connection", "Peppermint Palace East - Hub Connection",
        "Peppermint Palace West - Hub Connection",
    }),
}


def stone_carry_graph(row: dict[str, Any], area_keys: bool) -> TraversalGraph:
    """Reviewed Stone carry, not a global inventory/equipment OR.

    Candy407 uses an ordinary bomb approached from above. The PP212 path avoids
    all five rock bodies; PP216 avoids F0 blocks, PP217 avoids its star platform.
    All intermediate paths retain Stone and avoid Mini-only corridors.
    """
    path = _CARRY_PATHS[row["id"]]
    items = _CARRY_ITEMS[row["id"]]
    if area_keys:
        area = "Candy Constellation" if row["room"] in (401, 411) else "Peppermint Palace"
        items |= {area + " - Area Key"}
    nodes = tuple(Node(str(room), room) for room in path) + (Node("target", row["room"]),)
    routes = tuple(
        Route(str(source), str(target), items=items)
        for source, target in zip(path, path[1:])
    ) + (Route(str(path[-1]), "target", "peg", row["id"], allowed_abilities=frozenset(
        {"Stone", "Hammer", "Smash"} if row["room"] == 411 else {"Stone"}
    )),)
    sources = tuple(Placement(
        "190", key, identity=identity, renewable=True,
        retry_evidence="Hub190 permanent statue can be retouched before carry; eventual Stone draw assumed",
    ) for key, identity in (("STATUE:353900", "0x088B7CEC"), ("STATUE:3538FC", "0x088B7DA0")))
    return TraversalGraph(nodes, routes, sources, (Position("190"),), frozenset({"target"}))


def peg_graph(row: dict[str, Any]) -> TraversalGraph:
    return TraversalGraph(
        (Node("approach", row["room"]), Node("target", row["room"])),
        (Route("approach", "target", "peg", row["id"]),),
        tuple(Placement("approach", key, identity=identity) for key, identity in row["sources"]),
        (Position("approach"),), frozenset({"target"}),
    )


def peg_logic_enabled(policy: dict[str, Any]) -> bool:
    """Static assignments can be validated, including weight100 statue carriers."""
    mode = int(policy.get("mode", 0))
    return mode in (0, 1)


def _assignment_has_witness(row: dict[str, Any], policy: SourcePolicy) -> bool:
    if peg_graph(row).evaluate(policy, frozenset(), False).reaches("target"):
        return True
    graph = stone_carry_graph(row, False)
    items = frozenset(item for route in graph.routes for item in route.items)
    return graph.evaluate(policy, items, False).reaches("target")


def validate_peg_assignment(
    initial: dict[str, Any], factory: Callable[[], dict[str, Any]], include_statues: bool,
    max_attempts: int = 1024,
) -> dict[str, Any]:
    """Select a valid deterministic assignment; do not rewrite individual grants.

    This is conservative source validation, not a proof that rejected assignments
    have no remote-carried solution. Live random rollout remains incomplete.
    """
    if not peg_logic_enabled(initial):
        return initial
    candidate = initial
    for attempt in range(max_attempts):
        policy = SourcePolicy(candidate, include_statues)
        if all(_assignment_has_witness(row, policy) for row in PEG_ROUTES):
            return candidate
        if policy.mode != 1:
            break
        if attempt + 1 < max_attempts:
            candidate = factory()
    logging.getLogger(__name__).warning(
        "No reviewed peg-source witness found within %s assignment attempts. "
        "Keeping the original policy and deferring only unsupported draft routes; "
        "this is not a proof that other carried-source alternatives are impossible.", max_attempts,
    )
    return initial


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
        carry_graph = stone_carry_graph(row, world._area_keys_enabled())
        all_items = frozenset(f"{name} Ability" for name in GATEABLE_ENEMY_COPY_ABILITIES)
        all_items |= frozenset(item for route in carry_graph.routes for item in route.items)
        if not (graph.evaluate(policy, all_items, gating).reaches("target") or carry_graph.evaluate(
                policy, all_items, gating, allow_documented_retries=True).reaches("target")):
            logging.getLogger(__name__).warning(
                "Draft peg rule %s deferred: no reviewed source witness for this policy; "
                "unreviewed alternatives are not declared impossible", row["id"],
            )
            continue

        def rule(state: Any, graph: TraversalGraph = graph,
                 carry_graph: TraversalGraph = carry_graph) -> bool:
            owned = frozenset(
                f"{name} Ability" for name in GATEABLE_ENEMY_COPY_ABILITIES
                if state.has(f"{name} Ability", world.player)
            )
            if graph.evaluate(policy, owned, gating).reaches("target"):
                return True
            # Recursive AP reachability only seeds the separately verified
            # pre-gate source compartment. The carry path itself is explicit.
            if not state.can_reach_region(_STONE_HUB, world.player):
                return False
            required = frozenset(item for route in carry_graph.routes for item in route.items)
            owned |= frozenset(item for item in required if state.has(item, world.player))
            return carry_graph.evaluate(policy, owned, gating, allow_documented_retries=True).reaches("target")

        if row["exit"]:
            target = world.multiworld.get_entrance(f"{row['region']} -> {row['exit']}", world.player)
        else:
            location_data = data.locations[row["location"]]
            try:
                target = world.multiworld.get_location(location_data.label, world.player)
            except KeyError:
                continue
        add_rule(target, rule)
