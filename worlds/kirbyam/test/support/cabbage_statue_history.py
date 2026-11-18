"""Strictly project the shared Hub2 statue addition out of frozen native records."""
from copy import deepcopy
from .kibble310_history import digest

TARGET = 'bomb_517_chocolate'
WITNESS = 'hub2_statues_entry'
OLD = {'source_key': 'WADDLE_DOO', 'abilities': ['Beam', 'Smash', 'Fire', 'Missile', 'Parasol', 'Spark', 'Ice', 'Sword', 'Fighter', 'UFO']}
NEW = [OLD, *[{**OLD, 'source_key': key} for key in ('STATUE:353906', 'STATUE:353901')]]


def before_cabbage_statues_target(row):
    result = deepcopy(row)
    if result['id'] == TARGET:
        assert result.pop('requires_any_guaranteed_source') == NEW
        assert 'requires_guaranteed_source' not in result
        result['requires_guaranteed_source'] = deepcopy(OLD)
        assert result['graphs']['hub2_entry'].pop('requires_guaranteed_source') == {'source_key': 'WADDLE_DOO', 'ability': 'Beam'}
        assert digest(result['graphs'].pop(WITNESS)) == 'fae025115955fe018e1244abc7365438c0b5c39b4ae9296a04b2d1b42f6327de'
    return result


def before_cabbage_statues_catalog(catalog):
    result = deepcopy(catalog)
    assert (result['witnesses'], result['variants']) == (158, 316)
    added = [r for r in result['graphs'] if (r['target'], r['witness']) == (TARGET, WITNESS)]
    assert digest(added) == 'c6b0b2199e682202df025bb5b8b72404a88453f0ef1eababc871673adaf75e70'
    result['graphs'] = [r for r in result['graphs'] if (r['target'], r['witness']) != (TARGET, WITNESS)]
    for row in result['graphs']:
        if row['target'] == TARGET:
            assert row['target_source_condition'] is None and row['target_source_alternatives'] == NEW
            if row['witness'] == 'hub2_entry':
                assert row['graph_source_condition'] == ['WADDLE_DOO', 'Beam']
                row['graph_source_condition'] = None
            row['target_source_condition'] = deepcopy(OLD)
            row['target_source_alternatives'] = None
    result['witnesses'] -= 1
    result['variants'] -= 2
    return result
