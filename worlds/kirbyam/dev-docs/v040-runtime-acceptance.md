# v0.4.0 combined runtime acceptance

This is a test plan, not a record of passing gameplay. The cloud suite and dummy
ROM smoke cannot replace these checks. PR review status does not waive these
runtime gates; no merge or release is implied by this checklist.

## Historical Pi evidence versus pending gameplay

The following records an earlier build, not the current consolidated candidate.
On 2026-10-09 the owner-provided USA ROM was verified on the ARM64 Pi against
SHA-1 `274b102b6d940f46861a92b4e65f89a51815c12c`. The combined #930/#931/#934/
#935/#936 payload was rebuilt, retail hook sites validated, all 65 chest records
regenerated with zero ambiguity, and APWorld packaging checked. The rebuilt
base-patch SHA-256 is
`037b7704b1a0404d3b6bcee7a29c8458b087f7c20b3fcf80d0f70a3a9760e4e4`.
A genuine seed was generated after #938's compartment correction, and its
embedded base patch matched. A loopback-only server/client handshake reached
slot 1 with 115 pending checks; no location checks were simulated, no emulator
was used, and the server stopped afterward.

The combined automated suite passed 982 tests; five further research checks
covered selected real-ROM fields and a controlled host harness for native door
C. These results establish build, data and protocol behavior, **not gameplay**.
The committed base patch was not replaced. The final release candidate must
still be frozen and rebuilt from its exact reviewed source before acceptance.

BizHawk chest collection, item grants, lever behavior, ability gating, health,
save/reload, reconnect and full-session acceptance remain **UNRUN**. That earlier build kept Music Sheet #6 dormant. Current main activates all 65
physical checks; the final integrated candidate must preserve that baseline.
Pi generation/hosting and emulator acceptance are separate evidence.
The BLOCKED example later in this document refers to gameplay acceptance and
must not be interpreted as a claim that Pi real-ROM rebuilding is unrun.

## Freeze the build and inputs

- Record the exact combined source commit, each included PR head, Python/toolchain
  versions, generated APWorld SHA-256, payload SHA-256 and base-patch SHA-256.
- Use the maintainer's clean, lawfully obtained USA ROM in its existing authorized
  environment. Expected base MD5 is `DF5EFE075B35859529EBF82A4D824458`; the chest
  enumerator also checks SHA-1 `274b102b6d940f46861a92b4e65f89a51815c12c`.
- Rebuild the shared base patch from that ROM and the final combined payload.
  Do not substitute the dummy-ROM smoke output, distribute the ROM, or overwrite
  the original. Recheck generated artifacts against the frozen source commit.
- Generate fresh seeds with the rebuilt APWorld and verify that the running
  client/package match. The current manifest version alone does not distinguish
  these development builds; record the commit and artifact hashes.
- Start a new save or a reproducibly prepared save for this exact patched build.
  Historical savestates are research evidence, not automatic proof that old
  callback pointers/configuration remain valid with a rebuilt payload.
- Record BizHawk version, platform, seed, player/slot, options and whether the
  server connection is live. Preserve client logs and narrow screenshots/watch
  values; never attach a ROM to a result.

## Required cases

### Ordinary chest rewards: `v040-chest-ordinary-{type}`

Run one mapped source for each original 1-UP, Candy, Tomato, Meat, Energy Drink
and Cherry reward. Open it while assigned a distinguishable remote AP item.
The exact source must report its one AP check, retain chest persistence, and
avoid the native consumable grant. Deliver the AP item and verify its normal
mailbox award. Revisit the room and reconnect: no extra reward or false check.
Also verify the room mechanism/counter does not receive an extra increment from
the temporary `0x63` reward used to suppress the native bonus.

### Fixed collections: `v040-chest-fixed-{spray|sheet}`

