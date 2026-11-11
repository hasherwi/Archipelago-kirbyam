# Small-switch inventory for #1052

## Result and scope

Current implementation status is tracked in [ranged completion status](ranged-completion-status.md). This inventory retains its historical source/geometry observations; it is not current-generator or complete native-route proof. Main resolved 209's coarse token, 310/533 have conditional installed graphs, and 825 has one unconditional four-witness OR target. The JSON scan and historical native packets are unchanged.

The unmodified USA ROM contains **35 native small-switch instances in 24 populated room slots**. This is an exhaustive scan of all 983 native room slots and all 287 object lists, not a search for rooms already using an AP capability token. It includes both Dimension Mirror puzzle rooms, even though they have no AP room key. The scan covers 3,482 object templates, checks the 697 unused-slot sentinels, and checks the unreferenced object list 4 (no small switches). All 37 native Object Spawner templates were also checked; none spawns a small switch.

This is documentation and static evidence only. This static scan changes no gameplay logic and uses no emulator. Separate runtime witnesses are documented elsewhere. The ROM was read only; no ROM, extracted graphics or complete collision map is in the deliverable.

**#1052 should include distinct remote/timing/cooperation switch routes as well as wall-separated targets. It must not equate all small switches with an ability requirement, nor equate a projectile's wall behavior with a complete route.**

The clearest wall-independent ranged alternative is native **147 / Moonlight Mansion Room 19**: WiKirby explicitly describes striking the switch from near the gate instead of racing; the sampled initial static row between switch and gate is all 0x00. This still does not prove every candidate move, source, range or firing stance.

Native **310 / Mustard Mountain Chest** and **533 / Mustard Mountain Room 15** are strong remote/cooperative or delayed-attack candidates, but their switch-height horizontal rows contain intervening 0x0D geometry. Therefore the wiki's remote wording does **not** prove a flat non-wall-piercing shot. Native **825 / Olive Ocean Goal 2** is clearly a separated switch inside the locked treasure chamber. Native **209 / Peppermint Palace Chest** had a legacy token in the inventory snapshot; main now supplies directed entry/Normal/Snow-loop logic. The sampled raised 0x50 floor remains a geometry observation, not evidence for a new ranged requirement.

At this inventory snapshot, calling other Kirbys, Ice, Laser, UFO and Cupid were **candidate alternatives requiring individual witnesses**. Later bounded witnesses are listed in the completion status and ledger. No blanket capability grant is made here. Never rely on helper Copy Abilities, Bomb activation, combat, acquisition or carry. Only small switches and Heave-Ho blocks may use helper assistance, with positioning/behavior evidence; no Phone capability is implemented.

## Enumeration correction

The earlier 23-instance / 19-room result read only a prefix of each object stream. It is superseded by this 35-instance / 24-room scan. Newly included rooms are native 177, 426, 511, 708 and 804; native 608 expands from one switch to five. Native 527 and 608 do have object-driven vertical gates. Original artifacts are preserved for audit. No new traversal capability is granted by this correction.

## Game-code identity and behavior

