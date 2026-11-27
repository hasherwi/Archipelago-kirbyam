"""Validated generation-only item policy. Runtime receipts are not defined here."""
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from BaseClasses import ItemClassification

from .data import LocationCategory, data, load_json_data
from .narcolepsy import NARCOLEPSY_TRAP_CATALOG_VERSION
from .random_teleport import TRAP_CATALOG_VERSION


@dataclass(frozen=True)
class ItemPoolPolicy:
    weighted_filler: tuple[tuple[int, int], ...]
    filler_exclusions: Mapping[str, frozenset[int]]
    trap_exclusions: Mapping[str, frozenset[int]]
    trap_catalog_introduced_in: Mapping[int, int]
    pool_exclusions: Mapping[str, frozenset[int]]
    vanilla_boss_shards: tuple[tuple[str, int], ...]

    @property
    def filler_labels(self) -> tuple[str, ...]:
        return tuple(data.items[code].label for code, _ in self.weighted_filler)

    @property
    def filler_weights_by_label(self) -> dict[str, int]:
        return {data.items[code].label: weight for code, weight in self.weighted_filler}

    @property
    def shard_codes(self) -> tuple[int, ...]:
        return tuple(code for _, code in self.vanilla_boss_shards)

    @property
    def shard_labels(self) -> tuple[str, ...]:
        return tuple(data.items[code].label for code in self.shard_codes)

    @property
    def weighted_item_codes(self) -> frozenset[int]:
        return frozenset(code for code, _ in self.weighted_filler) | frozenset(
            code for code, item in data.items.items() if item.classification == ItemClassification.trap
        )

    def filler_for(self, *, maximum_health_is_one: bool,
                   no_extra_lives: bool) -> tuple[tuple[str, ...], tuple[int, ...]]:
        excluded = self._active_exclusions(
            self.filler_exclusions, maximum_health_is_one=maximum_health_is_one, no_extra_lives=no_extra_lives,
        )
        candidates = tuple((data.items[code].label, weight) for code, weight in self.weighted_filler
                           if code not in excluded)
        if not candidates:
            raise ValueError("KirbyAM active filler pool resolved empty")
        return tuple(label for label, _ in candidates), tuple(weight for _, weight in candidates)

    def traps_for(self, *, minimum_health_is_one: bool, no_extra_lives: bool,
                  catalog_version: int, player_excluded_labels: set[str]) -> tuple[str, ...]:
        excluded = self._active_exclusions(
            self.trap_exclusions, minimum_health_is_one=minimum_health_is_one, no_extra_lives=no_extra_lives,
        ) | {code for code, introduced in self.trap_catalog_introduced_in.items() if catalog_version < introduced}
        # Keep catalog order and the established option's external label representation.
        return tuple(item.label for code, item in data.items.items()
                     if item.classification == ItemClassification.trap and code not in excluded
                     and item.label not in player_excluded_labels)

    @staticmethod
    def _active_exclusions(exclusions: Mapping[str, frozenset[int]], **active: bool) -> frozenset[int]:
        return frozenset(code for condition, applies in active.items() if applies for code in exclusions[condition])


def _item_id(key: object) -> int:
    if not isinstance(key, str) or key not in data.item_key_to_id:
        raise ValueError(f"Item pool policy references unknown item key {key!r}")
    return data.item_key_to_id[key]


def _exclusions(raw: object, fields: set[str], valid_ids: set[int] | frozenset[int], *,
                group_tags: Mapping[str, str] | None = None) -> Mapping[str, frozenset[int]]:
    if not isinstance(raw, dict) or raw.keys() != fields:
        raise ValueError(f"Item pool policy must define exclusions for {sorted(fields)}")
    result: dict[str, frozenset[int]] = {}
    for condition, selector in raw.items():
        group_tag = group_tags.get(condition) if group_tags is not None else None
        if group_tag is not None:
            if selector != {"tag": group_tag}:
                raise ValueError(f"Item pool exclusion {condition!r} must select the {group_tag!r} tag")
            codes = frozenset(code for code, item in data.items.items() if group_tag in item.tags)
        elif isinstance(selector, list) and selector:
            codes = frozenset(map(_item_id, selector))
            if len(codes) != len(selector):
                raise ValueError(f"Item pool exclusion {condition!r} contains duplicate item keys")
        else:
            raise ValueError(f"Item pool exclusion {condition!r} must list at least one item key")
        if not codes or not codes <= valid_ids:
            raise ValueError(f"Item pool exclusion {condition!r} contains no or ineligible items")
        result[condition] = codes
    return MappingProxyType(result)


