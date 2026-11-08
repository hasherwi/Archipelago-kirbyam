# Metal-block room inventory and WiKirby cross-check

## Scope and findings

The native collision-map inventory covers all **983 room-property slots** of the
unmodified USA ROM: **286 populated rooms** and **697 exact unused sentinels**.
It finds **33 rooms containing ordinary metal**, totaling **358 tiles**.
A separate generic environmental collision class occurs in **25 rooms**, totaling **331 tiles**; seven
rooms contain both, for **51 distinct rooms** in the combined review list.

This is a presence inventory, not a reachability proof. A block may guard a
pickup, provide a shortcut, or be removed by a cannon/environmental mechanism.
Do not turn these room names into blanket ability requirements.

See the reproducible [scanner](../tools/scan_metal_tiles.py), the
[native inventory](../docs/metal-tile-inventory.json), and the structured
[WiKirby review](metal-block-wikirby-review.json). Raw ROMs, extracted artwork,
and complete collision grids are not published.

## Native classification

`ProcessAttackTileCollisions` in the [native collision code][collision] filters
attack/tile overlap by collision class:

- Ordinary metal: collision ID `0xF5`, attributes `0x201200`, class `0x200000`,
  requires the attack's `0x1000` flag.
- Environmental: collision ID `0xF7`, attributes `0x401200`,
  class `0x400000`, requires `0x800`, not the ordinary-metal ability flag.
- `0xF6` is deliberately excluded from the metal count. Its class `0x300000`
  uses flag `0x4000` and an activation path; numerical adjacency is not proof
  that it is another metal type.

WiKirby's [Block article][block] describes reinforced metal as removed by a
falling Heave-Ho Block or a Bomb Block mechanism; that visual description is not
a one-to-one mapping to F7. The native constructors
`CreateLargeStarStoneBlock7E`, `CreateLargeStarStoneBlock88`,
`CreateLargeStarStoneBlock89`, and `CreateLargeStarStoneBlock7D` set attack flag
`0x800` ([7E source][heavy], [7D source][heavy7d]). The environmental-only rows are
kept separate from ordinary metal and ordinary ability gates. Room-specific
mechanism still needs room-level acceptance; a wiki label is not a substitute
for collision data.

### Exhaustiveness audit

The scan and writer audit use native source revision
`7d969fbce14fdc838d2c1ea01389717fb96c3189` and USA ROM SHA-1
`274b102b6d940f46861a92b4e65f89a51815c12c`.
All valid collision maps are decoded, and every solidity mutation record is
checked for replacement bytes introducing F5/F6/F7. None introduces additional
tracked tiles. All initial tracked tiles have matching mutation records.
The complete valid-room list and unused-slot list are retained even for rooms
with no metal, so coverage is independently checkable against the native map.

The native grid writer audit found references to `gUnk_02024ED0` only in
[`level.c`](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/level.c)
(initialization/RL decompression) and
[`code_080023A4.c`](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/code_080023A4.c)
(reads, mutation helper `sub_08001408`, setter `sub_0800255C`), with no assembly
references. The setter's callers in
[`mirror_door.c`](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/mirror_door.c)
only clear and restore the prior tile. This closes the additional generated-map
metal question for this revision. **51 is the exhaustive native collision-map
F5/F7 room set**, not a claim to inventory every destructible object or prove
all room transitions.

### Correction: F7 is not synonymous with reinforced metal

The initial version overclassified all 25 F7-positive rooms as reinforced metal.
Native rooms 535, 601, and 605 have F7 tiles paired with `DestroyableRockBlock`
object `0x74`: `sub_0811BF24` detects standing contact and waits ten ticks, then
`sub_0811C07C` removes the tile. These are crumble floors, not evidence of a
reinforced-metal barrier. F7 also occurs in stone/cannon arrangements. The scan
is correct, but classifying all its F7 rows as reinforced metal was incorrect.
Keep all 25 rows as environmental candidates pending object/visual matching;
ordinary F5 counts are unaffected. See [native crumble implementation](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/destroyable_rock_block.c).

### Bomb-chain distinction under review

Do not equate the wiki visual label "reinforced" with every F7 tile. Native
`sub_0800E27C` propagates Bomb/peg destruction through four-neighbor tiles with
attribute `0x40`; F7 (`0x401200`) lacks that bit. F2 (`0x240`) and F3 (`0x41`)
participate in that separate chain category, triggered by F1 (`0x101260`).
Whether the wiki's visual reinforced category also includes F2 needs visual and
native mapping. The 51-room result is exhaustive for F5/F7, **not yet a claim
that every visually reinforced or Bomb-controlled tile is inventoried**. No
F7-to-Bomb relationship should be inferred from room co-occurrence alone.

