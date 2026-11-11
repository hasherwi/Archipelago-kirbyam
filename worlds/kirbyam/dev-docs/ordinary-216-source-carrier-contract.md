# Native216: statue-backed Burning chest branch

This checkpoint binds only `MINOR_CHEST_PEPPERMINT_PALACE_7_19` in
`REGION_PEPPERMINT_PALACE/ROOM_7_19`, target `metal_216_chest`. Native object
`0x088C1380` at(608,72) is the1-Up chest with flag36. The two ordinary exits and
the physical RoomSanity check remain unchanged. Starting Burning and Stone are
not removed, and no other metal provider or arrival is certified here.

## Real source and independent access

One target has two OR access graphs, not two independently ANDed bindings:

- `central_statues` starts Normal at `hub_801` with independent Central Circle
  access. Its minimal native route needs Peppermint East and West Hub Connection
  items, plus the Peppermint Area Key when area keys are enabled.
- `peppermint291_statues` starts Normal at `hub_291` with independently reached
  Peppermint Hub2 access. That start does not need either connection or another
  area-entry key before using its own statue and ordinary overland departure.

Both reuse `ordinary_hub_statues`. Native291 Burning statue `0x088C263C` has
source key `STATUE:3538FD`; other reachable hub statues may substitute only when
their actual source policy supplies Burning and their physical hub guards pass.
Fixed/excluded statues retain their native assignment. Shuffled statues use the
final runtime assignment. Included live statues use the existing documented
permanent-retouch fairness, not a finite-enemy RNG guarantee. Enemy no-ability
weight does not change a statue's mask. Permission is checked at acquisition and
does not itself equip Burning.

The target is unconditional. An unsupported assignment cannot fall back to the
previous ungated chest. Existing bounded whole-policy resampling handles shuffled
feasibility without rewriting individual sources or changing user options. Other
unreviewed routes are not declared impossible, but they are not credited.

## Reused carrier and exact accepted suffix

The existing `rope_217_6_5` contract supplies the ordinary carrier:

`291 ->215 spawn(27,29) ->212 spawn(74,9) ->216 spawn(44,18)`.

It uses ordinary block clearing and avoids the metal chest branch before arrival.
This prefix remains at its previously reviewed source/geometry evidence level.
It is not relabeled as a new complete291-to-chest controller replay. The shared
hub source graph and four-node source-free suffix avoid duplicating policy logic.
The final Burning-only action requires the same equipment to survive the carrier;
there are no suffix sources, dropped-star recovery or room-reset assumptions.

The [native acceptance](ordinary-216-imported-burning-acceptance.json) starts in212
and supplies imported Burning by replacing Waddle Doo template `0x088C103C` with
an essence at(40,40), type0x92/subtype1. **That synthetic essence is not a production
source.** Actual212-to216 transition reaches(696,280.996);216's objects are unchanged.

Kirby crosses the lower corridor, climbs the shaft and lands at(441.996,104.996).
The low rightward dash clears all six F5 cells at x28..30/y5..6. Higher dashes
hit the solid cap; this is not evidence for downward Burning or arbitrary aerial
attacks. After floating to(608.394,72.996), holding Up30 frames then releasing90
sets flag36 mask16. Earlier one-frame Up attempts and apparent visual absence
were not accepted as collection or a spawn failure.

Fresh100% and500% enemy-health runs each have ten post-boot segments and1,305
frames audited continuously: minimum6HP, zero decreases, Burning retained after
fixture acquisition. The500% fixture applies the pinned production scaler once
before fresh boot, not a single-enemy substitution. Its module Git blob and
SHA256 match the checked-in scaler; the record also checks native enemy type0x22
HP2 to10. These are native source-equivalent fixtures, not full AP-patched/server
acceptance or a direct one-HP replay.

The bounded Normal/Burning source reasoning in
[742 health scope](ordinary-742-health-scope.md), combined with the continuous
zero-loss trace, supports positive-HP movement without damage boosts or hit
invulnerability. Prefix evidence retains its original scope. Endpoint durability
acceptance is not an exhaustive replay of every intermediate multiplier or timing.

The target node is terminal. It records successful collection, not a reusable
Burning-equipped state, persistent destroyed blocks, or access from217's opposite
arrival. Extending that node would require a separate reviewed postcondition.

## Regression coverage and bounded cost

Tests cover exact291 source identity, Central/291 access alternatives, minimal
hub/key requirements, fixed and live statue policy, permission-versus-equipment,
disabled gating and location categories, no-source and source-behind-target
negatives, whole-policy resampling, all other providers, underwater rejection,
and actual AP permission/hub items placed behind their own chest. Ordinary exits
and the existing RoomSanity location are explicitly preserved.

Each expanded graph contains20 nodes,34 routes and30 renewable statue placements.
Graph/catalog compilation and per-evaluation grant memoization remain unchanged.
There is no new result cache, source-pool pruning or kernel feature. The benchmark
records minimal native, all-items native and full live-pool cases alongside707
using the same evaluator; it measures bounded graph cost rather than a speedup
or whole-generation runtime. See `source_backed_216` in
[the benchmark](ordinary-metal-kernel-benchmark.json).

The ordinary-metal benchmark above records the pre-optimization baseline. The
subsequent per-evaluation source-expansion optimization preserves all 477 live
Positions while reducing this graph from 19,284 to 2,004 dequeues. See
[source-expansion measurements](source-expansion-optimization.md) for the paired
post-integration timings and complete-result equivalence tests.
