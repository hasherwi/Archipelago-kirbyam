# WiKirby through-wall and remote-hit evidence inventory

Documentation pass and room-prose sweep, reviewed 2026-11-08. This is an evidence shortlist,
not an implemented ability predicate or an exhaustive gameplay audit. No logic,
locations, enemies, ROM patches, item pools, or existing traversal rules change.

## Findings at a glance

| WiKirby room | Target | Evidence classification |
| --- | --- | --- |
| Rainbow Route - Room 8 | Right-hand door to Room 9 | Explicit through-wall requirement; ability list unverified |
| Rainbow Route - Room 28 | Green Spray Paint chest | Beam and Spark explicitly documented; selective lower trigger |
| Rainbow Route - Room 36 | Horizontal route to Room 39 / Mustard Mountain Room 1 | Recessed-trigger traversal candidate; up/down remains an alternative before activation |
| Candy Constellation - Room 6 | Embedded-Bomb-Block shortcut near Chest 1 route | Shortcut candidate; stake route also documented |
| Cabbage Cavern - Room 6 | Chocolate Spray Paint chest | Explicit through-wall requirement |
| Carrot Castle - Room 7 | Mid-left door to Room 13, then its 1-Up chest | Recessed-trigger traversal candidate; exclusivity unproven |
| Carrot Castle - Room 16 | Yellow Spray Paint chest / lower path | Remote reach required for the described solo solution; friends are an explicit alternative |
| Olive Ocean - Goal 2 | Sound Effects chest switch | Through-wall interaction with a documented Ice/frozen-enemy solution; not a Beam/UFO/Master-only gate |
| Radish Ruins - Chest 2 | Bridge to Area Map chest | Remote activation from below is a safer route; damage is an explicit alternative |

Rainbow Route Room 8 and Cabbage Cavern Room 6 explicitly say their targets
require an ability hitting through a wall. The other rows must not be silently promoted to the same hard requirement.
A requirement for one chest or doorway is not a requirement for entering its whole
room, collecting RoomSanity, or using unrelated exits.

## Rainbow Route model and analogous traversals

### Rainbow Route - Room 8: explicit doorway requirement

