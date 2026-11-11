# Native707: statue-backed directed Burning exit

This checkpoint accepts one source-backed target, `metal_707_to_712`, on
`REGION_MOONLIGHT_MANSION/ROOM_2_04_PAST_SWITCH_WALL -> REGION_MOONLIGHT_MANSION/ROOM_2_13`.
It does not remove starting Burning or Stone, accept another metal provider, or
claim every ordinary-metal room is complete.

## Source and independent access

Two alternative graphs belong to this **one** target row. The installer ORs the
graphs; separate rows on the same entrance would incorrectly AND them.

- `central_statues` starts Normal at native801 with independent Central Circle access.
- `cabbage592_statues` starts Normal at native592 with independent Cabbage Hub3 access.

Both reuse `ordinary_hub_statues`, including its real physical identities,
directed door guards, source policy, and documented permanent-retouch fairness.
The vanilla Burning source is native592 object `0x088CEFC8`, `STATUE:3538FD`.
The minimal Central route needs Cabbage Cavern West and Moonlight Mansion Hub
Connections, plus their two destination Area Keys when enabled. Independently
reached592 needs both connections and the Moonlight key, not another Cabbage key.
No all-switch, Copy Ability Room, Cabbage East, or unrelated hub requirement is
added. Other already-reviewed hub statues can substitute only if their actual
policy supplies Burning and the corresponding guarded physical path succeeds.

The new target is unconditional. No `requires_guaranteed_source` extension was
needed. A policy lacking any reviewed source stays closed instead of retaining
the old permissive metal alias. Existing bounded whole-policy resampling applies
in shuffled mode; no single source or user option is rewritten. Live included
statues use the existing explicit positive-support retouch fairness, not a finite
RNG guarantee. Enemy no-ability weight does not apply to a statue's mask. Excluded
statues retain native abilities. Future Burning permission is tested at actual
acquisition; owning the permission does not equip it.

## Physical carrier and evidence boundary

The existing source/geometry-backed hub contract supplies acquisition and carry
to790. The new traces independently validate the missing continuation:

`790 -> 706 main/upper arrival -> 707 left arrival -> timed mechanism -> upper shaft -> F5 -> 712`.

Exact ordinary door records are790 `0x88565A` to706 spawn(4,3),706 `0x88358A`
to707 spawn(2,10), and707 `0x8836F4` to712 spawn(2,29). Live arrivals are
706(56,40.996),707(24,152.996),712(24,456.996). Neither the706 lower compartment
nor the709 alternate707 arrival is silently substituted.

Both controller fixtures change the native790 Bomb statue `0x088BDDF0` from
subtype6 to1 **only to supply imported Burning for the experiment**. Production
still maps that object to `STATUE:353902`, native Bomb. It is not a vanilla
Burning source and the fixtures are not a complete592 source-to712 replay.
No source/terrain/attack/runtime writes occur in the accepted controller chain.
The hub prefix and the continuation remain separately stated evidence layers.

- [Default-health trace](ordinary-707-imported-burning-acceptance.json):25 linked
  segments,24 post-acquisition segments/5,022 frames audited. Every audited frame
  has6HP, no decrease, and ability3 (Burning).
- [500% enemy-health trace](ordinary-707-all500-acceptance.json):26 linked
  segments,25 post-acquisition segments/5,243 frames audited with the same invariant.
  The production enemy-health scaler is applied once before cold boot, including
  all supported enemy classes, not only Waddle Doo. Its pinned module blob is
  checked against the checked-in scaler. Durable Heavy Knight uses a changed
  rapid repeated-Burning/ordinary-flight continuation, rather than assuming the
  default single-hit timing works.

Both traces read F5(69,4)/(70,4) as245 before and0 after the rightward action,
then activate the actual712 door while retaining Burning. The upper throat has
no reviewed Normal bypass or Throw ammunition route. The button `0x088BCD6C`
and sliding door `0x088BCD00` share slot1; the recorded timer field is0 and flags8,
not742's120-frame contract. Only the complete atomic crossing is accepted.
No permanent opened flag, room reset, or post-camera enemy deletion is inferred.

## Representation and health scope

The reusable suffix contains three nodes and two internal edges. Each graph has
one join from existing `hub_790`; that join is outside the part because standalone
parts validate all endpoints. It crosses706 and707 directionally without source
placements or dropped-star recovery. Its final same-room metal action permits
only Burning and bundles the exact707 carrier sequence. Therefore a successful
path must have retained the same Burning through706: dropping it cannot produce
a false route because nothing in the suffix can reacquire it. Ordinary carrier
edges do not separately certify Normal traversal. The final node is terminal and
cannot export equipment or open-state credit into another route.

The no-loss evidence does not rely on damage boosts or hit invulnerability. The
bounded Normal/Burning health-independence source analysis in
[742 health scope](ordinary-742-health-scope.md) also applies to these unchanged
moves. Starting1HP is supported by that source argument plus the no-loss trace,
not a direct AP1HP replay. The100% and500% traces are accepted route witnesses,
not a claim to have replayed every intermediate multiplier, RNG timing, live
source outcome, or a full AP/server session. Original hub-prefix acceptance stays
at its documented source/geometry evidence level.

## Explicit omissions

No Waddle Doo/Heavy Knight local acquisition, finite-enemy retry, dropped-star
recovery,709 approach, additional attack provider, or new renewability rule is
accepted. Other ordinary-metal targets and supported-policy completeness still
block starting-inventory removal. Native742 roof-Doo reappearance does not prove
that any Flamer is renewable; that future investigation remains separate.

## Regression and cost checks

Tests cover real source identity, exact minimal hub/key sets, included/excluded
statue policies, live fairness versus finite guarantees, no-source and source-
behind-metal failures, absence of outgoing terminal edges, one target/OR access,
indirect AP conditions, future Burning self-lock, and unchanged base rules.
Native artifact tests check every linked segment, audit coverage, source fixture
disclosure, actual transition/F5 observations and the production scaler hash.
A changed exact minimal-fuzz69 placement is now safe under the new gate; its test
requires successful generation and preserves the source policy. Separate mixed-
player and deliberately stranded fixtures still require the final all-check guard.

Five warmed1,000-evaluation samples per inventory are recorded in
[the benchmark](ordinary-metal-kernel-benchmark.json). Each expanded graph has
19 nodes,33 routes and30 renewable statues. Minimal items visit27/25 states
at129/116 microseconds median; all guarded route items visit290 states
at1.72/1.64 milliseconds. This measures the cost of retaining legitimate
alternative hub sources, not a before/after optimization or whole-generation time.

The full live statue pool is a separate worst-input case: all 25 supported
outputs, all route items and documented retries visit 452 states, taking
19.31/18.70 milliseconds median (five samples of 200 evaluations). Graph/catalog
compilation is cached and each evaluation memoizes grants by source key, but
fixed-point results are recomputed for the current inventory. No existing
post-guarantee source filter can prune irrelevant equipment safely. Filtering
through the permission callback would incorrectly turn mixed finite grants into
certainty. The bounded full-prefix cost is retained instead of adding a broad
kernel feature, changing source policy, or duplicating selected statue paths.
