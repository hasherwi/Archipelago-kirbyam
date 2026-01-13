from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict, NotRequired, Optional, Literal, List, Dict, Any, cast

try:
    import yaml  # type: ignore[import]
except Exception:
    import json as _json

    class _YamlFallback:
        @staticmethod
        def safe_load(s):
            # Fallback: parse JSON when PyYAML isn't available (keeps runtime behavior predictable).
            return _json.loads(s)

    yaml = _YamlFallback()


Locale = Literal["na", "eu", "jp", "vc"]


class AddressMap(TypedDict, total=False):
    na: Optional[int]
    eu: Optional[int]
    jp: Optional[int]
    vc: Optional[int]


class ItemRow(TypedDict):
    key: str
    name: str
    classification: NotRequired[str]
    addresses: NotRequired[AddressMap]
    tags: NotRequired[list[str]]


class LocationRow(TypedDict, total=False):
    key: str
    name: str
    addresses: NotRequired[AddressMap]
    tags: NotRequired[list[str]]


class GoalRow(TypedDict, total=False):
    key: str
    name: str
    addresses: NotRequired[AddressMap]
    tags: NotRequired[list[str]]


@dataclass(frozen=True)
class KirbyAMData:
    schema_version: int
    items: List[ItemRow]
    locations: List[LocationRow]
    goals: List[GoalRow]


def _world_data_dir() -> Path:
    # worlds/kirbyam/data_loader.py -> worlds/kirbyam/data/
    return Path(__file__).resolve().parent / "data"


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing data file: {path}")

    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise ValueError(f"Empty YAML file: {path}")

    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise TypeError(f"YAML root must be a mapping in {path}, got: {type(data).__name__}")

    return data


def _require_int(data: Dict[str, Any], key: str, path: Path) -> int:
    value = data.get(key)
    if not isinstance(value, int):
        raise TypeError(f"{path}: '{key}' must be an int, got {type(value).__name__}")
    return value


def _require_list_of_mappings(data: Dict[str, Any], key: str, path: Path) -> List[Dict[str, Any]]:
    value = data.get(key)
    if not isinstance(value, list):
        raise TypeError(f"{path}: '{key}' must be a list, got {type(value).__name__}")
    for i, entry in enumerate(value):
        if not isinstance(entry, dict):
            raise TypeError(f"{path}: '{key}[{i}]' must be a mapping, got {type(entry).__name__}")
    return value  # type: ignore[return-value]


def _require_non_empty_str(entry: Dict[str, Any], field: str, path: Path, idx: int, list_name: str) -> str:
    value = entry.get(field)
    if not isinstance(value, str) or not value.strip():
        raise TypeError(f"{path}: '{list_name}[{idx}].{field}' must be a non-empty string")
    return value.strip()


def _validate_unique_keys(entries: List[Dict[str, Any]], path: Path, list_name: str) -> None:
    seen: set[str] = set()
    for idx, entry in enumerate(entries):
        k = _require_non_empty_str(entry, "key", path, idx, list_name)
        if k in seen:
            raise ValueError(f"{path}: duplicate key '{k}' in '{list_name}'")
        seen.add(k)


def _validate_addresses(entry: Dict[str, Any], path: Path, idx: int, list_name: str) -> None:
    """
    addresses is optional. If present, it must be a mapping.
    Each locale key (na/eu/jp/vc) must be int or null (None).
    """
    if "addresses" not in entry:
        return

    addresses = entry.get("addresses")
    if addresses is None:
        return

    if not isinstance(addresses, dict):
        raise TypeError(f"{path}: '{list_name}[{idx}].addresses' must be a mapping")

    for locale in ("na", "eu", "jp", "vc"):
        if locale not in addresses:
            continue
        v = addresses[locale]
        if v is None:
            continue
        if not isinstance(v, int):
            raise TypeError(f"{path}: '{list_name}[{idx}].addresses.{locale}' must be int or null")


def load_kirbyam_data() -> KirbyAMData:
    """
    Load canonical YAML datasets for Kirby & The Amazing Mirror.

    Expected files:
      - worlds/kirbyam/data/items.yaml
      - worlds/kirbyam/data/locations.yaml
      - worlds/kirbyam/data/goals.yaml

    Notes fields (e.g., logic_notes/dev_notes/value_notes) may exist in YAML and are ignored by this loader.
    """
    base = _world_data_dir()

    items_path = base / "items.yaml"
    locations_path = base / "locations.yaml"
    goals_path = base / "goals.yaml"

    items_raw = _load_yaml(items_path)
    locations_raw = _load_yaml(locations_path)
    goals_raw = _load_yaml(goals_path)

    # Require schema_version and ensure it matches across files.
    items_schema = _require_int(items_raw, "schema_version", items_path)
    locations_schema = _require_int(locations_raw, "schema_version", locations_path)
    goals_schema = _require_int(goals_raw, "schema_version", goals_path)

    if not (items_schema == locations_schema == goals_schema):
        raise ValueError(
            "Schema version mismatch across data files: "
            f"items={items_schema}, locations={locations_schema}, goals={goals_schema}"
        )

    items = _require_list_of_mappings(items_raw, "items", items_path)
    locations = _require_list_of_mappings(locations_raw, "locations", locations_path)
    goals = _require_list_of_mappings(goals_raw, "goals", goals_path)

    # Uniqueness and minimal required fields.
    _validate_unique_keys(items, items_path, "items")
    _validate_unique_keys(locations, locations_path, "locations")
    _validate_unique_keys(goals, goals_path, "goals")

    for idx, entry in enumerate(items):
        _require_non_empty_str(entry, "name", items_path, idx, "items")
        _validate_addresses(entry, items_path, idx, "items")

    for idx, entry in enumerate(locations):
        _require_non_empty_str(entry, "name", locations_path, idx, "locations")
        _validate_addresses(entry, locations_path, idx, "locations")

    for idx, entry in enumerate(goals):
        _require_non_empty_str(entry, "name", goals_path, idx, "goals")
        _validate_addresses(entry, goals_path, idx, "goals")

    return KirbyAMData(
        schema_version=items_schema,
        items=cast(List[ItemRow], items),
        locations=cast(List[LocationRow], locations),
        goals=cast(List[GoalRow], goals)
    )
