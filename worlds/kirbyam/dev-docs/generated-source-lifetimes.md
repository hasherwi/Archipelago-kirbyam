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

## Bombar activation and paired missiles

Three static Bombar placements now record the native waiting callback's
live-Bombar-relative rectangle and target restrictions. Room membership alone
is insufficient. The room232 record's offsets are `(-24,-48,240,144)` relative
to Bombar at `(136,48)`. All 12 Bombar output candidates have source-hash-bound
conditional generation/lifetime contracts. The bomb helper creates one object;
the missile helper creates two simultaneous objects at separate offsets. A
random subtype is shared by both missiles and changes their homing speed cap.
Constructor-call counts do not certify allocation success when the global
32-slot template pool is exhausted.
The 256-tick behavior counter switches to the trail callback after a velocity
condition; it is not an expiry timer. Both types retain native parent expiry.
Attack entry, contact, defeat, reset and repeatability remain separate questions.

`generated-bombar232-native-observations.json` records three fresh local fixtures.
The stationary control remains outside the activation boundary and the boss
stays in its waiting callback. Walking into the rectangle activates the boss.
The longer activated sequence takes three hits. Two native Missile objects
enter intake together before Parasol appears; that observation cannot certify
an individual source's grant. A later single-missile intake yields Missile.
These observations show why a paired attack cannot be reduced to an assumed
safe single-source pickup. They do not certify a one-HP route, other timings,
health settings, randomization policies, or independently reachable entry.
A one-HP retreat variant dies at frame1672 before acquiring an ability; its
later healthy respawn is not counted as success. No production traversal graph
is installed from these fixtures.

## Shared static miniboss activation predicates

The same review now covers all 36 static placements of the eight miniboss types.
Each record pins its own native callback and file hash, plus `include/object.h`.
Frosty, Bonkers, Phan Phan, Box Boxer and Boxy anchor the test to the template
position. Batafire, Master Hand and Bombar anchor it to the live controller.
These anchors must not be interchanged if a waiting controller moves.

The pinned `sub_08039430` assembly checks the selected target's **integer origin**,
not its collision hitbox. Its arguments are signed left/top offsets and unsigned
width/height. After native fixed-point coordinates are shifted right by eight,
the accepted ranges are `left-1 <= x <= left+width` and
`top-1 <= y <= top+height`. Earlier Bombar metadata called this a hitbox
intersection; that description is corrected. Room232's parameter tuple remains
`(-24,-48,240,144)`: with the observed Bombar position, x111 is the inclusive
left boundary and x352 the right boundary. Room equality and the selected
target's `unkC & 0x8000` restriction are separate conditions.

This batch binds activation facts to physical identities without making them
AP access rules. It does not imply a reachable entry, an attack choice, an
output, a swallow opportunity, or a safe repeat. Spawner-produced miniboss
instances retain their separate generated-template and counter prerequisites.

## Complete encounter runtime eligibility boundary

A batch check now covers all 731 candidate records against the production
assignment boundary. Of these, 300 records across 32 native types have no
configured source key; none receives a copy-table patch or live-source bit
under maximally enabled vanilla, shuffled or Completely Random policies in the
three regression seeds. All 300 are rejected when presented as direct ability
sources, even with an invented grant key and activation/lifetime evidence.
The remaining 431 candidates have configured keys, which still require actual
policy grants, ownership, activation and physical acquisition evidence.

This partition is not an interaction or reachability classification. In
particular, 33 Dark Mind Star Mix candidates retain their native `Wait` effect;
the check does not turn mixing into Normal or certify a mix result. Unconfigured
projectiles, effects and controller objects remain in the inventory. Runtime
eligibility changes must update this regression and revisit the associated
physical contracts. No candidate gains a traversal edge from this batch.

## Boxy present and contents branches

All 36 Boxy candidates now bind to the reviewed native file and exact call site.
The present's three trajectory subtypes are selected before construction. After
its first bounce, opening depends on another floor contact and the selected
target's horizontal distance, or exhaustion of its ground-contact counter. The
480 counter is not a wall-clock expiry. Opening starts a separate 60 counter;
contents are chosen at 52, and the present expires at zero.

The content selector produces mutually exclusive food/battery, Minny/Prank Bomb,
or Prank Bomb branches. Minny requires no tracked Minny and controller template
flag8 clear. The two Prank Bomb call sites retain distinct predicates despite
sharing a runtime key. The present attaches to Boxy with native parent expiry;
Prank Bomb attaches to the present, while the helper does not attach Minny,
food or battery. Child expiry still requires the child's callback evidence.

These contracts establish neither a favorable content branch nor safe repeated
acquisition. No source, carry route or retry guarantee is installed from them.
The existing per-output lifetime model remains necessary: defeating Boxy,
opening a present and destroying its contents are different events.

## Dark Mind mirror enemy selection and cleanup

The three native `DarkMindForm2CreateRandomEnemies` call sites now have shared
hash-bound contracts across their 253 root/call/output candidates. Their actual
controller is a Form2 mirror, not whichever root happens to share the source
file. Root-to-phase access remains unresolved. A mirror sweep starts its counter
at 36 and emits one selected enemy at each of 22, 16 and 10, provided the
parent's `unk12E` flag is clear.

The contracts retain repeated entries in the native selection tables. The
first event samples indices 0–9; its UFO at index10 requires selecting Wheelie
and a second random check. It is not an ordinary eleventh equally selected
outcome. Different alternatives at one event cannot all be acquired from that
single event. The three events also occur at different positions/times.

