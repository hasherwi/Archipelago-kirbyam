"""Strict projections for pinned pre-union main graph fingerprints.

The two added compiled fields are checked before projecting the old shape.
The825 singleton is a reviewed semantic refinement, not byte identity. Raw
physical hashes additionally account for one exact accepted documentation edit.
"""
from copy import deepcopy
from dataclasses import asdict
from typing import Any

from ...traversal import TraversalGraph

FUSE_PREFIX = (
    "Ignite 0x88b950c at 72,88, then enter paired cannon 0x88b94e8 to native570 spawn6,1. "
    "This is one timed use, not a permanent opened event. "
)
HISTORICAL_FUSE_EVIDENCE = FUSE_PREFIX + (
    "Crash can ignite the fuse, but its cannon-entry timing is not yet a reviewed traversal witness."
)
ACCEPTED_FUSE_EVIDENCE = FUSE_PREFIX + (
    "The separately bounded lower_entry_crash graph models finite Crash ignition and cannon entry."
)


def historical_main_compiled(graph: TraversalGraph, target: str, witness: str) -> dict[str, Any]:
    """Call only for identities enumerated by the historical main fixtures."""
    payload = asdict(graph)
    expected = ('MR_FROSTY', 'Ice') if (target, witness) == ('frozen_825_sound_effects', 'local') else None
    assert payload['required_guaranteed_source'] == expected
    del payload['required_guaranteed_source']
    for route in payload['routes']:
        assert route['required_equipment'] is None
        del route['required_equipment']
    return payload


def historical_main_raw(payload: dict[str, Any], target: str, witness: str) -> dict[str, Any]:
    """Keep every physical field; assert the exact two reviewed differences."""
    result = deepcopy(payload)
    if (target, witness) == ('frozen_825_sound_effects', 'local'):
        assert result.get('requires_guaranteed_source') == {'source_key': 'MR_FROSTY', 'ability': 'Ice'}
        del result['requires_guaranteed_source']
    if (target, witness) == ('fuse_126', 'local'):
        assert result['routes'][0]['evidence'] == ACCEPTED_FUSE_EVIDENCE
        result['routes'][0]['evidence'] = HISTORICAL_FUSE_EVIDENCE
    return result
