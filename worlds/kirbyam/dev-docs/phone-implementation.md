# Phone a Friend implementation milestone

Status: **in progress, not enabled for generated seeds**. AI-assisted work, 2026-11-11. This implements the native permission and receipt foundation from the [route audit](phone-a-friend-traversal-audit.md). It does not close #490 or certify a helper traversal.

## Implemented boundary

- The common USA R-call entry at `0x08056C2C` is wrapped before native animation, battery or call-state writes. The installer verifies all eight displaced bytes and the Thumb wrapper replays that prologue for permitted calls.
- L return to Central Circle uses the separate native entry at `0x08056E40`, which is not patched. Native input, battery, room, ability and active-call restrictions are not replaced.
- Only a new call initiated by the local Kirby in an authenticated single-player Adventure is gated. Answering another Kirby's call, already-running calls, naturally present CPU Kirbys and native linked play are left native. This is not a ban on companions.
- Rooms 803–805 have a local tutorial exception. This does not award ownership and does not assume the tutorial is skipped. A cold-start replay now completes the retail tutorial and confirms the gate resumes afterward; the exception never grants ownership.
- The reserved Phone item ID is `3860501`. It is not yet in the production catalog or item pool. No generation option, slot capability or graph route is enabled. A generation regression test protects this boundary.
- Native ownership is saved alongside Copy Room in the existing authenticated per-file record. Copy Room retains bit 0 and its protocol-v2 snapshot; Phone uses bit 1. Grants OR into the record, so either grant order preserves the other item. The existing seed identity, selected/loaded-file, live-task, epoch, save retry and three-file checks remain authoritative.
- The client checks ROM/slot pairing on every watcher poll, before any watcher writes. An enabled Phone ROM requires a compatible slot, and a compatible slot requires the exact enabled ROM configuration. Unknown Phone versions and invalid enable words are rejected. Marker-free legacy ROMs and the shipping disabled configuration remain compatible with capability-free slots.
- The client uses a separate grant-only Phone request queue. It requires complete server history, explicit compatible slot capability, exact ROM marker/config, matching seed identity and two stable native context reads. Guarded writes publish the epoch last. Empty histories, reconnects and zero commands cannot revoke a saved grant. The ordinary mailbox cannot independently grant ownership.

## ABI

| Surface | Address / format |
| --- | --- |
| ROM configuration | `0x0900FFC8`: `APPHN01\0`, then a little-endian enabled word; shipping value **0** |
| Copy Room marker | Unchanged at `0x0900FFD4`, `APCPY02\0` |
| Native saved record | WORLD words 22–25: existing seed identity; word 26: `0x43500000` plus Copy bit 0 / Phone bit 1 |
| Phone snapshot | `0x0203B170`: epoch, native slot, owned boolean, cookie `0x50484E31` |
| Phone request | `0x0203B180`: request epoch, grant boolean, acknowledged epoch, acknowledged ownership |
| Copy Room transport | Unchanged context at `0x0203B13C` and request at `0x0203B160` |

The extension linker bound now ends before `0x0900FFC8`. No native save descriptor is resized and no additional WORLD words are claimed. A legacy ROM predating the Phone ownership bit is not a supported rollback target for an experimental Phone-enabled save.

## Validation so far

The ARM payload and BSDIFF patch were rebuilt locally from the verified USA base (SHA-1 `274b102b6d940f46861a92b4e65f89a51815c12c`). Only the patch is distributable, never the source ROM.

An optional ROM-free mGBA regression freshly builds the shipping ARM sources and executes the actual patched Thumb entry and wrapper. All 24 combinations pass: allowed, denied and noncanonical nonzero predicate returns; four register patterns; and two aligned stacks. The allowed path matches a separately executed native displaced prologue, while the denied path preserves the checked arguments, callee-saved registers, stack and return. A hostile ABI-conforming predicate stand-in stresses caller-saved clobbers. This is machine-code ABI coverage, not gameplay acceptance or a test of the C gate predicate. The test explicitly skips without the documented ARM toolchain and mGBA development prefix.

Host tests execute the shipping C against native-file save/load spies: both grant orders, all three files, save failure/retry, reload, stale requests, repeat/zero grants, cross-seed invalidation, tutorial-local permission, answering calls, CPU identity and linked-play exclusion. Protocol tests cover complete-history grants/precollection, snapshot/session races, mismatched ROM identity, disabled capability, malformed context and no-revoke behavior. These tests are not emulator or traversal witnesses.

