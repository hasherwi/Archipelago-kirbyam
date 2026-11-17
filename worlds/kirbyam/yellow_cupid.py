"""Exact-profile Yellow Paint witness; no generic Cupid or Phone grant.

The source-policy digest deliberately pins the complete demonstrated assignment,
not merely its Sparky result. Other profiles retain their existing rules. See
dev-docs/carrot-yellow-cupid-admission.md for the native evidence and limits.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
from typing import Any

from .data import load_json_data
from .traversal import SourcePolicy, TraversalGraph, compile_traversal_graph

TARGET = "bomb_733_yellow"
LOCATION = "MINOR_CHEST_SPRAY_PAINT_02"
OWNER = "REGION_CARROT_CASTLE/ROOM_5_16"
SOURCE_REGION = "REGION_CARROT_CASTLE/ROOM_5_14"
POLICY_SHA256 = "1b5321f57d0ed75ed938aaeda8889ab5c9d5439a3cac7c6df5a5b634bdb21ac0"
PROFILE = {
    "ability_randomization_mode": 1, "ability_gating": 0,
    "ability_randomization_statues": 0, "minimum_health": 6,
    "maximum_health": 6, "enemy_health_multiplier": 100,
    "one_hit_mode": 0, "area_keys": 0, "room_sanity": 1,
    "advanced_logic": 0,
}


def validate_profile(world: Any, *, install: bool = False) -> bool:
    """Refuse stale installed rules before validation, slot or ROM publication."""
    options = getattr(world, "options", None)
    values = tuple(getattr(option, "value", option) for name in PROFILE
                   for option in (getattr(options, name, None),))
    raw = getattr(world, "_enemy_copy_ability_policy", None)
    serialized = json.dumps(raw, sort_keys=True, separators=(",", ":"))
    signature = (tuple((type(value).__name__, value) for value in values), serialized)
    qualified = (bool(getattr(world, "ENABLE_MINOR_CHESTS", False))
                 and all(type(value) is int and value in ((0, 1) if name in ("room_sanity", "ability_gating") else (expected,))
                         for name, value, expected in zip(PROFILE, values, PROFILE.values()))
                 and hashlib.sha256(serialized.encode()).hexdigest() == POLICY_SHA256
                 and SourcePolicy(raw).grant("SPARKY", lambda _: True).guaranteed == frozenset({"Cupid"}))
    installed = getattr(world, "_yellow_cupid_signature", None)
    if installed is not None and (installed[0] or qualified) and installed != (qualified, signature):
        raise ValueError("Yellow Cupid profile changed after rule installation")
    if install:
        world._yellow_cupid_signature = (qualified, signature)
    return qualified



@lru_cache(maxsize=1)
def graph() -> TraversalGraph:
    payload = load_json_data("yellow_cupid_witness.json")
    if not isinstance(payload, dict):
        raise ValueError("Yellow Cupid witness must be an object")
    return compile_traversal_graph(payload)


def target_graphs(world: Any, row: dict[str, Any]) -> tuple[TraversalGraph, ...]:
    """Join the existing target's OR witnesses, never install another AND gate."""
    if (row.get("id"), row.get("region"), row.get("native_room"), row.get("location")) != (
        TARGET, OWNER, 733, LOCATION
    ) or row.get("exit") or not validate_profile(world):
        return ()
    return (graph(),)
