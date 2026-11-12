# KirbyAM APWorld Changelog

Contract for `## Unreleased` and post-public `## v...` sections going forward:

- `### New Features`
- `### Improvements`
- `### Known Limitations`
- `### Bug Fixes`
- `### Internal Changes`

## v0.5.1

### New Features
- Access to the Copy Ability Room is now an AP Item (Issue #1002).

### Improvements
- Add the exact late post-clear Central Master source and forward carrier as a fifth Carrot Room7-to-lower-Room13 alternative. Require all eight unique shards, actual Dimension access and the Dark Meta Knight sequence, reachable Central, both carrier Hubs and the enabled Carrot Key. Bounded native and source-derived health evidence grants no helper, return, upper-room or reward credit (PR #1052).
- Add the finite original Waddle Doo-to-UFO carry and maximum-charge large shot as a tenth Chocolate chest alternative, preserving source permission and all nine existing routes (PR #1052).
- Add the original finite Waddle Doo-to-Fighter route and ordinary first combo as a ninth Chocolate chest alternative, preserving prior routes and Fighter permission behavior (PR #1052).
- Add the original finite Waddle Doo-to-Sword route and ordinary first slash as another Chocolate chest alternative, preserving its seven existing routes (PR #1052).
- Add source-aware, entry-specific ranged routes for selected Bomb Blocks, timed switches, the Mustard map and Olive Sound Effects chest. Each accepted alternative keeps its own finite source, carried ability, attack and timing requirements; ordinary solo alternatives remain available (PR #1052).
- Add source-aware metal traversal with exact arrival compartments and reviewed ability-carry routes. Stone and Burning are now progression unlocks when ability gating is enabled; only Beam is automatically precollected. Explicit starting inventory and historical seed gate lists remain supported (PR #1051).
- Make the randomizer better understand what Kirby can actually do underwater and with frozen enemies. Correct two Olive Ocean routes that do not need a metal-breaking ability, keep one-way platforms one-way, and require a separate enemy for each frozen-enemy hit. The Sound Effects chest accepts its finite Frosty Ice/UFO witnesses or a guarded permanent Ice source and carry route, independently of Frosty assignment (PRs #1048, #1051, #1052).
- Cutter, Wheel and Mini are no longer in the starting inventory, with traversal logic added to support their removal (PRs #1041, #1042).

### Known Limitations
- Ranged-attack coverage is incomplete. Five bounded targets preserve the older base rule outside reviewed source assignments, including native Mustard map and Yellow Paint assignments; relevant physical outcomes still need adjudication. Unsupported source assignments and routes retain their existing partial behavior; the implemented subset does not establish universal wall piercing, maximum range or removal of starting abilities (PR #1052).
- Only the North American ROM is supported; AP notifications are English.
- Chests retain their original item sprites and collection animations; statues retain their original ability appearance.
- mGBA notifications require the visible **Archipelago Connector** scripting panel; they are plain text, not game-image overlays.
- Beam remains automatically precollected. Native evidence consists of bounded source, carrier and action proofs, not uninterrupted full-game, direct AP one-HP or universal multiplayer replays.
- Generation rejects unsafe minimal-accessibility placements before archive output. Finite test matrices do not prove every seed or option combination.

### Bug Fixes
- Keep the Carrot Castle Room 7 route limited to Room 13's lower compartment, and gate only the reviewed Rainbow Green Paint, Carrot Yellow Paint and Cabbage Chocolate chest targets. Preserve unrelated exits, Secret Notes and Room Sanity checks (PR #1052).
- Reconcile conditional Ice, Crash, Missile, Parasol, Magic and Spark starting permissions after their target locations or entrances exist, preserving requested item counts and unrelated classifications (PR #1052).
- Add guarded permanent Burning alternatives for the Batafire and Master Hand chests, and classify required Ice before region creation for explicit Main-order starting inventory (PR #1051).
- Require reviewed Burning routes through Rainbow Route Room 41 and Moonlight Mansion Rooms 4, 5 and 15, preserving directed entrances and independent checks. Remove the unvalidated Moonlight Room 15 upper-return shortcut to its Warp Star (PR #1051).
- Add reviewed Stone access to Beginning Notes and retained-Hammer access to Peppermint Palace's left 1-Up chest. Keep separately demonstrated Normal routes free of unnecessary copied-ability requirements (PR #1051).
- Require an actual Hammer source and reviewed carry route for the Peppermint Palace7-9 metal chest. Joint native traces preserve the same Hammer through its earlier Room7 chest; renewable Copy Ability Room statues support mixed-live source policies without assuming a lucky Bonkers grant. The separate rope chest is unchanged.
- Keep Cabbage Cavern Room3's fresh upper-left entrance separate from its lower/right passages. Preserve the directed Normal Bomb and swimming routes without requiring a metal ability or duplicating its room check.
- Keep Peppermint Palace's three chest-room approaches and Snow hallway separate. Require a reviewed Bonkers-Hammer or renewable statue-backed Stone route through the Room7 floor, preserving exact check IDs and one room check per physical room.
- Require a reviewed physical Burning source and carry route for the Peppermint Palace7-19 metal chest, while preserving both ordinary exits and its room check.
- Reject seeds that leave enabled Kirby checks unreachable, including under minimal accessibility. Reuse bounded source-assignment validation for minimal and audit actual placed progression after finalization; the safety guard is separate from the source-backed starting-inventory change.
- Preserve shuffled enemy ability assignments when native enemy behavior overwrites them, including Waddle Doo's Beam and Parasol state resets (Issue #1049).
- Correct Rainbow Route East’s Big Switch location and map grouping to Moonlight Mansion Room 2-09, so reaching the Rainbow Route hub no longer makes the switch reachable without a valid route through Moonlight Mansion (PR #1045, BlameMateo).

### Internal Changes
- Record reviewed Master719 source/carrier scalars, finite-health classes and local receipt boundaries, preserving historical Normal404 evidence. Ten key-on positive traces (five profiles, each repeated) and prior 54 real-generation checks do not establish full PR completion or replace final-head aggregate/package validation (PR #1052).
- Add a source-fingerprinted bounded ranged status report and real-installer coverage checks, separating public policy samples from synthetic narrowed pools. Correct stale 209/310/533/825 scope wording without changing traversal or upgrading historical native evidence (PR #1052).
- Add a normalized traversal-target ownership ledger, move-specific native evidence and regressions. Correct the native-object scanner to follow size-terminated streams and the actual spawn-list field (PR #1052).
- Preserve the historical 22-ability fallback for legacy slots, add source-aware traversal and native-evidence regressions, and classify expected unsafe minimal-accessibility generation rejections separately from successful fuzz runs (PR #1051).
- Add source-aware peg and cannon-fuse traversal using reachable enemies and Copy Ability statues, and keep Minny fixed to Mini (PR #1041).

## v0.5.0

### New Features
- Add Rainbow, Candy Corn, Negative, Pineapple, Cotton Candy, Royal, Pumpkin and Mint Chip Kirby palettes with normal, UFO and HUD rows; retain native effects and owned spray-paint precedence.
- Added eight Area Key progression items for Areas 2 through 9. Cross-area mirrors (and other transitions like Warp Stars) now require the destination area's key. Locked mirrors show boards and their associated Warp Stars stay hidden; receiving the key updates nearby mirrors and eligible Warp Stars while preserving other unlock requirements (Issues #42, #1010).
- Add a default-on Area Keys option under Make the game easier. Turning it off removes Area Key requirements and replaces the eight keys with filler.
- Added 15 Hub Connection progression items that unlock matching hub shortcuts while preserving alternate overland routes. Physical Big Switch checks remain independent, and received connections are restored across reconnects (Issue #482).
- Add Hub Teleport Trap, which returns Kirby to Rainbow Route’s central hub (Issue #697).
- Add `/goal` to display the seed's victory condition, including its resolved boss target while preserving legacy hidden targets (Issue #923).
- Add Defeat a Number of Area Bosses: defeat any 1–8 distinct area bosses, default 3 (Issue #973). Other goals ignore the count. New count-goal seeds require the updated KirbyAM client; older clients interpret the new goal as Dark Mind.

### Improvements
- Add a release-preparation runbook, read-only readiness checks and staging status reporting, with consistent exact-version or matching base-version changelog selection for release candidates (Issue #1012). Support a single-maintainer review path without mandatory settings evidence or a separate reviewer; a live release rehearsal remains pending.

### Known Limitations
- Only the North American ROM is supported; AP notifications are English.
- Chests retain their original item sprites and collection animations; statues retain their original ability appearance.
- mGBA notifications require the visible **Archipelago Connector** scripting panel; they are plain text, not game-image overlays.

### Bug Fixes
- Correct Rainbow Route 1-06’s small chest to the lower cave, preventing the upper path from granting access (Issue #1032).
- Avoid a misleading ROM compatibility warning when disconnecting from the server.
- Resume item delivery and gameplay polling when continuing a completed save, while keeping ending, title and demo screens deferred (Issue #1004).
- Keep duplicate incoming DeathLinks suppressed when reconnecting to the same seed and slot.
- Preserve Mr. Frosty’s ice cubes and Boxy’s boxes as no-ability sources when passive-enemy ability randomization is disabled.
- Keep Invincibility Candy queued until its native effect can start, including after leaving hubs or boss rooms and after an active Candy effect expires.
- Honor excluded passive enemies, minibosses, and boss spawns in Completely Random ability mode.
- Make repeated explicit `/toggle_text` disable commands safe for Kirby slots.
- Recreate the mGBA connector listener after socket errors and ignore callbacks from an obsolete listener.
- Keep Moonlight arrivals in Olive 6-13 behind the received Olive lever wall while preserving the physical RoomSanity check and return chute.
- Retry mGBA connections after self-connected sockets or malformed VERSION replies instead of stopping the client. Shared Archipelago transport and the stock BizHawk launcher are unchanged.
- Preserve excluded Minny grants in Completely Random mode while retaining normal ability gating (Issue #997).
- Correct the Carrot Castle lever placement and labels to room 5-05 (Issue #972).
- Restore outgoing DeathLink detection on dead gameplay frames while keeping fresh item delivery paused. Links received while already dead no longer kill the next respawn (Issue #975).
- Restore packaged region discovery on Python 3.11 by using a package resource anchor.
- Fix room-sanity generation by making each physical room check reachable from its valid compartment and restoring the missing Moonlight 2-05 lower descent (Issues #945, #969).
- Random-per-room colors now update Kirby and the HUD when native palette transformations remain enabled during gameplay (Issue #966).
- Allow the six guaranteed starting ability receipts and notices during the tutorial. Other items stay deferred, and Sword still requires its ability item (Issue #967).
- Bootstrap Kirby build/test dependencies with checksum-pinned pip 26.2.2 and certifi 2026.10.19 after the eMudhra/emSign incident (Issue #978), with matching development guidance. Global AP dependencies, Docker and general workflows are unchanged.
- Fix repeated healing sounds after hitting Scarfy or Bomber with enemy health set to 50%, and keep enemy health meters accurate when scaled health rounds to a whole number (Issue #1028).

### Internal Changes
- Isolate the stake-rule test fixture from shared graph data and exercise cold and warm Area Key and Dimension Mirror caches to prevent order-dependent test failures (PR #1014).
- Preserve compiled Hub switch mapping with generated lookup tables, fixed configuration addresses and explicit overlap checks. Historical native door aliases remain unchanged.
- Verify the complete wheel inventory and SHA-256 bytes before offline Kirby ROM-smoke dependency installation (Issue #980; broader dependency matrices remain open).
- Pin Kirby workflow actions to audited commit identities and reject mutable action references (Issue #981; interpreter/toolchain downloads remain separate).
- Add draft-artifact receipts, signed provenance and download verification; refuse published-asset replacement (Issue #983). Plugin-trust guidance and optional immutability safeguards are documented.
- Gate Kirby staging on release-tag pushes and trusted-main validation, preserving existing environment restrictions with optional tag protection; remove publisher PR authority and limit self-hosted smoke runs to main (Issue #982).
- Carry the abandoned v0.4.2 security work into v0.5.0; see the [integration plan](dev-docs/v050-security-integration.md) for dependencies and pending acceptance gates.
- Execute the full native mailbox/ACK path for all 24 Spray Paint/Music Sheet IDs and Vitality grants for all four player structures, including duplicate delivery and dead-state safety (Issues #971, #953).
- Exercise all eight shard receipts through twelve cold client/transport restarts, partial native saves and interleaved acknowledged food receipts (Issue #974).
- Verify starting Vitality with stock-server empty/nonempty normal histories, duplicate precollects and repeated cold-RAM recovery without replay healing (Issue #943).
- Integrate room connections and requirements into world-generation logic (PR #914).

## v0.4.1

### New Features
- Choose Shadow, Ivory, Citrus, White or Lavender from Kirby Squeak Squad as your starting Kirby color (Issue #599). They're also included in the random color pool.

### Improvements
- Configure one-hit starts through Minimum Health and Maximum Health. The redundant One-Hit Mode selector is removed from templates; older YAML presets still convert automatically (Issue #955).
- Reopening a game remembers items confirmed by the updated client, so food, lives, batteries, invincibility and traps are not applied again and old receive messages stay quiet. Permanent items can still be restored when loading an older save. If an interruption leaves an item's delivery uncertain, the client asks you to resolve it instead of guessing (Issue #952, PR #954).

### Known Limitations
- Progression: The entire game is still only two spheres. This means you can complete almost the entirety of Kirby and the Amazing Mirror without ever having to receive an item, except open the Dimension Mirror. In other words, you can do everything in the game except defeat Dark Mind without ever receiving an item from another player. This is a consequence of the original game design. We have plans to gate your progression in other ways, but they all require coding/hacking in intentional blockers.
- Localization: Only the North American ROM is supported. All AP notifications are in English.
- Native sprites and animations: Chests still show their original item sprite and collection animation. Statues still show their original ability.
- mGBA: notifications appear as plain text in the **Archipelago Connector** scripting panel, which must be visible. They do not appear over the game image.

### Bug Fixes
- Keep Kirby and the phone, life icon and health display colors together, including Pink. Random-per-room takes priority over a saved owned-paint choice, then the AP static color, then default Pink; treasure-room choices now survive native save/load (Issue #918).
- Restore acknowledged lever pulls after resets and reconnects, including already-loaded levers, without granting their separate wall items (Issue #949). Regenerate the ROM patch for immediate visual recovery.
- Pause new item deliveries during the update that applies an incoming DeathLink, including links received while checking locations. Items already being delivered can still finish, and new deliveries resume after Kirby respawns (Issue #944).

### Internal Changes
- List ability items, including guaranteed starting abilities, in `items.json` for tracker support (Issues #957, #961).
- Updated to AP 0.6.8 (Issue #933)

## v0.4.0

### New Features
- Added `minimum_health` and `maximum_health` YAML options for a custom starting/final HP capacity (Issues #778, #947). Defaults remain 6/10; all starting/final ranges within 1..10 HP are supported with up to nine unique Vitality Counter upgrades. Existing One-Hit Mode presets override these options.
- mGBA now supported as an optional emulator.
- All minor chests are added as locations and no longer provide their native item.
- Spray Paints and Music Sheets added as AP items.
- Added an `/abilities` client command that lists the abilities currently unlocked for the slot (Issue #891, PR #951).
- Added a new option: `enemy_health_multiplier`. Scale all enemies' health values between 50% to 500% of the original game. It defaults to 100% which matches the original game (Issue #880).
- Added `random_color_per_room` to Starting Kirby Color. It chooses an initial supported palette at generation, then changes to a different supported palette whenever the connected BizHawk client observes Kirby enter a different room (Issue #857).
- Added four progression items that independently open the walls controlled by those levers. Pulling a lever now sends its AP location check without opening the wall; receiving the matching Lever Wall item sets the native wall-unlock state instead (Issue #859).

### Improvements
- Ability unlock gating also applies at the final native ability commit, after roulette and other pending-ability writes (Issue #892).
- Unused Vitality Counters are replaced through the existing filler/trap policy while all vitality-chest checks remain available.
- The Tutorial World Map - Big Chest location check is now sent during the tutorial; item delivery remains paused until normal gameplay begins (Issue #868).
- Consolidated `defeat_random_hidden_area_boss` and `defeat_configured_area_boss` into the canonical `defeat_area_boss` goal. `configured_area_boss: random` now uses Archipelago's standard `Choice` randomization, the old `defeat_configured_area_boss` name remains a safe YAML alias, and all eight boss-to-area mappings are corrected (Issue #872).
- Generated YAML documentation now shows the scalar `configured_area_boss: random` and `starting_kirby_color: random` shorthands and explains how they replace the generated concrete weight mappings (Issue #872).

### Known Limitations
- Progression: The entire game is still only two spheres. This means you can complete almost the entirety of Kirby and the Amazing Mirror without ever having to receive an item, except open the Dimension Mirror. In other words, you can do everything in the game except defeat Dark Mind without ever receiving an item from another player. This is a consequence of the original game design. We have plans to gate your progression in other ways, but they all require coding/hacking in intentional blockers.
- Backwards Compatability: Use newly generated ROM patches for offline custom health initialization; older patches need a same-seed rebuild to embed health bounds. Client reconciliation remains required for authoritative AP ownership. Full gameplay coverage of every custom-health interaction remains pending.
- Kirby Color: random_color_per_room changes Kirby's color but does not update the corresponding UI element colors.
- Localization: Only the North American ROM is supported. All AP notifications are in English.
- Native sprites and animations: Chests still show their original item sprite and collection animation. Statues still show their original ability.
- mGBA: notifications appear as plain text in the **Archipelago Connector** scripting panel, which must be visible. They do not appear over the game image.
- Levers: Visually they'll revert to being "down" after a game reset. This does not affect gameplay.

### Bug Fixes

- Boss checks were mapped incorrectly for the `defeat_configured_area_boss` goal. That's been fixed (Issue #893).
- Adds cutter to the base ability pool to make sure players can cut the drop down platforms. (Issue #894)
- Preserve locally found ability unlocks after reconnecting by requesting the full received-item history from the server (Issue #910).

### Internal Changes
- Added shared health-range validation, full supported-range item-pool coverage, client reconciliation regression tests, and YAML/slot-data contracts without changing payload offsets or item IDs.
- Added pinned, checksum-verified Archipelago generation fuzzing with a strict local launcher, a pull-request/manual CI workflow, and retained failure artifacts (Issue #898).
- `starting_kirby_color` now uses the same standard Archipelago `Choice` literal `random`; the former world-specific `random_color` sentinel has been removed (Issue #872).
- Split Kirby color catalog validation into focused helpers so Flake8 complexity checks remain meaningful without suppressing C901 (Issue #872).

## v0.3.0

### New Features

- Ability gating is now available and under the `Make the game harder` option group. It defaults to be "on". A preset list of abilities is available at the beginning of the game (Beam, Burning, Mini, Stone, and Wheel). This list should be the bare minimum you need to complete the game and get all the currently supported locations. All other abilities are gated by custom AP items (for example, "Sword Ability") (Issues #855, #819).
- Added a new goal mode: `defeat_configured_area_boss` completes the seed after a specific area-boss is defeated (Issue #207).
  - Which area boss is used is determined by the new `configured_area_boss` option. It defaults to Master Hand and Crazy Hand.
- Added four new lever location checks sourced from native lever bits: Moonlight Mansion 2-11, Olive Ocean 6-13, Carrot Castle 5-12, and Radish Ruins 8-12 (Issue #850).
- Added the world map big chest in the tutorial rooms as an AP location check (Issue #845). We plan for the world map as an item to follow later.
  - Because of how we detect the game state, the check will only send AFTER the tutorial is completed and you enter Central Circle for the first time.

### Improvements

- Self-send item popups in BizHawk are now collapsed to one line (`You found your <item>.`) instead of separate send and receive popups (Issue #848).

### Known Limitations

- Localization: Only the North American ROM is supported. All AP notifications are in English.
- Progression: The entire game is still only two spheres. This means you can complete almost the entirety of Kirby and the Amazing Mirror without ever having to receive an item, except open the Dimension Mirror. In other words, you can do everything in the game except defeat Dark Mind without ever receiving an item from another player. This is a consequence of the original game design. We have plans to gate your progression in other ways, but they all require coding/hacking in intentional blockers.
- Small Chests: We know you want the "small" chests implemented. We want them implemented too. We've been working on it for months. We decided getting out what IS working, is more important.
- Sprite Swapping: The animation for getting the original item will play with the original sprite. Statues show the old ability. This is expected. We hope in the future to support "sprite swapping" where we show the sprite for the actual item delivered or ability granted.
- Emulator: Only BizHawk is supported. mGBA may work, but we don't currently test against it.

### Bug Fixes

- Prevent false LocationChecks after death by deferring polling while HP <= 0 (Issue #864).
- In `completely_random` mode, enabled regular ability statues now make a fresh per-touch draw from the configured statue pool instead of repeating their generation-time fallback assignment. The draw honors custom whitelists, the Minny toggle, and live ability unlocks while preserving statue-specific exclusions for no-ability and enemy-source toggles (Issue #875).
- When `ability_randomization_mode` was `completely_random` and `ability_randomization_statues` was enabled, statue abilities were just shuffled, not random (Issue #841).
- Changed map and shard item grants to be only additive, never overwriting what was already in the save. This was a consequence of how I "replayed" certain item grants when a game was opened again (PR #881).
- Fixed hub-switch first-poll baseline suppression so reconnect/disconnect windows do not drop legitimate big-switch location checks (Issue #879).
- Apply `Starting Kirby Color` before the first gameplay palette is created and explicitly refresh the live OBJ palette after reconnects, savestates, or soft resets (Issue #852).

### Internal Changes

- Added seed-specific initial-gate and statue-pool masks, executable native-C policy tests, client compatibility tests, ROM-token tests, and patch-callsite contracts for the statue runtime path.
- Fixed `patch_rom.py` importing on supported Python versions by typing the multiprocessing queue with its actual class rather than subscripting the `multiprocessing.Queue` factory.
- Log files now report the `world_version` and all game options (Issue #861).
- Added file-only telemetry diagnostics for ability statue grants when `ability_randomization_mode` is `shuffled` or `completely_random`, goal target resolution (one-time per session), runtime ability config rewrites (mask/seed snapshot on change), mailbox ACK timeout aggregates, and explicit statue ability-gate suppression reasons (PR #867).
- Expand the allowed versions of requirements.txt (PR #881).
- Reduce generated `kirbyam.apworld` size by excluding `worlds/kirbyam/save_states` and `worlds/kirbyam/kirby_ap_payload/patch_rom.log` from world packaging, and add explicit ignore entries for KirbyAM-local cache/log artifacts (Issue #871).

### Other

- Create a new AI disclosure page.

## v0.2.0

### New Features

- Expanded exploration location check coverage:
  - Hub switches are now implemented as location checks (Issue #481). We expect some bugs with this that we haven't found. Using the connection itself as an AP item is planned for later.
  - The first time you visit each area is now a location check (Issue #606). These nine new location checks give us room to add progression gating items later. This is not a toggleable feature and is separate from Room Sanity.
- Added several player-facing quality-of-life features:
  - `Starting Kirby Color` lets players begin with a chosen Kirby color instead of always starting as Pink, including a random option for surprise runs (Issue #597). See the Known Limitations section.
  - `Start With All Maps` lets players begin with every area map already unlocked for a more guided playthrough (Issue #584).
  - Room names now match Wikirby names, making the game easier to navigate and discuss (Issue #587).
- Added trap items (Issue #81), which are disabled by default. They are controlled by the options `Enable Traps` and `Trap Fill Percentage` (Issue #81):
  - `Health Down Trap`: reduces Kirby's current HP by 2 (but won't kill Kirby).
  - `Life Down Trap`: removes one extra life (if any remain).
  - `Bomb Trap`: sets Kirby's current HP to 0.
  - `Battery Drain Trap`: empties the cell phone battery to 0.
  - `Life Wipeout Trap`: sets Kirby's lives to 0 (Issue #693).
  - Trap item receive notifications are prefixed with "Received trap:" to distinguish them from regular items.
  - Trap pool filtering removes `Life Down Trap` and `Life Wipeout Trap` when `No Extra Lives` is enabled, and removes `Health Down Trap` when one-hit mode is enabled (PR #833).
- Added two new goal modes:
  - `defeat_any_area_boss` completes the seed after the first acknowledged area-boss defeat check (Issue #205).
  - `defeat_random_hidden_area_boss` selects one eligible area boss per seed, stores only an internal hidden boss-defeat key in slot data, and completes the seed when that exact boss is defeated while keeping the target out of normal player-facing output (Issue #206).
- Made changes to non-trap filler items:
  - Added two new filler consumables with tiered healing (`Energy Drink` (HP +2) and `Hunk of Meat` (HP +3), alongside existing `Small Food` (HP +1) which was renamed) (Issues #684, #685, #686).
  - Made filler items no longer equally likely. They each has preset weight loosely based on their likelihood in the original game. Base whole-number weights are Cell Phone Battery 25, Energy Drink 17, 1 Up 15, Max Tomato 15, Small Food 14, Hunk of Meat 9, Invincibility Candy 5. In one-hit mode (`exclude_vitality_counters`), healing filler (`Small Food`, `Energy Drink`, `Hunk of Meat`, `Max Tomato`) is removed and the remaining weights (`Cell Phone Battery`, `1 Up`, `Invincibility Candy`) are preserved proportionally. In no-lives mode, `1 Up` is removed and remaining filler keeps configured relative weights. When both modes are enabled together, only `Cell Phone Battery` and `Invincibility Candy` remain in weighted selection (Issue #688).
- Added the option to randomize Ability Statues with `ability_randomization_statues`. Defaults to off. It controls inclusion only and is only ever `shuffled`. Statues always grant an ability (ignoring `ability_randomization_no_ability_weight` and `ability_randomization_passive_enemies`, while respecting `ability_randomization_minny` just like enemy randomization) (Issue #209). See the Known Limitations section.

### Improvements

- Bump Archipelago Minimum version to 0.6.7 (PR #843).
- Enemy Ability Shuffle now covers more enemies, spreads allowed abilities more evenly across enemies when possible while still respecting settings that force no ability, and keeps `Ability Randomization: Minny` off by default unless players opt in (Issues #420, #583).
- DeathLink got flavor text (Issue #409).
- Spoiler output and generation logs now show shuffled enemy ability assignments, making seeds easier to review (Issue #586). This includes ability statues (Issue #804). For statues, see the Known Limitations section.

### Known Limitations
- Localization: Only the North American ROM is supported. All AP notifications are in English.
- Progression: The entire game is still only two spheres. This means you can complete almost the entirety of Kirby and the Amazing Mirror without ever having to receive an item, except open the Dimension Mirror. In other words, you can do everything in the game except defeat Dark Mind without ever receiving an item from another player. This is a consequence of the original game design. We have plans to gate your progression in other ways, but they all require coding/hacking in intentional blockers.
- Small Chests: We know you want the "small" chests implemented. We want them implemented too. We've been working on it for two months. We decided getting out what IS working, was more important.
- Major (big) chests: The animation for getting the original item will play with the original sprite. This is expected. We hope in the future to support "sprite swapping" where we show the sprite for the actual item delivered or a custom sprite if it's not a KirbyAM item.
- When `ability_randomization_mode` is set to `completely_random` ability statues are actually shuffled. This is known and incorrect, but we decided to release anyway and fix it later. You can always play with this feature off.
- `Starting Kirby Color`: The color is not immediately applied. It might take a room transition or a hit for it to apply, but it will eventually apply. Hopefully we can improve this later, but the feature does work.
### Bug Fixes

- Fixed an issue where having other custom GBA worlds installed with KirbyAM at the same time caused issues (Issue #742).
- Enemy Ability Randomization: Completely random now rerolls abilities per swallow, not per room (Issue #420).
- Warp rooms that were missing Room Sanity checks now have them (Issue #605).
- Fixed delivery synchronization and logging issues that could skip items when client and game counters drifted, while ensuring debug-only delivery diagnostics still go to the log file even when hidden from the live client output (Issue #601).
- Fixed vitality counter replays caused by transitions or resets, and prevented vitality counters from lingering in `One-Hit Mode` when that mode excludes them (Issue #571).
- Fixed extra logging showing up in the live client when they should have remained file-only (Issue #582).

### Internal Changes

- Tracker support now gives trackers a clearer view of room progress, location progress, and unique-item progress, and KirbyAM seed options are exposed in `slot_data` so tracker surfaces can render the exact seed configuration from slot data without inferring from partial fields, including newly added option surfaces such as `start_with_all_maps` (Issue #114).
- Reduce duplicate CI runs on feature branches by limiting push-triggered workflow execution to `main` for native static analysis and other PR-validated checks (`scan-build`, `ctest`, `type check`, `build`, and `analyze-modified-files`), while keeping `pull_request` validation behavior unchanged.
- Improve `worlds/kirbyam/build.py` usability for non-author machines by prompting for missing required patch inputs in interactive runs (including missing `--rom` when `--source-type arg` is selected), adding `--source-type file` fallback guidance when `rom_path.tmp` is invalid, and introducing `--non-interactive` fail-fast behavior for automation/CI (Issue #607).
- Move unswallowable enemy exclusion policy from a static runtime list into `data/enemies.json` source metadata (`can_be_swallowed`) and represent the currently configured non-swallowable enemies there: `GLUNK`, `JACK`, and `SQUISHY` (Issue #570).
- Completely random swallow abilities now emit file-only diagnostics describing what Kirby got from the latest swallow event, and the old `Enable Debug Logging` / `enable_debug_logging` toggle has been removed so those diagnostics are no longer part of the player-facing option surface.
- Simplified repeated client location-map initialization paths in `worlds/kirbyam/client.py`, added focused regression coverage for the refactor, and added concise runtime developer docs for location polling and item/native-reward interception flows (Issue #811).
- Room-owned location membership is now derived from `locations.json` parent-region metadata so `rooms.json` no longer acts as a second source of truth (Issue #840).
- Numerous improvements to logic mapping.

## v0.1.2

### New Features

- `Ability Randomization: Minny` lets players keep Minny at vanilla behavior even when other enemy ability sources are randomized (Issue #572).

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

- First public playable release of Kirby & The Amazing Mirror for Archipelago: seeds can be generated, patched, connected through BizHawk, and played through with working item delivery, location checks, and goal completion.
- Mirror Shards, maps, Vitality, Sound Player, boss rewards, major chests, and vitality chests are fully integrated into the randomizer so the core Amazing Mirror progression loop is part of normal Archipelago play.
- Optional `Room Sanity` adds room-discovery checks throughout the game for players who want denser exploration and more location coverage.
- `One-Hit Mode`, `No Extra Lives`, and `DeathLink` add extra challenge settings for harsher playthroughs and multiworld punishment runs.
- Enemy copy-ability randomization is available for players who want enemy abilities shuffled or fully randomized, with additional controls over bosses, minibosses, and non-ability enemies.
- Filler and utility rewards are more interesting in moment-to-moment play, with working consumable effects, clearer sent/received item notifications, and cleaner player-facing item/location names.
- Standard Archipelago item/location options and stable KirbyAM item groups are available for filters, YAML setup, hints, plando, and other normal AP workflows.

### Bug Fixes

- Harden the BizHawk client and ROM payload against pre-public integration regressions across mailbox delivery, reconnect recovery, goal reporting, gameplay-state gating, and title-demo suppression so item delivery and location checks remain stable in normal play (Issues #269, #419, #437, #457, #477, #489).
- Fix shard and boss progression handling by preserving native shard state, introducing AP-owned shard authority, and protecting post-boss cutscene/transition behavior from white-screen and premature-ownership regressions (Issues #393, #478, #505).
- Fix release-blocking content and integration bugs found during pre-public work, including missing vitality chest region binding, host upload/auth registration problems, handler detection issues, release packaging problems, and startup-state corruption in the ROM hook path (Issues #428 and related pre-public regressions).

### Internal Changes

- Align the public-release contract by normalizing ability-randomization naming/defaults, removing legacy compatibility paths and aliases, and cleaning up pre-public template output so the shipped option surface matches current behavior.
- Expand protocol, slot-data, patching, reconnect-chaos, release-metadata, snapshot, and negative-path test coverage across the world, client, and payload pipeline to support the first public version.
- Establish the pre-public build and release workflow baseline, including ROM patch rebuild smoke coverage, release integrity checks, and maintainer validation/documentation needed for the `v0.1.0` release line.
