"""Report inventory and witness gaps without declaring unproved routes impossible."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def audit(inventory: dict, rooms: dict, *, include_references: bool = False) -> dict:
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
        **({'inventory_references': references} if include_references else {}),
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


def acquisition_backlog(inventory: dict, report: dict) -> dict:
    """Index unbound source candidates by native room, not AP compartment."""
    # Explicit and legacy references both count, including all alternatives.
    referenced = {reference['inventory_id'] for reference in report['inventory_references']}
    aliases = {}
    for region in inventory.get('ap_region_inventory', []):
        for native_room in region.get('native_rooms', []):
            aliases.setdefault(native_room, set()).add(region['region'])

    by_room = {}
    counts = Counter()
    outside_adventure = 0
    for kind in ('placements', 'generated_statue_slots', 'spawner_outputs', 'encounter_sources'):
        for row in inventory.get(kind, []):
            identity = row['id']
            if identity in referenced:
                continue
            if not (row.get('source_key') or row.get('possible_source_keys')
                    or row.get('native_grant_states') or row.get('native_grant') not in (None, 'Normal')):
                continue
            if row.get('world_access', {}).get('status') == 'outside_adventure':
                outside_adventure += 1
                continue
            room = row['native_room']
            counts[kind] += 1
            by_room.setdefault(room, []).append({
                'id': identity, 'inventory_kind': kind, 'source_type': row['source_type'],
                'native_grant': row.get('native_grant'), 'source_key': row.get('source_key'),
                'possible_source_keys': row.get('possible_source_keys', []),
                'has_phase_dependent_grant': bool(row.get('native_grant_states')),
            })
    return {
        'version': 1,
        'scope': 'Unbound, potentially granting physical records. Not accessible sources or proven routes.',
        'outside_adventure_candidates_omitted': outside_adventure,
        'candidate_counts_by_inventory_kind': dict(sorted(counts.items())),
        'rooms': [
            {'native_room': room, 'candidate_ap_regions': sorted(aliases.get(room, ())),
             'sources': sorted(by_room[room], key=lambda row: row['id'])}
            for room in sorted(by_room)
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--acquisition-backlog', type=Path,
                        help='Also write unbound potential source records grouped by native room.')
    args = parser.parse_args()
    inventory = json.loads((ROOT / 'data/ability_source_inventory.json').read_text())
    result = audit(inventory, json.loads((ROOT / 'data/regions/rooms.json').read_text()),
                   include_references=args.acquisition_backlog is not None)
    if args.acquisition_backlog is not None:
        backlog = acquisition_backlog(inventory, result)
        args.acquisition_backlog.write_text(json.dumps(backlog, indent=2) + '\n')
        del result['inventory_references']
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(f"{result['reviewed_inventory_references']} references, "
          f"{result['distinct_referenced_placements']} distinct placements; issue remains incomplete")


if __name__ == '__main__':
    main()
