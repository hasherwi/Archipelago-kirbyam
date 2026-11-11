# Ranged-attack coverage ledger

This is the broad scope of PR #1052, not a claim that all ranged logic is
implemented. The current source-backed subset includes:

- Five Bomb Block targets described in `bounded-bomb-implementation.md`, including
  dry Spark and underwater Sword for Rainbow110, selective Rainbow Green Paint,
  Carrot Yellow Paint, ten separate Cabbage Chocolate alternatives (Beam, Smash,
  Fire, Missile, Parasol, Spark, Ice, Sword, Fighter and UFO), and
  Beam/Fighter/Sword/Fire for the Carrot lower Room13 entry.
- Conditional 533 small-switch alternatives: Bomb, UFO, Crash and bounded Magic
  Meta Knight. Each has its own `mustard-room15-*-source-witness.md` record;
  the original Bomb record is `mustard-room15-source-witness.md`.
- Conditional 310 map alternatives: UFO, Crash, Cupid and Cutter, documented in their
  `mustard-map-*-source-witness.md` records.
- The finite-source conditional 825 UFO alternative in `olive-sound-effects-ufo.md`.
- An optional, fail-closed native538 Beam left exit from VERTICAL directly to
  Rainbow39/native537, documented in `rainbow-beam538-source-witness.md`. It
  adds no reverse crossover, direct539 route or mandatory Beam requirement. The
  separate health supplement covers32 nativeHP1/2/4 tuples with one tested
  percentage each, without claiming all phases or upstream1HP composition.

- An ordinary Normal large-star alternative for native 177 Goal 3 chest, documented
  in `rainbow-normal177-source-witness.md`. This preserves its existing null
  rule and adds no generic Normal capability or copied-ability requirement.

- An ordinary staged Normal alternative for native 426's Candy map, documented in
  `candy-normal426-source-witness.md`. The qualified near-door 419 transition and
  map collection preserve the null rule without gating RoomSanity or the exit.

The move-family catalog below identifies candidates. It does not grant an
ability, arbitrary range, collision equivalence or a complete route.

## AP ownership census

`tools/build_ranged_target_coverage.py` reads production-normalized `data.regions` rather than a parallel raw-room loader. After integration with the source-aware metal traversal baseline it covers 382 regions, including 352 mapped native definitions (322 parents and 30 logical compartments), area/other connectivity and synthetic RoomSanity sinks. It records 384 uniquely owned locations, including 263 RoomSanity checks, and 1,083 location/exit surfaces. All 57 current traversal target definitions bind to exact normalized surfaces. These counts describe AP structure, **not** the number of attack-dependent targets.

Generated JSON includes SHA-256 hashes of the normalizer, every data JSON and native mapping. Tests cover moved location ownership, nested Mustard Mini/Fuse targets, Carrot's overridden compartment entrance, area adjacency and RoomSanity sinks. RoomSanity is recorded separately and must not inherit a chest/exit attack gate.

The 35 small switches in 24 rooms are an exhaustive static template inventory under `small-switch-inventory.json`'s stated scope. They are not 35 proved ranged routes. The static census below extends physical coverage; dynamic effects and exact check associations remain in progress.

## Move-family checklist

Source review: native `1197474f80e5de282fbedcd0025ebfa61f61a764`, compared to the existing report's `7d969fbce14fdc838d2c1ea01389717fb96c3189`. The examined Normal/UFO/Cupid blocks differ only by a three-line include offset and symbol/type renames; Magic also changes secondary-Kirby pointer spelling. Exact prior anchors remain in `collision-avoiding-attack-ranges.md`. This checklist is not exhaustive animation-frame or multiplayer acceptance.

