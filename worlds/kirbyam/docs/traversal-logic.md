# Source-backed traversal (draft)

## Contract

An ability item permits acquisition; it does not equip Kirby. `traversal.py`
models a directed entrance/compartment-to-exit/check graph, one equipped ability,
physical source identities, source consumption, and transient opened pegs.
Capability providers are separate from room records. The policy resolver uses
`build_enemy_copy_runtime_patch_writes`, the same assignments and eligibility
bitmap as the ROM. Excluded categories keep their native grants.

A source behind its own obstacle cannot solve it. Copying another ability replaces
current equipment. Mini disappears on a transition, including a same-room cannon.
A transition and a room-instance reset are distinct: only an explicit reset
renews consumed sources, and a reset also loses opened pegs. Multiple rows for
one physical source share its stable identity. No permanent AP peg event is used.

Live random grants expose outcome sets, not the deterministic fallback hash.
A single-use random source proves a capability only when every possible output
solves it and no Normal result is possible. Sequential capabilities cannot select
different favorable outputs from the same consumed source. Explicit renewable
placements can instead use possible-acquisition semantics: repeated attempts are
assumed eventually to produce a positive-support eligible output. This is a
fairness assumption, not a first-inhale or bounded-attempt guarantee. A full-period
PRNG alone does not prove it because grants consume differing numbers of draws.

The reviewed hub190 regular statue is renewable in place: native
`ability_objects.c:sub_080AA588` grants an ability without consuming the statue.
Kirby can drop an unwanted result and touch it again. Ordinary enemies and ability
stars do not inherit this renewable classification. Enemy weight100 removes
random enemy outputs; statue output pools ignore that enemy weight. All gateable
outputs still require their unlock items.

## Room-owned traversal schema

`data/regions/rooms.json` stores executable traversal metadata alongside each
target's ordinary exits and locations. `data.py` retains the optional version-1
`traversal` object on its owning region; `traversal_data.py` loads and validates
the catalog. A `targets` entry names exactly one existing directed `exit` or
`location`, its `native_room`, its `kind`, and its reviewed witness `graphs`.
The graph's `nodes`, `routes`, `starts`, and `required_targets` retain the exact
compartments, transitions and bypasses. A start is Normal, never free equipment.

Each graph uses the same `compile_traversal_graph` compiler. Route `items` are
unconditional prerequisites; `area_key_items` are added only with Area Keys on.
`allowed_abilities` may narrow, but cannot expand, the separate capability
providers in `traversal.py`. `room_transition` also covers a same-room cannon.
Only `room_instance: reset` renews consumed sources, and it requires explicit
`reset_evidence`; preserve and unknown lifetime remain distinct.

Local `sources` name exact acquisition nodes, physical identities and evidence.
Shared `source_sets` live with their hub region, name their native room, and are
referenced by ID and compartment in a witness. In particular, the nineteen 970
statues are defined once and reused by the Wheel and Smash carriers. The source
set's native room must match the receiving compartment. A renewable placement
needs repeatability evidence, and possible-acquisition retries additionally need
the witness's `retry_evidence` and an explicit evaluator opt-in.

The graph's `access.region` is an independently reachable source region.
`access.all_hub_switches` additionally requires each physical switch location,
not owned connection items or an area event. The shared runtime helper also
registers those access regions as indirect dependencies for entrance rules.
The Mini, peg, and Wheel installers retain their assignment and option policy;
they no longer carry a parallel hardcoded route/source catalog. Research-only
non-AP pegs belong in the evidence census below, not executable targets.

## Mini

The exhaustive native collision0x59 census contains only rooms134,312,321,736.
All four rooms have source-aware routes in every randomization mode:

- Olive6/134: lower Ocean Spray route, with local Minny and the drop/inhale/recover
  sequence before the final throat. Upper Goal1 remains independent.
- Mustard18/312: Warp branch. Ordinary Room19 remains independent.
- Mustard5/321: both lower Room6 routes require Mini. Each side's upper Room9
  exit stays independent. The Room5 chest is reachable with Normal from the
  right arrival; the left arrival must first cross the Mini corridors.
- Carrot10/736: down-cannon compartment to Chest1. Upper Room11 is independent.

Canonical Minny placements precede their throats; unrelated room-wide enemies
are not credited. In particular, a source across a cannon transition cannot carry
Mini back through that transition. The room-owned traversal records in `data/regions/rooms.json` hold the
executable routes; the Mini appendix below preserves source addresses and the
native evidence contract.

Minny always grants Mini. Only the Minny carve-out option was removed; general
randomization, statue, miniboss, boss-spawn and non-ability-enemy options remain.
Mini can still appear from other randomized enemies. Statue pools preserve the
former default exclusion of Mini. Mini remains gated and is no longer precollected.
Wheel is also gated/progression and no longer precollected. Stone starting permission remains unchanged.

Raw Mini ability stars recover Mini under the same unlock gate in every mode.
Other stars preserve existing behavior, including the existing native0x80 versus
legacy0x20 detector mismatch. Do not assume ordinary stars suppress no-ability
weight. See `mini-star-recovery.md` for actual-C tests and patch verification.
Old Minny policy keys are ignored for newly generated patch plans. This does not
repair an old ROM whose static Minny grant was already changed: regenerate and
repatch from the supported original ROM.

### Mustard 5 entry compartments

Native 321 has two distinct arrivals: 304 / Room4 enters the left side at tile
`(2,22)` (`0x0888FB12`); 546 / Room8 enters the right at `(30,19)`
(`0x0888F6B0`). The right arrival now enters `RIGHT_ENTRY`, which owns chest
`0x088C4DFC` at pixel `(184,248)`. Both sides retain their upper Room9 exit and
their own source-backed Mini route to the lower Room6 exit, record `0x08891758`
at tile `(5,39)` to native 544 spawn `(3,2)`. The physical RoomSanity check is
shared without connecting the compartments through it.

From the right arrival, an ordinary terrain body `[-6,-5,+6,+7]` has this
pixel-coordinate path using only air, platform `0x0E`, and door `0xFF` terrain:
`(472,296) -> (358,296) -> (358,216) -> (248,216) -> (248,248)`.
Facing left, an ordinary puff activates bomb `0x08891722` at tile `(14,15)`.
Its connected `0xF2` records at x9..13 in rows14/15 replace their collision with
air. Then `(248,248) -> (184,248)` reaches the chest without Mini. The same
ordinary body can cross to the left after opening the bomb:
`(184,248) -> (136,248) -> (136,344) -> (24,344)`.

