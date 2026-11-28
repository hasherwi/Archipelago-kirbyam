"""Project only the exact Candy 9-12 addition out of historical evidence."""
from copy import deepcopy

from .kibble310_history import digest
from .conditional_route_history import before_conditional_routes_target
from .stock_short_carrier_history import before_stock_short_catalog

TARGET = 'bomb_402_candy_chest'


def before_candy912_targets(rows):
    added, = [row for row in rows if row['target']['id'] == TARGET]
    predecessor = deepcopy(added)
    target = predecessor['target']
    if 'conditional_routes' in target:
        target = predecessor['target'] = before_conditional_routes_target(target)
    assert target['requires_guaranteed_source']['abilities'].pop() == 'Smash'
    assert digest(target['graphs'].pop('local_smash')) == (
        'cd649464aff26bcf3dcf2350e69c98167b7b573a9d047736a8d23adc10330b39')
    assert digest(predecessor) == '3afef6b75dde16a0b975ea5414dbe3df65ab648e79e32596a96f0df77e2df720'
    return [row for row in rows if row is not added]


def before_candy912_catalog(catalog):
    result = before_stock_short_catalog(catalog)
    assert (result['witnesses'], result['variants']) == (165, 330)
    added = [row for row in result['graphs'] if row['target'] == TARGET]
    smash = [row for row in added if row['witness'] == 'local_smash']
    assert digest(smash) == '6df2894d57a784dabb2b5347d091bcbcf6ea8ac859de63d154e9b519ce5734f4'
    predecessor = [row for row in added if row not in smash]
    for row in predecessor:
        assert row['target_source_condition']['abilities'].pop() == 'Smash'
    assert digest(predecessor) == '87281214916accf98b294cec263a2f42eac12b58a31c844187bf7f164fbc5f64'
    result['graphs'] = [row for row in result['graphs'] if row['target'] != TARGET]
    providers = {
        TARGET: ['Beam'],
        f'{TARGET}_ufo': ['UFO'],
        f'{TARGET}_spark': ['Spark'],
        f'{TARGET}_missile': ['Missile'],
        f'{TARGET}_sword': ['Sword'],
        f'{TARGET}_smash': ['Smash'],
    }
    for capability, expected in providers.items():
        assert result['capability_providers'].pop(capability, None) == expected
    assert result['sources'].pop('WADDLE_DOO@0x088C5BC8', None) == [
        {'source_key': 'WADDLE_DOO', 'identity': '0x088C5BC8', 'renewable': False, 'documented_retry': False}]
    result['witnesses'], result['variants'] = 159, 318
    return result
