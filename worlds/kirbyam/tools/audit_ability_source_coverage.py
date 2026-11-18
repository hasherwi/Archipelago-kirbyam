"""Report inventory and witness gaps without declaring unproved routes impossible."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def audit(inventory: dict, rooms: dict) -> dict:
    references = []
    compact_requirements = []
    scoped_targets = []

    def walk(value, path):
        if isinstance(value, dict):
            if 'inventory_id' in value:
                references.append({'path': path, 'inventory_id': value['inventory_id']})
            for key, child in value.items():
                walk(child, f'{path}/{key}')
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f'{path}/{index}')
        elif isinstance(value, str) and value in {
            'CanCutRopes', 'CanBreakBlocks', 'CanUseMini', 'CanLightFuses', 'CanPoundPegs',
            'can_break_block', 'can_cut_ropes', 'can_use_mini', 'can_light_fuses', 'can_pound_pegs',
        }:
            compact_requirements.append({'path': path, 'token': value})

    walk(rooms, 'rooms')
    for room in rooms.values():
        for target in room.get('traversal', {}).get('targets', []):
            if 'requires_guaranteed_source' in target or 'requires_any_guaranteed_source' in target:
                scoped_targets.append({'id': target['id'], 'fail_closed': target.get('fail_closed', False)})
    bound = set(inventory['reviewed_bindings'].values())
    references = [{'witness_identity': key, 'inventory_id': value}
                  for key, value in inventory['reviewed_bindings'].items()]
    relevant = [p for p in inventory['placements'] if p['source_type'] != 'other_object']
    return {
        'version': 1, 'issue': 1114, 'complete': False,
        'native_rooms': len(inventory['rooms']),
        'unused_native_room_slots': sum(r['unused_room_slot'] for r in inventory['rooms']),
        'empty_static_records': sum(not r['placements'] for r in inventory['rooms']),
        'static_placements': len(inventory['placements']),
        'static_types': dict(sorted(Counter(p['source_type'] for p in inventory['placements']).items())),
        'reviewed_inventory_references': len(references), 'distinct_referenced_placements': len(bound),
        'unbound_source_or_encounter_placements': [p['id'] for p in relevant if p['id'] not in bound],
        'encounter_call_sites': len(inventory['encounter_calls']),
        'known_dynamic_grant_types': len(inventory['dynamic_grant_types']),
        'compact_requirements_requiring_target_context_review': compact_requirements,
        'policy_scoped_targets': scoped_targets,
        'blockers': [
            'Static presence is complete; acquisition compartments, spawn-state predicates and carry routes are not.',
            'Encounter call sites are candidates, not a complete dynamic call graph; indirect helpers, variable types and lifetime prerequisites need review.',
            'Object-spawner descendants and random-statue runtime semantics remain unresolved.',
            'Legacy ability tokens and policy-scoped fallbacks remain; closing them needs accepted source routes or established Normal alternatives, not blanket rejection.',
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(json.loads((ROOT / 'data/ability_source_inventory.json').read_text()),
                   json.loads((ROOT / 'data/regions/rooms.json').read_text()))
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(f"{result['reviewed_inventory_references']} references, "
          f"{result['distinct_referenced_placements']} distinct placements; issue remains incomplete")


if __name__ == '__main__':
    main()
