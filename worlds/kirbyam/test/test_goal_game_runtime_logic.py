"""Host lifecycle checks, explicitly separate from emulator acceptance."""
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


def test_exact_origin_and_run_lifecycle(tmp_path):
    cc = shutil.which('cc')
    if not cc:
        pytest.skip('C compiler unavailable')
    source = r'''
#include "goal_game_runtime_logic.h"
#define CHECK(x) do { if (!(x)) return __LINE__; } while (0)
int main(void) {
    struct ApGoalRun run = {0};
    uint32_t seen = 0;
    for (unsigned i=0; i<sizeof(ap_goal_doors)/sizeof(ap_goal_doors[0]); i++) {
        const struct ApGoalDoor *d = &ap_goal_doors[i];
        seen |= 1u << d->bit;
        CHECK(ap_goal_origin(d->pointer,d->source,d->destination)==d->bit);
        CHECK(ap_goal_origin(d->pointer+1,d->source,d->destination)==16);
        CHECK(ap_goal_origin(d->pointer,d->source+1,d->destination)==16);
        CHECK(ap_goal_origin(d->pointer,d->source,d->destination+1)==16);
        ap_goal_enter(&run,42,d->pointer,d->source,d->destination);
        CHECK(ap_goal_complete(&run,42,d->destination,123,1,1)==16);
        ap_goal_start(&run,42,d->destination,123,1);
        CHECK(ap_goal_complete(&run,42,d->destination,123,1,0)==16);
        CHECK(ap_goal_complete(&run,42,d->destination,124,1,1)==16);
        CHECK(ap_goal_complete(&run,42,d->destination,123,0,1)==16);
        CHECK(ap_goal_complete(&run,42,d->destination,123,1,1)==d->bit);
        CHECK(ap_goal_complete(&run,42,d->destination,123,1,1)==16);
        for(unsigned phase=0;phase<2;phase++) {
            for(unsigned abort=0;abort<4;abort++) {
                ap_goal_enter(&run,42,d->pointer,d->source,d->destination);
                if(phase) ap_goal_start(&run,42,d->destination,123,1);
                if(abort==0) ap_goal_validate(&run,43,d->destination,1);
                if(abort==1) ap_goal_validate(&run,0,d->destination,1);
                if(abort==2) ap_goal_validate(&run,42,801,1);
                if(abort==3) ap_goal_validate(&run,42,d->destination,0);
                CHECK(ap_goal_complete(&run,42,d->destination,123,1,1)==16);
            }
        }
        ap_goal_enter(&run,42,d->pointer,d->source,d->destination);
        ap_goal_start(&run,42,d->destination,123,0);
        CHECK(run.phase==0);
        ap_goal_enter(&run,0,d->pointer,d->source,d->destination);
        CHECK(run.phase==0);
        ap_goal_enter(&run,42,d->pointer,d->source,d->destination);
        ap_goal_enter(&run,42,0,d->destination,801);
        CHECK(run.phase==0);
    }
    CHECK(seen==0xffff);
    return 0;
}
'''
    cfile, exe = tmp_path/'goal.c', tmp_path/'goal'
    cfile.write_text(source)
    include = Path(__file__).resolve().parents[1]/'kirby_ap_payload'
    subprocess.run([cc, '-std=c99', '-Wall', '-Wextra', '-Werror', '-I', str(include),
                    str(cfile), '-o', str(exe)], check=True, capture_output=True)
    result = subprocess.run([str(exe)], capture_output=True)
    assert result.returncode == 0, result.returncode


def test_generated_doors_current():
    script = Path(__file__).resolve().parents[1]/'tools/generate_goal_game_doors.py'
    subprocess.run([sys.executable, str(script), '--check'], check=True, capture_output=True)
