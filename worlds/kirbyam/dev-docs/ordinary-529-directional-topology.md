# Native 529 directed passage review

Native 529 is Cabbage Cavern Room 3 (`REGION_CABBAGE_CAVERN/ROOM_3_03`), with no item chest and one existing
RoomSanity check (3961090, completion bit 185).

## Accepted ordinary connection

Two independent fresh-layout controller replays establish the lower and
upper-right passages at default and 500% enemy durability. Both use Normal,
ordinary water-gun Bomb activation, and the visible bottom swimming connector.
Every audited native 529 frame retains all eight F5 tiles. No metal ability,
damage boost, inherited opened layout, or assumed room reset is needed.

| Direction | Native incoming record | Native outgoing record | Evidence |
| --- | --- | --- | --- |
| Lower to upper-right |523 `0x89E3F8` (17,2) to 529 (5,29)|529 `0x89EB0E` (24,2) to 512 (23,19)|`ordinary-529-lower-upper-right-acceptance.json`|
| Upper-right to lower |512 `0x89D364` (23,18) to 529 (24,3)|529 `0x89F236` (3,28) to 523 (19,3)|`ordinary-529-upper-right-lower-acceptance.json`|
| Lower to upper-left |523 `0x89E3F8` (17,2) to 529 (5,29)|529 `0x89EB00` (5,2) to 512 (10,19)|`native529-lower-to-upperleft-acceptance.json`|
| Fresh upper-left return |512 `0x89D344` (10,18) to 529 (7,3)|529 `0x89EB00` (5,2) to 512 (10,19)|`native529-fresh-upperleft-return-and-boundary.json`|

The lower-to-upper-left runs audit 1,263 gameplay frames each, including 1,200
native529 samples. All 90 Bomb cells are native at entry; precisely 53 cells in
four left components change to water. The other 37 cells and all F5 stay intact.
The fresh upper-left return audits 178 frames each, with 107 native529 samples;
all 90 Bomb cells remain native. These are distinct fresh runs, not a replay
using the lower route's already-opened wall.

The fresh fixtures start beside the source-room doorway. They prove the actual
door transition and directed passage, not independent access to source rooms 512/523.
Both 500% fixtures apply the pinned production scaler once before a blank-save
boot. These are native no-loss runs, not direct AP 1HP or randomized-placement
fixtures. Their scope does not establish equipment-preserving carry.

## Sufficient directed AP compartments

The canonical 529 region covers the mutually reachable lower and upper-right
approaches. It retains the existing ordinary exits to 523 (`ROOM_3_01`) and
512MAIN (`ROOM_3_04`), preserving their existing `can_swim` rules.

One logical `UPPER_LEFT` compartment receives only the redirected incoming
512SUB (`ROOM_3_04_SUB`) edge. Its native entry is 512 `0x89D344` (10,18)
to 529 (7,3). The local return doorway is 529 `0x89EB00` (5,2) to 512 (10,19).
There is no generic 512SUB-to-canonical 529 alias.

The canonical 529-to-UPPER_LEFT edge uses the separately accepted Normal
below-trigger Bomb route. No reverse edge is installed: fresh upper-left starts
above the lower F2 barrier, and tested downward air-puff inputs do not reach Bomb (3,11). This is bounded negative
evidence, not a proof that every ability or every possible route fails. The
source-backed downward-puff bound reaches at most y160.496 from the sealed
floor, short of the trigger's y176 top. The separate 311-frame bounded tests at
both durability settings leave all F2/F1/F5 cells unchanged. No speculative
metal ability is assigned to this unreviewed direction.

UPPER_LEFT returns only to 512SUB. Every 529 compartment connects to one terminal
`__ROOM_CHECK` sink. The sink must never provide passage between compartments.
No new check IDs, physical completion bits, metal-provider predicates, or
source-policy states are required.

## Regression coverage

- Keep the default/500% fresh accepted inputs, actual doorway transitions and
  collision readbacks, with portable Git-blob integrity checks.
- Test each entry in isolation with empty inventory, including the absence of
  an upper-left-to-canonical edge and absence of a generic 512SUB alias.
- Preserve the RoomSanity3961090/bit 185 singleton and all item/check IDs.
- Update the native/AP mapping through its official renderer and slot/region
  snapshots after any production compartment edit.
- Run focused topology tests, the complete RoomSanity file (including archives),
  mapping tool tests, and normal final-generation guards. Starting ability
  removal remains outside this checkpoint.