This case applies only when collection itemization (#936) is included. The
#931/#935 stack alone preserves native paint and sheet rewards.

Open active exact-source Spray Paint and Music Sheet chests before receiving
those items: the native ownership bit must remain unchanged. Receive each AP
item, then replay/reconnect: exactly its bit is added and existing ownership is
preserved. Sheets never grant Sound Player (bit 0). Check the independent Sound
Player chest and its AP item too. Preserve normal collection visuals and native
room-counter behavior.

The final main-integrated candidate preserves all 65 physical sources and
itemizes all 24 fixed collections. Verify Candy Spray Paint #6 only through its
9-01 compartment and Music Sheet #6 through upper Carrot 5-13.

### Carrot topology investigation: `v040-carrot-{approach|switch|music}`

These optional route investigations establish local traversal facts; they are
not a prerequisite for the owner-approved v0.4 physical-location baseline.
Use the combined build with #936's fixed collectibles and #938's corrected lower
1-UP compartment, and record all included heads and artifact hashes.

1. Record normal Kirby, current native room, ability/unlock settings and partner
   positions. Use no partner holding or phone assistance for the single-player
   baseline. Do not use a modified-position state as proof of the approach route.
2. Trace an observed approach through native 719 to tile (14, 3); press Up and
   verify entry to 720 at spawn (119, 8). Record movement actions and any required
   ability. Repeat with the purported required ability unavailable to distinguish
   necessity from convenience. Current AP identities are 5-07 and 5-14.
3. In 720, trace the actual route from the right-hand spawn toward the switch at
   pixel (600, 96) and sliding door at (520, 128). The eight OBJ_DESTROYABLE_ROCK_BLOCK
   records at x1256..1368, y120 use a crumble-on-contact path; do not assume an
   ability-breaking requirement from their name. Record whether they crumble,
   can be crossed/floated over, and whether any alternate route exists.
4. Measure the last switch contact/activation, room-state slot 1 changes and live
   door bounds. Template+0x18 = 30 initializes the native release counter to 32,
   but this is not a 32-frame passability claim: task scheduling, activation
   renewal and opening/closing animation determine the available passage.
   Record successful and failed normal walk/run/jump/float attempts. Repeat
   with partners kept away so another Kirby cannot hold the switch silently.
5. Verify whether passing the door reaches tile (2, 7) and Up transitions to 730
   at (29, 4). Separately test the automatic tiles (17..27, 11) into 734 at (14, 5).
   Record which actions enter the upper music compartment and whether the
   solid divider prevents access to the lower 1-UP compartment.
6. In the all-65 integrated build, opening the upper Music Sheet #6 chest must
   report location 3960519 once and suppress its native sheet grant. Confirm the
   assigned AP reward separately. The lower 1-UP source 0x008D3E88 belongs to
   the 5-07 entry. Retest collection/save/reload/reconnect.

The static source distinguishes attribute 255/0x4001 (Up) from 254/0x104001
(automatic). The door reads ROOM slot 1, shared with the small switch. These are
verified local conditions, not a complete logic rule. Preserve failed/blocked
trials as evidence. Do not add expanded route or ability logic to this v0.4 scope.

### Levers: `v040-lever-{moonlight|olive|carrot|radish}-{order}`

For each of the four levers, exercise both physical-first and item-first order:

1. Pull first: one physical AP check; the corresponding wall stays closed until
   its Lever Wall item is received.
2. Receive first: the correct wall opens, but the lever remains interactable and
   still sends its physical check when pulled.
3. Receive during the delayed popup; leave/reenter; reconnect; save/reload.
   The live room receives at most one wall contribution from the owned lever.
4. Check an unrelated ordinary small switch and an unrelated room-counter
   mechanism. Neither should inherit the AP lever gate.

### Ability gating: `v040-ability-final-{scenario}`

Reproduce the original damage/lost-ability/Waddle Doo contact sequence with
Tornado locked, then unlocked. Also cover ordinary copy, a dropped ability star,
and mix roulette across supported randomization modes and with gating disabled.
Watch pending and committed ability fields and the live unlock mask. A locked
ability must not commit after a late pending-field update; allowed abilities and
native upper transition flags must remain intact. Do not mark the original
collision report resolved merely because the isolated final-commit test passes.

### Custom health: `v040-health-{minimum}-{maximum}`

Cover default 6/10, both One-Hit presets, 1/1, 1/5, 7/10 and 10/10. Verify the
starting capacity, every included unique Vitality Counter, final cap and correct
filler substitution for excluded counters. Test damage, healing, item receipt,
room changes, respawn, DeathLink, save/load and reconnect. Repeated client polls
must not heal damage or revive dead Kirby. Check health-meter visuals and record
any visible interval before connected-client reconciliation. Also load an older
slot without the new keys and verify its prior behavior.

### Check delivery and lifecycle: `v040-check-retry-{scenario}`

Drop the server connection immediately after an observed chest check. Reconnect
and verify the pending check is retried until acknowledged, including after its
ring entry has been overwritten. Switch authenticated seed/team/slot and verify
old pending checks do not leak. AP server acknowledgment is the deduplication
boundary. Separately record the current limitations: events overwritten before
first observation and unacknowledged observations lost when the client exits are
not claimed durable by the eight-entry event ring.

### Existing flow: `v040-regression-{flow}`

Check tutorial World Map chest, map/shard/boss checks and grants, vitality big
chests, normal switch behavior, native rewards outside owned source tables,
mailbox ordering, save/reload, and the selected goal. Run at least one fresh seed
through a complete session after the focused cases.

## Record results with the existing parser

Use the repository's `.github/scripts/manual_test_checklist_parser.py` schema.
Produce one block per case/variant; keep failed and blocked evidence alongside
passes. The example below is intentionally BLOCKED and must not be copied as a
passing result. `BUILD_REF` must identify the actual tested combined commit.

<!-- MANUAL_TEST_RESULT:START -->
RESULT_SCHEMA_VERSION: 1
TEST_CASE_ID: v040-runtime-preflight
STATUS: BLOCKED
BUILD_REF: pending-final-combined-commit
PLATFORM: pending-authorized-runtime-environment
BIZHAWK_VERSION: not-run
ROM_REGION: USA
EXPECTED_RESULT: Rebuilt real-ROM payload and matching client complete the runtime cases above
OBSERVED_RESULT: Gameplay has not been run for this checklist
EVIDENCE: pending-client-log-and-case-evidence
NOTES: Pi real-ROM build and local protocol checks passed; BizHawk gameplay remains unrun
<!-- MANUAL_TEST_RESULT:END -->

## Review gate

A release decision requires the final combined build, passing applicable CI,
reviewed runtime results, and an explicit decision for every remaining failure or
deferred source. Neither generating this checklist nor completing an automated
suite authorizes merging, releasing, or moving private ROM files.
