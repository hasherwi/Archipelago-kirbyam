# Reinforced traversal implementation

This change is limited to reviewed environmental mechanisms. Ordinary metal
traversal remains deferred. Native collision `0xF7` is an environmental class,
not an exhaustive identification of visually reinforced metal: the mechanism
audit also finds crumbling platforms and cannon fields. Tile presence alone
must not add an ability gate, a room-wide requirement, or a reverse connection.

## Normal Heave-Ho mechanism

`heave_ho_pull` is a dry, same-room action available only while Normal is
actually equipped. The planner may drop carried equipment first; it cannot
silently retain Hammer, Stone, or another ability through the suction sequence.
No unlock item or enemy assignment grants this action. A serialized witness
must identify its object, approach and disposal evidence.

The action ends in a new compartment. It does not provide a persistent `opens`
event, an automatic return edge, or credit across a room reload. The native
Heave-Ho destructor marks a fallen/disposed object done, but that fact is not a
proof that its state survives every room transition. This implementation does
not need that broader lifetime assumption.

## Radish Ruins Room 22, native 102

The reviewed local mechanism is **pull from the right, clear the left tunnel**.
Native type `0x79` template `0x008D21C8` starts at `(488,280)`. Normal suction
from its right moves it into the shaft at column 31. Its falling collision clears
`0xF7` at `(31,19)` through `(31,22)`. The useful route is left along the now
unobstructed tunnel, not down through those four tiles.

The isolated controller run began at `(536,280.996)`, faced left, held B for
240 frames, then waited 30 frames. All four tracked tiles changed from 247 to
0. Walking left 90 plus 165 frames reached the Battle Notes chest at
approximately `(208.414,296.996)`, with Normal equipped and 6 HP. This establishes
the mechanism and chest approach, not an ability-equipped carrier or native
collection-save acceptance. See `heave-ho-native-acceptance.json` for fixture,
input, ROM identity and read-only observations.

A second controller run starts in native 113 at `(40,72.996)` and uses the
actual Up transition `0x008AF41E` into 102 at `(1176,120.996)`, matching the native
spawn record `(74,8)`. Normal floating, leftward movement and a platform descent
reach the right-hand approach. Suction again clears all four F7 tiles, and the
leftward walk reaches `(213.742,296.996)` beside the chest with Normal and 4 HP
remaining from 6. This run proves the actual entrance-to-target path; it does
not prove damage-free or one-hit-mode access. The fixture only changes initial
room/spawn in 113, with no runtime RAM writes or changes to room 102's objects,
terrain or collision code.

The installed `reinforced_102_battle_notes` graph records that directed
arrival, approach, clearance and chest path. Its target is only
`MINOR_CHEST_MUSIC_NOTE_04`; the main room exit and unrelated chest are unchanged.
It has no ability sources, AP-item prerequisites, retry assumptions or reverse
edges. The graph is valid in every ability-source randomization mode because it
uses Normal suction rather than a copied ability. The later combined AP-ROM replay also verifies collection and the local AP check
event, as described below. Existing traversal
logic does not model HP costs; no speculative health gate is added. The prior
chest availability is preserved, not newly certified for one-hit settings.

## Combined AP-ROM collection acceptance

A follow-up replay applies the exact inherited `base_patch.bsdiff4` from this PR
(Git blob `4d8ca561bf19893cbbc141e02f843b2afa9dad3d`) to the original USA ROM,
with only the established initial room 113 spawn fixture. The same controller
entry and Normal Heave-Ho route reaches and opens Battle Notes with 4 HP.
After Up at the chest, native flag 76 changes from clear to set (RAM byte
`0x02038969`: 0 to 16), and the local AP event counter at `0x0203B08C` changes
from 0 to 1. The first event-ring source is `0x088D230C`, the exact Battle Notes
chest template. Both remain set at the final checkpoint.

[Combined acceptance](heave-ho-ap-acceptance.json) records patch/fixture hashes,
inputs, and read-only observations. There are no runtime memory writes, no
server connection, and no terrain/attack changes. This establishes native
collection and local AP event emission, **not** server acknowledgement, item
delivery, battery-save persistence after reload, or damage-free traversal.

## Olive Ocean Room 6, native 134

The existing `mini_134_ocean_spray` witness is unchanged. Its combined controller
acceptance pulls the Heave-Ho only from x=712 to x=693.75, recovers the emitted
Mini star, jumps over the moved object and passes the final Mini throat. It
reaches the Ocean Spray Paint chest without relying on destruction of the six
`0xF7` shaft tiles. The new isolated attempt likewise moved this object without
clearing that shaft. Do not replace the proven Mini/drop/recovery route with a
mandatory reinforced-disposal or ordinary-metal requirement.

## Evaluation cost

The new witness uses four nodes, three edges, zero ability sources, and four
reached states in the Normal case. It adds no state dimension or persistent
opening combinations. Existing graph compilation remains cached.

A Python 3.12 paired in-process benchmark compared the prior kernel at `1f8e458`
with the integrated implementation (same traversal code as `49ec2e22`), excluding
imports/compilation. Twelve warmed samples gave 8.52 microseconds per new-witness
evaluation (10,000 calls per sample). Existing Mini 134 and peg 605 graphs kept
exactly the same seven and 18 reached states respectively. Their median times
were 18.38 versus 16.72 microseconds and 56.56 versus 53.99 microseconds (5,000
calls per sample). Timing ranges overlap; this shows no measurable regression
in these small fixtures, not a speedup claim or a whole-generation benchmark.
No optimization or duplicated per-room engine was introduced.

## Verification boundaries

Python tests establish graph semantics, source-policy independence and schema
validation. They do not prove native motion. Native records distinguish isolated
fixtures from actual-entry controller traversal, and original-ROM checks from
combined Archipelago-ROM acceptance. Full visual Bomb Block/chain coverage is
still separate work; the F7 inventory must not be used as a substitute.

## Sources

- [Native Heave-Ho behavior](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/star_stone_block.c).
- [Native attack/tile collision](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/object_collision.c).
- [WiKirby room context](https://wikirby.com/wiki/Radish_Ruins_-_Room_22).
- [Isolated controller evidence](heave-ho-native-acceptance.json).
- [Actual-entry controller evidence](heave-ho-entry-acceptance.json).
- [Existing combined Olive 6 acceptance](../docs/traversal-logic.md#combined-olive-6-acceptance).

The [targeted Bomb-chain follow-up](bomb-chain-route-audit.md) retains the existing
108/743 directed topology and adds regression coverage without a duplicate
mechanism state machine. It does not complete the visual chain inventory.
