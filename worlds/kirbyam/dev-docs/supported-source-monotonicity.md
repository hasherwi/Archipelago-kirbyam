# Supported source-policy monotonicity boundary

The general traversal evaluator is **not monotone for arbitrary narrowed live
ability pools**. With a finite Hammer/Stone pool, owning only Hammer can filter
its support to a guaranteed Hammer. Adding Stone can remove that guarantee.
The equivalent Smash/Burning example affects a finite Master Hand witness.
AP region caching assumes monotone reachability, so injecting these custom
policies into installed rules can cache a now-invalid crossing and even collect
an item that unlocks an independent alternative. Permanent OR alternatives do
not, by themselves, repair that problem.

## Why the current supported options do not permit that example

1. `KirbyAmWorld.generate_early` uses the default `VALID_ENEMY_COPY_ABILITIES`
   whitelist for both the initial draw and whole-policy redraw. There is no
   public whitelist/ability-pool option. Source-category switches change which
   native objects are randomized, not the live pool. Beam is in this default
   pool and is not gateable, independently of its automatic inventory item.
2. A nonempty live randomized enemy grant therefore always includes Beam.
   Positive Normal weight can additionally prevent certainty; weight 100 gives
   no live enemy ability. Randomized statues ignore enemy Normal weight and
   exclude Mini, but retain Beam. A finite live source cannot become a
   guaranteed metal, peg, fuse, rope, Wheel, Mini or frozen-enemy provider just
   because only one such permission is owned.
3. The combined catalog has three dry Beam-accepting witnesses: the optional
   538 crossover, the Chocolate chest's Beam entry and the Carrot Room13 Beam
   entry. The first requires a raw Waddle Doo-to-Beam singleton on its graph.
   The latter two have narrowly scoped target conditions that require a raw
   singleton Waddle Doo assignment before any rule is installed. These tests
   evaluate raw source policy with every permission available, never the
   transient permission-filtered live grant. A supported mixed live pool cannot
   activate those conditional witnesses merely by starting with Beam alone.
   Swimming Water Gun at `underwater_819_exit/local` succeeds without sources.
   The separate110 swimming spray also uses Normal, after an exact finite Knight
   mouth-payload route. Its capture/spit does not depend on the randomized pending
   ability. It cannot create a live copy guarantee or ordinary projectile stock.
   Ranged movement edges additionally retain their explicit carried-equipment
   guards. Their raw source conditions and fixed assignments do not disappear
   when source expansion is deduplicated.
4. Both recovery-required edges are Mini corridors. Original Minny remains
   invariant under all public source switches; raw Mini recovery is the special
   native Mini contract, not the growing general live pool.
5. Off/shuffled or excluded-source grants have fixed single assignments. Added
   permission can enable that fixed assignment but does not replace it with
   other outcomes. Documented renewable retries expose eligible outcomes as
   alternatives; adding permission retains the previously eligible choices.

These facts give the combined installed catalog a monotone target-reachability argument,
not a claim that every intermediate equipment-state set is monotone. A finite
Beam-containing uncertain grant cannot supply a previously missing reviewed
ability gate. Its ordinary traversal can instead be performed without taking
that source, preserving at least as many unspent physical objects.

## Regression scope

`test_supported_source_monotonicity.py` pins the public builder call sites,
Beam's pool/gate status, every compiled capability/recovery edge, and all 48
live source-switch/statue/Normal-weight combinations. It separately exercises
finite goal witnesses and static assignments. A bounded installed205/209/210
AP fixture compares cached and fresh states after adding Stone, with a hub
connection behind its own target. Neither state may bootstrap that connection;
independently obtaining it must enable the real permanent Stone alternative.
These are structural/logical tests, not new native gameplay or full-seed proofs.

A future custom-pool option, Beam gate, unguarded Beam-dependent route, new
recovery edge or different finite-source semantics requires a new soundness review and
may require evaluator redesign. The narrowed custom-policy issue must not be
silently treated as fixed by this release's public-option invariant.

## Complete enumerated catalog

`supported-source-monotonicity-catalog.json` records all 144 installed witnesses,
288 compiled Area Key variants and 108 distinct physical source/key identities.
It includes logical subregions, per-witness finite/renewable variants, capability providers,
water dispatch, raw target/graph source conditions, carried-equipment guards,
and every capability/recovery edge. Source hashes identify the
reviewed code/data. Tests compare the saved enumeration against the authoritative
compiled catalog rather than counting only raw top-level room definitions.

## Installed custom-policy counterexample, outside supported generation

Independent bounded AP replay installed the complete production room 205 target
with all its OR alternatives and the actual 205/209/210 compartment edges. It
then replaced the generated policy with a custom live Hammer/Stone whitelist.
Starting with Hammer permission and Rainbow East connection made the finite
Bonkers path true. After adding Stone permission, its direct entrance rule was
false, but AP's cached top-region and chest reachability remained true. A fresh
state with identical items correctly reported both false.

Placing Peppermint East connection in that top chest demonstrated a real bootstrap:
the cached state collected it and thereby enabled the independent permanent
Stone alternative; the fresh state could not collect it. Repeating the same
bounded setup with the unchanged supported generated pool kept both cached and
fresh states blocked throughout. The regression above preserves this supported
no-bootstrap contrast and its independently enabled positive control.

A second custom Master Hand Smash/Burning replay made the installed chest rule
true with Smash alone and false after Burning was added. The supported generated
pool was false in both states. These are actual installed-rule counterexamples
to general custom-pool monotonicity, not generated seeds, and not evidence of a
supported public-option exploit. Client compatibility with custom/older slot
policies does not turn those policies into supported generation configurations.
