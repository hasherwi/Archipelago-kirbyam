"""Historical hashes remain exact after the separately reviewed Phone delta."""
from copy import deepcopy
from pathlib import Path
import json

import pytest

from .support.phone_activation_history import items_before_phone, catalog_scope_before_phone, BASE_SCOPE

ROOT = Path(__file__).parents[1]


def test_items_projection_accepts_lf_and_crlf_only():
    raw = (ROOT / 'data/items.json').read_bytes().replace(b'\r\n', b'\n')
    assert items_before_phone(raw) == items_before_phone(raw.replace(b'\n', b'\r\n'))
    for bad in (raw.replace(b'3860501', b'3860502'),
                raw.replace(b'3860301', b'3860303'),
                raw.replace(b'3860302', b'3860303'),
                raw.replace(b'3860416', b'3860417'),
                raw.replace(b'PROGRESSION', b'USEFUL', 1), raw + b'\n',
                raw.replace(b'"Phone", "Unique"', b'"Unique", "Phone"')):
        with pytest.raises(AssertionError):
            items_before_phone(bad)


def test_scope_projection_changes_only_exact_annotation():
    raw = json.loads((ROOT / 'dev-docs/supported-source-monotonicity-catalog.json').read_text())
    saved = deepcopy(raw)
    projected = catalog_scope_before_phone(raw)
    assert raw == saved and projected == {**raw, 'scope': BASE_SCOPE}
    for bad_scope in (BASE_SCOPE, raw['scope'] + ' ', 'arbitrary replacement'):
        with pytest.raises(AssertionError):
            catalog_scope_before_phone({**raw, 'scope': bad_scope})
    # Unrelated graph drift is not erased by the projection; the existing full
    # historical structural-hash assertion still detects it.
    raw['witnesses'] += 1
    assert catalog_scope_before_phone(raw)['witnesses'] == saved['witnesses'] + 1