The left-to-right witness instead acquires left Minny `0x088C4DB4` at
`(24,280)`, crosses both Mini throats `(12..13,26)` and `(19..20,19)`, then
drops Mini on the right for ordinary flight/puff to the chest. The right lower
exit witness uses right Minny `0x088C4DD8` at `(472,232)`. The sources are
inhaled from their approach alcoves; neither is a global room-wide source.
The cross-side tile route is `(1,21) -> (8,21) -> (8,24) -> (9,25) ->
(11,26) -> (14,26) -> (19,26) -> (19,22) -> (16,22) -> (16,19) ->
(21,19) -> (24,19) -> (24,18) -> (29,18)`, including both Mini throats.

These are native terrain/body and point/slope topology checks, not an emulator
jump-physics replay. Ordinary enemy avoidance/combat is assumed. The earlier
claim that the upper halves freely reconnect was incorrect: a wall reaches
the top boundary, and the bomb approach is initially accessible only from the
right. Normal cannot reach the lower exit from either side even when ordinary
bomb/F0 mutations and slopes are granted in the optimistic topology model.
The [WiKirby Room5 description](https://wikirby.com/wiki/Mustard_Mountain_-_Room_5)
corroborates cross-side Mini travel and a 1-Up chest, but does not by itself prove
these entry-specific rules or the exhaustive native corridor census.

## Peg coverage

The peg census appendix below records all 14 pegs in 13 native rooms. An audit record is
not automatically an executable route. Production source-aware gates currently cover all eleven AP peg targets:

- 149 peg35,18: chest, with a local Giant Rocky or a carried Smash. The carry
  runs190 -> 143 -> 145 -> 146 upper exit -> 147 -> 148 right entry -> 149.
  Smash Up+B cuts the143 star-platform rope; Stone cannot substitute there.
  A190 statue may supply Smash under its actual assignment. The late970 statue
  fallback requires all15 physical switches, Central access and the East hub
  connection before this carry. Smash's down attack clears the149 ordinary floor.
  Room147's documented vanilla timed run is assumed, not emulator-replayed.
- 510 peg7,7: chest; Stone592 -> 528 -> 513 upper -> 509 upper-right -> 510 upper.
  The final segments need no peg, metal or rope clearing. The UFO inside the chest
  chamber is never used to bootstrap entry. A lower horizontal-metal alternative
  remains uncredited; the implemented peg route is a sufficient witness, not a
  claim that every other attack is impossible.
- 401 peg28,30: right shaft to406 Sound Player; local Rockys or explicit Stone
  carry190 -> 801 -> 490 -> 407 -> 401. The407 bomb is approached from above with Stone.
- 411 peg4,3: revealed405 doorway; Stone190 -> 801 -> 490 -> 411. Other exits stay free.
- 221 peg41,12: Pink chest tunnel; local Giant Rockys or Stone
  190 -> 801 -> 290 -> 291 -> 215 -> 212 -> 216 -> 217 -> 221. The carry avoids rock bodies,
  ordinary blocks, and the star platform rather than assuming them absent.

- 816 peg26,3: Olive Map; local Bonkers or Stone592 -> 801 -> 191 -> 890 -> 811 -> 830 -> 810 -> 802 -> 816. The reviewed carry avoids rock bodies and opposing currents; ordinary underwater puffs activate the811/802 bombs without dropping Stone.

- 204 peg62,4: alternate227 entrance to Happy Notes; Stone190 -> 801 -> 290 ->
  210 -> 227 main -> 204. Ordinary BoxBoxer combat retaining Stone is assumed.
  Native damage eligibility accepts Stone. The post-boss puff and transition
  retaining Stone were replayed, but the fight itself was not.
- 605 peg12,24: revealed610 door; Stone592 -> 690 -> 611 -> 601 upper exit -> 605.
  Standing untransformed on two native0x74 crumble objects removes the F7 floor
  layers without discarding Stone. The601 bomb uses an ordinary puff.
- 513 peg4,7: upper-to-lower passage, then ordinary bomb5,18; Stone592 -> 528 ->
  513 upper arrival. The528 wall puff and transition retaining Stone were replayed.
  Reverse lower-to-upper movement can activate the bomb without the peg; the
  directed0x0F platform prevents that reverse bypass from opening a forward route.
- 527 peg18,13: Sapphire, after the timed gate and bomb38,8; Stone592 -> 528 ->
  527. The documented vanilla timed run is assumed executable with untransformed
  Stone, which shares ordinary movement. Native timing and gradual door animation
  agree with that route; no exact frame schedule or emulator timing replay is claimed.
- 527 peg56,16: lower515 entrance only; Stone592 -> 528 -> 527. This carry avoids
  the timed gate and rock body. Its narrow ordinary corridors fit native flight
  terrain bounds. The independent upper exit is not gated by this peg.
  A segmented native replay verifies this peg, lower door, bomb and chest with
  Stone retained and no Mini. It does not verify the full randomized source carry.

Carrier witnesses require an independently reachable source hub, actual Hub
Connection items, and destination Area Key when that option is enabled. Static
assignment validation accepts reviewed local or carrier witnesses rather than
rewriting individual randomized outputs. Static policies, including shuffled weight100/statue configurations, get at most
1024 assignment attempts without forcing individual outputs. If that budget
finds no Wheel-validated assignment, generation fails that seed with a precise
search-budget diagnostic, not a claim that the configuration is impossible.
A Wheel-valid candidate without all reviewed peg witnesses also fails after the
bounded search. No target rule silently becomes permissive. Live-random rules
validate positive-support renewable statue witnesses before installation. Unknown
alternatives are not declared impossible; the diagnostic describes this seed and
reviewed witness set, not global configuration impossibility.
The current repository has no entrance
shuffle option; RoomSanity adds checks, not shuffled transitions.

204 -> 227 Happy Notes has a one-way target compartment: regular227 entry cannot
reach it through the nondroppable0x0F platform. The upper compartment can exit to
main. Its exact peg-side entrance now has source enforcement.

515 also has directed compartments: only the527 lower arrival reaches its chest.
The527 upper arrival can reach the common exits but not that chest. The513 arrival
occupies a separate shaft that can return to513 but cannot reach the chest or
bottom500 exit. No Mini requirement is inferred from an ordinary16px corridor.

509 and218 gate food rather than AP exits;741 gates a loose1-Up, not its room exit.
527 Sapphire requires bomb38,8 then peg18,13; an earlier bomb24,14-only bypass was
invalidated by directed0x0F analysis. Its timed gate uses the qualified ordinary-movement assumption above. The816 remote bomb alternative remains unresolved. Ordinary underwater
weapons and puffs cannot break149's alternate F7 ceiling because they lack the
required attack flag; environmental large-block/cannon alternatives are not claimed.

## Destructive chains and remaining acceptance

A closing chain is not automatically a Wheel gate. Candy424 Music Scores was
collected with Normal in an isolated native replay. Moonlight708's secret22,28
exit was reached with Normal from the743 return entrance30,29. These successes
must not be gated on Wheel. Other708 entrances need separate analysis.

Rainbow108 upper chest has an actual Wheel success witness from110 arrival34,19.
Wheel exclusivity is not established. A consolidated uninterrupted native replay
now verifies Normal140 arrival, actual Wheelie acquisition, the independent108
bomb,110 detour, fresh108 return, and chest collection. There were no RAM edits
or reloads after initial140 setup. The exact108 lower-mid -> chest route is now enforced. Wheel140 supplies an early
source when its actual output is Wheel. All19 regular statues in970 provide a
late fallback after every physical hub switch can be activated. Area-wide events
and received Hub Connection items do not substitute for those15 physical checks.
The carry passes970 -> 801 -> 190 -> 140 -> 108 -> 110 -> 108, retainingWheel.
The970-to140 path uses clear ordinary flight and avoids touching the190 statues. Only its final
110 -> 108 return explicitly uses a fresh unoccupied room reset. Ordinary
single-player opportunity for that reset is assumed; no adversarial-AI or bounded
reset guarantee and no unlimited phone battery are claimed. Native code rebuilds
original collision for a fresh room slot. The final arrival matches the witnessed
Wheel race start. See the Wheel evidence appendix below and the room-owned traversal metadata in
`data/regions/rooms.json`. Wheel is removed from
starting abilities in every mode, while Stone remains.

Before treating this draft as gameplay accepted:

- Expand alternative witnesses where useful; all eleven AP peg targets now have
  source-aware rules, while the three non-AP consumable pegs remain audit records.
- Repeat the verified native Rainbow108 carrier/reset route on the rebuilt
  randomized/gated ROM and investigate more speed alternatives. The current
  rule retains the explicit fresh-room opportunity assumption.
- Replay the full Olive Mini sequence with the rebuilt randomized/gated ROM.
- Replay both Mustard5 arrivals and the Mini cross-side route on that ROM;
  its new compartment correction has native geometry and logic tests, not
  completed Mini jump-physics or patched-ROM acceptance.
- Verify room-reset retry routes before marking any enemy renewable; AI occupancy
  can preserve a room and prevent respawn.
- Run the complete world suite and archive generation matrix on the final commit.

Research was pinned to native source commit
`7d969fbce14fdc838d2c1ea01389717fb96c3189`. Published records contain compact
facts and addresses, not full ROMs, save states, or native collision dumps.


## Evidence appendices and ownership

`data/regions/rooms.json` is the owner of executable Mini, Wheel, and peg traversal
metadata. These appendices retain research provenance, native addresses, census
coverage, and limitations; they are not a second executable graph or a blanket
room gate. Capability-provider policy remains separate from room records.
Historical static-connectivity observations below do not supersede the reviewed
source/carry contracts above. In particular, a static component is not proof of
playable movement, and an untested alternative is not proof of impossibility.

All native references use commit `7d969fbce14fdc838d2c1ea01389717fb96c3189`:

- [Hammer pegs](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/hammer_peg.c).
- [Room loading and collision](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/level.c).
- [Mini collision handling](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/code_080023A4.c).

Coordinates are tile coordinates unless explicitly labeled pixels or native body
bounds. Source-object positions in the source tables are pixels. Transition
rows give the source-door tile and destination spawn tile separately. Hexadecimal
addresses are native record/object addresses, not stable shuffled assignments.

### Mini evidence: all four native 0x59 corridor rooms

Native collision `0x59` / `sub_080088CC` requires actual Mini equipment. These
reviewed routes do not exhaust source alternatives and make no emulator claim.
Local Minny acquisition means inhaling from the approach to its pocket, not that
Kirby can stand on its spawn tile. Only Olive needs the explicit dropped-ability
recovery sequence. The cannon is a transition before acquisition, not a reset or
a way to carry Mini between compartments.

| Native room | AP room and gated target | Canonical Minny objects | Additional evidence |
| --- | --- | --- | --- |
| 134 | Olive `ROOM_6_06`, `MINOR_CHEST_SPRAY_PAINT_07` (Ocean Spray) | `0x088CBD88` | Drop/inhale/recover at star-stone `0x088CBD40`; independent upper Goal1. |
| 312 | Mustard `ROOM_4_18` to `ROOM_4_WARP` | `0x088C417C` | Approach is not a transition; ordinary Room19 independent. |
| 321 | Mustard left and `RIGHT_ENTRY` to `ROOM_4_06`; left to right | Left `0x088C4DB4`, right `0x088C4DD8` | Approach is not a transition. Upper Room9 exits are independent; only the right arrival has a Normal bomb/chest witness. See entry-compartment proof above. |
| 736 | Carrot `ROOM_5_10` to `ROOM_5_CHEST_1` | `0x088D41A0` | Down cannon `0x088B2616` self-transitions before local acquisition; upper Room11 independent. |

### Peg census: 14 pegs in 13 rooms

Eleven AP targets have production source-aware routes. Three non-AP pegs remain
consumable-only evidence and impose no AP exit gate. `0x0F` platforms are
upward-only, not undirected flood-fill connections.

| Census ID | Native room | Peg tile | Coverage |
| --- | --- | --- | --- |
| `peg_149_35_18` | 149 | 35,18 | AP target; production source-aware |
| `peg_204_62_4` | 204 | 62,4 | AP target; production source-aware |
| `peg_218_9_33` | 218 | 9,33 | Non-AP consumables; no exit gate |
| `peg_221_41_12` | 221 | 41,12 | AP target; production source-aware |
| `peg_401_28_30` | 401 | 28,30 | AP target; production source-aware |
| `peg_411_4_3` | 411 | 4,3 | AP target; production source-aware |
| `peg_509_32_2` | 509 | 32,2 | Non-AP consumables; no exit gate |
| `peg_510_7_7` | 510 | 7,7 | AP target; production source-aware |
| `peg_513_4_7` | 513 | 4,7 | AP target; production source-aware |
| `peg_527_18_13` | 527 | 18,13 | AP target; production source-aware |
| `peg_527_56_16` | 527 | 56,16 | AP target; production source-aware |
| `peg_605_12_24` | 605 | 12,24 | AP target; production source-aware |
| `peg_741_27_13` | 741 | 27,13 | Non-AP consumables; no exit gate |
| `peg_816_26_3` | 816 | 26,3 | AP target; production source-aware |

#### `peg_149_35_18`

**Route observations.**

- Arrivals: Source: 148; Record: 0x8882a42; Spawn: 2, 10; Compartment: hillside.
- Target: Kind: small_chest; Object: 0x88bc4a0; Pixel position: 624, 376; Item: 1-Up.
- Peg route: hillside -> star opening -> peg -> lower-right chest pocket.
- Alternate: Obstacle: F7; Tiles: (42,24), (43,24); Approach: underwater from below; Status: Ordinary underwater attacks lack F7-required0x800; environmental large-block/cannon alternatives unverified.
- Source: Object: 0x88bc434; Kind: Giant Rocky; Vanilla: Stone; Before peg: yes.
- Exit gated: no.

**Reviewed carry evidence.**

- Path: 190, 143, 145, 146, 147, 148, 149.
- Required equipment: Smash.
- Late source path: 970, 801, 190.
- Late access: All15 physical hub switches reachable, Central reachable, East Hub Connection; actual970 statue assignment and Smash gating apply.
- Qualification: Smash Up+B0x2000 hits143 rope from344,216; Stone carry rejected.146 passes left/above heavy block.147 vanilla ordinary timed route assumed, puff retains Smash.149 Down+B calls Stone attack function and clears ordinary floor without dropping Smash. Local GiantRocky before peg remains separate early source.

#### `peg_204_62_4`

AP region: `REGION_PEPPERMINT_PALACE/ROOM_7_12`.

| Direction | Other room | Door tile | Destination spawn | Native record | Other native fields |
| --- | --- | --- | --- | --- | --- |
| In | 203 | 1, 18 | 73, 4 | `0x8887002` | â€” |
| In | 220 | 59, 4 | 3, 8 | `0x888a00a` | â€” |
| In | 227 | 16, 2 | 56, 9 | `0x888a310` | â€” |
| Out | 203 | 73, 3 | 3, 19 | `0x88870d4` | â€” |
| Out | 220 | 1, 7 | 59, 5 | `0x8887160` | â€” |
| Out | 227 | 56, 8 | 18, 3 | `0x888716e` | â€” |
| Out | 227 | 64, 8 | 27, 2 | `0x888717c` | â€” |

**Trigger.**

- Position: 62, 4.
- Record: 0x088870E2.
- Sprite: 0x088BEA24.
- Chain cells: 6.

**Routes.**

- From: any initial incoming port; To: door64,8 to227 spawn27,2; Requires: peg_204_62_4; Status: collision separation and opening verified.
- From: any initial incoming port; To: door56,8 to227 spawn18,3 /exit1,7 to220 /exit73,3 to203; Requires: none; Status: same initial component, movement untested.

**Source observations.**

none; Pengy/Cookin/Chip/BrontoBurt

**Reviewed carry evidence.**

- Path: 190, 801, 290, 210, 227, 204.
- Qualification: Ordinary BoxBoxer combat retaining Stone assumed; native strength/damage eligibility verified. Post-boss Stone puff and210-to227 transition replayed, not full combat. Only alternate227 Happy Notes entrance is peg gated.

#### `peg_218_9_33`

AP region: `REGION_PEPPERMINT_PALACE/ROOM_7_23`.

| Direction | Other room | Door tile | Destination spawn | Native record | Other native fields |
| --- | --- | --- | --- | --- | --- |
| In | 221 | 1, 2 | 15, 3 | `0x888c72c` | Kind 3; Collision 255; Size 14; Flags 2 |
| Out | 200 | 5, 4 | 41, 9 | `0x888c3ce` | Kind 3; Collision 255; Size 14; Flags 2 |

**Compartments.**

- Before opening: Tall upper room, incoming221 at upper-right; peg at bottom of main room(9,33).
- After opening: Six F2 tiles x8..10,y34..35 disappear, opening downward consumable shaft.

**Affected targets.**

- Kind: item; Object: 0x088C1798; Name: Pop Soda; Pixel position: 152, 600.
- Kind: item; Object: 0x088C1774; Name: Meat; Pixel position: 152, 648.
- Kind: item; Object: 0x088C1750; Name: Battery; Pixel position: 152, 696.
- Kind: item; Object: 0x088C172C; Name: 1UP; Pixel position: 152, 744.

**Independent targets.**

- Destination native: 200; Tile: 5, 4; Object: 0x088C1654; Requires: Separate bomb(2,4), not peg.

**Observed sequence.**

- From221 upper-right entrance traverse/fall down main room to peg.
- Press peg to enter treat shaft; ordinary F0 breakable rows at y38,41,44,47 separate its levels.
- Exit200 is at top(5,4), hidden by independent bomb chain at(2,4); that chain replaces ceiling x2..8,y1 with collision29 spikes.

**Source observations.**

- Room: 221; Object: 0x088C192C; Type: GIANT_ROCKY; Pixel position: 816, 160; Ability: Stone; Prerequisite: Super Inhale by holding inhale about48 ticks; carry through221 -> 218. Actual carrying route not emulator-tested.
- Room: 221; Object: 0x088C1A4C; Type: GIANT_ROCKY; Pixel position: 768, 288; Ability: Stone; Prerequisite: Same Super Inhale prerequisite; reach221 exit(1,2) through separate bomb-block route.

**Caveats.**

- No local vanilla peg-solving enemy. Local Pengy/SwordKnight/Sparky/WaddleDoo provide Ice/Sword/Spark/Beam, not the peg attack mask.
- Treat shaft is not a treasure check in native objects; only gate consumable checks if those checks are enabled.
- Strict collision graph supports separation; tile15 semantics and complete movement have not been simulated.

#### `peg_221_41_12`

AP region: `REGION_PEPPERMINT_PALACE/ROOM_7_22`.

| Direction | Other room | Door tile | Destination spawn | Native record | Other native fields |
| --- | --- | --- | --- | --- | --- |
| In | 217 | 1, 3 | 57, 19 | `0x888c04c` | Kind 3; Collision 255; Size 14; Flags 2 |
| In | 225 | 4, 88 | 58, 5 | `0x888dd76` | Kind 3; Collision 255; Size 14; Flags 2 |
| Out | 218 | 1, 2 | 15, 3 | `0x888c72c` | Kind 3; Collision 255; Size 14; Flags 2 |
| Out | 225 | 58, 4 | 6, 89 | `0x888c7ee` | Kind 3; Collision 255; Size 14; Flags 1 |
| Out | 217 | 57, 18 | 3, 4 | `0x888cdc0` | Kind 3; Collision 255; Size 14; Flags 1 |

**Compartments.**

- Before opening: Right main chamber includes incoming225 upper-right and217 lower-right, two Giant Rockys, and bomb-block pocket leading to peg.
- After opening: Winding peg-linked tunnel leads from(41,12) down one tile, left to39, up/left via36 and33, then up to top chest pocket(39,3).

**Affected targets.**

- Kind: chest; Object: 0x088C1ADC; Pixel position: 632, 56; Subtype: 20; Name: Pink Spray (wiki identification).

**Independent targets.**

- Destination native: 225; Tile: 58, 4.
- Destination native: 217; Tile: 57, 18.
- Destination native: 218; Tile: 1, 2; Requires: Separate lower-left bombblock route; not the peg-linked chest tunnel.

**Observed sequence.**

- Reach right chamber from225 spawn(58,5) or217 spawn(57,19).
- Upper GiantRocky at(816,160) lies beside bomb(49,10). Super Inhale provides Stone without needing another ability.
- Trigger bomb(49,10) to clear(47,9),(47,10),(48,10), opening peg approach chamber x41..46,y9..12.
- Activate peg(41,12), then follow newly opened winding chain into chest at(39,3).
- Separate bomb(36,18) starts lower-left progression toward218; it does not unlock the top chest.

**Source observations.**

- Object: 0x088C192C; Type: GIANT_ROCKY; Pixel position: 816, 160; Ability: Stone; Prerequisite: Hold inhale until strength3 Super Inhale (about48 ticks). No multi-Kirby requirement.
- Object: 0x088C1A4C; Type: GIANT_ROCKY; Pixel position: 768, 288; Ability: Stone; Prerequisite: Same. Lower-right chamber, outside peg-linked tunnel.

**Caveats.**

- Point connectivity allowing slopes passable and every OTHER mutation destroyed still leaves top chest disconnected until peg chain removed. This is a useful no-other-bomb-bypass proof under that model, not movement feasibility.
- GiantRocky availability is native-vanilla; ability shuffling/randomization must use resolved source assignment, and Super Inhale reach geometry still needs testing.

**Reviewed carry contract.**

Actual resolved statue slots STATUE:353900 and STATUE:3538FC; independently reachable hub190; explicit hub/area requirements. Renewable randomized statues use documented possible-acquisition assumption.

#### `peg_401_28_30`

AP region: `REGION_CANDY_CONSTELLATION/ROOM_9_06`.

| Direction | Other room | Door tile | Destination spawn | Native record | Other native fields |
| --- | --- | --- | --- | --- | --- |
| In | 406 | 7, 7 | 28, 49 | `0x8894bbc` | Kind 3; Collision 255; Size 14; Flags 2 |
| In | 407 | 41, 12 | 3, 49 | `0x8894f6a` | Kind 3; Collision 255; Size 14; Flags 1 |
| In | 408 | 1, 3 | 28, 4 | `0x88955c4` | Kind 3; Collision 255; Size 14; Flags 2 |
| Out | 408 | 28, 3 | 3, 4 | `0x8893010` | Kind 3; Collision 255; Size 14; Flags 1 |
| Out | 407 | 1, 48 | 41, 13 | `0x88933b4` | Kind 3; Collision 255; Size 14; Flags 2 |
| Out | 406 | 28, 48 | 7, 8 | `0x88933c2` | Kind 3; Collision 255; Size 14; Flags 2 |

**Compartments.**

- Before opening: Upper winding shaft and peg approach, reached from408 top entrance; lower-left407 entrance is separated by bomb shortcut.
- After opening: Peg clears right drop shaft x27..28 y31..45 into lower-right406 door pocket.

**Affected targets.**

- Kind: door; Destination native: 406; Destination ap: REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_1; Tile: 28, 48; Object address: 0x088C5888; Check object: 0x088C644C; Check pixel position: 120, 48; Check subtype: 40; Check name: Sound Player (wiki identification).

**Observed sequence.**

- From408 spawn(28,4), descend winding upper passage; Rockys at(288,152) and(240,312) precede peg.
- Press peg(28,30), descend newly empty right shaft, enter406.
- Bomb(6,40) or(7,40) opens separate lower-left shortcut toward407, not the peg shaft. Bomb(22,23) also has a separate chain.

**Source observations.**

- Object: 0x088C5840; Type: ROCKY; Pixel position: 288, 152; Ability: Stone; Before peg: Upper passage; static map places it before peg from408.
- Object: 0x088C5864; Type: ROCKY; Pixel position: 240, 312; Ability: Stone; Before peg: Upper passage; static map places it before peg from408.

**Caveats.**

- Reverse incoming406 starts in lower-right door pocket, below unpressed shaft. Do not assume it can activate peg from there.
- Incoming407 lower-left access to upper area is bomb-shortcut dependent; abilityless bomb reach/attack angle not emulator-tested.
- Slope-relaxed connectivity overconnects this map; strict tile graph supports shaft separation but cannot prove movement or absence of bypass.

**Reviewed carry contract.**

Actual resolved statue slots STATUE:353900 and STATUE:3538FC; independently reachable hub190; explicit hub/area requirements. Renewable randomized statues use documented possible-acquisition assumption.

#### `peg_411_4_3`

AP region: `REGION_CANDY_CONSTELLATION/ROOM_9_08`.

| Direction | Other room | Door tile | Destination spawn | Native record | Other native fields |
| --- | --- | --- | --- | --- | --- |
| In | 405 | 74, 8 | 3, 8 | `0x8894922` | Kind 3; Collision 255; Size 14; Flags 1 |
| In | 418 | 1, 4 | 28, 7 | `0x8898fda` | Kind 3; Collision 255; Size 14; Flags 2 |
| In | 490 | 14, 5 | 3, 19 | `0x889b438` | Kind 3; Collision 255; Size 14; Flags 1 |
| Out | 418 | 28, 6 | 3, 5 | `0x8895aa8` | Kind 3; Collision 255; Size 14; Flags 1 |
| Out | 405 | 2, 7 | 74, 9 | `0x8895ac8` | Kind 3; Collision 255; Size 14; Flags 2 |
| Out | 490 | 1, 18 | 14, 6 | `0x8895b0c` | Kind 3; Collision 255; Size 14; Flags 2 |

**Compartments.**

- Before opening: Main sloping route connecting490 bottom-left hub entrance and418 right entrance; peg on upper-left ledge. Hidden405 door pocket remains blocked.
- After opening: Peg chain clears x4..5 y4..7 wall and hidden-door tiles x2,y6..7 and x3,y7; changes(2,7) to exit collisionFF.

**Affected targets.**

- Kind: door; Destination native: 405; Destination ap: REGION_CANDY_CONSTELLATION/ROOM_9_09; Tile: 2, 7; Object address: 0x088C6AF0; Door subtype: 1.

**Independent targets.**

- Destination native: 418; Tile: 28, 6; Object: 0x088C6B14.
- Destination native: 490; Tile: 1, 18; Object: 0x088C6B38.

**Observed sequence.**

- Enter from490 or418, climb main slope to peg ledge(4,3).
- Press peg to reveal upper-left405 exit;418 and490 exits are independent of peg.

**Source observations.**

- Room: 490; Object: 0x088C8C3C; Type: ABILITY_STATUE_1; Pixel position: 64, 32; Subtype1: 2; Subtype2: 1; Ability: Laser; Randomized slot: STATUE:3538FE.
- Room: 490; Object: 0x088C8C60; Type: ABILITY_STATUE_4; Pixel position: 200, 32; Subtype1: 2; Subtype2: 0; Ability: Cupid; Randomized slot: STATUE:35390E.

**Caveats.**

- No enemies or ability sources inside411. Neighboring490 hub statues grant Laser and Cupid in vanilla, neither solves peg. Randomized statue assignments may supply a solver; must resolve actual mode/seed and gating.
- Incoming405 spawn(3,8) puts center near blocked hidden-door(2,7). Native initialization may clear entry-adjacent tiles; reverse traversal needs separate engine/emulator verification.

**Reviewed carry contract.**

Actual resolved statue slots STATUE:353900 and STATUE:3538FC; independently reachable hub190; explicit hub/area requirements. Renewable randomized statues use documented possible-acquisition assumption.

#### `peg_509_32_2`

AP region: `REGION_CABBAGE_CAVERN/ROOM_3_10`.

| Direction | Other room | Door tile | Destination spawn | Native record | Other native fields |
| --- | --- | --- | --- | --- | --- |
| In | 127 | 10, 17 | 21, 8 | `0x887a068` | â€” |
| In | 508 | 44, 27 | 4, 19 | `0x889b79e` | â€” |
| In | 510 | 2, 5 | 41, 4 | `0x889bd08` | â€” |
| In | 513 | 8, 2 | 43, 17 | `0x889d458` | â€” |
| Out | 510 | 41, 3 | 4, 6 | `0x889b9ac` | â€” |
| Out | 127 | 19, 7 | 12, 18 | `0x889bac8` | â€” |
| Out | 508 | 2, 18 | 43, 28 | `0x889bbd2` | â€” |

**Trigger.**

- Position: 32, 2.
- Record: 0x0889B940.
- Sprite: 0x088C9080.
- Affected: Battery0x088C9038 and meat0x088C905C pocket only.
- Not affected: all three exits.
- Chain cells: 25.

**Routes.**

- From: any initial incoming port; To: battery/meat pocket; Requires: peg_509_32_2; Status: collision separation verified; movement not emulated.

**Source observations.**

none; only Blippers in room

#### `peg_510_7_7`

AP region: `REGION_CABBAGE_CAVERN/ROOM_3_09`.

| Direction | Other room | Door tile | Destination spawn | Native record | Other native fields |
| --- | --- | --- | --- | --- | --- |
| In | 501 | 14, 3 | 24, 29 | `0x889cd08` | â€” |
| In | 509 | 41, 3 | 4, 6 | `0x889b9ac` | â€” |
| Out | 509 | 2, 5 | 41, 4 | `0x889bd08` | â€” |
| Out | 501 | 24, 28 | 14, 4 | `0x889c694` | â€” |

**Trigger.**

- Position: 7, 7.
- Record: 0x0889BD16.
- Sprite: 0x088C90F0.
- Chain cells: 17.

**Routes.**

- From: 509 via spawn4,6 upper; To: chest0x088C9114 at96,456; Alternatives: (peg_510_7_7) OR (ordinary blocks x24..26,y10..26, then bomb_510_21_28, then metal x8..17,y28); Status: peg shaft and metal barrier verified; alternate route movement untested.
- From: 501 via spawn24,29 lower-right; To: same chest; Alternatives: (bomb_510_21_28, then metal x8..17,y28) OR (bomb_510_21_28, then peg_510_7_7); Status: static action-graph alternatives; traversal untested.
- From: upper; To: exit24,28 to501; Requires: ordinary block shaft, independent of peg; Status: collision route verified, movement untested.

**Source observations.**

- Source: HeavyKnight; Pixel position: 216, 112; Record: 0x088C91A4; Compartment: upper; vanilla Sword does not pound pegs.
- Source: Sparky; Pixel position: 56, 120; Record: 0x088C9180; Compartment: upper-left side pocket; interaction reach unverified.
- Source: UFO; Pixel position: 40, 440; Record: 0x088C91C8; Compartment: lower-left chest chamber; do not use to justify own gate.

**Reviewed carry evidence.**

- Path: 592, 528, 513, 509, 510.
- Qualification: 528 wall puff and upper513 transition retain Stone.513 exit0889D458 ->509spawn43,17;509 exit0889B9AC ->510spawn4,6. Exact13px-body initial-map paths reach upperpeg with no prior peg/rope/metal. ChestUFO cannot bootstrap. Horizontalmetal alternate uncredited, not declared impossible.

#### `peg_513_4_7`

AP region: `REGION_CABBAGE_CAVERN/ROOM_3_13`.

| Direction | Other room | Door tile | Destination spawn | Native record | Other native fields |
| --- | --- | --- | --- | --- | --- |
| In | 501 | 2, 28 | 27, 5 | `0x889cef8` | â€” |
| In | 515 | 10, 2 | 27, 19 | `0x889dad0` | â€” |
| In | 528 | 21, 31 | 4, 6 | `0x889cbac` | â€” |
| Out | 509 | 8, 2 | 43, 17 | `0x889d458` | â€” |
| Out | 501 | 27, 4 | 5, 29 | `0x889d466` | â€” |
| Out | 528 | 2, 5 | 21, 32 | `0x889d474` | â€” |
| Out | 515 | 27, 18 | 12, 3 | `0x889d7e2` | â€” |

**Trigger.**

- Position: 4, 7.
- Record: 0x0889D482.
- Sprite: 0x088C9A30.
- Chain cells: 17.

**Routes.**

- From: 501 spawn27,5 or528 spawn4,6 upper; To: exit27,18 to515 spawn12,3; Requires: peg_513_4_7, then bomb_513_5_18; Status: ordered collision action graph; movement untested.
- From: 515 spawn27,19 lower; To: upper exits; Requires: bomb_513_5_18; Note: opens alternative middle passage without activating peg; Status: optimistic reverse bypass; physical movement untested.
- From: upper; To: 509 exit8,2 /501 exit27,4 /528 exit2,5; Requires: none; Status: same initial collision component.

**Source observations.**

none; upper Haley/Foley/Chip, lower Shooty/Foley

**Reviewed carry evidence.**

- Path: 592, 528, 513.
- Qualification: 528 ordinary wall puff and transition retain Stone.513 upper arrivals4,6/27,5 require peg4,7 then bomb5,18 to descend. Lower arrival27,19 can activate bomb then ascend without peg. Exact native terrain body[-6,-5,6,7] and upward-only0F preserve this directed distinction.

#### `peg_527_18_13`

AP region: `REGION_CABBAGE_CAVERN/ROOM_3_14`.

| Direction | Other room | Door tile | Destination spawn | Native record | Other native fields |
| --- | --- | --- | --- | --- | --- |
| In | 528 | 22, 47 | 3, 17 | `0x889cbc8` | â€” |
| Out | 515 | 69, 5 | 2, 3 | `0x889e62c` | â€” |
| Out | 528 | 1, 16 | 22, 48 | `0x889e820` | â€” |
| Out | 515 | 69, 17 | 5, 24 | `0x889e918` | â€” |

**Trigger.**

- Position: 18, 13.
- Record: 0x0889E736.
- Sprite: 0x088CA7F0.
- Chain cells: 10.

**Routes.**

- From: 528 spawn3,17 main; To: lower exit69,17 to515 spawn5,24; Requires: peg_527_56_16; Status: initial tile separation and peg opening verified.
- From: 528 spawn3,17 main; To: upper exit69,5 to515 spawn2,3; Requires: none; Note: no peg tile separates this port; dynamic gate/movement constraints separate; Status: static component only.
- From: upper-left peg approach; To: Sapphire chest0x088CA520 at224,280; Requires: peg_527_18_13; Status: opened local approach verified.
- From: main lower passage; To: Sapphire; Requires: reach bomb_527_38_8 via timed gate, bomb_527_38_8, peg_527_18_13; Note: Prior bomb_527_24_14 bypass disproved by directed0F platform graph. Dynamic gate timing still not simulated.; Status: directed tile separation verified; full movement/timer untested.

**Source observations.**

- Source: GiantRocky; Pixel position: 752, 288; Record: 0x088CA568; Vanilla: Stone; Status: same optimistic main lower component before second peg; dynamic/movement confirmation pending.

**Timed gate.**

- Switch: 0x088CA544.
- Position: 856, 192.
- Door: 0x088CA6F4.
- Door xy: 808, 144.
- Shared room state slot: 1.
- Switch unk18: 100.
- Door initial bounds: -8, -32, 8, 0.
- Note: time-bounded gate; complete timing route not simulated; door absent from point graph.

**Reviewed carry evidence.**

- Path: 592, 528, 527.
- Sequence: ordinary timed switch route, bomb38,8, peg18,13, Sapphire.
- Qualification: Wiki Room14 documents ordinary run through gate. Native timer100 loads102, gradual4px/7-update door animation, ordinary jump/horizontal movement shared by held Stone,176px clear waypoint route. Vanilla timed traversal assumed; no integrated frame schedule or emulator timing replay. No forced damage or ability drop.

#### `peg_527_56_16`

AP region: `REGION_CABBAGE_CAVERN/ROOM_3_14`.

Shares arrivals, exits, Giant Rocky, timed-gate observations, and route alternatives with `peg_527_18_13` above. Its own trigger and carry qualification follow.

**Trigger.**

- Position: 56, 16.
- Record: 0x0889E89A.
- Sprite: 0x088CA814.
- Chain cells: 2.

**Reviewed carry evidence.**

- Path: 592, 528, 527.
- Qualification: Lower515 entrance only. Carry avoids timed-door and rock-body envelopes. Flight terrain bounds(-6,-5,6,7) fit ordinary16px corridors.515 lower chest separate from common exits and isolated513 arrival.

#### `peg_605_12_24`

**Route observations.**

- Arrivals: Source: 601; Record: 0x88a8ede; Spawn: 4, 25; Compartment: peg_platform / Source: 601; Record: 0x88a8a30; Spawn: 3, 18; Compartment: upper_left; Obstacle to peg: F7 x11..13,y18..19 / Source: 606; Record: 0x88aa2c6; Spawn: 7, 17; Compartment: upper_left; Obstacle to peg: F7 x11..13,y18..19 / Source: 621; Record: 0x88ab6e8; Spawn: 44, 5; Compartment: main_maze; Obstacle to peg: separate bomb triangle with F1 at28,27.
- Target: Kind: activated_door; Record: 0x88aa0c4; Tile: 11, 28; Destination: 610; Spawn: 42, 4; Mutation: 0x88aa0b2; Replacement: FF; Then chest: Object: 0x88cfd64; Pixel position: 552, 96; Subtype: 6; Item: Vitality.
- Peg route: peg platform -> peg -> F2 door tile becomes FF -> Chest1 arrival chamber -> Vitality.
- Alternate: No alternative incoming transition to610 found; separate bomb triangle not linked to peg chain.
- Local peg solver: none in inspected vanilla objects; not exhaustive remote ability search.
- Other exit gated: no.

**Reviewed carry evidence.**

- Path: 592, 690, 611, 601, 605.
- Qualification: 601 upper exit112,3. Ordinary puff activates601 bomb5,8. Standing untransformed on0x74 objects088CF8DC and088CFA8C removes605 F7 layers12,18/19 after native delay; no ability drop.

#### `peg_741_27_13`

**Route observations.**

- Arrivals: Source: 712; Record: 0x8884640; Spawn: 4, 39; Compartment: main_bottom / Source: 742; Record: 0x888554e; Spawn: 11, 8; Compartment: isolated_top_annex.
- Target: Kind: loose_1up; Object: 0x88bd984; Pixel position: 440, 264.
- Peg route: main_bottom -> bomb-chain ascents -> upper corridor -> peg -> optional 1-Up cage.
- Annex can reach peg: no.
- Source: Object: 0x88bda80; Kind: Bonkers; Vanilla: Hammer; Before peg: conditional; Obstacle: F5 wall x14..20,y22..23 except17,23; Status: geometry verified; exact playable entry/attack route untested.
- Exit gated: no.

#### `peg_816_26_3`

**Route observations.**

- Arrivals: Source: 802; Records: 0x88a72ba, 0x88a72c8, 0x88a72d6, 0x88a72e4, 0x88a72f2, 0x88a7300; Spawn: 2, 4; Compartment: water_inlet_to_upper_hall.
- Target: Kind: big_chest; Object: 0x88ce86c; Pixel position: 632, 240; Item: Olive Ocean Map.
- Peg route: upper hall -> peg shaft -> lower map pocket.
- Alternate: Obstacle: bomb_wall; Bounds: 44, 12, 50, 13; Bomb: 44, 13; Status: remote/piercing activation from far side or above untested; no ordinary walking bypass.
- Source: Object: 0x88ce8fc; Kind: Bonkers; Vanilla: Hammer; Before peg: yes; Note: normal fight/arena behavior applies.
- Exit gated: no.

**Reviewed carry contract.**

592 ->801 ->191 ->890 ->811 ->830 ->810 ->802 ->816; resolved Stone from either592 regular statue. Avoids rock bodies and opposing currents; ordinary underwater puff activates811/802 bombs while retainingStone. Requires CabbageWest/East andOliveHub connections, Cabbage/OliveAreaKeys whenenabled. No full emulator carry replay claimed.


### Wheel evidence: Rainbow108 race and source carry

The reviewed `wheel_race` provider is Wheel. Its sufficiency is witnessed;
alternatives have not been exhaustively excluded. The enforced AP segment is
`REGION_RAINBOW_ROUTE/ROOM_1_06_LOWER_MID` to
`REGION_RAINBOW_ROUTE/ROOM_1_06_LOWER_CHEST`.

| Evidence point | Native detail |
| --- | --- |
| Race arrival | Room110 return to room108 spawn `(34,19)` |
| Race trigger | Bomb `(36,18)` |
| Target | Chest at pixel `(40,216)` |
| Local source | Room140, `WHEELIE`, stationary subtype2 object `0x088B765C`, pixel `(680,56)` |
| Source approach/departure | Ordinary flight; exit `(1,8)` to room108 spawn `(58,12)`; single-use, not assumed farmable |
| Independent opening | In108 an ordinary air puff activates bomb `(44,17)` while retaining equipment, opening the right wall |
| Detour | Activate `(36,18)`; after mutation use door `(34,18)` to110, to the right of the final closing pillars |
| Return | Room110 door `(7,7)` to108 spawn `(34,19)` with Wheel |

The consolidated uninterrupted native replay began Normal at room140 hub arrival
`(43,9)`, acquired the actual Wheelie, traversed108 right/bomb44/bomb36, entered110,
returned to fresh108, and collected the chest. Every post-copy checkpoint retained
Wheel and6HP. No RAM edits or reloads occurred after initial140 setup. This is a
fixed vanilla replay, not acceptance of every randomized grant or the patched ROM.

Only110 ->108 requires the explicit fresh, unoccupied room-instance opportunity.
Native `level.c:318-358` rebuilds original collision with `RLUnCompWram` for a fresh
room slot; `kirby.c` transitions retain non-Mini equipment. Ordinary single-player
play is assumed able to obtain the opportunity. It is not guaranteed on every door
use, under adversarial AI occupancy, or within bounded attempts; unlimited phone
battery is not assumed.

#### Ability-room fallback provenance

| Evidence point | Native detail |
| --- | --- |
| Entry to970 | From801 tile `(3,4)`, record `0x088730E0`, spawn `(15,6)` |
| Return from970 | Record `0x088B4AB8`, tile `(14,5)`, to801 spawn `(5,4)` |
| Sources | All19 regular statue slots `3538FC..35390E`; each has an ordinary-flight roundtrip from entry to return door |
|801 carrier segment | 28-node two-high air route to exit `0x08873428`, tile `(24,12)`, then190 spawn `(9,3)` |
|190 carrier segment | 14-node two-high air/door route avoids statue envelopes, to exit `0x08879CE4`, tile `(1,8)`, then140 spawn `(43,9)` |
| Complete carry |970 ->801 ->190 ->140 ->108 ->110 ->108; requires Rainbow Route East - Hub Connection |

All15 physical hub-switch activations populate native WORLD slots1..15;
`WorldMapUnlockMain` then sets slot18. AP validates each physical switch location's
reachability, not area-wide events or received Hub Connection items. Actual statue
assignments and ability unlocks apply. There is no forced pickup, obstacle, or
ability change along the reviewed970-to140 carrier geometry. Permanent statues
can be retouched after dropping unwanted results. Positive-support repeated
acquisition relies on fairness, not a finite guarantee; enemy no-ability weight
does not remove statue outputs.

#### Native Normal successes that must not become Wheel gates

- Room424 Music Scores: Normal puff and run collected the chest in an isolated replay.
- Room708: from743 return spawn `(30,29)`, Normal puff and run entered the distinct
  secret exit `(22,28)` to743 spawn `(6,3)`. Other arrivals are not inferred.