A qualified native fixture places the local Kirby in room 147 and the three CPU Kirbys in room 148. It changes only initial rooms/positions, a synthetic seed identity, and the experimental enabled flag before boot. With no runtime state injection:

- Locked R held for 60 frames leaves battery at 3, caller at 255 and the local idle state unchanged.
- The real Phone protocol grants ownership; Copy Room remains unowned.
- The same unlocked R hold consumes one battery and enters the native call state. After 600 additional frames all three CPU Kirbys have arrived in room 147, and native health recovery occurred.
- Three repeated locked R holds do not consume battery. L reaches settled room-801 control both before and after Phone receipt; a subsequent 30-frame right input moves Kirby normally.

This proves a permission/receipt interaction in a configured normal-ability fixture. It does **not** prove a switch hold, Bomb Block attack, Heave-Ho displacement, collectible access, or a reproducible helper route.

The [sanitized native ledger](phone-native-gate-evidence.json) also contains a complete retail-start tutorial replay and a disabled-gate control. Both use the original initial rooms/positions, a blank native save and synthetic seed identity. The enabled replay has no Phone receipt or runtime writes. It traverses 803, summons the three CPU Kirbys in 804 (battery 3 to 2), reaches the tutorial chest/exit in 805 and enters Central Circle with normal control and ownership still zero. This is an exploratory playthrough, including ordinary damage and a native death/retry, not an optimized route or no-death claim.

Both tutorial runs replay the same 245 input segments, 31,422 frames. Recorded room, position, health, ability, AI state, battery, function state and CPU rooms match through frame 30,992. At frame 31,052, after a CPU has naturally departed to room 101, the enabled/unowned run remains in its native floating state with battery 2. The disabled control enters the native R-call state and spends one battery; the CPU returns and native healing follows. This isolates post-tutorial gate restoration from ordinary native call ineligibility.

## Carried-ability calls and reset contract

A [dry carried-Cutter matrix](phone-cutter-call-evidence.json) starts from the genuine post-tutorial save without Phone. Complete initial history grants East Hub, Moonlight Key and Cutter permission, and the human genuinely acquires finite Cutter in native room 143. Locked R leaves battery 3, caller 255 and idle control unchanged. The real guarded Phone queue grant then establishes ownership; R spends one battery and brings the helpers while retaining Cutter. Separate L controls before and after ownership both return to settled Central Circle with Cutter retained and subsequent movement working. This does not certify underwater calls or the whole ability matrix.

A separately [observed underwater Normal matrix](phone-water-call-evidence.json) follows ordinary inputs through 801 → 190 → 140 → 108, including native air-puff Bomb Block openings. Actual `unk58 & 0x02` establishes the wet state. All 60 locked-R samples stay underwater with battery 3 and caller 255. After the real guarded ownership grant, R enters the native call while underwater and consumes one battery; the helpers eventually reach 108. The primary R run has HP 1 before the call and HP 3 by its settled checkpoint; the precise recovery mechanism is not established. Separate L controls begin underwater both unowned and owned, return to settled Central Circle with the expected ownership/battery state, and permit subsequent movement. The approach takes native damage down to HP 1, so this is neither a no-damage route nor a health-option test. It covers one Normal-ability water compartment, not all layouts or abilities.

Native source invokes the identified exhausted-lives fallen-help initializer only in the multiplayer branch (`kirby.c:10709–10715` at the pinned source revision). The single-player path retries/respawns instead. Linked play is excluded from authenticated Phone gating. This narrows the applicable matrix; it is not a runtime multiplayer test.

The [source/reset audit](phone-reset-source-evidence.json) establishes a bounded reset prefix: successfully persist Phone in the same authenticated native file, cold-restart/load single-player Adventure after the tutorial, then use the separately accepted controller route. Native startup recreates all four Kirbys in room 801 with Normal, three batteries, full configured health capacity and fresh CPU tasks. The health patch initializes capacity from the configured minimum plus clamped saved Vitality; it does not reuse injured runtime HP.

Startup clears SESSION state and fresh room allocation clears ROOM state. Authorized-ROM inspection identifies the finite native-143 Sir Kibble at `0x088B7C0C` as ROOM scope 0, flag 8, so earlier consumption does not survive that restart. All 50 static objects in 143/145/146 have ROOM or SESSION scope, not WORLD. Room 146's helper script branches on ROOM slot 15, then requests Normal and performs navigation/timed actions. Its parameter 180 is not a guarantee of 180 elapsed frames or successful inhaling.

