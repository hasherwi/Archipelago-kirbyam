"""Host saved-check tests; copying buffers is not emulator SRAM acceptance."""
from pathlib import Path
import shutil
import subprocess

import pytest


def test_seed_bound_checks_and_native_door_words(tmp_path: Path) -> None:
    cc = shutil.which("cc")
    if not cc:
        pytest.skip("C compiler unavailable")
    source = r'''
#include <stdint.h>
#include <string.h>
#include "hub_save_logic.h"
#define CHECK(x) do { if (!(x)) return __LINE__; } while (0)
int main(void) {
    uint32_t world[32], disk[3][32] = {{0}}, auth[4] = {1,2,3,4};
    for (unsigned slot=0;slot<3;slot++) {
        memset(world,0,sizeof(world));
        for(unsigned i=0;i<27;i++) world[i]=0x12340000+i;
        for(unsigned bit=0;bit<15;bit++) {
            CHECK(ap_hub_record_check(world+27,auth,bit)==1);
            CHECK(ap_hub_record_check(world+27,auth,bit)==0);
            memcpy(disk[slot],world,sizeof(world));
            memset(world,0,sizeof(world));
            memcpy(world,disk[slot],sizeof(world));
            CHECK(ap_hub_saved_checks(world+27,auth)==((1u<<(bit+1))-1));
            for(unsigned i=0;i<27;i++) CHECK(world[i]==0x12340000+i);
        }
        for(unsigned i=0;i<4;i++) {
            auth[i]^=1;CHECK(ap_hub_saved_checks(world+27,auth)==0);auth[i]^=1;
        }
        world[31]^=0x80000;CHECK(ap_hub_saved_checks(world+27,auth)==0);
        CHECK(ap_hub_record_check(world+27,auth,14)==1);
        CHECK(ap_hub_saved_checks(world+27,auth)==(1u<<14));
        CHECK(ap_hub_record_check(world+27,auth,15)==0);
        memset(world,0,sizeof(world));CHECK(ap_hub_saved_checks(world+27,auth)==0);
    }
    /* Every hub mask and every lever subset survive, including legacy migration.
     * Updating either family never clears the other or touches native door words. */
    for(unsigned hubs=0;hubs<32768;hubs++) for(unsigned levers=0;levers<16;levers++) {
        memset(world,0,sizeof(world));
        for(unsigned i=0;i<27;i++) world[i]=0xABC00000u+i;
        memcpy(world+27,auth,16);
        world[31]=AP_HUB_SAVE_TAG|hubs;
        CHECK(ap_hub_saved_checks(world+27,auth)==hubs);
        CHECK(ap_lever_saved_checks(world+27,auth)==0);
        for(unsigned bit=0;bit<4;bit++) if(levers&(1u<<bit)) {
            CHECK(ap_lever_record_check(world+27,auth,bit)==1);
            CHECK(ap_lever_record_check(world+27,auth,bit)==0);
        }
        CHECK(ap_hub_saved_checks(world+27,auth)==hubs);
        CHECK(ap_lever_saved_checks(world+27,auth)==levers);
        CHECK(ap_lever_record_check(world+27,auth,4)==0);
        ap_hub_record_check(world+27,auth,0);
        CHECK(ap_hub_saved_checks(world+27,auth)==(hubs|1u));
        CHECK(ap_lever_saved_checks(world+27,auth)==levers);
        for(unsigned i=0;i<27;i++) CHECK(world[i]==0xABC00000u+i);
    }
    for(unsigned flags=0;flags<32;flags++) for(unsigned local=0;local<4;local++)
        for(unsigned owner=0;owner<4;owner++)
            CHECK(ap_hub_save_action(flags,local,owner)==
                  ((flags&16)?0:((flags&2)&&local!=owner)?2:1));
    for(unsigned slot=0;slot<65536;slot++) CHECK(ap_hub_save_slot(slot)==(slot<3?slot:0));
    return 0;
}
'''
    cfile, exe = tmp_path / "save.c", tmp_path / "save"
    cfile.write_text(source)
    include = Path(__file__).resolve().parents[1] / "kirby_ap_payload"
    result = subprocess.run([cc, "-std=c99", "-Wall", "-Wextra", "-Werror", "-I", str(include),
                             str(cfile), "-o", str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    result = subprocess.run([str(exe)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
