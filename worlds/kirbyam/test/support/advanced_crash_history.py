"""Strict projection of only the three reviewed logic-level annotations.

Historical physical evidence remains byte-for-byte pinned. This projection does
not hide graph, source, ownership or applicability changes.
"""
from copy import deepcopy
from typing import Any

MARKERS = {'fuse_126': ['lower_entry_crash'],
           'switch_533_room16': ['hub4_crash_entry'],
           'switch_310_mustard_map': ['hub4_crash_entry']}


def before_advanced_crash(target: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(target)
    if result['id'] in MARKERS:
        assert result.pop('advanced_graphs') == MARKERS[result['id']]
    else:
        assert 'advanced_graphs' not in result
    return result


def rooms_before_advanced_crash(rooms: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(rooms)
    for room in result.values():
        traversal = room.get('traversal', {})
        if 'targets' in traversal:
            traversal['targets'] = [before_advanced_crash(row) for row in traversal['targets']]
    return result
