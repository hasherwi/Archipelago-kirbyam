"""Reverse only the pinned top and east Mirra additions in frozen historical contracts."""
from copy import deepcopy
from .kibble310_history import digest

EAST_TARGET = 'mirra_141_east_moonlight'
EAST_OWNER = 'REGION_RAINBOW_ROUTE/ROOM_1_41__LOGIC__EAST_MOONLIGHT'
TARGET = 'mirra_141_top_mustard'
OWNER = 'REGION_RAINBOW_ROUTE/ROOM_1_41__LOGIC__TOP_MUSTARD'


def before_mirra141_targets(rows):
    result = []
    for row in rows:
        if row['target']['id'] == EAST_TARGET:
            assert row['owner'] == EAST_OWNER
            assert digest(row['target']) == '020e2c9b461897ee37349d474a340458b0fa47d781d955b1a7f1fd396146d48f'
        elif row['target']['id'] == TARGET:
            assert row['owner'] == OWNER
            assert digest(row['target']) == '2e7f9f36c385cddcfe449fa2f197e39a7f6a663e9c37756884a59cd305e7ebd9'
        else:
            result.append(row)
    return result


def before_mirra141_surfaces(rows):
    result = deepcopy(rows)
    for row in result:
        if (row['owner'], row['kind'], row['target']) == (EAST_OWNER, 'exit', 'REGION_MOONLIGHT_MANSION/ROOM_2_16'):
            assert row['requirement'] is None
            row['requirement'] = 'can_mirra'
        if (row['owner'], row['kind'], row['target']) == (OWNER, 'exit', 'REGION_MUSTARD_MOUNTAIN/ROOM_4_07'):
            assert row['requirement'] is None
            row['requirement'] = 'can_mirra'
    return result


def catalog_before_mirra141(catalog):
    result = deepcopy(catalog)
    assert (result['witnesses'], result['variants']) == (151, 302)
    east = [r for r in result['graphs'] if r['target'] == EAST_TARGET]
    assert digest(east) == '506e57b0add54cc3ca9049108938910ba86320ef50c50ffe5c9fc9ae9e6e7bf8'
    assert result['capability_providers'].pop('mirra_141_east_normal_puff') == ['Normal']
    result['graphs'] = [r for r in result['graphs'] if r['target'] != EAST_TARGET]
    added = [r for r in result['graphs'] if r['target'] == TARGET]
    assert digest(added) == '587a1664dc805138ba2b4134a49743e7c040e264ccb0594a98150b5e4f65e055'
    assert result['capability_providers'].pop('mirra_141_top_normal_puff') == ['Normal']
    result['graphs'] = [r for r in result['graphs'] if r['target'] != TARGET]
    result['witnesses'], result['variants'] = 149, 298
    return result
