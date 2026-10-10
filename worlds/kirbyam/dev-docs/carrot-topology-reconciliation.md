# Carrot compartment correction from USA-ROM evidence

The existing lower 1-UP check at native source `0x008D3E88` was assigned to
`ROOM_5_13__LOGIC__ENTRY_FROM_5_12`. Move it to `ENTRY_FROM_5_07`. Its location
ID 3960606, source address and collection behavior stay unchanged. Music Sheet
#6 is now active in the verified upper `ENTRY_FROM_5_14` compartment as part
of main's 65 physical checks. No new progression route is added.

## Evidence and scope

The verified USA ROM independently gives the lower chest's ObjectTemplate
position as `(72, 264)`, reward 0, and the music chest at `0x008D3E64` as
`(128, 120)`, reward 46. Completion records for native 734 contain those same
two positions. The previously examined USA save-state collision grid has a
solid divider at rows 9..10; the Pi also independently decoded the USA RL-compressed solidity map
(index 261, 368 cells at width 16) and confirmed all cells in those two rows
use collision attribute 13 (native mask 0x200). Its hash and provenance are recorded in
[minor-chest-collection-items.md](minor-chest-collection-items.md).

[The extracted records](carrot-room-evidence.json) show native 719 entering
734 at tile `(13, 14)` in the lower section, and 734 returning to 719 from
`(13, 13)`. Native 720 enters the upper section at `(14, 5)` and has its
separate return. Current room-sanity mappings assign 719 to 5-07, 720 to 5-14,
and 734 to 5-13. This proves which of the already modeled entrance compartments
owns the lower chest. Isolated-entry graph tests prevent 5-12, 5-14, 5-18 or
5-Warp from collecting it merely through their modeled 5-13 entry.

This does not prove full gameplay reachability of the music compartment from
the start. The old graph still mixes historical names with current room-sanity
identities, including legacy 5-12 and 5-18/5-Warp compartments. They are retained
without chest claims pending a separately justified route reconciliation.
Absence from the extracted tile records is insufficient evidence for deleting
an edge: native transitions can also be driven by objects. Music Sheet #6 must
not be enabled just because native 720 has a record entering its section.

## Independent decoder review

The review checked original structures and consumers at KatAM commit
`7d969fbce14fdc838d2c1ea01389717fb96c3189`, separately from the AP room graph:

- `include/data.h`: RoomProps stride 0x28, solidityMapIdx +0x1A,
  objectListIdx +0x20, doorsIdx +0x24. AP keys use doorsIdx only.
- `data/data_2.s`: solidity and completion pointer tables each span 0x47C,
  or 287 entries. Completion records use a byte size at +1; their signed
  chest coordinates differ from unsigned destination/spawn fields.
- `src/code_080023A4.c`: completion count and 0x8000 visited bit are separate;
  completion records are indexed for progress, not an outgoing-edge list.
  The native tile lookup matches collision attribute plus source x/y and
  advances by the halfword size at +4.
- `include/data.h`: tile kinds 1/2/3 have sizes 0x12/0x0E/0x0E. Kind 3
  destination is +8, spawn tiles +0xA/+0xB and flags +0xC.
- `src/kirby.c`, `sub_080562D0`: kind-3 flags affect facing and whether the
  saved respawn is updated. The adjacent object-driven transition path does
  not read this table. Record presence alone is not an unconditional AP edge.

The decoder now retains flags, checks the entire record including trailing
fields/padding, rejects invalid destinations and does not dereference a zero
count's unused pointer. Its zero-kind list ending is an observed USA-data
convention, not a demonstrated condition in the native search loop. Size/hash
verification pins CLI input, and a bounded walk rejects malformed lists.
Synthetic tests exercise these semantics independently of the real-ROM run.
Only interpreted facts are checked in; no ROM, extracted code or graphics.

## Validation

Re-run the extractor with the lawful USA ROM and rooms 719, 720, 730, 732, 734;
re-run `enumerate_minor_chests.py` against the pinned AMR item source and compare
all 65 entries. Run the combined v0.4.0 Kirby suite, including isolated Carrot
entry tests. Actual BizHawk gameplay, save/reload and connector acceptance remain
unrun; a supported x86-64 host is still needed for that acceptance path.

Pi validation on 2026-10-09: 982 combined tests passed, including 16 decoder
tests and six new Carrot regressions; all 65 regenerated chest entries match
with zero ambiguity. The checked-in base patch remains unchanged.
