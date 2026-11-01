"""Preserve compiled runtime mapping independently of catalog bit identities."""
import copy
import json
from pathlib import Path
import shutil
import subprocess

import pytest

from ..tools import generate_hub_switch_contract as generator

WORLD = Path(__file__).resolve().parents[1]
PAYLOAD = WORLD / 'kirby_ap_payload'


def inputs():
    return (json.loads(generator.CONTRACT_PATH.read_text()), json.loads(generator.LOCATIONS_PATH.read_text()))


def test_generated_mapping_is_current_and_preserves_compiled_baseline():
    contract, locations = inputs()
    entries = generator._validate_contract(contract, locations)
    assert generator._build_c_include_output(entries) == generator.C_INC_OUT_PATH.read_text()
    assert generator._build_c_table_output(entries) == generator.C_TABLE_OUT_PATH.read_text()
    assert generator._build_python_output(entries) == generator.PY_OUT_PATH.read_text()
    assert generator.C_INC_OUT_PATH.read_bytes() == (WORLD / 'test/data/hub_switch_compiled_baseline.inc').read_bytes()
    assert [(e['ap_bit_index'], e['runtime_ap_bit_index']) for e in entries[:2]] == [(1, 11), (11, 1)]


@pytest.mark.parametrize('mutation', ['missing', 'range', 'duplicate', 'reason'])
def test_invalid_mapping_is_rejected(mutation):
    contract, locations = inputs()
    contract = copy.deepcopy(contract)
    if mutation == 'missing':
        contract['entries'].pop()
    elif mutation == 'range':
        contract['entries'][0]['world_props_unlock_index'] = 256
    elif mutation == 'duplicate':
        contract['entries'][0]['runtime_ap_bit_index'] = 1
    else:
        contract['entries'][0].pop('runtime_bit_reason')
    with pytest.raises(ValueError):
        generator._validate_contract(contract, locations)


def test_production_lookup_matches_original_for_all_uint16_and_pointer_cases(tmp_path):
    cc = shutil.which('cc') or shutil.which('gcc') or shutil.which('clang')
    if not cc:
        pytest.skip('native C compiler unavailable')
    source = (PAYLOAD / 'ap_payload.c').read_text()
    start = source.index('static uint8_t ap_try_map_worldmap_door_to_hub_switch_bit(')
    end = source.index('\nstatic volatile uint32_t *ap_get_hub_unlock_entry', start)
    production = source[start:end]
    baseline = (WORLD / 'test/data/hub_switch_compiled_baseline.inc').read_text()
    harness = '#include <stdint.h>\n#include <assert.h>\n#include "generated_hub_switch_tables.inc"\n' + production
    harness += '''
static uint8_t original_lookup(uint16_t door_index, uint32_t *out_bit, uint8_t *out_world_props_unlock_index) {
 if (!out_bit || !out_world_props_unlock_index) return 0;
 switch (door_index) {
''' + baseline + '''
 }
 return 0;
}
int main(void) {
 for (unsigned d=0; d<65536; d++) for(unsigned mask=0; mask<4; mask++) {
  uint32_t a=0xdeadbeef,b=a; uint8_t c=0x98,e=c;
  uint8_t r=original_lookup(d,mask&1?&a:0,mask&2?&c:0);
  uint8_t t=ap_try_map_worldmap_door_to_hub_switch_bit(d,mask&1?&b:0,mask&2?&e:0);
  assert(r==t && a==b && c==e);
 }
 for (unsigned d=0; d<65536; d++) for(unsigned offset=0; offset<4; offset++) {
  uint32_t a=0xdeadbeef,b=a;
  uint8_t r=original_lookup(d,&a,((uint8_t*)&a)+offset);
  uint8_t t=ap_try_map_worldmap_door_to_hub_switch_bit(d,&b,((uint8_t*)&b)+offset);
  assert(r==t && a==b);
 }
 return 0;
}
'''
    cfile = tmp_path / 'check.c'
    binary = tmp_path / 'check'
    cfile.write_text(harness)
    subprocess.run(
        [cc, '-std=c99', '-O2', '-Wall', '-Wextra', '-I', str(PAYLOAD), str(cfile), '-o', str(binary)], check=True
    )
    subprocess.run([str(binary)], check=True, timeout=15)
