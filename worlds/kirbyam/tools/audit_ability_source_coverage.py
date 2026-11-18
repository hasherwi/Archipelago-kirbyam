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
            for identity in value.get('inventory_alternatives', []):
                references.append({'path': path, 'inventory_id': identity,
                                   'exclusive_alternative': True})
            if 'graphs' in value and (
                'requires_guaranteed_source' in value or 'requires_any_guaranteed_source' in value
            ):
                scoped_targets.append({'id': value['id'], 'fail_closed': value.get('fail_closed', False)})
            for key, child in value.items():
                walk(child, f'{path}/{key}')
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f'{path}/{index}')
        elif isinstance(value, str) and value in {
            'CanCutRopes', 'CanBreakBlocks', 'CanUseMini', 'CanLightFuses', 'CanPoundPegs',
            'can_break_block', 'can_cut_ropes', 'can_use_mini', 'can_light_fuses', 'can_pound_pegs',
            'can_break_floating_block', 'can_break_metal', 'can_break_metal_throw',
            'can_climb', 'can_fly', 'can_swim', 'can_wheel', 'can_mirra',
            'can_hit_far_switch', 'can_get_rr_map_chest',
        }:
            compact_requirements.append({'path': path, 'token': value})

    walk(rooms, 'rooms')
    references.extend({'witness_identity': key, 'inventory_id': value}
                      for key, value in inventory['reviewed_bindings'].items())
    known = {p['id'] for p in inventory['placements'] + inventory['generated_statue_slots']
             + inventory.get('spawner_outputs', []) + inventory.get('encounter_sources', [])}
    referenced = {row['inventory_id'] for row in references}
    bound = known & referenced
    relevant = [p for p in inventory['placements'] if p['source_type'] != 'other_object']
    return {
        'version': 1, 'issue': 1114, 'complete': False,
        'native_rooms': len(inventory['rooms']),
        'declared_ap_regions': len(inventory.get('ap_region_inventory', [])),
        'unmapped_ap_regions': [row['region'] for row in inventory.get('ap_region_inventory', [])
                               if row['mapping_evidence'] == 'unresolved'],
        'unused_native_room_slots': sum(r['unused_room_slot'] for r in inventory['rooms']),
        'empty_static_records': sum(not r['placements'] for r in inventory['rooms']),
        'static_placements': len(inventory['placements']),
        'static_types': dict(sorted(Counter(p['source_type'] for p in inventory['placements']).items())),
        'unknown_inventory_references': sorted(referenced - known),
        'reviewed_inventory_references': len(references), 'distinct_referenced_placements': len(bound),
        'unbound_source_or_encounter_placements': [p['id'] for p in relevant if p['id'] not in bound],
        'encounter_controller_call_pairs': len(inventory['encounter_calls']),
        'distinct_encounter_call_sites': len({row.get('evidence') for row in inventory['encounter_calls']
                                            if row.get('evidence')}),
        'known_dynamic_grant_types': len(inventory['dynamic_grant_types']),
        'generated_statue_slots': len(inventory['generated_statue_slots']),
        'object_spawner_outputs': len(inventory['spawner_outputs']),
        'encounter_source_candidates': len(inventory.get('encounter_sources', [])),
        'compact_requirements_requiring_target_context_review': compact_requirements,
        'policy_scoped_targets': scoped_targets,
        'blockers': [
            'Static presence is complete; acquisition compartments, spawn-state predicates and carry routes are not.',
            ('Encounter call sites are candidates, not a complete dynamic call graph; '
             'indirect helpers, phase-specific branches and lifetime prerequisites need review.'),
            ('Object-spawner output types are decoded; their acquisition/lifetime and routes to the two native '
             'random-statue slots remain unresolved.'),
            ('Legacy ability tokens and policy-scoped fallbacks remain; closing them needs accepted source routes '
             'or established Normal alternatives, not blanket rejection.'),
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
