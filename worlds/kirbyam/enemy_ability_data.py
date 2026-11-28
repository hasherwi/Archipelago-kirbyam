"""Shared JSON-backed enemy copy-ability data for KirbyAM."""

from __future__ import annotations

import json
import pkgutil
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AbilitySource:
    key: str
    addresses: tuple[int, ...]
    default_ability_name: str
    default_ability_id: int
    kind: str  # enemy | miniboss | boss_spawned
    can_be_swallowed: bool = True


@dataclass(frozen=True)
class EncounterParentCopyAudit:
    """Native parent only; this is not an accessible source or a ROM patch row."""

    native_types: tuple[tuple[int, str], ...]
    swallow_status: str  # swallowable | not_swallowable | unknown
    vanilla_copy: str | None  # "Normal" is a genuine swallow with no copy ability.
    when: str | None  # ordinary | after_defeat
    evidence: str


@dataclass(frozen=True)
class EncounterOutputCopyAudit:
    """What a generated native object can yield, not a route or retry witness."""

    native_type: int
    native_name: str
    swallow_status: str  # swallowable | not_swallowable | unknown
    vanilla_copy: str | None
    copy_result: str | None  # fixed (including Normal) | random (mix)
    phase: str
    evidence: str


def _load_json_file(filename: str) -> dict[str, Any]:
    raw = pkgutil.get_data(__name__, "data/" + filename)
    if raw is None:
        raise FileNotFoundError(f"Missing data file: worlds/kirbyam/data/{filename}")
    data = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(data, dict):
        raise ValueError(f"{filename} root must be a JSON object")
    return data


def _parse_address(value: Any) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text.lower().startswith("0x"):
            return int(text, 16)
        return int(text)
    raise ValueError(f"unsupported address value type: {type(value).__name__}")


_ABILITY_DATA = _load_json_file("abilities.json")

_runtime_ability_name_to_id: dict[str, int] = {}
_valid_enemy_copy_abilities: list[str] = []
_forbidden_enemy_copy_abilities: set[str] = set()
_gateable_enemy_copy_abilities: list[str] = []

for ability_name, raw_entry in _ABILITY_DATA.items():
    if not isinstance(ability_name, str) or not ability_name:
        raise ValueError("ability keys in abilities.json must be non-empty strings")
    if not isinstance(raw_entry, dict):
        raise ValueError(f"ability entry for {ability_name} must be an object")

    runtime_id_raw = raw_entry.get("runtime_ability_id")
    runtime_id = None if runtime_id_raw is None else int(runtime_id_raw)
    enemy_copy_allowed_raw = raw_entry.get("enemy_copy_allowed", True)
    enemy_copy_allowed = True if enemy_copy_allowed_raw is None else bool(enemy_copy_allowed_raw)
    safe_to_gate = bool(raw_entry.get("safe_to_gate", False))

    if runtime_id is not None:
        _runtime_ability_name_to_id[ability_name] = runtime_id

    if enemy_copy_allowed:
        if runtime_id is None:
            raise ValueError(
                f"ability {ability_name} is enemy_copy_allowed but has no runtime_ability_id"
            )
        _valid_enemy_copy_abilities.append(ability_name)
    else:
        _forbidden_enemy_copy_abilities.add(ability_name)

    if safe_to_gate:
        if runtime_id is None:
            raise ValueError(f"ability {ability_name} is safe_to_gate but has no runtime_ability_id")
        if not enemy_copy_allowed:
            raise ValueError(f"ability {ability_name} is safe_to_gate but enemy_copy_allowed is false")
        if not (0 < runtime_id <= 31):
            raise ValueError(
                f"ability {ability_name} is safe_to_gate but runtime_ability_id "
                f"{runtime_id} is outside the supported 1..31 range"
            )
        _gateable_enemy_copy_abilities.append(ability_name)


ABILITY_NAME_TO_ID: dict[str, int] = dict(_runtime_ability_name_to_id)
VALID_ENEMY_COPY_ABILITIES: tuple[str, ...] = tuple(_valid_enemy_copy_abilities)
FORBIDDEN_ENEMY_COPY_ABILITIES: frozenset[str] = frozenset(_forbidden_enemy_copy_abilities)
GATEABLE_ENEMY_COPY_ABILITIES: tuple[str, ...] = tuple(_gateable_enemy_copy_abilities)


