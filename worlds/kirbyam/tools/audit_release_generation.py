#!/usr/bin/env python3
"""Durable finite release audit. No ROM/gameplay or universal-seed claim.

Plan: python -m worlds.kirbyam.tools.audit_release_generation --output DIR --plan-only
Run/resume: same command without --plan-only. Use --limit N for bounded batches.
Each case runs in a fresh process. JSONL records are flushed/fsynced after every
attempt. A candidate/options mismatch refuses resume; interrupted attempts require
--retry-incomplete and get a new directory, preserving the original output.
"""
from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Callable, Iterable, Iterator
from concurrent.futures import Future, ThreadPoolExecutor, wait, FIRST_COMPLETED
from contextlib import contextmanager
from dataclasses import asdict
import hashlib
from itertools import product
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
from typing import Any, TextIO, TYPE_CHECKING, cast

if TYPE_CHECKING:
    from BaseClasses import MultiWorld
    from worlds.kirbyam import KirbyAmWorld

# Options and decoded multidata are heterogeneous JSON records.
Record = dict[str, Any]

ROOT = Path(__file__).resolve().parents[3]
SEEDS = (105100, 20261109)


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def plan() -> list[Record]:
    profiles: list[tuple[str, Record]] = []
    for mode, gating, access, weight in product(range(3), (0, 1), ('full', 'minimal'), (0, 99, 100)):
        profiles.append(('core', {'ability_randomization_mode': mode, 'ability_gating': gating,
                                  'accessibility': access, 'ability_randomization_no_ability_weight': weight}))
    # Sixteen rows, distinct nonzero linear functions of four bits: every pair
    # of the first seven binary factors has all four combinations four times.
    factors = ('ability_randomization_statues', 'ability_randomization_passive_enemies',
               'ability_randomization_minibosses', 'ability_randomization_boss_spawns',
               'room_sanity', 'area_keys', 'start_with_all_maps')
    for row in range(16):
        options: Record = {name: (row & mask).bit_count() % 2 for mask, name in enumerate(factors, 1)}
        options.update(ability_randomization_mode=row % 3, ability_gating=(row >> 3) & 1,
                       accessibility=('full', 'minimal')[row & 1],
                       ability_randomization_no_ability_weight=(0, 99, 100)[(row // 3) % 3],
                       minimum_health=(1, 6)[row & 1], maximum_health=(1, 10)[row & 1],
                       enemy_health_multiplier=(50, 100, 500)[row % 3],
                       goal=(0, 1, 2, 4)[row % 4], configured_area_boss=row % 8,
                       required_area_bosses=(1, 8)[row & 1], shards=(0, 2)[(row >> 1) & 1])
        profiles.append(('orthogonal', options))
    cases = []
    for seed in SEEDS:
        for index, (family, options) in enumerate(profiles):
            cases.append({'id': f'{family}-{index:02}-{seed}', 'seed': seed, 'players': [options]})
        for access in ('full', 'minimal'):
            mixed = [{'ability_randomization_mode': mode, 'ability_gating': int(mode != 1),
                      'accessibility': access, 'ability_randomization_statues': 1,
                      **({'start_inventory': {'Ice Ability': 3}} if mode == 1 else {})}
                     for mode in range(3)]
            cases.append({'id': f'mixed-{access}-{seed}', 'seed': seed, 'players': mixed})
            link = [{'name': 'ReleaseShared', 'item_pool': ['Stone Ability', 'Burning Ability'],
                     'replacement_item': 'Small Food'}]
            linked = [{'ability_randomization_mode': mode, 'ability_gating': 1,
                       'accessibility': access, 'item_links': link} for mode in (0, 2)]
            cases.append({'id': f'itemlink-{access}-{seed}', 'seed': seed, 'players': linked})
    return cases


def product_plan() -> list[Record]:
    """Exactly the defined public product, at one fixed seed; other defaults fixed."""
    flags = ('ability_randomization_statues', 'ability_randomization_passive_enemies',
             'ability_randomization_minibosses', 'ability_randomization_boss_spawns',
             'room_sanity', 'area_keys')
    cases = []
    axes = product(range(3), (0, 1), ('full', 'minimal'), (0, 99, 100), product((0, 1), repeat=6))
    for index, (mode, gating, access, weight, bits) in enumerate(axes):
        options: Record = dict(zip(flags, bits))
        options.update(ability_randomization_mode=mode, ability_gating=gating,
                       accessibility=access, ability_randomization_no_ability_weight=weight)
        cases.append({'id': f'product-{index:04}-105100', 'seed': 105100, 'players': [options]})
    return cases


@contextmanager
def exclusive_lock(path: Path) -> Iterator[TextIO]:
    """POSIX lifetime lease, inherited by a child when explicitly passed."""
    import fcntl
    with path.open('a+') as lease:
        try:
            fcntl.flock(lease.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError('Audit/worker still running: ' + str(path)) from error
        yield lease
        # Do not explicitly LOCK_UN: a surviving child may share this open file
        # description and must retain its lease after the parent closes its copy.


def assert_attempt_idle(directory: Path) -> None:
    with exclusive_lock(directory / 'worker.lease'):
        pass


def candidate() -> Record:
    # Include all tracked world files and generation core. Working bytes matter,
    # not just HEAD, so tests cannot accidentally resume across an uncommitted edit.
    paths = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    selected = [p for p in paths if p and (p.startswith('worlds/kirbyam/') or
                p in {'Main.py', 'Generate.py', 'BaseClasses.py', 'Options.py', 'Fill.py', 'worlds/AutoWorld.py'})]
    script = Path(__file__).resolve().relative_to(ROOT).as_posix()
    if script not in selected:
        selected.append(script)
    hashes = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sorted(selected)}
    return {'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip(),
            'tree': subprocess.check_output(['git', 'rev-parse', 'HEAD^{tree}'], cwd=ROOT).decode().strip(),
            'source_digest': digest(hashes), 'source_files': hashes}


def append_record(path: Path, record: Record) -> None:
    with path.open('a') as stream:
        stream.write(json.dumps(record, sort_keys=True) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def recover_completed_result(directory: Path, case: Record) -> Record | None:
    """Recover a finished child result, never infer completion from an archive alone."""
    assert_attempt_idle(directory)
    return validate_completed_result(directory, case)


def validate_completed_result(directory: Path, case: Record) -> Record | None:
    """Check result identity and output bytes while the caller owns/excludes work."""
    path = directory / 'result.json'
    if not path.exists():
        return None
    saved_case = json.loads((directory / 'case.json').read_text())
    result: Record = json.loads(path.read_text())
    if (saved_case != case or result.get('case_id') != case['id']
            or result.get('seed') != case['seed'] or result.get('options') != case['players']):
        raise ValueError('Preserved result/case mismatch: ' + case['id'])
    archives = list(directory.glob('output/*.zip'))
    if result.get('archive_count') != len(archives):
        raise ValueError('Preserved archive count mismatch: ' + case['id'])
    if result.get('outcome') == 'accepted_archive':
        name = result['archive_name']
        if Path(name).name != name or len(archives) != 1:
            raise ValueError('Invalid preserved archive identity')
        archive = directory / 'output' / name
        if hashlib.sha256(archive.read_bytes()).hexdigest() != result['archive_sha256']:
            raise ValueError('Preserved archive hash mismatch: ' + case['id'])
    elif result.get('outcome', '').startswith('refused') and archives:
        raise ValueError('Refused attempt has an archive')
    return result


def audit_archive(multiworld: MultiWorld, decoded: Record, archive: Path) -> list[Record]:
    from worlds.kirbyam.enemy_ability_data import (ABILITY_NAME_TO_ID, GATEABLE_ENEMY_COPY_ABILITIES,
                                                   VALID_ENEMY_COPY_ABILITIES, starting_copy_abilities)
    from worlds.kirbyam.test.test_cutter_progression import _gate_words
    from worlds.kirbyam.test.support.check_accessibility import audit_local_checks
    gates = _gate_words(archive)
    placed = Counter((value[1], value[0]) for locations in decoded['locations'].values()
                     for value in locations.values())
    records = []
    for player in multiworld.player_ids:
        world = cast("KirbyAmWorld", multiworld.worlds[player])
        gating = bool(world.options.ability_gating.value)
        explicit = world.options.start_inventory.value
        starts = Counter(decoded['precollected_items'][player])
        expected_starts = {world.item_name_to_id[name]: count for name, count in explicit.items()}
        for name in starting_copy_abilities(world.options.ability_randomization_mode.value):
            expected_starts.setdefault(world.item_name_to_id[name + ' Ability'], 1)
        ability_codes = {world.item_name_to_id[name + ' Ability'] for name in ABILITY_NAME_TO_ID
                         if name + ' Ability' in world.item_name_to_id}
        actual_starts = {code: starts[code] for code in ability_codes if starts[code]}
        assert actual_starts == {code: count for code, count in expected_starts.items() if code in ability_codes}
        expected_gate = 0x03FFFF7E if gating else 0
        assert gates[player] == expected_gate
        assert set(decoded['slot_data'][player]['ability_gateable_abilities']) == (
            set(GATEABLE_ENEMY_COPY_ABILITIES) if gating else set())
        whitelist = set(decoded['slot_data'][player]['enemy_copy_ability_whitelist'])
        assert whitelist == set(VALID_ENEMY_COPY_ABILITIES) and 'Beam' in whitelist
        assert gates[player] & (1 << ABILITY_NAME_TO_ID['Beam']) == 0
        linked = {}
        for group_id, group in multiworld.groups.items():
            if player in group['players']:
                for name in group['item_pool']:
                    linked[world.item_name_to_id[name]] = group_id
        pool = {}
        for name in GATEABLE_ENEMY_COPY_ABILITIES:
            code = world.item_name_to_id[name + ' Ability']
            owner = linked.get(code, player)
            count = placed[owner, code]
            assert count == int(gating and name not in starting_copy_abilities(0)), (player, name, owner, count)
            if owner != player:
                assert placed[player, code] == 0
            pool[name] = {'owner': owner, 'placed': count}
        assert placed[player, world.item_name_to_id['Beam Ability']] == 0
        audit_start = time.perf_counter()
        closure = audit_local_checks(multiworld, player)
        assert not closure.unfilled and not closure.inventory_unreachable and not closure.progression_unreachable
        records.append({'player': player, 'gate_mask': hex(gates[player]),
                        'enemy_copy_whitelist': sorted(whitelist), 'ability_starts': actual_starts,
                        'ability_pool': pool, 'closure': asdict(closure),
                        'closure_seconds': time.perf_counter() - audit_start})
    return records


def worker(case_path: Path, result_path: Path) -> None:
    # Auditing must never install packages or prompt to change the environment.
    os.environ['SKIP_REQUIREMENTS_UPDATE'] = '1'
    import pytest
    from worlds.kirbyam import check_accessibility
    from worlds.kirbyam.test.test_cutter_progression import _generate
    import worlds.kirbyam as kirby
    case = json.loads(case_path.read_text())
    result: Record = {'case_id': case['id'], 'seed': case['seed'], 'options': case['players'],
                      'scope': 'Generated patch/archive structure and logical closure; not applied-ROM gameplay.'}
    began = time.perf_counter()
    phase = 'setup'
    assignment_runs: list[Record] = []
    production_audits: list[float] = []
    original_select: Callable[..., Record] = getattr(kirby, "validate_peg_assignment")
    original_validate = check_accessibility.validate_all_checks

    def select(initial: Record, factory: Callable[[], Record], include_statues: bool, **kwargs: Any) -> Record:
        nonlocal phase
        phase = 'source_policy'
        attempts = 1
        start = time.perf_counter()

        def counted() -> Record:
            nonlocal attempts
            attempts += 1
            return factory()
        try:
            selected = original_select(initial, counted, include_statues, **kwargs)
            phase = 'generation'
            return selected
        except Exception:
            phase = 'source_policy_refusal_or_error'
            raise
        finally:
            assignment_runs.append({'attempts': attempts, 'seconds': time.perf_counter() - start})

    def validate(multiworld: MultiWorld, players: Iterable[int]) -> None:
        nonlocal phase
        phase = 'all_check_guard'
        start = time.perf_counter()
        try:
            return original_validate(multiworld, players)
        finally:
            production_audits.append(time.perf_counter() - start)
    try:
        with pytest.MonkeyPatch.context() as patch:
            patch.setattr(kirby, 'validate_peg_assignment', select)
            patch.setattr(check_accessibility, 'validate_all_checks', validate)
            phase = 'generation'
            multiworld, decoded, archive = _generate(patch, case_path.parent, case['seed'], case['players'])
            phase = 'archive_contract'
            result['players'] = audit_archive(multiworld, decoded, archive)
            result['archive_sha256'] = hashlib.sha256(archive.read_bytes()).hexdigest()
            result['archive_name'] = archive.name
            result['outcome'] = 'accepted_archive'
    except check_accessibility.KirbyAmCheckAccessibilityError as error:
        result.update(outcome='refused_all_check_guard', error=str(error), phase=phase)
    except Exception as error:
        # Never call an arbitrary ValueError a safe refusal. The traceback and
        # phase remain available for manual classification and repair.
        known_budget_refusal = (isinstance(error, ValueError) and phase == 'source_policy_refusal_or_error'
                                and str(error).startswith('Reviewed ')
                                and 'search budget exhausted after' in str(error))
        result.update(outcome='refused_source_policy_budget' if known_budget_refusal else 'unexpected_error',
                      error=str(error), error_type=type(error).__name__,
                      phase=phase, traceback=traceback.format_exc())
    result.update(seconds=time.perf_counter() - began, source_assignment_runs=assignment_runs,
                  production_audit_seconds=production_audits)
    archives = list(case_path.parent.glob('output/*.zip'))
    if result['outcome'].startswith('refused') and archives:
        result['outcome'] = 'unexpected_archive_after_refusal'
    result['archive_count'] = len(archives)
    try:
        import resource
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        result['peak_rss_bytes'] = int(peak if sys.platform == 'darwin' else peak * 1024)
    except ImportError:
        result['peak_rss_bytes'] = None
    temporary = result_path.with_suffix('.tmp')
    with temporary.open('w') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(result_path)


def run_attempt(case: Record, directory: Path, timeout: float) -> Record:
    """Run one isolated worker. No journal writes occur in executor threads."""
    case_path = directory / 'case.json'
    with exclusive_lock(directory / 'worker.lease') as lease, (directory / 'worker.log').open('w') as log:
        try:
            process = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--worker', str(case_path),
                                      '--result', str(directory / 'result.json')], cwd=ROOT,
                                     stdout=log, stderr=subprocess.STDOUT, timeout=timeout,
                                     pass_fds=(lease.fileno(),))
            result_path = directory / 'result.json'
            return cast(Record, validate_completed_result(directory, case)) if (
                process.returncode == 0 and result_path.exists()) else {
                'case_id': case['id'], 'outcome': 'worker_failure', 'returncode': process.returncode}
        except subprocess.TimeoutExpired:
            return {'case_id': case['id'], 'outcome': 'timeout', 'seconds': timeout}


def run_pending(pending: list[Record], output: Path, journal: Path, old: list[Record],
                source_digest: str, jobs: int, timeout: float) -> None:
    """Bounded dispatch; only this coordinating thread writes durable records."""
    if len({case['id'] for case in pending}) != len(pending):
        raise ValueError('Duplicate pending case IDs')
    iterator = iter(pending)
    futures: dict[Future[Record], tuple[Record, int]] = {}
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        def dispatch() -> bool:
            case = next(iterator, None)
            if case is None:
                return False
            attempt = sum(r['event'] == 'started' and r['case_id'] == case['id'] for r in old) + 1
            directory = output / f"{case['id']}-attempt{attempt}"
            directory.mkdir()
            (directory / 'case.json').write_text(json.dumps(case, indent=2))
            append_record(journal, {'event': 'started', 'case_id': case['id'], 'attempt': attempt,
                                    'source_digest': source_digest})
            futures[pool.submit(run_attempt, case, directory, timeout)] = (case, attempt)
            return True
        for _ in range(jobs):
            if not dispatch():
                break
        while futures:
            done, _ = wait(futures, return_when=FIRST_COMPLETED)
            for future in done:
                case, attempt = futures.pop(future)
                result = future.result()
                append_record(journal, {'event': 'completed', 'attempt': attempt, **result})
                print(json.dumps({'case_id': case['id'], 'outcome': result['outcome']}), flush=True)
                dispatch()


def require_parallel_settings(jobs: int) -> None:
    """Do not let fresh workers race the shared default-settings bootstrap."""
    if jobs > 1 and not any((ROOT / name).is_file() for name in ('options.yaml', 'host.yaml')):
        raise SystemExit(
            'Parallel audit requires existing options.yaml or host.yaml in the source checkout. '
            'Initialize sequentially with --jobs 1 --limit 1, then resume with --jobs 2 (or more). '
            'No configuration was created or changed by this preflight.')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--plan-only', action='store_true')
    parser.add_argument('--plan', choices=('sample112', 'product2304'), default='sample112')
    parser.add_argument('--jobs', type=int, choices=range(1, 5), default=1)
    parser.add_argument('--limit', type=int)
    parser.add_argument('--case', action='append', help='Run only exact case IDs (repeatable).')
    parser.add_argument('--retry-incomplete', action='store_true')
    parser.add_argument('--timeout', type=int, default=600)
    parser.add_argument('--worker', type=Path)
    parser.add_argument('--result', type=Path)
    args = parser.parse_args()
    if args.worker:
        worker(args.worker, args.result)
        return
    if not args.output:
        parser.error('--output is required')
    if not args.plan_only:
        require_parallel_settings(args.jobs)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    cases = product_plan() if args.plan == 'product2304' else plan()
    scope = ('Full defined2304 product at seed105100; not all goals, health settings or seeds.'
             if args.plan == 'product2304' else
             'Finite core and orthogonal sample, not exhaustive option/seed coverage.')
    manifest = {
        'schema': 2, 'plan': args.plan, 'scope': scope,
        'candidate': candidate(), 'cases': cases, 'options_digest': digest(cases),
        'dimension_values_explicit': {
            name: sorted({json.dumps(p.get(name, '<default>'), sort_keys=True)
                          for c in cases for p in c['players']})
            for name in sorted({key for c in cases for p in c['players'] for key in p})
        },
        'binary_orthogonal_factors': (
            ['ability_randomization_statues', 'ability_randomization_passive_enemies',
             'ability_randomization_minibosses', 'ability_randomization_boss_spawns',
             'room_sanity', 'area_keys', 'start_with_all_maps']
            if args.plan == 'sample112' else []),
    }
    manifest_path = output / 'manifest.json'
    if manifest_path.exists():
        if json.loads(manifest_path.read_text()) != manifest:
            raise SystemExit('Candidate/options changed; use a new output directory.')
    else:
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    if args.plan_only:
        print(json.dumps({'cases': len(cases), 'options_digest': manifest['options_digest'],
                          'source_digest': manifest['candidate']['source_digest']}))
        return
    journal = output / 'results.jsonl'
    old = [json.loads(line) for line in journal.read_text().splitlines()] if journal.exists() else []
    complete = {r['case_id'] for r in old if r['event'] == 'completed'}
    incomplete = {r['case_id'] for r in old if r['event'] == 'started'} - complete
    # A child may finish after the coordinating process is interrupted. The
    # manifest comparison above pins its source/options; validate its own case,
    # result and archive before recording completion, without regenerating it.
    for case_id in sorted(incomplete):
        case = next(c for c in cases if c['id'] == case_id)
        attempt = max(r['attempt'] for r in old if r['event'] == 'started' and r['case_id'] == case_id)
        result = recover_completed_result(output / f"{case_id}-attempt{attempt}", case)
        if result is not None:
            append_record(journal, {'event': 'completed', 'attempt': attempt,
                                    'reconciled_preserved_result': True, **result})
            complete.add(case_id)
    incomplete -= complete
    if incomplete and not args.retry_incomplete:
        raise SystemExit('Interrupted cases preserved; inspect them, then use --retry-incomplete: '
                         + ','.join(sorted(incomplete)))
    pending = [c for c in cases if c['id'] not in complete and (not args.case or c['id'] in args.case)]
    run_pending(pending[:args.limit], output, journal, old, manifest['candidate']['source_digest'],
                args.jobs, args.timeout)
    # Completed outcomes retain their original attempt and are never silently replaced.
    records = [json.loads(line) for line in journal.read_text().splitlines()] if journal.exists() else []
    counts = Counter(r['outcome'] for r in records if r['event'] == 'completed')
    summary = {
        'planned': len(cases), 'outcomes': counts,
        'candidate_digest': manifest['candidate']['source_digest'], 'options_digest': manifest['options_digest'],
        'total_completed_seconds': sum(r.get('seconds', 0) for r in records if r['event'] == 'completed'),
        'not_a_universal_seed_or_native_gameplay_proof': True,
    }
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')


if __name__ == '__main__':
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    # One coordinator per durable output directory. Worker processes retain only
    # their individual attempt lease, so completed orphans can be reconciled.
    routing = argparse.ArgumentParser(add_help=False)
    routing.add_argument('--output', type=Path)
    routing.add_argument('--worker', type=Path)
    route, _ = routing.parse_known_args()
    if route.output is not None and route.worker is None:
        output = route.output.resolve()
        output.mkdir(parents=True, exist_ok=True)
        with exclusive_lock(output / 'coordinator.lease'):
            main()
    else:
        main()
