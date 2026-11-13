"""Regenerate the current compiled catalog without changing historical provenance.

Run with AP_TEST_WORLDS=kirbyam and import test before importing this module.
This enumerates structure only; it does not generate seeds or certify gameplay.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

from ..enemy_ability_data import GATEABLE_ENEMY_COPY_ABILITIES, VALID_ENEMY_COPY_ABILITIES
from ..traversal import CAPABILITY_ABILITIES, attack_provider
from ..traversal_data import _room_catalog, room_traversal_graph

ROOT = Path(__file__).resolve().parents[3]
CATALOG = ROOT / 'worlds/kirbyam/dev-docs/supported-source-monotonicity-catalog.json'


def build_catalog(previous: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = deepcopy(previous)
    # Canonical LF hashes tolerate Git's Windows checkout conversion only.
    # Do not strip whitespace or normalize bare CR: every other byte is evidence.
    result['source_sha256'] = {name: hashlib.sha256((ROOT / name).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
                               for name in previous['source_sha256']}
    result['valid_pool'] = sorted(VALID_ENEMY_COPY_ABILITIES)
    result['ungated_pool_abilities'] = sorted(set(VALID_ENEMY_COPY_ABILITIES) - set(GATEABLE_ENEMY_COPY_ABILITIES))
    result['capability_providers'] = {key: sorted(values) for key, values in CAPABILITY_ABILITIES.items()}
    sources: dict[str, list[dict[str, str | bool]]] = {}
    rows: list[dict[str, Any]] = []
    for target in _room_catalog()[0]:
        for witness in target['graphs']:
            for keys in (False, True):
                graph = room_traversal_graph(target['id'], witness, keys)
                source_ids = set()
                for source in graph.placements:
                    assert source.identity is not None
                    key = source.source_key + '@' + source.identity
                    source_ids.add(key)
                    variant: dict[str, str | bool] = {
                        'source_key': source.source_key, 'identity': source.identity,
                        'renewable': source.renewable, 'documented_retry': bool(source.retry_evidence)}
                    if variant not in sources.setdefault(key, []):
                        sources[key].append(variant)
                routes = []
                for route in graph.routes:
                    if not route.capability:
                        continue
                    allowed = (CAPABILITY_ABILITIES[route.capability]
                               if route.allowed_abilities is None else route.allowed_abilities)
                    routes.append({'from': route.source, 'to': route.target, 'capability': route.capability,
                                   'water_state': route.water_state, 'allowed_abilities': sorted(allowed),
                                   'beam_provider': attack_provider('Beam', route.water_state),
                                   'beam_accepted': attack_provider('Beam', route.water_state) in allowed,
                                   'normal_accepted': attack_provider('Normal', route.water_state) in allowed,
                                   'recover_dropped_ability': route.recover_dropped_ability})
                rows.append({'target': target['id'], 'witness': witness, 'area_keys': keys,
                             'source_ids': sorted(source_ids), 'capability_routes': routes,
                             'target_source_condition': target.get('requires_guaranteed_source'),
                             'target_source_alternatives': target.get('requires_any_guaranteed_source'),
                             'graph_source_condition': (list(graph.required_guaranteed_source)
                                                        if graph.required_guaranteed_source else None),
                             'equipment_routes': [
                                 {'from': route.source, 'to': route.target,
                                  'required_equipment': sorted(route.required_equipment)}
                                 for route in graph.routes if route.required_equipment is not None]})
    # Preserve historical enumeration order; newly introduced variants append.
    order = {(row['target'], row['witness'], row['area_keys']): index
             for index, row in enumerate(previous['graphs'])}
    rows.sort(key=lambda row: order.get((row['target'], row['witness'], row['area_keys']), len(order)))
    result.update(witnesses=len(rows) // 2, variants=len(rows), sources=sources, graphs=rows)
    return result


def main() -> None:
    CATALOG.write_text(json.dumps(build_catalog(json.loads(CATALOG.read_text())), indent=2) + '\n')


if __name__ == '__main__':
    main()
