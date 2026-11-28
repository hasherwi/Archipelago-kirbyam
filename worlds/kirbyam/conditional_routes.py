"""Shared evaluator for conditional witnesses declared on exact room targets."""

from functools import lru_cache
import hashlib
import json
from typing import Any

from .traversal import SourcePolicy, TraversalGraph, compile_traversal_graph
from .traversal_data import _room_catalog


def _guaranteed(policy: SourcePolicy, source: dict[str, str]) -> bool:
    return policy.grant(source["source_key"], lambda _: True).guaranteed == frozenset({source["ability"]})


@lru_cache(maxsize=None)
def contract(name: str) -> tuple[dict[str, Any], dict[str, Any]]:
    entries = [(row, profile) for row in _room_catalog()[0]
               for profile in row.get("conditional_routes", ()) if profile["contract"] == name]
    if len(entries) != 1:
        raise ValueError(f"Expected one room target for traversal contract: {name}")
    return entries[0]


def activate(name: str, raw: dict[str, Any], *, minor_chests: bool) -> bool:
    """Select a generation contract; the caller owns any persisted/native effect."""
    from .data import data
    from .traversal_rules import target_applies

    row, profile = contract(name)
    condition = profile["activation"]
    if condition.get("physical_minor_check") and (
        not minor_chests or data.locations[row["location"]].source_rom_offset is None
    ):
        return False
    return condition.get("reviewed_source") != "missing" or not target_applies(row, SourcePolicy(raw))


def policy_with_contract(name: str, raw: dict[str, Any], *, runtime_key: str) -> dict[str, Any]:
    condition = contract(name)[1]["activation"]
    if set(condition["source_policy_values"]) != {runtime_key}:
        raise ValueError(f"Unexpected runtime key for traversal contract: {name}")
    if raw.get("mode") != condition["source_policy_mode"]:
        return raw
    return {**raw, **condition["source_policy_values"]}


def policy_has_contract(name: str, policy: SourcePolicy) -> bool:
    condition = contract(name)[1]["activation"]
    return (policy.mode == condition["source_policy_mode"]
            and all(type(policy.policy.get(key)) is type(value) and policy.policy[key] == value
                    for key, value in condition["source_policy_values"].items()))


def signed_world_profile(name: str, world: Any) -> tuple[bool, tuple]:
    """Match an exact witnessed slot without accepting a mixed/partial match."""
    condition = contract(name)[1]["activation"]
    options = getattr(world, "options", None)
    expected = {key: value for key, value in condition["fixture_options"].items()
                if key not in condition["fixture_only_options"]}
    values = tuple(getattr(option, "value", option) for key in expected
                   for option in (getattr(options, key, None),))
    raw = getattr(world, "_enemy_copy_ability_policy", None)
    serialized = json.dumps(raw, sort_keys=True, separators=(",", ":"))
    signature = (tuple((type(value).__name__, value) for value in values), serialized)
    qualified = (bool(getattr(world, "ENABLE_MINOR_CHESTS", False))
                 and all(type(value) is int and value in ((0, 1) if key in condition["any_boolean_options"] else (item,))
                         for key, value, item in zip(expected, values, expected.values()))
                 and hashlib.sha256(serialized.encode()).hexdigest() == condition["policy_sha256"]
                 and _guaranteed(SourcePolicy(raw), condition["guaranteed_source"]))
    return qualified, signature


@lru_cache(maxsize=None)
def graph(name: str, index: int = 0) -> TraversalGraph:
    return compile_traversal_graph(contract(name)[1]["witnesses"][index]["graph"])


def matches_target(name: str, row: dict[str, Any]) -> bool:
    owner, _ = contract(name)
    fields = ("id", "region", "native_room", "location", "exit")
    return row.get("id") == owner["id"] and all(
        row[field] == owner.get(field) for field in fields if field in row
    )


def active_graphs(row: dict[str, Any], active: frozenset[str], policy: SourcePolicy) -> tuple[TraversalGraph, ...]:
    return tuple(graph(name, index)
                 for name in sorted(active) if matches_target(name, row)
                 for index, witness in enumerate(contract(name)[1]["witnesses"])
                 if "guaranteed_source" not in witness or _guaranteed(policy, witness["guaranteed_source"]))


class CandyFuseContract:
    """Fixed Candy ROM marker and historical slot codec; route logic is room data."""

    CONTRACT = "candy_9_12_linked_fuse"
    TARGET = "bomb_402_candy_chest"
    LOCATION = "MINOR_CHEST_CANDY_CONSTELLATION_9_12"
    SLOT_KEY = "candy912_linked_west_fuse"
    ROM_OFFSET = 0x1006FF8
    STOCK_CONFIG = b"\x00" b"19C"
    LINKED_CONFIG = b"\x01" b"19C"

    @staticmethod
    def needs_linked_fuse(raw: dict[str, Any], *, minor_chests: bool) -> bool:
        return activate(CandyFuseContract.CONTRACT, raw, minor_chests=minor_chests)

    @classmethod
    def enabled(cls, slot_data: dict[str, Any]) -> bool:
        """Missing intent is stock for seeds prepared before this patch."""
        if cls.SLOT_KEY in slot_data and slot_data[cls.SLOT_KEY] is not True:
            raise ValueError("Invalid Candy 9-12 linked fuse patch contract")
        return slot_data.get(cls.SLOT_KEY) is True

    @classmethod
    def config_bytes(cls, linked: bool) -> bytes:
        return cls.LINKED_CONFIG if linked else cls.STOCK_CONFIG

    @staticmethod
    def graph() -> TraversalGraph:
        return graph(CandyFuseContract.CONTRACT, 0)

    @staticmethod
    def fire_graph() -> TraversalGraph:
        return graph(CandyFuseContract.CONTRACT, 1)

    @staticmethod
    def target_graphs(row: dict[str, Any], linked: bool, policy: SourcePolicy) -> tuple[TraversalGraph, ...]:
        return active_graphs(row, frozenset({CandyFuseContract.CONTRACT}) if linked else frozenset(), policy)


CANDY_FUSE = CandyFuseContract()
