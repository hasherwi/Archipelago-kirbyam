# Ranged-attack coverage ledger

This is the broad scope of PR #1052, not a claim that all ranged logic is implemented. The five source-backed Bomb Block targets described in `bounded-bomb-implementation.md` (including the separate dry Spark and underwater Sword alternatives for Rainbow110, selective Rainbow Green Paint and Carrot Yellow Paint routes and separate Beam and Smash alternatives for the Cabbage Chocolate chest), the conditional533 small-switch alternatives in `mustard-room15-source-witness.md` and `mustard-room15-ufo-source-witness.md`, and the conditional310 map route in `mustard-map-ufo-source-witness.md` are the implemented subset. The source catalog below identifies candidate move families; it does not grant an ability, arbitrary range, collision equivalence or complete route.

## AP ownership census

`tools/build_ranged_target_coverage.py` reads production-normalized `data.regions` rather than a parallel raw-room loader. At the current implementation baseline it covers 366 regions, including 343 mapped native definitions (322 parents and 21 logical compartments), area/other connectivity and synthetic RoomSanity sinks. It records 384 uniquely owned locations, including 263 RoomSanity checks, and 1,058 location/exit surfaces. All 37 current traversal target definitions bind to exact normalized surfaces. These counts describe AP structure, **not** the number of attack-dependent targets.

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
- `src/code_0806F780.c:7963–8076`: Magic Meta Knight moving viewport-height damage, category0x2000, no terrain query/tile-scan flag in examined update. Full switch callback/special flags still unproved.
- `src/foley.c:142–156,237–242`, `code_0806F780.c:2497–2522,2653–2674`: nearby Kirby triggers drop, landing creates category0x40 explosion, damage±20 with animation eligibility and no tile scanner. Not Bomb equivalence.

## Target namespaces and live investigation

Keep ordinary Bomb Block0xF1 and selective0xF6 filters separate. Small and big switches have different masks/player handling. Small switches also accept overlapping star-stone/large-star-stone objects (`big_small_switch.c:135–197`). Fuses admit categories0x100/0x10000 (`cannon_fuse.c:39–53,603–610`). Star-stone objects have strength4 resistance and physical behavior (`star_stone_block.c:14–37`); they are not background tiles. Destroyable rock blocks use Kirby position/state/delay (`destroyable_rock_block.c:13–64`), not an inferred attack from their name. Animated door opening is not completed traversal.

Three coarse `can_hit_far_switch` surfaces currently remain in this branch: Mustard Chest310, Mustard15/native533→Mustard16/native325, and Peppermint Chest209. They must not become blanket ability gates:

- 310 has a solid intervening wall and near-zero release timer. A guaranteedTWISTER→UFO subset now uses the complete Normal Hub4/native590→534 approach, finiteTwister acquisition and UFO carry into310. The room-specific top-charge combat, switch shot and timed crossing reach chest39/map4 without damage at50/100/450/451/462/463/500% enemy health; matched100/500% no-final-charge controls remain blocked. Only `MAJOR_CHEST_MUSTARD_MOUNTAIN` is gated; return exit, Area-Key entry and RoomSanity rules are unchanged. Unsupported source policies, other attacks, arbitrary arrival paths and Phone/helper alternatives remain unproved. See `mustard-map-ufo-source-witness.md` and `mustard-map-ufo-acceptance.json`.
- 533 has a solid/elevation obstacle. Separate environmental Foley explosion from acquiring its default Bomb and placing a delayed bomb. A guaranteedFOLEY→Bomb subset now uses the complete no-damage Hub4→534→533 acquisition, placement and325 crossing at100%/500% enemy health, with matched controls. A second guaranteedFOLEY→UFO graph proves the top-charge shot and crossing under production assignment-table fixtures, with no-shot/low-laser/medium-shot controls. Unsupported source assignments retain prior behavior. Environmental and other attack alternatives remain unproved.
- 209 is a dependency on **published** PR #1051 head177d765: `ordinary-209-snow-map-loop-acceptance.json` proves a qualified upper210-arrival Normal route through Snow and the first Bomb chain to the map, with100%/500% enemy-health variants. It does not prove arbitrary209 entry joins. Do not duplicate that coarse placeholder as a ranged requirement or import unrelated unpublished #1051 work.

147 is calibration only: ordinary timed traversal is an alternative, so a ranged witness alone does not justify a mandatory AP gate. Further work must inspect all actual target/check associations, enemy-health/interception, source randomization, 1HP/no-damage movement, precise entry compartments and matched controls.

For future Phone/ranged alternatives on the same AP surface, use alternative witness graphs inside **one target row** (OR). Separate installed rows combine through `add_rule` as AND and must not accidentally require both Phone and a solo attack.

## Cabbage Chocolate chest Smash alternative

`bomb_517_chocolate` now has separate guaranteed WADDLE_DOO→Beam and
WADDLE_DOO→Smash witness graphs within one OR target row. The new production
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
from the finite source do not gain an eventual-draw promise. Spark/Ice carries, other entry sides or exits,
RoomSanity reachability, arbitrary health interpolation and global Smash
collision equivalence remain unproved. Carrot's condition remains Beam-only.
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