| Ability/family | Distinct actions and limits to preserve |
| --- | --- |
| Normal | Inhale; payload-dependent ordinary/large spit stars; air puff; water spray; body actions. Not Copy Ability ownership. |
| Fire | Held breath, directional boost/aim, near-mouth tile-only effect. Damage and tile bounds differ. |
| Ice | Breath versus frozen-enemy kick and size variants; kick has no direct tile scanner. |
| Burning | Body-attached effect; movement collision limits attack origin. |
| Wheel | Body-attached effect, not independent ranged travel. |
| Parasol | Swing, held and attached states; tile flag only in particular states. |
| Cutter | Launch, outward, return and rebound; initial terrain-bypass flag is temporary. |
| Beam | Actual sweep versus visual effects; envelope is not a filled rectangle. |
| Stone | Transformation/body effect, not a traveling projectile. |
| Bomb | Held, aimed throw, flight and detonation; terrain-sensitive flight versus local wall-overlapping blast. |
| Throw | Payload, ordinary/large/angled launch and tile halo. Halo has no damage hitbox. |
| Sleep | No independent ranged attack identified; do not assume Normal actions remain available asleep. |
| Cook | Screen capture; no tile scanner; small-switch category rejected. |
| Laser | Straight and slope-reflected paths; terrain-sensitive. |
| UFO | Whip, low-charge laser, medium shot and top-charge shot are four distinct paths. |
| Spark | Attached short-range field, target-specific rectangles. |
| Tornado | Attached damage effect; audited effect lacks tile flag, other body paths not exhaustively excluded. |
| Hammer | Local weapon/animation overlap and target category. |
| Sword | Attached attacks, including the exact110 underwater spin, versus landing wave and its separate setup. |
| Cupid | Aim, charge, ground/air and charged triple-arrow release; ballistic terrain-sensitive paths. |
| Fighter | Melee, ordinary wave, charged wave and 1HP wave; only 1HP wave has reviewed terrain bypass. |
| Magic | Conversion, invincibility and Meta Knight outcomes; different category/space/eligibility. |
| Smash | Hammer/Sword effects, Final Cutter/landing wave and Stone-like effect. |
| Mini | No independent ranged effect identified; shared Normal actions not universally excluded. |
| Crash | Viewport-wide effect, switch-compatible category, no tile scanner. |
| Missile | Kirby movement versus detonation; blast overlap does not imply piercing flight. |
| Master | Melee, landing wave and charged wave; distinct lifetime/setup. |
| Wait | AP metadata27 is non-enemy-copy, non-gateable internal metadata, not a native combat ability. Native count ends at Master26. Client hides Wait; do not invent a provider. |
| Environment/helpers | Foley drop/explosion, movable blocks and helper contact require their own setup and timing. Foley also supplies default Bomb, a separate source-policy-dependent acquisition path. |

### Additional pinned source anchors

All anchors below refer to native1197474. Their category-mask compatibility is not a complete collision-dispatch or route witness.

- `src/code_0806F780.c:1931–2027`: Normal star, category0x40 strength3, damage±12 versus tile scan±2, launch8px ahead,4px/update. Qualifying destructible terrain exception is not ordinary-wall piercing. Large-star variant differs in object-hit termination. Ground/water release calls `kirby.c:12350–12362,14166`.
- `src/code_0806F780.c:2093–2179`: air puff, category0x40 strength2, damage±5 versus tile scan±2,3.75px/update then deceleration; terrain/object sensitive.
- `src/code_0806F780.c:4997–5043`: UFO low-charge laser,8px/update, damage±6×±3 versus tile scan±1; distinct launch/cancellation owner.
- `src/kirby.c:20685–20719`, `code_0806F780.c:7052–7100`: Cupid charge≥0x30 releases three arrows with successively reduced charge, not identical trajectories.
- `src/code_0806F780.c:7963–8076`: Magic Meta Knight has moving viewport-height
  damage, category 0x2000, and no terrain query/tile-scan flag in the examined
  update. This source anchor alone did not establish switch contact. The later
  frozen v4 Room15 witness proves the exact local callback and timed 533 to 325
  route; other targets, poses, outcomes and alternate-mode behavior remain unproved.
- `src/foley.c:142–156,237–242`, `code_0806F780.c:2497–2522,2653–2674`: nearby Kirby triggers drop, landing creates category0x40 explosion, damage±20 with animation eligibility and no tile scanner. Not Bomb equivalence.

## Target namespaces and live investigation

Keep ordinary Bomb Block0xF1 and selective0xF6 filters separate. Small and big switches have different masks/player handling. Small switches also accept overlapping star-stone/large-star-stone objects (`big_small_switch.c:135–197`). Fuses admit categories0x100/0x10000 (`cannon_fuse.c:39–53,603–610`). Star-stone objects have strength4 resistance and physical behavior (`star_stone_block.c:14–37`); they are not background tiles. Destroyable rock blocks use Kirby position/state/delay (`destroyable_rock_block.c:13–64`), not an inferred attack from their name. Animated door opening is not completed traversal.

Three coarse `can_hit_far_switch` surfaces currently remain in this branch: Mustard Chest310, Mustard15/native533→Mustard16/native325, and Peppermint Chest209. They must not become blanket ability gates:

- 310 has a solid intervening wall and near-zero release timer. The guaranteed
  TWISTER → UFO subset uses the complete Normal Hub4/native 590 → 534 approach,
  finite Twister acquisition and UFO carry into 310. The room-specific top-charge
  combat, switch shot and timed crossing reach chest 39/map 4 without damage at
  50/100/450/451/462/463/500% enemy health; matched 100/500% no-final-charge
  controls remain blocked. Only `MAJOR_CHEST_MUSTARD_MOUNTAIN` is gated; return
  exit, Area-Key entry and RoomSanity are unchanged. See
  `mustard-map-ufo-source-witness.md` and `mustard-map-ufo-acceptance.json`.
  Later Crash, Cupid and Cutter records add their own complete OR graphs on this same
  target, preserving each source, attack, timing and health boundary. Unsupported
  source policies, arbitrary arrivals and Phone/helper alternatives remain unproved.