## Cross-check method and limits

The native scan supplies the room set, including rooms whose prose never says
“metal.” Each positive room was joined to the repository's verified
[native-to-WiKirby map](native-room-wikirby-map.json), then its linked article was
opened and reviewed for puzzle/entry/target context. **All 51 pages were read**.
Four initially failed in the search reader, but their normal public HTML pages
were retrieved successfully and reviewed on 2026-11-08. In 28 ordinary-metal
rooms, prose or captions explicitly identify metal; the other articles provide
context without naming that class. The review JSON preserves the recovered
revision IDs and retrieval method.
This pass reviewed prose/captions, not every composite-map pixel.

No new traversal rules, ability-item classification, starting inventory, or runtime
patches are introduced. The isolated Hammer acceptance is recorded separately. In particular:

- Preserve the previously demonstrated Normal exits in Olive Ocean Rooms 12 and 21.
- Aerial Hammer cleared the isolated no-side floor plug in native room 205.
  [Acceptance evidence](metal-hammer-floor-acceptance.json) preserves the setup and limits.
- Completed Stone can enter water and sink; starting Stone while swimming is a
  different, unavailable action. See the corrected [ability notes](metal-block-traversal-preparation.md).
- Vanilla local abilities, Mix outcomes, and sources behind a barrier are not
  automatic guarantees under randomization.

## Every native-positive room

O = ordinary metal; E = generic F7 environmental class, not necessarily metal.
The native JSON retains coordinates/counts. The last column is a contextual
research note and next check, **not a validated traversal rule**.

