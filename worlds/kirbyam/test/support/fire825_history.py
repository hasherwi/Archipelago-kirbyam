"""Reverse only the exact Advanced Fire addition, retaining historical pins."""
from copy import deepcopy
from .kibble310_history import digest

TARGET = 'frozen_825_sound_effects'
WITNESS = 'fire_entry'


def before_fire_target(row):
    result = deepcopy(row)
    if result['id'] == TARGET:
        assert result['advanced_graphs'] == ['generated_ice', WITNESS]
        result['advanced_graphs'] = ['generated_ice']
        assert digest(result['graphs'].pop(WITNESS)) == '4f86f3bb282e6decbcb9e526a75e8e9930a3029a5cf3e440bfe87fe66ab014c3'
    return result


def before_fire_catalog(catalog):
    result = deepcopy(catalog)
    assert (result['witnesses'], result['variants']) == (159, 318)
    added = [r for r in result['graphs'] if (r['target'], r['witness']) == (TARGET, WITNESS)]
    assert digest(added) == 'a7eb0f9820e4a6781896df68103126167302c6fee1bd3a3b142c513a161eb6e8'
    result['graphs'] = [r for r in result['graphs'] if (r['target'], r['witness']) != (TARGET, WITNESS)]
    assert result['capability_providers'].pop('switch_825_fire_breath') == ['Fire']
    assert result['sources'].pop('HOT_HEAD@0x088CD3A8') == [
        {'source_key': 'HOT_HEAD', 'identity': '0x088CD3A8', 'renewable': False, 'documented_retry': False}]
    result['witnesses'], result['variants'] = 158, 316
    return result