- 533 has a solid/elevation obstacle. Environmental Foley explosion is separate
  from acquiring its default Bomb and placing a delayed bomb. Guaranteed
  FOLEY → Bomb uses the complete no-damage Hub4 → 534 → 533 acquisition,
  placement and 325 crossing at 100%/500% enemy health, with matched controls.
  Guaranteed FOLEY → UFO proves a separate top-charge shot and crossing under
  production assignment-table fixtures, with no-shot/low-laser/medium-shot
  controls. Later independent Crash and Magic records add complete OR graphs on
  this same target, summarized below. Unsupported source assignments retain
  prior behavior. Environmental Foley contact and other attack alternatives
  remain unproved.
- 209 is a dependency on **published** PR #1051 head177d765: `ordinary-209-snow-map-loop-acceptance.json` proves a qualified upper210-arrival Normal route through Snow and the first Bomb chain to the map, with100%/500% enemy-health variants. It does not prove arbitrary209 entry joins. Do not duplicate that coarse placeholder as a ranged requirement or import unrelated unpublished #1051 work.

147 is calibration only: ordinary timed traversal is an alternative, so a ranged witness alone does not justify a mandatory AP gate. Further work must inspect all actual target/check associations, enemy-health/interception, source randomization, 1HP/no-damage movement, precise entry compartments and matched controls.

For future Phone/ranged alternatives on the same AP surface, use alternative witness graphs inside **one target row** (OR). Separate installed rows combine through `add_rule` as AND and must not accidentally require both Phone and a solo attack.

## Cabbage Chocolate chest Smash alternative

`bomb_517_chocolate` gained a separate guaranteed WADDLE_DOO → Smash graph
alongside Beam within one OR target row. Later Fire, Missile and Parasol
alternatives have their own evidence below. The production
seed173 route starts Normal at actual Hub2/native591 entry, consumes the finite
native Doo0x088CA04C, carries Smash and opens F1(14,7) with rising Up+B at3129.
The seven linked F2 cells then clear by3179. Physical chest57 records
0x088CA0B8 and the actual client produces LocationChecks3960511 locally; native
spray11 remains suppressed by the AP-owned reward hook. Four replays cover
HP1/6 × enemy100/500% without damage or ability loss, with exact-window and
full-route no-target-attack negatives. The only RAM writes are the eight logged
initial client configuration writes before movement, not gameplay injection.

Only `MINOR_CHEST_SPRAY_PAINT_12` gains this alternative. Independent Hub2
access remains required, gating-on needs Smash permission, and the existing
Beam proof is unchanged. Live-random multi-outcome or failure-weighted grants
from the finite source do not gain an eventual-draw promise. Other entry sides or exits,
RoomSanity reachability, arbitrary health interpolation and global Smash
collision equivalence remain unproved. This Smash evidence adds no Carrot route;
Carrot now has separate Beam, Fighter and Sword witnesses on its lower entry.
See `cabbage-smash-source-witness.md` and `cabbage-smash-source-runtime.json`.

## Rainbow110 underwater Sword alternative

The same `bomb_110_room9` target and exact110→554 AP exit now have two OR
graphs: unchanged dry Spark and distinct attached underwater Sword spin.
Original finite Sword Knight0x088B74CC is acquired while Normal. The original
five runs use independent108 lower-mid access and a startup-reproduced decoded
upper arrival, without replaying the incoming door. A separate actual-entry
supplement now covers that door, source, target and554 exit continuously at100%
enemy health and actual1HP, still requiring exact lower-mid access. Medium-aware
carry reaches F1(13,57) with Kirby0x69/weapon0x6F variant1, clears through solid column12, and physically
crosses to554 with Sword intact. This is not landing wave or a general range.

Five native-assignment/gating-off production replays cover actual1HP at enemy
50/100/500% and actual6HP at100/500%. Three matched1HP controls omit only the
exact target attack and stay sealed in110; no gameplay writes or state restores.
These are discrete tested values, not every supported health setting. Logic
source-policy equivalence and gating-on tests are separate from native coverage.
Applicability is guaranteed SPARKY→Spark OR SWORD_KNIGHT→Sword, validated only
for this target/owner/exit. Neither finite mixed pools nor failure-weighted
randomness gains a retry guarantee. Other exits, RoomSanity and the target
count are unchanged by this alternative. See `rainbow-route-8-sword-witness.md` and
`rainbow-route-8-sword-runtime.json`; the additional actual-door record is
`rainbow-route-8-sword-entry-runtime.json`.

## Rainbow Green Paint selective lower trigger

`bomb_138_green` gates only `MINOR_CHEST_SPRAY_PAINT_04` in Room28/native138
for guaranteed SPARKY→Spark. Independent Room27 UPPER_LEFT/native532 access,
Normal arrival, finite original Sparky acquisition and intact carry are required.
A 300-frame clearing pause precedes the selective lower F1 (36,13) attack;
upper F1 (37,12) stays intact through physical chest collection and client check
3960503. Four natural-mode, gating-off cold boots cover actual HP1/6 × enemy
100%/500%, with no damage or ability loss. Matched no-attack and both-trigger
controls fail to collect. The latter is not a strict upper-first control.

