# v0.4.0 combined runtime acceptance

This is a test plan, not a record of passing gameplay. The cloud suite and dummy
ROM smoke cannot replace these checks. Keep the implementation PRs as drafts
until their remaining gates are reviewed.

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

Open active exact-source Spray Paint and Music Sheet chests before receiving
those items: the native ownership bit must remain unchanged. Receive each AP
item, then replay/reconnect: exactly its bit is added and existing ownership is
preserved. Sheets never grant Sound Player (bit 0). Check the independent Sound
Player chest and its AP item too. Preserve normal collection visuals and native
room-counter behavior.

The currently deferred Spray Paint #6 and Music Sheet #6 must remain native and
must not report checks or enter the item pool unless a later reviewed mapping
explicitly activates them. Record the build's intended active-source count.

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
NOTES: Cloud tests and dummy-ROM smoke are not runtime acceptance
<!-- MANUAL_TEST_RESULT:END -->

## Review gate

A release decision requires the final combined build, passing applicable CI,
reviewed runtime results, and an explicit decision for every remaining failure or
deferred source. Neither generating this checklist nor completing an automated
suite authorizes merging, releasing, or moving private ROM files.
