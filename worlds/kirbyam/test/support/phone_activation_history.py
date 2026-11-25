"""Exact test-only reversal of Phone activation, not refreshed native evidence."""
from copy import deepcopy
import hashlib
from typing import Any

BASE_SCOPE = ('Current supported public generation, not custom narrowed policy safety or native gameplay. '
              'All compiled targets including logical subregions, both area-key modes.')
PHONE_SCOPE = (BASE_SCOPE + ' The always-on Phone 146 ownership rule and its separately profile-qualified witness are described in phone-progression-admission.md; neither is a compiled attack-provider graph, and the implementation is pinned here.')
PHONE_ITEM_SUFFIX = b'''  },
  "PHONE_A_FRIEND": {
    "label": "Phone a Friend",
    "classification": "PROGRESSION",
    "item_id": 3860501,
    "tags": ["Phone", "Unique"]
  }
}
'''

TRAP_CATALOG_INSERTION = b'''  "TRAP_NARCOLEPSY": {
    "label": "Narcolepsy",
    "classification": "TRAP",
    "item_id": 3860301,
    "tags": ["Trap"]
  },
  "TRAP_RANDOM_TELEPORT": {
    "label": "Random Teleport Trap",
    "classification": "TRAP",
    "item_id": 3860302,
    "tags": ["Trap"]
  },
'''


def items_before_phone(raw: bytes) -> bytes:
    """Check every current byte, remove the exact trap additions and Phone item."""
    raw = raw.replace(b'\r\n', b'\n')
    assert hashlib.sha256(raw).hexdigest() == (
        '74fa44a5e18e22bf3ac529008854d852d1538b69393f577e2b44bbdc3ff2e60c')
    assert raw.count(TRAP_CATALOG_INSERTION) == 1
    raw = raw.replace(TRAP_CATALOG_INSERTION, b'', 1)
    assert hashlib.sha256(raw).hexdigest() == (
        'de4ecaaa79208b78f9054aa364caba91a0d10e211d2e68ab55c2a23881825d8d')
    assert raw.endswith(PHONE_ITEM_SUFFIX)
    result = raw[:-len(PHONE_ITEM_SUFFIX)] + b'  }\n}\n'
    assert hashlib.sha256(result).hexdigest() == (
        '8c55b3b53f973bee4a6ecd5b8409d6ec4204e60cae13f676077d111d1630ddea')
    return result


def catalog_scope_before_phone(catalog: dict[str, Any]) -> dict[str, Any]:
    """Reverse only the exact Phone annotation; preserve all graph/source fields."""
    result = deepcopy(catalog)
    assert result['scope'] == PHONE_SCOPE, 'Unreviewed Phone scope annotation'
    result['scope'] = BASE_SCOPE
    return result
