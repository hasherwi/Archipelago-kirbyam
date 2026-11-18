"""Reverse only the pinned Radish Normal addition for older native records."""
from copy import deepcopy
import hashlib
import json

OWNER = 'REGION_RADISH_RUINS/ROOM_8_CHEST_2'
TARGET = 'bomb_617_radish_map'


def before_radish617_targets(rows):
    added, = [row for row in rows if row['target']['id'] == TARGET]
    assert added['owner'] == OWNER
    assert hashlib.sha256(json.dumps(added['target'], sort_keys=True).encode()).hexdigest() == (
        'da4f72bd492a4df1dec26fd997972ec500b72e39f54a26ea03911f22867e4cd8')
    from .kibble310_history import before_kibble310
    return [{**row, 'target': before_kibble310(row['target'])} for row in rows if row is not added]


def before_radish617_surfaces(rows):
    result = deepcopy(rows)
    row, = [row for row in result if row['owner'] == OWNER and row['kind'] == 'location'
            and row['target'] == 'MAJOR_CHEST_RADISH_RUINS']
    assert row['requirement'] is None
    row['requirement'] = 'can_get_rr_map_chest'
    return result



def catalog_before_radish617(catalog):
    from .kibble310_history import catalog_before_kibble310
    result = catalog_before_kibble310(catalog)
    assert (result['witnesses'], result['variants']) == (148, 296)
    added = [row for row in result['graphs'] if row['target'] == TARGET]
    assert hashlib.sha256(json.dumps(added, sort_keys=True, separators=(',', ':')).encode()).hexdigest() == (
        'f94e475e7edd89f3d439477b827b8d98e65956f28e963b5d5b30f7409461567f')
    assert result['capability_providers'].pop('bomb_617_normal_puff_slide') == ['Normal']
    result['graphs'] = [row for row in result['graphs'] if row['target'] != TARGET]
    result['witnesses'], result['variants'] = 147, 294
    return result