Enemy health supports 50–500%; 50–99% and 101–499% were not replayed.
Guaranteed same-Spark randomized assignments and gating-on behavior have logic
tests, not new native acceptance. Unsupported source assignments retain the
prior partial pattern. The existing Room8 Spark progression condition already
covers this source policy even with optional paint disabled. Other checks,
exits, RoomSanity and Area Keys are unchanged; no global F1/Spark equivalence
or finite random-source retry guarantee is introduced. See
`rainbow-green-source-witness.md` and `rainbow-green-source-runtime.json`.

## Carrot Yellow Paint: two-source UFO route

`bomb_733_yellow` gates only `MINOR_CHEST_SPRAY_PAINT_02` /3960501 in
Room16/native733 for guaranteed SPARKY→UFO. Independent Room14/native720
access is required. Existing719→720 labels remain unchanged and currently
permissive. A separate Normal170-door→719→720 segment is now verified, but
not all170 arrivals or its timing composition with the Yellow route. The native witness joins
720 far right→734 upper→720 left→730 top as Normal, without either720-left
bomb-chain cell activating. No generic719 or circular734 entry is assumed.

Two distinct finite original730 Sparkies are required: upper0x088D4FC0 supplies
UFO through the maze/Gordo, then intentional discard permits the Normal ladder,
and lower0x088D4F9C supplies the UFO carried into733. A separate dry top-charge
capability opens only lowerF1(21,6), leaving upper(18,2) intact through physical
chest0x088D3DD0 and real-client check3960501. Equipment guards constrain actual
carry, not inventory or underwater attack substitution.

Four new Normal ingress runs and12 complete runs cover actualHP1/6 × enemy
100%/500%, with top160-frame charge success and matched no-shot/medium controls.
Production seed8 uses the normal25-ability shuffled pool. Eight initial real-client
configuration writes precede movement; no gameplay writes, restores, helpers or
server transmissions occur. The earlier12 left-arrival cases remain separately
qualified. These are discrete health settings, not interpolation or an exhaustive
ordinary-route impossibility claim. Unsupported assignments retain the prior
partial behavior. Gating-on, statues, Area Keys, optional paint and full1HP fills
are separate logic tests. No other exit, compartment, RoomSanity or source pool
changes; future qualified Phone alternatives belong as OR graphs on this target.
See `carrot-yellow-ufo-source-witness.md` and `carrot-yellow-ufo-source-runtime.json`.
The separate ordinary segment is retained in `carrot-yellow-ufo-upstream-witness.md`
and `carrot-yellow-ufo-upstream-runtime.json`; it does not change any AP rule.

## Extended static target census

`ranged-static-target-census.json` pins the original USA ROM and independent extraction artifacts. All983room slots were checked:286populated,697exact unused sentinels,286unique collision maps and293,674cells. There are403initialF1cells in125rooms and14initialF6cells in13rooms. All417target cells have exactly one matching listed mutation record; no listed kind1/2 replacement creates anotherF1/F6. Dimensions were derived through the foreground-map metadata and all decoded lengths agree. Seven synthetic RLE tests, all13previous evidence-room dimensions/F1positions and all943cells of the independent533decoder agree.

The namespace-aware object scan covers287static lists and3,482templates, all table1 in this ROM. It finds35small switches,15big switches,4cannon fuses,14hammer pegs (matching the14F6positions),22CPU triggers and the distinct movable/large-block types. All37static ObjectSpawner target types are enemy/midboss types, not these switch/block families. The retained type histogram is broader than the focused barrier subset. These counts do not cover arbitrary runtime constructors, establish attack eligibility or assign a physical obstacle to every AP check.

F6rooms are149,204,218,221,401,411,509,510,513,527(two),605,741and816. The hammer-peg object watchesF6change; that does not prove everyF6 accepts every attack. The census records native-room/AP-key joins only. Exact compartment entry, barriers, check dependencies and ordinary alternatives must still be resolved before further rules.

### Reconciled F6 ownership

All14initialF6positions reconcile with the existing peg audit in `docs/traversal-logic.md`:11are represented by room-owned peg targets, while native218(9,33) and509(32,2) gate non-AP food/battery pockets and741(27,13) gates a loose1-Up rather than an AP exit. These three must not become new room or exit gates. Existing11peg targets preserve their individually reviewed compartments/source alternatives; the full tile census adds no new global ranged provider. This reconciles static target ownership, not every possible attack variant or carrying route.

### Reconciled cannon-fuse ownership

