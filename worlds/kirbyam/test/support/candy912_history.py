"""Project only the exact Candy 9-12 addition out of historical evidence."""
from copy import deepcopy

from .kibble310_history import digest

TARGET = 'bomb_402_candy_chest'


def before_candy912_targets(rows):
    added, = [row for row in rows if row['target']['id'] == TARGET]
    assert digest(added) == '2a779e52a8388c959df84d12c7f628c2e30dd4e87dd5b3bf84682c9de48eec87'
    return [row for row in rows if row is not added]


def before_candy912_catalog(catalog):
    result = deepcopy(catalog)
    assert (result['witnesses'], result['variants']) == (161, 322)
    added = [row for row in result['graphs'] if row['target'] == TARGET]
    assert digest(added) == '482aef8abfdef0579b23968df31438eea6d8d3c224151aa30be92b4e28b8f75b'
    result['graphs'] = [row for row in result['graphs'] if row['target'] != TARGET]
    assert result['capability_providers'].pop('bomb_402_candy_chest') == ['Beam']
    assert result['capability_providers'].pop('bomb_402_candy_chest_ufo') == ['UFO']
    assert result['sources'].pop('WADDLE_DOO@0x088C5BC8') == [
        {'source_key': 'WADDLE_DOO', 'identity': '0x088C5BC8', 'renewable': False, 'documented_retry': False}]
    result['witnesses'], result['variants'] = 159, 318
    return result
