"""Load reviewed, room-owned traversal targets and reusable physical source sets.

Ability providers stay in traversal.py. This module joins explicit source-set
references, never infers acquisition from the enemies present in a whole room.
"""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from typing import Any, Mapping

from Options import Accessibility

from .ability_source_inventory import generation_instance_suffix, resolve_inventory_source
from .data import LocationCategory, data
from .enemy_ability_data import ABILITY_NAME_TO_ID, ABILITY_SOURCES
from .traversal import TraversalGraph, compile_traversal_graph


HUB_SWITCH_LABELS = tuple(row.label for row in data.locations.values()
                          if row.category == LocationCategory.HUB_SWITCH)


def requires_all_traversal_witnesses(world: Any) -> bool:
    """Only explicit minimal accessibility may leave source-backed checks closed.

    This controls the early feasibility filter, never the installed access rules.
    Normal fill and accessibility still have to prove the selected goal reachable.
    Missing or malformed options conservatively retain full validation.
    """
    accessibility = getattr(getattr(world, "options", None), "accessibility", None)
    return not (
        isinstance(accessibility, Accessibility)
        and type(accessibility.value) is int
        and accessibility.value == Accessibility.option_minimal
    )


def graph_items(graph: TraversalGraph) -> frozenset[str]:
    """Inventory prerequisites for both route traversal and source acquisition."""
    return (frozenset(item for route in graph.routes for item in route.items)
            | frozenset(item for source in graph.placements for item in source.requirements))


def has_graph_access(world: Any, state: Any, graph: TraversalGraph) -> bool:
    """Test independent acquisition access, not inventory-as-equipment."""
    if graph.unavailable_reason is not None:
        return False
    if graph.access_region is not None and not state.can_reach_region(graph.access_region, world.player):
        return False
    return not graph.requires_all_hub_switches or all(
        world.multiworld.get_location(name, world.player).can_reach(state) for name in HUB_SWITCH_LABELS
    )


def graph_access_regions(graph: TraversalGraph) -> frozenset[str]:
    """Region dependencies needed when a source-backed entrance is reconsidered."""
    regions = frozenset({graph.access_region}) if graph.access_region is not None else frozenset()
    if graph.requires_all_hub_switches:
        regions |= frozenset(row.parent_region for row in data.locations.values()
                             if row.category == LocationCategory.HUB_SWITCH)
    return regions


def _expand_graph_parts(expanded: dict[str, Any], graph_parts: Mapping[str, Any] | None) -> None:
    references = expanded.pop("graph_parts", [])
    if not isinstance(references, list) or any(not isinstance(key, str) for key in references):
        raise ValueError("Graph part references must be a list of IDs")
    if len(references) != len(set(references)):
        raise ValueError("Duplicate graph part reference")
    for key in references:
        if graph_parts is None or key not in graph_parts:
            raise ValueError(f"Unknown traversal graph part: {key}")
        part = graph_parts[key]
        if part.get("version") != 1 or part.get("status") != "reviewed" or set(part) - {
            "version", "status", "nodes", "routes", "sources", "source_sets",
        }:
            raise ValueError(f"Unsupported traversal graph part: {key}")
        for field in ("nodes", "routes", "sources", "source_sets"):
            expanded.setdefault(field, []).extend(deepcopy(part.get(field, [])))


