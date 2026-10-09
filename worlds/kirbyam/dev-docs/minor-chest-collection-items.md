# Fixed minor-chest collection items (#525, #535, #537)

## Identity and scope

- Spray Paint #1..#14: AP item IDs 3860200..3860213, native rewards 0x14..0x21,
  native ownership bits 0..13, location IDs 3960500..3960513.
- Music Sheet #1..#10: AP item IDs 3860214..3860223, native rewards 0x29..0x32,
  native ownership bits 1..10, location IDs 3960514..3960523.
- Sound Player remains item 3860025, its own big-chest location, and music bit 0.
- Numbered collection labels deliberately do not assume the starting-color palette
  table has the same ordering as native Spray Paint collection indices.
- IDs below 3860200 are not repurposed: deferred PR #932 reserves 3860041..55,
  PR #908 uses 3860041..48, and dynamic ability IDs occupy 3860101..131.
- The original fixed location rows already identified these collection indices
  (Spray Paint bit 0..13; Music Note legacy bit 101..110). The manifest has exactly
  one physical source per collection reward, so the same IDs retain their identity.

## Native evidence

All decomp links are pinned to katam commit
`7d969fbce14fdc838d2c1ea01389717fb96c3189`:

- [chest.c](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/chest.c):
  `sub_0800AFC8` writes native chest persistence first, then dispatches
  Spray Paint as `reward - 0x14`, and Music Player/Sheets as `reward - 0x28`.
  Collection grants precede `UpdateSaveBufferByOffset`. Ordinary rewards 0..5
  spawn their consumable only later in `sub_0800B97C`.
- [treasures.c](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/treasures.c):
  `CollectSprayPaint` and `CollectMusicPlayerOrSheet` each perform only a bitwise OR.
  They do not set chest flags, change palettes, or save independently.
- [treasures.h](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/include/treasures.h):
  the native ownership fields are consecutive u32 words in `gTreasures`.
- Checked-in `data/addresses.json` and `data/native_address_policy.json` already
  establish USA fields 0x02038974 (Spray Paint) and 0x02038978 (Music Player/Sheets).
- The checked-in USA manifest establishes the 24 physical sources and rooms.
  No new JP-to-USA address shift, ROM offset, or SRAM layout is inferred here.

## Runtime contract

The 64 active sources are exact matches in the same AP-owned source table. The generic
chest hook records the source and preserves native chest flags. It marks only
ordinary rewards 0..5 for delayed popup suppression. New Spray Paint interception
uses the already-validated callsite 0xB1D0. Music Sheets use the existing 0xB264
Sound Player/Sheets wrapper. Unknown sources retain bounded native collection
behavior. Collection reward fields remain unchanged, preserving their popups.

Mailbox delivery uses the same tested C helpers as native-host contract tests.
All 24 item IDs can OR their ownership bit and ACK normally, but only the 23
items with active locations enter the generated pool. Replay is
idempotent and leaves unrelated bits untouched. A sheet never implicitly unlocks
Sound Player; delivering any collection item never consumes a physical check.
Existing one-shot chest persistence and all six ordinary consumable effects stay
unchanged. Cherry uses the existing Small Food item/effect.

The popup bridge preserves r1, r2, r3, and LR around its C call with a four-register
stack frame. It then replays `ldr r4, [r2, #0x4C]; adds r0, r4, #0`, including the
original flag effects. It no longer assumes caller-live scratch registers can be
clobbered or reconstructs r2 from a different register.

## Candy Spray Paint #6: resolved compartment

Location 3960505 and item 3860205 retain their historical identities. Exact source
0x008C5EA0 (native reward 25, room 403) is claimed only by
`REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_2__LOGIC__ENTRY_FROM_9_01`.
The unsplit parent remains unreachable; no transition, gate, exit, or incoming
routing override changes. The other compartment retains the Vitality chest.

Independent evidence, rather than previous-room history alone, establishes this:

