"""Private native mode-menu acceptance. Never commit generated ROM/save artifacts."""
import argparse
from pathlib import Path
import struct
import subprocess

import bsdiff4

parser = argparse.ArgumentParser()
parser.add_argument('--rom', type=Path, required=True)
parser.add_argument('--observer', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=True)
world = Path(__file__).resolve().parents[2]
rom = bytearray(bsdiff4.patch(args.rom.read_bytes(), (world/'data/base_patch.bsdiff4').read_bytes()))
rom[0xF00000:0xF00010] = bytes(range(1, 17))
rom_path = out/'private-menu.gba'
rom_path.write_bytes(rom)
title = '0 180\n8 1\n0 120\n8 1\n0 240\n'
adventure = '64 1\n0 1\n64 1\n0 1\n1 1\n0 120\n1 1\n0 240\n'
boss = '64 1\n0 1\n1 1\n0 180\n128 1\n0 1\n128 1\n0 1\n128 1\n0 1\n1 1\n0 240\n1 1\n0 400\n8 1\n0 500\n'


def run(name, save, inputs):
    source = out/(name+'.input.sav')
    source.write_bytes(save)
    state = out/(name+'.ss1')
    result = subprocess.run([str(args.observer.resolve()), str(rom_path), 'cold:'+str(source),
                             str(state), str(out/(name+'.ppm'))], input=inputs,
                            text=True, capture_output=True, timeout=60)
    (out/(name+'.log')).write_text(result.stdout+result.stderr)
    assert result.returncode == 0, result.stderr
    assert 'save_id=1 ' not in result.stdout and 'save_id=2 ' not in result.stdout
    return result.stdout, Path(str(state)+'.sav').read_bytes()


log, fresh = run('fresh-adventure', bytes([255])*32768, title+adventure)
assert 'context=1 serial=1 slot=0' in log and 'room=803 ' in log
# Synthetic, checksum-valid 100% native progress; no emulator memory writes.
complete = bytearray(fresh)
for copy in range(2):
    start = 24+copy*4884
    data = bytearray(complete[start+8:start+4884])
    for i in range(1, 16):
        struct.pack_into('<I', data, 32+i*4, 1)
    for i in range(287):
        struct.pack_into('<H', data, 160+i*2, 0x8000)
    data[734:750] = ((1 << 84)-1).to_bytes(16, 'little')
    data[750] = 255
    struct.pack_into('<H', data, 778, 9999)
    total = sum(struct.unpack('<2438H', data)) & 65535
    complete[start:start+4884] = struct.pack('<4H', total, total ^ 65535, (-total) & 65535, 0)+data
log, saved = run('completed-mode-menu', complete, title)
assert 'completion=100' in log and 'context=1 ' not in log and saved == complete
log, saved = run('boss-endurance', complete, title+boss)
assert 'mode=00000004' in log and 'room=950 ' in log and 'context=1 ' not in log
log, saved = run('mode-back-title-reentry', complete, title+'2 1\n0 180\n8 1\n0 240\n')
assert 'completion=100' in log and 'context=1 ' not in log and saved == complete
log, saved = run('completed-adventure', complete, title+adventure)
assert 'context=1 serial=1 slot=0' in log and 'room=801 ' in log
log, saved = run('boss-reset-adventure', complete, title+boss+'15 60\n'+title+adventure)
assert 'mode=00000004' in log and 'context=1 serial=1 slot=0' in log and 'room=801 ' in log
# Authenticated File 1 with owned paints, selected through native Collection UI.
owned = bytearray(complete)
for copy in range(2):
    start = 24+copy*4884
    data = bytearray(owned[start+8:start+4884])
    struct.pack_into('<I', data, 754, 0x3fff)
    struct.pack_into('<H', data, 768, 0)
    total = sum(struct.unpack('<2438H', data)) & 65535
    owned[start:start+4884] = struct.pack('<4H', total, total ^ 65535, (-total) & 65535, 0)+data
collection_paint = '1 1\n0 300\n16 1\n0 10\n16 1\n0 10\n1 1\n0 180\n'
log, painted = run('collection-paint', owned, title+collection_paint)
assert 'context=1 ' not in log and 'selected_color=1 ' in log
for copy in range(2):
    start = 24+copy*4884
    data = painted[start+8:start+4884]
    assert struct.unpack_from('<H', data, 768)[0] == 0xc61e
    total = sum(struct.unpack('<2438H', data)) & 65535
    assert painted[start:start+8] == struct.pack('<4H', total, total ^ 65535, (-total) & 65535, 0)
log, saved = run('collection-paint-adventure', owned,
                 title+collection_paint+'2 1\n0 240\n'+adventure)
assert 'context=1 serial=1 slot=0' in log and 'selected_color=1 live_color=1' in log
log, saved = run('collection-paint-cold-reload', painted, title+adventure)
assert 'context=1 serial=1 slot=0' in log and 'selected_color=1 live_color=1' in log
print('PASS Collection owned-paint selection with epoch zero, both native checksum copies, Adventure color and cold reload')
print('PASS fresh/continued Adventure, completed-file Boss Endurance room 950, inactive menu/Boss AP context, mode Back/title/re-entry, Boss reset/Adventure, File 1 isolation')