def compile_room_graph(
    payload: Mapping[str, Any], source_sets: Mapping[str, Any], *, area_keys: bool = False,
    graph_parts: Mapping[str, Any] | None = None, advanced: bool = False, require_inventory: bool = False,
) -> TraversalGraph:
    """Expand physical placements without changing their identity or retry policy."""
    expanded = deepcopy(dict(payload))
    _expand_graph_parts(expanded, graph_parts)
    sources = expanded.setdefault("sources", [])
    nodes = {node["id"]: node["native_room"] for node in expanded["nodes"]}
    for reference in expanded.pop("source_sets", ()):
        key, node = reference["id"], reference["node"]
        if key not in source_sets:
            raise ValueError(f"Unknown traversal source set: {key}")
        definition = source_sets[key]
        if "unavailable" in definition:
            reason = definition["unavailable"]
            if not isinstance(reason, str) or not reason.strip():
                raise ValueError(f"Unavailable source set {key} needs a concrete reason")
            expanded.setdefault("access", {})["unavailable"] = reason
        if nodes.get(node) != definition["native_room"]:
            raise ValueError(f"Source set {key} is not in its native room at {node}")
        for placement in definition["sources"]:
            source = {**placement, "node": node,
                      "items": sorted(set(definition.get("items", ())) | set(placement.get("items", ())))}
            if "retry_evidence" in reference:
                source["retry_evidence"] = reference["retry_evidence"]
            sources.append(source)
    physical_identities: dict[str, str] = {}
    identity_placements: dict[str, str] = {}
    prototype_instance_modes: dict[str, bool] = {}
    for source in sources:
        inventory_id = source.get("inventory_id")
        if inventory_id is not None:
            suffix = generation_instance_suffix(source)
            explicit = bool(suffix)
            if inventory_id in prototype_instance_modes and prototype_instance_modes[inventory_id] != explicit:
                raise ValueError("Generated prototype cannot mix implicit and explicit instances")
            prototype_instance_modes[inventory_id] = explicit
            physical_id = inventory_id + suffix
            identity = source.get("id") or physical_id
            if physical_id in physical_identities and physical_identities[physical_id] != identity:
                raise ValueError("One physical source cannot have multiple consumption identities")
            if identity in identity_placements and identity_placements[identity] != physical_id:
                raise ValueError("Different physical sources cannot share one consumption identity")
            identity_placements[identity] = physical_id
            physical_identities[physical_id] = identity
            source["id"] = identity
    expanded["sources"] = [resolve_inventory_source(source, nodes.get(source["node"]), advanced=advanced,
                                                      require_inventory=require_inventory)
                           for source in sources]
    if not advanced:
        encounter_keys = {source.key for source in ABILITY_SOURCES if source.kind == "boss_spawned"}
        if any(source["source_key"] in encounter_keys for source in expanded["sources"]):
            raise ValueError("Encounter-generated sources require an Advanced Logic graph")
    graph = compile_traversal_graph(expanded, area_keys=area_keys)
    if graph.access_region is not None and graph.access_region not in data.regions:
        raise ValueError(f"Unknown traversal access region: {graph.access_region}")
    return graph


def load_room_traversal(
    rooms: Mapping[str, Mapping[str, Any]], *, require_inventory: bool = False,
) -> tuple[tuple[dict[str, Any], ...], dict[str, Any], dict[str, Any]]:
    """Collect the shared schema and reject invalid or detached AP targets."""
    targets: list[dict[str, Any]] = []
    source_sets: dict[str, Any] = {}
    graph_parts: dict[str, Any] = {}
    seen: set[str] = set()
    for region, room in rooms.items():
        traversal = room.get("traversal", {})
        if not traversal:
            continue
        if traversal.get("version") != 1 or set(traversal) - {"version", "source_sets", "graph_parts", "targets"}:
            raise ValueError(f"Unsupported room traversal schema: {region}")
        for key, definition in traversal.get("graph_parts", {}).items():
            if key in graph_parts:
                raise ValueError(f"Duplicate traversal graph part: {key}")
            graph_parts[key] = definition
        for key, definition in traversal.get("source_sets", {}).items():
            if key in source_sets:
                raise ValueError(f"Duplicate traversal source set: {key}")
            if not definition.get("sources"):
                raise ValueError(f"Empty traversal source set: {key}")
            source_sets[key] = definition
        for record in traversal.get("targets", ()):
            row = {**record, "region": region}
            if row["id"] in seen:
                raise ValueError(f"Duplicate traversal target: {row['id']}")
            seen.add(row["id"])
            if row["kind"] not in {"mini", "peg", "wheel", "fuse", "rope", "block", "switch", "reinforced", "metal"}:
                raise ValueError(f"Unknown traversal target kind: {row['kind']}")
            _validate_target(row)
            targets.append(row)
    _validate_graph_parts(graph_parts, source_sets, require_inventory=require_inventory)
    for row in targets:
        _validate_graphs(row, source_sets, graph_parts, require_inventory=require_inventory)
    return tuple(targets), source_sets, graph_parts


