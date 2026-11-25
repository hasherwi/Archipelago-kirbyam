"""Project only the exact Candy 9-12 addition out of historical evidence."""
from copy import deepcopy

from .kibble310_history import digest

TARGET = 'bomb_402_candy_chest'


def before_candy912_targets(rows):
    added, = [row for row in rows if row['target']['id'] == TARGET]
    assert digest(added) == '3afef6b75dde16a0b975ea5414dbe3df65ab648e79e32596a96f0df77e2df720'
    return [row for row in rows if row is not added]


def before_candy912_catalog(catalog):
    result = deepcopy(catalog)
    assert (result['witnesses'], result['variants']) == (164, 328)
    added = [row for row in result['graphs'] if row['target'] == TARGET]
    assert digest(added) == '87281214916accf98b294cec263a2f42eac12b58a31c844187bf7f164fbc5f64'
    result['graphs'] = [row for row in result['graphs'] if row['target'] != TARGET]
    providers = {
        TARGET: ['Beam'],
        f'{TARGET}_ufo': ['UFO'],
        f'{TARGET}_spark': ['Spark'],
        f'{TARGET}_missile': ['Missile'],
        f'{TARGET}_sword': ['Sword'],
    }
    for capability, expected in providers.items():
        assert result['capability_providers'].pop(capability, None) == expected
    assert result['sources'].pop('WADDLE_DOO@0x088C5BC8', None) == [
        {'source_key': 'WADDLE_DOO', 'identity': '0x088C5BC8', 'renewable': False, 'documented_retry': False}]
    result['witnesses'], result['variants'] = 159, 318
    return result
