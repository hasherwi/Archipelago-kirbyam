# Remote switch geometry: native 147, 310, 533

Evidence-only supplement, 2026-11-08. No gameplay code, rules or ROMs modified. Source: jiangzhengwenjz/katam commit 7d969fbce14fdc838d2c1ea01389717fb96c3189. USA ROM SHA-1 274b102b6d940f46861a92b4e65f89a51815c12c. Starting inventory is the corrected complete object-stream inventory (35 switches in 24 native rooms). This document contains only bounded scalar geometry and source analysis, no ROM bytes or graphics.

## Interpretation and source anchors

- Coordinates below are object-template positions, NOT final moving object positions. Switch constructor in asm/big_small_switch.s:47–101 uses local bounds (-7,-10,+7,-2), then snaps its Y using the lower bound. For these aligned template Y values the initial fixed-point origin is template Y+2−1/256, integer Y+1. Thus initial integer contact rectangles are x±7, template Y−9..Y−1. Later physics or sprite/state changes must be checked at runtime.
- Collision attributes in src/code_080023A4.c:71–104 map tile 0x00 to 0x00000001, 0x0D to 0x00000200, 0x0F to 0x00000004, and 0xF2 to 0x00000240. The 0x0D dispatcher selects sub_08009E0C (line5839), which calls generic solid handler sub_080042BC (line2519 onward). 0x0D is not a directional/passable platform. 0x0F has a different platform handler; do not treat every nonzero collision byte as a wall.
- src/vert_sliding_door.c:11–24 sets closed bounds (-8,-32,+8,0). Its open/close functions change the bottom in 4px steps, with a counter threshold greater than6 and animation-complete transitions. An activated switch counter is not identical to the time available for traversing the door.
- asm/big_small_switch.s:803–1014 reloads counter from template +0x18 PLUS TWO, and decrements it on subsequent non-contact updates. Parameters 35/0 therefore initialize counters37/2. A zero parameter is not literal instantaneous closure. Held/repeated interaction, release state, room-slot publication and door animation still matter.
- Generic attack eligibility is separate from geometry. Constructor mask0x00308020 and contact category/strength dispatch permit several attacks but do not prove an entire route. See the separately reviewed [collision-avoiding-attack-ranges.md](collision-avoiding-attack-ranges.md), especially its small-switch target section, and asm/big_small_switch.s:564–610. No ability grants follow from this supplement.

## 147: Moonlight Mansion Room19

Switch index7 at(520,112), state slot1, parameter35, mode0x0008. Gate index8 at(632,112), same slot. Closed gate bounds x624..640,y80..112. Initial switch contact x513..527,y103..111.

The entire switch-to-gate corridor x520..632 at tile rows5 and6 (y80..111) is 0x00. This includes the initial switch contact height. There is no static intervening wall on this lane. Floor rows7/8 have a pit between x544..607; a direct walking-distance estimate ignores it. Gordo object index6 at(576,104) is a separate dynamic hazard on the firing lane.

Retained WiKirby text describes a quick careful run OR a ranged strike from near the gate. That supports remote activation as an alternative, not a mandatory Copy Ability. Horizontal projectiles are statically plausible here, but exact firing position/height, enemy interception, spawn timing, cancellation, gate-crossing timing and ability access remain unwitnessed. A broad range envelope is not a specific move witness. Beam/Spark have different short ranges; Laser/UFO/Cupid and Ice are not interchangeable solely because the lane is clear.

## 310: Mustard Mountain Chest

Switch index2 at(312,144), state slot1, parameter0, mode0. Gate index3 at(440,144), same slot. Closed gate bounds x432..448,y112..144. Initial switch contact x305..319,y135..143.

The direct horizontal lane at switch contact height crosses a SOLID block x320..367,y112..143 (tile columns20..22, rows7..8, all0x0D). Above it the solid overhang widens to x320..399,y80..111 (columns20..24, rows5..6). Row4, y64..79, is clear over this structure, but a horizontal shot there is too high for the switch. An arcing or angled route must descend on its left side into x305..319,y135..143; it is not established by the mere existence of overhead air. Underneath, row9 y144..159 is solid floor, so there is no lower free-air lane at the switch.

Thus a generic flat non-piercing shot from the gate side is not supported. Remote/cooperative WiKirby wording does not distinguish a piercing shot, angled approach, delayed effect or helper contact. Top-charge UFO shot has a terrain-bypassing source path distinct from medium UFO shot/short whip; kicked Ice differs from Ice breath and requires a suitable frozen enemy. These remain candidate classes, not completed route witnesses. Gate timing and standing/firing position are still required even if a shot reaches the switch.

## 533: Mustard Mountain Room15

Switch index2 at(312,144), state slot1, parameter0, mode0. Gate index1 at(152,128), same slot. Closed gate bounds x144..160,y96..128. Initial switch contact x305..319,y135..143.

Direct gate-to-switch height crosses SOLID columns15..17 x240..287 for y80..159 (rows5..9). In addition, gate column9 is solid at y128..143: the gate itself is one tile higher than the switch, so a flat switch-height probe starts below the gate opening. There is overhead air across the middle structure at y64..79; a path reaching the switch must then descend into the right-side recess x288..319, above its solid row9 floor. This is an elevation/trajectory problem as well as a solid-wall problem.

A separate platform pair0x0F exists at x352..383,y64..79 and y112..127, to the right of the switch and behind solid columns20..21 x320..351. Those platform tiles are NOT the obstruction between the gate and switch; the intervening x240..287 structure is0x0D.

Foley index3/type0x22 is at(224,64). This confirms a nearby environmental object consistent with the retained WiKirby delayed-Foley description, but not its attack trajectory, drop timing, travel to the switch, or the player's successful passage. Do not substitute “any projectile” for the Foley alternative, or assume top-charge UFO/Ice/Laser/Cupid all solve the route.

## Remaining tests, exactly scoped

No emulator acceptance tests were performed. For each proposed alternative, establish entry-side reachability, available ability/enemy source, legal firing/throwing pose, switch contact event, slot activation, dynamic door clearance, destination traversal, and ability cancellation. Record the specific move, not only ability name. For 533, also witness Foley's delayed interaction and crossing. For 310/533, a failure of one flat shot is not proof that all angled/delayed moves of that ability fail. No universal negative or blanket logic change is justified.

The retained WiKirby references are https://wikirby.com/wiki/Moonlight_Mansion_-_Room_19 , https://wikirby.com/wiki/Mustard_Mountain_-_Chest , and https://wikirby.com/wiki/Mustard_Mountain_-_Room_15 . No new requests or retries of denied WiKirby content were made.
