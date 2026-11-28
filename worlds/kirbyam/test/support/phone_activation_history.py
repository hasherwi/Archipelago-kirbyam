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


STARTING_MIRROR_CATALOG_INSERTION = b'''  "HUB_CONNECTION_STARTING_MIRROR": {
    "label": "Room 1-01 Mirror - Hub Connection",
    "classification": "PROGRESSION",
    "item_id": 3860416,
    "tags": [
      "HubConnections",
      "Progression",
      "Unique"
    ]
  },
'''

RAINBOW_AREA_KEY_CATALOG_INSERTION = b'''  "AREA_KEY_1": {
    "label": "Rainbow Route - Area Key",
    "classification": "PROGRESSION",
    "item_id": 3860056,
    "tags": ["AreaKeys", "Unique"]
  },
'''


def items_before_phone(raw: bytes) -> bytes:
    """Reverse the reviewed battery classification, then the exact prior catalog additions."""
    raw = raw.replace(b'\r\n', b'\n')
    # 36d9ebcd made the existing Beam item progression when ability gating is active.
    beam = b'"label": "Beam Ability",\n    "classification": "PROGRESSION",\n    "item_id": 3860107,'
    assert raw.count(beam) == 1
    raw = raw.replace(beam, beam.replace(b'PROGRESSION', b'USEFUL'), 1)
    assert hashlib.sha256(raw).hexdigest() == 'ec3fdad4a43eb9ef0a3bf0c5f2ab73d17ca0682287e392f5d9d73a37965a23c1'
    for item_id in range(3860002, 3860010):
        explicit_id = f'    "item_id": {item_id},\n'.encode()
        assert raw.count(explicit_id) == 1
        raw = raw.replace(explicit_id, b'', 1)
    assert hashlib.sha256(raw).hexdigest() == 'a780255a758f82dc1f158343b339203b3f1cc35aa823ba63c001fc7278c17738'
    battery = b'"classification": "USEFUL",\n    "item_id": 3860027'
    assert raw.count(battery) == 1
    raw = raw.replace(battery, battery.replace(b'USEFUL', b'FILLER'), 1)
    assert hashlib.sha256(raw).hexdigest() == (
        'c3dc98375cdefea7e60378a9837d90c179007cb37901650dcddd1ac00292b806')
    assert raw.count(RAINBOW_AREA_KEY_CATALOG_INSERTION) == 1
    raw = raw.replace(RAINBOW_AREA_KEY_CATALOG_INSERTION, b'', 1)
    assert hashlib.sha256(raw).hexdigest() == (
        'd212a0b44e9ea3db96427a916ce2bb1c5112c0fb861526058ec979abe181d507')
    assert raw.count(STARTING_MIRROR_CATALOG_INSERTION) == 1
    raw = raw.replace(STARTING_MIRROR_CATALOG_INSERTION, b'', 1)
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
