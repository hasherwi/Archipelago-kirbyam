"""Project the private Master719 candidate off unchanged historical snapshots.

The hash pins candidate graph bytes for this comparison, not native acceptance.
The source, schema and real-state tests separately exercise the current union.
"""
from copy import deepcopy
import hashlib
import json
from typing import Any

MASTER_GRAPH_SHA256 = "fba341b826cbd8d4a72914798219fe12b71af80cc304503fd79e08b0732ddbf4"


def before_master719(target: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(target)
    if result['id'] != 'bomb_719_room13':
        return result
    assert 'requires_guaranteed_source' not in result
    assert 'requires_any_guaranteed_source' not in result
    graph = result['graphs'].pop('central_master')
    assert hashlib.sha256(json.dumps(graph, sort_keys=True, separators=(',', ':')).encode()).hexdigest() == (
        MASTER_GRAPH_SHA256)
    for witness, ability in (('room5_entry', 'Beam'), ('room5_fighter_entry', 'Fighter')):
        assert result['graphs'][witness].pop('requires_guaranteed_source') == {
            'source_key': 'WADDLE_DOO', 'ability': ability}
    result['requires_guaranteed_source'] = {
        'source_key': 'WADDLE_DOO', 'abilities': ['Beam', 'Fighter', 'Sword', 'Fire']}
    return result
