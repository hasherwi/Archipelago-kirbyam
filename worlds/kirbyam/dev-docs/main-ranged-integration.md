# Main and ranged traversal integration

This reconciles merged main `a58d79223214d4e274b57afda5845a491e7c9e71`
with the reviewed PR1052/UFO source tree
`65ec012ad7762a31574b11f7b41b00c356446513`. It adds no native gameplay proof.
Unmerged PR1086 source, Phone, payload and Chalk changes are not included.

## Logic union

- Sound Effects chest825 has one unconditional installed target. Its four OR
  witnesses are finite Frosty Ice, finite Frosty UFO, Central statue Ice and
  Peppermint290 statue Ice. Only the two finite graphs gain exact raw singleton
  source applicability; their physical graphs remain unchanged. Permanent Ice
  stays available under unrelated Frosty assignments. Separate target rows
  would incorrectly AND these alternatives.
- Retain metal, reinforced, Throw/projectile and Heave-Ho validation alongside
  target-specific ranged capabilities, switch targets, required equipment and
  tightly scoped target lists. Optional538 remains fail-closed. Graph source
  conditions accept singleton `{source_key, ability}` only.
- Keep source expansion deduplicated by `(node, opened, consumed)` and cache
  grants per evaluation. All route, equipment, drop and recovery expansion still
  runs per Position. Opened barriers and finite object use remain separate.
- Goal2 Ice is progression before region creation whenever the physical minor
  chest category and gating are enabled, independently of Frosty. Chocolate
  and other conditional classifications remain. Post-region reconciliation
  touches only non-progression precollected items, preventing double collection.
- Keep Beam-only automatic inventory, Stone/Burning progression, explicit24
  slot gates, frozen22 legacy fallback, bounded source validation even under
  minimal accessibility and final placed-progression closure before archive.

## Evidence and tests

`main-ranged-union-catalog.json` is derived from both pinned input trees. It
checks every target, graph part and source set, including all ten Chocolate
witnesses. It is a structural integration record, not an emulator acceptance.
The source monotonicity census now records143 witnesses,286 key variants and108
physical source/key identities, including witness-specific renewal variants.
Existing ranged raw-source guards explain its three dry Beam routes.

Historical native records keep their original hashes, source policies, item
permissions and scope. A historical whole-catalog or client hash is not a claim
that the current merged generator produces that earlier setup. Preservation
checks now compare unchanged physical graphs and separately adopted main data.

Isolated rule/lifecycle tests inject fixed historical policies after ordinary
`generate_early` validation. They do not force the whole-policy retry builder to
return a rejected historical assignment8192 times, and do not assert generation
acceptance for that policy. Full archive tests still use actual validation,
unchanged bounds, final reachability and safe refusal/no-archive behavior.

The pre-union main compiled fingerprints remain historical. Tests first require
all added equipment fields to be null and all source conditions to be null
except the exact825/local Frosty-Ice predicate, then project the old shape and
check the original hashes. Raw graph checks additionally verify one exact
accepted fuse126 documentation edit. Mutation tests reject missing/changed
predicates, new equipment constraints and changed physical graph fields.

Deterministic generation expectations are scoped to the combined catalog:
- Cutter seed8675309/mode0/gating1/minimal now produces124 reachable physical
  checks. Cutter is earned in sphere4 and Radish Big Switch is reached in sphere6.
  Modes1/2 retain their explicit unsafe-fill refusal assertions.
- Permission smoke core09 (profile0/mode0/gating1/minimal, seed105100) now refuses
  at final placed-progression closure with zero archives. The exact failure and
  original8192 source-selection budget are checked. The pre-union main table is
  retained as history rather than treated as the combined acceptance promise.
- Yellow seed8/mode1 with statues, keys, room sanity and gating enabled selects
  Sparky-to-Smash, not the isolated catalog's Cutter. Both policies are outside
  the bounded UFO witness; its historical native UFO policy is unchanged.

These changes do not turn any archive-generation test into a synthetic-policy
rule test, permit arbitrary acceptance/refusal outcomes, or relax a validator.
