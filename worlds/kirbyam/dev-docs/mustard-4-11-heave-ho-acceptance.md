# Mustard Mountain 4-11: Hammer and the large Heave-Ho

Issue [#1134](https://github.com/hasherwi/Archipelago-kirbyam/issues/1134)
investigates an optional in-room crossing. The large Heave-Ho moves with
Hammer, but it is **not** a requirement for the Small Chest, the room visit,
or the existing exit to 4-12. Do not add a traversal rule unless a later
witness establishes a distinct check, room transition, or exclusive ability
source.

## Native witness

The tests used mGBA 0.10.5, the USA ROM (SHA-1
`274b102b6d940f46861a92b4e65f89a51815c12c`), and the AP base patch from
`364a0773816696254443a2eb86f63415640ada62`. This was a controlled room-local
fixture with untouched room objects and collision: player one spawned at
(790, 60) in native room 322; CPU Kirbys started in another room. The Hammer
trial started already equipped, with the stock Hammer animation table.
The inputs below start after Kirby has settled on the dry ledge near
(776, 41), facing right. No phone, damage boost, or AI assistance was used.

- **Hammer:** Tap B while grounded and let the swing finish. With one frame
  of B and 50 released frames per swing, the block moved two pixels left per
  hit. The 17th swing took it from x832 to x830, starting its drop. Let it
  settle before proceeding. The test used 18 cycles, then jump and move
  right, tapping A again in the air to hover. For exact input timings after
  the 18th cycle: A+Right for 1 frame, Right for 12, alternate A+Right and
  Right for 1 frame each until three further A taps, then Right for 140
  frames. Kirby reached (934, 110) with Hammer still equipped and all 6 HP.
  The two loose 1-Ups were visible in the far section; no AP chest event
  fired during the crossing.
- **Normal:** From the same starting ledge, hold Left for 15 frames, release
  for 40 to drop onto the chest platform, hold Right for 14, then press Up
  at the chest. The actual AP chest event reported template `0x088C4F24`
  at (752, 88) with all 6 HP and the Heave-Ho still at x864. The chest
  therefore does not acquire a Hammer or Advanced Logic requirement.

## Randomizer implications

| Room content | Consequence for logic |
| --- | --- |
| Small Chest, AP location `3960574` | On the chest side, witnessed with Normal and no phone. Leave its current rule unchanged. |
| RoomSanity visit, AP location `3961114` | Credits entry to room 322, not reaching the far side. No split check. |
| Loose 1-Ups at x984 and x1048, templates `0x088C4F6C` and `0x088C4F48` | Native pickups, not AP checks. |
| Pengy, template `0x088C5044` | Starts at x936, but native movement brought it to x807 while the Heave-Ho remained intact at x864; Kirby was still on the chest side. The local test did not establish a swallowed grant. Do not infer an exclusive source from the spawn coordinate. |
| Existing 4-12 exit, template `0x088C4FD8` | At x40, before the lava wall. The optional crossing does not add a room transition. |

The witness establishes a physical Hammer maneuver, not a new modeled
Advanced Logic route. It does not establish a Stone method, access to Hammer
from any specific seed, or a retained-ability route for the separate 4-12
cannon approach.

Sources: [room rules](../data/regions/rooms.json),
[exact AP chest mapping](../data/locations.json),
[native object placements](../data/ability_source_inventory.json), and
[large Heave-Ho implementation](https://github.com/jiangzhengwenjz/katam/blob/89a012c0d2e46a0ae87d9133c7a0435d95e348e8/src/large_star_stone_block.c).
