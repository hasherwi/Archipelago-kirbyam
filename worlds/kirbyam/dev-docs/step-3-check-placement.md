# Step 3: check, goal and event placement

The [placement audit](../tools/audit_check_placement.py) joins the actual
compiled AP locations to the existing native USA inventories. To inspect the
per-check keys, owners, room IDs, anchors and nearby alternative compartments:

```sh
python -m worlds.kirbyam.tools.audit_check_placement --json /tmp/kirby-check-placement.json
```

The JSON is a review output, not another source of rules. Matching a native
room or source pointer does not in itself prove ability availability,
unobstructed access, or successful live server acknowledgement.

| Check or event | Catalog count | Evidence and boundary |
| --- | ---: | --- |
| Native room visits | 263 (8 core landmarks) | Independent native completion bit. Every AP compartment in a shared native room feeds the one visit sink; the sink has no exits. |
| Small and big chest rewards | 80 | Exact chest source, native room, coordinate and flag; 65 minor, 10 map, 4 vitality, 1 Sound Player. The tutorial chest's AP owner is the game-start bridge and the native object is in room 805. |
| Big Switch checks | 15 | One native Big Button placement in the physical owner room. The world-map Hub Connection can be received without a press; the press does not grant ownership of that connection. |
| Lever checks | 4 | Exact native chest objects with reward `0x63`, reported through dedicated lever bits instead of the chest recovery map. The corresponding wall item is separate. |
| Area-boss defeats | 8 | Native encounter slots 1–8 in their matching rooms, not arena visits, minibosses, or receipt of a shard. |
| First area visits | 9 | Observed area ID; the area summary represents the union of physical arrivals, not a travel shortcut. |
| Goal Games | 16 | Matched source room, trigger tiles and completion bit. Entry, return, zero/nonzero prizes and AP acknowledgement are distinct; reaching the room is not the check. |
| Goal definitions | 6 | Five current selectable modes, one legacy client reporting binding. Only the selected goal advances AP completion. All goal objects are addressless from region creation, never eligible for fill. |
| Named region events | 21 | 15 switch annotations, 4 lever annotations, Dark Meta Knight sequence prerequisite, post-clear Central return. None has a numeric AP location or item code. |

**Option behavior.** RoomSanity off produces **140** addressed locations
(132 other checks plus 8 core visits); on produces **395**. The same physical
visit sinks are available to the 100% goal independently of the AP option.
The goal still models access to each native visit, exact physical chest,
switch and lever, prerequisite fight sequence and required AP item. The client
separately checks native full-clear/save evidence and its existing server
protocol. No native flag, location ID, item delivery or goal reporting changed.

**Side of obstacle.** A native visit is a union of entrances; a physical reward
is not. Moonlight Goal Room 2's Chalk chest remains in the upper-left
compartment; the Goal Game check remains on the different door side. Candy
9-Chest-2 Vitality and Carbon Paint share native room 403 but keep separate
ingress regions. Peppermint 7-Chest's lower map, lower small chest and upper
small chest also stay separate. The generated inventory identifies 30
action-based checks that share a native room with alternative AP compartments.
It records existing exact traversal overlays and source coordinates; it does
not treat a different compartment or absent overlay as a proven bypass.

**Corrected differences.** All 15 addressless Big Switch annotations now
inherit the matching physical switch's final access predicate in its own
region. Visiting another room in that area no longer sweeps the annotation.
The 33 incomplete RoomSanity compartment families now match the native room
visit bit; no new connection from a check back into game space was introduced.
Production catalog validation rejects duplicate owners and ID/label
collisions instead of hiding them via first-owner iteration order.

**Compatibility boundary.** The two existing Moonlight Mansion / Rainbow East
raw Big Switch transport-bit overrides are explicit in the audit output and
the [contract](../data/hub_switch_contract.json). This change does not
reinterpret the saved bits or claim an independently replayed mapping of both
individual physical presses to their outgoing AP packets. Review of any
remaining gate-side reachability and ability acquisition belongs to the
separate next steps; these checks do not alter playthrough evidence.