| Native ID | WiKirby room | Class | WiKirby review | Context and next check |
| --- | --- | --- | --- | --- |
| 102 | [Radish Ruins - Room 22](https://wikirby.com/wiki/Radish_Ruins_-_Room_22) | E | Context; class not named | Lower tunnel to Battle Notes is blocked by a Heave-Ho Block. Inspect its falling path and the F7 environmental tiles rather than assigning a copy-ability gate. |
| 117 | [Rainbow Route - Room 24](https://wikirby.com/wiki/Rainbow_Route_-_Room_24) | E | Context; class not named | Horizontal log/barrel hall; Mirra protects the Carrot Castle door. Article does not name F7 environmental tiles; determine which environmental barrier uses them. |
| 121 | [Carrot Castle - Room 3](https://wikirby.com/wiki/Carrot_Castle_-_Room_3) | E | Context; class not named | Wooden platforms above a pit, with two left exits and a hidden Star Block door. Article does not identify F7 environmental tiles or their function. |
| 132 | [Olive Ocean - Room 4](https://wikirby.com/wiki/Olive_Ocean_-_Room_4) | E | Context; class not named | Coastal path divides into upper and lower approaches to Room 5. Article does not identify the F7 environmental tile mechanism. |
| 134 | [Olive Ocean - Room 6](https://wikirby.com/wiki/Olive_Ocean_-_Room_6) | E | Context; class not named | Upper and Mini routes converge toward Goal 1; the Ocean Spray Paint route uses a Heave-Ho Block and Mini passage. Match F7 coordinates to the relevant mechanism; do not equate these with ordinary metal. |
| 141 | [Rainbow Route - Room 41](https://wikirby.com/wiki/Rainbow_Route_-_Room_41) | O | Explicit metal | Mixed Star/metal barriers between grassy platforms, with local Flamers. Multiple entrances and upper-right exits require separate source and approach analysis. |
| 149 | [Moonlight Mansion - Room 20](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_20) | E | Context; class not named | Stone slope, pegged chest barrier, and underwater channel. Article does not call out F7 tiles; match the native cluster to the environmental mechanism. |
| 176 | [Rainbow Route - Goal 2](https://wikirby.com/wiki/Rainbow_Route_-_Goal_2) | O | Explicit metal | Batafire chamber has a metal-blocked Energy Drink chest to its right. Burning from the defeated mid-boss is a vanilla candidate; the Goal door is a separate target. |
| 205 | [Peppermint Palace - Room 7](https://wikirby.com/wiki/Peppermint_Palace_-_Room_7) | O | Explicit metal | Article caption identifies a metal barrier; most doors are accessible but Chest-room access needs an outside ability. Aerial Hammer cleared the isolated native floor plug; source access and other clearance still need validation. |
| 216 | [Peppermint Palace - Room 19](https://wikirby.com/wiki/Peppermint_Palace_-_Room_19) | O | Explicit metal | Metal barricade protects a 1-Up chest in the icy tunnel. Article calls for an outside ability; validate carried equipment and contact from each approach. |
| 228 | [Peppermint Palace - Room 9](https://wikirby.com/wiki/Peppermint_Palace_-_Room_9) | O | Explicit metal | Right-hand metal branch leads to a 1-Up chest; other branches include a rope puzzle and three exits. Destructive choices can block other compartments. |
| 229 | [Peppermint Palace - Room 10](https://wikirby.com/wiki/Peppermint_Palace_-_Room_10) | O | Explicit metal | Left side passage from the tower leads to a metal-blocked 1-Up chest. Keep this distinct from the Grape Spray Paint tower and main Warp route. |
| 308 | [Mustard Mountain - Room 9](https://wikirby.com/wiki/Mustard_Mountain_-_Room_9) | O | Explicit metal | Two entrances supply Flamer or Rocky before paths merge. Metal protects a 1-Up along the tunnel; a second 1-Up beyond the exit has different hazards. |
| 312 | [Mustard Mountain - Room 18](https://wikirby.com/wiki/Mustard_Mountain_-_Room_18) | O/E | Context; class not named | Article describes ruin chambers and Minny access to the Warp route, but does not name the metal tiles. Both native classes occur; map them to compartments before inferring a gate. |
| 317 | [Mustard Mountain - Room 17](https://wikirby.com/wiki/Mustard_Mountain_-_Room_17) | O | Context; class not named | Entry from Room 15 leads through Phan Phan; entry from Room 16 bypasses that fight. Article does not name metal; native presence must not become a mandatory boss/Throw rule. |
| 405 | [Candy Constellation - Room 9](https://wikirby.com/wiki/Candy_Constellation_-_Room_9) | O | Explicit metal | Chest 2 return enters the upper path; an ability from that chest room can break a metal barrier for a 1-Up. Entry direction and source accessibility matter. |
| 414 | [Candy Constellation - Room 11](https://wikirby.com/wiki/Candy_Constellation_-_Room_11) | O/E | Explicit metal | Side passage behind metal and spikes contains a 1-Up. Another 1-Up triggers Heavy Knights and a Bomb Block response. Separate ordinary and F7 environmental clusters. |
| 415 | [Candy Constellation - Room 14](https://wikirby.com/wiki/Candy_Constellation_-_Room_14) | O | Context; class not named | Path continues right after Master Hand, past barriers and oversized enemies. Article does not explicitly label metal; Smash and Giant Rocky are vanilla candidates, not proven access rules. |
| 419 | [Candy Constellation - Room 13](https://wikirby.com/wiki/Candy_Constellation_-_Room_13) | O | Explicit metal | Lower of two passages splits again; the lower branch has metal, spikes, Flamers, and a Maxim Tomato before Chest 3. Upper passage leads to Warp. Do not use a Flamer behind the barrier to justify entry. |
| 421 | [Candy Constellation - Room 18](https://wikirby.com/wiki/Candy_Constellation_-_Room_18) | O | Explicit metal | Open airborne route includes a Maxim Tomato behind metal. Local UFO is a vanilla candidate; charged shot position and barrier overlap still need verification. |
| 502 | [Radish Ruins - Room 16](https://wikirby.com/wiki/Radish_Ruins_-_Room_16) | O | Context; class not named | Open canyon with a Bomb Block 1-Up and Fuse Cannon near exits. Article does not name ordinary metal; inspect its native coordinates against those mechanisms. |
| 510 | [Cabbage Cavern - Room 9](https://wikirby.com/wiki/Cabbage_Cavern_-_Room_9) | O | Explicit metal | Upper peg opens the 1-Up chamber; UFO can appear inside and break its right-hand metal exit. That internal source cannot justify entering the chamber from outside. |
| 512 | [Cabbage Cavern - Room 4](https://wikirby.com/wiki/Cabbage_Cavern_-_Room_4) | O | Explicit metal | Different Room 3 doors enter different compartments. Food and a battery sit between metal sets near the Rainbow Route door; audit optional pickup access separately from exits. |
| 527 | [Cabbage Cavern - Room 14](https://wikirby.com/wiki/Cabbage_Cavern_-_Room_14) | E | Context; class not named | Timed gate, Sword Knight, and Bomb Block sequence leads to Sapphire paint. Native F7 environmental tiles belong in that environmental-state audit, not the ordinary-metal ability list. |
| 529 | [Cabbage Cavern - Room 3](https://wikirby.com/wiki/Cabbage_Cavern_-_Room_3) | O | Explicit metal | Flooded tunnels split by metal into two channels, also connected at a bottomless pit. Air-pocket drink and left/right routes need water-state and entry-specific analysis. |
| 531 | [Cabbage Cavern - Goal](https://wikirby.com/wiki/Cabbage_Cavern_-_Goal) | E | Context; class not named | Tunnel maze with a Bomb Block barrier protecting the area map, then a stone-barrier chamber before the Goal door. Article does not name F7 environmental metal explicitly. |
| 532 | [Rainbow Route - Room 27](https://wikirby.com/wiki/Rainbow_Route_-_Room_27) | O/E | Explicit metal | Cannons launch through a spike section toward metal; ladders above reach Room 28. Return Bomb Block changes access. Cannon-based breaking must be considered independently of copy abilities. |
| 533 | [Mustard Mountain - Room 15](https://wikirby.com/wiki/Mustard_Mountain_-_Room_15) | O/E | Explicit metal | Metal blocks a Gordo side chamber; Bomb Block order can contain or release the Gordos. Main exits, timed gate, and occasional UFO are separate route/source questions. |
| 535 | [Rainbow Route - Room 35](https://wikirby.com/wiki/Rainbow_Route_-_Room_35) | E | Context; class not named | Short paired spike tunnels permit different passage by travel direction. Article does not identify F7 environmental blocks; keep directional environmental barriers distinct. |
| 537 | [Rainbow Route - Room 39](https://wikirby.com/wiki/Rainbow_Route_-_Room_39) | O | Explicit metal | Right-side metal passage protects Beginning Notes. Article calls for an imported ability or Mix; random/lucky Mix is not a guaranteed source witness. |
| 541 | [Mustard Mountain - Room 3](https://wikirby.com/wiki/Mustard_Mountain_-_Room_3) | E | Context; class not named | Two-way maze, Gordo-guarded pickups, Giant Rockies, and a shortcut. Article does not identify F7 environmental tiles or imply ordinary Stone can remove them. |
| 555 | [Rainbow Route - Room 10](https://wikirby.com/wiki/Rainbow_Route_-_Room_10) | E | Context; class not named | Downward cave leads to a Bomb Block-opened water current; a second bomb barrier protects a 1-Up. Reinforced positions need matching to those environmental changes. |
| 557 | [Rainbow Route - Goal 1](https://wikirby.com/wiki/Rainbow_Route_-_Goal_1) | O | Explicit metal | Master Hand supplies Smash before the metal-blocked Maxim Tomato chest. Goal door remains a separate target; shuffled sources must be evaluated from actual policy. |
| 601 | [Radish Ruins - Room 4](https://wikirby.com/wiki/Radish_Ruins_-_Room_4) | E | Context; class not named | Entry direction and Bomb Block barriers determine usable exits. F7 tiles must be evaluated with destructive room state rather than a generic ability check. |
| 605 | [Radish Ruins - Room 3](https://wikirby.com/wiki/Radish_Ruins_-_Room_3) | E | Context; class not named | Compartment maze restricts Room 8 and Chest 1 access from Room 2, with a peg alternative for the chest. Native F7 environmental tiles need mechanism-level reconciliation. |
| 606 | [Radish Ruins - Room 8](https://wikirby.com/wiki/Radish_Ruins_-_Room_8) | O/E | Explicit metal | Metal guards a Maxim Tomato and shortcut toward Room 3; article calls for an outside ability. Both native classes occur and must not be conflated. |
| 609 | [Radish Ruins - Room 18](https://wikirby.com/wiki/Radish_Ruins_-_Room_18) | O/E | Explicit metal | Lower metal branch protects ham; upper cannon route leads through Master Hand to Room 19. Local Flamers and later Smash are candidates only from reachable compartments. |
| 621 | [Radish Ruins - Room 2](https://wikirby.com/wiki/Radish_Ruins_-_Room_2) | E | Context; class not named | Descending ruined hall and crumbling bridge lead past a released Gordo. A Bomb Block releases water into the final chamber and the door to Room 3. Match the native F7 coordinates separately; Bomb-chain participation is not implied by F7 presence. |
| 707 | [Moonlight Mansion - Room 4](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_4) | O | Explicit metal | Upper-right door toward Room 13 is blocked by metal; other exits involve Bomb Block barriers. Preserve bomb order and distinguish lower-right access. |
| 708 | [Moonlight Mansion - Room 1](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_1) | O | Explicit metal | Two metal blocks separate left and right mansion compartments; required powers are not supplied locally according to the article. Several doors and bomb barriers make entry direction material. |
| 720 | [Carrot Castle - Room 14](https://wikirby.com/wiki/Carrot_Castle_-_Room_14) | E | Context; class not named | Castle-wall path includes a timed gate and Shotzo room; the apparent pit leads to Room 13. Article does not name F7 environmental tiles; match their mechanism before assigning requirements. |
| 736 | [Carrot Castle - Room 10](https://wikirby.com/wiki/Carrot_Castle_-_Room_10) | O/E | Explicit metal | Rightward cannon branch has a 1-Up below ordinary metal; article describes two-Sparky Mix yielding Missile. Other cannon branches serve Mini, Phan Phan, and the exit. Verify source policy and keep F7 environmental tiles separate. |
| 737 | [Carrot Castle - Room 11](https://wikirby.com/wiki/Carrot_Castle_-_Room_11) | E | Context; class not named | Enemy-free branching cannon sequence: upper path collects battery/tomato, lower path cherry/1-Up, both toward Room 12. Large F7 environmental count is environmental terrain, not evidence of 220 separate ability gates. |
| 741 | [Moonlight Mansion - Room 14](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_14) | O | Explicit metal | Metal barrier protects a tomato on the way toward Bonkers; alternate return from Room 15 has Flamers. Do not use later Hammer to justify an earlier inaccessible barrier. |
| 742 | [Moonlight Mansion - Room 15](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_15) | O | Explicit metal | Upper roof path is metal-blocked; lower path loops to Room 14 to obtain Burning. Returning opens access toward the sparerib chest and Warp door. |
| 743 | [Moonlight Mansion - Room 11](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_11) | E | Context; class not named | Correct entry is required to descend; Bomb Block activates a sparking machine and opens the path, then a lever opens Room 12. F7 tiles require environmental-state review. |
| 802 | [Olive Ocean - Room 20](https://wikirby.com/wiki/Olive_Ocean_-_Room_20) | O | Context; class not named | Underwater Bomb Block barrier changes walls to spikes; dry section has Sparky and cannons. The final cannon accesses optional goodies, then a current leads to Chest 2. Article does not explicitly identify the metal class. |
| 810 | [Olive Ocean - Room 19](https://wikirby.com/wiki/Olive_Ocean_-_Room_19) | E | Context; class not named | Underwater chamber and rightward current lead toward Room 20. Article does not identify the single F7 environmental tile; verify its mechanism and reachability underwater. |
| 814 | [Olive Ocean - Room 12](https://wikirby.com/wiki/Olive_Ocean_-_Room_12) | O | Explicit metal | Metal and a Flamer occur near Room 11; upper branching paths and a directional cannon reach other exits. Existing proven Normal routes must not acquire speculative metal gates. |
| 819 | [Olive Ocean - Room 21](https://wikirby.com/wiki/Olive_Ocean_-_Room_21) | O | Explicit metal | Underwater metal guards a 1-Up and other optional goodies. Rightward current leads through the tunnel to Room 22. Preserve the controller-proven Normal exit; retaining Hammer helps with goodies, not a mandatory exit requirement. |
| 821 | [Olive Ocean - Room 22](https://wikirby.com/wiki/Olive_Ocean_-_Room_22) | O | Explicit metal | Watery route with a dry Sword Knight chamber leads to Room 23. Metal guards an optional 1-Up; the article suggests retaining Hammer from Bonkers. Do not turn this pickup barrier into an exit gate. |

## Next step before logic changes

For each relevant target, use the recorded coordinate clusters to establish
entry compartment, accessible approach face, water state at activation/impact,
actual ability source, environmental alternatives, and return access. Add a
controller-only witness plus negative cases before changing a directed edge.
Optional pickups must remain distinct from required exits and AP checks.

[collision]: https://github.com/jiangzhengwenjz/katam/blob/master/src/object_collision.c
[block]: https://wikirby.com/wiki/Block
[heavy]: https://github.com/jiangzhengwenjz/katam/blob/master/src/large_star_stone_block.c
[heavy7d]: https://github.com/jiangzhengwenjz/katam/blob/master/src/large_stone_block_7D.c