The construction macro does not attach these ordinary enemies to the mirror.
Form2 tracks three enemy pointers and `sub_0810CBE8` marks each for destruction,
except while interaction flag0x400 is set. `ObjectMain` processes that mark;
this differs from attached-projectile parent expiry. The exception does not
prove safe swallowing or survival across a phase. Neither entry into the sweep,
contact, cleanup timing, phase transitions nor repeatability is admitted as a
world route by this metadata.

## Room-local reset scope

A certified room reset now clears ordinary-source consumption only for physical
identities whose recorded compartments all belong to the destination native
room. Previously it cleared every ordinary consumption identity in the graph,
allowing a reset elsewhere followed by return travel to recreate a spent source
without evidence that its own room reset. Remote, unknown and cross-room aliased
identities retain consumption. Generated identities additionally retain the
explicit revival requirement. Acquired equipment is unchanged by this correction.
Positive and negative graph tests cover both gating modes, reset of the actual
source room, reset elsewhere, and unresolved identities.

The inventory join also prevents a room reset from clearing session/world
spawn-state consumption. Native `sub_080027E8` reads bank0 from the room slot,
bank1 from `gUnk_02023368` and bank2 from `gUnk_02028BF0`; `level.c` clears only
the room bank when allocating a slot. `ObjectDestroy` can retain the bit after
defeat (including Cookin and Jack). All ten configured static sources with
persistent-bank predicates now compile with `room_reset_respawns = false`, and
a caller cannot override that physical contract. The other reviewed source
contracts keep their existing behavior. This is not a claim that a source can
never return under a separately proved session/world reset, nor a grant of
renewability or new world access.

The 143 Dark Mind star/bomb candidates also retain conditional native contracts.
Star color selection depends on Form1 subtype: subtype0 is red only, subtype1
adds blue, subtype2 adds purple, and other subtypes permit the native Mix type.
One helper creates two separately selected stars; the other two create one.
Their behavior differs: the bouncing pair has a 128 counter, the linear variant
checks `unk58 & 0x200`, and the waiting variant releases in response to parent
phase changes. Release is not expiry. Bombs use parent expiry but their initial
200 counter advances on floor contact and begins a rising phase at zero, rather
than expiring. None of these facts proves root-to-phase entry, a favorable branch,
a safe swallow or repeatability; native Mix remains outside direct ability grants.

## Remaining configured encounter generation contracts

All 431 candidates with configured runtime keys now have at least a hash-bound,
conditional generation contract. This is a generation-fact denominator, not an
access, safe-acquisition or complete-lifetime denominator. The remaining batch
covers 26 records (including Moley's two unconfigured alternatives): Master/Crazy
Hand bullets, King Golem's three golem types, Kracko's three enemy branches,
Gobbler's tracked baby slots, Moley's seven possible objects, and six configured
Wiz outputs.

The hand helpers have different firing animation predicates but share the
bullet constructor in `crazy_hand.c`; both files are pinned for Master Hand.
King Golem's rejected random value and subtype0x80 child initialization are
preserved, with `golem.c` pinned separately. Kracko uses two conditional random
draws, not three freely available sources. Moley's selection retains rock/screw
outcomes even though they are not configured grants. Wiz's ten-way selector
includes football/balloon branches and secondary binary choices; its outputs
cannot be treated as one convenient guaranteed grant. Gobbler has three tracked
slots with separate counter events rather than an unlimited always-live baby.

Initial parent-expiry callbacks are recorded where reviewed. Wiz's Bronto Burt
child expiry remains explicitly unreviewed; parent attachment alone is not a
callback. Later phase lifetimes, safe contact, root access and repeatability
remain unresolved throughout this batch. No production target is added.

King Golem's child source additionally requires the boss's HP to be at most half
the native multiplayer health-table value, the random/`unk85` attack branch, and
an empty tracked-enemy slot. Merely entering the arena at full boss health does
not satisfy this. The child's custom destructor clears that slot, but does not
prove another favorable attack or safe reacquisition. The threshold remains an
expression tied to the actual runtime health table, not a hard-coded HP value.

`generated-king-golem710-native-observations.json` binds six fresh local fixtures.
The full-health control never produces a golem. The damage-and-copy sequence
uses Normal rock spits to reach 30 HP out of 60, then observes the original
controller create type31, its single-object intake and the resulting ability.
Vanilla yields Stone; owned shuffled Ice and singleton live Ice yield Ice;
unowned Ice and 100% no-ability controls remain Normal. All damage-and-copy
fixtures retain at least 3 HP, and the original boss remains alive at 30 HP.
The swallowed object's native ability field is Stone even in the shuffled case;
the production swallow hook correctly restores the configured Ice assignment.

These observations do not certify a one-HP route, other health settings or
arrivals, other golem variants, arena entry, boss defeat, exit carry, reset or
repeatability. No target graph is installed. Negative fixtures continue past
the positive fixtures' first grant; comparison uses the common frame3645
endpoint as well as each recorded full trace. The controller's literal30-HP
input switch belongs only to this 100%-health fixture; production metadata
keeps the native health-table expression.

## Separately observed finite occurrences

An encounter inventory record describes a native output prototype. A reviewed
fixture may distinguish successive physical occurrences with `generation_instance`
and `instance_evidence`. The resulting consumption and lifetime identity appends
`/instance:<name>` to the prototype ID. Each occurrence still needs its own
activation, generation, lifetime and acquisition evidence. Naming an occurrence
neither spawns it nor establishes its attack branch or a safe retry.

A graph cannot mix implicit and named occurrences of one prototype, give one
occurrence multiple consumption identities, or share a consumption identity
between occurrences. Ordinary placements and non-reclaiming spawners cannot
use named occurrences to multiply their supply. A finite second occurrence can
therefore support reacquisition only after its separately evidenced activation;
room travel, loss of equipment and reactivating a spent occurrence cannot
manufacture it. These schema tests install no new world route.
