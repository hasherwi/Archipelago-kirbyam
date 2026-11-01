"""Execute production transport guards with native effects stubbed, not emulator proof."""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


def _function(source: str, name: str) -> str:
    start = re.search(r"uint(?:8|32)_t " + name + r"\(", source)
    assert start is not None
    opening = source.index("{", start.start())
    depth = 1
    end = opening + 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[start.start():end]


def test_production_cannon_and_warp_guards_before_native_mutation(tmp_path: Path) -> None:
    if not sys.platform.startswith("linux"):
        pytest.skip("fixed private RAM mappings require Linux")
    cc = shutil.which("cc")
    if cc is None:
        pytest.skip("host C compiler unavailable")
    assert cc is not None
    payload = (Path(__file__).resolve().parents[1] / "kirby_ap_payload" / "ap_payload.c").read_text()
    names = (
        "KIRBY_STRUCT_ROOM_OFFSET", "KIRBY_EWRAM_START", "KIRBY_EWRAM_END",
        "KIRBY_IWRAM_START", "KIRBY_IWRAM_END", "KIRBY_WARP_STAR_KIRBY_PTR_OFFSET",
        "KIRBY_WARP_STAR_DESTINATION_ROOM_OFFSET",
    )
    constants = []
    for name in names:
        definition = re.search(r"^#define " + name + r" .+$", payload, re.MULTILINE)
        assert definition is not None
        constants.append(definition.group())
    preamble = r'''
#define _GNU_SOURCE
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/mman.h>
#define CHECK(c) do { if (!(c)) { fprintf(stderr,"line %d: %s\n",__LINE__,#c); return 1; } } while (0)
static unsigned permitted, calls, predicates, logs;
static uint16_t seen_source, seen_destination;
static uint8_t seen_method, seen_allowed;
static void *native_argument;
static uint32_t native_human_only;
static uint32_t ap_transition_allowed(uint16_t source, uint16_t destination) {
    predicates++; seen_source=source; seen_destination=destination; return permitted;
}
static uint8_t ap_transition_reason(uint16_t source, uint16_t destination, uint8_t allowed) {
    (void)source; (void)destination; return allowed ? 3 : 2;
}
static void ap_log_transition_attempt(uint16_t source, uint16_t destination,
                                     uint8_t method, uint8_t allowed, uint8_t reason) {
    (void)source; (void)destination; (void)reason;
    logs++; seen_method=method; seen_allowed=allowed;
}
static uint8_t cannon_native(void *kirby) {
    calls++; native_argument=kirby; ((uint8_t*)kirby)[0x106]=0xA5; return 7;
}
static uint32_t warp_native(void *star, uint32_t human_only) {
    calls++; native_argument=star; native_human_only=human_only;
    ((uint8_t*)star)[0x100]=0xA5; return 0x12345678;
}
#define KIRBY_CANNON_BOARD_FN cannon_native
#define KIRBY_WARP_STAR_TRANSITION_FN warp_native
static void reset_observers(void) { calls=predicates=logs=0; native_argument=0; }
'''
    body = r'''
int main(void) {
    CHECK(mmap((void*)KIRBY_EWRAM_START,0x40000,PROT_READ|PROT_WRITE,
               MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)KIRBY_EWRAM_START);
    CHECK(mmap((void*)KIRBY_IWRAM_START,0x8000,PROT_READ|PROT_WRITE,
               MAP_PRIVATE|MAP_ANONYMOUS|MAP_FIXED_NOREPLACE,-1,0)==(void*)KIRBY_IWRAM_START);
    uint8_t *kirby=(void*)0x02001000;
    uint8_t *star=(void*)0x03003000;
    uint8_t original[0x200], object_original[0x200];
    uintptr_t cannons[]={0x03001000,0x02002000};
    for (unsigned i=0;i<2;i++) {
        uint8_t *cannon=(void*)cannons[i];
        memset(kirby,0x39,0x200); memset(cannon,0x59,0x200);
        *(uint32_t*)(kirby+0x6C)=(uint32_t)cannons[i];
        *(uint16_t*)(kirby+KIRBY_STRUCT_ROOM_OFFSET)=142;
        *(uint16_t*)(cannon+0xBA)=195;
        memcpy(original,kirby,sizeof(original)); memcpy(object_original,cannon,sizeof(object_original));
        reset_observers(); permitted=0;
        CHECK(ap_on_cannon_board_transition(kirby)==0);
        CHECK(calls==0 && predicates==1 && logs==1);
        CHECK(seen_source==142 && seen_destination==195 && seen_method==2 && seen_allowed==0);
        CHECK(memcmp(original,kirby,sizeof(original))==0);
        CHECK(memcmp(object_original,cannon,sizeof(object_original))==0);
        permitted=1;
        CHECK(ap_on_cannon_board_transition(kirby)==7);
        CHECK(calls==1 && native_argument==kirby && kirby[0x106]==0xA5);
        CHECK(predicates==2 && logs==2 && seen_allowed==1);
    }
    /* Bad/out-of-range object pointers are delegated without dereferencing. */
    uintptr_t invalid[]={0,0x01000000,KIRBY_EWRAM_END-0xBB,KIRBY_IWRAM_END-0xBB,0xFFFFFFF0};
    for (unsigned i=0;i<sizeof(invalid)/sizeof(*invalid);i++) {
        *(uint32_t*)(kirby+0x6C)=(uint32_t)invalid[i]; reset_observers(); permitted=0;
        CHECK(ap_on_cannon_board_transition(kirby)==7);
        CHECK(calls==1 && predicates==0 && logs==0 && native_argument==kirby);
    }
    /* Both RAM banks are valid Kirby pointers in the shared Warp Star helper. */
    uintptr_t kirbys[]={0x02001000,0x03001000};
    for (unsigned i=0;i<2;i++) {
        kirby=(void*)kirbys[i]; memset(kirby,0x49,0x200); memset(star,0x69,0x200);
        *(uint32_t*)(star+8)=0x40000;
        *(uint32_t*)(star+KIRBY_WARP_STAR_KIRBY_PTR_OFFSET)=(uint32_t)kirbys[i];
        *(uint16_t*)(star+KIRBY_WARP_STAR_DESTINATION_ROOM_OFFSET)=195;
        *(uint16_t*)(kirby+KIRBY_STRUCT_ROOM_OFFSET)=142;
        memcpy(original,kirby,sizeof(original)); memcpy(object_original,star,sizeof(object_original));
        reset_observers(); permitted=0;
        CHECK(ap_on_warp_star_transition(star,1)==0);
        CHECK(calls==0 && predicates==1 && logs==1);
        CHECK(seen_source==142 && seen_destination==195 && seen_method==1 && seen_allowed==0);
        CHECK(memcmp(original,kirby,sizeof(original))==0);
        CHECK(memcmp(object_original,star,sizeof(object_original))==0);
        permitted=1;
        CHECK(ap_on_warp_star_transition(star,0)==0x12345678);
        CHECK(calls==1 && native_argument==star && native_human_only==0 && star[0x100]==0xA5);
        CHECK(predicates==2 && logs==2 && seen_allowed==1);
        reset_observers(); permitted=0;
        *(uint32_t*)(star+8)=0; /* no contacted passenger; native owns this path */
        CHECK(ap_on_warp_star_transition(star,1)==0x12345678);
        CHECK(calls==1 && predicates==0 && logs==0 && native_human_only==1);
        reset_observers(); *(uint32_t*)(star+8)=0x40000;
        *(uint32_t*)(star+KIRBY_WARP_STAR_KIRBY_PTR_OFFSET)=KIRBY_IWRAM_END;
        CHECK(ap_on_warp_star_transition(star,1)==0x12345678);
        CHECK(calls==1 && predicates==0 && logs==0 && native_human_only==1);
    }
    *(uint32_t*)(star+8)=0x40000;
    *(uint32_t*)(star+KIRBY_WARP_STAR_KIRBY_PTR_OFFSET)=0xFFFFFFF0;
    reset_observers();
    CHECK(ap_on_warp_star_transition(star,1)==0x12345678);
    CHECK(calls==1 && predicates==0 && logs==0);
    return 0;
}
'''
    source = tmp_path / "transport_guards.c"
    source.write_text("\n".join(constants) + preamble + "\n" +
                      _function(payload, "ap_on_cannon_board_transition") + "\n" +
                      _function(payload, "ap_on_warp_star_transition") + "\n" + body)
    executable = tmp_path / "transport_guards"
    compiled = subprocess.run(
        [cc, "-std=c99", "-Wall", "-Wextra", "-Werror", "-Wno-pointer-to-int-cast",
         "-Wno-int-to-pointer-cast", str(source), "-o", str(executable)],
        capture_output=True, text=True,
    )
    assert compiled.returncode == 0, compiled.stdout + compiled.stderr
    result = subprocess.run([str(executable)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
