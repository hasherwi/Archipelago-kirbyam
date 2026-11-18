# Generated source activation and lifetime (#1118)

Generated inventory candidates require an evidenced activation edge before they
can be acquired. Permission and reaching the source compartment do not activate
it. The carry solver tracks active and expired output lifetimes separately from
held equipment and finite consumption. Ending a lifetime prevents acquisition,
but does not erase equipment already swallowed. A room-instance reset clears
activation; explicit revival only permits subsequent generation. It does not
manufacture a live object. An activation cannot revive an expired output or
recycle a consumed finite instance.

Finite generated consumption now survives a generic room reset, even when
the output was swallowed without an explicit expiry edge. Only revival of that
specific lifetime clears its consumption. Revival of a different output does
not help. Ordinary placement reset behavior is unchanged. This closes the
reset-plus-activation bypass without treating a surviving held ability as lost.
Cross-room travel also drops live-output activation unless the route explicitly
preserves the room instance. Unknown retention cannot certify a projectile is
still there on return; held equipment remains independent.
Activation and revival must enter the output's native room; one output lifetime
cannot span native rooms, and one consumption identity cannot alias incompatible
lifetimes. These checks reject remote activation and reset bookkeeping aliases
without adding access to any room.

Native `level.c` room loading reuses another Kirby's room slot if it remains
occupied. A newly allocated slot clears room-local object bits and room-local
state, not the session/world banks used by `sub_080027E8`. Door travel alone
therefore cannot certify recreation. Native predicate evidence and a physical
return route remain separate requirements; no RNG reroll guarantee follows.

The lifetime identity is the generated output record, not its parent placement.
Native `sub_080AA6F8` destroys the random-statue controller after creating two
independent statues. Ordinary spawner construction likewise does not attach the
child to the controller. Controller defeat therefore cannot universally mean
child destruction. For attached projectiles, `object.c:sub_0809F840` destroys the
child when its parent is destroyed or has zero HP, except while the child's
`unkC & 0x400` interaction flag is set. No held-object exception or unreviewed
phase transition is admitted by this change; a graph must evidence its explicit
expiry edge. Separate generated phases and outputs retain separate identities.

All 37 object-spawner prototypes now record decoded counter-bank and threshold,
delay, startup timer and capacity predicates from the pinned
`asm/object_spawner.s`, plus its 32-slot global search bound. The search falls
through after exhaustion; safe exhaustion behavior is not certified. Actual
counter state and physical acquisition paths remain unresolved. All 37 have
capacity one and no destroyed-slot reclamation;
none supplies an unlimited retry guarantee. These native predicates are data,
not automatically satisfied AP requirements.

Spawner counter prerequisites now link to candidate contributors in the same
native room. Bank 0 increments on `ObjectDestroy` only for table-1 types 0–100,
with template flag `0x22 & 1`, nonpositive HP and an assigned room slot. Bank 1
uses qualifying bonus collection or chest callbacks; ordinary enemy defeat is
not a substitute. Native dynamic bonuses with state `(0, 31)` do not contribute
through `BonusSetFunc`. Generated boss templates carry flags 5, so their defeats
can contribute to a later spawner; ordinary spawner children carry flags 0.
These are conditional events, not satisfied prerequisites. Outputs whose nonzero
counter prerequisite has only encounter-defeat contributors are Advanced-only
(including the post-Boxy spawners); ordinary spawners are not all classified as
encounter attacks. Runtime chest contents and ownership remain conditions. The production
`ap_on_chest_popup_room_counter` hook suppresses physical AP lever pulls and
AP-owned ordinary bonus popups; fixed collection rewards retain their increment.
`ap_update_lever_wall` applies the wall item's contribution once per room instance,
including a live item delivery. Existing executable chest/lever lifecycle tests
cover these branches. Thus collecting an AP lever is not wall ownership, and an
output unlocked by collecting a chest cannot establish access to that same chest. Both counters clear when
`level.c` allocates a new room slot; entering a room occupied by another Kirby
reuses its slot and counters. Leaving and returning does not by itself prove a
reset, respawn, or safe retry. Extractor input hashes include these native files.

The two room951 random-statue slots preserve all 19 native selections. A fixed
selection is evaluated using every alternative's actual runtime SourcePolicy
grant. One convenient possible branch cannot become a guarantee; an empty or
unowned branch remains a failure outcome. Explicitly witnessed retouch may be
renewable, but cannot reroll the native selection. Live runtime randomness and
native branch selection are separate; no branch retry is admitted. A documented
safe retouch may retry a Completely Random runtime draw only when every fixed
native choice has the identical randomized grant contract. This requires the
existing opt-in retry setting and does not become a finite guarantee. Mixed
fixed/randomized outcomes or differing branch contracts remain non-retryable.

`generated-statue-live-retry-acceptance.json` verifies this distinction with a
paired local fixture. Ten contacts preserve both native statue objects and
their selected indices. With the production live statue mask for Ice/Beam,
contacts yield both abilities; with that mask deliberately disabled the same
static table assignment stays Ice. Every recorded drop returns to Normal and
all contacts retain 6 HP. This verifies per-touch runtime variability, not a
finite guarantee, native-selector reroll, or Adventure access to room951.