Saved WORLD progress and AI progression remain intact. These initialization/spawn-eligibility invariants remove the need to assume old injury, equipment, battery use or stale CPU tasks survive reload; they do not guarantee future RNG timing, successful acquisition or universal helper cooperation. Phone persistence must be successfully saved, not merely acknowledged by the grant queue. L alone is not this full reload/reset procedure.

## Battery exhaustion and offline lifecycle

The [native lifecycle ledger](phone-battery-lifecycle-evidence.json) extends the genuine dry-Cutter approach with three eligible calls in native rooms 143, 801 and 190. The calls naturally consume batteries from 3 to 2 to 1 to 0. L still returns from 190 to Central Circle at zero battery, and subsequent movement works. With all three CPUs still in 190, a further 60-frame R hold in Central Circle leaves battery 0, caller 255 and idle control at the recorded checkpoint; ownership remains set.

A separate eight-frame R press enters native startup. Releasing R for one frame and holding L for 120 does not cancel that pending call: one battery is consumed and all helpers reach 143. A later L still returns to Central Circle with movement restored. A one-frame exploratory press did not enter a call; these samples do not establish a minimum press duration or general interruption behavior.

The battery-exhaustion run’s persisted native file is then cold-loaded without any client reads, receipts or writes. The same synthetic ROM identity retains Phone ownership and restarts all four Kirbys as Normal in Central Circle with three batteries and HP 6. A separate cold load of that exact save under a different synthetic ROM identity invalidates the Phone bit and still permits ordinary movement. This exercises file 0 only and uses checkpoint observations, not a per-frame trace. The approach has ability gating ON, Area Keys ON, health 6–10 and fixed finite Cutter, and takes ordinary damage before the calls. It does not prove broader health/source combinations, a helper route, cross-file gameplay or the BizHawk Lua transport.

The client also rejects in-place changes to Phone, Copy Room, shared-save capability or starting Phone ownership while either emulator read is pending. The fence compares both scalar values and types, preserving the distinction between boolean and integer values. Regression coverage includes reconnects, fresh guards after a failed write and eight ability-gating/Area-Keys/RoomSanity generation combinations. All eight still exclude Phone from the catalog, pool, precollection and slot capability.

## Native three-file ownership and menu controls

The [three-file ledger](phone-three-file-evidence.json) uses ordinary title and file-selection inputs against isolated native saves. File 0 receives Phone then Copy Room, and file 1 receives Copy Room then Phone. Both retain both bits. File 2 remains unowned until its own Phone-only grant, producing final ownership bits `3, 3, 2`. All six native WORLD checksums validate and both copies agree on identity/ownership. Initial blank-save startup initializes all three files; subsequent matrix steps alter only the selected file's WORLD range.

Independent offline cold loads of each file retain those bits with no client writes and byte-identical whole saves. A separate foreign-identity load clears both bits in file 1 while the file-0 and file-2 ranges remain byte-for-byte unchanged. Three menu attempts with complete synthetic Phone/Copy histories are also rejected by both production ownership synchronizers: the file selector, file-0 mode menu and file-2 mode menu after Back/navigation. The context remains inactive and the save does not change. Menu preview WORLD contents are not treated as gameplay ownership evidence.

Four additional controls use persisted ownership without client writes. Unowned file 2 rejects a 60-frame R hold without spending battery. Owned files 0, 1 and 2 enter the native call and spend one battery; L subsequently returns each case to Central Circle with retained ownership and movement. The helpers remain in Central Circle at the 600-frame post-R checkpoints, so these runs do not certify arrival or traversal. The fixture has no Mustard Key receipt.

A separate matched file-2 experiment uses the same ROM, persisted Phone save and controller inputs, changing only production Area Key configuration from zero to precollected Mustard bit 16. Both calls consume one battery, but all three helpers arrive in 316 at the 600- and 1800-frame post-R checkpoints only with the key. The keyed run makes one ordinary four-byte configuration write through the production client, separate from the guarded ownership queues. L returns the player to Central Circle in both cases. The patched response uses the explicit room-transition gate, which also applies to CPUs: native 801 is area 0 and 316 is area 3, requiring Mustard bit 16. This isolates the missing key in this fixture; it does not certify a helper attack or target traversal.

These are relocated native-316 fixtures with CPUs initially in 801, fixed sources, Normal player ability, HP 6, Area Keys ON and ability gating OFF. Grants use complete synthetic histories, production ROM/health validation and the actual ownership queues. No live server, full watcher, native BizHawk transport or retail tutorial reset is claimed. Observations are checkpoints. Only ten guarded four-byte queue writes occur across the grant matrix; no direct Phone/Copy ownership, file index, pose or equipment field is injected.

