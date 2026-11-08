"""Cross-check generated source exclusions and native caller/bitmap boundaries."""
import itertools
import os
import random
import shutil
import struct
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from ..ability_randomization import build_enemy_copy_ability_policy
from ..enemy_ability_data import ABILITY_SOURCES
from .. import enemy_ability_runtime_patch as runtime_patch


@pytest.mark.parametrize("mode", [0, 1, 2])
@pytest.mark.parametrize("bosses,minibosses,minny,passive", tuple(itertools.product([False, True], repeat=4)))
def test_source_bitmap_matches_option_exclusions(mode, bosses, minibosses, minny, passive):
    policy = build_enemy_copy_ability_policy(
        random.Random(908), mode, bosses, minibosses,
        include_minny=minny, include_passive_enemies=passive,
    )
    encoded = runtime_patch.build_enemy_source_runtime_config(policy)
    assert len(encoded) == 36
    magic, *words = struct.unpack("<9I", encoded)
    assert magic == 0x41534501
    actual = {i for i in range(256) if words[i // 32] & (1 << (i % 32))}
    addresses = set()
    for source in ABILITY_SOURCES:
        enabled = mode != 0
        enabled &= source.kind != "enemy" or source.can_be_swallowed
        enabled &= source.default_ability_id != 0 or passive
        enabled &= source.key != "MINNY"
        enabled &= source.kind != "miniboss" or minibosses
        enabled &= source.kind != "boss_spawned" or bosses
        if enabled:
            addresses.update(source.addresses)
    assert actual == {(address - 0x35164E) // 24 for address in addresses}
    assert set(runtime_patch.build_enemy_copy_runtime_patch_writes(policy)) == addresses


@pytest.mark.parametrize("address", [0x35164D, 0x35164F, 0x35164E - 24, 0x35164E + 256 * 24])
def test_source_bitmap_rejects_unverified_addresses(monkeypatch, address):
    source = replace(ABILITY_SOURCES[0], addresses=(address,))
    monkeypatch.setattr(runtime_patch, "ABILITY_SOURCES", (source,))
    policy = build_enemy_copy_ability_policy(
        random.Random(908), 2, True, True, include_minny=True, include_passive_enemies=True,
    )
    with pytest.raises(ValueError, match="Unverified enemy source table address"):
        runtime_patch.build_enemy_source_runtime_config(policy)


def test_native_source_bitmap_boundaries_and_legacy_callers(tmp_path):
    compiler = shutil.which("cc") or shutil.which("clang") or shutil.which("gcc")
    if compiler is None:
        pytest.skip("no host C compiler available")
    source = tmp_path / "policy.c"
    executable = tmp_path / ("policy.exe" if os.name == "nt" else "policy")
    source.write_text(r'''
#include "enemy_runtime_logic.h"
#define CHECK(c) do { if (!(c)) return __LINE__; } while (0)
int main(void) {
    uint32_t config[9] = {AP_ENEMY_SOURCE_CONFIG_MAGIC};
    uint32_t type, pointer, i;
    const uint32_t readable[] = {0x02000000u, 0x0203FF7Cu, 0x03000000u, 0x03007F7Cu};
    const uint32_t invalid[] = {0u, 0x01FFFFFCu, 0x02000001u, 0x0203FF80u,
        0x03007F80u, 0x08000000u, 0xFFFFFFFFu};
    for (i = 0; i < 4; i++) {
        pointer = readable[i];
        for (type = 0; type < 256; type++) {
            CHECK(!ap_enemy_source_policy_allows(config, AP_ENEMY_SWALLOW_CALLSITE, pointer, type));
            config[1 + type / 32] = 1u << (type % 32);
            CHECK(ap_enemy_source_policy_allows(config, AP_ENEMY_SWALLOW_CALLSITE, pointer, type));
            CHECK(!ap_enemy_source_policy_allows(config, AP_ENEMY_SWALLOW_CALLSITE, pointer, type ^ 1u));
            config[1 + type / 32] = 0;
        }
        CHECK(!ap_enemy_source_policy_allows(config, AP_ENEMY_SWALLOW_CALLSITE, pointer, 256));
        CHECK(!ap_enemy_source_policy_allows(config, AP_ENEMY_SWALLOW_CALLSITE, pointer, 0xFFFFFFFFu));
    }
    for (i = 0; i < sizeof(invalid) / sizeof(invalid[0]); i++)
        CHECK(ap_enemy_source_policy_allows(config, AP_ENEMY_SWALLOW_CALLSITE, invalid[i], 0));
    /* Stars and special callers do not interpret incidental r5 as Object2. */
    CHECK(ap_enemy_source_policy_allows(config, 0x0809C69Cu, 0x02001000u, 0x27));
    CHECK(ap_enemy_source_policy_allows(config, 0x0809C674u, 0x02001000u, 0));
    CHECK(ap_enemy_source_policy_allows(config, 0u, 0x02001000u, 0));
    config[0] = AP_ENEMY_SOURCE_CONFIG_LEGACY;
    CHECK(ap_enemy_source_policy_allows(config, AP_ENEMY_SWALLOW_CALLSITE, 0x02001000u, 0));
    config[0] = 0xFFFFFFFFu;
    CHECK(ap_enemy_source_policy_allows(config, AP_ENEMY_SWALLOW_CALLSITE, 0x02001000u, 0));
    CHECK(!ap_enemy_should_reroll(2, 0, 0x27));
    CHECK(ap_enemy_should_reroll(2, 1, 0x27));
    CHECK(!ap_enemy_should_reroll(0, 1, 0));
    CHECK(!ap_enemy_should_reroll(1, 1, 0));
    return 0;
}
''', encoding="utf-8")
    payload = Path(__file__).resolve().parents[1] / "kirby_ap_payload"
    compiled = subprocess.run(
        [compiler, "-std=c99", "-Wall", "-Wextra", "-Werror", "-I", str(payload),
         str(source), "-o", str(executable)], capture_output=True, text=True,
    )
    assert compiled.returncode == 0, compiled.stdout + compiled.stderr
    executed = subprocess.run([str(executable)], capture_output=True, text=True)
    assert executed.returncode == 0, executed.stdout + executed.stderr


@pytest.mark.parametrize("flags", [None, (False, False, False, False), (True, True, True, True),
                                   (True, False, True, False)])
def test_rom_tokens_embed_exact_source_policy(flags):
    from worlds.Files import APTokenTypes
    from ..rom import write_tokens
    from .test_rom_tokens import _DummyPatch, _make_world

    mode = 0 if flags is None else 2
    world = _make_world(mode)
    policy = None
    if flags is not None:
        bosses, minibosses, minny, passive = flags
        policy = build_enemy_copy_ability_policy(
            random.Random(908), mode, bosses, minibosses,
            include_minny=minny, include_passive_enemies=passive,
        )
        world._enemy_copy_ability_policy = policy
    patch = _DummyPatch()
    write_tokens(world, patch)
    source_tokens = [token for token in patch.token_writes
                     if token[1] == runtime_patch.ENEMY_SOURCE_CONFIG_ROM_OFFSET]
    expected = runtime_patch.build_enemy_source_runtime_config(policy or {"mode": 0})
    assert source_tokens == [(APTokenTypes.WRITE, 0x100FFDC, expected)]
    if flags is None:
        assert expected == (0x41534501).to_bytes(4, "little") + bytes(32)


def test_rom_base_validation_precedes_seed_tokens():
    from ..rom import KirbyAmProcedurePatch

    steps = [name for name, _arguments in KirbyAmProcedurePatch.procedure]
    assert steps.index("apply_bsdiff4") < steps.index("validate_enemy_source_base")
    assert steps.index("validate_enemy_source_base") < steps.index("apply_tokens")


@pytest.mark.parametrize("mutation", ["none", "stale", "truncated", "version", "bitmap", "seeded"])
def test_rom_base_marker_requires_exact_legacy_placeholder(mutation):
    from ..rom import KirbyAmPatchExtension

    offset = runtime_patch.ENEMY_SOURCE_CONFIG_ROM_OFFSET
    rom = bytearray(offset + 36)
    rom[offset:offset + 4] = (0x41534500).to_bytes(4, "little")
    if mutation == "stale":
        rom = rom[:0x1000000]
    elif mutation == "truncated":
        rom = rom[:-1]
    elif mutation == "version":
        rom[offset] ^= 2
    elif mutation == "bitmap":
        rom[-1] = 1
    elif mutation == "seeded":
        rom[offset:offset + 4] = (0x41534501).to_bytes(4, "little")
    raw = bytes(rom)
    if mutation == "none":
        assert KirbyAmPatchExtension.validate_enemy_source_base(None, raw) is raw
    else:
        with pytest.raises(ValueError, match="Enemy source config marker missing"):
            KirbyAmPatchExtension.validate_enemy_source_base(None, raw)


def test_shuffled_native_overwrite_regression(tmp_path):
    """Run production C resolver against state resets and excluded callers."""
    compiler = shutil.which("cc") or shutil.which("clang") or shutil.which("gcc")
    if compiler is None:
        pytest.skip("no host C compiler available")
    root = Path(__file__).resolve().parent
    executable = tmp_path / ("shuffled.exe" if os.name == "nt" else "shuffled")
    compiled = subprocess.run(
        [compiler, "-std=c99", "-Wall", "-Wextra", "-Werror", "-I",
         str(root.parent / "kirby_ap_payload"),
         str(root / "native" / "shuffled_enemy_host.c"), "-o", str(executable)],
        capture_output=True, text=True,
    )
    assert compiled.returncode == 0, compiled.stdout + compiled.stderr
    executed = subprocess.run([str(executable)], capture_output=True, text=True)
    assert executed.returncode == 0, f"native policy check line: {executed.returncode}"


def test_shuffled_resolution_precedes_authoritative_gate():
    payload = (Path(__file__).resolve().parents[1] / "kirby_ap_payload" / "ap_payload.c").read_text()
    request = payload.split("void ap_on_request_copy_ability_transition_c(", 1)[1]
    request = request.split("KIRBY_REQUEST_ABILITY_TRANSITION_FN(kirby, rewritten_flags);", 1)[0]
    restore = request.index("rewritten_flags = ap_enemy_restore_shuffled_ability(")
    gate = request.index("selected_ability = (uint8_t)(rewritten_flags & KIRBY_ABILITY_MASK);")
    assert restore < gate
    assert "ap_is_locked_gated_ability(selected_ability)" in request[gate:]
