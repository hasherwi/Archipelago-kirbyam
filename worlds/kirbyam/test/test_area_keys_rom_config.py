"""Immutable per-seed Area Key mode and stale base-patch rejection."""
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from ..rom import (
    AREA_KEYS_CONFIG_OFF, AREA_KEYS_CONFIG_ON, AREA_KEYS_CONFIG_ROM_OFFSET,
    STARTING_RAINBOW_ROUTE_KEY_CONFIG_BIT, KirbyAmPatchExtension, KirbyAmProcedurePatch, write_tokens,
)
from .test_rom_tokens import _DummyPatch, _make_world


@pytest.mark.parametrize("enabled", [False, True, None])
def test_area_keys_token_is_explicit_with_default_on(enabled: bool | None) -> None:
    world = _make_world(0)
    if enabled is not None:
        world.options.area_keys = SimpleNamespace(value=int(enabled))
    patch = _DummyPatch()
    write_tokens(cast(Any, world), cast(Any, patch))
    expected = (AREA_KEYS_CONFIG_OFF if enabled is False
                else AREA_KEYS_CONFIG_ON | STARTING_RAINBOW_ROUTE_KEY_CONFIG_BIT)
    assert [(address, value) for _, address, value in patch.token_writes
            if address == AREA_KEYS_CONFIG_ROM_OFFSET] == [
        (0x15F688, expected.to_bytes(4, "little"))
    ]
    # Adjacent established seed words keep their addresses.
    assert {address for _, address, _ in patch.token_writes} >= {
        0x15F68C, 0x15F690, 0x15F694, 0x15F698, 0x15F69C,
    }


@pytest.mark.parametrize("word", [0, 0xFFFFFFFF, 0x414B0001, AREA_KEYS_CONFIG_OFF])
def test_base_guard_rejects_missing_or_already_modified_config(word: int) -> None:
    rom = bytearray(0x15F6A0)
    rom[AREA_KEYS_CONFIG_ROM_OFFSET:AREA_KEYS_CONFIG_ROM_OFFSET + 4] = word.to_bytes(4, "little")
    with pytest.raises(ValueError, match="Area Keys config marker missing"):
        KirbyAmPatchExtension.validate_area_keys_base(cast(Any, None), bytes(rom))


def test_base_guard_runs_before_tokens_and_accepts_default_marker() -> None:
    rom = bytearray(0x15F6A0)
    rom[AREA_KEYS_CONFIG_ROM_OFFSET:AREA_KEYS_CONFIG_ROM_OFFSET + 4] = AREA_KEYS_CONFIG_ON.to_bytes(4, "little")
    original = bytes(rom)
    assert KirbyAmPatchExtension.validate_area_keys_base(cast(Any, None), original) is original
    steps = [name for name, _ in KirbyAmProcedurePatch.procedure]
    assert steps.index("apply_bsdiff4") < steps.index("validate_area_keys_base") < steps.index("apply_tokens")


@pytest.mark.parametrize("keys", [0, 1])
def test_starting_mirror_config_bit_is_independent(keys) -> None:
    world = _make_world(0)
    world.options.area_keys = SimpleNamespace(value=keys)
    world.options.random_starting_mirror = SimpleNamespace(value=1)
    patch = _DummyPatch()
    write_tokens(cast(Any, world), cast(Any, patch))
    assert [(a, v) for _, a, v in patch.token_writes if a == AREA_KEYS_CONFIG_ROM_OFFSET] == [
        (AREA_KEYS_CONFIG_ROM_OFFSET, (0x414B0107 if keys else 0x414B0102).to_bytes(4, "little"))
    ]


