# Phone a Friend implementation milestone

Status: **in progress, not enabled for generated seeds**. AI-assisted work, 2026-11-10. This implements the native permission and receipt foundation from the [route audit](phone-a-friend-traversal-audit.md). It does not close #490 or certify a helper traversal.

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

## Helper-route acceptance

A [room-146 Heave-Ho investigation](phone-heave-ho-acceptance.md) now records repeated configured successes, a matched unowned negative control, native ability disposal, and save/reload refill. Natural-ability contrasts still fail despite eventual normalization, so positioning reliability and a real-start approach remain unresolved. No Phone traversal witness is installed.

## Static object inventory

The [Phone-relevant inventory](phone-static-object-inventory.json) scans all 287 static object lists (3,482 templates), separating spawn-table namespaces. All static records use table 1. The 35 small-switch positions/offsets were cross-checked against the existing switch inventory. It also records 22 CPU triggers, seven ordinary `0x79` blocks, and three large blocks:

- `0x7D`: native 146 / Moonlight 18, `(160,128)`, ROM offset `0x8BBB90`.
- `0x88`: native 315 / Mustard 12, `(160,32)`, ROM offset `0x8C4628`.
- `0x7E`: native 322 / Mustard 11, `(864,32)`, ROM offset `0x8C4E94`. This is an additional review target beyond the original prose audit.

There is no static `0x89` instance. All 37 static ObjectSpawner low-byte targets were checked and do not create these blocks or small switches. Arbitrary runtime constructors remain outside this census. Counts and source eligibility do not certify helper reliability, a mandatory Phone dependency or an AP route. The census used native source commit `7d969fbce14fdc838d2c1ea01389717fb96c3189`; the original audit's separately pinned source references remain historical provenance.

A native mGBA bridge probe also checks the new configuration read at System Bus address `0x0900FFC8` against the unmodified 16 MiB USA ROM and the pre-Phone patch from `7a198f4ff09a0b3a279dc61bc420bc57a0d62c10`. Both return 12 marker-free bytes. The [sanitized probe results](phone-legacy-bus-evidence.json) record hashes and lengths, not ROM bytes. This confirms native-core bus mapping, not the end-to-end BizHawk Lua transport.

Independent review found no blocking defect in this disabled-production milestone or the reverse-pairing follow-up. The broader native acceptance gaps below remain open.

## Remaining work before activation

1. Complete the R/L runtime matrix: normal/underwater/ability-specific states, full/zero battery, repeated/cancelled/interrupted calls, fallen-Kirby calls, actual reload/offline/cross-file lifecycle. The ROM-free machine-level wrapper regression above is complete.
2. Extend the completed tutorial/control replay to the supported generation-option matrix; retain the original initial rooms and positions.
3. Extend the static inventory to other runtime constructors, then certify each helper route with exact caller/CPU positions, arrival reliability, battery assumptions, target activation and final traversal or collection. Include the Carrot-16 Bomb Block candidate.
4. Keep independent solo witnesses. Shared #1052 ranged/Phone solutions must be OR alternatives in one target's witness list; independent `add_rule` calls would incorrectly AND the requirements. No shared traversal bindings are changed in this milestone.
5. Resolve helper ability/source/randomization interactions before crediting an attack. Phone ownership is not a provider for an arbitrary CPU copy ability.
6. Complete a supported BizHawk end-to-end smoke test of the legacy-ROM bus probe. Host tests cover both pairing directions, malformed configuration, configuration changes between polls and refusal before watcher side effects; the mGBA bridge probe above covers native bus mapping only.
7. Add the progression classification, balanced item-pool insertion, generation option, versioned ROM token/slot-data pairing, source combinations, placement and reachability tests only after the relevant routes are sound. Keep activation zero until then.

The initial source audit and its uncertainty remain applicable. Room prose and source eligibility are not CPU reliability evidence.