The pinned decomp is [jiangzhengwenjz/katam at 7d969fb](https://github.com/jiangzhengwenjz/katam/tree/7d969fbce14fdc838d2c1ea01389717fb96c3189). The private vanilla USA ROM passed size 16 MiB and SHA-1 `274b102b6d940f46861a92b4e65f89a51815c12c` checks.

- [Object type definition](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/include/constants/object_types.h#L113): `OBJ_SMALL_BUTTON = 0x6D`.
- [Object creation dispatch](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/code_080023A4.c#L6112-L6127): spawn table 1 selects `gSpawnFuncTable1[type]`. All 35 instances use table 1, type 0x6D. The ROM function pointer at table index 0x6D is independently verified as `0x081191C5` (Thumb), for `CreateSmallSwitch` at `0x081191C4`.
- [Small-switch constructor and shared switch logic](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/asm/big_small_switch.s): small constructor writes its small/big discriminator at object +0xB8 to 0; Big Switch writes 1. The small switch sets bounds `(-7,-10,+7,-2)`, then aligns its Y to a 16-pixel boundary. These are ordinary touch/interaction switches, not a separate attack-only switch species.
- `sub_081194DC` at `0x081194DC` checks eligible object overlaps (types 0x79 and 0x7D), interaction flags, and in the applicable branch Kirby bounds. Its interaction-flag branch returns true for a small switch without the Big Switch human-player check. It does not contain an Ice/Laser/UFO/Cupid ability whitelist. Compatibility still depends on the producing attack, collision state and actual overlap.
- `sub_081197D4` at `0x081197D4` drives press/release state and initializes an internal release counter from `ObjectTemplate.unk18 + 2`; the counter is decremented on later update calls without activation. A nonzero timer is not an ability requirement. **The exported parameter is not the gate's exact open duration.** The door has its own opening/closing animation and bounds changes.
- `sub_08119980` dispatches by template flags at +0x22: mask 0x0001 selects the multi-byte state handler, mask 0x0002 a callback handler, mask 0x8000 an additional state-slot handler, otherwise the ordinary handler. `sub_08119A20` increments/decrements room state indexed by template byte +0x04 on press/release transitions. Native 815's two switches use 0x8000 and additionally update room state slot 15 from template byte +0x11; retain this stage behavior rather than flattening them.
- [Vertical gate code](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/vert_sliding_door.c#L27-L96): type 0x71 gates read the room state slot identified by their template byte +0x04. This supports the per-switch gate links exported in JSON. Gate collision bounds are `(-8,-32,+8,0)` when closed and change during animation.
- [Object Spawner](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/asm/object_spawner.s#L365-L422) constructs table-1 templates with the low byte of template +0x14 as their type. All 37 native spawners were checked; none targets 0x6D. Other arbitrary runtime-created templates were not exhaustively proven absent.

## Reproducible enumeration and scalar collision evidence

`extract_small_switches.py` checks every slot and object list, validates the ROM and mapping joins, verifies the constructor pointer, and exports instance indices, positions, mode fields, state-slot links and limited collision-row samples. Its scan distinguishes all 24 native IDs from AP room keys and WiKirby titles.

The layout comes from [RoomProps and ObjectTemplate](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/include/data.h) and [level loading](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/level.c#L165-L223): `gRoomProps` is at ROM offset 0x9331AC, stride 0x28; **objectListIdx is +0x20**, not +0x22. `gLevelObjLists` is at 0xD637AC, 287 pointers. Each list header has its object stream pointer at +0. Native CreateLevelObjects advances by each template byte +1 until a zero size; all decoded nonterminal records have size 0x24. Header +0x0C counts distinct spawn-table-1 types in the separate +4 array, not template instances. This relationship was checked for all 287 lists (and table 2 through header +8/+0x0D). Templates have size 0x24, spawn table at +0, signed X/Y at +6/+8 and type at +0x0C.

An older local `enrich_native_object_room_usage.py` incorrectly names the +0x22 field as the object-list index. It was not used for this inventory. The independently validated native-room map and `extract_room_evidence.py` use the correct +0x20 field. No helper was changed.

Collision probes reproduce the RLE decompression used by `src/level.c` and validate expanded length against foreground dimensions. `GetCollisionTile` indexes 16-pixel tiles using roomWidth/16. The artifact stores only short scalar horizontal samples at switch Y minus 6, plus dimensions and offsets. All-0x00 is evidence for clear **initial static** tiles on that row, not proof of attack trajectory, projectile lifetime, dynamic gate clearance, object interference or Kirby's approach. Nonzero tiles are not all equivalent: their attributes and directional collision behavior must be respected.

The local AP reference was `prepare-1016` at `e45ceabd753c8056ba9f2f8780bcd0e7a93fb720`, not a claim about the latest main head. It places `can_hit_far_switch` at native 209's map chest, native 310's map chest, and the native 533-to-Room-16 exit. In that snapshot the token is in `_PENDING_ROOM_ABILITY_REQUIREMENTS`; evaluation returns the permissive placeholder result. There is **no implemented ability list to inherit as evidence**.


## Exhaustive room list

Coordinates are native pixels. T is the template release-counter parameter, not a measured gate-open duration. Instance indices are zero-based in the complete object-template stream.

| Native room | WiKirby room | Switch instances (index: X,Y; T) | Classification |
| --- | --- | --- | --- |
| 147 / 0x093 | [Moonlight Mansion - Room 19](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_19) | 7: 520,112; T=35 | ordinary timing with clear remote alternative |
| 177 / 0x0B1 | [Rainbow Route - Goal 3](https://wikirby.com/wiki/Rainbow_Route_-_Goal_3) | 9: 120,288; T=60 | ordinary Normal large-star route reviewed; Fighter remains a suggestion |
| 209 / 0x0D1 | [Peppermint Palace - Chest](https://wikirby.com/wiki/Peppermint_Palace_-_Chest) | 3: 288,624; T=100 | directed Normal/Snow map loop integrated; exact entries remain qualified |
| 228 / 0x0E4 | [Peppermint Palace - Room 9](https://wikirby.com/wiki/Peppermint_Palace_-_Room_9) | 7: 160,208; T=60 | ordinary alternate exit gate |
| 310 / 0x136 | [Mustard Mountain - Chest](https://wikirby.com/wiki/Mustard_Mountain_-_Chest) | 2: 312,144; T=0 | remote or cooperative timing |
| 404 / 0x194 | [Candy Constellation - Room 1](https://wikirby.com/wiki/Candy_Constellation_-_Room_1) | 3: 440,64; T=0 | falling switch timing |
| 426 / 0x1AA | [Candy Constellation - Chest 3](https://wikirby.com/wiki/Candy_Constellation_-_Chest_3) | 5: 312,128; T=0<br>6: 312,64; T=0<br>7: 184,64; T=0 | reviewed ordinary Normal staged map route |
| 427 / 0x1AB | [Candy Constellation - Room 2](https://wikirby.com/wiki/Candy_Constellation_-_Room_2) | 4: 56,240; T=300<br>5: 424,144; T=120 | two ordinary timing gates |
| 511 / 0x1FF | [Cabbage Cavern - Room 5](https://wikirby.com/wiki/Cabbage_Cavern_-_Room_5) | 10: 56,112; T=135 | ordinary timing or cooperative chest route |
| 527 / 0x20F | [Cabbage Cavern - Room 14](https://wikirby.com/wiki/Cabbage_Cavern_-_Room_14) | 2: 856,192; T=100 | ordinary timing puzzle |
| 533 / 0x215 | [Mustard Mountain - Room 15](https://wikirby.com/wiki/Mustard_Mountain_-_Room_15) | 2: 312,144; T=0 | remote or delayed timing |
| 608 / 0x260 | [Radish Ruins - Room 11](https://wikirby.com/wiki/Radish_Ruins_-_Room_11) | 4: 328,96; T=200<br>5: 464,112; T=255<br>6: 752,208; T=70<br>7: 1064,272; T=70<br>14: 936,48; T=30 | ordinary puzzle geometry pending |
| 610 / 0x262 | [Radish Ruins - Chest 1](https://wikirby.com/wiki/Radish_Ruins_-_Chest_1) | 4: 432,128; T=120 | ordinary one way exit |
| 707 / 0x2C3 | [Moonlight Mansion - Room 4](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_4) | 6: 560,304; T=0 | clear static corridor timing pending |
| 708 / 0x2C4 | [Moonlight Mansion - Room 1](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_1) | 12: 80,384; T=100 | ordinary timing and barrier route |
| 712 / 0x2C8 | [Moonlight Mansion - Room 13](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_13) | 5: 344,464; T=100 | ordinary timing gate |
| 720 / 0x2D0 | [Carrot Castle - Room 14](https://wikirby.com/wiki/Carrot_Castle_-_Room_14) | 1: 600,96; T=30 | ordinary timing gate |
| 742 / 0x2E6 | [Moonlight Mansion - Room 15](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_15) | 5: 280,464; T=120 | ordinary timing and hazard gate |
| 804 / 0x324 | [Labyrinth Entrance Stage](https://wikirby.com/wiki/Labyrinth_Entrance_Stage) | 7: 136,80; T=0<br>8: 296,128; T=0 | tutorial cooperative switch route |
| 815 / 0x32F | [Olive Ocean - Chest 1](https://wikirby.com/wiki/Olive_Ocean_-_Chest_1) | 6: 312,80; T=0<br>7: 168,144; T=0 | reviewed moved block and Normal puff |
| 825 / 0x339 | [Olive Ocean - Goal 2](https://wikirby.com/wiki/Olive_Ocean_-_Goal_2) | 5: 656,144; T=255 | wall separated target |
| 831 / 0x33F | [Olive Ocean - Room 14](https://wikirby.com/wiki/Olive_Ocean_-_Room_14) | 4: 472,224; T=240 | optional timing or explosive route |
| 911 / 0x38F | [Dimension Mirror (level)](https://wikirby.com/wiki/Dimension_Mirror_(level)) | 1: 56,256; T=60<br>2: 136,304; T=90<br>5: 72,304; T=80 | sequential timing puzzle |
| 915 / 0x393 | [Dimension Mirror (level)](https://wikirby.com/wiki/Dimension_Mirror_(level)) | 7: 120,304; T=180 | timing geometry pending |

## Per-room assessment

### 147: Moonlight Mansion - Room 19

Retained WiKirby assessment: Gate can be reached by a quick, careful run, or the switch can be struck from near the gate with a ranged attack. [Source](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_19).

Strong wall-independent ranged-alternative example: the initial static collision row at switch height is all 0x00 between switch and gate. A Gordo is a separate hazard. Ranged ability is not established as mandatory.

Still needed: Specific attacks, range, approach position, Gordo interference and helper behavior remain untested.

### 177: Rainbow Route - Goal 3

WiKirby: Absorbing Box Boxer for Fighter lets Kirby open the switch gate to the 1-Up. The specific move is not stated. [Source](https://wikirby.com/wiki/Rainbow_Route_-_Goal_3). Reviewed 2026-11-08.

One switch, counter 60, with a clear initial static row to its gate. The article proposes Fighter, but does not establish a specific Fighter move, exclusive ability need or arbitrary projectile compatibility.

Reviewed ordinary alternative: `rainbow-normal177-source-witness.md` and its
acceptance JSON establish exact 178 right arrival → 177, Normal Box Boxer combat,
same-pass original-Flamer pair capture, damage 25 object-door bypass, slot 2 and
physical chest 0x088BB0BC with local client 3960568. Four ungated actual HP 1/6 ×
enemy 100/500 positives and matched final-shot omissions preserve the existing
`MINOR_CHEST_RAINBOW_ROUTE_1_GOAL_3` null rule. This is not terrain piercing or
Copy Ability ownership. Upstream 138/new-game access, all RNG/options,
central-circle return, RoomSanity and helper routes remain unproved.
The Fighter suggestion and failed upper/ordinary-star routes do not establish
an exclusive ability gate.

A separate independently reviewed gated/no-items representative at actual 1 HP
and 500% enemy health also reaches this chest with Normal equipment and zero
unlock mask. Its own final-shot omission stays sealed. This is one additional
case, not all random policies or a full gated health matrix.

### 209: Peppermint Palace - Chest

Retained WiKirby assessment: Intertwining chambers require different entrances for the map and smaller chests. The article does not describe this small switch. [Source](https://wikirby.com/wiki/Peppermint_Palace_-_Chest).

The historical AP map-chest rule said can_hit_far_switch. Native gate is (224,608), switch (288,624), counter parameter 100. The horizontal sample crosses raised-floor code 0x50, so that token never proved an unobstructed shot.

Current integration: Normal208→BOTTOM_MINOR and Normal210→UPPER_ENTRY are separate targets. The reviewed210/Snow loop reaches LOWER_MAP, which owns the map. The coarse token is gone. `ordinary-209-snow-map-loop-acceptance.json` retains its qualified upper210 arrival and100%/500% variants, not arbitrary209 joins or a universal projectile route.

### 228: Peppermint Palace - Room 9

Retained WiKirby assessment: Three exits lead to Room 10: the left is switch-gated, the middle is unguarded, and the right has Mirra. [Source](https://wikirby.com/wiki/Peppermint_Palace_-_Room_9).

Include the switch in the inventory, but do not make ranged activation a blanket Room 10 requirement. The existing alternate exits matter.

Still needed: The switch-specific trajectory and timing have not been tested.

### 310: Mustard Mountain - Chest

Retained WiKirby assessment: The map-chest gate closes almost immediately after switch activation; the article proposes remote activation or another Kirby. [Source](https://wikirby.com/wiki/Mustard_Mountain_-_Chest).

Confirmed remote/cooperation candidate. Switch (312,144), gate (440,144), counter parameter 0. Static 0x0D tiles intervene at switch height, so a generic horizontal non-wall-piercing attack is not proven by the wiki description.

Current bounded implementation: guaranteed Twister→UFO/Crash/Cupid/Cutter each has its own graph and qualified native witness. Native Tornado and other source-policy/ordinary alternatives remain open. Unproved Ice, Laser or helper routes cannot inherit those witnesses. See the completion status and `mustard-map-*-source-witness.md` records.

### 404: Candy Constellation - Room 1

Retained WiKirby assessment: Bomb Blocks beneath the switch must be broken to reveal the Chest 2 door, but doing so drops the switch into a pit. The gate must be crossed before it closes. [Source](https://wikirby.com/wiki/Candy_Constellation_-_Room_1).

A timing plus destructible-support puzzle, not simply a permanent remote target. The initial switch-height corridor to the gate is all 0x00, but the switch and objective move/change after the Bomb Blocks break.

Still needed: Activation order, falling trajectory and whether a candidate attack also breaks the support must be verified.

### 426: Candy Constellation - Chest 3

WiKirby: Swift movement and breath attacks, or friends, solve the map switch puzzle. A lower bypass exists; the room has no enemies. [Source](https://wikirby.com/wiki/Candy_Constellation_-_Chest_3). Reviewed 2026-11-08.

Three zero-counter switches link to three gates; all three sampled static horizontal rows are clear.
Switches 5/6 use mode bit 0x4 and latch while loaded; the first switch is momentary.

Reviewed ordinary alternative: `candy-normal426-source-witness.md` and its acceptance JSON
establish a qualified near-door 419 fixture → actual 426 transition → staged Normal route →
map 3960208, with physical chest 0x088C87FC and exact local production-client output.
Three witnesses cover 1 HP at 100/500% and 6 HP at 100%, with no damage or helper in 426.
Retained repeated-contact/puff timing, a late first-gate jump, lower-switch access via the
narrow shaft, inflation return and an ordinary F1 slide precede map collection. A matched
6 HP first-jump omission never crosses the gate or collects the map. Preserve the null map
rule and ordinary alternatives; do not impose a Copy Ability requirement.

Still unproved: arbitrary 419 access, room-reset latch persistence, RoomSanity, 426 → 420,
helper routes and a copied-ability matrix. Lower-bypass exploration did not collect the map
or enter 420, so it earns neither check nor outgoing-door credit.

### 427: Candy Constellation - Room 2

Retained WiKirby assessment: One switch can be lowered by removing crumbling blocks to help reach the Red Spray Paint chest. Another requires a run across the room to the gate leading to Room 3. [Source](https://wikirby.com/wiki/Candy_Constellation_-_Room_2).

Two distinct switches and objectives: index 5 / slot 1 / counter 120 controls gate 6 near the chest; index 4 / slot 2 / counter 300 controls gate 7 on the Room 3 route. Keep them separate.

Still needed: Ranged alternatives may help, but changing support geometry and intervening platforms prevent one generic distance-only witness.

### 511: Cabbage Cavern - Room 5

WiKirby: Jump on the switch and rush to Secret Sounds, or use friends. [Source](https://wikirby.com/wiki/Cabbage_Cavern_-_Room_5). Reviewed 2026-11-08.

One switch at (56,112), counter 135. Its horizontal gate probe crosses 0x0D and F2 tiles, so the described ordinary/cooperative route is not proof of a flat projectile path.

Still needed: Exact attack trajectories, helper positioning, timing and full route acceptance remain untested. No blanket ability grant follows from this description.

### 527: Cabbage Cavern - Room 14

Retained WiKirby assessment: The chest route involves pressing the switch, passing a gate quickly, defeating Sword Knight, breaking a Bomb Block and dashing to the Sapphire paint chest. [Source](https://wikirby.com/wiki/Cabbage_Cavern_-_Room_14).

Timed route with follow-on obstacles. The corrected complete stream includes vertical gate index 14 linked to switch index 2 by state slot 1. The direct static probe contains 0x0D geometry; the earlier claim that no object gate existed was a parser-truncation error.

Still needed: Verify the whole timed route, approach and attack trajectory before allowing specific ranged alternatives.

### 533: Mustard Mountain - Room 15

Retained WiKirby assessment: The Room 16 gate resets quickly, and the nearby Foley can be used to solve the timing problem. [Source](https://wikirby.com/wiki/Mustard_Mountain_-_Room_15).

Confirmed delayed/remote candidate. Switch (312,144), gate (152,128), counter parameter 0. Static 0x0D tiles lie between them at switch height. Foley is an environmental route to investigate, not evidence that every projectile works.

Current bounded implementation: guaranteed Foley→Bomb/UFO/Crash/Magic has four distinct OR graphs. Acquiring copied Bomb is separate from the environmental Foley drop/explosion, whose crossing still needs acceptance. Other source-policy and helper alternatives remain open; see the completion status and `mustard-room15-*-source-witness.md` records.

### 608: Radish Ruins - Room 11

Retained WiKirby assessment: Interconnected corridors contain switch gates and Bomb Block barriers; a small switch puzzle guards the 1-Up chest. [Source](https://wikirby.com/wiki/Radish_Ruins_-_Room_11).

Five switches are present, not one: indices 4, 5, 6, 7 and 14 use state slots 5, 4, 2, 1 and 3, and counter parameters 200, 255, 70, 70 and 30. Each has a corresponding type 0x71 gate. The earlier no-object-gate claim was a parser-truncation error. Some direct static rows are clear and others cross geometry; preserve the five independent objectives.

Still needed: The article does not establish mandatory ranged or cooperative solutions. Classify each recovered switch/gate pair separately and verify approach, timing and target before assigning capabilities.

### 610: Radish Ruins - Chest 1

Retained WiKirby assessment: After collecting Vitality, Kirby passes a one-way switch gate and Noddy to reach Room 5. [Source](https://wikirby.com/wiki/Radish_Ruins_-_Chest_1).

Ordinary exit gate; no remotely activated ability requirement is established. Static switch-to-gate row is all 0x00 and counter parameter is 120.

Still needed: No gameplay acceptance test performed; do not turn simple switch presence into an ability lock.

### 707: Moonlight Mansion - Room 4

Retained WiKirby assessment: The article describes hallways, Bomb Block barriers and the lower-right routes but omits the small switch. [Source](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_4).

Switch (560,304), gate (616,304), counter parameter 0. The direct static collision row is all 0x00. Existing AP compartments distinguish the switch-wall side, but that name is not proof of a projectile collision requirement.

Still needed: Establish entry side, ordinary contact timing and dynamic gate traversal. Do not classify as a through-wall attack solely from the AP region name.

### 708: Moonlight Mansion - Room 1

WiKirby: Switch-toggled doors and metal/Bomb Block barriers feature in the room; the third lower-right door requires quick passage. [Source](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_1). Reviewed 2026-11-08.

One switch at (80,384), counter 100, with a clear initial static row to its gate. The article does not establish a remote-only requirement; barriers and the full approach still matter.

Still needed: Exact attack trajectories, helper positioning, timing and full route acceptance remain untested. No blanket ability grant follows from this description.

### 712: Moonlight Mansion - Room 13

Retained WiKirby assessment: A Flamer guards a switch gate that requires quick passage before the rest of the room and optional Boxy fight. [Source](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_13).

Counter parameter 100. The static sample at switch height is all 0x00, though gate and switch elevations differ. Wiki establishes speed, not a mandatory ranged attack.

Still needed: Candidate attacks and approach positions remain untested.

### 720: Carrot Castle - Room 14

Retained WiKirby assessment: A switch gate precedes the Shotzo, low-ceiling and spike section. The pit leads to Room 13, and the far route reaches Room 15. [Source](https://wikirby.com/wiki/Carrot_Castle_-_Room_14).

Short counter parameter 30 with switch (600,96) and gate (520,128). Elevation is part of the geometry; the article does not establish a remote-only condition.

Still needed: Verify the short timing window and any optional remote solution without treating range alone as sufficient.

### 742: Moonlight Mansion - Room 15

Retained WiKirby assessment: A timed switch gate and spike pit precede a dangerous landing near another pit and Waddle Doo. [Source](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_15).

Counter parameter 120. Hazard and solid tiles appear on the sampled row. This is not evidence for a simple flat free-air projectile route.

Still needed: Ordinary race versus specific ranged alternatives needs a route-level witness.

### 804: Labyrinth Entrance Stage

WiKirby: In the second tutorial room, the first switch opens by walking. The next timed switch calls for cell-phone friends to hold it while a Kirby reaches the Bomb Block. [Source](https://wikirby.com/wiki/Labyrinth_Entrance_Stage). Reviewed 2026-11-08.

Two zero-counter switches control separate gates. This is a source-backed cooperation tutorial, not evidence for a mandatory acquired Copy Ability. The second static switch-to-gate row crosses 0x0D geometry; helper positioning and the Bomb Block stage must be retained.

Still needed: Exact attack trajectories, helper positioning, timing and full route acceptance remain untested. No blanket ability grant follows from this description.

### 815: Olive Ocean - Chest 1

Retained WiKirby assessment: The upper puzzle leading to Vitality can be solved with inhale/spit and quick movement; the underwater lower route skips it. [Source](https://wikirby.com/wiki/Olive_Ocean_-_Chest_1).

Two zero-counter switches, each using mode 0x8000, cross-control vertically separated gates: index 6 at (312,80) sets slot 2 for lower gate 5, and index 7 at (168,144) sets slot 1 for upper gate 3. Do not collapse into one remote attack check.

Reviewed native witness: Normal inhale moves silver block `0x088CCCFC` into maintained lower-switch contact, without swallowing or spitting it. Inclusive integer contact at x175 holds the upper gate open. A final intrinsic air puff triggers the upper switch; its release and gate animation leave time to cross below, slide and collect Vitality. Four actual 1/6 HP × 100/500% runs and a matched final-puff omission control retain the ordinary `can_break_block` rule. The qualified late 551 approach is not arbitrary upstream access. See `olive-normal815-source-witness.md` and its compact manifest.

### 825: Olive Ocean - Goal 2

Retained WiKirby assessment: The Sound Effects chest and its switch are both inside a gate-locked chamber after Mr. Frosty. [Source](https://wikirby.com/wiki/Olive_Ocean_-_Goal_2).

Confirmed separated-target candidate for the wall-aware part of #1052. The initial horizontal sample to switch (656,144) crosses 0x0D tiles. Keep distinct from free-air ranged timing alternatives.

The article alone does not prove an Ice move or projectile path. Current integration has one unconditional target with finite Frosty Ice/UFO and permanent Central/Peppermint290 statue Ice alternatives. Keep their distinct source/carry/native boundaries, including layered permanent Ice evidence, rather than treating them as uninterrupted current-generator chest replays. See `main-ranged-integration.md`.

### 831: Olive Ocean - Room 14

Retained WiKirby assessment: An optional 1-Up sits behind a timed gate; quick movement or an explosive approach can solve it. The room contains dry/wet passages and currents. [Source](https://wikirby.com/wiki/Olive_Ocean_-_Room_14).

Counter parameter 240. The article's image caption also describes Kirby using his blowhole to activate the switch. This supports an ordinary interaction candidate, not a mandatory acquired Copy Ability.

Still needed: Confirm water/air state and exact attack trajectory before adopting non-water-capable ability alternatives.

### 911: Dimension Mirror (level)

Retained WiKirby assessment: The third Dimension Mirror area resembles Radish Ruins and contains a switch puzzle. [Source](https://wikirby.com/wiki/Dimension_Mirror_(level)).

Three switches, state slots 1/2/3 and counter parameters 60/90/80, controlling three separate vertical gates. Native room is retained despite having no AP room key. Two switches sit in the lower recess, so approach and sequence matter.

Still needed: The shared article does not document the full sequence or mandatory remote alternatives. Master availability and side paths must be considered separately.

### 915: Dimension Mirror (level)

Retained WiKirby assessment: The seventh Dimension Mirror area resembles Peppermint Palace and contains several obstacles. [Source](https://wikirby.com/wiki/Dimension_Mirror_(level)).

One switch (120,304), gate (216,304), counter parameter 180. The static horizontal row includes raised-floor code 0x50. Native room is retained despite having no AP room key.

Still needed: Shared article is too general to prove a remote-only solution; establish the obstacle route and attack trajectory.

## Validation and remaining limits

- Passed: ROM size and SHA-1, constructor pointer, all 983 native slots, 286 populated identities, 697 unused sentinels, all 287 complete object streams / 3,482 templates, all per-table type-list set checks, the unreferenced list, all 37 Object Spawners, 24 room identities, 35 switch instances, all decoded RLE lengths, and assessment-to-room joins.
- 23 unique WiKirby article texts cover all 24 native room rows: 18 retained original reads plus five new standard-tool reads on 2026-11-08. Dimension Mirror rooms 911 and 915 share one article. None of the five new reads was a denied page.
- The prior direct Peppermint Chest gallery request returned HTTP 403 and was not retried or bypassed. The previously successful text read remains the source.
- Not performed: emulator tests, per-move attack acceptance, complete dynamic collision simulation, source-reachability proofs, helper positioning, or exhaustive exclusion of all arbitrary runtime-created templates. No capability grants are made.
- No rebuild required: only standalone evidence files changed. Python parsing, JSON, negative controls and deterministic extraction were checked; the evidence manifest records the corrected scan counts and limits.

## Evidence manifest

[Small-switch evidence manifest](small-switch-inventory.json) contains all 35 switches, linked gates, bounded collision probes and assessments. Unrelated objects, ROM bytes and graphics are omitted. The reproducible extractor and full validation record are retained privately.

## Follow-up geometry and existing Ice implementation

[Exact geometry supplement](remote-small-switch-geometry.md) refines initial switch contact bounds and confirms solid 0x0D obstructions in native 310/533, versus the clear initial lane in 147. Counter parameters 0/35 initialize 2/37, not measured gate-open durations. The earlier conditional guaranteed-Frosty Ice traversal and two upper-arena cold replays remain historical evidence. Current main integration instead has one unconditional four-witness target: finite Frosty Ice/UFO plus independent permanent Ice sources. Those records retain their own source, carry and native-proof limits; this is not blanket source-independent Ice equipment.
