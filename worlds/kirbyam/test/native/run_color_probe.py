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
    parser.add_argument('--elf', type=Path, required=True, help='Matching rebuilt payload.elf')
    args = parser.parse_args()
    clean = args.rom.read_bytes()
    if hashlib.sha1(clean).hexdigest() != '274b102b6d940f46861a92b4e65f89a51815c12c':
        raise SystemExit('Expected the verified clean USA ROM')
    patched = bsdiff4.patch(clean, args.patch.read_bytes())
    symbols = {}
    for line in subprocess.check_output(['arm-none-eabi-nm', str(args.elf)], text=True).splitlines():
        fields = line.split()
        if len(fields) == 3:
            symbols[fields[2]] = '0x' + fields[0]
    targets = [symbols[name] for name in ('ap_poll_mailbox_c',
               'ap_on_treasure_paint_selection', 'ap_on_start_single_player_game')]
    library_dir = str(args.library_dir.resolve())
    env = os.environ.copy()
    env['LD_LIBRARY_PATH'] = library_dir + os.pathsep + env.get('LD_LIBRARY_PATH', '')
    with tempfile.TemporaryDirectory(prefix='kirby-color-probe-') as temp:
        binary = Path(temp) / 'color-runtime-probe'
        subprocess.run([args.cc, '-I', str(args.mgba_prefix / 'include'),
                        str(Path(__file__).with_name('color_runtime_probe.c')),
                        '-L', library_dir, '-Wl,-rpath,' + library_dir,
                        '-lmgba', '-o', str(binary)], check=True, env=env)
        subprocess.run([str(binary), *targets], input=patched, check=True, env=env)


if __name__ == '__main__':
    main()
