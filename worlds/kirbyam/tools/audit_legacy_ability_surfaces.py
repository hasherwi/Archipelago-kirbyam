"""Classify normalized compact requirements without inventing route evidence."""
from collections import Counter
import json
from pathlib import Path

from ..conditional_routes import CANDY_FUSE
from ..rules import (_NORMAL_MOVEMENT_REQUIREMENTS, _ROOM_LEVER_WALL_ITEMS,
                     normal_movement_satisfies_requirement)
from ..traversal_data import _room_catalog
from .build_ranged_target_coverage import build_coverage

ROOT = Path(__file__).resolve().parents[1]


CANDY912_FUSE_TARGET = CANDY_FUSE.TARGET

def tokens(requirement):
    if isinstance(requirement, str):
        yield requirement
    elif isinstance(requirement, dict):
        for operator, operands in requirement.items():
            if operator in ('all', 'any'):
                for operand in operands:
                    yield from tokens(operand)


def classify(surfaces, targets):
    rows = []
    totals = Counter()
    for surface in surfaces:
        terms = list(tokens(surface['requirement']))
        if not terms:
            continue
        matched = [target for target in targets if target.get('region') == surface['owner']
                   and target.get('exit' if surface['kind'] == 'exit' else 'location') == surface['target']]
        scoped = any(target.get('requires_guaranteed_source') or target.get('requires_any_guaranteed_source')
                     for target in matched if not target.get('fail_closed'))
        classified = []
        for token in terms:
            if token in _NORMAL_MOVEMENT_REQUIREMENTS:
                category = 'normal_movement'
            elif token in _ROOM_LEVER_WALL_ITEMS:
                category = 'lever_item'
            elif matched:
                category = 'policy_scoped_witness' if scoped else 'installed_witness'
            elif normal_movement_satisfies_requirement(surface['requirement']):
                category = 'declared_normal_alternative'
            else:
                category = 'unresolved_action_context'
            totals[category] += 1
            classified.append({'token': token, 'category': category})
        rows.append({**surface, 'tokens': classified,
                     'installed_targets': [target['id'] for target in matched]})
    fallbacks = [target['id'] for target in targets
                 if (target.get('requires_guaranteed_source') or target.get('requires_any_guaranteed_source'))
                 and not target.get('fail_closed') and target['id'] != CANDY912_FUSE_TARGET]
    return {'version': 1, 'issue': 1119, 'complete': False,
            'counts': dict(sorted(totals.items())), 'surfaces': rows,
            'policy_fallback_targets': sorted(fallbacks),
            'scope': 'Normalized AP requirement surfaces; exact Boolean alternatives are preserved.',
            'limitations': [
                'An installed target is structural coverage, not proof that every source policy is supported.',
                'Declared Normal alternatives are existing Boolean rules, not newly verified physical routes.',
                'Unresolved action tokens do not prove an ability is required or a Normal route impossible.',
                'No global ability source reachability, room-wide acquisition or three-room carry rule is inferred.']}


def build_audit():
    return classify(build_coverage()['surfaces'], _room_catalog()[0])


def main():
    output = ROOT / 'dev-docs/legacy-ability-surface-audit.json'
    output.write_text(json.dumps(build_audit(), indent=2) + '\n')


if __name__ == '__main__':
    main()