def parse_item_pool_policy(raw: object) -> ItemPoolPolicy:
    if not isinstance(raw, dict) or type(raw.get("schema")) is not int or raw["schema"] != 1 or raw.keys() != {
        "schema", "weighted_filler", "filler_exclusions", "trap_exclusions", "trap_catalog_introduced_in",
        "pool_exclusions", "vanilla_boss_shards",
    }:
        raise ValueError("Unsupported KirbyAM item pool policy")

    weighted_filler: list[tuple[int, int]] = []
    filler = raw["weighted_filler"]
    if not isinstance(filler, list):
        raise ValueError("Weighted filler policy must be an ordered list")
    for row in filler:
        if (not isinstance(row, dict) or row.keys() != {"item", "weight"}
                or type(row["weight"]) is not int or row["weight"] <= 0):
            raise ValueError("Weighted filler policy must define a positive integer weight for each item")
        weighted_filler.append((_item_id(row["item"]), row["weight"]))
    filler_ids = {code for code, item in data.items.items() if "Filler" in item.tags}
    if len(weighted_filler) != len(filler_ids) or {code for code, _ in weighted_filler} != filler_ids:
        raise ValueError("Weighted filler policy must cover every Filler-tagged item exactly once")

    trap_ids = {code for code, item in data.items.items() if item.classification == ItemClassification.trap}
    raw_versions = raw["trap_catalog_introduced_in"]
    if not isinstance(raw_versions, dict):
        raise ValueError("Trap catalog introduction policy must be an item-key map")
    trap_versions = {_item_id(key): since for key, since in raw_versions.items()}
    if not trap_versions.keys() <= trap_ids or any(
        type(since) is not int or since <= 0 for since in trap_versions.values()
    ):
        raise ValueError("Trap catalog introduction policy must bind trap items to a positive catalog version")

    published_versions = {
        _item_id("TRAP_NARCOLEPSY"): NARCOLEPSY_TRAP_CATALOG_VERSION,
        _item_id("TRAP_RANDOM_TELEPORT"): TRAP_CATALOG_VERSION,
    }
    if trap_versions != published_versions:
        raise ValueError("Trap introduction policy disagrees with published tracker versions")

    bosses = {key for key, location in data.locations.items() if location.category == LocationCategory.BOSS_DEFEAT}
    shard_ids = {code for code, item in data.items.items()
                 if "Shards" in item.tags and item.classification == ItemClassification.progression}
    bindings: list[tuple[str, int]] = []
    if not isinstance(raw["vanilla_boss_shards"], list):
        raise ValueError("Vanilla boss-shard policy must be an ordered list")
    for row in raw["vanilla_boss_shards"]:
        if (not isinstance(row, dict) or row.keys() != {"check", "item"}
                or not isinstance(row["check"], str) or row["check"] not in bosses):
            raise ValueError("Vanilla shard binding must use a boss-defeat check key")
        bindings.append((row["check"], _item_id(row["item"])))
    if (len(bindings) != len(bosses) or len(bindings) != len(shard_ids)
            or {check for check, _ in bindings} != bosses or {code for _, code in bindings} != shard_ids):
        raise ValueError("Vanilla shard policy must bind every boss check and shard exactly once")

    filler_exclusions = _exclusions(raw["filler_exclusions"], {"maximum_health_is_one", "no_extra_lives"}, filler_ids)
    if filler_ids <= set().union(*filler_exclusions.values()):
        raise ValueError("Automatic exclusions must leave at least one filler item")
    trap_exclusions = _exclusions(raw["trap_exclusions"], {"minimum_health_is_one", "no_extra_lives"}, trap_ids)
    pool_group_tags = {"start_with_all_maps": "Maps", "area_keys_off": "AreaKeys", "ability_gating_off": "Abilities"}
    pool_exclusions = _exclusions(
        raw["pool_exclusions"], {"always", "random_starting_mirror_off", *pool_group_tags},
        set(data.items) - filler_ids - trap_ids, group_tags=pool_group_tags,
    )

    return ItemPoolPolicy(tuple(weighted_filler), filler_exclusions, trap_exclusions,
                          MappingProxyType(trap_versions), pool_exclusions, tuple(bindings))


ITEM_POOL_POLICY = parse_item_pool_policy(load_json_data("item_pool_policy.json"))