[Room overview](https://wikirby.com/wiki/Rainbow_Route_-_Room_8#Overview),
[reviewed revision 574491](https://wikirby.com/w/index.php?title=Rainbow_Route_-_Room_8&oldid=574491):

> If the door to Room 9 is desired, Kirby will need to acquire an ability that can hit a bomb block through a wall.

This is the right-hand door near the bottom of the vertical shaft. The lower-left
door leads to Room 12 and the upper door to Room 6. The page has no treasure chest.

- Origin: native **110** (`0x06E`), completion index **27**;
  `REGION_RAINBOW_ROUTE/ROOM_1_08`.
- Destination: native **554** (`0x22A`), completion index **39**;
  `REGION_RAINBOW_ROUTE/ROOM_1_09`.
- Model the specific outgoing edge, not Room 8 entry/RoomSanity or its other exits.
  Do not assume the reverse edge needs the same action.
- The page suggests enemies above can supply a solution and lists Sparky and
  Sword Knight, but does not name Beam as the required solution or exclude other
  abilities. Spark/Sword are therefore leads for this target, not verified moves.
- This textual match confirms a Rainbow Route wall-separated trigger, without
  claiming to identify which room a player's remembered Beam use occurred in.

### Rainbow Route - Room 28: Beam explicitly named, Spark alternative

[Room overview](https://wikirby.com/wiki/Rainbow_Route_-_Room_28#Overview),
[reviewed revision 574509](https://wikirby.com/w/index.php?title=Rainbow_Route_-_Room_28&oldid=574509),
identifies two Bomb Blocks in the floor after the Star Block formation. Only the
lower trigger should be hit to obtain Green Spray Paint; the upper one blocks the
chest. It specifically describes Beam from the platform edge and Spark from a
closer position. Returning through the door allows another attempt.

- Native **138** (`0x08A`), completion index **49**;
  `REGION_RAINBOW_ROUTE/ROOM_1_28`.
- Check: `MINOR_CHEST_SPRAY_PAINT_04`, location **3960503**.
- This is selective trigger reach plus chain state, not proof that every attack
  crossing a wall is safe: hitting both triggers may defeat the solution.
- Spark is an explicit alternative to Beam, so a Beam/UFO/Master-only whitelist
  would omit a documented method. The exit to Room 29 is a separate target.

### Rainbow Route - Room 36: horizontal-route candidate

[Room overview](https://wikirby.com/wiki/Rainbow_Route_-_Room_36#Overview),
[reviewed revision 571793](https://wikirby.com/w/index.php?title=Rainbow_Route_-_Room_36&oldid=571793),
says an ability must reach the left/right Bomb Blocks for the horizontal route;
without it, Kirby must go up/down. Activating the blocks closes those vertical
paths instead. The left exit is Room 39, the right Mustard Mountain Room 1, the
upper Room 35, and the lower Room 37.

- Native **538** (`0x21A`), completion index **15**.
- Existing AP compartments: `REGION_RAINBOW_ROUTE/ROOM_1_36_VERTICAL` and
  `REGION_RAINBOW_ROUTE/ROOM_1_36_HORIZONTAL`.
- Candidate is a stateful transition to the horizontal route, not a permanent
  requirement on all four doors. Check each arrival side and resulting geometry.
  WiKirby does not explicitly name wall collision or enumerate valid abilities.

### Candy Constellation - Room 6: analogous embedded-trigger shortcut

[Room overview](https://wikirby.com/wiki/Candy_Constellation_-_Room_6#Overview)
describes a wall-embedded Bomb Block shortcut near the downward Chest 1 route,
while also describing pounding a stake to expose that route. This is a useful
analog of the Room 8 pattern, but not evidence that Chest 1 exclusively requires
wall piercing. Exact shortcut endpoints still need a map/geometry check.

- Native **401** (`0x191`), completion index **143**;
  `REGION_CANDY_CONSTELLATION/ROOM_9_06`.
- Chest 1 is native **406** (`0x196`), completion index **148**;
  `REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_1`.
- Keep the stake-pounding alternative and embedded-trigger shortcut distinct;
  neither is established here as a source-aware randomized witness.

## 1. Cabbage Cavern - Room 6: confirmed textual requirement

[Room overview](https://wikirby.com/wiki/Cabbage_Cavern_-_Room_6#Overview):

> Kirby will need an ability that can pass through the wall to activate it

The target is the Bomb Block embedded in the wall near the left end of the path,
opening the Chocolate Spray Paint chest chamber. The
[Treasure guide](https://wikirby.com/wiki/Treasure#Kirby_&_The_Amazing_Mirror)
independently names Beam as a way to hit this otherwise inaccessible block.

- Native room **517** (`0x205`), completion index **182**.
- AP room: `REGION_CABBAGE_CAVERN/ROOM_3_06`.
- AP check: `MINOR_CHEST_SPRAY_PAINT_12`, location **3960511**.
- WiKirby lists a local Waddle Doo. This describes vanilla availability, not a
  guaranteed Beam source with shuffled enemies/abilities.
- The text does not apply this restriction to the Room 7 or Hub 2 exits.
- Before implementation, establish exact attack/position witnesses and negative
  controls. A nearby Bomber/Crash source is listed too; this pass does not test
  whether screen-wide effects provide additional solutions.

## 2. Carrot Castle - Room 7: traversal candidate

[Room overview](https://wikirby.com/wiki/Carrot_Castle_-_Room_7#Overview):

> the door to Room 13 can be accessed if Kirby can reach the Bomb Block in the back of the barrier

This is a specific mid-left doorway, not the Room 8/Room 14 exits and not the
cherry chest on Room 7's upper-right branch. The text identifies a recessed
trigger, but does not explicitly say every non-piercing attack fails or enumerate
valid abilities. Treat wall piercing as a hypothesis pending geometry/runtime
verification.

- Origin: native **719** (`0x2CF`), completion index **258**;
  `REGION_CARROT_CASTLE/ROOM_5_07`.
- Destination: native **734** (`0x2DE`), completion index **261**;
  `REGION_CARROT_CASTLE/ROOM_5_13__LOGIC__ENTRY_FROM_5_07`.
- Associated check: `MINOR_CHEST_CARROT_CASTLE_5_13_OBJECT_02`, location
  **3960606**.
- [Room 13](https://wikirby.com/wiki/Carrot_Castle_-_Room_13#Overview) says entering
  from Room 7 reaches the **1-Up**, whereas entering from Room 14 reaches the
  **Secret Notes**. Do not gate the Secret Notes on this Room 7 trigger.
- WiKirby lists Waddle Doo in Room 7, but this is not a proof of exclusivity or a
  source-aware randomized traversal witness.

## 3. Carrot Castle - Room 16: remote reach, with cooperation alternative

[Room overview](https://wikirby.com/wiki/Carrot_Castle_-_Room_16#Overview):

> an ability with long reach is needed, or perhaps Kirby's new friends can help

The upper Bomb Block must be activated without committing Kirby to that upper
path, so that he can enter the lower path and collect Yellow Spray Paint. The
[Treasure guide](https://wikirby.com/wiki/Treasure#Kirby_&_The_Amazing_Mirror)
also describes remote activation and help from friends.

- Native **733** (`0x2DD`), completion index **260**.
- AP room: `REGION_CARROT_CASTLE/ROOM_5_16`.
- AP check: `MINOR_CHEST_SPRAY_PAINT_02`, location **3960501**.
- Confirm whether the intended shot actually crosses solid collision, rather
  than merely needing reach/angle. WiKirby's wording alone does not settle that.
- Do not infer that the ordinary upper path, Shadow Kirby encounter, or exit to
  Room 9 needs the same capability. Cooperation is documented, but not thereby
  admitted as a reliable single-player randomizer witness.

## 4. Olive Ocean - Goal 2: include the Ice solution

[Room overview](https://wikirby.com/wiki/Olive_Ocean_-_Goal_2#Overview) places the
Sound Effects chest and its switch inside the same gated chamber, after Mr.
Frosty. The [Treasure guide](https://wikirby.com/wiki/Treasure#Kirby_&_The_Amazing_Mirror)
describes freezing a Waddle Dee and kicking it through the wall onto the switch.

- Native **825** (`0x339`), completion index **203**.
- AP room: `REGION_OLIVE_OCEAN/ROOM_6_GOAL_2`.
- AP check: `MINOR_CHEST_MUSIC_NOTE_10`, location **3960523**.
- This is relevant through-wall interaction evidence, but it contradicts a
  restrictive whitelist containing only Beam, UFO, and Master.
- Test whether those abilities can operate this particular switch, and model
  availability of a freezeable enemy if the Ice solution is later admitted.
  The room's boss and goal exit are separate targets.

## 5. Radish Ruins - Chest 2: safer optional route

[Room overview](https://wikirby.com/wiki/Radish_Ruins_-_Chest_2#Overview) says the
Bomb Block above the spike corridor must be activated from below to make the
bridge useful. It also explicitly permits skipping that process, likely taking
a hit. Thus the Area Map is not documented as exclusively wall-piercing-gated.

- Native **617** (`0x269`), completion index **237**.
- AP room: `REGION_RADISH_RUINS/ROOM_8_CHEST_2`.
- Whether the trigger needs wall piercing rather than ordinary upward reach is
  unverified. Damage/health assumptions also need separate validation.

## False positives and different puzzle classes

- [Olive Ocean - Room 9](https://wikirby.com/wiki/Olive_Ocean_-_Room_9#Overview),
  native **823**: the caption says Kirby cannot quite reach the Bomb Block
  through the wall. Its cherry-chest solution is to enter from the **Hub**, not
  Room 8, avoiding the block that seals the chest. This is entry/chain-state
  evidence, not confirmation of a through-wall-required chest. A longer-reaching
  alternative remains untested, not disproved for every ability.
- [Candy Constellation - Room 16](https://wikirby.com/wiki/Candy_Constellation_-_Room_16#Overview):
  Kirby's Sounds is described as a race against a Bomb Block chain that reseals
  the chest. No exclusive piercing requirement is stated.
- [Olive Ocean - Room 5](https://wikirby.com/wiki/Olive_Ocean_-_Room_5#Overview):
  taking optional snacks through a wall is mentioned, without specifying an
  exclusive attack requirement; this is not a chest or door gate.
- [Peppermint Palace - Room 7](https://wikirby.com/wiki/Peppermint_Palace_-_Room_7#Overview):
  an outside ability is needed for the Chest doorway, but the description does
  not identify wall-piercing. Do not conflate a metal-block requirement with an
  attack passing through solid collision.
- General mentions of Beam in enemy tables or the navigation footer are not
  room-specific constraint evidence. Wall-clipping glitches and other games'
  rooms are outside this inventory.

## Ability evidence and its limits

The investigation starts with Beam, UFO, and Master as requested candidates;
Smash's landing shockwave now has source-level terrain-bypass evidence (see follow-up below). This does not assert that those three are sufficient
for every row, or that no other ability works.

| Ability | What WiKirby supports | What remains unverified |
| --- | --- | --- |
| Beam | Treasure guide identifies it for Cabbage Cavern Room 6; Room 28 explicitly describes its use for Green Spray Paint | Other individual triggers, angles, and safe positions |
| UFO | [Amazing Mirror moveset](https://wikirby.com/wiki/UFO#Kirby_&_The_Amazing_Mirror) says the long-hold Piercing Heat Beam pierces walls | Specific targets and applicable charge/move; do not equate every UFO attack with this property |
| Master | [Article](https://wikirby.com/wiki/Master#Kirby_&_The_Amazing_Mirror) describes a charged energy wave and broad puzzle-solving capability except Mini puzzles | Exact move and collision behavior per target; the broad claim is not a controller witness |
| Smash | [Amazing Mirror moveset](https://wikirby.com/wiki/Smash_Bros.#Kirby_&_The_Amazing_Mirror) includes Final Cutter and its shockwave | WiKirby alone did not establish wall penetration; the pinned source follow-up establishes terrain bypass, but not per-target success |
| Spark | Rainbow Route Room 28 explicitly describes a closer-position solution | Room 8 is a lead only; exact moves and collision behavior still need testing |
| Ice | Treasure guide supplies the frozen-Waddle-Dee solution for Olive Goal 2 | Exact enemy/source/position and switch timing under randomization |

## Additional remote-action result outside the wall-separated-trigger class

[Mustard Mountain - Chest](https://wikirby.com/wiki/Mustard_Mountain_-_Chest#Overview)
(native **310**, `REGION_MUSTARD_MOUNTAIN/ROOM_4_CHEST`) describes remotely
operating a nearly immediate switch gate, with friends as a possible solution.
This is a timing/cooperation candidate, not evidence of a solid wall between the
attack and switch. Keep it out of a through-wall-only rule.

## Method, coverage, and next steps

1. Search WiKirby for through-wall, embedded/recessed Bomb Blocks, long reach,
   remote activation, ranged attacks, and ability-specific wall interaction.
   Cross-check named-area queries and discard other-game results.
2. Review the Amazing Mirror significant-collectibles table on the Treasure
   page, then inspect candidate room pages and distinguish required actions,
   optional routes, alternatives, and unrelated targets.
3. Join room names to the existing
   [native/WiKirby inventory](native-room-wikirby-map.md) and check identifiers
   against `data/regions/rooms.json` and `data/locations.json` on base
   `370dbb4` (main at branch creation).

The first search-led pass missed Rainbow Route Room 8. The follow-up uses its
specific pattern as a reusable test: **identify a destination, find the trigger
separated from Kirby by a wall/barrier, establish that an attack must reach it,
and preserve entry direction, changed barriers, and documented alternatives**.
Search results and the significant-treasures table are discovery aids, not
coverage evidence.

A direct fetch was attempted for every one of the **263** main-area room URLs in
the native/WiKirby inventory. **250** returned overview/description prose that
was screened for wall-separated triggers, recessed/embedded Bomb Blocks, remote
activation, long reach, shortcuts, and related reach/barrier wording. Hits were
reviewed in context, including the page's linked destinations and enemy table.
The remaining **13** failed retrieval and remain unreviewed. A follow-up public
HTML retrieval recovered Rainbow Route Room 21 (revision 574497): its ascent
and Bomb Blocks do not state a wall-separated trigger. Further retrievals
returned HTTP 403; access restrictions were respected. Remaining gaps:

- Rainbow Route: Room 24; Hub 2.
- Cabbage Cavern: Room 10.
- Peppermint Palace: Rooms 2 and 23.
- Radish Ruins: Rooms 2, 6, and 23.
- Olive Ocean: Rooms 3, 21, 22, and 23.
- Candy Constellation: Room 8.

The [per-room coverage manifest](wikirby-through-wall-coverage.json) records all
263 titles/URLs and screening status. Prose screening is not an exhaustive
mechanics audit: wording can omit a constraint, and a non-hit is not evidence of
absence. No room-map pixels, ROM geometry, collision code, or controller tests
were inspected during the initial prose sweep. Subsequent source analysis and one
qualified native Spark witness are linked below; they do not retroactively verify
all prose candidates.

Next, inspect candidate maps and validate each
candidate from every relevant entry. Record move/charge, attack origin and target,
solid tiles crossed, enemy/source availability, chain state, alternatives, and
failures. Keep a one-target proof separate from a global ability capability.
Only then propose source-aware logic and regression tests.


## Range investigation: source evidence versus measurements

The comparison must be move-specific, not a single global "ignores collision"
flag. Source-derived numeric envelopes are now available in the linked follow-up, but
no maximum-distance target-hit sweep has been measured for all six abilities. A successful target hit is a lower bound, not a maximum; a failed
hit can reflect alignment or chain state rather than range.

| Ability/move | Evidence applicable to Amazing Mirror | Range and per-room comparison still needed |
| --- | --- | --- |
| Beam whip | Room 28 explicitly permits an edge-position lower-trigger hit; Cabbage 6 has a documented Beam solution | Horizontal/vertical hitbox envelope during the sweep, facing, wall thickness, and target-specific placement |
| Spark barrier | Room 28 explicitly permits a closer-position solution; the [Spark article](https://wikirby.com/wiki/Spark#Kirby_&_The_Amazing_Mirror) describes the same basic version as Nightmare in Dream Land | Barrier radius and overlap through walls. Beam's longer-reaching placement does not prove Spark can substitute at every target |
| UFO Piercing Heat Beam | Long-hold projectile explicitly pierces walls | Charge threshold, travel lifetime/distance, height alignment, camera/despawn limits and trigger activation |
| Master energy wave | Charged ranged move and broad puzzle utility are documented | Separate wave travel from sword hitbox; collision, range, and low/raised targets |
| Smash Final Cutter | Amazing Mirror moveset explicitly lists a landing shockwave | Shockwave collision, lifetime and height; upward/downward blade hitboxes are distinct. Still not confirmed wall-piercing |
| Ice: kicked frozen enemy | Olive Goal 2 documents the frozen-Waddle-Dee switch solution; [Ice article](https://wikirby.com/wiki/Ice#Kirby_&_The_Amazing_Mirror) supports freezing and kicking enemies | Projectile path/range, floor and wall behavior, thaw/despawn, available freezable enemy, and launch alignment. Ice breath is a separate attack |

Do not import Spark's chargeable wall-piercing projectiles from Squeak Squad or
later games into Amazing Mirror. Likewise, the Squeak Squad Ice Scroll's aim
control is not evidence for Amazing Mirror. The reviewed WiKirby pages provide
no numeric maximum distances, and do not establish Spark as equivalent to Beam.
"Created ice blocks" is treated here as kicked frozen enemies, not a claim that
Ice can spawn a free projectile without a suitable enemy.

For each target above, reset the room/chain state and record: native room and
entry, move/charge, player and target pixel coordinates, launch position and
facing, wall tiles crossed, successful/failed distances, and the opened route or
collected check. Test both facings and targets above/below where geometry permits.
For projectiles, also record frames alive and camera position. Freeze-and-kick
trials must identify the actual enemy and source; do not substitute an injected
ice projectile for proof that the room supplies one. A synthetic geometry test
can measure a move but must not be represented as natural room accessibility.


## Native follow-up and expanded small-switch scope

- [Move-specific source ranges](collision-avoiding-attack-ranges.md): Spark reaches 23 pixels sideways; Beam's forward envelope is 59; Master wave 118; Smash landing shockwave about 86. These are source-derived attack edges, not universal target-center distances or demonstrated maximum-distance switch hits. UFO and kicked frozen enemies are camera-limited rather than governed by a fixed flight timer. Laser and Cupid are terrain-colliding remote options.
- [Rainbow Route Room 8 Spark witness](rainbow-route-8-spark-witness.md): a continuous qualified vanilla-engine replay opened the intended wall-separated trigger and reached Room 9 (native 554). A no-attack replay stayed in 110. Startup placement and an essence substitution mean this proves physical feasibility after acquiring Spark, not source-aware randomized accessibility.
- [Exhaustive native small-switch inventory](small-switch-inventory.md): 23 instances in 19 native rooms, all 983 slots and 287 object lists scanned. Room-by-room WiKirby classifications distinguish ordinary contact/timing, remote alternatives, cooperation and separated targets. Moonlight Mansion Room 19 is a clear-static-row ranged alternative; Mustard Chest/Room 15 require additional trajectory/timing work. No blanket Laser, Cupid, Ice, UFO or Phone grant is implemented.

Spark's Room 8 success and WiKirby's Room 28 solution do **not** prove that it
replaces Beam at every target. Other room/move witnesses and the 13 failed prose
retrievals remain open. The small-switch scan is exhaustive for static native
templates (including the 18 native spawners checked), not every possible dynamic
object creation or every gameplay solution.
