"""Strict reversible projection of the accepted Green138 Normal candidate.

This graph pin identifies candidate bytes, not native acceptance. Historical
Spark evidence and catalog pins remain unchanged and checked independently.
"""
from copy import deepcopy
import hashlib
import json
from typing import Any

NORMAL_GRAPH_SHA256 = 'eda0fa78a061e1cc1c83da9c20be589da4e8c30ebb7de28d0ac817595afbfe7f'


def before_green138(target: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(target)
    if result['id'] != 'bomb_138_green':
        return result
    assert 'requires_guaranteed_source' not in result
    assert 'requires_any_guaranteed_source' not in result
    assert set(result['graphs']) == {'upper_left_entry', 'upper_left_normal_slide'}
    graph = result['graphs'].pop('upper_left_normal_slide')
    assert hashlib.sha256(json.dumps(graph, sort_keys=True, separators=(',', ':')).encode()).hexdigest() == (
        NORMAL_GRAPH_SHA256)
    condition = {'source_key': 'SPARKY', 'ability': 'Spark'}
    assert result['graphs']['upper_left_entry'].pop('requires_guaranteed_source') == condition
    result['requires_guaranteed_source'] = condition
    return result


def catalog_before_green138(catalog: dict[str, Any]) -> dict[str, Any]:
    """Reverse only the exact current compiled Green addition, retaining hashes."""
    result = deepcopy(catalog)
    assert (result['witnesses'], result['variants']) == (147, 294)
    ice = [row for row in result['graphs'] if row['witness'] == 'hub4_ice_entry']
    assert hashlib.sha256(json.dumps(ice, sort_keys=True, separators=(',', ':')).encode()).hexdigest() == (
        'ff40de76cee274afba23ef8c406ac6bfd44cacff958f43c1a5e5362c0b27162f')
    assert result['sources'].pop('FOLEY@0x088C2714:camera_respawn1') == [{
        'source_key': 'FOLEY', 'identity': '0x088C2714:camera_respawn1',
        'renewable': False, 'documented_retry': False}]
    result['graphs'] = [row for row in result['graphs'] if row['witness'] != 'hub4_ice_entry']
    for row in result['graphs']:
        if row['target'] == 'switch_533_room16':
            assert row['target_source_condition'] == {
                'source_key': 'FOLEY', 'abilities': ['Bomb', 'UFO', 'Crash', 'Magic', 'Ice']}
            row['target_source_condition']['abilities'].remove('Ice')
    result['witnesses'], result['variants'] = 145, 290
    assert result['capability_providers'].pop('bomb_138_green_normal_lower_slide') == ['Normal']
    new = [row for row in result['graphs'] if row['witness'] == 'upper_left_normal_slide']
    assert hashlib.sha256(json.dumps(new, sort_keys=True, separators=(',', ':')).encode()).hexdigest() == (
        'c9e2ebfe9806497b8378647f2cc40fae21b9e253f6b1832de778342f4e23f1cf')
    result['graphs'] = [row for row in result['graphs'] if row['witness'] != 'upper_left_normal_slide']
    old = [row for row in result['graphs'] if row['target'] == 'bomb_138_green']
    assert len(old) == 2 and {row['area_keys'] for row in old} == {False, True}
    for row in old:
        assert row['witness'] == 'upper_left_entry'
        assert row['target_source_condition'] is None and row['target_source_alternatives'] is None
        assert row['graph_source_condition'] == ['SPARKY', 'Spark']
        row['graph_source_condition'] = None
        row['target_source_condition'] = {'source_key': 'SPARKY', 'ability': 'Spark'}
    return result
