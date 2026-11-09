# Stone and Burning starting-permission removal audit

Baseline: `1cdde1ad93897ed01e76398a3dc749dd2152591e`, 2026-11-08.

**Removal is blocked.** This change adds an all-check generation guard and its
regressions. It does not remove either starting item, change gateability, change
item classifications, or establish native ordinary-metal route soundness.

The acceptance requirement is every enabled check, not just the selected goal.
This applies to `minimal` too. No option value is silently rewritten, no enabled
location is dropped, and no ROM/runtime algorithm is changed.

## Coordinated dependencies

1. `enemy_ability_data.starting_copy_abilities` currently returns Beam, Burning,
   Stone in all three randomization modes. Once route coverage is accepted,
   new seeds must return only Beam. Keep `STARTING_COPY_ABILITIES` unchanged:
   it is the historical six-item receipt compatibility list, not the new-seed
   policy. The function's mode parameter is retained for existing callers.
2. `KirbyAmWorld.generate_early` precollects that policy and avoids duplicating
   explicit `start_inventory`. `Main` adds user-requested copies afterward.
   The same policy removes automatic copies from `create_items`; changing the
   policy returns Stone/Burning to the pool without changing total pool size.
   Gating off still removes all ability items from the pool. Explicit starting
   inventory is additive, so it does not itself remove an ordinary pooled item.
   This world does **not** expose `start_inventory_from_pool`; do not promise it.
3. `data/abilities.json` must mark Burning and Stone `safe_to_gate: true` together
   with removal. Otherwise the native grants remain unlocked despite having no
   starting inventory. Runtime IDs stay Burning=3 and Stone=8, and AP IDs stay
   3860103 and 3860108. The catalog drives `GATEABLE_ENEMY_COPY_ABILITIES`,
   `SourcePolicy` permission filtering, slot-data gate lists, ROM bootstrap gate
   masks, and client synchronization. There is no separate hard-coded C starting
   list that needs expansion or a native runtime rewrite for these permissions.
4. `data/items.json` must promote the newly logical permissions from USEFUL to
   PROGRESSION. `collect_item` tracks historical useful starts for compatibility,
   but useful items are not safely progression-filled. Throw and Missile are
   also USEFUL and not collected by the ordinary AP state: promoting only Stone
   and Burning is insufficient if a newly reviewed metal route can rely on
   Throw or Missile as its sole provider. Hammer, Smash and UFO already are
   progression. Promote any admitted required provider or do not credit it in
   logical witnesses. This is independent of native attack effectiveness.
5. `peg_traversal`, `traversal_rules`, Mini and Wheel installers share source
   acquisition and item permission semantics. Gating Stone/Burning affects
   existing peg/fuse carriers too. Recheck each exact witness, its independent
   `access_region`, hub/Area Key prerequisites, finite source consumption, and
   return path. A source type assigned an ability is not proof a reachable
   physical source exists. Copy Room access cannot justify a source behind a
   hub switch that itself needs that source.
6. `_ensure_starting_area_key` already counts actual early reachable checks and
   sweeps events; keep that behavior. New starting permissions may change its
   count and fallback key selection. Do not hard-code a replacement early count
   or restore Stone/Burning as a silent fallback.
7. `client._is_guaranteed_starting_ability_receipt` deliberately uses the
   historical list for tutorial receipt handling. Old seed slot-data lists must
   remain authoritative. Verify connection, cold ROM reset, save rollback,
   replayed ReceivedItems, and explicit new-seed starts without changing held
   Kirby equipment. Commit `242e3d7` now gives both client consumers the shared
   `resolve_slot_gateable_abilities` helper. Missing, empty or non-list values
   select the frozen 22-name `LEGACY_SLOT_GATEABLE_ABILITIES`, whose mask is
   `0x03fffe76`; future catalog expansion must not change it. A nonempty explicit
   list remains authoritative, with non-string entries filtered only after
   selection (`[None]` does not fall back). Keep the six historical receipt
   constants unchanged and rerun `test_legacy_ability_gate_list` alongside the
   reconnect/reset/receipt tests when expanding new-seed gateability.