The four static cannon fuses are native126,323,502 and827. Each already has a room-owned fuse target: respectively Rainbow32→33Left, Mustard13 CANNON_LEFT→14 CANNON_LEFT, Radish16→17, and Olive7→5 ENTRY_FROM_6_07. The normalized ledger retains those precise compartments. Their existing source-backed alternatives and ignition category rules are not generalized to small switches or F1/F6. Physical fuse coverage is complete for the static lists; extra attack variants still require their own source/carry, ignition and cannon-entry proof.

### Published ordinary-route context, not new ranged acceptance

PR #1051's published `ordinary-metal-role-review.json` at commit424b9e262b4e39dac30101fa678af7cca70786a5 records useful exclusions:414's Bomb Block alternate leads to a loose1-Up rather than an AP check;533's separate Bomb Blocks release Gordos and are not its AP exit gate;529's visible Bomb/pit alternatives still need directed mapping;532's return Bomb near(10,8) reconnects the cannon network, with reverse entry separate. These are qualified map-role notes, not a complete native F1 chain inventory or new ranged proof. The533 switch witness here must not be confused with533's separate Bomb Block hazards. No unpublished #1051 candidate is imported.

## Mustard Room15 Crash alternative

The existing `switch_533_room16` row now also OR-composes guaranteed
FOLEY→Crash with its unchanged Bomb and UFO witnesses. The full normal
25-ability pool, shuffled seed 29, assigns the original finite Foley to Crash.
The complete independent Hub4 → 534 → 533 approach acquires it, carries it to
the witnessed camera-valid pose, consumes it to Normal, then completes the
timed gate crossing and actual 325 arrival. Crash permission is progression
only when this source condition applies and ability gating is enabled.

Four native positives cover actual 1 HP and 6 HP at discrete 100% and 500%
enemy health. No-trigger and offscreen controls are qualified at 1 HP only.
Native fixtures use gating and area keys off; host tests cover permissions,
world binding and full fills separately. No persistent switch credit,
whole-room effect, arbitrary camera pose, other target, environmental Foley
explosion or Phone/helper equivalence is granted. See
`mustard-room15-crash-source-witness.md` and the compact acceptance manifest.

## Olive Sound Effects: finite Frosty UFO alternative

`frozen_825_sound_effects` now OR-composes guaranteed singleton MR_FROSTY→UFO
with its unchanged Ice graph on the same optional Sound Effects chest,
`MINOR_CHEST_MUSIC_NOTE_10` /3960523 in ROOM_6_GOAL_2/native825. Independent
ROOM_6_14/native831 access starts at its verified bottom-left arrival from its
sole normalized incoming ROOM_6_12/native814. Normal crosses the complete
current/spike maze and physically enters825 at the lower arrival. The startup814
right-door fixture does not establish arbitrary814 arrival or traversal.

The original finite Frosty is defeated with Normal's native ammunition and
swallowed to acquire UFO, then carried to the exact dry top-charge firing pose.
The shot activates the timed small switch; physical gate crossing and chest66
collection follow. Separate interception runs show damage18 kills WaddleHP2/10
and the identical live shot continues to the switch. No persistent switch credit,
renewable source, frozen-Waddle payload, generic UFO attack or other-target
ranged equivalence is granted. UFO's existing progression classification and
Ice's original source-qualified promotion remain unchanged.

The original ten endpoint runs remain separately qualified to the831 door
alcove. Eight continuous814→831→825 runs cover actual HP1/6 × enemy100/500,
positive and matched no-target-attack controls. Two further cold attribution runs
identify all3/15 Frosty hits and the activating beam as player0-parented. These
are discrete endpoints, not a health continuum. Native fixtures use gating and
keys off; host policy, permission, optional-chest, statue, key and full1HP fill
tests are separate. Only eight fenced startup client writes occur; no gameplay
writes, restores, Phone/shoulder or multiplayer inputs. Other Kirbys are autonomous
offscreen actors:101 at100%, moving101→106 in long500% runs, never814/831/825;
no helper route projectile or source contribution is credited. Client check capture
is local, not server submission. Unsupported assignments retain partial behavior.
See `olive-sound-effects-ufo.md` and its separate endpoint/composition JSON records.

## Carrot Room7: bounded Fighter first combo

`bomb_719_room13` now has a same-row Fighter OR witness from independent
Room5/native170 through finite original lower Waddle Doo. Only guaranteed
singleton WADDLE_DOO→Beam/Fighter enables this target. The new dry719 capability
is the exact left-facing ordinary first combo at86,232.996, separate from Beam
and from HP1 waves. HP1 special-wave and HP6 charged-wave carry are independently
replayed at enemy100/500; only the final combo is HP-independent. Eight matched
positive/control runs and four tile audits establish only actual lower734
ENTRY_FROM_5_07. No Secret Notes, other exit, general734 or reward credit.
Conditional Fighter progression supplies the enforced permission without changing
gating-off useful classification. See `carrot-room7-fighter-witness.md` and
`carrot-room7-fighter-acceptance.json`. Other ranged families remain partial.