def _validate_graph_parts(graph_parts: Mapping[str, Any], source_sets: Mapping[str, Any],
                          *, require_inventory: bool = False) -> None:
    for key, definition in graph_parts.items():
        if not definition.get("nodes"):
            raise ValueError(f"Empty traversal graph part: {key}")
        # Validate even unused fragments, without inventing an equipped start.
        compile_room_graph({
            "version": 1, "status": "reviewed", "nodes": [], "routes": [],
            "starts": [definition["nodes"][0]["id"]], "graph_parts": [key],
        }, source_sets, graph_parts=graph_parts, advanced=True, require_inventory=require_inventory)


def _validate_graphs(row: Mapping[str, Any], source_sets: Mapping[str, Any], graph_parts: Mapping[str, Any],
                     *, require_inventory: bool = False) -> None:
    if not row.get("graphs"):
        raise ValueError(f"Traversal target has no reviewed graphs: {row['id']}")
    advanced = row.get("advanced_graphs", [])
    if (not isinstance(advanced, list) or any(not isinstance(name, str) for name in advanced)
            or len(set(advanced)) != len(advanced) or any(name not in row["graphs"] for name in advanced)):
        raise ValueError(f"Invalid advanced traversal graph list: {row['id']}")
    for name, payload in row["graphs"].items():
        graph = compile_room_graph(payload, source_sets, graph_parts=graph_parts, advanced=name in advanced,
                                   require_inventory=require_inventory)
        from .master_source import CENTRAL_MASTER_SOURCE
        if any(source.source_key == CENTRAL_MASTER_SOURCE for source in graph.placements) and (
            row.get("id"), row.get("kind"), row.get("native_room"), row.get("region"), row.get("exit")
        ) != (
            "bomb_719_room13", "block", 719, "REGION_CARROT_CASTLE/ROOM_5_07",
            "REGION_CARROT_CASTLE/ROOM_5_13__LOGIC__ENTRY_FROM_5_07",
        ):
            raise ValueError("Central Master witness belongs only to the lower719 entry")
        if not graph.starts or not graph.required_targets:
            raise ValueError(f"Traversal target has no start or required target: {row['id']}")
        target_rooms = {node.room for node in graph.nodes if node.key in graph.required_targets}
        if target_rooms != {row["native_room"]}:
            raise ValueError(f"Traversal graph targets the wrong native room: {row['id']}")
        if any(node.room != row["native_room"] for node in graph.nodes) and graph.access_region is None:
            raise ValueError(f"Remote traversal witness needs independent access: {row['id']}")


def _validate_carrot_source_condition(row: Mapping[str, Any], condition: Any) -> Any:
    if condition == {"source_key": "WADDLE_DOO", "abilities": ["Beam", "Fighter", "Sword", "Fire"]}:
        if tuple(row.get(key) for key in ("id", "kind", "native_room", "region", "exit")) != (
            "bomb_719_room13", "block", 719, "REGION_CARROT_CASTLE/ROOM_5_07",
            "REGION_CARROT_CASTLE/ROOM_5_13__LOGIC__ENTRY_FROM_5_07",
        ):
            raise ValueError("Carrot source applicability belongs only to the reviewed Carrot entry")
        return None  # Validated here; never extend the chest source conditions.
    return condition


def _validate_new_connection(row: Mapping[str, Any]) -> None:
    if not isinstance(row.get("new_connection", False), bool):
        raise ValueError("new_connection must be a boolean")
    if row.get("new_connection") and (
        not row.get("exit") or row.get("requires_guaranteed_source") is not None
        or row.get("requires_any_guaranteed_source") is not None
        or row.get("required_for_generation", True)
    ):
        raise ValueError("New optional connections need unconditional rule installation, not target applicability")


def _validate_source_condition(condition: Any) -> None:
    """Narrow a partial witness to a native source policy, never invent a source."""
    sources = {source.key for source in ABILITY_SOURCES if source.can_be_swallowed}
    if (not isinstance(condition, dict) or set(condition) != {"source_key", "ability"}
            or not isinstance(condition["source_key"], str) or condition["source_key"] not in sources
            or not isinstance(condition["ability"], str) or condition["ability"] == "Normal"
            or condition["ability"] not in ABILITY_NAME_TO_ID):
        raise ValueError("Unsupported guaranteed-source applicability condition")


