# KirbyAM APWorld Changelog

Contract for `## Unreleased` and all post-public `## v...` sections:

- `### New Features`
- `### Bug Fixes`
- `### Internal Changes`

## Unreleased

### New Features

- Add `Starting Kirby Color` (`starting_kirby_color`) with canonical color definitions in `data/colors.json`, generation-time deterministic `random_color` resolution, resolved color emission in `slot_data` (`starting_kirby_color` + `starting_kirby_color_name`), and runtime payload synchronization via new mailbox register `starting_kirby_color_id` (`0x0203B050`) that applies non-Pink palettes while keeping Pink as no-op behavior. Non-Pink color changes become visible after the first room/area transition. Generation/client logs now always record the selected color in log files and only stream those messages when `enable_debug_logging` is enabled. Follow-up hardening validates `colors.json` keys as safe option identifiers and IDs within `0..13`, and reduces per-tick runtime sync reads via cached sync state plus periodic revalidation for reset recovery (Issue #597).
- Add 15 decomp-aligned world-map big-switch AP checks (`HUB_SWITCH_*`) with a dedicated ROM transport register (`hub_switch_flags` at `0x0203B04C`), BizHawk resend/dedupe polling, payload hook integration at the world-map unlock dispatcher callsite (`sub_08039ED4`), protocol/address contract updates, and regression coverage for data/polling/patch offsets/region binding (Issue #481).
- Expand tracker integration surface by exporting all locations, all rooms (including those outside Room Sanity), and all received unique items via expanded KirbyAM `slot_data` for use in tracker templates and generic player/multiworld trackers (Issue #114).
- Add `Start With All Maps` (`start_with_all_maps`) option to the `Make the game easier` option group. When enabled, all nine area maps are precollected at generation time and removed from the randomized item pool (replaced with filler), so the player begins with every map already acquired (Issue #584).
- Updated room names to match the names that Wikirby uses. (Issue #587)

### Bug Fixes

- Updated `Ability Randomization: Minny` (`ability_randomization_minny`) so that it's off by default (Issue #583).
- Harden vitality delivery against transition/reset replay by clamping native vitality counter grants to the shipped AP vitality item cardinality (4), and in `one_hit_mode=exclude_vitality_counters` scrub native vitality back to `0` during gameplay so vitality receipts cannot persist in that mode (Issue #571).
- Fix missing boss-defeat LocationChecks when the matching shard is already owned by adding a conservative client fallback: rising-edge bits from `boss_mirror_table_native` byte 0 (bits 0-7) now backfill boss checks when `boss_defeat_flags` is absent for that fight (Issue #573).
- Hide additional KirbyAM reconnect/resend diagnostics from the live client output unless `Enable Debug Logging` is enabled, while still writing those diagnostics to log files unconditionally (`NoStream`-filtered stream suppression only); includes watcher transport reconnect messages and resend diagnostics for boss/major/vitality/sound-player LocationChecks polling (Issue #582).

### Internal Changes

- Improve `worlds/kirbyam/build.py` usability for non-author machines by prompting for missing required patch inputs in interactive runs (including missing `--rom` when `--source-type arg` is selected), adding `--source-type file` fallback guidance when `rom_path.tmp` is invalid, and introducing `--non-interactive` fail-fast behavior for automation/CI (Issue #607).
- Expose all configured KirbyAM seed options in `slot_data` (including `start_with_all_maps` and `enable_debug_logging`) so tracker surfaces can render the exact seed configuration from slot data without inferring from partial fields (Issue #114).
- Move unswallowable enemy exclusion policy from a static runtime list into `data/enemies.json` source metadata (`can_be_swallowed`) and represent the currently configured non-swallowable enemies there: `GLUNK`, `JACK`, and `SQUISHY` (Issue #570).

## v0.1.2

### New Features

- Add `Ability Randomization: Minny` (`ability_randomization_minny`) so Minny can be excluded from enemy copy-ability randomization and kept at vanilla behavior while other enemy ability sources remain randomized (Issue #572).

### Bug Fixes

- Fix duplicate vitality grants caused by reconnect/reset mailbox replay by adding a ROM-payload vitality replay guard (`delivered_vitality_item_bits`) so each `VITALITY_COUNTER_1..4` AP item is applied at most once per AP mailbox session, and add item-pool invariants/tests that enforce vitality counters appear exactly once in pool modes that include them (Issue #571).
- Exclude unswallowable enemies from the enemy copy-ability randomization pool to prevent no-ability lockouts from non-inhalable enemies; this currently removes `GLUNK` and reserves `SCARFY`/`SHOTZO` as blocked keys for future source-table additions (Issue #570).

### Internal Changes

- Gate ROM delivery-counter reconciliation diagnostics behind `Enable Debug Logging` (`enable_debug_logging`) so non-debug sessions only show normal sent/received item notifications; counter-ahead/back-in-range/rewind/fallback progress messages are now suppressed unless debug logging is enabled (Issue #574).

## v0.1.1

### New Features

- None.

### Bug Fixes

- Harden `One-Hit Mode` (`one_hit_mode`) `exclude_vitality_counters` behavior by removing health-restoring filler (`Small Food`, `Max Tomato`) from filler selection in that mode; when combined with `No Extra Lives`, `1 Up` is also excluded from the already-reduced filler pool.

### Internal Changes

- Gate additional non-user-facing BizHawk client diagnostics behind `enable_debug_logging`, including AP session readiness/reconnect-state logs, room-sanity resend diagnostics, mailbox delivery cursor fast-forward logs, and send/receive queue diagnostic logs; user-facing popups and gameplay behavior are unchanged.
- Add regression coverage for the one-hit/no-extra-lives filler-pool interaction and one-hit HP clamp behavior, plus debug-log gating coverage for runtime gameplay-gate, notification queue, room-sanity resend, mailbox delivery, and AP session-ready diagnostics.

## v0.1.0

First Public Build!

### New Features

- Add `One-Hit Mode` (`one_hit_mode`) with both `exclude_vitality_counters` and `include_vitality_counters` behaviors, keeping the HP cap tied to vitality progression and supporting the public gameplay contract for the mode (Issue #549).
- Add `No Extra Lives` (`no_extra_lives`) and `DeathLink`, including native runtime enforcement, outgoing/incoming DeathLink flow, slot-data support, flavor text, and end-to-end gameplay validation guidance (Issue #491).
- Add the public enemy copy-ability randomization feature set, including shuffled/completely-random logic, boss/miniboss controls, passive-enemy support, and `No Ability Weight` configuration for included randomized sources (Issues #338, #398, #399).
- Add major AP location families and gameplay checks for boss defeats, major chests, vitality chests, Sound Player chest, and optional Room Sanity, along with the supporting room/region topology needed for those checks (Issues #32, #35, #428, #480).
- Add player-facing quality-of-life features and content for the public release line, including stable item groups, unhidden supported common AP options, shipped consumable filler effects, clearer sent/received item messaging, and standardized item/location naming (Issues #295, #370, #432, #460, #546).

### Bug Fixes

- Harden the BizHawk client and ROM payload against pre-public integration regressions across mailbox delivery, reconnect recovery, goal reporting, gameplay-state gating, and title-demo suppression so item delivery and location checks remain stable in normal play (Issues #269, #419, #437, #457, #477, #489).
- Fix shard and boss progression handling by preserving native shard state, introducing AP-owned shard authority, and protecting post-boss cutscene/transition behavior from white-screen and premature-ownership regressions (Issues #393, #478, #505).
- Fix release-blocking content and integration bugs found during pre-public work, including missing vitality chest region binding, host upload/auth registration problems, handler detection issues, release packaging problems, and startup-state corruption in the ROM hook path (Issues #428 and related pre-public regressions).

### Internal Changes

- Align the public-release contract by normalizing ability-randomization naming/defaults, removing legacy compatibility paths and aliases, and cleaning up pre-public template output so the shipped option surface matches current behavior.
- Expand protocol, slot-data, patching, reconnect-chaos, release-metadata, snapshot, and negative-path test coverage across the world, client, and payload pipeline to support the first public version.
- Establish the pre-public build and release workflow baseline, including ROM patch rebuild smoke coverage, release integrity checks, and maintainer validation/documentation needed for the `v0.1.0` release line.
