"""Source and patch-tool contracts for ability-statue runtime hooks."""

from __future__ import annotations

import importlib.util
from pathlib import Path


_WORLD_DIR = Path(__file__).resolve().parents[1]
_PAYLOAD_DIR = _WORLD_DIR / "kirby_ap_payload"
_PATCH_ROM_PATH = _PAYLOAD_DIR / "patch_rom.py"


def test_patch_rom_queue_annotation_is_runtime_safe() -> None:
    """`multiprocessing.Queue` is a factory method and cannot be subscripted."""
    source = _PATCH_ROM_PATH.read_text(encoding="utf-8")
    assert "from multiprocessing.queues import Queue as MultiprocessingQueue" in source
    assert "result_queue: MultiprocessingQueue[str]" in source
    assert "mp.Queue[str]" not in source


def test_statue_transition_hook_documents_exact_runtime_contract() -> None:
    payload_source = (_PAYLOAD_DIR / "ap_payload.c").read_text(encoding="utf-8")
    helper_source = (_PAYLOAD_DIR / "statue_runtime_logic.h").read_text(encoding="utf-8")
    hook_body = payload_source[
        payload_source.index("void ap_on_start_copy_ability_transition"):
        payload_source.index("void ap_on_collect_sound_player_chest")
    ]

    assert "gApAbilityGateMaskInitial" in payload_source
    assert "gApAbilityRandomizationStatueAllowedMask" in payload_source
    assert "ap_statue_should_reroll" in hook_body
    assert "ap_statue_unlocked_candidate_mask" in hook_body
    assert "ap_statue_apply_final_gate" in hook_body
    assert "AP_ABILITY_RANDOMIZATION_NO_ABILITY_WEIGHT" not in hook_body
    assert "AP_STATUE_TOUCH_CALLSITE_START 0x080AA588u" in helper_source
    assert "AP_STATUE_TOUCH_CALLSITE_END   0x080AA618u" in helper_source

    linker_source = (_PAYLOAD_DIR / "linker.ld").read_text(encoding="utf-8")
    rom_source = (_WORLD_DIR / "rom.py").read_text(encoding="utf-8")

    # Issue #852 prepends a starting-color word without moving the already
    # shipped gate/statue token addresses. Verify the complete ordered ABI
    # rather than assuming the ability words begin the config region.
    assert "AP_CONFIG_ADDR = 0x0815F694" in linker_source
    assert "KEEP(*(.apconfig.color))" in linker_source
    assert "KEEP(*(.apconfig.gate))" in linker_source
    assert "KEEP(*(.apconfig.statue))" in linker_source
    assert linker_source.index(".apconfig.color") < linker_source.index(".apconfig.gate")
    assert linker_source.index(".apconfig.gate") < linker_source.index(".apconfig.statue")
    assert "SIZEOF(.apconfig) == 12" in linker_source
    assert "ABILITY_GATE_MASK_INITIAL_ROM_OFFSET = 0x0015F698" in rom_source
    assert "ABILITY_RANDOMIZATION_STATUE_ALLOWED_MASK_ROM_OFFSET = 0x0015F69C" in rom_source


def test_transition_start_target_remains_discoverable() -> None:
    spec = importlib.util.spec_from_file_location("kirbyam_patch_rom_statue_test", _PATCH_ROM_PATH)
    assert spec is not None and spec.loader is not None
    patch_rom = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(patch_rom)

    rom_base = 0x08000000
    scan_start = 0xC0
    target = patch_rom.ORIGINAL_ABILITY_TRANSITION_START_FN_ADDR
    rom = bytearray(scan_start + 8)
    rom[scan_start:scan_start + 4] = patch_rom.thumb_bl_bytes(
        rom_base + scan_start,
        target,
    )

    assert patch_rom.discover_thumb_bl_callsites_to_targets(
        rom,
        {target, target | 1},
        rom_base=rom_base,
        scan_start=scan_start,
        scan_end=patch_rom.PAYLOAD_OFFSET,
    ) == [scan_start]
