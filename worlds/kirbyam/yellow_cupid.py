"""Exact-profile Yellow Paint witness; no generic Cupid or Phone grant.

The source-policy digest deliberately pins the complete demonstrated assignment,
not merely its Sparky result. Other profiles retain their existing rules. See
dev-docs/carrot-yellow-cupid-admission.md for the native evidence and limits.
"""
from __future__ import annotations

from typing import Any

from . import conditional_routes
from .traversal import SourcePolicy, TraversalGraph

CONTRACT = "carrot_yellow_cupid"
_TARGET, _AUTHORED = conditional_routes.contract(CONTRACT)
TARGET = _TARGET["id"]
LOCATION = _TARGET["location"]
OWNER = _TARGET["region"]
SOURCE_REGION = _AUTHORED["activation"]["source_region"]
POLICY_SHA256 = _AUTHORED["activation"]["policy_sha256"]
PROFILE = _AUTHORED["activation"]["fixture_options"]


def validate_profile(world: Any, *, install: bool = False) -> bool:
    """Refuse stale installed rules before validation, slot or ROM publication."""
    qualified, signature = conditional_routes.signed_world_profile(CONTRACT, world)
    installed = getattr(world, "_yellow_cupid_signature", None)
    if installed is not None and (installed[0] or qualified) and installed != (qualified, signature):
        raise ValueError("Yellow Cupid profile changed after rule installation")
    if install:
        world._yellow_cupid_signature = (qualified, signature)
    return qualified



def graph() -> TraversalGraph:
    return conditional_routes.graph(CONTRACT)


def target_graphs(world: Any, row: dict[str, Any]) -> tuple[TraversalGraph, ...]:
    """Join the existing target's OR witnesses, never install another AND gate."""
    if not conditional_routes.matches_target(CONTRACT, row):
        return ()
    if not validate_profile(world):
        return ()
    return conditional_routes.active_graphs(row, frozenset({CONTRACT}), SourcePolicy(world._enemy_copy_ability_policy))