8. The starting-item assertions in `test_starting_abilities`,
   `test_cutter_progression`, `test_mini_traversal`, `test_fuse_rope_traversal`,
   `test_all_minor_locations`, and generic traversal tests must be revised
   deliberately. Do not delete historical receipt tests. Update current-facing
   documentation and changelog statements claiming three starts/22 pooled
   abilities. Historical changelog entries remain historical.

## Why minimal needs an independent final guard

The baseline let typed minimal accessibility skip static source-assignment
rejection. Generation now explicitly requires all static source witnesses under
both accessibility modes using the existing bounded policy search. The AP fill
algorithm still permits
optional progression to remain unreachable once its selected goal is beatable.
These are two distinct failure modes:

- **Source/graph feasibility:** even granting every item does not open an enabled
  check under the chosen source assignment.
- **Actual progression:** an all-inventory state opens a check, but its required
  item is stranded behind itself or a cross-player dependency cycle.

A final `get_all_state` alone cannot catch the second case: the item pool remains
available to that helper after placement. `can_beat_game` and
`fulfills_accessibility` intentionally do not impose full checks on minimal.

The new `stage_pre_output` runs once for all Kirby players. `Main.main` calls all
worlds' `finalize_multiworld` after progression balancing, then all `pre_output`
hooks and stage hooks. Logical edits are forbidden during `pre_output`. This is
also before the `skip_output` return and before output workers create archives.
`post_fill` is too early because balancing has not yet happened. A single
Kirby instance's finalizer is too early because other finalizers may remain.

The guard constructs a fresh `CollectionState`, sweeps the **whole multiworld**
for reachable advancements using AP's existing fixed-point implementation, and
checks each enabled addressful Kirby location. It never grants the pool to this
state and does not mutate `multiworld.state`. Addressless events participate in
the sweep but are not checks themselves. Absent/disabled categories are not
invented. An excluded physical check still must be reachable: exclusion is a
fill preference, not removal of that check. Other games' optional checks do not
become mandatory, but their reachable deliveries can unlock Kirby checks.

On failure, an all-inventory diagnostic separates source/graph closures from
placed-progression closures, names the exact checks and player, and raises a
clear generation error before output. The current change does not retry fill or
rewrite source assignments. Automatic retries would need a separate bounded,
reproducible whole-fill strategy, especially with plando, item links and other
worlds' state; retrying only Kirby after shared fill would be unsound. A failure
is preferable to distributing a seed that violates the all-check requirement.
The same source-assignment filter now applies to full and minimal for useful
early rejection; final validation also catches cross-player placement dependencies.

This preserves the minimal option value but narrows which generated minimal
seeds are accepted. It does not make every formerly accepted minimal seed valid.
It cannot detect a native barrier missing from the AP graph. Ordinary-metal
coverage and controller evidence remain a separate release prerequisite.

## Reproducible baseline and outcome

`starting-permission-generation-audit.json` records all 36 baseline cases, exact
options, both unreachable-check lists, and measured audit durations. The seeds
are 105100, 105101, 105102. The matrix is:

- mode: off, shuffled, completely_random;
- gating: off/on;
- accessibility: full/minimal;
- profile 0: weight 0, statues/passive/minibosses/boss-spawns/rooms off, keys on;
- profile 1: weight 99, statues/minibosses/rooms on, passive/boss-spawns/keys off;
- profile 2: weight 100, all those toggles on.

All 36 passed the baseline's configured AP accessibility. Eighteen full cases
passed both stronger audits. Nine minimal cases passed, and nine did not:

| Seed | Mode | Gating | All-inventory closures | Actual-fill closures |
| --- | --- | --- | ---: | ---: |
| 105100 | shuffled | off | 0 | 21 |
| 105100 | completely_random | off | 0 | 21 |
| 105101 | shuffled | off | 11 | 11 |
| 105101 | shuffled | on | 11 | 11 |
| 105101 | completely_random | on | 0 | 1 |
| 105102 | shuffled | off | 12 | 51 |
| 105102 | off | on | 0 | 90 |
| 105102 | shuffled | on | 12 | 129 |
| 105102 | completely_random | on | 0 | 121 |

All rows use minimal. The artifact includes the closed reviewed traversal
identities and stranded progression-item placements for each failing case;
these distinguish source closures from missing Area Keys, permission items,
lever/hub access, and Copy Room dependencies. These are modeled reachability
findings, not claims that unreviewed native alternatives are impossible.

Concrete dependency examples:

- Seed 105100 has the Olive Area Key at Mustard First Visit and the Mustard Area
  Key at the Olive hub check, a two-area access cycle. Both assignments leave
  the same 21 checks stranded despite an all-inventory state reaching them.
- Seed 105101 shuffled leaves nine reviewed peg targets, the Mustard fuse route
  and the Wheel race rule closed at all inventory. The 11 inaccessible checks
  include peg chests and two Room Sanity checks. Its live-random/gating-on case
  instead has no all-inventory closures, but the Cabbage East Hub Connection is
  placed at the Olive Map chest and the actual progression cannot reach it.
- Seed 105102/gating-on variants strand Moonlight or Peppermint Area Keys,
  ordinary ability permissions and hub access items. In the shuffled case,
  the Moonlight Area Key is in Moonlight Goal 1, the Olive Area Key in the Olive
  Map chest, and the Candy Area Key at Olive's lever. The source assignment also
  closes ten reviewed peg routes and three fuse routes. The artifact retains
  the complete lists rather than reducing these overlapping causes to a count.

The smoke tests require all checks for accepted cases and a clear pre-output
rejection with no archive for any unsafe fill. Reusing the source filter repairs
three of the nine baseline failures: the final matrix accepts 30 cases and
clearly rejects six unsafe minimal fills. There is no xfail, silent failure
suppression, or claim that 36 seeds prove all seeds.
The independent audit helper's baseline median was 20.25 ms and maximum 116.11 ms
across 36 cases on this executor. It deliberately computes both diagnostic
states; the production success path needs only one shared progression sweep.

With source filtering and the final guard enabled, production audit time across
all 36 accepted/rejected cases was median 15.95 ms, maximum 151.95 ms. Source
selection was median 2.60 ms, maximum 208.02 ms; these samples required 1 to 51
candidate policies. The unchanged hard budget is 8,192 attempts and existing
budget regressions cover 1, 3 and the default limit. No new retry loop exists.
The full per-case measured results are in the artifact's `guarded_generation`.

### Improving generation success without changing other players

For the four baseline all-inventory failures, applying the existing source
filter while retaining minimal eliminates every theoretical closure. Three
then pass actual progression; seed 105102/gating-on still strands 39 checks.
The artifact records this controlled source-filter experiment separately.

In this AP version, `fill_restrictive` checks the item owner's accessibility
option directly and exposes no per-player force-access-check parameter.
`accessibility_corrections` deliberately exempts minimal-owned progression.
Calling these from `fill_hook` cannot override that behavior by itself. Avoid
mutating the option temporarily or replacing the shared fill algorithm. The
supported immediate choice is `full` for Kirby while leaving other players'
minimal settings intact. Retaining minimal means accepting the explicit
fail-closed behavior until a bounded, reproducible whole-fill retry is designed.
Safety rejection is not completion of the starting-removal goal, nor a promise
that every option/seed combination will generate.

## Release acceptance matrix

Before removing the guarantees, complete every layer below. More random seeds
cannot replace any missing native or structural proof.

