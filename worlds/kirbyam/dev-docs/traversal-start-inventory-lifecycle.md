# Starting inventory for conditional traversal permissions

This is a host generation lifecycle correction, not new native route evidence.
`Main.main` creates explicit `start_inventory` items after `generate_early` but
before `create_regions`. Ice's Goal 2 chest condition, Crash's Twister-only
Mustard map condition and Missile's Chocolate chest condition inspect actual
locations. Before those locations exist, each can legitimately return false
and create a useful item. CollectionState does not count such an item as an
owned permission even when its target later becomes enabled.

After Kirby's regions are created, the world rechecks only precollected Ice,
Crash and Missile items that are not already advancement items. It uses the
existing item factory to reevaluate each unchanged source, gating and actual
location predicate. If the item is now progression, the original precollected
instance receives that classification and is collected into the existing state
once. Fresh states subsequently collect the corrected precollected instances.
Already-progression items are not recollected, and duplicate starting items
retain their requested multiplicity.

No helper predicate or route is widened. Missing/disabled targets, unsupported
source policies and gating-off cases retain their existing classifications.
Spark, Fighter, unconditional progression items and unrelated useful items are
not included. Foley and Hot Head Crash paths already classify before regions;
they do not gain extra copies during reconciliation.

Tests run real full generation for native Frosty→Ice, the normal full-pool
seed 15 Twister→Crash assignment and seed 5 Doo→Missile assignment with
explicit starting items. They check the state immediately after region creation,
fresh-state ownership, multiplicity, removal, filled locations, beatability and
full accessibility. Controlled lifecycle tests remove the actual target before
reconciliation or use disabled categories, gating off and wrong source policies.
These fixtures are distinct from native source/carry acceptance. The supported
option tested here is `start_inventory`; no claim is made for options the world
does not expose.
