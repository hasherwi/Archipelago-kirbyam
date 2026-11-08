# Ordinary-metal traversal implementation checkpoint

This checkpoint prepares directional ordinary-metal rules without pretending
that the complete 33-room audit is finished. **Only native557 has a bounded
Master Hand-to-Smash witness; removing forced Stone/Burning is not safe on
this evidence.** Other assignments and rooms remain unvalidated. Runtime
patches, starting inventory and item classification are unchanged here. The
foundation baseline is `1cdde1a`.

## Reuse the existing state model

Metal attacks use the existing equipped-ability, source-policy, room-instance,
and consumed-object planner. There is no new dynamic facing, charge, jump or
water-phase state. A reviewed action sequence is one directed edge whose
geometry and controller proof live in an acceptance record. Compilation checks
an explicit provider list and one evidence reference per provider. It does not
claim that nonempty text proves native physics.

The seven direct providers are Burning, Hammer, Stone, Missile, UFO, Smash and
Master. Throw remains the eighth metal-breaking ability, but uses the separate
`metal_throw` physical-object action. A one-use enemy is captured and released
from the reviewed source compartment. The shared `uses_object`/`consumed`
mechanism prevents swallowing it for an ability and then also throwing it.
Unavailable or already-consumed ammunition, another compartment's enemy,
statues, registry-ineligible enemies, renewable objects, and cross-room capture
transport are rejected. The generic enemy eligibility flag is a conservative
minimum, not proof that every remaining enemy is grabbable by Throw; the
room-specific capture witness is still required.
Throw cannot start from swimming. No held-object movement is inferred.

Both direct and Throw sequences remain within one native room. A subsequent
door crossing is a separate edge. Direction, airborne clearance, UFO charge,
Stone transformation completion, and Missile dry launch into water must be
supported by each provider's exact accepted sequence. These details are not
universal capability claims. Unproven reverse routes remain absent.

The `metal` target kind joins the shared installer and source feasibility
checks. The existing conditional-source mechanism now accepts validated enemy
source keys and non-Normal ability names rather than a hard-coded single boss.
Its meaning is unchanged: a partial witness applies only when the finalized
source policy guarantees that output. This applicability test never equips
Kirby, creates an enemy placement, or proves access to that source. An
unreviewed assignment remains unvalidated; such a conditional witness cannot
justify broad starting-inventory removal.

At this baseline, no serialized production route uses `metal`, so separating
Throw from direct attacks does not change an existing accepted room witness.
Existing frozen-enemy identity semantics are preserved through the shared
projectile validator.

## Exhaustive coverage worklist

[The coverage matrix](ordinary-metal-coverage.json) accounts for all **358 F5
tiles in 81 four-neighbor clusters across 33 native rooms**. Tests compare every
coordinate to the independent presence inventory, check exact connected
components, and preserve current AP checks, compartments, logical room-check
helpers and exits. This is a worklist, not a 81-gate implementation.

The [role review](ordinary-metal-role-review.json) gives provisional roles to all
47 initially unknown clusters. Current totals are 25 with no required AP passage,
21 optional non-AP-loot clusters, 15 clusters in the two existing Normal-bypass
rooms, 13 potential AP exit clusters and seven potential AP check clusters.
A role classification does not certify a whole-room route or accept a provider.
In particular, native502 overhead clearance, native529 directed underwater/pit
routes, and native736's top-left exit retain explicit unresolved questions.

Native312 F5 uses orange ruin masonry artwork, so collision identity rather
than silver-looking pixels defines this inventory. Native736 cannon-ring F5 is
physical terrain that the native launch attack can break before self-transition;
it is not dismissed as decorative teleport scenery and needs no invented copy
ability requirement. This role review does not add controller shot acceptance.
Public composites omit the final two native tile rows; those crops cannot
prove a safe bottom route. Native510's metal tunnel is an alternate approach to
the existing peg-access chest, not an additional universal requirement.

There are **nine**, not ten, directed legacy edges containing
`can_break_metal` or `can_break_metal_throw`. They cover native 141, 205, 707,
708 and 742. Those permissive tokens are not an exhaustive AP-target inventory:
metal-protected minor chests in 176, 216, 228, 229, 537 and 557 are untagged.
Starting-inventory removal must cover actual checks and routes, not just replace
these nine strings.

The matrix also audits all compact block placeholders: 137 `can_break_block`
alias occurrences, 18 `can_break_floating_block`, eight `can_break_metal`, one
`can_break_metal_throw`, and no literal `CanBreakBlocks` bindings. The alias
still calls the permissive `CanBreakBlocks` helper; many uses describe ordinary
Normal-breakable terrain, so these counts are not metal-gate counts. The shared
eight-ability constant is descriptive and never supplies equipment or Throw
ammunition. Native collision geometry and actual AP targets remain authoritative.

Important unresolved examples:

