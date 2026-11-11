# Starting inventory for conditional traversal permissions

This is a host generation lifecycle correction, not new native route evidence.
`Main.main` creates explicit `start_inventory` items after `generate_early` but
before `create_regions`. Ice's Goal 2 chest condition, Crash's Twister-only
Mustard map condition and the Missile, Parasol, Spark and Ice Chocolate chest conditions
inspect actual locations. Before those locations exist, each can legitimately
return false and create a useful item. CollectionState does not count such an
item as an owned permission even when its target later becomes enabled.

After Kirby's regions are created, the world rechecks only precollected Ice,
Crash, Missile, Parasol, Magic and Spark items that are not already advancement items. It uses
the existing item factory to reevaluate each unchanged source, gating and actual
location predicate. If the item is now progression, the original precollected
instance receives that classification and is collected into the existing state
once. Fresh states subsequently collect the corrected precollected instances.
Already-progression items are not recollected, and duplicate starting items
retain their requested multiplicity.

No helper predicate or route is widened. Missing/disabled targets, unsupported
source policies and gating-off cases retain their existing classifications.
Fighter, unconditional progression items and unrelated useful items are
not included. Foley and Hot Head Crash paths already classify before regions;
they do not gain extra copies during reconciliation.

Tests run real full generation for native Frosty→Ice, the normal full-pool seed
15 Twister→Crash, seed 5 Doo→Missile and seed 29 Doo→Parasol assignments with
explicit starting items. They check the state immediately after region creation,
fresh-state ownership, multiplicity, removal, filled locations, beatability and
full accessibility. Controlled lifecycle tests remove the actual target before
reconciliation or use disabled categories, gating off and wrong source policies.
These fixtures are distinct from native source/carry acceptance. The supported
option tested here is `start_inventory`; no claim is made for options the world
does not expose.

Magic uses the same lifecycle for the enabled Room15 to Room16 entrance and raw
guaranteed Foley source. Its existing safe-to-gate policy is unchanged. Before
regions exist it remains useful; after the entrance exists it becomes progression
only with gating on and guaranteed Magic. Tests cover absent targets, unsupported
source policies, explicit multiplicity, preexisting progression and full seed 12
generation. Other useful abilities remain outside this reconciliation.

Spark and Ice additionally use this lifecycle for the enabled Chocolate chest
and the raw guaranteed original Waddle Doo assignment. Full-pool seeds 22 and
149 isolate those new promotion reasons from the existing Sparky and Frosty
conditions. Tests cover disabled minor chests, gating off, mixed or failable
source pools, preexisting progression, duplicate starting items and full 1 HP
generation. Spark's earlier Sparky condition and Ice's earlier Frosty condition
remain independent reasons for promotion; permission never supplies equipment.
