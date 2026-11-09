# Native205/209/210: separate arrivals and sufficient check routes

This checkpoint removes the coarse209 shortcut between the205 floor exit, both
210 entrances and the208 bottom entrance. It preserves all four item-check IDs,
the three physical RoomSanity IDs/bits, and a singleton check sink for each split
native room. A sink has no outgoing edge and cannot connect compartments.

The starting Stone/Burning permissions remain unchanged. The remaining ordinary
metal coverage and source-policy gaps still block their removal.

## Directed check ownership

- `ROOM_7_CHEST` is209 TOP. It owns minor23, object0x088BF3C8, location3960587.
  Only the205 floor route enters it. Its sole physical egress is205 WATER_RETURN.
- `ROOM_7_CHEST__LOGIC__BOTTOM_MINOR` receives the exact208 entrance and owns
  minor24, object0x088BF3EC, location3960588. It does not grant TOP or map access.
- `ROOM_7_CHEST__LOGIC__UPPER_ENTRY` receives the Bonkers-side210 door. It leads
  through Mirra only to210's separate Snow hallway.
- `ROOM_7_05__LOGIC__SNOW_HALL` owns Snow Paint, object0x088BF610,
  location3960504. It leads only to209 LOWER_MAP, not210 main/Bonkers/205.
- `ROOM_7_CHEST__LOGIC__LOWER_MAP` owns the map, object0x088BF338,
  location3960202. It is the terminal result of the accepted Normal Bomb route.
- `ROOM_7_07__LOGIC__WATER_RETURN` is the post-floor water pocket reached by
 209's top return. It has a reviewed directed exit to native203/ROOM_7_11 only.
  It does not directly grant205 main or every outer exit.

There are no cannon objects in209. Earlier exploratory descriptions mistook
ordinary food pickups for cannons. The optional lower-return door, bottom-to-map
far-switch alternative, and internal TOP/UPPER/BOTTOM joins remain omitted. This
is a sufficient-check model, not proof those omitted paths are impossible.

## One target, two reviewed ability paths

`metal_205_to_209_top` is fail closed and has four OR graphs, not four
independently ANDed target rows. A finite Bonkers-Hammer branch and three
renewable statue-backed Stone starts share the same exact205 exit and209 top
check. Unsupported assignments remain closed; no source or option is rewritten.

### Finite Bonkers and retained Hammer

The graph starts only with independently reached205 outer access. Shared part
`metal_205_bonkers_approach` follows actual205 door10,18 into210, then the
controller-proven Normal ladder/right-shaft approach to Bonkers. Native source
0x088BF730, type0x39, is finite and resolved through `SourcePolicy`. Permission
is not equipment, and neither an inaccessible source nor an unused fixture
statue can equip Hammer. There is no retry or respawn credit.

The [source contract](ordinary-205-source-carrier-contract.md) retains the
world's existing ordinary miniboss-combat assumption. Native defeat increments
room slot2 and releases the matching scroll lock. Actual boss defeat and capture
were not replayed as one controller chain. The suffix fixture discloses its
Bonkers-to-Hammer essence substitution and relocated scroll lock.

After acquisition, the real210 return door leads to205's lower dry arrival.
The accepted carrier climbs to the dry floor launch at350.121,120.996. Two low
aerial swings, each A1/release8/B1/wait60, clear all four F5 cells x21..22/y8..9.
Higher A6 timing failed. The atomic Hammer edge includes the subsequent swim
around the shelf, final underwater Hammer attack and immediate door approach.
Thus a free drop cannot substitute Normal for the required water continuation.
Only the final doorway transition is outside that atomic move. No destruction
state is exported through a room reload.

Actual209 top entry and Up collection set flag23 mask128 in both default and500%
enemy-health traces. Hammer is retained. The Normal return trace is a separate
alternative, not a claim that Hammer must be dropped. Before another target such
as228 reuses this finite Bonkers, it needs a joint retained-Hammer itinerary or
a separately proved source-reset contract; independent target success is not
evidence of unlimited reacquisition.