- Native 205 has two clusters. The accepted aerial-Hammer floor plug is only
  `(21–22,8–9)`; `(24–26,3–4)` and the source/whole chest-room route are separate.
- Native 537 Beginning Notes is behind a floor plug, not a generic horizontal
  wall. The proposed Normal drop-shaft bypass from native 538's reverse entrance
  at `(44,3)` failed controller testing: the `0x0F` shaft cap could not be
  descended with Down/Down+A. Do not infer a bypass from an apparent grid opening.
- Native 557 now has the bounded, layered witness below. A combined actual
  defeat, acquisition and chest-collection replay remains uncompleted.
- Native 814 and 819 retain their existing controller-proven Normal exits.
  Those proofs do not grant access to their optional metal-protected loot.
- Native 707 has no capture object at the upper firing position. Throw cannot
  carry a lower enemy up to the shaft.

## Native 557 Goal 1 tomato: bounded conditional witness

`metal_557_goal1_tomato` targets only
`MINOR_CHEST_RAINBOW_ROUTE_1_GOAL_1_OBJECT_01`. It applies only when the finalized
`MASTER_HAND` source policy guarantees Smash, including native/excluded sources
and a deterministic Smash assignment. A multi-outcome live-random source or
possible Normal outcome does not qualify. Other policies retain prior rules
and are explicitly unvalidated, not declared safe or impossible.

[The acceptance record](ordinary-557-smash-acceptance.json) separates three layers:

1. **Actual-entry controller access.** Native556 door `0x87C31C` transitions to
   557 at `(24,72.996)` as Normal. Rightward descent, the shelf and ladder reach
   the actual, unchanged Master Hand arena. A continuation reaches the boss
   floor and walks left to `(268.656,328.996)` as Normal with four HP remaining.
2. **Native source/capture proof with the existing ordinary-combat assumption.**
   Master Hand template `0x088B9358`, type `0x3E`, starts at `(440,264)` before
   the metal barrier. `InitObject` reads its ability from table `0x351C1E`,
   native value22 (Smash). Shared defeated-miniboss and inhale code retains a
   capture interval and passes its current `kirbyAbility` to `sub_080547C4`.
   This is the usual defeatable/swallowable miniboss-source assumption used by
   existing traversal witnesses, not a newly completed Normal fight replay.
   After successful in-arena capture, the open floor corridor x15–30/y19–20,
   solid floor y21, and walk-off platforms connect to the launch position with
   no extra copy ability, water or metal barrier. No claim covers every possible
   knockback/body position.
3. **Isolated AP-patched move and collection.** A disclosed physical Smash
   essence replaces Master Hand in this separate fixture. From the right-hand
   floor, two grounded Left+B Hammer swings while advancing clear13 of14 F5
   tiles. Only `(10,18)` remains. Walking into the pocket and pressing Up sets
   native chest flag6 and emits local AP event `0x088B9280` (counter0 to1), with
   Smash equipped and six HP. The essence is not proof of actual Hand acquisition.

The four-node graph starts Normal, reaches the arena source, carries the acquired
Smash along the reviewed common floor, and performs that exact dry attack
sequence. It adds no persistent opening, retry, reverse traversal, or free
ability start. The Goal exit and room visit remain independent of the chest
rule; a Normal Goal-door replay is not claimed here.

The record does not establish a combined actual Hand defeat/swallow/chest run,
randomization/unlock gameplay, server acknowledgement, battery-save reload,
damage-free access or one-hit-mode acceptance. Python policy/gating tests are
separate from the isolated fixture, whose ability gate was disabled. The source
contract was independently reread at native revision
`7d969fbce14fdc838d2c1ea01389717fb96c3189` in
[`object.c`](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/object.c):
`InitObject`, `sub_0809C48C`, and `sub_0809D060`/`sub_0809D1E0`.

## Cost and verification

The [paired Python 3.12 benchmark](ordinary-metal-kernel-benchmark.json) compares
this kernel with `1cdde1a`, excluding imports and graph compilation. Existing
Mini 134, peg 605 and Heave-Ho 102 keep exactly 7, 18 and 4 reached states.
Twelve warmed paired samples gave median evaluation times of 16.25 vs 16.12,
47.32 vs 49.97, and 8.01 vs 8.28 microseconds respectively (new vs baseline).
Ranges overlap; this is no speedup claim or whole-generation benchmark.
A synthetic two-node Throw action reaches four states and takes 10.34
microseconds median. It measures kernel cost, not native room acceptance.
The new conditional557 graph reaches nine states and takes 18.01 microseconds
median with the reviewed source assignment and owned Smash permission.

Focused tests cover provider narrowing, unreachable sources, permission versus
equipment, source-policy uncertainty, physical ammunition availability and
consumption, no reverse or cross-room capture transport, swimming rejection,
per-provider evidence, and exhaustive worklist consistency. Native and AP-ROM
acceptance are separate from these Python semantic tests.