def test_native_config_defaults_on_and_bypasses_only_destination_key(tmp_path: Path) -> None:
    import shutil
    import subprocess
    from .test_native_transport_guards import _function

    cc = shutil.which("cc")
    if cc is None:
        pytest.skip("host compiler unavailable")
    assert cc is not None
    payload = (Path(__file__).resolve().parents[1] / "kirby_ap_payload/ap_payload.c").read_text()
    functions = "\n".join(_function(payload, name) for name in (
        "ap_random_starting_mirror_enabled", "ap_is_starting_mirror",
        "ap_area_keys_enabled", "ap_rainbow_route_gate_enabled", "ap_is_rainbow_return_mirror",
        "ap_is_keyed_inter_area_edge", "ap_transition_allowed", "ap_transition_reason",
    ))
    harness = r'''
#include <stdint.h>
#include <stdio.h>
#define AP_AREA_KEYS_CONFIG_OFF 0x414B0100u
#define AP_AREA_KEYS_CONFIG_ON 0x414B0101u
#define AP_RAINBOW_ROUTE_KEY_CONFIG_BIT 4u
#define AP_RAINBOW_ROUTE_KEY_BIT (1u << 1)
#define AP_MAILBOX_INIT_COOKIE_VALUE 0x4B41504Du
#define AP_STARTING_MIRROR_CONFIG_BIT 2u
#define AP_STARTING_MIRROR_OWNED (1u << 19)
#define KIRBY_NATIVE_AREA_UNKNOWN 255u
static uint32_t gApAreaKeysConfig, AP_AREA_KEY_BITFIELD_RUNTIME, copy_room_owned;
static uint32_t AP_MAILBOX_INIT_COOKIE = AP_MAILBOX_INIT_COOKIE_VALUE;
static uint32_t durable_area_key_bits;
static uint32_t ap_progress_owned(void) { return durable_area_key_bits; }
static uint32_t ap_copy_room_owned(void) { return copy_room_owned & 1u; }
static uint32_t ap_copy_room_access_owned(uint32_t mask) { return copy_room_owned & mask; }
/* Native area metadata is isolated here; all tested policy functions are extracted production bodies. */
static uint8_t ap_native_area_for_room(uint16_t room) {
    if (room == 790 || room == 710) return 1;
    if (room == 801 || room == 101) return 0;
    if (room == 803) return 9;
    return (uint8_t)room;
}
#define CHECK(c) do { if (!(c)) {fprintf(stderr,"line %d: %s\n",__LINE__,#c);return 1;} } while (0)
'''
    harness += functions + r'''
int main(void) {
    uint32_t defaults[]={0x414B0101u,0u,0xFFFFFFFFu,0x414B0000u,0x414B0103u};
    for(unsigned i=0;i<sizeof(defaults)/sizeof(*defaults);i++) {
        gApAreaKeysConfig=defaults[i]; AP_AREA_KEY_BITFIELD_RUNTIME=0;
        CHECK(ap_area_keys_enabled()==1);
        CHECK(ap_is_keyed_inter_area_edge(0,1)==1);
        CHECK(ap_transition_allowed(0,1)==0);
        CHECK(ap_transition_reason(0,1,0)==2);
        AP_AREA_KEY_BITFIELD_RUNTIME=1u<<2;
        CHECK(ap_transition_allowed(0,1)==0); /* Client mirror does not earn Area 2. */
        durable_area_key_bits=1u;
        CHECK(ap_transition_allowed(0,1)==1);
        durable_area_key_bits=0u;
        CHECK(ap_transition_reason(0,1,1)==3);
    }
    gApAreaKeysConfig=AP_AREA_KEYS_CONFIG_OFF;
    for(unsigned keys=0;keys<1024;keys++) {
        AP_AREA_KEY_BITFIELD_RUNTIME=keys;
        for(unsigned source=0;source<11;source++) for(unsigned destination=0;destination<11;destination++) {
            CHECK(ap_area_keys_enabled()==0);
            CHECK(ap_is_keyed_inter_area_edge(source,destination)==0);
            CHECK(ap_transition_allowed(source,destination)==1);
            CHECK(ap_transition_reason(source,destination,1)==6);
        }
    }
    CHECK(ap_transition_allowed(801,970)==0);
    copy_room_owned=1;CHECK(ap_transition_allowed(801,970)==1);
    copy_room_owned=0;
    /* Enabling again never synthesizes ownership from the disabled mode. */
    gApAreaKeysConfig=0x414B0101u; AP_AREA_KEY_BITFIELD_RUNTIME=0;
    CHECK(ap_transition_allowed(0,1)==0);
    CHECK(ap_transition_allowed(1,0)==1);
    CHECK(ap_transition_allowed(1,1)==1);
    CHECK(ap_transition_allowed(801,101)==1);
    for(unsigned keys=0;keys<=1;keys++) {
        gApAreaKeysConfig=0x414B0102u|keys;
        CHECK(ap_area_keys_enabled()==keys);
        CHECK(ap_transition_allowed(801,101)==0);
        CHECK(ap_transition_allowed(101,801)==1);
        copy_room_owned=AP_STARTING_MIRROR_OWNED;
        CHECK(ap_transition_allowed(801,101)==1);
        CHECK(ap_transition_allowed(801,970)==0);
        copy_room_owned=0;
    }
    /* Moonlight's native return mirror can close, unlike its boss exit. */
    gApAreaKeysConfig=0x414B0105u; AP_AREA_KEY_BITFIELD_RUNTIME=0;
    CHECK(ap_transition_allowed(790,801)==0);
    CHECK(ap_transition_reason(790,801,0)==2);
    CHECK(ap_transition_allowed(710,801)==1);
    CHECK(ap_transition_allowed(803,801)==1);
    CHECK(ap_transition_allowed(801,101)==1);
    AP_MAILBOX_INIT_COOKIE=0;
    CHECK(ap_transition_allowed(790,801)==1); /* ROM startup grant before mailbox initializes */
    AP_MAILBOX_INIT_COOKIE=AP_MAILBOX_INIT_COOKIE_VALUE;
    AP_AREA_KEY_BITFIELD_RUNTIME=1u<<1;
    CHECK(ap_transition_allowed(790,801)==1);
    CHECK(ap_transition_reason(790,801,1)==3);
    gApAreaKeysConfig=0x414B0101u; AP_AREA_KEY_BITFIELD_RUNTIME=0;
    CHECK(ap_transition_allowed(790,801)==1); /* pre-feature configuration */
    return 0;
}
'''
    source, executable = tmp_path / "area_mode.c", tmp_path / "area_mode"
    source.write_text(harness)
    result = subprocess.run([cc, "-std=c99", "-Wall", "-Wextra", "-Werror", str(source), "-o", str(executable)],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    result = subprocess.run([str(executable)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
