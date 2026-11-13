"""Source-backed, directional traversal planning.

Inventory grants permission to acquire an ability, not equipment. This planner
keeps one equipped ability and room-instance switches on each search state.
It deliberately does not infer sources from a global enemy-type assignment.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping

from .master_source import (
    CARROT_HUB, CARROT_KEY, CENTRAL_MASTER_IDENTITY, CENTRAL_MASTER_SOURCE, CENTRAL_REGION,
    CENTRAL_RETURN_EVENT, MASTER719_CAPABILITY, MASTER719_NODES, MASTER719_PREFIX, RAINBOW_WEST_HUB,
)
from .enemy_ability_data import ABILITY_NAME_TO_ID, ABILITY_SOURCES, GATEABLE_ENEMY_COPY_ABILITIES
from .enemy_ability_runtime_patch import (
    _STATUE_TABLES,
    build_enemy_copy_runtime_patch_writes,
    build_enemy_source_runtime_config,
    build_statue_runtime_allowed_mask,
)


METAL_BREAKING_ABILITIES = frozenset({
    "Hammer", "Stone", "Throw", "Burning", "Missile", "UFO", "Smash", "Master",
})


CAPABILITY_ABILITIES: Mapping[str, frozenset[str]] = {
    "peg": frozenset({"Stone", "Hammer", "Smash", "Master"}),
    "fuse": frozenset({"Fire", "Burning", "Bomb", "Laser", "UFO", "Master", "Hammer", "Crash"}),
    "rope": frozenset({"Cutter", "Sword", "Cupid", "Smash", "Master"}),
    "mini_corridor": frozenset({"Mini"}),
    # These are attack classes, not permission-to-equip shortcuts. Room data
    # must still establish direction, reach, source and water state.
    "metal": METAL_BREAKING_ABILITIES - {"Throw"},
    # Throw is a physical capture-and-release sequence, never an unarmed attack.
    "metal_throw": frozenset({"Throw"}),
    # A reviewed dry ordinary-block attack/carry, not a metal crossing. Only
    # Burning has an accepted provider witness for this class so far.
    "ordinary_block_hit": frozenset({"Burning"}),
    "frozen_enemy_hit": frozenset({"Ice"}),
    # Normal suction moves an existing Heave-Ho into a reviewed disposal path.
    # This is not an attack against metal or an inventory-granted ability.
    "heave_ho_pull": frozenset({"Normal"}),
    "underwater_block_hit": frozenset({"Normal", "Parasol", "Hammer", "Sword", "Master"}),
    # Target-specific native witnesses, NOT a general wall-piercing class.
    "bomb_110_room9": frozenset({"Spark"}),
    "bomb_110_room9_underwater_sword": frozenset({"Sword"}),
    # Exact finite mouth payload and lower spray; not generic Normal ammunition.
    "bomb_110_upper_normal_spit": frozenset({"Normal"}),
    "bomb_110_room9_underwater_normal_spray": frozenset({"Normal"}),
    # Select only lower F1, leaving the upper blocking-chain trigger intact.
    "bomb_138_green": frozenset({"Spark"}),
    "bomb_138_green_normal_lower_slide": frozenset({"Normal"}),
    # Grounded left-ledge sweep and completed chain crossing, not Beam range.
    "bomb_538_beam_left_crossover": frozenset({"Beam"}),
    "bomb_733_yellow_ufo_top_charge": frozenset({"UFO"}),
    "bomb_517_chocolate": frozenset({"Beam", "Spark", "Ice", "Smash"}),
    "bomb_517_fire_breath": frozenset({"Fire"}),
    "bomb_517_missile_blast": frozenset({"Missile"}),
    "bomb_517_parasol_swing": frozenset({"Parasol"}),
    "bomb_517_sword_first_slash": frozenset({"Sword"}),
    "bomb_517_fighter_first_combo": frozenset({"Fighter"}),
    "bomb_517_ufo_top_charge": frozenset({"UFO"}),
    "bomb_719_room13": frozenset({"Beam"}),
    "bomb_719_fighter_first_combo": frozenset({"Fighter"}),
    "bomb_719_sword_repeated_slash": frozenset({"Sword"}),
    "bomb_719_fire_breath": frozenset({"Fire"}),
    MASTER719_CAPABILITY: frozenset({"Master"}),
    "switch_533_bomb_placement": frozenset({"Bomb"}),
    "switch_533_ufo_top_charge": frozenset({"UFO"}),
    # Exact camera-valid room533 pose and timed crossing, not whole-room damage.
    "switch_533_crash_viewport": frozenset({"Crash"}),
    # Ordinary-mode visible roulette selection, exact pose and timed crossing.
    "switch_533_magic_meta_knight": frozenset({"Magic"}),
    "switch_310_ufo_top_charge": frozenset({"UFO"}),
    "switch_310_crash_viewport": frozenset({"Crash"}),
    "switch_310_cupid_up_left_q0": frozenset({"Cupid"}),
    # Five roof returns, enemy-aware setup and timed crossing, not any Cutter shot.
    "switch_310_cutter_five_roof_returns": frozenset({"Cutter"}),
    "switch_825_ufo_top_charge": frozenset({"UFO"}),
    # Only attach to a route whose timing has actually been established.
    "wheel_race": frozenset({"Wheel"}),
}
# Each target effect keeps its reviewed room and attack medium. The underwater
# Sword spin and Normal spray remain separate from the dry Spark effect.
ROOM_SCOPED_CAPABILITIES: Mapping[str, int] = {
    "bomb_110_room9": 110,
    "bomb_110_room9_underwater_sword": 110,
    "bomb_110_upper_normal_spit": 110,
    "bomb_110_room9_underwater_normal_spray": 110,
    "bomb_138_green": 138,
    "bomb_138_green_normal_lower_slide": 138,
    "bomb_538_beam_left_crossover": 538,
    "bomb_733_yellow_ufo_top_charge": 733,
    "bomb_517_chocolate": 517,
    "bomb_517_fire_breath": 517,
    "bomb_517_missile_blast": 517,
    "bomb_517_parasol_swing": 517,
    "bomb_517_sword_first_slash": 517,
    "bomb_517_fighter_first_combo": 517,
    "bomb_517_ufo_top_charge": 517,
    "bomb_719_room13": 719,
    "bomb_719_fighter_first_combo": 719,
    "bomb_719_sword_repeated_slash": 719,
    "bomb_719_fire_breath": 719,
    MASTER719_CAPABILITY: 719,
    "switch_533_bomb_placement": 533,
    "switch_533_ufo_top_charge": 533,
    "switch_533_crash_viewport": 533,
    "switch_533_magic_meta_knight": 533,
    "switch_310_ufo_top_charge": 310,
    "switch_310_crash_viewport": 310,
    "switch_310_cupid_up_left_q0": 310,
    "switch_310_cutter_five_roof_returns": 310,
    "switch_825_ufo_top_charge": 825,
}

ROOM_SCOPED_ATTACK_WATER_STATES: Mapping[str, str] = {
    capability: "swimming" if capability in {
        "bomb_110_room9_underwater_sword", "bomb_110_room9_underwater_normal_spray",
    } else "dry"
    for capability in ROOM_SCOPED_CAPABILITIES
}

# Native kirby.c swimming B dispatch. Other equipment uses Normal Water Gun
# without replacing the carried ability. In particular, swimming cannot start
# Stone or use Smash's hammer. A pre-transformed Stone descent is a separate
# geometric sequence and must not be inferred from a swimming attack.
UNDERWATER_ATTACK_ABILITIES = frozenset({"Parasol", "Hammer", "Sword", "Master"})


def attack_provider(ability: str, water_state: str) -> str | None:
    if water_state not in {"dry", "swimming"}:
        raise ValueError(f"Unknown traversal water state: {water_state}")
    if water_state == "swimming" and ability == "Mini":
        return None  # Native swimming input excludes Mini; dropping is separate.
    if water_state == "swimming" and ability not in UNDERWATER_ATTACK_ABILITIES:
        return "Normal"
    return ability


# Equipment consumed by actually using a capability, not by crossing an already
# opened barrier. Physical source consumption remains tracked independently.
CAPABILITY_CONSUMED_ABILITIES: Mapping[str, frozenset[str]] = {
    "fuse": frozenset({"Crash"}),
    "switch_310_crash_viewport": frozenset({"Crash"}),
    "switch_533_crash_viewport": frozenset({"Crash"}),
    "switch_533_magic_meta_knight": frozenset({"Magic"}),
}
_ID_TO_NAME = {value: key for key, value in ABILITY_NAME_TO_ID.items()}
# Wait (27) is AP metadata, never actual native carried equipment.
_NATIVE_EQUIPMENT = frozenset(name for name, value in ABILITY_NAME_TO_ID.items()
                              if 0 <= value <= ABILITY_NAME_TO_ID["Master"])
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
        if key == CENTRAL_MASTER_SOURCE:
            # Conditional output only. Physical Normal contact and availability
            # are enforced by the bounded witness, not ordinary permission RNG.
            return Grant(frozenset({"Master"}))
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

    ``required_equipment`` optionally narrows actual carried equipment on a
    reviewed movement edge. Every possible outcome must qualify. It grants no
    attack, does not use swimming attack substitution and defaults to no guard.
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
    water_state: str = "dry"
    uses_object: str | None = None
    # Physical carry/ladder state, independent of attack-provider substitution.
    required_equipment: frozenset[str] | None = None


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


def _has_central_master(placements: Iterable[Placement], routes: Iterable[Route]) -> bool:
    return (any(source.source_key == CENTRAL_MASTER_SOURCE for source in placements)
            or any(route.capability == MASTER719_CAPABILITY for route in routes))


def _validate_central_master_witness(nodes: list[Node], routes: list[Route],
                                     placements: list[Placement], starts: list[Position]) -> None:
    """Allow only the first finite, single-acquisition719 witness.

    Exact forward topology prevents return/retouch and equipment-cache aliasing.
    This is a restriction on admitted evidence, not a native impossibility claim.
    Ordinary sources, reset bookkeeping and equipment expansion stay unchanged.
    """
    if not _has_central_master(placements, routes):
        return
    expected_nodes = {MASTER719_PREFIX + key: room for key, room in MASTER719_NODES}
    keys = tuple(expected_nodes)
    if len(nodes) != len(keys) or {node.key: node.room for node in nodes} != expected_nodes:
        raise ValueError("Central Master witness requires the exact801-to719 compartments")
    if starts != [Position(keys[0])]:
        raise ValueError("Central Master witness requires one fresh Normal Central entry")
    expected_source = Placement(keys[1], CENTRAL_MASTER_SOURCE,
                                frozenset({CENTRAL_RETURN_EVENT}), identity=CENTRAL_MASTER_IDENTITY)
    if placements != [expected_source]:
        raise ValueError("Central Master requires the sole original nonrenewable stand and return event")
    pairs = tuple(zip(keys, keys[1:]))
    if len(routes) != len(pairs) or {(route.source, route.target) for route in routes} != set(pairs):
        raise ValueError("Central Master witness must be forward-only without loops or reacquisition")
    for route in routes:
        index = pairs.index((route.source, route.target))
        items = {RAINBOW_WEST_HUB} if index == 1 else {CARROT_HUB} if index == 2 else set()
        if index == 2 and CARROT_KEY in route.items:
            items.add(CARROT_KEY)
        expected = Route(
            route.source, route.target,
            capability=MASTER719_CAPABILITY if index == len(pairs) - 1 else None,
            items=frozenset(items),
            room_transition=expected_nodes[route.source] != expected_nodes[route.target],
            required_equipment=frozenset({"Normal" if index == 0 else "Master"}),
        )
        if route != expected:
            raise ValueError("Central Master requires exact carrier items, equipment and charged-wave action")


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
    route_list = list(routes)
    start_list = list(starts)
    _validate_central_master_witness(node_list, route_list, placement_list, start_list)
    objects: dict[str, list[Placement]] = defaultdict(list)
    for source in placement_list:
        identity = source.identity or f"{source.node}:{source.source_key}"
        objects[identity].append(source)
    node_by_key = {node.key: node for node in node_list}
    if len(node_by_key) != len(node_list):
        raise ValueError("Duplicate traversal compartment")
    outgoing: dict[str, list[Route]] = defaultdict(list)
    sources: dict[str, list[Placement]] = defaultdict(list)
    for route in route_list:
        if route.source not in node_by_key or route.target not in node_by_key:
            raise ValueError(f"Unknown traversal endpoint: {route}")
        if route.capability is not None and route.capability not in CAPABILITY_ABILITIES:
            raise ValueError(f"Unknown traversal capability: {route.capability}")
        if route.capability is not None and route.capability in ROOM_SCOPED_CAPABILITIES:
            native_room = ROOM_SCOPED_CAPABILITIES[route.capability]
            medium = ROOM_SCOPED_ATTACK_WATER_STATES[route.capability]
            if (node_by_key[route.source].room != native_room
                    or node_by_key[route.target].room != native_room or route.water_state != medium):
                raise ValueError(f"Room-scoped attack witness requires its native room and {medium} attack pose")
        attack_provider("Normal", route.water_state)
        if route.required_equipment is not None and (
            not isinstance(route.required_equipment, frozenset) or not route.required_equipment
            or not route.required_equipment <= _NATIVE_EQUIPMENT
        ):
            raise ValueError("Required equipment must be a nonempty set of native ability names")
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
        if route.capability == "ordinary_block_hit":
            if route.opens is not None:
                raise ValueError("Atomic ordinary-block carrier cannot have a persistent opens event")
            if route.room_transition or node_by_key[route.source].room != node_by_key[route.target].room:
                raise ValueError("An ordinary-block attack sequence must remain in its native room")
        if route.capability == "underwater_block_hit" and route.water_state != "swimming":
            raise ValueError("An underwater block hit needs swimming attack state")
        if (route.capability in {"frozen_enemy_hit", "metal_throw", "bomb_110_upper_normal_spit"}) != (
            route.uses_object is not None
        ):
            raise ValueError("A projectile hit needs a physical target object and no unrelated capability")
        if route.capability in {"frozen_enemy_hit", "metal_throw", "bomb_110_upper_normal_spit"} \
                and route.opens is not None:
            raise ValueError("Projectile hit cannot have a persistent opens event")
        if route.capability in {"bomb_110_upper_normal_spit", "bomb_110_room9_underwater_normal_spray"}:
            if route.required_equipment != frozenset({"Normal"}):
                raise ValueError("Normal110 actions require actual Normal equipment")
            if route.opens is not None or route.room_transition:
                raise ValueError("Normal110 actions are atomic local sequences without persistent opens")
        if route.capability == "bomb_138_green_normal_lower_slide":
            if (route.required_equipment != frozenset({"Normal"}) or route.opens is not None
                    or route.room_transition or route.items or route.recover_dropped_ability
                    or route.source != "bomb_138_green:normal_lower_slide"
                    or route.target != "bomb_138_green:normal_chest"):
                raise ValueError("Green138 Normal slide is an exact chest-only local action")
        if route.uses_object is not None:
            if not isinstance(route.uses_object, str) or not route.uses_object.strip():
                raise ValueError("Route object identity must be a nonempty string")
            candidates = objects.get(route.uses_object, ())
            if len(set(candidates)) > 1:
                raise ValueError("Conflicting physical source identity for projectile target")
            if not candidates or candidates[0].identity is None or candidates[0].node != route.source:
                raise ValueError("Route object must be a physical source in its launch compartment")
            if route.capability == "bomb_110_upper_normal_spit" and (
                candidates[0].source_key != "SWORD_KNIGHT" or candidates[0].identity != "0x088B74CC"
            ):
                raise ValueError("Normal110 spit needs its original finite Sword Knight payload")
            if route.capability == "metal_throw":
                target_source = _SOURCE_BY_KEY.get(candidates[0].source_key)
                if target_source is None or not target_source.can_be_swallowed:
                    raise ValueError(
                        "Throw target must be a reviewed eligible enemy, not a statue or ineligible source")
            if candidates[0].renewable:
                raise ValueError("Projectile target needs a one-use physical placement")
        # Native cannon_fuse.c regrows the fuse after its timed pause; ignition
        # cannot grant a persistent room-local opened event. The Crash533 and
        # Magic533 gates close during the witnessed Normal crossing. UFO825 also uses
        # a timed crossing, never a persistent switch-open event. Cupid310 likewise
        # crosses a closing gate; its embedded arrow does not keep the slot high.
        # Cutter310 setup cycles the gate and crosses after its final return.
        if (route.capability in {"fuse", "switch_533_crash_viewport", "switch_310_crash_viewport",
                                 "switch_825_ufo_top_charge", "switch_310_cupid_up_left_q0",
                                 "switch_533_magic_meta_knight", "switch_310_cutter_five_roof_returns"}
                and route.opens is not None):
            raise ValueError("Timed fuse ignition cannot have a persistent opens event"
                             if route.capability == "fuse"
                             else "Timed switch attack cannot have a persistent opens event")
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
    queue = deque(start_list)
    visited: set[Position] = set()
    assumptions: set[str] = set()
    grants: dict[str, Grant] = {}
    expanded_sources: set[tuple[str, frozenset[str], frozenset[str]]] = set()

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
        # Acquiring a source replaces equipment; its successors depend only on
        # this physical phase and the fixed policy/permissions, not what is held.
        # Keep both phase sets: finite source use and opened barriers must never
        # be merged. Route, drop and recovery expansion still uses every Position.
        source_phase = (position.node, position.opened, position.consumed)
        if source_phase not in expanded_sources:
            expanded_sources.add(source_phase)
            for source in sources[position.node]:
                if source.source_key == CENTRAL_MASTER_SOURCE and position.equipped != "Normal":
                    continue  # The admitted Normal prefix makes phase deduplication safe.
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
            if route.required_equipment is not None and (
                not position.equipment_outcomes or not position.equipment_outcomes <= route.required_equipment
            ):
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
    unavailable_reason: str | None = None
    required_guaranteed_source: tuple[str, str] | None = None

    def evaluate(self, policy: SourcePolicy, owned: frozenset[str], gating: bool,
                 allow_documented_retries: bool = False) -> TraversalResult:
        if _has_central_master(self.placements, self.routes):
            if (self.access_region != CENTRAL_REGION or self.requires_all_hub_switches
                    or self.unavailable_reason is not None or self.required_guaranteed_source is not None
                    or self.required_targets != frozenset({MASTER719_PREFIX + "left_door"})):
                raise ValueError("Central Master requires its independent Central access and exact lower719 target")
            _validate_central_master_witness(list(self.nodes), list(self.routes),
                                             list(self.placements), list(self.starts))
        if self.unavailable_reason is not None:
            return TraversalResult(frozenset(), frozenset())
        if self.required_guaranteed_source is not None:
            source, ability = self.required_guaranteed_source
            if policy.grant(source, lambda _: True).guaranteed != frozenset({ability}):
                return TraversalResult(frozenset(), frozenset())
        return reachable_positions(
            self.nodes, self.routes, self.placements, self.starts, policy, owned, gating,
            allow_documented_retries,
        )


def _validate_heave_ho_evidence(row: Mapping[str, Any]) -> None:
    if row.get("capability") == "heave_ho_pull":
        evidence = row.get("heave_ho_evidence")
        if not isinstance(evidence, str) or not evidence.strip():
            raise ValueError("Heave-Ho pulling requires object, approach and disposal evidence")
    elif "heave_ho_evidence" in row:
        raise ValueError("Heave-Ho evidence requires the local pulling mechanism")


def _validate_projectile_evidence(row: Mapping[str, Any]) -> None:
    evidence_key = {
        "frozen_enemy_hit": "frozen_enemy_evidence", "metal_throw": "throw_evidence",
        # One atomic capture/carry/spit witness uses the existing evidence field.
        "bomb_110_upper_normal_spit": "evidence",
    }.get(row.get("capability", ""))
    if row.get("uses_object") is not None:
        if evidence_key is None:
            raise ValueError("Physical target object requires a projectile capability")
        evidence = row.get(evidence_key)
        if not isinstance(evidence, str) or not evidence.strip():
            raise ValueError("Projectile requires freeze/kick evidence or capture/throw evidence")
    for key in ("frozen_enemy_evidence", "throw_evidence"):
        if key in row and (key != evidence_key or row.get("uses_object") is None):
            raise ValueError("Projectile evidence requires the matching physical target object")
    if evidence_key is not None and row.get("opens") is not None:
        raise ValueError("Projectile hit cannot have a persistent opens event")


def _validate_metal_evidence(row: Mapping[str, Any]) -> None:
    """Each accepted move is an atomic room witness, not another search state.

    Evidence must cover the launch/capture point, direction, clearance, charge,
    water at initiation and impact, and exact native barrier. The compiler only
    checks completeness of provider attribution; it cannot prove that evidence.
    """
    if row.get("capability") not in {"metal", "metal_throw"}:
        if "metal_evidence" in row:
            raise ValueError("Metal evidence requires an ordinary-metal capability")
        return
    allowed = row.get("allowed_abilities")
    if (not isinstance(allowed, list) or not allowed
            or any(not isinstance(ability, str) for ability in allowed)
            or len(set(allowed)) != len(allowed)):
        raise ValueError("Metal routes need explicit unique reviewed ability providers")
    evidence = row.get("metal_evidence")
    if (not isinstance(evidence, dict) or set(evidence) != set(allowed)
            or any(not isinstance(value, str) or not value.strip() for value in evidence.values())):
        raise ValueError("Metal routes need move and geometry evidence for every allowed ability")


def _compile_route(row: Mapping[str, Any], area_keys: bool) -> Route:
    if set(row) - {
        "from", "to", "capability", "opens", "items", "area_key_items", "evidence",
        "allowed_abilities", "recover_dropped_ability", "room_transition",
        "room_instance", "reset_evidence", "water_state", "uses_object",
        "frozen_enemy_evidence", "required_equipment", "heave_ho_evidence", "metal_evidence", "throw_evidence",
    }:
        raise ValueError("Unknown traversal route field or effect")
    if not row.get("evidence"):
        raise ValueError("Traversal route is missing evidence")
    if row.get("room_instance") not in (None, "reset", "preserve"):
        raise ValueError("Unknown room instance policy")
    if row.get("room_instance") == "reset" and not row.get("reset_evidence"):
        raise ValueError("Room reset is missing evidence")
    _validate_projectile_evidence(row)
    for key in ("recover_dropped_ability", "room_transition"):
        if not isinstance(row.get(key, False), bool):
            raise ValueError(f"{key} must be a boolean")
    _validate_heave_ho_evidence(row)
    _validate_metal_evidence(row)
    equipment = row.get("required_equipment")
    if "required_equipment" in row and (
        not isinstance(equipment, list) or not equipment
        or any(not isinstance(name, str) or name not in _NATIVE_EQUIPMENT for name in equipment)
        or len(equipment) != len(set(equipment))
    ):
        raise ValueError("Required equipment must be a nonempty list of distinct native ability names")
    allowed = row.get("allowed_abilities")
    capability = row.get("capability")
    if (capability in {"fuse", "switch_533_crash_viewport", "switch_310_crash_viewport",
                       "switch_825_ufo_top_charge", "switch_310_cupid_up_left_q0",
                       "switch_533_magic_meta_knight", "switch_310_cutter_five_roof_returns"}
            and row.get("opens") is not None):
        raise ValueError("Timed fuse ignition cannot have a persistent opens event"
                         if capability == "fuse" else "Timed switch attack cannot have a persistent opens event")
    if capability == "ordinary_block_hit" and row.get("opens") is not None:
        raise ValueError("Atomic ordinary-block carrier cannot have a persistent opens event")
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
        row.get("water_state", "dry"), row.get("uses_object"),
        None if equipment is None else frozenset(equipment),
    )


def _compile_placement(row: Mapping[str, Any]) -> Placement:
    if not row.get("acquisition_evidence"):
        raise ValueError("Source is missing acquisition evidence")
    if row["source_key"] == CENTRAL_MASTER_SOURCE:
        if set(row) - {"node", "source_key", "items", "id", "renewable", "acquisition_evidence"}:
            raise ValueError("Unknown Central Master placement field or effect")
    elif row["source_key"] not in _SOURCE_BY_KEY and row["source_key"] not in _STATUE_DEFAULTS:
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


def _validate_central_master_metadata(payload: Mapping[str, Any], graph: TraversalGraph) -> None:
    if _has_central_master(graph.placements, graph.routes):
        if set(payload) - {"version", "status", "nodes", "routes", "sources", "starts",
                           "required_targets", "access"}:
            raise ValueError("Unknown Central Master graph field or effect")
        if any(set(node) != {"id", "native_room"} for node in payload["nodes"]):
            raise ValueError("Unknown Central Master compartment field or effect")
        # Compilation and direct evaluation have the same exact access contract.
        graph.evaluate(SourcePolicy({"mode": 0}), frozenset(), True)
        for row in payload["routes"]:
            expected_key = [CARROT_KEY] if row["from"] == MASTER719_PREFIX + "west_hub" else []
            if row.get("area_key_items", []) != expected_key:
                raise ValueError("Central Master requires the exact optional192-to193 Carrot Area Key")


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
    if not isinstance(access, dict) or set(access) - {"region", "all_hub_switches", "unavailable"}:
        raise ValueError("Unknown traversal access prerequisite")
    if set(access) - {"unavailable"} and not isinstance(access.get("region"), str):
        raise ValueError("Traversal access must name an independent region")
    if not isinstance(access.get("all_hub_switches", False), bool):
        raise ValueError("all_hub_switches must be a boolean")
    if "unavailable" in access and (not isinstance(access["unavailable"], str) or not access["unavailable"].strip()):
        raise ValueError("Unavailable traversal source needs a concrete reason")
    condition = payload.get("requires_guaranteed_source")
    required_source = None
    if condition is not None:
        if (not isinstance(condition, dict) or set(condition) != {"source_key", "ability"}
                or not isinstance(condition["source_key"], str)
                or not isinstance(condition["ability"], str)
                or condition["ability"] not in _NATIVE_EQUIPMENT - {"Normal"}
                or not any(p.source_key == condition["source_key"] for p in placements)):
            raise ValueError("Graph guaranteed-source condition must name a placement and native ability")
        required_source = (condition["source_key"], condition["ability"])
    graph = TraversalGraph(
        nodes, tuple(routes), tuple(placements), starts, required_targets,
        access.get("region"), access.get("all_hub_switches", False), access.get("unavailable"),
        required_source,
    )
    _validate_central_master_metadata(payload, graph)
    # Validate all endpoints even when this reviewed geometry is currently
    # unavailable on the patched ROM. Availability must not hide malformed data.
    reachable_positions(graph.nodes, graph.routes, graph.placements, graph.starts, SourcePolicy({"mode": 0}))
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