## Rainbow Room32 Crash fuse alternative

`fuse_126` additionally accepts a separate finite HOT_HEAD→Crash witness from
qualified lower native126 entry. The Normal approach, camera-valid ignition,
consumption, early Normal cannon entry and actual570 arrival are covered by
HP1/6 ×100%/500% positive/no-trigger cold runs and two attribution runs.
See `rainbow-room32-crash-source-witness.md` and its compact acceptance JSON.
The old reusable providers/statue alternatives remain; mixed random retries,
other cannons and occupied Jack are not extended. Crash permission becomes
progression only with gating and guaranteed Foley or HotHead→Crash sources.

## Mustard map Crash alternative

`mustard-map-crash-source-witness.md` and `mustard-map-crash-acceptance.json` add
one finite guaranteedTWISTER→Crash OR graph to the existing310 map target, leaving
its UFO graph unchanged. Independent590→534 acquisition/carry, exact camera-valid
dry310 activation, Crash consumption and Normal timed crossing/chest continuation
are witnessed at1HP/6HP and100%/500% without damage. Full omission controls take
Knight damage before positive contact; clean prefix and offscreen controls have
separate limited roles. Local production polling emits3960205 from transport bit4;
that is distinct from physical chest39, suppressed vanilla ownership and server
receipt. No global range, persistent credit or mixed-source retry guarantee follows.

## Cabbage Chocolate chest: finite Fire alternative

The existing `bomb_517_chocolate` target now OR-composes its unchanged Beam
and Smash witnesses with a separate guaranteed WADDLE_DOO→Fire graph. The
original finite Doo is acquired after the independently required Hub2 entry.
The complete Fire-specific carry, neutral breath packet, physical chest and
local client check are native-tested at HP 1/6 and enemy health 100/500%, with
four matched no-breath controls. No global Fire range, other exit, RoomSanity
or renewable source is inferred. Fire already has a gateable progression item;
permission remains separate from equipment. See `cabbage-fire-source-witness.md`
and `cabbage-fire-acceptance.json` for startup/configuration qualifications,
packet attribution and the limits of native versus host rule coverage.

## Cabbage Chocolate chest: finite Missile alternative

The same `bomb_517_chocolate` row now OR-composes a separate guaranteed
WADDLE_DOO→Missile route with Beam, Smash and Fire. Native acceptance starts
Normal at actual Hub2 entry, acquires the original finite Doo, carries Missile
to the exact upper pose and uses a down-right local detonation. The ±24 tile
scanner, not later ±30 damage bounds or piercing flight, opens the F1 chain.
Four HP 1/6 and enemy health 100/500% positives reach the physical chest and
local client check; four no-attack controls stop at frame 3813 before collection.
Failed later closed-wall continuations are excluded from no-damage controls.
Missile permission is progression only for the enabled guaranteed-source chest
rule with gating on. See `cabbage-missile-source-witness.md` and its acceptance
metadata for setup, attribution, policy and option qualifications.

## Cabbage Chocolate chest: finite Parasol alternative

The existing target gains only a separate guaranteed WADDLE_DOO→Parasol graph.
Normal entry from independently reachable Hub2, the original finite source,
Parasol-specific carry, dry animation 0x35 and physical chest continuation are
covered by four HP 1/6 and enemy health 100/500% positives and full-length
no-target-swing controls. Actual ObjectSetBounds (16,-11,48,11), not held
umbrella or a generic damage envelope, reaches F1 (14,7). Parasol permission
is progression only for the enabled guaranteed-source chest with gating on,
including scoped starting-inventory reconciliation. See
`cabbage-parasol-source-witness.md` and `cabbage-parasol-acceptance.json`.
Existing Beam, Smash, Fire and Missile routes, exits and RoomSanity remain
unchanged. No global range, other move, other target or source renewal follows.

## Carrot Room7: bounded Sword repeated slash

A separate guaranteed lower WADDLE_DOO→Sword graph OR-composes with unchanged
Beam/Fighter graphs on `bomb_719_room13`. Independent Room5/native170 entry,
finite acquisition and actual Sword carry lead to the dry three-tap111 combo.
The attached Sword scanner opens F1(1,14) and15F2, then ordinary movement reaches
734 lower. Four HP1/6 × enemy100/500 positives and matched controls establish
this path without damage or landing waves; at500%, Big Waddle survives the
carry hit while Kirby passes. Only ENTRY_FROM_5_07 is changed, not Secret Notes,
rewards, other exits or RoomSanity. Sword already has a gateable progression
permission. See `carrot-room7-sword-witness.md` and its compact acceptance JSON
for raw hashes, startup qualifications and native-versus-host coverage limits.

## Mustard Room15: bounded Magic Meta Knight alternative

