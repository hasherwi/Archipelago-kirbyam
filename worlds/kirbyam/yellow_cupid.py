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

from .special_route_data import SPECIAL_ROUTE_PROFILES
from .traversal import SourcePolicy, TraversalGraph, compile_traversal_graph

_PROFILE = SPECIAL_ROUTE_PROFILES["carrot_yellow_cupid"]
TARGET = _PROFILE["target"]
LOCATION = _PROFILE["check"]
OWNER = _PROFILE["target_region"]
SOURCE_REGION = _PROFILE["source_region"]
POLICY_SHA256 = _PROFILE["policy_sha256"]
PROFILE = _PROFILE["fixture_options"]

# Player health is recorded for the fixture; it does not qualify the route.
_ROUTE_PROFILE = {name: value for name, value in PROFILE.items()
                  if name not in _PROFILE["fixture_only_options"]}


def validate_profile(world: Any, *, install: bool = False) -> bool:
    """Refuse stale installed rules before validation, slot or ROM publication."""
    options = getattr(world, "options", None)
    values = tuple(getattr(option, "value", option) for name in _ROUTE_PROFILE
                   for option in (getattr(options, name, None),))
    raw = getattr(world, "_enemy_copy_ability_policy", None)
    serialized = json.dumps(raw, sort_keys=True, separators=(",", ":"))
    signature = (tuple((type(value).__name__, value) for value in values), serialized)
    source = _PROFILE["guaranteed_source"]
    qualified = (bool(getattr(world, "ENABLE_MINOR_CHESTS", False))
                 and all(type(value) is int and value in ((0, 1) if name in _PROFILE["any_boolean_options"] else (expected,))
                         for name, value, expected in zip(_ROUTE_PROFILE, values, _ROUTE_PROFILE.values()))
                 and hashlib.sha256(serialized.encode()).hexdigest() == POLICY_SHA256
                 and SourcePolicy(raw).grant(source["source_key"], lambda _: True).guaranteed == frozenset({source["ability"]}))
    installed = getattr(world, "_yellow_cupid_signature", None)
    if installed is not None and (installed[0] or qualified) and installed != (qualified, signature):
        raise ValueError("Yellow Cupid profile changed after rule installation")
    if install:
        world._yellow_cupid_signature = (qualified, signature)
    return qualified



@lru_cache(maxsize=1)
def graph() -> TraversalGraph:
    payload = _PROFILE["witness"]
    if not isinstance(payload, dict):
        raise ValueError("Yellow Cupid witness must be an object")
    return compile_traversal_graph(payload)


def target_graphs(world: Any, row: dict[str, Any]) -> tuple[TraversalGraph, ...]:
    """Join the existing target's OR witnesses, never install another AND gate."""
    if (row.get("id"), row.get("region"), row.get("native_room"), row.get("location")) != (
        TARGET, OWNER, _PROFILE["native_room"], LOCATION
    ) or row.get("exit") or not validate_profile(world):
        return ()
    return (graph(),)
