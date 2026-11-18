"""Common physical source facts; inventory presence is never an access rule."""
from __future__ import annotations

import json
import pkgutil
from functools import lru_cache
from typing import Any, Mapping


@lru_cache(maxsize=1)
def _inventory_payload() -> dict[str, Any]:
    raw = pkgutil.get_data(__name__, 'data/ability_source_inventory.json')
    if raw is None:
        raise FileNotFoundError('Missing physical ability source inventory')
    payload = json.loads(raw)
    if payload.get('version') != 1:
        raise ValueError('Unsupported physical ability source inventory')
    return payload


@lru_cache(maxsize=1)
def source_inventory() -> Mapping[str, Mapping[str, Any]]:
    records = _inventory_payload()['placements']
    result = {row['id']: row for row in records}
    if len(result) != len(records):
        raise ValueError('Duplicate physical ability placement identity')
    return result


def resolve_inventory_source(source: Mapping[str, Any], native_room: int,
                             *, advanced: bool = False) -> dict[str, Any]:
    """Join a reviewed compartment witness to physical facts without adding access.

    Native spawn state, acquisition, renewability and geometry are separate.
    The witness must still supply all those conditions. A catalog row alone
    cannot construct a Placement or justify a retry of a finite random source.
    """
    result = dict(source)
    identity = result.pop('inventory_id', None)
    if identity is None:
        identity = _inventory_payload()['reviewed_bindings'].get(f"{native_room}:{source.get('id')}")
    if identity is None:
        return result  # Isolated solver fixtures and the special Master contract.
    record = source_inventory().get(identity)
    if record is None:
        raise ValueError(f'Unknown physical ability placement: {identity}')
    if record['native_room'] != native_room:
        raise ValueError(f'Physical ability placement belongs to another room: {identity}')
    key = record['source_key']
    if key is None:
        raise ValueError(f'Unresolved physical ability grant: {identity}')
    if result.get('source_key', key) != key:
        raise ValueError(f'Physical ability placement grant mismatch: {identity}')
    if record['logic'] == 'advanced' and not advanced:
        raise ValueError(f'Encounter source requires Advanced Logic: {identity}')
    result['source_key'] = key
    return result