`switch_533_room16` adds one separate guaranteed FOLEY → Magic OR graph.
Normal enters through actual Hub4 → 534 → 533, acquires the finite source,
carries Magic to the reviewed dry pose, selects Meta Knight using the visible
roulette icon, consumes Magic to Normal and completes the timed crossing and
actual 325 arrival. Existing Bomb/UFO/Crash graphs are unchanged. No persistent
switch credit, source renewal, general Magic attack or unrelated target follows.

Frozen v4 has 36 positives and eight controls. The 12 endpoint/control runs use
baseline layout 3 at actual HP 1/6 × enemy health 100%/500%; 32 more positives
cover ordinary layouts 0 to 4 at 100%/1 HP. Alternate-mode layouts 5 to 7 have
source recurrence only. Native gating/keys are off; host permission, scoped
progression, starting inventory, options and full-fill tests are separate.
See `mustard-room15-magic-source-witness.md` and its sanitized acceptance JSON.
This supersedes the earlier unproved switch-contact note only for this exact
source, pose, strategy and target, not Magic's other outcomes or generic range.

## Bounded Cutter310 addition

The five-roof-return witness in `mustard-map-cutter-source-witness.md` adds only
the guaranteed original534 TWISTER-to-Cutter alternative to the existing map
row. Thirty fresh ungated positives cover all28 distinct Chip/Knight HP pairs
at1HP plus6HP100/500% endpoints; thirteen omissions and a separate two-case
gating-on acquisition check retain their distinct scopes. Contact precedes
terrain, Cutter is retained, and the timed gate never earns persistent credit.
This does not finish the broader ranged-attack checklist or prove arbitrary
arrivals, every integer health percentage, global RNG states or universal range.

## Rainbow Goal 3: ordinary Normal alternative

Four independently reviewed ungated HP 1/6 × enemy 100/500 witnesses start at
exact 178 right arrival and traverse into 177, complete the Box Boxer fight and
capture two original Flamers in one pass. Damage 25 large-star object-door
bypass opens slot 2 and leads to physical chest 0x088BB0BC and local client 3960568.
The existing `MINOR_CHEST_RAINBOW_ROUTE_1_GOAL_3` null rule remains; no copied
ability, generic Normal power, health restriction, new target or AP edge follows.
Matched final-shot omissions remain sealed through their bounded prefix stops.
These distinct recipes do not prove upstream 138/new-game access, all RNG/options,
a full gated matrix, RoomSanity or central-circle return. This is not terrain piercing.
See `rainbow-normal177-source-witness.md` and `rainbow-normal177-acceptance.json`.

A separate independently reviewed gated/no-items representative at actual 1 HP
and 500% enemy health also reaches this chest with Normal equipment and zero
unlock mask. Its own final-shot omission stays sealed. This is one additional
case, not all random policies or a full gated health matrix.

## Candy map: ordinary Normal alternative

Three independently reviewed witnesses cover actual 1 HP at 100/500% enemy health
and 6 HP at 100%, from a qualified near-door 419 fixture through the actual 426
transition to physical chest 0x088C87FC and local client check 3960208. Repeated
first-switch contacts/puffs, a late jump, lower-switch shaft access, inflation
return and an ordinary F1 slide provide a sufficient solo route with no damage.
The matched 6 HP first-jump omission produces no complete crossing or check.
Preserve the map's existing null rule and other ordinary alternatives. Switches
5/6 latch only while loaded. This adds no generic Normal power, copied-ability
gate, health restriction, new AP edge, RoomSanity or outgoing 420 credit. The
all-frame claim is limited to 1085–4154; arbitrary 419/new-game access and reset
persistence remain unproved. See `candy-normal426-acceptance.json` and its witness.
This does not finish the broader ranged-attack checklist.

## Olive Vitality: ordinary Normal alternative

The reviewed native 815 route moves silver block `0x088CCCFC` with sustained
Normal inhale to maintain lower-switch contact, then uses an intrinsic air puff
and timed lower-gate crossing before ordinary slide and chest `0x088CCC90`.
It never consumes or spits the block. Four actual 1/6 HP × 100/500% cold runs
emit only local `3960301`; a one-bit final-puff omission does not cross or check.
Keep the existing `can_break_block` rule, RoomSanity and other exits unchanged.
The qualified late 551 approach is not arbitrary upstream/new-game access or a
generic Normal capability. Review audited recorded evidence and source without
rerunning the emulator or reconstructing every collision tile. See
`olive-normal815-source-witness.md` and `olive-normal815-acceptance.json`.

## Carrot Room7: bounded Fire traveling breath

A separate guaranteed finite lower WADDLE_DOO→Fire graph OR-composes with
unchanged Beam/Fighter/Sword graphs on `bomb_719_room13`. Independent native170
entry, Normal acquisition and the qualified longer directional Fire carry are
required. The dry719-only final B breath uses a traveling player-parented packet,
not its mouth effect, to open F1(1,14)/15F2 and enter734 lower. It does not extend
Fire517, upper Secret Notes, other exits or RoomSanity. Fire is already gateable
and progression; permission/equipment and item lifecycle remain unchanged.