### Renewable Stone, actual Box Boxer combat and guarded hub access

Central Circle, independently reached native190 and independently reached290
are alternative Normal starts. Each reuses the full `ordinary_hub_statues`
part, preserving every physical source identity, directed connection/key guard,
and documented permanent-statue retouch assumption. Native190 Stone is object
`0x088B7CEC`, `STATUE:353900`. The minimal native-source route requires Rainbow
Route East and Peppermint Palace East connections, plus the Peppermint Area Key
when enabled. It does not require every hub, the Copy Ability Room or a West
connection. A statue randomized to another ability only helps if its actual
resolved policy can supply Stone and the guarded route reaches it.

The [imported-Stone trace](ordinary-205-imported-stone-acceptance.json) validates
actual290→210→205→209. Its original290 Ice statue `0x088C0ED0` is changed from
type0x93/subtype1 to type0x92/subtype4 only to supply imported equipment. Production
keeps that source as `STATUE:353905`, native Ice. The real190 acquisition and hub
prefix remain at their existing source/geometry evidence level, not a fabricated
full190-to-check controller replay.

The lower210 route encounters a real Box Boxer boundary. Unlike the layered
Bonkers fixture, this trace defeats the actual Box Boxer `0x088BF7E4`, observes
HP reaching zero, and ascends through the former y128 clamp. The matching slot1
scroll lock `0x088BF5EC` is unchanged. Kirby keeps Stone while waiting transformed,
untransforming with safe separation, rising and timing successive Stone drops.
After defeat, a600-frame transformed wait avoids the defeated body before ascent.
No artificial release, source replacement inside210, dropped-star recovery or
reacquisition is credited.

The actual210 upper door reaches205's lower dry arrival. At approximately
350.383,120.996, dry B transformation breaks both rows of the floor plug and
continues into water. The atomic Stone action includes untransforming without
dropping the ability, swimming around the shelf, repeated water-gun interception
of Blipper, and the door-side Bomb approach. The final actual209 transition and
Up collection set flag23 mask128 while retaining Stone. Starting Stone while
already swimming is not accepted, and the separate upper F5 obstacle is unused.

Default and500% fresh runs audit8,097 and19,542 post-boot frames respectively,
with no HP decrease and continuous Stone8 after acquisition. The500% scaler
includes Box Boxer's dedicated health row: single-human runtime HP40→200,
not merely the generic enemy metadata. These are sufficient adaptive input
sequences, not a claim that the default fixed timing works at every durability.

Mixed finite live Bonkers outcomes still cannot guarantee Hammer. Excluded
statues retain native Stone; included live statues use the existing explicit
positive-support retouch assumption. Enemy no-ability weight does not remove a
statue's eligible outcome. Thus the default mixed-live boss setting retains a
reviewed renewable basis without inventing enemy respawn. Deterministic shuffled
policies lacking both paths are rejected by the existing bounded whole-policy
feasibility process, rather than silently changing user options. Final placed-
item reachability remains a separate generation guard.

## Normal upper entry, Snow and map

`normal_210_to_209_upper` reuses the independent205 arena approach, without
acquiring any copy. It does not treat every coarse210 arrival as proven arena
access. The [post-defeat doorway fixture](ordinary-210-bonkers-side209-entrance.json)
remains Normal and never touches its unused Hammer essence.

The Bonkers scroll-lock release does not itself reveal the door. An air puff
activates Bomb(29,12), whose chain changes cells29,12/13/14 from241/242/242 to
0/0/255. Native `mirror_door.c` subtype1 observes the door collision attribute
0x4000. Actual door0x888D00 reaches209 at24,136.996, precisely matching the
next fixture. Default and500% each audit642 post-boot frames without damage.

