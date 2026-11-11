"""Frozen fixed-point reference from commit 181c6e9, before source deduplication.

Keep this evaluator unchanged when adjusting the optimized source loop. The
shared value types and pure policy helpers allow exact full-result comparison.
This is a synthetic algorithm oracle, not native gameplay evidence.
"""

from collections import defaultdict, deque
from typing import Iterable

from ..traversal import (
    CAPABILITY_ABILITIES, CAPABILITY_CONSUMED_ABILITIES, Grant, Node, Placement,
    Position, Route, SourcePolicy, TraversalResult, _SOURCE_BY_KEY,
    ability_permission, attack_provider,
)


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
    placement_list = list(placements)
    objects: dict[str, list[Placement]] = defaultdict(list)
    for source in placement_list:
        identity = source.identity or f"{source.node}:{source.source_key}"
        objects[identity].append(source)
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
        attack_provider("Normal", route.water_state)
        if route.capability == "heave_ho_pull":
            if route.water_state != "dry":
                raise ValueError("Heave-Ho pulling needs a dry Normal suction approach")
            if route.opens is not None:
                raise ValueError("Heave-Ho pulling does not model a persistent opens event")
            if route.room_transition or node_by_key[route.source].room != node_by_key[route.target].room:
                raise ValueError("Heave-Ho pulling must be a local mechanism sequence")
        if route.capability in {"metal", "metal_throw"} and (
            route.room_transition or node_by_key[route.source].room != node_by_key[route.target].room
        ):
            raise ValueError("A metal attack sequence must remain in its native room")
        if route.capability == "underwater_block_hit" and route.water_state != "swimming":
            raise ValueError("An underwater block hit needs swimming attack state")
        if (route.capability in {"frozen_enemy_hit", "metal_throw"}) != (route.uses_object is not None):
            raise ValueError("A projectile hit needs a physical target object and no unrelated capability")
        if route.capability in {"frozen_enemy_hit", "metal_throw"} and route.opens is not None:
            raise ValueError("Projectile hit cannot have a persistent opens event")
        if route.uses_object is not None:
            if not isinstance(route.uses_object, str) or not route.uses_object.strip():
                raise ValueError("Route object identity must be a nonempty string")
            candidates = objects.get(route.uses_object, ())
            if len(set(candidates)) > 1:
                raise ValueError("Conflicting physical source identity for projectile target")
            if not candidates or candidates[0].identity is None or candidates[0].node != route.source:
                raise ValueError("Route object must be a physical source in its launch compartment")
            if route.capability == "metal_throw":
                target_source = _SOURCE_BY_KEY.get(candidates[0].source_key)
                if target_source is None or not target_source.can_be_swallowed:
                    raise ValueError(
                        "Throw target must be a reviewed eligible enemy, not a statue or ineligible source")
            if candidates[0].renewable:
                raise ValueError("Projectile target needs a one-use physical placement")
        # Native cannon_fuse.c regrows the fuse after its timed pause; ignition
        # cannot grant a persistent room-local opened event.
        if route.capability == "fuse" and route.opens is not None:
            raise ValueError("Timed fuse ignition cannot have a persistent opens event")
        if route.allowed_abilities is not None and (
            not route.allowed_abilities
            or not route.allowed_abilities <= CAPABILITY_ABILITIES.get(route.capability or "", frozenset())
        ):
            raise ValueError("Allowed abilities must narrow the route capability providers")
        transitions = route.room_transition or node_by_key[route.source].room != node_by_key[route.target].room
        if route.resets_room_instance and route.preserves_room_instance:
            raise ValueError("A room instance cannot be both reset and preserved")
        if route.opens and transitions:
            raise ValueError("Open a room-local peg before taking the room transition")
        if route.recover_dropped_ability and transitions:
            raise ValueError("Drop/recovery must be an audited local sequence, not a room transition")
        outgoing[route.source].append(route)
    for source in placement_list:
        if source.node not in node_by_key:
            raise ValueError(f"Unknown source compartment: {source.node}")
        sources[source.node].append(source)
    queue = deque(starts)
    visited: set[Position] = set()
    assumptions: set[str] = set()
    grants: dict[str, Grant] = {}

    def permitted(ability: str) -> bool:
        return ability_permission(ability, owned, gating)

    def source_grant(key: str) -> Grant:
        # Grants describe deterministic possibilities, not individual RNG draws.
        # Policy, owned permissions and gating are fixed for this evaluation.
        if key not in grants:
            grants[key] = policy.grant(key, permitted)
        return grants[key]

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
            grant = source_grant(source.source_key)
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
                # Swimming Hammer is the spin, not the dry Hammer Flip used
                # by our fuse witnesses. No underwater ignition is reviewed.
                if route.water_state == "swimming" and route.capability == "fuse":
                    continue
                attacks = frozenset(attack_provider(ability, route.water_state)
                                    for ability in position.equipment_outcomes)
                if not attacks or not attacks <= abilities:
                    continue
            if not already_open and route.uses_object is not None:
                if (route.uses_object in position.consumed
                        or not objects[route.uses_object][0].requirements <= owned):
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
            if route.capability and not already_open:
                spent = CAPABILITY_CONSUMED_ABILITIES.get(route.capability, frozenset())
                if isinstance(ability, str):
                    if ability in spent:
                        ability = "Normal"
                elif ability & spent:
                    ability = (ability - spent) | {"Normal"}
            consumed = position.consumed
            if route.uses_object is not None and not already_open:
                consumed |= {route.uses_object}
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