def resolve_slot_gateable_abilities(value: object) -> tuple[str, ...]:
    """Use the seed's declared gates or the current catalog when unspecified."""
    if not isinstance(value, list) or not value:
        return GATEABLE_ENEMY_COPY_ABILITIES
    return tuple(name for name in value if isinstance(name, str))


_ENEMY_DATA = _load_json_file("enemies.json")

def _parse_parent_copy_audit(key: str, raw: Any) -> EncounterParentCopyAudit:
    fields = {"native_types", "swallow_status", "vanilla_copy", "when", "evidence"}
    if not isinstance(raw, dict) or raw.keys() != fields:
        raise ValueError(f"Invalid encounter parent copy audit: {key}")
    status, ability, when = raw["swallow_status"], raw["vanilla_copy"], raw["when"]
    if status == "swallowable":
        if not isinstance(ability, str) or ability not in ABILITY_NAME_TO_ID or when not in (
            "ordinary", "after_defeat",
        ):
            raise ValueError(f"Swallowable encounter needs a known grant and phase: {key}")
    elif status not in ("not_swallowable", "unknown") or ability is not None or when is not None:
        raise ValueError(f"Unswallowable or unknown encounter cannot name a vanilla grant: {key}")
    types, evidence = raw["native_types"], raw["evidence"]
    if not isinstance(evidence, str) or not evidence.strip() or not isinstance(types, list) or not types:
        raise ValueError(f"Encounter parent audit needs native type and evidence: {key}")
    native = []
    for row in types:
        if (not isinstance(row, dict) or row.keys() != {"id", "name"}
                or type(row["id"]) is not int or not 0 <= row["id"] <= 0xFF
                or not isinstance(row["name"], str) or not row["name"].startswith("OBJ_")):
            raise ValueError(f"Invalid native encounter parent type: {key}")
        native.append((row["id"], row["name"]))
    return EncounterParentCopyAudit(tuple(native), status, ability, when, evidence)


def _parse_encounter_output_copy_audit(key: str, row: Any) -> EncounterOutputCopyAudit:
    fields = {"native_type", "native_name", "swallow_status", "vanilla_copy",
              "copy_result", "phase", "evidence"}
    if not isinstance(row, dict) or row.keys() != fields:
        raise ValueError(f"Invalid encounter output copy audit: {key}")
    native_type = row["native_type"]
    if type(native_type) is not int or not 0 <= native_type <= 0xFF:
        raise ValueError(f"Invalid native encounter output type: {key}")
    if any(not isinstance(row[field], str) or not row[field].strip()
           for field in ("native_name", "phase", "evidence")) or not row["native_name"].startswith("OBJ_"):
        raise ValueError(f"Encounter output audit needs a native name, phase and evidence: {key}")
    status, ability, result = row["swallow_status"], row["vanilla_copy"], row["copy_result"]
    if status == "swallowable":
        fixed = result == "fixed" and isinstance(ability, str) and ability in ABILITY_NAME_TO_ID
        if not (fixed or (result == "random" and ability is None)):
            raise ValueError(f"Swallowable encounter output needs a fixed or random result: {key}")
    elif status not in ("not_swallowable", "unknown") or ability is not None or result is not None:
        raise ValueError(f"Unswallowable or unknown encounter output cannot name a vanilla grant: {key}")
    return EncounterOutputCopyAudit(**row)


