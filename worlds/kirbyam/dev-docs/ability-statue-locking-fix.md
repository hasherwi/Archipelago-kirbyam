# Ability-statue locking fix

## Root cause

The original Archipelago runtime patch redirected calls to the retail function at
`0x080547C4` (`sub_080547C4`). That function handles ordinary copy-ability
requests and ability-star requests.

Ability statues use a different path. The retail code in `ability_objects.c`
assigns the statue's ability directly to `Kirby::transitioningAbility` and then
calls `sub_08054C0C` at `0x08054C0C`. Consequently, statues never pass their
ability ID through the existing Archipelago request hook and could grant an
ability whose unlock item had not been received.

The decompilation identifies `Kirby::transitioningAbility` as byte offset
`0x0DD` in `struct Kirby`. Its low five bits contain the ability ID; upper bits
are transition-state flags.

## Implementation

`kirby_ap_payload/ap_payload.c` now exports
`ap_on_start_copy_ability_transition`. The hook:

1. Reads `Kirby::transitioningAbility` at verified offset `0xDD`.
2. Extracts the low-five-bit ability ID.
3. Checks that ID against `AP_ABILITY_GATE_MASK` and
   `AP_ABILITY_UNLOCK_MASK`.
4. Clears only the low five bits when the pending ability is locked.
5. Calls the original `sub_08054C0C` routine so the retail transition state
   machine and animation remain authoritative.

`kirby_ap_payload/patch_rom.py` discovers and redirects all direct Thumb `BL`
calls to both relevant retail routines:

- `0x080547C4`: request/reroll hook.
- `0x08054C0C`: pending-transition sanitization hook.

This covers statues, the Master Sword stand, and other direct writers of
`transitioningAbility`, while retaining the existing enemy-reroll behavior.

## Files changed

- `kirby_ap_payload/ap_payload.c`
- `kirby_ap_payload/patch_rom.py`
- `test/test_patch_rom.py`
- `test/test_reset_safe_shards.py`

## Validation notes

The Python files pass syntax compilation. The C payload passes Clang's
ARM7TDMI syntax check. A full payload build still requires devkitARM's
`arm-none-eabi-gcc`, which was not installed in the validation environment.
Run the normal payload build and ROM patch process in the project's configured
devkitARM environment before testing in BizHawk or on hardware.
