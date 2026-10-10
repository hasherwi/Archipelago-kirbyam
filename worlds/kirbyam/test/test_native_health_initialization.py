"""Native reload capacity and per-seed ROM bounds, retaining four-item v1."""
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace
import pytest
from .test_health_hud_hooks import patch
from .test_runtime_regression_hooks import _function
from .test_rom_tokens import _DummyPatch, _make_world
from .. import KirbyAmWorld
from ..health import resolve_health_range
from ..rom import write_tokens, HEALTH_INITIAL_ROM_OFFSET

RANGES = [(lo, hi) for lo in range(1, 11) for hi in range(lo, min(lo + 4, 10) + 1)]


def test_native_initializer_patch_fail_closed():
    rom = bytearray(0x40000)
    rom[0x3EB0E:0x3EB14] = patch.thumb_bl_bytes(0x0803EB0E, 0x08019F0C) + b'\x06\x30'
    before = bytes(rom)
    writes = patch.build_initial_health_writes(rom, 0x0815E100)
    assert bytes(rom) == before
    assert writes == {0x3EB0E: patch.thumb_bl_bytes(0x0803EB0E, 0x0815E100), 0x3EB12: b'\xc0\x46'}
    for offset in (0x3EB0E, 0x3EB12):
        bad = bytearray(before); bad[offset] ^= 1
        with pytest.raises(SystemExit, match='native initial health'):
            patch.build_initial_health_writes(bad, 0x0815E100)
    for offset, data in writes.items():
        rom[offset:offset + len(data)] = data
    with pytest.raises(SystemExit, match='native initial health'):
        patch.build_initial_health_writes(rom, 0x0815E100)


@pytest.mark.parametrize('minimum,maximum', RANGES)
@pytest.mark.parametrize('one_hit', [0, 1, 2])
def test_seed_health_and_old_config_offsets(minimum, maximum, one_hit):
    world = _make_world(0)
    world.options.minimum_health = SimpleNamespace(value=minimum)
    world.options.maximum_health = SimpleNamespace(value=maximum)
    world._one_hit_mode_value = lambda: one_hit
    world._health_range = lambda: KirbyAmWorld._health_range(world)
    out = _DummyPatch(); write_tokens(world, out)
    values = {offset: int.from_bytes(value, 'little') for _, offset, value in out.token_writes}
    health = resolve_health_range(minimum, maximum, one_hit)
    assert values[HEALTH_INITIAL_ROM_OFFSET] == 0xA9010000 | health.maximum << 8 | health.minimum
    assert {0x15F690, 0x15F694, 0x15F698, 0x15F69C} <= values.keys()


def test_actual_c_all_u16_counts_and_grant_policy(tmp_path):
    cc = shutil.which('cc') or shutil.which('gcc')
    if not cc:
        pytest.skip('C compiler unavailable')
    payload = (Path(__file__).resolve().parents[1] / 'kirby_ap_payload/ap_payload.c').read_text()
    capacity = _function(payload, 'ap_initial_health_capacity')
    sync = _function(payload, 'ap_sync_active_kirby_health_from_vitality').replace('uint32_t kirby_addr', 'uintptr_t kirby_addr')
    source = '''#include <stdint.h>
#include <stdio.h>
static uint32_t gApHealthConfigInitial;
static uint16_t KIRBY_VITALITY_COUNTER;
static uint8_t KIRBY_CURRENT_PLAYER;
static uint8_t kirbies[4][0x1A8];
#define KIRBY_STRUCTS_ADDR ((uintptr_t)kirbies)
#define KIRBY_STRUCT_STRIDE 0x1A8u
#define KIRBY_STRUCT_HP_OFFSET 0x100u
#define KIRBY_STRUCT_MAX_HP_OFFSET 0x101u
#define CHECK(x) do {if(!(x)){fprintf(stderr,"line%d\\n",__LINE__);return 1;}} while(0)
''' + capacity + '\n' + sync + '''
int main(void) {
 for(unsigned lo=1;lo<=10;lo++) for(unsigned hi=lo;hi<=10 && hi-lo<=4;hi++) {
  gApHealthConfigInitial=0xA9010000u | (hi<<8) | lo;
  for(unsigned count=0;count<=65535;count++) {
   KIRBY_VITALITY_COUNTER=count;
   CHECK(ap_initial_health_capacity()==lo+(count>hi-lo?hi-lo:count));
  }
  for(unsigned player=0;player<4;player++) for(unsigned count=0;count<=4;count++) {
   KIRBY_CURRENT_PLAYER=player;KIRBY_VITALITY_COUNTER=count;
   for(int hp=-128;hp<=10;hp++) {
    kirbies[player][0x100]=(uint8_t)hp;kirbies[player][0x101]=99;
    ap_sync_active_kirby_health_from_vitality();
    unsigned want=lo+(count>hi-lo?hi-lo:count);
    CHECK(kirbies[player][0x101]==want);
    CHECK((int8_t)kirbies[player][0x100]==(hp>0?(int)want:hp));
   }
  }
 }
 unsigned invalid[]={0,0xffffffff,0xA9020703,0xA9010700,0xA9010307,0xA9010b06,0xA9010a01};
 for(unsigned i=0;i<sizeof invalid/sizeof *invalid;i++) {
  gApHealthConfigInitial=invalid[i];KIRBY_VITALITY_COUNTER=1;
  CHECK(ap_initial_health_capacity()==7);
 }
 gApHealthConfigInitial=0xA9010703;KIRBY_VITALITY_COUNTER=1;
 CHECK(ap_initial_health_capacity()==4);
 return 0;
}
'''
    c = tmp_path / 'health.c'; exe = tmp_path / 'health'
    c.write_text(source)
    built = subprocess.run([cc, '-std=c99', '-O2', str(c), '-o', str(exe)], capture_output=True, text=True)
    assert built.returncode == 0, built.stderr
    result = subprocess.run([str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