`generated-statue-native-acceptance.json` records four fresh blank-battery checks.
From a configured lower-floor arrival, vanilla contact grants Beam, dropping it
and retouching the same statue grants Beam again, and singleton shuffled contact
and retouch grant Cutter. Unowned gated Cutter grants nothing. Both outputs have
no parent attachment and persist after their controller disappears. The upper
platform fixture cannot contact them. Room951 is the Boss Endurance rest room,
not an Adventure source. No room-reset selection or Adventure route is inferred.

`generated-frosty-native-acceptance.json` binds the original room955 Frosty's
small-cube call at `src/mr_frosty.c:762`. With singleton shuffled Cutter, the
player acquires Cutter at frame1752 while Frosty remains alive at 30 HP. The
cube is attached to that Frosty; its vanilla native grant is Normal. Vanilla and
unowned gated Cutter controls do not acquire an ability during the matched
1765-frame checks. Each starts at 6 HP and takes one hit. This is a conditional
local acquisition witness, not a safe one-hit-mode or independent world route.
Room955 is a dedicated Boss Endurance encounter, so this fixture does not install
Adventure access either. Encounter-generated sources remain Advanced-only, including normally empty
projectiles that become eligible through the actual runtime configuration.

The inventory preserves dedicated Boss Endurance rooms 950, 951, 955, 956, 957
and 969 with `world_access.status = outside_adventure`. Production Adventure
graph compilation rejects their sources; isolated mechanics fixtures can still
join their native records. Adventure's Copy Ability Room970 and shared boss
arenas are not excluded. The initializer, Boss Challenge Door destination table
and boss-clear return handling are documented in
[`native-room-wikirby-map.md`](native-room-wikirby-map.md#native-969-boss-endurance-nonparticipant-holding-room).
The existing native menu checks in `goal-game-evidence.json` separately verify
inactive AP context in Boss Endurance. An unmapped room alone is not evidence
of exclusion; only the six specifically identified rooms receive this status.

## Adventure Frosty investigation

`generated-frosty825-native-acceptance.json` records nine fresh cold fixtures
from the reviewed room825 lower arrival, starting Normal. A Normal air puff
opens the lower star-block passage; flight reaches the arena. The selected
timing acquires the small cube while the original Frosty retains full HP.
Four 1 HP shuffled-Ice cases cover enemy health 100/500% and gating off/on;
a live-random singleton-Ice case also succeeds. Vanilla, unowned gated Ice
and 100% no-ability controls stay Normal, while the wrong-grant control gains
Beam. All nine retain 1 HP through the matched 1729-frame endpoint. Gated
ownership uses only the production client's guarded startup configuration.

This is conditional acquisition evidence, not an installed target. Five tested
arrival delays fail before acquisition; the previously reviewed Ice combat
controller also fails to compose safely with this new lineage. No large-cube
acquisition, generic attack selection, combat suffix, repeatability or reset
guarantee follows from these observations.

All eight Frosty cube candidates now include the source-hash-bound conditional
native contract. The wind-up callback chooses one of three attack callbacks,
each invokes `sub_080CCEE0`, and its nonzero/zero `RandLessThan3()` branches
create small/large cubes. Both use the same actual runtime source key, but
their size, collision and trajectory differ. Parent animation, collision and
parent-expiry callbacks limit lifetime. The preceding idle attack selection
is random and is not certified to enter this wind-up in a finite bound.

These records certify the shared mechanics and bounded observations. They do
not certify all 731 encounter candidates, all branch predicates, phase changes,
controller defeat sequences, room-reset revival or safe repeatability. Unproved
candidates remain unresolved and add no automatic world access. No new world
entrance or target graph is installed from a configured native fixture. Existing
Normal witnesses and the paused #1059 playthrough are preserved.

## Bonkers nut branches

All 16 Bonkers nut candidates now share a hash-bound review of
`bonkers.c:BonkersNutAttack`, `BonkersThrowNut`, `CreateBonkersNut` and
`BonkersNutFly`. The throwing animation's `header.unk1 == 0x44` calls the
constructor; `RandLessThan3()` selects small versus large. Both attach to the
creating Bonkers and use `sub_0809F840` parent expiry. They allow one floor
collision bounce; the next floor collision or the wall collision mask destroys
the nut. The large variant has different bounds and half the horizontal launch
and bounce speeds. Neither branch proves a safe acquisition or repeatable
attack entry. These facts cover 16 candidates, not 16 newly accessible sources.

Both native types currently grant Normal and have no configured source key.
Tests verify that maximally enabled production policies in all three modes
neither patch their copy-table entries nor enable their live source bits. They
remain in the comprehensive physical inventory but cannot silently become
random ability grants. Changing runtime eligibility would require revisiting
this contract. No world route or retry guarantee is installed from this review.
