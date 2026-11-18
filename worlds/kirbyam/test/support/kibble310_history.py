"""Strictly reverse the separate Sir Kibble witness for frozen historical records."""
from copy import deepcopy
import hashlib
import json

TARGET = 'switch_310_mustard_map'
WITNESS = 'hub4_kibble_cutter_entry'
OLD_CONDITION = {'source_key': 'TWISTER', 'abilities': ['UFO', 'Crash', 'Cupid', 'Cutter']}
NEW_CONDITIONS = [OLD_CONDITION, {'source_key': 'SIR_KIBBLE', 'ability': 'Cutter'}]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def before_kibble310(row):
    result = deepcopy(row)
    if result['id'] != TARGET:
        return result
    assert result.pop('requires_any_guaranteed_source') == NEW_CONDITIONS
    assert 'requires_guaranteed_source' not in result
    result['requires_guaranteed_source'] = deepcopy(OLD_CONDITION)
    added = result['graphs'].pop(WITNESS)
    assert digest(added) == '1639d0335b8e55335c3b0ac6aaf803661ab54e17989de0025e81ea334359016f'
    return result


def catalog_before_kibble310(catalog):
    result = deepcopy(catalog)
    assert (result['witnesses'], result['variants']) == (149, 298)
    added = [r for r in result['graphs'] if r['witness'] == WITNESS]
    assert digest(added) == '1a36d8b7b7f601e1773647546ee6d25e749294d8dac715f68308f3f6669bff6d'
    assert result['capability_providers'].pop('switch_310_kibble_cutter_roof_returns') == ['Cutter']
    assert result['sources'].pop('SIR_KIBBLE@0x088C3FEC') == [
        {'source_key': 'SIR_KIBBLE', 'identity': '0x088C3FEC', 'renewable': False, 'documented_retry': False}]
    result['graphs'] = [r for r in result['graphs'] if r['witness'] != WITNESS]
    for r in result['graphs']:
        if r['target'] == TARGET:
            assert r['target_source_condition'] is None and r['target_source_alternatives'] == NEW_CONDITIONS
            r['target_source_condition'] = deepcopy(OLD_CONDITION)
            r['target_source_alternatives'] = None
    result['witnesses'], result['variants'] = 148, 296
    return result
