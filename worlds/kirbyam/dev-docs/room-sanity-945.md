# Room-sanity reachability: issue #945

All five checks in #945 belong to real, player-accessible native rooms. None is
an unused room or an alias that should be removed. The repair preserves their
location IDs and native visit bits.

| AP room | Native room / visit bit | Native evidence | AP defect |
| --- | --- | --- | --- |
| Moonlight 2-06 | 744 / 83 | Room 702 (2-05), tile (43,17), enters at (2,3) | No edge enters the modeled 2-05 lower compartment |
| Carrot 5-13 | 734 / 261 | Rooms 719 (5-07) and 720 (5-14) enter separate portions | Entrances reach logical compartments, while the visit check remains on an unreachable canonical parent |
| Olive 6-05 | 133 / 193 | Room 132 (6-04) has entrances to (2,6) and (3,18) | Same check-ownership defect |
| Radish 8-09 | 604 / 222 | Room 603 (8-06) enters at (4,6); 606 (8-08) at (78,9) | Same check-ownership defect |
| Candy 9-CHEST_2 | 403 / 145 | Room 404 (9-01) enters at (7,9); 405 (9-09) at (55,4) | Same check-ownership defect |

## Moonlight's directed approach

Native room 706 (2-03), tile (25,18), enters room 702 (2-05) at (4,12).
Room 702 has clear collision cells at x=5..6, y=10..17, beside this spawn,
providing a drop into the lower-left compartment. The adjacent ladder is not
needed for that descent. The stone-block object (type 0x79) at (200,280) lies
farther along the lower corridor, outside the chute.

Add only the missing 2-05 -> 2-05_LOWER descent. Preserve the existing lower
corridor requirement and reverse climb/fly requirement. Moving the heavy stone
uses basic Super Inhaling; Burning is an alternative, not a mandatory item gate.
The [Room 5 description](https://wikirby.com/w/index.php?title=Moonlight_Mansion_-_Room_5&oldid=574543)
corroborates this route. This is not a new ability-gating policy.

The native transition at ROM file offset 0x885AF6 leads from 702 to 744.
Room 744 tile (3,58) then enters room 745 (2_GOAL_1) at (7,3).
Consequently the descent also repairs PR #914's stranded Goal 1 check through
the existing 2-06 -> 2_GOAL_1 chain. No guessed hub shortcut or reverse route
is added. The [Room 6 description](https://wikirby.com/w/index.php?title=Moonlight_Mansion_-_Room_6&oldid=574542)
identifies it as a one-way route to Goal 1.

## Physical check ownership without extra traversal

For each room with logical compartments, create one terminal room-check region.
Every modeled compartment and the canonical parent can reach that check region;
it has no exits. Thus entering any part satisfies the single physical visit
check without granting access to another compartment's exits or chests.
This applies consistently to all five modeled split rooms, including Radish
8-07, whose check was not one of the original failures. Physical location
metadata and the client/native bit mapping remain unchanged.

## Evidence and regression scope

Native metadata was decoded read-only from the USA ROM with SHA1
`274b102b6d940f46861a92b4e65f89a51815c12c`, using
`tools/extract_room_evidence.py` and the pinned decompilation commit
`7d969fbce14fdc838d2c1ea01389717fb96c3189`. Room properties are at ROM file
0x9331AC (stride 0x28); the solidity/transition table is at 0xD63330.
Collision and object inspection supplements the transition decoder for the
Moonlight internal descent. No ROM bytes are included here.

Regressions isolate every compartment, require exactly one reachable check,
and reject cross-compartment traversal. They preserve all 263 unique physical
visit IDs/bits, test the directed Moonlight route, and generate real AP archives
across all three goals, room-sanity on/off, vanilla/shuffled shards and ability
gating on/off. The original seed 935 reproduction is included. The health
archive matrix now requires success instead of expecting the five-check error.

This establishes static route evidence and AP generation/accessibility, not
new emulator gameplay acceptance or exhaustive ability/physics validation.
Native payload, ROM patch, transport and running game are unaffected.