The shared Copy Room synchronizer now mirrors Phone's scalar authorization fence. Copy capability, shared-save version and starting ownership must retain their presence, value and type across either awaited read. Twelve unsafe-grant regressions failed before the fix; coverage now also checks already-saved ownership responses at both read boundaries. Both synchronizers also distinguish absent optional fields from explicit null values: sixteen mutation regressions failed before that refinement, while four unchanged-absence controls remain valid. Both native grant-order runs were replayed after the final fixes and produced byte-identical runtime traces and saves.

## Helper-route acceptance

A [room-146 Heave-Ho investigation](phone-heave-ho-acceptance.md) records repeated configured successes, native ability disposal, and save/reload refill. Later source-informed retries now cross the block approach and physically collect Chalk after naturally acquired Missile and Fire/Fire/Beam. The Missile input schedule also cold-repeats unchanged. Native chest flag/event evidence supports correcting Chalk to Goal 2 upper-left and its return endpoint to Room 18 bottom-right; no Phone condition is added. The unowned retry schedule ends on the earlier approach and does not isolate the block. A separately qualified actual Central Circle approach now cold-repeats and also succeeds in one production-format ability-gating-ON variant, with genuine finite Cutter pickup and real permission. Its first prefix starts at HP 6 and takes damage to HP 2. A revised complete no-health-loss route now independently cold-repeats at HP 6 and succeeds once with production minimum = maximum = 1, native HP-1 initialization and no HP injection. Both retain the post-tutorial Phone-owned native save and fixed finite Cutter conditions. Arbitrary source assignments, other helper routes and general reliability remain unresolved. No Phone traversal witness is installed.

## Carrot 16 helper-assisted chest

The [sanitized Carrot ledger](phone-carrot-helper-evidence.json) now records a complete helper-assisted Yellow chest procedure. Qualified startup places the player beside native 730's original `(27,48)` door, and ordinary Up input enters 733 at `(40,120.99609375)`. Retail geometry and sources are unchanged. The production Phone queue grant and precollected Carrot Key configuration are the only client writes; the player remains Normal.

The player calls from below the barrier, then stands idle while the helpers arrive and the upper Bomb Block opens at frame 3053. This clears the lower corridor. Normal Kirby walks through, opens the lower Bomb Block with an air puff at frame 3546, flies around its cleared right wall and collects the physical chest at frame 3902. Native flag 80, event `0x088D3DD0` and a locally captured production-client `LocationChecks` for `3960501` confirm collection. Subsequent movement confirms control.

Two HP-6 cold runs have byte-identical traces and saves. One native HP-1 run uses the same schedule, with every observed field other than current/max HP matching. All 1,742 audited frames per run preserve initial health and Normal ability. Two matched HP-6 controls either omit Phone receipt or replace only the 60-frame R window with idle; neither opens either Bomb Block, summons the helpers or collects the chest. The unowned native entry differs by one frame, so the controls share controller schedules rather than identical native timing.

This remains a bounded witness: native file 0, Area Keys ON, ability gating OFF, fixed retail sources, three starting batteries with one spent, synthetic history and native mGBA. It is not a full progression-safe approach, a chest-to-exit proof, a live server check or BizHawk acceptance. The successful helpers are Bomb/Normal/Normal after arrival. Source describes a slide script but does not normalize equipment; Sleep, UFO, Mini and some other states divert from sliding. Helper animation/input/contact identity was not recorded, so the exact attacker or executed instruction is not directly measured. Arbitrary helper/source reliability remains open. Independent solo UFO evidence remains separate, and no traversal binding or Phone activation is added.

## Independent Mustard 11 solo witnesses

The [sanitized solo ledger](phone-mustard-solo-evidence.json) records two separate targets reached without Phone: the small chest in native 322 and the ordinary exit to native 315. Both use the actual doorway from native 316. Startup is deliberately relocated to 316 with a blank native file, synthetic identity and experimental Phone enabled but unowned; the three CPU Kirbys remain in Central Circle. Retail geometry and source assignments are unchanged. These are bounded room-entry witnesses, not a full progression-safe Central Circle approach.

Normal Kirby can slide open the floor Bomb Block, take the lower passage, fly to the chest and open it with Up. Native chest flag 42 and event `0x088C4F24` confirm collection, followed by idle control and movement. One schedule passes at HP 6 twice and native HP 1 once with ability gating OFF. A revised lower-flight schedule passes at HP 6 once and HP 1 twice with gating ON. Area Keys remain ON. Per-frame audits preserve the initial health, Normal player ability, unowned Phone, battery 3, idle caller and all three off-room CPUs. Their abilities are not assumed to remain Normal.

