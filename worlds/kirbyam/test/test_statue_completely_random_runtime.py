"""Source-level regressions for direct ability-statue runtime behavior."""

from __future__ import annotations

from pathlib import Path


_WORLD_DIR = Path(__file__).resolve().parents[1]
_PAYLOAD_DIR = _WORLD_DIR / "kirby_ap_payload"


def test_replacement_hook_rerolls_direct_statues_per_touch() -> None:
    content = (_PAYLOAD_DIR / "statue_transition_fix.c").read_text(encoding="utf-8")

    assert "ABILITY_STATUE_TOUCH_FN_START_ADDR 0x080AA588u" in content
    assert "ABILITY_STATUE_TOUCH_FN_END_ADDR 0x080AA618u" in content
    assert "gApAbilityRandomizationStatuesEnabled" in content
    assert "ABILITY_RANDOMIZATION_MODE_COMPLETELY_RANDOM" in content
    assert "ap_is_direct_ability_statue_callsite(caller_pc)" in content
    assert "AP_ABILITY_RANDOMIZATION_ALLOWED_MASK & ~locked_mask" in content
    assert "ap_statue_next_rng_u32()" in content
    assert "AP_ABILITY_RANDOMIZATION_NO_ABILITY_WEIGHT" not in content
    assert "KIRBY_START_ABILITY_TRANSITION_FN(kirby)" in content


def test_replacement_hook_preserves_issue_874_final_gating() -> None:
    content = (_PAYLOAD_DIR / "statue_transition_fix.c").read_text(encoding="utf-8")

    assert "ap_statue_is_locked(selected_ability)" in content
    assert "pending_flags & (uint8_t)~KIRBY_ABILITY_MASK" in content
    assert "*transitioning_ability = pending_flags" in content


def test_linker_reserves_seed_specific_statue_config_word() -> None:
    linker = (_PAYLOAD_DIR / "linker.ld").read_text(encoding="utf-8")
    makefile = (_PAYLOAD_DIR / "Makefile").read_text(encoding="utf-8")

    assert "AP_CONFIG_ADDR = 0x0815F69C" in linker
    assert "KEEP(*(.apconfig))" in linker
    assert "SIZEOF(.apconfig) == 4" in linker
    assert "statue_transition_fix.o" in makefile
    assert "-include fix875_rename_start_hook.h" in makefile
    assert "--gc-sections" in makefile
