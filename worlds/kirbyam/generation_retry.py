"""Opt-in, transactional single-player generation at Archipelago's main boundary."""
from copy import deepcopy
import hashlib
import json
import logging
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import zipfile

from Fill import FillError
from Utils import output_path
from .check_accessibility import KirbyAmCheckAccessibilityError

MAX_ATTEMPTS = 8
GAME = 'Kirby & The Amazing Mirror'


class KirbyAmGenerationRetryExhausted(FillError):
    """No audited archive was produced within the deterministic attempt budget."""


def attempt_seed(seed: int, attempt: int) -> int:
    if attempt == 0:
        return seed
    payload = f'kirbyam-placement-retry-v1:{seed}:{attempt}'.encode('ascii')
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], 'big')


def generate(args, seed: int, baked_server_options=None):
    """Keep rolled options fixed; discard each failed world and its staged output.

    This intentionally does not patch Main.main or modify an existing fill. Other
    entry points retain the ordinary audit. Multiworld/race need a separately
    supported coordinator and are rejected before any generation side effects.
    """
    import Main
    if args.multi != 1 or args.game != {1: GAME}:
        raise ValueError('KirbyAM retry generation supports one KirbyAM player only; use ordinary generation for multiworld.')
    if args.race or type(seed) is not int:
        raise ValueError('KirbyAM retries require a reproducible integer seed and race mode off.')
    if args.csv_output or args.spoiler_only:
        raise ValueError('KirbyAM retries support standard archives or skip_output, not CSV/spoiler-only output.')
    destination = Path(args.outputpath or output_path()).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    baseline = deepcopy(args)
    server_options = deepcopy(baked_server_options)
    prior_output = getattr(output_path, 'cached_path', None)
    failures = []
    try:
        for attempt in range(MAX_ATTEMPTS):
            current_seed = attempt_seed(seed, attempt)
            with TemporaryDirectory(prefix='.kirbyam-retry-', dir=destination) as temporary:
                current = deepcopy(baseline)
                current.outputpath = temporary
                try:
                    world = Main.main(current, current_seed, deepcopy(server_options))
                except KirbyAmCheckAccessibilityError as error:
                    if not error.retryable_placement:
                        raise
                    failures.append({'attempt': attempt + 1, 'seed': current_seed, 'reason': str(error)})
                    logging.warning('KirbyAM placement attempt %s/%s rejected (seed %s): %s',
                                    attempt + 1, MAX_ATTEMPTS, current_seed, error)
                    continue
                receipt = {'schema': 1, 'input_seed': seed, 'successful_seed': current_seed,
                           'attempt': attempt + 1, 'attempt_cap': MAX_ATTEMPTS, 'failures': failures}
                world.kirbyam_generation_retry = receipt
                if not args.skip_output:
                    archives = list(Path(temporary).glob('*.zip'))
                    if len(archives) != 1:
                        raise RuntimeError('KirbyAM generation did not produce exactly one validated archive.')
                    archive = archives[0]
                    with zipfile.ZipFile(archive, 'a', compression=zipfile.ZIP_DEFLATED) as output:
                        output.writestr('kirbyam-generation-attempts.json', json.dumps(receipt, indent=2) + '\n')
                    # Same-filesystem, atomic no-clobber publication; no partial
                    # archive becomes visible, including on a name collision.
                    os.link(archive, destination / archive.name)
                logging.info('KirbyAM validated attempt %s/%s: input seed %s, successful seed %s',
                             attempt + 1, MAX_ATTEMPTS, seed, current_seed)
                return world
        raise KirbyAmGenerationRetryExhausted(
            f'KirbyAM exhausted {MAX_ATTEMPTS} deterministic placement attempts for input seed {seed}; '
            'no archive published. Settings were unchanged. Last audit:\n' + failures[-1]['reason'])
    finally:
        if prior_output is None:
            if hasattr(output_path, 'cached_path'):
                del output_path.cached_path
        else:
            output_path.cached_path = prior_output


def main(*arguments: str) -> None:
    """Launcher entry point; roll requested YAML/options once, then retry fill."""
    import Generate
    previous = sys.argv
    try:
        sys.argv = [previous[0], *arguments]
        args, seed = Generate.main()
        generate(args, seed)
    finally:
        sys.argv = previous


if __name__ == '__main__':
    main(*sys.argv[1:])
