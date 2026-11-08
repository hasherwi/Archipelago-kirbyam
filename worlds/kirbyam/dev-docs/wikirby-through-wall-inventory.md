# WiKirby through-wall and remote-hit evidence inventory

Initial documentation pass, reviewed 2026-11-08. This is an evidence shortlist,
not an implemented ability predicate or an exhaustive gameplay audit. No logic,
locations, enemies, ROM patches, item pools, or existing traversal rules change.

## Findings at a glance

| WiKirby room | Target | Evidence classification |
| --- | --- | --- |
| Cabbage Cavern - Room 6 | Chocolate Spray Paint chest | Explicit through-wall requirement |
| Carrot Castle - Room 7 | Mid-left door to Room 13, then its 1-Up chest | Recessed-trigger traversal candidate; exclusivity unproven |
| Carrot Castle - Room 16 | Yellow Spray Paint chest / lower path | Remote reach required for the described solo solution; friends are an explicit alternative |
| Olive Ocean - Goal 2 | Sound Effects chest switch | Through-wall interaction with a documented Ice/frozen-enemy solution; not a Beam/UFO/Master-only gate |
| Radish Ruins - Chest 2 | Bridge to Area Map chest | Remote activation from below is a safer route; damage is an explicit alternative |

Only the first row explicitly says the target requires an ability passing through
a wall. The other rows must not be silently promoted to the same hard requirement.
A requirement for one chest or doorway is not a requirement for entering its whole
room, collecting RoomSanity, or using unrelated exits.

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
Smash remains unconfirmed. This does not assert that those three are sufficient
for every row, or that no other ability works.

| Ability | What WiKirby supports | What remains unverified |
| --- | --- | --- |
| Beam | Treasure guide identifies it for Cabbage Cavern Room 6 | Other individual triggers, angles, and safe positions |
| UFO | [Amazing Mirror moveset](https://wikirby.com/wiki/UFO#Kirby_&_The_Amazing_Mirror) says the long-hold Piercing Heat Beam pierces walls | Specific targets and applicable charge/move; do not equate every UFO attack with this property |
| Master | [Article](https://wikirby.com/wiki/Master#Kirby_&_The_Amazing_Mirror) describes a charged energy wave and broad puzzle-solving capability except Mini puzzles | Exact move and collision behavior per target; the broad claim is not a controller witness |
| Smash | [Amazing Mirror moveset](https://wikirby.com/wiki/Smash_Bros.#Kirby_&_The_Amazing_Mirror) includes Final Cutter and its shockwave | No reviewed statement establishes wall penetration or success at these targets; do not add it as confirmed |
| Ice | Treasure guide supplies the frozen-Waddle-Dee solution for Olive Goal 2 | Exact enemy/source/position and switch timing under randomization |

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

This is a search-led first pass, **not a claim that all 263 main-area room pages
were read end-to-end**. The Treasure table excludes ordinary consumable chests;
search absence does not prove a room has no relevant constraint. No emulator,
ROM geometry, collision code, or controller test was run for this document.

For a later complete audit, use the 263-room inventory as a checklist and record
reviewed/unreviewed status, examine remaining ordinary chests and doorways, then
validate each candidate from every relevant entry. Record move/charge, attack
origin and target, solid tiles crossed, enemy/source availability, chain state,
alternatives, and failures. Keep a one-target proof separate from a global
ability capability. Only then propose source-aware logic and regression tests.
