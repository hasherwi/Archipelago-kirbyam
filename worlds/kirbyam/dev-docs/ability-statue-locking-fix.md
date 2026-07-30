# Ability-statue locking and completely-random fixes

## Issue #874 root cause

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

## Issue #875 root cause

The same bypass also explains why a statue in `completely_random` mode gave the
same ability every time it was touched. Generation writes one deterministic
ability into each statue's native table entry. The statue object caches that
value in `Object2::kirbyAbility`, then copies the cached value directly into
`Kirby::transitioningAbility` on every touch.

The existing per-event reroll hook is attached to `sub_080547C4`; direct statue
touches never call it. Therefore the generation-time fallback mapping became
the final result instead of merely the initial/fallback value.

## Runtime implementation

`kirby_ap_payload/statue_transition_fix.c` exports the public
`ap_on_start_copy_ability_transition` symbol used by `patch_rom.py`. It replaces
the original Issue #874 implementation at link time while preserving and
extending its behavior:

1. It snapshots the caller address before any helper call can clobber `lr`.
2. It identifies direct regular-statue calls as callers inside
   `sub_080AA588` (`0x080AA588..0x080AA617`).
3. When statue randomization is enabled and the mode is `completely_random`, it
   advances the shared runtime RNG and selects a fresh ability for that touch.
4. It removes currently locked gated abilities from the candidate mask before
   selection. Statues therefore reroll among unlocked allowed abilities rather
   than selecting a locked ability and then becoming Normal.
5. It ignores `ability_randomization_no_ability_weight`, matching the documented
   rule that randomized statues always grant an ability when an eligible one is
   available.
6. It preserves all upper transition flags and writes only the low five ability
   bits.
7. It performs the final Issue #874 gating check for every transition source.
8. It emits the existing statue telemetry for shuffled and completely-random
   touches.
9. It calls the original `sub_08054C0C` transition state machine.

Independent random draws may legitimately repeat the previous ability. The fix
guarantees a new draw per touch, not a forced-different result.

The Master Sword stand begins at `sub_080AA618` and is intentionally outside the
regular statue range because it is not part of the configurable statue table.
It still receives the final gating check.

## Seed-specific statue toggle

The shared `base_patch.bsdiff4` cannot know whether a particular seed enabled
`ability_randomization_statues`. The linker reserves the final four bytes of the
existing payload window at ROM address `0x0815F69C` (file offset `0x15F69C`) for
`gApAbilityRandomizationStatuesEnabled`.

`rom.write_tokens()` writes an explicit little-endian `0` or `1` into that word
for every generated patch. This avoids expanding the runtime mailbox protocol
and prevents completely-random enemy-only seeds from accidentally rerolling
statues.

## Link-time replacement

The `fix-statues` branch already contained an Issue #874 hook with the same
public symbol. `fix875_rename_start_hook.h` renames that older implementation
only while compiling `ap_payload.c`. `statue_transition_fix.c` then owns the
public symbol. Function/data sections plus linker garbage collection remove the
unreferenced renamed implementation from the final payload.

The linker explicitly keeps all `ap_on_*` hook sections because `patch_rom.py`
resolves them by ELF symbol name rather than through normal relocation
references.

## Files changed

- `kirby_ap_payload/Makefile`
- `kirby_ap_payload/fix875_rename_start_hook.h`
- `kirby_ap_payload/statue_transition_fix.c`
- `kirby_ap_payload/linker.ld`
- `rom.py`
- `test/test_rom_tokens.py`
- `test/test_statue_completely_random_runtime.py`

## Build requirement

These source changes alter the injected payload, so `data/base_patch.bsdiff4`
must be regenerated with the project's normal clean USA ROM and devkitARM build
workflow before the fix is testable in a generated `.apkirbyam` patch.

## Per-touch completely-random behavior

Issue #875 shares the same retail bypass: regular statues never call the
`sub_080547C4` request hook that rerolls enemy and dropped-star grants. The
transition-start hook now identifies only callsites inside `sub_080AA588` and,
when statue randomization is enabled in `completely_random` mode, replaces the
pending ability with a fresh draw from the seed-specific statue pool before
applying the final gating check. The Master Sword stand begins at
`sub_080AA618`, so it is outside the reroll callsite range.

The full option matrix, per-seed ROM mask, gating behavior, telemetry contract,
and executable tests are documented in
[`ability-statue-runtime-contract.md`](ability-statue-runtime-contract.md).
