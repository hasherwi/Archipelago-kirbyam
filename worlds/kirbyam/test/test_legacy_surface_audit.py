"""Keep Normal movement, covered targets and unresolved route evidence distinct."""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from .. import rules
from ..tools.audit_legacy_ability_surfaces import build_audit, classify


@pytest.mark.parametrize('token', ['can_fly', 'can_swim', 'can_climb'])
def test_normal_movement_does_not_call_pending_equipment_fallback(monkeypatch, token):
    def forbidden(*args):
        raise AssertionError('Normal movement must not request an ability fallback')
    monkeypatch.setattr(rules, '_allow_pending_ability_gate', forbidden)
    assert rules.evaluate_room_logic_requirement(token, SimpleNamespace(), 1)
    state = SimpleNamespace(has=lambda item, player: False)
    assert not rules.evaluate_room_logic_requirement({'all': [token, {'item': 'Cutter Ability'}]}, state, 1)
    assert rules.evaluate_room_logic_requirement({'any': [token, {'item': 'Cutter Ability'}]}, state, 1)


def test_saved_audit_matches_normalized_surfaces_without_declaring_completion():
    record = json.loads((Path(__file__).resolve().parents[1]
                         / 'dev-docs/legacy-ability-surface-audit.json').read_text())
    assert record == build_audit()
    assert not record['complete']
    assert record['counts'] == {'installed_witness': 29, 'lever_item': 8, 'normal_movement': 218,
                                'policy_scoped_witness': 2, 'unresolved_action_context': 156}
    assert record['policy_fallback_targets'] == ['bomb_517_chocolate', 'bomb_733_yellow', 'switch_310_mustard_map']
    assert 'switch_533_room16' not in record['policy_fallback_targets']


def test_audit_matches_exact_direction_and_preserves_boolean_alternatives():
    requirement = {'any': ['can_use_mini', {'all': ['can_fly', {'item': 'Key'}]}]}
    surface = {'owner': 'A', 'kind': 'exit', 'target': 'B', 'requirement': requirement}
    snapshot = deepcopy(surface)
    target = {'id': 'mini', 'region': 'B', 'exit': 'A'}
    report = classify([surface], [target])
    assert report['counts']['unresolved_action_context'] == 1
    assert surface == snapshot and report['surfaces'][0]['requirement'] == requirement
    target.update(region='A', exit='B')
    report = classify([surface], [target])
    assert report['counts']['installed_witness'] == 1
    assert report['counts']['normal_movement'] == 1
    assert report['surfaces'][0]['installed_targets'] == ['mini']
