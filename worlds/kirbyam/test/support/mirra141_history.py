"""Reverse only the pinned top Mirra addition in frozen historical contracts."""
from copy import deepcopy
from .kibble310_history import digest

TARGET = 'mirra_141_top_mustard'
OWNER = 'REGION_RAINBOW_ROUTE/ROOM_1_41__LOGIC__TOP_MUSTARD'


def before_mirra141_targets(rows):
    result = []
    for row in rows:
        if row['target']['id'] == TARGET:
            assert row['owner'] == OWNER
            assert digest(row['target']) == '2e7f9f36c385cddcfe449fa2f197e39a7f6a663e9c37756884a59cd305e7ebd9'
        else:
            result.append(row)
    return result


def before_mirra141_surfaces(rows):
    result = deepcopy(rows)
    for row in result:
        if (row['owner'], row['kind'], row['target']) == (OWNER, 'exit', 'REGION_MUSTARD_MOUNTAIN/ROOM_4_07'):
            assert row['requirement'] is None
            row['requirement'] = 'can_mirra'
    return result


def catalog_before_mirra141(catalog):
    result = deepcopy(catalog)
    assert (result['witnesses'], result['variants']) == (150, 300)
    added = [r for r in result['graphs'] if r['target'] == TARGET]
    assert digest(added) == '587a1664dc805138ba2b4134a49743e7c040e264ccb0594a98150b5e4f65e055'
    assert result['capability_providers'].pop('mirra_141_top_normal_puff') == ['Normal']
    result['graphs'] = [r for r in result['graphs'] if r['target'] != TARGET]
    result['witnesses'], result['variants'] = 149, 298
    return result
