"""Generate real archives from an installed Kirby APWorld across finite option cases.

Run with the selected AP runtime as cwd and its Python interpreter. The runtime
must load only the candidate Kirby APWorld (no loose Kirby world). --output keeps
summaries and any failing case; successful temporary archives are removed after
checking their multidata and embedded patch bytes. No ROM or emulator is used.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import itertools
import json
import logging
import os
from pathlib import Path
import sys
import tempfile
import time
import importlib
import zipfile


def matrix_cases():
    """Exhaust the six graph-affecting factors; cycle independent boundary profiles."""
    health = [(lo, hi) for lo in range(1, 11) for hi in range(lo, 11)]
    graph = itertools.product(range(3), range(8), range(2), (0, 2), range(2), range(2))
    for index, (goal, boss, rooms, shards, gating, maps) in enumerate(graph):
        lo, hi = health[index % len(health)]
        yield index, {
            'goal': goal, 'configured_area_boss': boss, 'room_sanity': rooms,
            'shards': shards, 'ability_gating': gating, 'start_with_all_maps': maps,
            'minimum_health': lo, 'maximum_health': hi, 'one_hit_mode': index % 3,
            'starting_kirby_color': ([*range(19), 'random', 'random_color_per_room'])[index % 21],
            'no_extra_lives': (index // 2) % 2, 'enable_traps': index % 2,
            'trap_fill_percentage': (0, 1, 25, 99, 100)[index % 5],
            'enemy_health_multiplier': (50, 100, 500)[index % 3],
            'death_link': (index // 3) % 2, 'ability_randomization_mode': (index // 4) % 3,
            'ability_randomization_no_ability_weight': (0, 55, 100)[index % 3],
            'ability_randomization_boss_spawns': index % 2,
            'ability_randomization_minibosses': (index // 2) % 2,
            'ability_randomization_minny': (index // 3) % 2,
            'ability_randomization_passive_enemies': (index // 4) % 2,
            'ability_randomization_statues': (index // 5) % 2,
            'progression_balancing': (0, 50, 99)[index % 3],
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apworld', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seeds', type=int, nargs='+', default=[935, 202610120972, 0])
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    # Resolve the AP runtime, not the directory containing this verification tool.
    sys.path.insert(0, str(Path.cwd()))
    importlib.import_module('unittest')  # Enable AP_TEST_WORLDS in test runtimes.
    os.environ.setdefault('AP_TEST_WORLDS', 'kirbyam')
    sys.modules['pyximport'] = None
    import yaml
    import Generate
    import Main
    import Utils
    import worlds.kirbyam as world_module
    from worlds.kirbyam.data import LocationCategory, data
    from MultiServer import Context

    package = args.apworld.resolve()
    assert str(package) in world_module.__file__, world_module.__file__
    assert '.apworld/' in world_module.__file__.replace('\\', '/')
    with zipfile.ZipFile(package) as z:
        base_patch = z.read('kirbyam/data/base_patch.bsdiff4')
    room_ids = {loc.location_id for loc in data.locations.values()
                if loc.category == LocationCategory.ROOM_SANITY}
    assert len(room_ids) == 263
    args.output.mkdir(parents=True, exist_ok=True)
    cases = list(matrix_cases())[:args.limit]
    passed = slots = 0
    coverage: dict[str, set[str]] = {}
    started = time.monotonic()
    logging.disable(logging.CRITICAL)
    for index, options in cases:
        for key, value in options.items():
            coverage.setdefault(key, set()).add(str(value))
        for seed_index, seed in enumerate(args.seeds):
            players = 1 + (index + seed_index) % 2
            case_root = Path(tempfile.mkdtemp(prefix=f'case-{index}-{seed}-', dir=args.output))
            player_dir = case_root / 'players'
            player_dir.mkdir()
            for player in range(1, players + 1):
                selected = dict(options)
                if player == 2:
                    # Include heterogeneous room-sanity and health within multiworlds.
                    selected.update(room_sanity=1-options['room_sanity'], minimum_health=1,
                                    maximum_health=10, one_hit_mode=0)
                (player_dir / f'{player}.yaml').write_text(yaml.safe_dump({
                    'name': f'Probe{player}', 'game': 'Kirby & The Amazing Mirror',
                    'Kirby & The Amazing Mirror': selected,
                }), encoding='utf-8')
            try:
                settings = Generate.mystery_argparse([
                    '--seed', str(seed), '--player_files_path', str(player_dir),
                    '--outputpath', str(case_root / 'output'), '--spoiler', '0',
                ])
                settings.weights_file_path = settings.meta_file_path = None
                settings.race = False
                Main.main(*Generate.main(settings))
                archives = list((case_root / 'output').glob('*.zip'))
                assert len(archives) == 1
                with zipfile.ZipFile(archives[0]) as archive:
                    md = [n for n in archive.namelist() if n.endswith('.archipelago')]
                    patches = [n for n in archive.namelist() if n.endswith('.apkirbyam')]
                    assert len(md) == 1 and len(patches) == players
                    decoded = Context.decompress(archive.read(md[0]))
                    for player in range(1, players + 1):
                        actual = set(decoded['locations'][player]) & room_ids
                        enabled = decoded['slot_data'][player]['room_sanity']
                        assert actual == (room_ids if enabled else set())
                    for name in patches:
                        with zipfile.ZipFile(io.BytesIO(archive.read(name))) as patch:
                            assert patch.read('base_patch.bsdiff4') == base_patch
            except Exception:
                print(f'FAIL case={index} seed={seed} players={players}; retained {case_root}', flush=True)
                raise
            else:
                import shutil
                shutil.rmtree(case_root)
                passed += 1
                slots += players
            if passed % 48 == 0:
                print(f'PASS archives={passed} slots={slots}', flush=True)
    result = {'runtime': Utils.__version__, 'artifact_sha256': hashlib.sha256(package.read_bytes()).hexdigest(),
              'cases': len(cases), 'seeds': args.seeds, 'archives': passed, 'slots': slots,
              'seconds': round(time.monotonic()-started, 2),
              'option_values': {k: sorted(v) for k, v in coverage.items()},
              'scope': 'Cartesian graph factors; cycling other boundaries, not all option tuples or seeds'}
    (args.output / 'summary.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