Eight endpoint/control runs cover HP1/6×enemy100/500, plus a gated1HP500 route
and acquisition-only no-permission control. Independent supplement review covers
26 remaining encountered enemy-HP tuple representatives at1HP, for28 distinct
tuples across50..500. This is bounded discrete-health coverage, not all RNG or
all arrivals. Correct names are Chip(type08) and Blockin(type0D); the original
report's name erratum preserves raw IDs/results. See
`carrot-room7-fire-witness.md` and `carrot-room7-fire-acceptance.json` for scope,
input/source hashes and independent review provenance.


## Cabbage Chocolate chest: finite Spark and Ice alternatives

Two exact OR graphs add guaranteed original WADDLE_DOO→Spark and →Ice to
`bomb_517_chocolate`, preserving all five earlier graphs. Each requires independent
Hub2 access, Normal 591→517 entry, finite source 0x088CA04C, source-corridor
clearing and actual retained equipment. Spark uses the dry upper step
(201.9961,88.9961) and its attached field. Ice uses ordinary right-facing traveling
breath from (185.9961,120.9961), with no frozen enemy, platform or kicked payload.
Each packet has four full HP1/6 × enemy100/500 positives and four full target-only
omissions, plus a real-client single-permission full positive and bounded
no-permission acquisition negative. Non-source enemies are avoided; observed
HP-to1 transitions with despawn flags are removals, not damage dependencies.
Physical chest57 and local client check3960511 are verified; server receipt,
intermediate health percentages, other arrivals and global range are not claimed.

Spark and Ice remain useful/gateable baseline items. The enabled actual Chocolate
location, gating and matching raw singleton Doo grant add a progression reason,
OR-composed with existing Rainbow Spark and Goal2 Ice reasons. Spark joins early
precollected-item reconciliation; inventory still does not equip Kirby. Mixed and
Normal-weight pools retain prior partial-policy behavior, and no unrelated Wheel
bypass is added. See `cabbage-spark-source-witness.md`, `cabbage-ice-source-witness.md`
and their compact acceptance manifests for frozen provenance and bounded scope.

## Cabbage Chocolate chest: finite Sword first slash

`hub2_sword_entry` adds only raw guaranteed original Doo→Sword to the same
Chocolate row. A separate room517 capability records ordinary first slash,
not room719 repeated slash or a global Sword range. Full-pool seed4 starts
Normal, enters591→517, acquires the finite source, clears its own corridor
and carries Sword without damage to the dry lower pose. The actual attached
scanner opens target3339; linked cells finish3369 and physical chest4252.
Four full endpoints, four single-tap omissions and two separate gating checks
are independently reviewed in `cabbage-sword-source-witness.md` and the compact
acceptance JSON. Non-source enemies are avoided, not combat dependencies.
All seven earlier graphs remain unchanged; inventory permission still cannot
replace source acquisition or independent Hub2 access. Sword already has
progression classification, so no item factory or lifecycle change is needed.
No exit, RoomSanity, other target, starting removal or wider arrival is added.

## Cabbage Chocolate chest: finite Fighter first combo

`hub2_fighter_entry` adds raw guaranteed original Doo to Fighter as a ninth
same-target alternative. The separate room 517 capability uses the ordinary
first combo and a Fighter-specific short-punch/flight carry, not the charged
or HP1 wave. Ten fresh native traces and independent review are documented
in `cabbage-fighter-source-witness.md` and its sanitized acceptance JSON.
Endpoint positives open at 3328, linked cells finish at 3358, and chest 57
opens at 4252. Full single-tap omissions remain sealed with maximum HP.
The eight prior graphs, all other room data and existing Carrot progression
reason remain unchanged. No item factory, reconciliation, exit, RoomSanity
or starting-removal change is introduced.

## Cabbage Chocolate chest: finite UFO maximum-charge shot

`hub2_ufo_entry` is the tenth same-target alternative. It requires independent
Hub2 access, a raw guaranteed original Waddle Doo to UFO assignment, finite
acquisition and continuous UFO-specific carry. The separate dry room 517
capability admits only the witnessed maximum-charge large shot, not generic
UFO range or the low/medium shots. All nine prior graphs remain unchanged;
permission does not equip UFO, and no exit, RoomSanity or item lifecycle rule
changes. See `cabbage-ufo-source-witness.md` and `cabbage-ufo-acceptance.json`.

Independent native review audited all 12 accepted traces and freshly replayed
the HP1, enemy 500% positive/omission pair. Acceptance covers the documented
HP1/6 and enemy 100%/500% endpoints, not arbitrary arrivals, RNG or intermediate
health settings. The no-permission control is acquisition-only. Host validation
passed 2,265 focused tests, including 24 complete seed 52 generations across
gating, Area Keys, enemy 100%/500% and starting UFO counts 0/1/3 at HP1. These
host tests are not new native replay evidence or a full aggregate test pass.