1. **Native coverage:** account for every F5 barrier, every directed entry and
   protected AP target, including untagged minor chests. Record a reviewed Normal
   bypass or an exact source-backed attack witness. Audit F7/environmental
   mechanisms separately. Test directions, water startup/contact, Throw capture
   and object consumption, UFO charging, room instance/reset semantics, and
   paths to acquire or return with the ability. Preserve unchanged Normal and
   reinforced Heave-Ho alternatives.
2. **Source/permission structure:** for every admitted graph test permission
   alone, absent source, source behind its barrier, inaccessible independent
   carrier, wrong entry/direction/water, consumed shared object, weight 100 empty
   enemy output, excluded categories, statue policy, and all required AP guards.
   Test finite nonrenewable live-random sources separately from documented
   repeatable positive-support sources. Eventual stochastic availability is not
   a bounded completion guarantee; a zero-probability provider must never pass.
3. **Core option product:** all 2,304 combinations of modes `{0,1,2}`, gating
   `{0,1}`, accessibility `{full,minimal}`, no-ability weight `{0,99,100}`, and
   the six booleans statues/passive/minibosses/boss-spawns/Area Keys/Room Sanity.
   Test each accepted policy against the structural witness contract, generated
   pool, exact bootstrap token, slot data, actual progression audit, and no
   forced Stone/Burning. Unsupported sampled assignments may fail clearly; they
   must not emit unsafe output. Fixed seed sampling of this product remains
   integration coverage, not a proof over the shuffled seed space.
4. **Orthogonal options:** for each mode/gating/accessibility combination cover
   goals dark_mind/defeat_any_area_boss/each configured area boss/boss-count 1 and 8;
   shard placement vanilla/random; maps-start off/on; health/trap boundary pools;
   excluded/priority checks and all disabled location categories. Verify early
   Area Key fallback and unchanged item/location cardinality. Source access
   cannot be justified solely by already satisfying a short goal.
5. **Inventory/protocol:** each mode/gating choice with zero explicit starts,
   explicit Stone only, Burning only, both, multiplicities 1 and 3, and unrelated
   starts. Exact counts, stable IDs, collected/removed permissions, pool counts,
   slot gate list, ROM bits 3/8 and reconnect histories must agree. Gating off
   omits pooled ability unlocks while physical acquisition remains necessary.
6. **Multiworld:** mixed modes/gating/accessibility, explicit starts in one slot,
   progression balancing on/off, valid remote unlock chains, deliberate
   same-player and cross-player self-locks, item links, and remote unreachable
   optional checks. Both normal archive generation and skip_output must run the
   guard after every finalizer. Assert no global state/option mutation.
7. **Final gates:** focused tests, full Kirby suite, syntax/lint/type checks,
   generated-token/packaged-world checks, exact-commit CI, native acceptance for
   activated routes, and measured hot-path/one-time audit cost. Retain full
   failing-seed evidence for safe generation errors.

## Alternate-source release plan at 7633065

This checkpoint retains Beam/Burning/Stone starts. Seven metal target rows
(557, 176, three directed 141 routes and two 742 checks) and frozen 825 use
`requires_guaranteed_source`. When that condition is false,
`traversal_rules.target_applies` skips the reviewed rule and preserves the
legacy permissive rule. These fallbacks cannot survive starting removal.
Making them unconditional without alternatives would instead reject many
ordinary shuffled or mixed live-random policies. The final AP check audit
cannot detect a missing native barrier.

The smallest reusable design is to add reviewed statue-carry graphs to each
existing target row, then remove its applicability condition once the complete
alternative set is sound. Graphs within one row are OR alternatives; separate
rows on the same target would combine as AND rules. Reuse
`ordinary_hub_statues` and `statues_970`, cached graph compilation, actual source
identities, permission filtering, independent access regions and exact route
guards. Start carriers in Normal; owning an ability item does not equip Kirby.

