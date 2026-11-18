"""Strict projection of only the reviewed Crash/Magic logic-level annotations.

Historical physical evidence remains byte-for-byte pinned. This projection
does not hide changes to historical graphs, sources or ownership. The exact
new Ice graph is hash-checked and removed only when comparing older witnesses. The exact issue #1099
fail-closed metadata is projected separately from the historical native evidence.
"""
from copy import deepcopy
import hashlib
import json
from typing import Any

MARKERS = {'fuse_126': ['lower_entry_crash'],
           'switch_533_room16': ['hub4_crash_entry', 'hub4_magic_entry'],
           'switch_310_mustard_map': ['hub4_crash_entry']}


ROOM16_POLICY_METADATA = {
    'required_for_generation': False,
    'fail_closed': True,
    'optional_route_evidence': 'dev-docs/mustard-room15-source-witness.md#all-policy-access-rule-issue-1099; Room15 -> Room17 -> Room18 bypasses Room16 for ordinary progression. Room16 itself is not granted by that bypass; its optional RoomSanity check remains subject to fill/accessibility.',
}


def before_advanced_crash(target: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(target)
    if result['id'] in MARKERS:
        assert result.pop('advanced_graphs') == MARKERS[result['id']]
    elif result['id'] == 'frozen_825_sound_effects' and 'generated_ice' in result['graphs']:
        assert result['advanced_graphs'] == ['generated_ice']
        assert hashlib.sha256(json.dumps(result['graphs']['generated_ice'], sort_keys=True, separators=(',', ':')).encode()).hexdigest() == '951c005dbcb4b76d6718ad4ce4d8847a20758ec485f3245f1e01ab0ccae29058'
    else:
        assert 'advanced_graphs' not in result
    if result['id'] == 'switch_533_room16':
        ice = result['graphs'].pop('hub4_ice_entry')
        assert hashlib.sha256(json.dumps(ice, sort_keys=True).encode()).hexdigest() == (
            'd000537124e8c4b531f59efc338e0dd5cd36b60ca6bf28247feb054c0c6eb48b')
        source = result['requires_guaranteed_source']
        assert source == {'source_key': 'FOLEY', 'abilities': ['Bomb', 'UFO', 'Crash', 'Magic', 'Ice']}
        source['abilities'].remove('Ice')
        for key, expected in ROOM16_POLICY_METADATA.items():
            actual = result.pop(key)
            assert type(actual) is type(expected) and actual == expected, key
    return result


def rooms_before_advanced_crash(rooms: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(rooms)
    for room in result.values():
        traversal = room.get('traversal', {})
        if 'targets' in traversal:
            traversal['targets'] = [before_advanced_crash(row) for row in traversal['targets']]
    return result
