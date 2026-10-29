# PR #914 generation and topology review

Audited source head `08507541bd3cbc596b6f65a885ea9a008b752a46` against main
`d4ea4a43a7197718dae8e9ce944f752864001f65`. The follow-up merges that main without
changing numeric item/location IDs, native payload, mailbox or save formats.
Existing seeds retain their generated graph; regenerate to use corrected logic.

## Generation consumes this graph

`data.py` loads `regions/rooms.json`, materializes logical compartments and rewrites
incoming entrances. `KirbyAmWorld.create_regions` calls `regions.create_regions`;
`KirbyAmWorld.set_rules` installs the compact requirements on actual entrances and
locations. `Main.main` calls those stages before restrictive fill, which consults
`Location.can_fill` and `CollectionState` reachability. Its accessibility sweep
collects reachable items (including other players' items) until completion and the
selected accessibility policy are satisfied. Minimal accessibility promises
completion, not that every filler check can be collected.

A bounded audit generated twelve real archives (seeds 935–946): six solo Kirby and
six Kirby + ChecksFinder worlds, all three goals, room sanity and ability gating
on/off, full/minimal accessibility, shards 0/2, ability randomization 0/1/2 and
statue randomization on/off. All completed fill and accessibility/beatability checks.
The original head evaluated compact rules 190,146 times, including 6,207 false
results; mixed worlds contained 38–50 cross-player placements. Each lever item
changed its corresponding gate from false to true. These are model checks, not
proof that the ROM permits every modeled move.

Starting Beam, Burning, Cutter, Mini, Stone and Wheel permissions are precollected;
a Mini-item self-lock is therefore not a valid counterexample. Capability helpers
remain permissive. Permission does not prove an accessible enemy/statue source or
an equipped ability. Shuffled enemy coverage guarantees distinct abilities only
when enough enemy types are available; it does not prove spatial availability.
Those limitations predate this PR. No impossible seed from ability-source placement
was established in this bounded audit, and no universal softlock guarantee is made.

## Stake export repair

The graph uses `can_pound_pegs`; the export helper previously recognized only
`CanPoundPegs`, producing an empty tracker list. Both spellings now identify the
same capability. Five actual directed entrances are exported. Olive's major chest
has a location requirement instead of the former, nonexistent 6-15 → Chest 2 edge.
The obsolete Rainbow Hub 3 → Moonlight Goal 1 shortcut is not restored to satisfy
a stale test. Compact `all`/`any` predicates remain intact when the legacy stake
pass runs; regressions independently toggle the capability and lever ownership.

## Radish 8-07 and 8-09

The same defective Radish definitions existed on main. They routed arrivals to
canonical rooms while leaving declared compartments disconnected, and listed
8-07 shortcuts unrelated to its native transitions. These are substantive graph
errors; an AP-only successful generation does not excuse them.

The private, unmodified USA ROM has SHA-256
`cfb194cd0cb373787094a962852e3e564fb2ecdb0609fe065afdd8de3f4e11f1`.
Native identities use `gRoomProps` at ROM offset `0x9331AC`, 40-byte records,
`doorsIdx` at +0x24; records 623/604 have indices 230/222. The 8-07 small chest
object is `0x8D039C`, at pixels (176,184). Its saved-check identity stays unchanged.

| Directed native transition | Record ROM offset | Activation tile | Destination spawn tile | Logical role |
|---|---|---|---|---|
| 601 (8-04) → 623 (8-07) | 0x8A89CC | (47,2) | (4,12) | lower chest compartment |
| 604 (8-09) → 623 (8-07) | 0x8A96E0 | (48,8) | (3,3) | upper Bonkers compartment |
| 623 → 601 (8-04) | 0x8AB97E | (3,15) | (48,10) | lower return |
| 623 → 606 (8-08) | 0x8AB970 | (34,7) | (2,28) | upper exit |
| 603 (8-06) → 604 | 0x8A9024 | (11,3) | (4,6) | upper corridor arrival |
| 604 → 603 (8-06) | 0x8A9642 | (2,5) | (11,4) | upper corridor |
| 604 → 622 (Goal 1) | 0x8A955C | (102,2) | (3,18) | upper corridor |
| 604 → 606 (8-08) | 0x8A97FC | (78,8) | (4,5) | lower corridor |
| 606 (8-08) → 604 | 0x8AA228 | (2,4) | (78,9) | lower corridor arrival |

The two 8-07 compartments are separated by full-width solid rows 8 and 9. The
chest is in the lower component. For 8-09, a flood over every tile except native
solid attribute 13 separates upper endpoints (2,5)/(102,2) from lower endpoints
(48,8)/(78,8). The flood deliberately treats slopes and destructible tiles as open:
it proves disconnection, not movement feasibility. The component sizes are
161/58 for 8-07 and 335/108 for 8-09. The verifier converts each incoming
spawn using native `sub_080562D0` (x = (sx << 12) - 0x800,
y = (sy << 12) - 0x701) before selecting its component. It decodes each source room's transition list,
asserts the recorded destination and spawn against independently decoded provenance
fixtures, then derives collision coordinates from the decoded spawn. Fixed record
addresses and expected spawn tuples are provenance fixtures, not generated evidence.
No reciprocal route is inferred.

Native collision attributes and record selection follow `src/code_080023A4.c`
(`gCollisionAttributes`, `GetCollisionTile`, `sub_080025AC`); ordinary door visuals
use that lookup in `src/mirror_door.c`. Room 623's object list contains the scroll
lock, Bonkers, two ordinary doors and the chest, with no separate hub/area door.
The 8-09 lower corridor's (48,8) transition is initially blocked by an attack-chain
barrier: attribute 242/flags 0x240 changes to 255 through mutation record 0x8A96CE.
The neighboring (49,8) tile has attribute 241/flags 0x101260. Native handler
0x08036CBC (especially 0x080370EC–0x08037180), `src/code_0800E0E4.c:103–149`
and `src/code_080023A4.c:586` establish generic attack-chain activation. No AP
ownership, lever or boss gate was identified for that barrier; reaching and
activating it through gameplay has not been tested here.

Room 623's upper door at 0x8D0354 is an ordinary subtype-0 door, but the passage
has a Bonkers defeat prerequisite. Scroll lock 0x8D030C and Bonkers 0x8D0330
share room slot 1: `src/scroll_lock.c:201–218,449–482` constrains/releases the
passage, and `src/object.c:1264–1285` increments the slot after miniboss defeat.
This is a normal combat prerequisite, not an identified AP ownership gate. Neither
combat feasibility nor accessible ability sources are established by this verifier.
An open door attribute or flood connection must not be read as unconditional travel.

Source reference: [katam 7d969fb](https://github.com/jiangzhengwenjz/katam/tree/7d969fbce14fdc838d2c1ea01389717fb96c3189).
[WiKirby's room description](https://wikirby.com/wiki/Radish_Ruins_-_Room_7)
independently describes the lower chest and upper Bonkers areas; the ROM records
and geometry, rather than the article alone, establish this correction.

Reproduce privately, without outputting ROM bytes:

```sh
python worlds/kirbyam/tools/verify_radish_compartments.py --rom /private/usa.gba
python worlds/kirbyam/tools/extract_room_evidence.py --rom /private/usa.gba --room 601 --room 603 --room 604 --room 606 --room 623 --output /private/radish-endpoints.json
```

The graph now routes 8-04 to the lower chest compartment, 8-09's lower corridor
to 8-07's upper compartment, and 8-06/8-08 to their respective 8-09 corridors.
Room checks remain terminal singletons and cannot bridge compartments. Unsupported
8-18/8-21/8-23/Goal 1 → 8-07 and 8-03 → 8-09 shortcuts are removed. Boss combat,
ability-source availability and fresh-game emulator acceptance are not established
by these static checks. No native code or ROM patch changes are needed here.

Rainbow 1-39's existing return to 1-38 is independently recorded by native room
537 → 536 at `0x875E3E`; the stale one-way test was corrected without adding an
edge. Other unresolved campaign/runtime limitations, including the separate Hub
work's directed-pair accounting and release/security acceptance gaps, remain open.

## Candidate verification

- Full Kirby suite: 4,355 passed. The final verifier import/type-narrowing follow-up
  also passed 49 verifier/room-sanity tests; seven changed Python files pass mypy.
- Twelve actual archive generations pass with the mixed options described above;
  each is beatable and fulfills its accessibility setting.
- Shared reachability: 2 passed and 494 subtests passed. Only the Kirby-specific
  expected-unreachable list changes; assertions and other games remain untouched.
- Fatal Flake8 checks and whitespace checks pass (existing CRLF files retained).
- Native compartment verifier passes against the unchanged original ROM. Native
  payload and BSDIFF are byte-identical to integrated main; no native rebuild is
  required for these Python/graph changes.
- Snapshot differences are confined to graph/location exports and stake metadata.
  All item definitions and numeric check identities remain unchanged. The only
  location definition change is the Radish 8-07 chest's logical parent.

The original PR's eleven failures were reproduced: stale room-count/adjacency and
schema expectations, the empty stake export and tracker contract, and the golden
slot-data mismatch. Corresponding tests pass on current main, so these were not
classified as inherited AP setup failures. The reviewed update corrects the alias
bug and source-backed topology, and updates expectations for the resulting graph.
The original-head unit CI also reported 11 failures/4,191 passes. No new CI success
is claimed for an unpublished local candidate.