def _validate_target(row: Mapping[str, Any]) -> None:
    from .master_source import MASTER719_CAPABILITY
    if any(route.get("capability") == MASTER719_CAPABILITY
           for graph in row.get("graphs", {}).values() for route in graph.get("routes", ())) and (
        row.get("id"), row.get("kind"), row.get("native_room"), row.get("region"), row.get("exit")
    ) != (
        "bomb_719_room13", "block", 719, "REGION_CARROT_CASTLE/ROOM_5_07",
        "REGION_CARROT_CASTLE/ROOM_5_13__LOGIC__ENTRY_FROM_5_07",
    ):
        raise ValueError("Central Master belongs only to the reviewed Carrot entry")
    if any(route.get("capability") == "mirra_141_top_normal_puff"
           for graph in row.get("graphs", {}).values() for route in graph.get("routes", ())) and (
            row.get("id"), row.get("kind"), row.get("native_room"), row.get("region"), row.get("exit")) != (
            "mirra_141_top_mustard", "block", 141,
            "REGION_RAINBOW_ROUTE/ROOM_1_41__LOGIC__TOP_MUSTARD",
            "REGION_MUSTARD_MOUNTAIN/ROOM_4_07"):
        raise ValueError("Mirra141 Normal clearance belongs only to the top Mustard exit")
    if any(route.get("capability") == "mirra_141_east_normal_puff"
           for graph in row.get("graphs", {}).values() for route in graph.get("routes", ())) and (
            row.get("id"), row.get("kind"), row.get("native_room"), row.get("region"), row.get("exit")) != (
            "mirra_141_east_moonlight", "block", 141,
            "REGION_RAINBOW_ROUTE/ROOM_1_41__LOGIC__EAST_MOONLIGHT",
            "REGION_MOONLIGHT_MANSION/ROOM_2_16"):
        raise ValueError("Mirra141 Normal clearance belongs only to the east Moonlight exit")
    if any(route.get("capability", "").startswith("mirra_117_")
           for graph in row.get("graphs", {}).values() for route in graph.get("routes", ())) and (
            row.get("id"), row.get("kind"), row.get("native_room"), row.get("region"), row.get("exit")) != (
            "mirra_117_carrot", "block", 117, "REGION_RAINBOW_ROUTE/ROOM_1_24",
            "REGION_CARROT_CASTLE/ROOM_5_02"):
        raise ValueError("Mirra117 Normal clearance belongs only to the Carrot exit")
    if row.get("id") == "mirra_117_carrot":
        for graph in row.get("graphs", {}).values():
            if graph.get("access") != {"region": "REGION_RAINBOW_ROUTE/ROOM_1_HUB_3"}:
                raise ValueError("Mirra117 requires independent native192 access")
            if [(source.get("id"), source.get("inventory_id"), source.get("node"))
                for source in graph.get("sources", ())] != [
                    ("0x088B9904", "room:117/template:0x088B9904", "mirra_117_carrot:arrival"),
                    ("0x088B9874", "room:117/template:0x088B9874", "mirra_117_carrot:ladder")]:
                raise ValueError("Mirra117 requires its original two finite payloads")
    _validate_new_connection(row)
    if not isinstance(row.get("fail_closed", False), bool):
        raise ValueError("fail_closed must be a boolean")
    if row.get("fail_closed") and not row.get("exit"):
        raise ValueError("fail_closed requires an exit target")
    condition = row.get("requires_guaranteed_source")
    alternatives = row.get("requires_any_guaranteed_source")
    if "requires_any_guaranteed_source" in row:
        if "requires_guaranteed_source" in row:
            raise ValueError("Guaranteed-source conditions are mutually exclusive")
        scoped_alternatives = (
            ([{"source_key": "SPARKY", "ability": "Spark"},
              {"source_key": "SWORD_KNIGHT", "ability": "Sword"}],
             ("bomb_110_room9", "block", 110, "REGION_RAINBOW_ROUTE/ROOM_1_08",
              "REGION_RAINBOW_ROUTE/ROOM_1_09", None)),
            ([{"source_key": "TWISTER", "abilities": ["UFO", "Crash", "Cupid", "Cutter"]},
              {"source_key": "SIR_KIBBLE", "ability": "Cutter"}],
             ("switch_310_mustard_map", "switch", 310, "REGION_MUSTARD_MOUNTAIN/ROOM_4_CHEST",
              None, "MAJOR_CHEST_MUSTARD_MOUNTAIN")),
        )
        if not any(alternatives == expected and tuple(row.get(key) for key in (
                "id", "kind", "native_room", "region", "exit", "location")) == target
                   for expected, target in scoped_alternatives):
            raise ValueError("Unsupported target-specific guaranteed-source alternatives; reviewed chest target only")
    # These selective carry proofs may not spread to another source or surface.
    scoped_conditions = (
        ({"source_key": "TWISTER", "abilities": ["UFO", "Crash", "Cupid", "Cutter"]}, (
            "switch_310_mustard_map", "switch", 310, "REGION_MUSTARD_MOUNTAIN/ROOM_4_CHEST",
            "MAJOR_CHEST_MUSTARD_MOUNTAIN",
        )),
        ({"source_key": "WADDLE_DOO",
          "abilities": ["Beam", "Smash", "Fire", "Missile", "Parasol", "Spark", "Ice", "Sword", "Fighter", "UFO"]}, (
            "bomb_517_chocolate", "block", 517, "REGION_CABBAGE_CAVERN/ROOM_3_06",
            "MINOR_CHEST_SPRAY_PAINT_12",
        )),
        ({"source_key": "SPARKY", "ability": "UFO"}, (
            "bomb_733_yellow", "block", 733, "REGION_CARROT_CASTLE/ROOM_5_16",
            "MINOR_CHEST_SPRAY_PAINT_02",
        )),
    )
    condition = _validate_carrot_source_condition(row, condition)
    condition = _validate_mustard_source_condition(row, condition)
    scoped_target = next((target for supported, target in scoped_conditions if condition == supported), None)
    if scoped_target is not None:
        if tuple(row.get(key) for key in ("id", "kind", "native_room", "region", "location")) != scoped_target:
            raise ValueError("Target-specific source applicability belongs only to its reviewed chest target")
    elif condition is not None:
        _validate_source_condition(condition)
    if not isinstance(row.get("required_for_generation", True), bool):
        raise ValueError("required_for_generation must be a boolean")
    if not row.get("required_for_generation", True) and not row.get("optional_route_evidence"):
        raise ValueError("Optional traversal route needs independent bypass evidence")
    region = data.regions.get(row["region"])
    if region is None:
        raise ValueError(f"Unknown traversal owner: {row['region']}")
    exit_name, location = row.get("exit"), row.get("location")
    if bool(exit_name) == bool(location):
        raise ValueError("Traversal target must name exactly one exit or location")
    if exit_name and exit_name not in region.exits:
        raise ValueError(f"Traversal target is not an exit of its owner: {exit_name}")
    if location and location not in region.locations:
        raise ValueError(f"Traversal target is not a location of its owner: {location}")


