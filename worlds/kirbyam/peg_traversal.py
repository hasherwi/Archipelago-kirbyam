"""Confirmed local-source peg routes; remaining census is explicitly audited.

These conservative witnesses do not claim that carried abilities are impossible.
They seed explicit carried-source paths from an independently reachable hub and
never credit a source behind its own peg. Other peg routes await a reviewed carry/compartment graph.
"""

from __future__ import annotations

from typing import Any, Callable

from .data import data
from .traversal import Node, Placement, Position, Route, SourcePolicy, TraversalGraph


PEG_ROUTES: tuple[dict[str, Any], ...] = (
    {
        "id": "peg_149_35_18", "room": 149,
        "region": "REGION_MOONLIGHT_MANSION/ROOM_2_20",
        "exit": None, "location": "MINOR_CHEST_MOONLIGHT_MANSION_2_20",
        "sources": (("GIANT_ROCKY", "0x088BC434"),), "carry_abilities": {"Smash"},
    },
    {
        "id": "peg_510_7_7", "room": 510,
        "region": "REGION_CABBAGE_CAVERN/ROOM_3_09",
        "exit": None, "location": "MINOR_CHEST_CABBAGE_CAVERN_3_09",
        "sources": (), "source_hub": "REGION_CABBAGE_CAVERN/ROOM_3_HUB_3",
    },
    {
        "id": "peg_513_4_7", "room": 513,
        "region": "REGION_CABBAGE_CAVERN/ROOM_3_13",
        "exit": "REGION_CABBAGE_CAVERN/ROOM_3_13_LOWER", "location": None,
        "sources": (), "source_hub": "REGION_CABBAGE_CAVERN/ROOM_3_HUB_3",
    },
    {
        "id": "peg_204_62_4", "room": 204,
        "region": "REGION_PEPPERMINT_PALACE/ROOM_7_12",
        "exit": "REGION_PEPPERMINT_PALACE/ROOM_7_06__LOGIC__HAPPY_NOTES_ENTRY", "location": None,
        "sources": (),
    },
    {
        "id": "peg_605_12_24", "room": 605,
        "region": "REGION_RADISH_RUINS/ROOM_8_03",
        "exit": "REGION_RADISH_RUINS/ROOM_8_CHEST_1", "location": None,
        "sources": (), "source_hub": "REGION_CABBAGE_CAVERN/ROOM_3_HUB_3",
    },
    {
        "id": "peg_527_56_16", "room": 527,
        "region": "REGION_CABBAGE_CAVERN/ROOM_3_14",
        "exit": "REGION_CABBAGE_CAVERN/ROOM_3_15_LOWER_ENTRY", "location": None,
        "sources": (), "source_hub": "REGION_CABBAGE_CAVERN/ROOM_3_HUB_3",
    },
    {
        "id": "peg_527_18_13", "room": 527,
        "region": "REGION_CABBAGE_CAVERN/ROOM_3_14",
        "exit": None, "location": "MINOR_CHEST_SPRAY_PAINT_08",
        "sources": (), "source_hub": "REGION_CABBAGE_CAVERN/ROOM_3_HUB_3",
    },
    {
        "id": "peg_816_26_3", "room": 816,
        "region": "REGION_OLIVE_OCEAN/ROOM_6_CHEST_2",
        "exit": None, "location": "MAJOR_CHEST_OLIVE_OCEAN",
        "sources": (("BONKERS", "0x088CE8FC"),),
        "source_hub": "REGION_CABBAGE_CAVERN/ROOM_3_HUB_3",
    },
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
    "peg_149_35_18": (190, 143, 145, 146, 147, 148, 149),
    "peg_510_7_7": (592, 528, 513, 509, 510),
    "peg_513_4_7": (592, 528, 513),
    "peg_204_62_4": (190, 801, 290, 210, 227, 204),
    "peg_605_12_24": (592, 690, 611, 601, 605),
    "peg_527_56_16": (592, 528, 527),
    "peg_527_18_13": (592, 528, 527),
    "peg_816_26_3": (592, 801, 191, 890, 811, 830, 810, 802, 816),
    "peg_411_4_3": (190, 801, 490, 411),
    "peg_401_28_30": (190, 801, 490, 407, 401),
    "peg_221_41_12": (190, 801, 290, 291, 215, 212, 216, 217, 221),
}
_CARRY_ITEMS = {
    "peg_149_35_18": frozenset(),
    "peg_510_7_7": frozenset(),
    "peg_513_4_7": frozenset(),
    "peg_204_62_4": frozenset({
        "Rainbow Route East - Hub Connection", "Peppermint Palace East - Hub Connection",
    }),
    "peg_605_12_24": frozenset({"Radish Ruins - Hub Connection"}),
    "peg_527_56_16": frozenset(),
    "peg_527_18_13": frozenset(),
    "peg_816_26_3": frozenset({
        "Cabbage Cavern West - Hub Connection", "Cabbage Cavern East - Hub Connection",
        "Olive Ocean - Hub Connection",
    }),
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


def stone_carry_graph(row: dict[str, Any], area_keys: bool, statue_room: bool = False) -> TraversalGraph:
    """Reviewed Stone carry, not a global inventory/equipment OR.

    Candy407 uses an ordinary bomb approached from above. The PP212 path avoids
    all five rock bodies; PP216 avoids F0 blocks, PP217 avoids its star platform.
    All intermediate paths retain Stone and avoid Mini-only corridors.
    """
    path = _CARRY_PATHS[row["id"]]
    items = _CARRY_ITEMS[row["id"]]
    if statue_room:
        assert row["room"] == 149
        path = (970, 801) + path
        items |= {"Rainbow Route East - Hub Connection"}
    if area_keys:
        areas = {row["region"].split("/")[0].removeprefix("REGION_").replace("_", " ").title()}
        if row["room"] == 816:
            areas.add("Cabbage Cavern")  # Carrier re-enters191 after Central Circle.
        items |= {area + " - Area Key" for area in areas}
    nodes = tuple(Node(str(room), room) for room in path) + (Node("target", row["room"]),)
    routes = tuple(
        Route(str(source), str(target), items=items)
        for source, target in zip(path, path[1:])
    ) + (Route(str(path[-1]), "target", "peg", row["id"], allowed_abilities=frozenset(
        row.get("carry_abilities", {"Stone", "Hammer", "Smash"} if row["room"] == 411 else {"Stone"})
    )),)
    placements: tuple[tuple[str, str], ...] = (("STATUE:353900", "0x088B7CEC"), ("STATUE:3538FC", "0x088B7DA0"))
    if path[0] == 592:
        placements = (("STATUE:353900", "0x088CEFEC"), ("STATUE:3538FD", "0x088CEFC8"))
    if statue_room:
        from .wheel_traversal import STATUE_OBJECTS
        placements = tuple((f"STATUE:{0x3538FC + index:06X}", address)
                           for index, address in enumerate(STATUE_OBJECTS))
    sources = tuple(Placement(
        str(path[0]), key, identity=identity, renewable=True,
        retry_evidence="Permanent hub statue can be retouched before carry; eventual eligible draw assumed",
    ) for key, identity in placements)
    return TraversalGraph(nodes, routes, sources, (Position(str(path[0])),), frozenset({"target"}))


def carry_graphs(row: dict[str, Any], area_keys: bool) -> tuple[TraversalGraph, ...]:
    graphs: tuple[TraversalGraph, ...] = (stone_carry_graph(row, area_keys),)
    if row["room"] == 149:
        graphs += (stone_carry_graph(row, area_keys, statue_room=True),)
    return graphs


def carrier_reachable(world: Any, state: Any, policy: SourcePolicy, graph: TraversalGraph,
                      source_hub: str, owned: frozenset[str], gating: bool) -> bool:
    if graph.nodes[0].room == 970:
        from .wheel_traversal import CENTRAL_REGION, HUB_SWITCH_LABELS
        if not state.can_reach_region(CENTRAL_REGION, world.player):
            return False
        if not all(world.multiworld.get_location(name, world.player).can_reach(state)
                   for name in HUB_SWITCH_LABELS):
            return False
    elif not state.can_reach_region(source_hub, world.player):
        return False
    required = frozenset(item for route in graph.routes for item in route.items)
    owned |= frozenset(item for item in required if state.has(item, world.player))
    return graph.evaluate(policy, owned, gating, allow_documented_retries=True).reaches("target")


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
    for graph in carry_graphs(row, False):
        items = frozenset(item for route in graph.routes for item in route.items)
        if graph.evaluate(policy, items, False).reaches("target"):
            return True
    return False


def validate_peg_assignment(
    initial: dict[str, Any], factory: Callable[[], dict[str, Any]], include_statues: bool,
    max_attempts: int = 1024,
) -> dict[str, Any]:
    """Select a valid deterministic assignment; do not rewrite individual grants.

    This is conservative source validation, not a proof that rejected assignments
    have no remote-carried solution. Live random statues use explicit retry semantics.
    """
    if max_attempts < 1:
        raise ValueError("assignment search budget must be positive")
    if not peg_logic_enabled(initial):
        return initial
    from .wheel_traversal import static_wheel_witness

    candidate = initial
    wheel_valid_candidate = None
    for attempt in range(max_attempts):
        policy = SourcePolicy(candidate, include_statues)
        wheel_valid = static_wheel_witness(policy)
        if wheel_valid and wheel_valid_candidate is None:
            wheel_valid_candidate = candidate
        if wheel_valid and all(_assignment_has_witness(row, policy) for row in PEG_ROUTES):
            return candidate
        if policy.mode != 1:
            break
        if attempt + 1 < max_attempts:
            candidate = factory()
    if wheel_valid_candidate is None:
        raise ValueError(
            f"Reviewed Wheel-source search budget exhausted after {attempt + 1} attempts "
            f"(mode={initial.get('mode')}, initial seed={initial.get('seed')}). "
            "This does not prove the configuration or unreviewed alternatives impossible; try another seed."
        )
    raise ValueError(
        f"Reviewed peg-source search budget exhausted after {attempt + 1} attempts "
        f"(mode={initial.get('mode')}, initial seed={initial.get('seed')}). "
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
        all_items |= frozenset(item for carrier in carriers for route in carrier.routes for item in route.items)
        if not any(candidate.evaluate(policy, all_items, gating, allow_documented_retries=True).reaches("target")
                   for candidate in (graph, *carriers)):
            raise ValueError(
                f"No reviewed source witness for {row['id']} in mode {policy.mode}; "
                "unreviewed alternatives are not declared impossible. Try another seed."
            )

        def rule(state: Any, graph: TraversalGraph = graph,
                 carriers: tuple[TraversalGraph, ...] = carriers,
                 source_hub: str = row.get("source_hub", _STONE_HUB)) -> bool:
            owned = frozenset(
                f"{name} Ability" for name in GATEABLE_ENEMY_COPY_ABILITIES
                if state.has(f"{name} Ability", world.player)
            )
            if graph.evaluate(policy, owned, gating).reaches("target"):
                return True
            return any(carrier_reachable(world, state, policy, carrier, source_hub, owned, gating)
                       for carrier in carriers)

        if row["exit"]:
            target = world.multiworld.get_entrance(f"{row['region']} -> {row['exit']}", world.player)
            hub = world.multiworld.get_region(row.get("source_hub", _STONE_HUB), world.player)
            world.multiworld.register_indirect_condition(hub, target)
        else:
            location_data = data.locations[row["location"]]
            try:
                target = world.multiworld.get_location(location_data.label, world.player)
            except KeyError:
                continue
        add_rule(target, rule)
