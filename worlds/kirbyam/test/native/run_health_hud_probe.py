"""Optional private-ROM instruction regression; no full ROM or save output."""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile

import bsdiff4


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', required=True, type=Path, help='Private, clean USA ROM')
    parser.add_argument('--mgba-prefix', required=True, type=Path,
                        help='Existing mGBA development prefix containing include/ and lib/')
    parser.add_argument('--library-dir', required=True, type=Path,
                        help='Existing directory containing libmgba and its dependencies')
    parser.add_argument('--patch', type=Path,
                        default=Path(__file__).resolve().parents[2] / 'data/base_patch.bsdiff4')
    parser.add_argument('--cc', default='cc')
    args = parser.parse_args()
    clean = args.rom.read_bytes()
    if hashlib.sha1(clean).hexdigest() != '274b102b6d940f46861a92b4e65f89a51815c12c':
        raise SystemExit('Expected the verified clean USA ROM')
    patched = bsdiff4.patch(clean, args.patch.read_bytes())
    library_dir = str(args.library_dir.resolve())
    env = os.environ.copy()
    env['LD_LIBRARY_PATH'] = library_dir + os.pathsep + env.get('LD_LIBRARY_PATH', '')
    with tempfile.TemporaryDirectory(prefix='kirby-hud-probe-') as temp:
        binary = Path(temp) / 'health-hud-probe'
        subprocess.run([args.cc, '-I', str(args.mgba_prefix / 'include'),
                        str(Path(__file__).with_name('health_hud_probe.c')),
                        '-L', library_dir, '-Wl,-rpath,' + library_dir,
                        '-lmgba', '-o', str(binary)], check=True, env=env)
        subprocess.run([str(binary)], input=patched, check=True, env=env)


if __name__ == '__main__':
    main()
