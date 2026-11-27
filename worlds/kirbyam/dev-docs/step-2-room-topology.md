# Step 2: room, subroom and directed traversal audit

## Compiled inventory

Join the production-normalized AP graph to the pinned [native room inventory](native-room-wikirby-map.md). The join accounts for all 354 physical AP compartment keys, including Copy Ability Room `/MAIN` (native 970), which is a physical room despite its suffix. The native table contains 286 populated records; not all are represented by an AP region. The other AP nodes are ten area summaries, 21 Room Sanity sinks, and two start nodes including Menu.

| Link type | Count | Treatment in a physical carry route |
| --- | ---: | --- |
| Different native room IDs | 561 | Directed candidates only; verify the actual door/arrival and state restrictions |
| Same native room ID | 82 | Compartments of one room; don't assume either direction is open or count an ordinary boundary as a crossing |
| Area summary fan-in | 350 | Bookkeeping, never a physical crossing or shortcut |
| Room Sanity sink links | 59 | Check ownership, never travel |
| Area-summary bridges | 3 | Aggregate topology; no physical carry credit |
| Menu/start/tutorial bookkeeping bridges | 3 | Initial/spawn or tutorial state; not automatic physical return routes |

Of the 561 directed cross-room candidates, 241 have no exact reverse AP edge. An existing reverse edge is also not native evidence; two mirrors between the same IDs may use different compartments or spawn points. Preserve doors that are truly one-way. The 134 unpaired generic-block entries from Step 1 are a separate audit queue, not a count of confirmed missing doors.

### Existing synthetic route to watch

71 physical Rainbow compartments feed the Rainbow area summary. The area summary points to Central Circle and to the shard-gated aggregate Dimension Mirror. These are AP reachability edges, not player movement. In particular, do not count `Rainbow room → Rainbow MAIN → Central Circle` as a physical return, a portable ability source, or proof that a locked mirror can be exited. The start currently reaches Central Circle via the same summary, so removing the bridge without moving start setup would change generation. This pass leaves the start and the three area-summary bridges unchanged.

The split-room check sink can be reached from multiple compartments to award a shared Room Sanity check. The area-summary builder used to give all 21 sinks a redundant outgoing summary link because their names contain `/ROOM_`. This pass removes those links. Each real feeder compartment already connects to the same area summary, so area visits still work; a sink no longer has an outgoing travel edge. Do not connect a sink back to the canonical room, which could leak other doors from the wrong compartment.

### Physical witnesses and the three-transition rule

Review the 165 graph variants under the 66 current catalog targets. In the Area Keys-off compilation, they contain 1,599 cross-native-ID witness edges; 97 are recognized by their differing native IDs without a literal `room_transition: true` flag. That matches the engine's existing transition detection and is not 97 missing gates. One explicit same-native transition, native 736 Mini `arrival → source`, is the authored down-cannon self-transition **before** acquiring Mini. Preserve its room-state handling and don't count it as an equipped carry crossing in this witness. These totals count declared edge instances across graphs, not unique doors, routed distance, or evidence that all alternatives are Standard. The Standard limit is calculated on the **actual equipped route to the required action**, not by counting every edge in a witness graph.

### Charge-free Phone return

The native L-return path is independent of the Phone-a-Friend item and battery charge. [Existing controller evidence](phone-implementation.md) proves a zero-charge return from native 190, dry returns with Cutter retained, and a separate underwater Normal return from 108. UFO can return but is cleared by arrival at Central Circle in its verified cases.

Don't assume every room/state is eligible: the [native input path](https://github.com/jiangzhengwenjz/katam/blob/89a012c0d2e46a0ae87d9133c7a0435d95e348e8/src/kirby.c#L6968-L7126) checks room priority bit `0x40`, active encounter/session state and the eligible character state; the shown idle path excludes Mini. The [return sequence](https://github.com/jiangzhengwenjz/katam/blob/89a012c0d2e46a0ae87d9133c7a0435d95e348e8/src/kirby.c#L13124-L13401) leads to native 801, not an arbitrary Central Circle compartment. A source review found that all 24 direct entry call sites require the room bit, the encounter/session predicate and the global state gate. Which attack, movement, or ability states can take the branch still varies.

The [local extraction tool](../tools/extract_phone_return_rooms.py) reads the room bit and the encounter-to-session-slot mapping from an exact SHA-1-matched USA image. The pinned retail extraction is now in [the native room return inventory](phone-return-native-rooms.json): 262 populated rooms have the enable bit and 24 do not. Central Circle, the three tutorial rooms, Copy Ability Room, and the final-area or minigame rooms on the excluded list do not acquire return edges. A room with the bit set is only statically eligible, and encounter rooms are not permanently excluded solely because they have a session slot. A return never implies a reverse route or grants a Hub Connection. No Phone edges are installed by this pass.

### First native door crosswalk

- **Rainbow 1-41 (141):** the pins cover four arrivals and their four outgoing doors. Native 543 (spawn 3,14) and 143 (43,19) enter the lower partition. Native 144 (43,9) enters `EAST_MOONLIGHT`; native 545 (34,4) enters `TOP_MUSTARD`. The existing normalized AP edges land in those exact partitions. The east-to-top flights and the Bomb Block routes between partitions are same-room logical moves, not four more doors; the observed one-way cap geometry is not grounds to add an opposite edge.
- **Moonlight 2-14 / 2-15 (741/742):** there are two directed 741→742 records, with distinct spawns (19,8) and (30,29). Upper lands in `UPPER_RETURN`; lower lands in canonical 2-15. Native 742 exits to 741 upper (spawn 11,8) and 705 Warp (spawn 4,39). The native records prove their existence and landing, not a route from the upper return partition to either trigger. Current logic keeps the upper partition disconnected from the lower chest and Warp; the old permissive upper shortcut stays removed.

### Full retail tile-door inventory

[The decoded door catalog](native-tile-door-inventory.json) records 724 directed tile transitions from the SHA-1-matched USA image. It records each trigger and landing separately. Of the 561 cross-room AP edges, 459 match exactly one directed native room pair, 54 match multiple candidate doors, and 48 have no tile match. The last group includes known non-tile paths such as boss/Goal returns, portals and object-driven doors; it is not 48 confirmed errors. A one-door match still does not prove that an AP source compartment can reach the trigger or that the landing is assigned to the right compartment. The audit command reports all candidates per edge without installing new logic.

## Next audit batch

1. Crosswalk the candidate edges to actual native door/spawn records, expanding beyond the [141](ordinary-141-door-topology.json) and [742](ordinary-742-door-topology.json) pilot. Keep trigger direction and landing compartment explicit, and distinguish genuine reverse doors from room resets.
2. Derive a clean room eligibility inventory for the charge-free return from the pinned retail table and test state/ability exceptions separately. Add only evidenced, correctly directed transitions.
3. Keep Step 3 check/event ownership separate from movement; a successful room visit does not prove its chest, goal, or reverse door.

Reproduce the full JSON inventory from the repository root:

```sh
python -m worlds.kirbyam.tools.audit_room_topology --output /tmp/kirby-room-topology.json
```
