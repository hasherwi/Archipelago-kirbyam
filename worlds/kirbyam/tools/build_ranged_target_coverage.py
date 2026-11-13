"""Inventory normalized AP surfaces; this is coverage bookkeeping, not route proof.

Run as a module from the repository root. Production data normalization owns
location moves, logical compartments, area connectivity and RoomSanity sinks.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePath

from ..data import data

ROOT = Path(__file__).resolve().parents[1]


def _input_path_key(path: PurePath, root: PurePath) -> str:
    return path.relative_to(root).as_posix()


def build_coverage() -> dict:
    mapping = json.loads((ROOT / 'dev-docs/native-room-wikirby-map.json').read_text())
    native_by_key = {key: row['native_id'] for row in mapping['rooms'] for key in row['ap_keys']}
    regions = []
    surfaces = []
    targets = []
    for key, region in sorted(data.regions.items()):
        kind = ('room_sanity_sink' if key.endswith('__ROOM_CHECK') else
                'native_room' if key in native_by_key else 'area_or_other')
        native = native_by_key.get(key.removesuffix('__ROOM_CHECK'))
        regions.append({'region': key, 'kind': kind, 'native_room': native,
                        'locations': list(region.locations), 'exits': list(region.exits)})
        for destination in region.exits:
            surfaces.append({'owner': key, 'kind': 'exit', 'target': destination,
                             'requirement': region.exit_requirements.get(destination),
                             'room_sanity': destination.endswith('__ROOM_CHECK')})
        for location in region.locations:
            info = data.locations[location]
            surfaces.append({'owner': key, 'kind': 'location', 'target': location,
                             'requirement': region.location_requirements.get(location),
                             'room_sanity': info.category.name == 'ROOM_SANITY'})
        for target in (region.traversal or {}).get('targets', []):
            targets.append({'owner': key, 'target': target})
    inputs = [ROOT / 'data.py', ROOT / 'dev-docs/native-room-wikirby-map.json']
    inputs.extend(sorted((ROOT / 'data').rglob('*.json')))
    return {
        'schema_version': 1,
        'input_sha256': {_input_path_key(path, ROOT): hashlib.sha256(path.read_bytes()).hexdigest()
                         for path in inputs},
        'scope': 'All production-normalized AP regions, checks and exits; not a complete native attack-target census.',
        'proof_boundary': ('Structural ownership and existing rules only. A shared native room is not proof of '
                           'approach, acquisition, carry or target access.'),
        'counts': {'regions': len(regions), 'mapped_native_definitions': len(native_by_key),
                   'locations': len(data.locations), 'surfaces': len(surfaces),
                   'room_sanity_locations': sum(s['kind'] == 'location' and s['room_sanity'] for s in surfaces),
                   'installed_target_definitions': len(targets)},
        'regions': regions, 'surfaces': surfaces, 'installed_targets': targets,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(build_coverage(), indent=2) + '\n')


if __name__ == '__main__':
    main()
