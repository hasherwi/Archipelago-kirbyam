"""Combined candidate identity checks, including the original v0.5 collisions."""
import json
from pathlib import Path

import pytest

from ..data import data, load_json_data
from ..tools.check_item_ids import resolve_catalog, validate_catalogs

INVENTORY = json.loads((Path(__file__).resolve().parents[1] / 'data/item_id_reservations.json').read_text())


def test_resolver_matches_runtime_and_preserves_baseline_ids() -> None:
    items = load_json_data('items.json')
    assert isinstance(items, dict)
    current = resolve_catalog(items)
    assert current == data.item_key_to_id
    validate_catalogs({'main': INVENTORY['baseline_catalog'], 'current': current}, INVENTORY['reserved_items'])
    assert current['TRAP_HUB_TELEPORT'] == 3860300


def test_new_reservation_is_unused_in_every_inventoried_open_pr() -> None:
    assert len(INVENTORY['open_pr_snapshots']) == 16
    for snapshot in INVENTORY['open_pr_snapshots']:
        historical = INVENTORY['baseline_catalog'] | snapshot['changes']
        assert 3860300 not in historical.values()
        assert len(snapshot['head']) == 40 and len(snapshot['items_blob']) == 40


def test_historical_progression_collision_is_not_silently_accepted() -> None:
    snapshots = {row['pr']: row for row in INVENTORY['open_pr_snapshots']}
    catalogs = {str(pr): INVENTORY['baseline_catalog'] | snapshots[pr]['changes'] for pr in (908, 932)}
    with pytest.raises(ValueError, match='3860041 aliases'):
        validate_catalogs(catalogs, INVENTORY['reserved_items'])
    # The revised trap can combine with each branch individually without an alias.
    for name, catalog in catalogs.items():
        validate_catalogs({name: catalog, 'trap': data.item_key_to_id}, INVENTORY['reserved_items'])


def test_old_trap_identity_is_rejected_even_without_progression_branch() -> None:
    with pytest.raises(ValueError, match='TRAP_HUB_TELEPORT moved'):
        validate_catalogs({'old draft': {'TRAP_HUB_TELEPORT': 3860041}}, INVENTORY['reserved_items'])
    with pytest.raises(ValueError, match='3860300 aliases'):
        validate_catalogs({'new item': {'OTHER_ITEM': 3860300}}, INVENTORY['reserved_items'])


def test_implicit_allocations_are_included_and_duplicate_ids_rejected() -> None:
    catalog = resolve_catalog({'EXPLICIT': {'item_id': 3860001}, 'IMPLICIT': {}})
    assert catalog == {'EXPLICIT': 3860001, 'IMPLICIT': 3860002}
    with pytest.raises(ValueError, match='3860002 aliases'):
        validate_catalogs({'implicit': catalog, 'other': {'OTHER': 3860002}}, {})
    with pytest.raises(ValueError, match='Duplicate explicit'):
        resolve_catalog({'A': {'item_id': 3860001}, 'B': {'item_id': 3860001}})