1. The checked-in USA state `9 - Candy Constellation/9 - 8 Small Chest Spray
   Paint.State` (SHA-256
   `1d719a3487582e79a9ac72c4a4be52a51a5db32d9906c2740e3dbec18218fee4`)
   contains the live source pointer 0x088C5EA0, reward 25, room 403, and chest
   position (144, 88). `gKirbys[0].roomId` is 403 and its `spawnLocation` is (7, 9).
   The 976 x 208 room's decoded collision grid encloses that chest in the left
   section (tile columns 4..13, rows 1..8), with its only mirror tile at (5, 8).
   Solid tile 0x0D walls enclose the section. The other mirror is at (55, 3).
2. Pinned [AMR mirror records](https://github.com/HeyImTG/Amazing-Mirror-Randomizer/blob/2ea1c963535405e1ba7d678bb4361a7f5c30703b/JSON/mirrors.json#L2290-L2345)
   independently encode `Can4_Can5Carbon` as `93 01 07 09 01`: destination
   native room 403, spawn (7, 9). The reverse returns to native room 404.
   `Can12_Can5Vitality` instead enters room 403 at (55, 4) from native room 405.
   The native spawn calculation places Kirby at `(tile_x * 16 - 8,
   tile_y * 16 - 7 - 1/256)`. These are entry coordinates, not mirror tile centers.
3. The pinned USA decomp [pause-map room record for native 404](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/pause_area_map.c#L1940-L1946)
   gives map coordinate (12, 30), independently matching the historical
   [AP 9-01 source metadata](https://github.com/hasherwi/Archipelago-kirbyam/blob/9a515bc5fc33a4b8c7de238912f60114b49ec83f/worlds/kirbyam/data/regions/rooms.json).
   The analogous native 403/405 metadata agrees with 9-Chest 2/9-09. Map
   coordinates are not gameplay coordinates; both forms are kept distinct here.

AMR targets JP, so no ROM address or global version shift is imported from it.
Its room/coordinate tuple is corroborated by the checked-in USA state and USA
manifest. AMR writes `location` as five big-endian bytes ([writer](https://github.com/HeyImTG/Amazing-Mirror-Randomizer/blob/2ea1c963535405e1ba7d678bb4361a7f5c30703b/amrMirrors.py#L485-L494),
[serializer](https://github.com/HeyImTG/Amazing-Mirror-Randomizer/blob/2ea1c963535405e1ba7d678bb4361a7f5c30703b/amrShared.py#L4-L6));
the native [door structure](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/include/data.h#L125-L136)
then reads a little-endian u16 room ID followed by coordinate bytes.

### Reproducing the state observations without a ROM

Open the State ZIP, Zstandard-decompress `Core.bin`, and skip its four-byte
BizHawk state-length prefix. The mGBA serialized state's EWRAM is at 0x21000
and IWRAM at 0x19000. Read the USA structures using these native addresses:

- `gCurLevelInfo[0]`: 0x02023530; room at +0x5F8, width/height at +0xBC/+0xBE,
  loaded collision slot at +0x65E.
- `gKirbys[0]`: 0x02020EE0; respawn room at +0x106, signed tile x/y at +0x108/+0x10A.
- Collision grid: 0x02024ED0 + slot * 1950, row stride roomWidth / 16.
  The Candy state uses slot 2. Inspect the grid's bounds and doors, not just
  the previous-room field or state filename.
- The chest at 0x03003CC0 has its ObjectTemplate pointer at +0xB0, reward at
  +0xE0, native room at +0x60, and fixed-point x/y at +0x40/+0x44.

These layouts and collision lookup semantics are in pinned
[data.h](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/include/data.h),
[kirby.h](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/include/kirby.h),
[level.c](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/level.c), and
[collision lookup](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/code_080023A4.c).

## Music Sheet #6 remains deliberately deferred

Music Sheet #6 (location 3960519, item 3860219) has verified source 0x008D3E64,
native room 734, and canonical manifest parent `REGION_CARROT_CASTLE/ROOM_5_13`.
It remains native/dormant and excluded from the AP source table and pool.

The physical compartment is now known: the USA state `5 - Carrot Castle/5 - 9
Small Chest Music Sheet.State` (SHA-256
`bd0a342e7b79bf6740ad442862cae508ecafc5a98c3acbf4c08a94268a076016`)
places reward 46 at (128, 120) in the upper section of a 256 x 368 room,
with spawn (14, 5). The lower section contains the ordinary 1-UP at (72, 264).
The collision grid has an unbroken solid boundary at rows 9..10 between them.

- [AMR Car10_Car9](https://github.com/HeyImTG/Amazing-Mirror-Randomizer/blob/2ea1c963535405e1ba7d678bb4361a7f5c30703b/JSON/mirrors.json#L3994-L4001)
  enters the music section from native 720 at (14, 5), exactly matching the USA state.
- [AMR Car8W_Car9 and reverse](https://github.com/HeyImTG/Amazing-Mirror-Randomizer/blob/2ea1c963535405e1ba7d678bb4361a7f5c30703b/JSON/mirrors.json#L3914-L3961)
  connect the lower section with native 719 at (13, 14). The USA manifest maps
  native 719 to doorsIdx 258 / AP 5-07, contradicting the existing 1-UP claim
  on `ENTRY_FROM_5_12`. That older claim is unchanged in this focused update.
- Historical Carrot AP topology labels disagree with current room-sanity
  identities. The [native pause-map records](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/pause_area_map.c#L1130-L1214)
  put 720 at (30, 8), 734 at (30, 14), and 732 at (7, 9); historical AP
  transition source coordinates instead attach these to 5-Chest 2, 5-10,
  and 5-13 respectively. The current split model has four entry compartments,
  while native room 734 contains two physically separated sections.

An object-editor list suggests native 720 is object-list slot 266, but that does
not prove its doorsIdx or AP region. Do not equate those fields or guess
`ENTRY_FROM_5_14`. Native [gRoomProps](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/data/data_8.s#L44013-L44014)
and the [door-pointer table](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/data/data_2.s#L863-L864)
remain ROM-only incbins in the pinned public decomp.

Resolution requires a lawful USA-ROM-backed extract of gRoomProps and door
records for native rooms 719, 720, 730, and 734, followed by reconciliation of
AP room IDs, inbound spawn coordinates, and the actual gameplay routes. Review
that topology correction separately; do not change progression edges merely to
make this item reachable. All 24 mailbox IDs remain supported in the meantime.

## Validation and release gate

The Candy-only compartment update passes 750 KirbyAM tests (the known local
socket-blocked hosting integration test is excluded), including real generation,
source-table/native-C contracts, mailbox delivery, pool counts, and both isolated
entry cases. ARM payload build, deterministic synthetic-image patch smoke,
APWorld packaging, the modified collection-test type check, and lint pass. The
committed base patch is unchanged; packaging is not a lawful-ROM rebuild.

Automated tests cover every item/source pair, stable IDs, one item per pool,
standard mailbox writes, exact physical checks, native grant interception,
unknown IDs/indices, unrelated ownership bits, duplicate delivery, and preservation
of the Sound Player bit. ARM compilation validates the full payload and bridge.
Dummy-ROM patch smoke tests prove patch wiring only, never game behavior.

Before releasing:
1. Rebuild the base patch using the supported, lawfully supplied USA ROM. The
   previously committed base patch does not contain this source change.
2. In BizHawk, open one Spray Paint and one Music Sheet chest. Confirm exactly one
   AP check, original visuals, and no native collection unlock before AP receipt.
3. Receive each item locally and remotely; inspect collection menus, receive a
   duplicate, and verify Sound Player remains independently locked/unlocked.
4. Test item-first then chest-first order, reconnect, and ordinary native save/load.
   Grants follow the native in-memory ownership semantics; no speculative direct
   SRAM write is added, so immediate power-loss durability is not claimed.
