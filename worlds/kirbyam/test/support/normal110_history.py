"""Strict projection of the reviewed110 addition onto the frozen union snapshot."""
from copy import deepcopy
import hashlib
import json
from typing import Any

NORMAL_GRAPH_SHA256 = "b66fb353cb40d81dc2a73c839782755cede126ecd444921c3bd15466a52217ac"


def before_normal110(target: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(target)
    if result['id'] != 'bomb_110_room9':
        return result
    assert 'requires_any_guaranteed_source' not in result
    assert 'requires_guaranteed_source' not in result
    graph = result['graphs'].pop('upper_entry_normal_water')
    assert hashlib.sha256(json.dumps(graph, sort_keys=True, separators=(',', ':')).encode()).hexdigest() == (
        NORMAL_GRAPH_SHA256)
    conditions = []
    for witness, source, ability in (('upper_entry', 'SPARKY', 'Spark'),
                                     ('upper_entry_sword', 'SWORD_KNIGHT', 'Sword')):
        condition = {'source_key': source, 'ability': ability}
        assert result['graphs'][witness].pop('requires_guaranteed_source') == condition
        conditions.append(condition)
    result['requires_any_guaranteed_source'] = conditions
    return result
