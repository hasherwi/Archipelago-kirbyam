"""Source-backed, directional traversal planning.

Inventory grants permission to acquire an ability, not equipment. This planner
keeps one equipped ability and room-instance switches on each search state.
It deliberately does not infer sources from a global enemy-type assignment.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping

from .enemy_ability_data import ABILITY_NAME_TO_ID, ABILITY_SOURCES, GATEABLE_ENEMY_COPY_ABILITIES
from .enemy_ability_runtime_patch import (
    _STATUE_TABLES,
    build_enemy_copy_runtime_patch_writes,
    build_enemy_source_runtime_config,
    build_statue_runtime_allowed_mask,
)


CAPABILITY_ABILITIES: Mapping[str, frozenset[str]] = {
    "peg": frozenset({"Stone", "Hammer", "Smash", "Master"}),
    "mini_corridor": frozenset({"Mini"}),
    # Only attach to a route whose timing has actually been established.
    "wheel_race": frozenset({"Wheel"}),
}
_ID_TO_NAME = {value: key for key, value in ABILITY_NAME_TO_ID.items()}
_SOURCE_BY_KEY = {source.key: source for source in ABILITY_SOURCES}
_STATUE_DEFAULTS = {
    f"STATUE:{base + index:06X}": (base + index, name)
    for base, names in _STATUE_TABLES for index, name in enumerate(names)
}


@dataclass(frozen=True)
class Grant:
    """A set of possible outputs, explicitly distinguished from certainty."""

    abilities: frozenset[str]
    randomized: bool = False
    can_fail: bool = False

    @property
    def guaranteed(self) -> frozenset[str]:
        if self.can_fail or len(self.abilities) != 1:
            return frozenset()
        return self.abilities


class SourcePolicy:
    """Use exactly the assignments and eligibility bitmap sent to the ROM.

    Live random grants are not predicted by the static fallback hash. They
    expose possible outputs separately; callers must not silently equate those
    with a finite guarantee. Excluded categories retain their native grant.
    """

    def __init__(self, policy: dict[str, Any], include_statues: bool = False) -> None:
        self.policy = dict(policy)
        self.mode = int(policy.get("mode", 0))
        self.writes = build_enemy_copy_runtime_patch_writes(policy, include_statues)
        self.source_config = build_enemy_source_runtime_config(policy)
        self.statue_mask = build_statue_runtime_allowed_mask(policy, include_statues)

    def grant(self, key: str, permitted: Callable[[str], bool]) -> Grant:
        if key in _STATUE_DEFAULTS:
            address, native_name = _STATUE_DEFAULTS[key]
            randomized = self.mode == 2 and bool(self.statue_mask)
            pool = frozenset(
                name for ability_id, name in _ID_TO_NAME.items()
                if self.statue_mask & (1 << ability_id) and permitted(name)
            )
            can_fail = not pool
        else:
            source = _SOURCE_BY_KEY[key]
            if not source.can_be_swallowed:
                return Grant(frozenset())
            address, native_name = source.addresses[0], source.default_ability_name
            native_type = (address - 0x35164E) // 24
            config_word = int.from_bytes(
                self.source_config[4 + 4 * (native_type // 32):8 + 4 * (native_type // 32)], "little"
            )
            randomized = self.mode == 2 and bool(config_word & (1 << (native_type % 32)))
            pool = frozenset(
                name for name in self.policy.get("allowed_abilities", ()) if permitted(name)
            )
            weight = int(self.policy.get("ability_randomization_no_ability_weight", 0))
            can_fail = weight > 0 or not pool
            if weight >= 100:
                pool = frozenset()
        if randomized:
            return Grant(pool, randomized=True, can_fail=can_fail)
        ability = _ID_TO_NAME[self.writes.get(address, ABILITY_NAME_TO_ID[native_name])]
        return Grant(frozenset({ability}) if ability != "Normal" and permitted(ability) else frozenset())

    def dropped_star_grant(self, previous_ability: str, permitted: Callable[[str], bool]) -> Grant:
        """Recovery is conditional on a previously acquired ability.

        Raw Mini stars use the narrow gated recovery exception. Other stars
        retain the existing live-random behavior, including the native 0x80 vs
        legacy detector 0x20 flag mismatch: do not assume weight suppression.
        A star is never an independent initial source.
        """
        if previous_ability == "Normal":
            return Grant(frozenset())
        if previous_ability == "Mini":
            return Grant(frozenset({"Mini"}) if permitted("Mini") else frozenset())
        if self.mode == 2:
            pool = frozenset(name for name in self.policy.get("allowed_abilities", ()) if permitted(name))
            weight = int(self.policy.get("ability_randomization_no_ability_weight", 0))
            if weight >= 100:
                pool = frozenset()
            return Grant(pool, randomized=True, can_fail=weight > 0 or not pool)
        return Grant(frozenset({previous_ability}) if permitted(previous_ability) else frozenset())


def ability_permission(ability: str, owned: frozenset[str], gating: bool) -> bool:
    """Match current runtime gateability without altering starting abilities."""
    return not gating or ability not in GATEABLE_ENEMY_COPY_ABILITIES or f"{ability} Ability" in owned


@dataclass(frozen=True)
class Node:
    key: str
    room: int


@dataclass(frozen=True)
class Route:
    """One directed compartment/entrance to target edge, never a room-wide gate.

    ``opens`` is a room-local peg identity. Once opened, that edge can be used
    without the ability until the search leaves the native room. A reverse edge
    must be supplied independently, including any verified bypass.
    """

    source: str
    target: str
    capability: str | None = None
    opens: str | None = None
    items: frozenset[str] = frozenset()
    allowed_abilities: frozenset[str] | None = None
    recover_dropped_ability: bool = False
    room_transition: bool = False
    resets_room_instance: bool = False
    preserves_room_instance: bool = False


@dataclass(frozen=True)
class Placement:
    """A physically reachable source with an audited acquisition predicate.

    ``requirements`` are AP items needed for acquisition (for example a boss
    clear). Geometry belongs in the compartment graph, not this item predicate.
    An object located behind a peg must be assigned to its post-peg node.
    """

    node: str
    source_key: str
    requirements: frozenset[str] = frozenset()
    retry_evidence: str | None = None
    identity: str | None = None
    renewable: bool = False


@dataclass(frozen=True)
class Position:
    node: str
    equipped: str | frozenset[str] = "Normal"
    opened: frozenset[str] = frozenset()
    consumed: frozenset[str] = frozenset()

    @property
    def equipment_outcomes(self) -> frozenset[str]:
        return frozenset({self.equipped}) if isinstance(self.equipped, str) else self.equipped


@dataclass(frozen=True)
class TraversalResult:
    positions: frozenset[Position]
    retry_assumptions: frozenset[str]

    def reaches(self, node: str) -> bool:
        return any(position.node == node for position in self.positions)


def reachable_positions(  # noqa: C901 - explicit finite-state transfer cases
    nodes: Iterable[Node],
    routes: Iterable[Route],
    placements: Iterable[Placement],
    starts: Iterable[Position],
    policy: SourcePolicy,
    owned: frozenset[str] = frozenset(),
    gating: bool = True,
    allow_documented_retries: bool = False,
) -> TraversalResult:
    """Compute a finite fixed point without consulting AP region reachability.

    Thus a source cannot bootstrap its own barrier through recursive
    ``state.can_reach`` calls. Starts are physical entry states; an unlock item
    must never be converted to an equipped starting state.

    Retry mode is opt-in *and* requires per-placement evidence of safe repeatable
    acquisition. Its result is explicitly conditional, not a bounded guarantee.
    No claim is made that resetting a room/client resets RNG to a new result.
    """
    node_list = list(nodes)
    node_by_key = {node.key: node for node in node_list}
    if len(node_by_key) != len(node_list):
        raise ValueError("Duplicate traversal compartment")
    outgoing: dict[str, list[Route]] = defaultdict(list)
    sources: dict[str, list[Placement]] = defaultdict(list)
    for route in routes:
        if route.source not in node_by_key or route.target not in node_by_key:
            raise ValueError(f"Unknown traversal endpoint: {route}")
        if route.capability is not None and route.capability not in CAPABILITY_ABILITIES:
            raise ValueError(f"Unknown traversal capability: {route.capability}")
        transitions = route.room_transition or node_by_key[route.source].room != node_by_key[route.target].room
        if route.resets_room_instance and route.preserves_room_instance:
            raise ValueError("A room instance cannot be both reset and preserved")
        if route.opens and transitions:
            raise ValueError("Open a room-local peg before taking the room transition")
        if route.recover_dropped_ability and transitions:
            raise ValueError("Drop/recovery must be an audited local sequence, not a room transition")
        outgoing[route.source].append(route)
    for source in placements:
        if source.node not in node_by_key:
            raise ValueError(f"Unknown source compartment: {source.node}")
        sources[source.node].append(source)
    queue = deque(starts)
    visited: set[Position] = set()
    assumptions: set[str] = set()

    def permitted(ability: str) -> bool:
        return ability_permission(ability, owned, gating)

    while queue:
        position = queue.popleft()
        if position in visited:
            continue
        if position.node not in node_by_key:
            raise ValueError(f"Unknown starting compartment: {position.node}")
        visited.add(position)
        # Dropping is possible, but a dropped star is NOT a free initial source.
        if position.equipped != "Normal":
            queue.append(Position(position.node, "Normal", position.opened, position.consumed))
        for source in sources[position.node]:
            if not source.requirements <= owned:
                continue
            identity = source.identity or f"{source.node}:{source.source_key}"
            if identity in position.consumed:
                continue
            consumed = position.consumed if source.renewable else position.consumed | {identity}
            grant = policy.grant(source.source_key, permitted)
            abilities = grant.guaranteed
            if (allow_documented_retries and source.renewable and source.retry_evidence
                    and grant.randomized and grant.abilities):
                abilities = grant.abilities
                assumptions.add(source.retry_evidence)
            for granted_ability in abilities:
                queue.append(Position(position.node, granted_ability, position.opened, consumed))
            if not grant.can_fail and grant.abilities and not abilities:
                # Player receives one of these, not all of them. Retain the
                # uncertainty: a subsequent edge must work for EVERY outcome.
                queue.append(Position(position.node, grant.abilities, position.opened, consumed))
        for route in outgoing[position.node]:
            if not route.items <= owned:
                continue
            opened = position.opened
            already_open = route.opens is not None and route.opens in opened
            if route.capability and not already_open:
                abilities = (
                    CAPABILITY_ABILITIES[route.capability]
                    if route.allowed_abilities is None else route.allowed_abilities
                )
                if not position.equipment_outcomes or not position.equipment_outcomes <= abilities:
                    continue
            if route.recover_dropped_ability:
                if not all(
                    previous in policy.dropped_star_grant(previous, permitted).guaranteed
                    for previous in position.equipment_outcomes
                ):
                    continue
            if route.opens:
                opened |= {route.opens}
            ability = position.equipped
            consumed = position.consumed
            if route.room_transition or node_by_key[position.node].room != node_by_key[route.target].room:
                # A transition always clears Mini, but need not recreate the
                # room instance. Unknown lifetime loses credit for opened pegs
                # WITHOUT granting a free source respawn.
                if not route.preserves_room_instance:
                    opened = frozenset()
                if route.resets_room_instance:
                    consumed = frozenset()
                if ability == "Mini":
                    ability = "Normal"
                elif isinstance(ability, frozenset) and "Mini" in ability:
                    ability = (ability - {"Mini"}) | {"Normal"}
            queue.append(Position(route.target, ability, opened, consumed))
    return TraversalResult(frozenset(visited), frozenset(assumptions))


@dataclass(frozen=True)
class TraversalGraph:
    """A reviewed graph; compiling it does not install it into world logic."""

    nodes: tuple[Node, ...]
    routes: tuple[Route, ...]
    placements: tuple[Placement, ...]
    starts: tuple[Position, ...]
    required_targets: frozenset[str]
    access_region: str | None = None
    requires_all_hub_switches: bool = False

    def evaluate(self, policy: SourcePolicy, owned: frozenset[str], gating: bool,
                 allow_documented_retries: bool = False) -> TraversalResult:
        return reachable_positions(
            self.nodes, self.routes, self.placements, self.starts, policy, owned, gating,
            allow_documented_retries,
        )


def _compile_route(row: Mapping[str, Any], area_keys: bool) -> Route:
    if not row.get("evidence"):
        raise ValueError("Traversal route is missing evidence")
    if row.get("room_instance") not in (None, "reset", "preserve"):
        raise ValueError("Unknown room instance policy")
    if row.get("room_instance") == "reset" and not row.get("reset_evidence"):
        raise ValueError("Room reset is missing evidence")
    for key in ("recover_dropped_ability", "room_transition"):
        if not isinstance(row.get(key, False), bool):
            raise ValueError(f"{key} must be a boolean")
    allowed = row.get("allowed_abilities")
    capability = row.get("capability")
    providers = CAPABILITY_ABILITIES.get(capability, frozenset()) if isinstance(capability, str) else frozenset()
    if allowed is not None and (
        not allowed or not set(allowed) <= providers
    ):
        raise ValueError("Allowed abilities must narrow the route capability providers")
    return Route(
        row["from"], row["to"], row.get("capability"), row.get("opens"),
        frozenset(row.get("items", ())) | frozenset(row.get("area_key_items", ()) if area_keys else ()),
        None if "allowed_abilities" not in row else frozenset(row["allowed_abilities"]),
        bool(row.get("recover_dropped_ability", False)),
        bool(row.get("room_transition", False)),
        row.get("room_instance") == "reset",
        row.get("room_instance") == "preserve",
    )


def _compile_placement(row: Mapping[str, Any]) -> Placement:
    if not row.get("acquisition_evidence"):
        raise ValueError("Source is missing acquisition evidence")
    if row["source_key"] not in _SOURCE_BY_KEY and row["source_key"] not in _STATUE_DEFAULTS:
        raise ValueError(f"Unknown ability source: {row['source_key']}")
    if not isinstance(row.get("renewable", False), bool):
        raise ValueError("renewable must be a boolean")
    if row.get("renewable") and not row.get("renewable_evidence"):
        raise ValueError("Renewable source is missing repeatability evidence")
    if row.get("retry_evidence") and not row.get("renewable"):
        raise ValueError("Retry evidence requires a renewable source")
    return Placement(
        row["node"], row["source_key"], frozenset(row.get("items", ())),
        retry_evidence=row.get("retry_evidence"),
        identity=row.get("id"), renewable=bool(row.get("renewable", False)),
    )


def compile_traversal_graph(payload: Mapping[str, Any], *, area_keys: bool = False) -> TraversalGraph:
    """Compile explicitly reviewed route data, refusing unresolved research.

    This is not a tile flood-fill or an automatic enemy-placement join. A source
    record must include its acquisition evidence and the exact compartment.
    """
    if payload.get("version") != 1 or payload.get("status") != "reviewed":
        raise ValueError("Only version 1 reviewed traversal graphs can be compiled")
    nodes = tuple(Node(row["id"], int(row["native_room"])) for row in payload["nodes"])
    keys = {node.key for node in nodes}
    if len(keys) != len(nodes):
        raise ValueError("Duplicate traversal compartment")
    routes = tuple(_compile_route(row, area_keys) for row in payload["routes"])
    placements = tuple(_compile_placement(row) for row in payload.get("sources", ()))
    # Default to Normal. Carried equipment belongs to a predecessor path, not
    # to an inventory grant or an unproved optimistic entry assumption.
    starts = tuple(Position(key) for key in payload["starts"])
    required_targets = frozenset(payload.get("required_targets", ()))
    if not required_targets <= keys or any(position.node not in keys for position in starts):
        raise ValueError("Unknown start or required target")
    access = payload.get("access", {})
    if not isinstance(access, dict) or set(access) - {"region", "all_hub_switches"}:
        raise ValueError("Unknown traversal access prerequisite")
    if access and not isinstance(access.get("region"), str):
        raise ValueError("Traversal access must name an independent region")
    if not isinstance(access.get("all_hub_switches", False), bool):
        raise ValueError("all_hub_switches must be a boolean")
    graph = TraversalGraph(
        nodes, tuple(routes), tuple(placements), starts, required_targets,
        access.get("region"), access.get("all_hub_switches", False),
    )
    # Validate all endpoints, capabilities and local events even if disconnected.
    graph.evaluate(SourcePolicy({"mode": 0}), frozenset(), True)
    return graph


def validated_assignment(
    graph: TraversalGraph,
    candidate_factory: Callable[[], SourcePolicy],
    owned: frozenset[str],
    gating: bool,
    max_attempts: int = 128,
) -> tuple[SourcePolicy, int]:
    """Bounded deterministic assignment rejection, without changing options.

    A seeded factory owns the RNG. The returned policy must be used for *both*
    generation and ROM writes. This tests a supplied acquisition frontier, not
    full multiworld fill accessibility; callers must still run normal fill.
    Fully-random mode is not retried using its irrelevant static fallback seed.
    """
    if max_attempts < 1:
        raise ValueError("Assignment validation needs at least one attempt")
    missing: set[str] = set()
    for attempt in range(1, max_attempts + 1):
        candidate = candidate_factory()
        result = graph.evaluate(candidate, owned, gating)
        missing = {target for target in graph.required_targets if not result.reaches(target)}
        if not missing:
            return candidate, attempt
        if candidate.mode != 1:
            break
    raise ValueError(
        "No source-backed traversal witness for " + ", ".join(sorted(missing))
        + "; options and native source outputs were not changed"
    )