ENCOUNTER_OUTPUT_COPY_AUDITS: dict[int, tuple[str, EncounterOutputCopyAudit]] = {}
ENCOUNTER_PARENT_COPY_AUDITS: dict[str, EncounterParentCopyAudit] = {}
NATIVE_PARENT_COPY_AUDIT_KEYS: dict[int, str] = {}
_ability_sources: list[AbilitySource] = []
for source_key, raw_entry in _ENEMY_DATA.items():
    if not isinstance(source_key, str) or not source_key:
        raise ValueError("enemy source keys in enemies.json must be non-empty strings")
    if not isinstance(raw_entry, dict):
        raise ValueError(f"enemy source entry for {source_key} must be an object")

    kind = str(raw_entry.get("kind", "")).strip()
    if kind not in {"enemy", "miniboss", "boss_spawned", "boss", "encounter_output"}:
        raise ValueError(f"enemy source {source_key} has unsupported kind: {kind}")

    audit = None
    if "parent_copy_audit" in raw_entry or kind in {"boss", "miniboss"}:
        if kind not in {"boss", "miniboss"}:
            raise ValueError(f"Encounter parent audit must describe an encounter parent: {source_key}")
        audit = _parse_parent_copy_audit(source_key, raw_entry.get("parent_copy_audit"))
        ENCOUNTER_PARENT_COPY_AUDITS[source_key] = audit
        for type_id, _ in audit.native_types:
            if type_id in NATIVE_PARENT_COPY_AUDIT_KEYS:
                raise ValueError(f"Duplicate native encounter parent type: {type_id:#x}")
            NATIVE_PARENT_COPY_AUDIT_KEYS[type_id] = source_key
    if "encounter_copy_audit" in raw_entry or kind == "encounter_output":
        rows = raw_entry.get("encounter_copy_audit")
        if kind not in {"boss_spawned", "encounter_output"} or not isinstance(rows, list) or not rows:
            raise ValueError(f"Expected encounter output audits: {source_key}")
        for raw in rows:
            output = _parse_encounter_output_copy_audit(source_key, raw)
            if output.native_type in ENCOUNTER_OUTPUT_COPY_AUDITS:
                raise ValueError(f"Duplicate native encounter output type: {output.native_type:#x}")
            if kind == "boss_spawned" and (
                    0x35164E + 24 * output.native_type not in
                    {_parse_address(address) for address in raw_entry.get("addresses", ())}
                    or (output.copy_result == "fixed" and output.vanilla_copy != raw_entry.get("default_ability"))):
                raise ValueError(f"Runtime source and encounter output audit disagree: {source_key}")
            ENCOUNTER_OUTPUT_COPY_AUDITS[output.native_type] = (source_key, output)
    if kind in {"boss", "encounter_output"}:
        if {"addresses", "default_ability", "can_be_swallowed"} & raw_entry.keys():
            raise ValueError(f"Catalog-only audits must not define runtime ability patches: {source_key}")
        continue

    can_be_swallowed_raw = raw_entry.get("can_be_swallowed", True)
    if not isinstance(can_be_swallowed_raw, bool):
        raise ValueError(
            f"enemy source {source_key} field can_be_swallowed must be a boolean"
        )
    can_be_swallowed = can_be_swallowed_raw

    addresses_raw = raw_entry.get("addresses")
    if not isinstance(addresses_raw, list) or not addresses_raw:
        raise ValueError(f"enemy source {source_key} must include non-empty addresses")
    addresses = tuple(_parse_address(addr) for addr in addresses_raw)

    default_ability_name = str(raw_entry.get("default_ability", "")).strip()
    if not default_ability_name:
        raise ValueError(f"enemy source {source_key} missing default_ability")
    if default_ability_name not in ABILITY_NAME_TO_ID:
        raise ValueError(
            f"enemy source {source_key} references unknown default ability: {default_ability_name}"
        )

    if audit is not None and (
            (audit.swallow_status == "swallowable") != can_be_swallowed
            or (can_be_swallowed and audit.vanilla_copy != default_ability_name)
            or {type_id for type_id, _ in audit.native_types}
            != {(address - 0x35164E) // 24 for address in addresses}
            or any((address - 0x35164E) % 24 for address in addresses)):
        raise ValueError(f"Runtime source and parent copy audit disagree: {source_key}")

    _ability_sources.append(
        AbilitySource(
            key=source_key,
            addresses=addresses,
            default_ability_name=default_ability_name,
            default_ability_id=ABILITY_NAME_TO_ID[default_ability_name],
            kind=kind,
            can_be_swallowed=can_be_swallowed,
        )
    )

ABILITY_SOURCES: tuple[AbilitySource, ...] = tuple(_ability_sources)