def _validate_mustard_source_condition(row: Mapping[str, Any], condition: Any) -> Any:
    if condition == {"source_key": "FOLEY", "abilities": ["Bomb", "UFO", "Crash", "Magic", "Ice"]}:
        if tuple(row.get(key) for key in ("id", "kind", "native_room", "region", "exit")) != (
            "switch_533_room16", "switch", 533, "REGION_MUSTARD_MOUNTAIN/ROOM_4_15",
            "REGION_MUSTARD_MOUNTAIN/ROOM_4_16",
        ):
            raise ValueError("Foley source applicability belongs only to the reviewed Room16 exit")
        return None
    return condition


@lru_cache(maxsize=1)
def _room_catalog() -> tuple[tuple[dict[str, Any], ...], dict[str, Any], dict[str, Any]]:
    return load_room_traversal({name: {"traversal": region.traversal} for name, region in data.regions.items()},
                               require_inventory=True)


def room_traversal_targets(kind: str) -> tuple[dict[str, Any], ...]:
    return tuple(row for row in _room_catalog()[0] if row["kind"] == kind)


@lru_cache(maxsize=None)
def room_traversal_graph(target_id: str, witness: str, area_keys: bool = False) -> TraversalGraph:
    targets, source_sets, graph_parts = _room_catalog()
    row = next(row for row in targets if row["id"] == target_id)
    return compile_room_graph(row["graphs"][witness], source_sets, area_keys=area_keys, graph_parts=graph_parts,
                              advanced=witness in row.get("advanced_graphs", ()), require_inventory=True)
