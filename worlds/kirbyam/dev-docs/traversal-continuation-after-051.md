# Traversal continuation after v0.5.1

This document tracks continuation work. The bounded experiments below do not themselves install new route rules. Baseline: merged PR #1052 at `727099d75aec8a70ea87cce88d7d69358e345426`, with Beam and Ice starting inventory. The catalog's 57 targets and 146 witnesses are not a physical-room count or a completion certificate.

## Scope
- [x] Separate the three reviewed Crash witnesses into **Advanced Logic**, the default-off `advanced_logic: false` toggle under **Make the game harder**. It enables only the reviewed room-126 fuse, room-533 switch and room-310 map witnesses, not every Crash trick. Normal-only baseline and Normal + Crash (#1064) remain distinct. The earlier `traversal_logic` choice was unreleased and is no longer supported.
- [ ] Complete remaining Normal-only physical qualification; the advanced option does not establish new route evidence.
- [ ] Keep unmerged Phone work (#1086) separate.
- [x] Record final baseline CI and release-artifact verification: final #1052 head `2b51efe` passed the complete Windows/macOS/Linux matrix and focused Kirby tests ([run](https://github.com/hasherwi/Archipelago-kirbyam/actions/runs/43362275606)). Merged source `727099d` was tagged `kirbyam-v0.5.1-rc1`; [tag-push run 43363217716](https://github.com/hasherwi/Archipelago-kirbyam/actions/runs/43363217716), attempt 1, staged all three assets. Read-only public verification passed their downloaded hashes, signatures, source/tag/run identity and exact asset allowlist. Release remains mutable, not guaranteed immutable.

## Remaining declared source-policy fallbacks
- [ ] Chocolate chest (517): qualify an ordinary or exact source/carry alternative across supported assignments. Upper-194 transit probes are not lower-194/591 or complete 517 proof.
- [ ] Yellow Paint (733): qualify source acquisition, ladder/drop/reacquisition, trigger and collection separately.
- [ ] Timed exit (533): qualify exact entry, attack, health and timed crossing without assuming a successful mixed/failable source roll.
- [ ] Mustard map (310): qualify exact source, carry, attack and timed chest continuation.
- [ ] Preserve older rules explicitly until each replacement is reviewed. These four targets are not an exhaustive physical-room checklist.

## Bounded Chocolate-route progress (2026-11-13)

A fresh, independently audited native run now validates the retained human
Master carrier through the upper-to-lower landing in room 194, ending stationary
at the reviewed frame-2081 boundary. The run contains 381 accepted observations
and 380 committed gameplay commands, followed by a separate termination that
adds no game frames. The complete child, service and controller suites passed
independently: 571, 136 and 122 tests respectively. The reviewed source closure
is `5421056eb1f67de035bad2126f7695f2ac36d85ed2483b8cb20cabcd92a2681a`.

This closes the bounded landing segment, **not the Chocolate chest witness**.
The endpoint retains Master at one HP and has not collected chest 57. Historical
clear/Hub prerequisites remain explicit; this is not a new-seed full playthrough,
universal multiplayer proof, or credit for helper combat or ability acquisition.
The audit preserves earlier rejected attempts and verifies the final run's
command acknowledgements, unchanged input save and actual process closure.

The next segment is neutral landing-effect cleanup, followed separately by
lower-room positioning, the 591 transition and the 517 target action. Cleanup
still needs fresh terrain evidence and source-qualified retirement/new-generation
tracking for remote effects. No new fallback replacement, source-policy coverage,
location access rule or target count is claimed by this landing result.

Checkpoint-based test acceleration is experimental and remains disabled for
these traversal runs. A core save alone does not reconstruct the client,
observer histories, input latch or command custody. The accepted landing run
used the existing cold-prefix path; it was not restored from a checkpoint.

## Reset and busy-lock diagnostic progress (2026-11-15)

A separate retained run subsequently verified the bounded rightward window
through frame 2099 in room 194, with successful owning-process waits. It did
not qualify the Chocolate chest or the full route. The historical frame-2081
landing result above remains distinct from this later window.

The new milestone is **diagnostic equivalence through frame 2100**, not a new
accepted traversal endpoint. A one-shot comparison used a replay-assisted
historical prefix through frame 2095, followed by five diagnostic right-input
frames. The rebuilt, guarded-but-unarmed, reset-unarmed and reset-guarded variants
all matched the original at frames 2095, 2099 and 2100: 12 comparisons covering
serialized native state and image data, excluding only wall-clock metadata.
All child and coordinator waits completed successfully; no retry was performed.

The reset-guarded diagnostic retained seven reset records, eleven instruction
witnesses for one complete SoundMain busy-lock acquisition/release, and 128 audio
word records for the 2099-to-2100 generation. The lock observer binds the copied
code to reviewed source bytes, checks the executed instruction sequence, and
rejects DMA writes into that protected code region before mutation. Separate,
versioned receipts retain the reset, lock and audio histories; a reset receipt
alone is not lock evidence.

The corresponding source validation passed 544 tests and three subtests, with
unchanged pinned inputs and verified module origins. These tests and the A/B
comparison do **not** establish retained scene/service/controller acceptance at
frame 2100, a new-seed playthrough, the 591 transition, the 517 target action, or
full-route completion. The diagnostic remains explicitly replay-assisted and
non-authoritative for gameplay acceptance. No route rule, fallback, target count,
tag or release is changed by this result.

### Current status (2026-11-16)

Later supervised work reached the retained frame-2101 boundary. That is a
bounded room-194 result, not the 591 transition, room-517 target action or
Chocolate chest acceptance. The subsequent one-shot attempt toward 2102 timed
out under its supervisor; its last committed observation was frame 2098.
It produced no native owning-wait receipt, so the native child's exit remains
unknown. Controller termination and absent processes do not substitute for that
receipt. The attempt remains unresolved; neither retry nor 2102 acceptance is
implied. These are separate runs, not a regression of the earlier 2101 result.

CI is green as of public source `18a96a3a3` ([unit and focused matrix](https://github.com/hasherwi/Archipelago-kirbyam/actions/runs/43782381123));
the release job is skipped. That source/test result does not
convert the physical limitations above into a route pass or a merge decision.
The supervised lifecycle and recovery-reader work remains private qualification
work, not a new public traversal rule.

### Practical validation choices

- **Human gameplay review now:** use an exact current generated patch, record
  its source/build hashes and options, and retain a continuous source pickup,
  ability carry, room transitions, target action and chest/AP check. Disclose
  imported clear/Hub prerequisites, health, damage and normal client writes;
  do not splice a target suffix into upstream proof. This needs one playable
  setup and a recorded route, plus a repeat and an omitted-final-action control
  if proposing a new witness. It can support route feasibility with transparent
  limits, not callback/DMA custody, every source policy or full owner acceptance.
- **Shorter automated checkpoint:** a cold source-acquisition or already reached
  room-194 endpoint can check setup and retention at lower scope. Much of that
  evidence already exists; it cannot establish the missing 591/517 continuation.
  A restored near-target state would be a local suffix experiment only, and
  checkpoint reconstruction remains unqualified. Do not add that infrastructure
  merely to relabel a shorter test as a full carrier pass.
- **Continue the automated supervised carrier:** after separately resolving lifecycle/recovery
  prerequisites, qualify lower-room positioning, 591 entry, the 517 target and
  collection. This is the highest-work automated option for a new complete
  Chocolate witness with supervised custody. A continuous human run can instead
  support physical feasibility with the limits above. No new diagnostic or launch is authorized by this
  document.

A human reviewer can assess the source changes and bounded evidence now while
leaving the remaining physical work explicitly open. Prefer that focused review
and a concrete gameplay checklist over expanding recovery infrastructure beyond
what the next justified experiment requires.

## Evidence and integration
- [ ] Reconcile the coverage ledger, source census and exact AP location/exit ownership before selecting experiments.
- [ ] Review ordinary routes first. Permission inventory does not supply an equipped ability or renewable source.
- [ ] Keep alternatives as separate same-target OR witnesses with graph-local source predicates.
- [ ] Qualify actor ownership, post-presentation lifetime, terrain/collision state, finite consumption and directed entry compartments.
- [ ] Use positive/repeat/omission controls and relevant health/option boundaries; preserve failures and historical hashes.
- [ ] Never assume helper Copy Abilities, combat, acquisition or carry. Only supported small-switch and Heave-Ho assistance is eligible.
- [ ] Do not count a target-only suffix as upstream acquisition/carry proof or a local receipt as server acknowledgment.
- [ ] Add positive and negative route/source/ownership/equipment tests; preserve unrelated exits, Secret Notes and Room Sanity ownership.
- [ ] Recheck starting-item multiplicity, conditional progression, frozen legacy gates and receipt compatibility.
- [ ] Run real generation with deterministic outcomes and the final all-check safety guard; distinguish accepted archives from deliberate refusals.
- [ ] Independently review new route evidence and compiler/runtime changes.
- [ ] Verify exact-head CI, source/package identity and unchanged or explicitly reviewed ROM patch before requesting merge.

Detailed evidence remains in the [coverage ledger](ranged-coverage-ledger.md) and linked target records. Mark steps complete only with their actual source SHA and evidence. Publish reviewed source and derived observations only, never ROMs, saves, credentials or unrelated private material. This continuation does not authorize a tag, release or deployment.
