"""Reject item-ID collisions before combining candidate Kirby catalogs.

Pass each candidate's data/items.json with --catalog. The checked-in reservations
are always enforced. Do not pass historical snapshots as if they were compatible.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from collections.abc import Mapping
from typing import Any

RESERVATIONS = Path(__file__).resolve().parents[1] / 'data/item_id_reservations.json'


def resolve_catalog(items: Mapping[str, Any]) -> dict[str, int]:
    """Mirror data.py's explicit-first allocation, including implicit IDs."""
    explicit = [int(row['item_id']) for row in items.values() if row.get('item_id')]
    if len(explicit) != len(set(explicit)):
        raise ValueError('Duplicate explicit item IDs within catalog')
    used = set(explicit)
    next_id = 3860001
    resolved = {}
    for key, row in items.items():
        item_id = int(row.get('item_id') or 0)
        if not item_id:
            while next_id in used:
                next_id += 1
            item_id = next_id
            next_id += 1
        used.add(item_id)
        resolved[key] = item_id
    return resolved


def validate_catalogs(catalogs: Mapping[str, Mapping[str, int]], reservations: Mapping[str, int]) -> None:
    """Same identity may repeat; neither ID aliases nor identity renumbering may."""
    ids: dict[int, str] = {}
    identities: dict[str, int] = {}
    for source, catalog in [('reservations', reservations), *catalogs.items()]:
        for key, item_id in catalog.items():
            if item_id in ids and ids[item_id] != key:
                raise ValueError(f'{source}: ID {item_id} aliases {ids[item_id]} and {key}')
            if key in identities and identities[key] != item_id:
                raise ValueError(f'{source}: {key} moved from {identities[key]} to {item_id}')
            ids[item_id] = key
            identities[key] = item_id


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, action='append', required=True)
    args = parser.parse_args()
    reservations = json.loads(RESERVATIONS.read_text())['reserved_items']
    catalogs = {str(path): resolve_catalog(json.loads(path.read_text())) for path in args.catalog}
    validate_catalogs(catalogs, reservations)
    print(f'Validated {len(catalogs)} catalogs and stable reservations')


if __name__ == '__main__':
    main()