Ordinary hubs expose 15 distinct statue slots, with native Burning in 291/592
and Ice in 290, but no native Smash. Copy Room 970 exposes all 19 slots,
including Smash, behind the progression item `Copy Ability Room Access`.
Its direct Central mirror does not require every hub switch. The reviewed
970-to-Central retained-ability transition can be shared, but each onward
approach still needs its own proof. Shuffled statues need not contain every
required ability. Live statue retouch uses its existing documented contract;
enemy weight 100 cannot produce a missing enemy ability.

Prioritize the missing physical suffixes:

1. **742:** reuse the retained-Burning 790/706/707 carrier, whose native capture
   reaches 712. Explicitly represent its actual 712 arrival before composition;
   its current graph terminal alone is not a downstream handoff contract.
   Prove 712 through 741 to the same clean lower-742 entry without consuming the
   randomized Flamer. Reuse the accepted same-visit bank/chest/Warp suffix.
2. **141:** prove imported Burning through the actual 543 lower entry for both
   forward targets and the 545 upper entry for the reverse target. Preserve
   equipment through approach and bomb interactions. Existing local Flamer
   captures do not prove these imported arrivals or a safe reverse return.
3. **557/176:** bring Smash/Burning through the real 556/175 approaches and
   defeat/release the arena while retaining that ability, without swallowing a
   wrongly assigned Master Hand/Batafire. Post-defeat attack captures alone do
   not establish this combined combat-and-carry path. Burning at 557 would be a
   useful common alternative, but is not accepted by generic metal capability.
4. **825:** carry statue Ice through the actual 831 lower entrance, retain it
   through Frosty combat/release, and preserve the finite Waddle Dee at
   `0x088CD318` for the frozen projectile. No Pengy carrier is inferred.

The 825 change has a coordinated item-classification dependency:
`goal2_ice_is_progression` currently requires guaranteed Frosty Ice. An accepted
unconditional statue-Ice alternative must promote Ice whenever that enabled
target needs its gated permission, independent of Frosty's assignment. Add
regressions for enabled 825 + gating + non-Ice Frosty + a real reachable statue
Ice source, absent Ice permission, source behind the chest, missing source
access, disabled target category and gating off. Include an actual progression
fill and a self-lock rejection, not only an all-inventory graph test. Do not
change this predicate before the carrier is accepted.

Do not replace these obligations with enemy-renewal flags or a larger policy
budget. Native `FillLevelInfo` resets room state on reentry only when no other
Kirby occupies the destination; ordinary solo includes three independently
roaming CPU Kirbies (decompilation `7d969fb`).
Existing captures do not prove wrong-grant exit/reentry or hold-L reacquisition.
Mini needs a safe disposal/resize opportunity; Sleep needs a survivable wait
until ordinary controls return. A room reset cannot fix zero output support or
reroll a static shuffled assignment.

After each accepted carrier, test local-or-statue alternatives under fixed,
shuffled and live policies, excluded categories, weight 100, missing guards,
equipment loss and source consumption. Keep the existing bounded source filter
and final shared progression sweep. Report rejected policies separately from
accepted generation, and run the release matrix above after all coordinated
catalog, starting-policy and classification changes. This plan is research,
not implemented carrier coverage or a generation-success guarantee.

## Remaining blockers

- Ordinary-metal directed coverage is incomplete, including targets absent from
  the compact token list. The inventory of 33 F5 rooms/358 tiles is not a route
  proof. Do not enable removal from that count alone.
- New sole Throw/Missile logical providers need classification review.
- Source/graph correctness under the final catalog must be validated before
  declaring the all-check audit a guarantee about native play.
- The full 2,304-case option product, orthogonal option matrix, item-link matrix,
  and combined native acceptance for ordinary-metal routes have not been run by
  this audit. The 36 baseline cases are explicitly a smoke matrix.
- Future inventory removal will require updating the compatibility assertions
  and metadata listed above. This branch intentionally retains starting Stone
  and Burning until those prerequisites are satisfied.