The [Normal loop](ordinary-209-snow-map-loop-acceptance.json) uses a native star
block from outside Mirra's close reaction range, takes actual209 door1,13 to210
Snow Hall, collects Snow flag25 mask2, then takes actual210 door29,28 to209's
lower arrival at24,312.996. Bomb(4,17) opens the map shaft through delayed
propagation. Bomb(15,23) stays241 throughout; a historical segment name does
not mean it activated. Actual Up sets map flag22 mask64. Both runs audit2,714
post-boot frames, Normal6HP throughout. No cross-room Bomb persistence or
generic210 join is needed. Snow and map are collected together in this trace.

## Actual bottom entrance and bounded top return

`normal_208_to_209_bottom` requires independent290/ROOM_7_HUB_1 access. The
[bottom proof](ordinary-208-bottom209-minor24-acceptance.json) starts beside its
208 door, takes actual290→208 and208→209 transitions, then collects minor24
flag mask1. Both default and500% audit1,253 post-boot frames with Normal6HP and
no damage. The fixture does not provide the hub connection or Area Key items.

TOP's return takes the actual209→205 water doorway. The reviewed Normal
[Bomb-shaft egress](ordinary-205-normal-return-egress.json) leaves both F5 banks
intact. Its [continuation](ordinary-205-water-return-outer-join.json) follows the
left corridor and actual205 door1,2 to203 live936,72.996, another919 damage-free
frames at each durability. The alternate lower210 attempt failed at500% and
is not credited. There is no unqualified WATER_RETURN→205-main edge.

## Evidence boundaries and checks

All500% fixtures use the pinned production health-table scaler once before fresh
boot. These are source-equivalent native fixtures, not full AP/server sessions
or direct1HP gameplay. Continuous zero-loss traces plus the existing Normal and
Hammer health-independent movement/attack analysis support the bounded positive
HP paths. The Bonkers branch retains its explicit ordinary boss-combat assumption; the
Stone branch instead replays actual Box Boxer combat. For Stone, pinned native
`kirby.c` dry dispatch index8 selects `sub_0805E304`; transformation/holding/fall/
untransform states through `sub_0805F428` use input, collision, timers and fixed
speeds without a positive-HP predicate. Swimming index8 selects Normal water gun
`sub_0805A4EC`, preserving equipment. The existing health-scope analysis separates
Fighter's one-HP projectile from these moves. Stone-form immunity is ordinary
ability behavior, not hit invulnerability or damage tanking. This source argument
plus the continuous zero-loss traces supports positive Kirby HP; it is not a
direct AP one-HP or arbitrary multiplayer replay.

Regression tests cover exact source identity/finite consumption, source behind
its target, missing permission and independent entry, narrowed dry Hammer move,
terminal/mutation semantics, actual doorway and collection readbacks, no
bottom/top or hallway/main alias, item self-locks, stable IDs, generated mapping
and slot-data snapshots. The graph part is compiled once through the existing
catalog cache. No new kernel feature or persistent reachability cache is added.


## Bounded evaluation and generation checks

[The paired benchmark](ordinary-205-kernel-benchmark.json) records full-result
cost with the existing source-expansion deduplication. Each expanded Stone graph
has20 nodes,34 routes and30 renewable placements:292 native states and454 full-
live states. Five warmed samples measured1.26–1.43ms/native and2.76–3.01ms/live;
the same-run707 control had452 live states at2.42ms. The finite Bonkers graph has
six nodes/five routes and12 native states at25 microseconds. No source outcomes
are pruned and no persistent inventory/reachability cache is introduced.

The full source-expansion reference-equivalence matrix includes every current
catalog graph and source/gating/retry/Area-Key combination. The36-case generation
matrix produced32 all-check-reachable archives and4 correctly refused unsafe
minimal fills; there were no unsupported-source-policy failures. This is bounded
regression evidence with current starting abilities, not all-seed or all-native-
route certification. Exact check ownership, native mapping generator output,
slot snapshots and physical RoomSanity IDs/bits are also tested.
