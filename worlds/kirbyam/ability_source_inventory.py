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
    payload = _inventory_payload()
    records = (payload['placements'] + payload['generated_statue_slots']
               + payload.get('spawner_outputs', []) + payload.get('encounter_sources', []))
    result = {row['id']: row for row in records}
    if len(result) != len(records):
        raise ValueError('Duplicate physical ability placement identity')
    return result


def resolve_inventory_source(source: Mapping[str, Any], native_room: int,
                             *, advanced: bool = False, require_inventory: bool = False) -> dict[str, Any]:
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
        legacy_id = source.get('id')
        if legacy_id is not None and any(
            key.partition(':')[2] == legacy_id for key in _inventory_payload()['reviewed_bindings']
        ):
            raise ValueError(f'Physical ability placement belongs to another room: {legacy_id}')
        if require_inventory:
            from .master_source import CENTRAL_MASTER_SOURCE
            if source.get('source_key') != CENTRAL_MASTER_SOURCE:
                raise ValueError(f"Production ability source requires a physical inventory reference: "
                                 f"room={native_room}, id={source.get('id')}, key={source.get('source_key')}")
        return result  # Isolated solver fixtures and the special Master contract.
    record = source_inventory().get(identity)
    if record is None:
        raise ValueError(f'Unknown physical ability placement: {identity}')
    if record['native_room'] != native_room:
        raise ValueError(f'Physical ability placement belongs to another room: {identity}')
    key = record['source_key']
    if key is None:
        choices = record.get('possible_source_keys')
        if not choices:
            raise ValueError(f'Unresolved physical ability grant: {identity}')
        if result.get('source_choices', choices) != choices:
            raise ValueError(f'Native source choices mismatch: {identity}')
        if result.get('retry_evidence'):
            raise ValueError(f'Fixed native selection cannot justify retry: {identity}')
        key = choices[0]
        result['source_choices'] = list(choices)
    if 'source_choices' in result and result['source_choices'] != record.get('possible_source_keys'):
        raise ValueError(f'Native source choices mismatch: {identity}')
    if result.get('source_key', key) != key:
        raise ValueError(f'Physical ability placement grant mismatch: {identity}')
    if record['logic'] == 'advanced' and not advanced:
        raise ValueError(f'Encounter source requires Advanced Logic: {identity}')
    if 'parent_placement' in record:
        # Native candidates are not automatically available. A reviewed graph
        # must put activation/branch conditions on its path to this compartment.
        for field in ('generation_evidence', 'lifetime_evidence'):
            if not isinstance(result.get(field), str) or not result[field].strip():
                raise ValueError(f'Generated source requires {field}: {identity}')
        # Generation ownership is not object lifetime: statue controllers die
        # immediately, while their outputs persist. Each output needs an explicit
        # activation and expiry contract; sharing the controller ID was unsound.
        lifetime = record['id']
        if result.get('lifetime', lifetime) != lifetime:
            raise ValueError(f'Generated source lifetime mismatch: {identity}')
        if (record.get('configured_child_capacity') == 1
                and record.get('reclaims_destroyed_slots') is False and result.get('renewable')):
            raise ValueError(f'Finite non-reclaiming spawner cannot be renewable: {identity}')
        result['lifetime'] = lifetime
    result['source_key'] = key
    return result
