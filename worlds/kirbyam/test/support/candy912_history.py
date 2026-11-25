"""Project only the exact Candy 9-12 addition out of historical evidence."""
from copy import deepcopy

from .kibble310_history import digest

TARGET = 'bomb_402_candy_chest'


def before_candy912_targets(rows):
    added, = [row for row in rows if row['target']['id'] == TARGET]
    assert digest(added) == '32aeb45d7ad5f44f20e6f6afddf9b53af5ffce6c0e9c680c6f7fc1e2315b889e'
    return [row for row in rows if row is not added]


def before_candy912_catalog(catalog):
    result = deepcopy(catalog)
    assert (result['witnesses'], result['variants']) == (163, 326)
    added = [row for row in result['graphs'] if row['target'] == TARGET]
    assert digest(added) == '2d9ff4b491663aceccfc470534c150998c82ae7e2b0a491514281009b4964427'
    result['graphs'] = [row for row in result['graphs'] if row['target'] != TARGET]
    assert result['capability_providers'].pop('bomb_402_candy_chest') == ['Beam']
    assert result['capability_providers'].pop('bomb_402_candy_chest_ufo') == ['UFO']
    assert result['capability_providers'].pop('bomb_402_candy_chest_spark') == ['Spark']
    assert result['capability_providers'].pop('bomb_402_candy_chest_missile') == ['Missile']
    assert result['capability_providers'].pop('bomb_402_candy_chest_spark') == ['Spark']
    assert result['capability_providers'].pop('bomb_402_candy_chest_missile') == ['Missile']
    assert result['capability_providers'].pop('bomb_402_candy_chest_spark') == ['Spark']
    assert result['capability_providers'].pop('bomb_402_candy_chest_missile') == ['Missile']
    assert result['sources'].pop('WADDLE_DOO@0x088C5BC8') == [
        {'source_key': 'WADDLE_DOO', 'identity': '0x088C5BC8', 'renewable': False, 'documented_retry': False}]
    result['witnesses'], result['variants'] = 159, 318
    return result