The schedules are not interchangeable: recorded cross-setting trials hit Chip (`0x088C4FFC`) and stop at HP 0 before collection. Chip's source uses targeting and random decisions, but the cause of the difference is not established. The successes do not establish arbitrary enemy timing, shuffled-source reliability or one universal controller replay.

A separate ordinary-exit schedule passes with HP 6/gating OFF, HP 1/gating OFF and HP 1/gating ON, reaching 315 with subsequent movement and no health loss in the audited gameplay frames. It is not a continuous chest-then-exit proof. None of these runs uses R, receives Phone or writes runtime memory. They do not activate or isolate the right-hand large block at `(864,32)`, certify the room-315 alternatives, or supply a Phone-assisted traversal witness. The existing chest and ordinary-exit bindings remain unchanged.

## Static object inventory

The [Phone-relevant inventory](phone-static-object-inventory.json) scans all 287 static object lists (3,482 templates), separating spawn-table namespaces. All static records use table 1. The 35 small-switch positions/offsets were cross-checked against the existing switch inventory. It also records 22 CPU triggers, seven ordinary `0x79` blocks, and three large blocks:

- `0x7D`: native 146 / Moonlight 18, `(160,128)`, ROM offset `0x8BBB90`.
- `0x88`: native 315 / Mustard 12, `(160,32)`, ROM offset `0x8C4628`.
- `0x7E`: native 322 / Mustard 11, `(864,32)`, ROM offset `0x8C4E94`. This is an additional review target beyond the original prose audit.

There is no static `0x89` instance. All 37 static ObjectSpawner low-byte targets were checked and do not create these blocks or small switches. Arbitrary runtime constructors remain outside this census. Counts and source eligibility do not certify helper reliability, a mandatory Phone dependency or an AP route. The census used native source commit `7d969fbce14fdc838d2c1ea01389717fb96c3189`; the original audit's separately pinned source references remain historical provenance.

A native mGBA bridge probe also checks the new configuration read at System Bus address `0x0900FFC8` against the unmodified 16 MiB USA ROM and the pre-Phone patch from `7a198f4ff09a0b3a279dc61bc420bc57a0d62c10`. Both return 12 marker-free bytes. The [sanitized probe results](phone-legacy-bus-evidence.json) record hashes and lengths, not ROM bytes. This confirms native-core bus mapping, not the end-to-end BizHawk Lua transport. A [bounded read-only stock-transport harness](phone-bizhawk-smoke.md) is now prepared, with ROM identity checks, repeated exact reads, timeouts and exclusive sanitized output. Its 31 contract tests use stubs; no native BizHawk run is claimed. The guide requires verifying the dedicated emulator process and listener, and restarting Lua after each ROM load because the connector caches its ROM hash.

Independent review found no blocking defect in this disabled-production milestone or the reverse-pairing follow-up. The broader native acceptance gaps below remain open.

## Remaining work before activation

1. Complete the R/L runtime matrix beyond the bounded normal, underwater, carried-ability, battery, call-start and three-file cases above, including other restricted states and interruption behavior. Zero-battery L/R and same-/cross-identity offline cold reload are now observed in the bounded file-0 scenario above; the multiplayer-only fallen-help initializer is outside the single-player gate. The ROM-free machine-level wrapper regression above is complete.
2. Extend the completed tutorial/control replay to the supported generation-option matrix; retain the original initial rooms and positions.
3. Extend the static inventory to other runtime constructors, then certify each helper route with exact caller/CPU positions, arrival reliability, battery assumptions, target activation and final traversal or collection. Include the Carrot-16 Bomb Block candidate.
4. Keep independent solo witnesses. Shared #1052 ranged/Phone solutions must be OR alternatives in one target's witness list; independent `add_rule` calls would incorrectly AND the requirements. No shared traversal bindings are changed in this milestone.
5. Resolve helper ability/source/randomization interactions before crediting an attack. Phone ownership is not a provider for an arbitrary CPU copy ability.
6. Complete a supported BizHawk end-to-end smoke test of the legacy-ROM bus probe. Host tests cover both pairing directions, malformed configuration, configuration changes between polls and refusal before watcher side effects; the mGBA bridge probe above covers native bus mapping only.
7. Add the progression classification, balanced item-pool insertion, generation option, versioned ROM token/slot-data pairing, source combinations, placement and reachability tests only after the relevant routes are sound. Keep activation zero until then.

The initial source audit and its uncertainty remain applicable. Room prose and source eligibility are not CPU reliability evidence.
