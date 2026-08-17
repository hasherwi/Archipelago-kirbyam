# Ability-statue gating and per-touch randomization

This document describes the runtime changes for Issues #874 and #875. The
implementation intentionally shares one transition-start hook because both bugs
come from the same retail acquisition path.

## Retail acquisition paths

Ordinary enemy copy requests and dropped ability stars call `sub_080547C4`.
The existing Archipelago request hook can rewrite those requests before the
retail state machine begins.

Regular ability statues use `sub_080AA588`. They bypass `sub_080547C4`, write
`Object2::kirbyAbility` directly into `Kirby::transitioningAbility`, and then
call `sub_08054C0C`. The Master Sword stand uses the next callback beginning at
`sub_080AA618` and also calls `sub_08054C0C`.

The decompilation identifies `Kirby::transitioningAbility` at offset `0x0DD`.
Its low five bits are the ability ID; upper bits are transition flags.

## Hook placement

`patch_rom.py` discovers direct Thumb `BL` calls to both retail functions:

- `0x080547C4`: ordinary request and live enemy/ability-star reroll hook.
- `0x08054C0C`: authoritative pending-transition hook for statues and other
  direct writers.

`ap_on_start_copy_ability_transition` snapshots `lr` before calling helpers and
converts it to the original callsite PC with `(lr & ~1) - 4`. Only callsites in
`[0x080AA588, 0x080AA618)` are regular statue touches. The end boundary excludes
the Master Sword stand, which must retain its native grant behavior.

## Issue #874: ability gating

The transition-start hook always performs a final gating check, regardless of
randomization mode or whether statue randomization is enabled. A pending
ability is removed when its bit is present in `ability_gate_mask_runtime` but
absent from `ability_unlock_mask_runtime`. Only the low five ability bits are
cleared, preserving the retail transition flags and animation state.

The client also supports legacy slot data that lacks
`enemy_copy_ability_policy`. Gating is independent of randomization, so the
client still derives and synchronizes gate/unlock masks from legacy option and
item fields. When `ability_gating` is disabled, both masks are explicitly zero.

## Issue #875: completely-random statues

Generation-time statue table writes are only a deterministic fallback. In
`completely_random` mode, every verified regular-statue touch performs a fresh
runtime RNG draw before the transition starts. Repeated results remain possible
by chance; the contract is a fresh draw, not a forced-different result.

The generated ROM carries two seed-specific configuration masks:

- Initial gate mask at ROM `0x0815F698` / file offset `0x0015F698`, exposed as
  `gApAbilityGateMaskInitial`. It is zero when ability gating is disabled. When
  enabled, it protects startup, reset, and offline windows before the client
  has synchronized the live mailbox.
- Statue pool mask at ROM `0x0815F69C` / file offset `0x0015F69C`, exposed as
  `gApAbilityRandomizationStatueAllowedMask`. Zero disables live statue rerolls.

`rom.py` always writes both words. The statue mask is built from the same
normalized pool used for static table writes, so runtime and fallback behavior
agree on the custom whitelist and `ability_randomization_minny`. The masks are
in ROM rather than new mailbox fields so they are available before BizHawk
connects and do not change the client transport layout. Once connected, the
client remains authoritative for the live gate and unlock masks.

For a live draw, the payload removes abilities that are currently gateable but
locked, then selects uniformly from the remaining set bits. If no candidates
remain, the result is Normal. The existing final gating check still runs after
the draw as a defensive authority against configuration races or corrupted
state.

## Option matrix

| Configuration | Regular statue behavior |
|---|---|
| Randomization off | Native ability; locked gated abilities become Normal. |
| Statues toggle off | Native ability in every mode; gating still applies. |
| Shuffled + statues on | Fixed generation-time remap; locked result becomes Normal. |
| Completely random + statues on | Fresh per-touch draw from the statue-specific, currently unlocked pool. |
| Ability gating off | No abilities are removed from the configured statue pool. |
| Ability gating on | Locked gateable abilities are excluded before the random draw. |
| Custom whitelist | Runtime mask contains exactly the supported whitelisted abilities. |
| Minny off | Mini is removed from both static and live statue pools. |
| No-ability weight | Ignored by statues; randomized statues always draw an ability when one is available. |
| Passive enemies | Does not affect statues. |
| Minibosses / boss spawns | Do not affect statues. |
| Master Sword stand | Never randomized; final gating authority remains available. |

## Telemetry

Direct regular statues bypass the request hook's telemetry. The transition-start
hook emits a statue event in shuffled and completely-random modes after gating
has determined the final ability. The event records the original callsite and
active Kirby index. Telemetry is diagnostic only and does not control gameplay.

## Test coverage

- `test_statue_runtime_logic.py` compiles and executes the actual pure C helper
  header, covering callsite boundaries, mode/toggle behavior, gating masks,
  empty pools, uniform set-bit selection, and transition-flag preservation.
- `test_enemy_copy_ability_runtime_patch.py` covers the generated statue mask,
  custom whitelists, Minny inclusion/exclusion, no-ability independence, and
  disabled combinations.
- `test_rom_tokens.py` verifies both per-seed mask writes, exact little-endian
  encoding, gating-on/off behavior, and one-write semantics.
- `test_statue_runtime_config.py` covers structured and legacy client runtime
  configuration, including the gating-disabled zero-mask contract.
- `test_patch_rom.py` covers both hook-target discovery and runtime-safe queue
  annotations used by patch generation.

A source change to the payload requires regenerating
`data/base_patch.bsdiff4` with the project's clean USA ROM and devkitARM build
workflow before gameplay testing.
