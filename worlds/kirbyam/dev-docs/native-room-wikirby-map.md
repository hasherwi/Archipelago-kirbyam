# Native room IDs and WiKirby rooms (USA)

This is a complete **native table-slot inventory**, with an explicit mapping or
exception for every slot. All 263 main-area room titles and URLs were verified
against WiKirby's category listings. Native 969 is an internal Boss Endurance holding room without a separately
verified wiki target; that row deliberately has no guessed link. Completeness
refers to native inventory coverage, not one individual wiki page per record.
No gameplay, region logic, locations, ROM patch or item pool changes accompany it.

## Coverage and identifiers

| Inventory | Count |
| --- | ---: |
| Native table slots, IDs 0–982 inclusive | 983 |
| Populated native records | 286 |
| Unpopulated sentinel slots, in 58 inclusive ranges | 697 |
| Populated records with a physical AP RoomSanity check | 263 |
| Other populated records | 23 |
| Top-level AP room keys accounted for | 322 |
| Generated logical subregion aliases accounted for | 20 |
| Total AP keys in the table | 342 |
| Additional logical compartment keys sharing physical records | 55 |
| Tutorial keys without RoomSanity checks | 3 |

Native ID means the index into `gRoomProps`, not a WiKirby room number, an AP
location ID, an object-list index, or a completion bit. In the pinned USA ROM,
the 286 populated records use each completion index 0–286 except **4** exactly
once. The table has no populated record for index 4. Native **806** (`0x326`)
is a sentinel even though the decompilation's Dimension Mirror world-map list
mentions it; a map-list entry alone does not establish a loadable room.

The 55 top-level AP compartments and 20 generated logical subregions are aliases for purposes of this lookup, not additional
native rooms. The table retains every full AP key, including the `parent__LOGIC__key` names
constructed by [data.py](../data.py) from nested `logical_subregions`. For example, Rainbow Route
Room 3's upper/lower logic keys both resolve to native 107 and completion 25.
This does not mean those compartments are mutually traversable.

## Sources and method

1. [Pinned decompilation table extent](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/data/data_8.s#L44013)
   gives ROM file offset `0x9331AC`, byte size `0x9998`.
   [RoomProps layout](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/include/data.h#L447)
   gives stride `0x28`, object-list index at `+0x20`, and `doorsIdx` at `+0x24`.
   Thus `0x9998 / 0x28 = 983` slots, independently of the AP room list.
2. Read a privately held, unmodified 16 MiB USA ROM with SHA-1
   `274b102b6d940f46861a92b4e65f89a51815c12c`. Every sentinel record has nineteen
   `0xFFFF` halfwords followed by zero. Every other slot was decoded successfully
   with [extract_room_evidence.py](../tools/extract_room_evidence.py). No ROM
   bytes, graphics, saves or machine-specific paths are included here.
3. Join `doorsIdx` to the included `room_sanity.bit_index` in
   [rooms.json](../data/regions/rooms.json), including its nested `locations`
   form. This yields 263 physical AP rows. Normalize only the AP compartment
   suffix when associating keys with WiKirby's existing numbered/named rooms.
   Existing repository names supply the semantic correspondence; a page fetch
   establishes the title/URL, not independent visual confirmation of every room.
4. Verify WiKirby titles and URLs through retrieved pages and browser category
   listings on 2026-11-01. The browser resolved initial API/lookup failures.
   All 263 distinct titles and canonical hrefs match, including Rainbow Route's
   second category page. Category evidence:
   [Rainbow Route](https://wikirby.com/wiki/Category:Rooms_in_Rainbow_Route),
   [Moonlight Mansion](https://wikirby.com/wiki/Category:Rooms_in_Moonlight_Mansion),
   [Cabbage Cavern](https://wikirby.com/wiki/Category:Rooms_in_Cabbage_Cavern),
   [Mustard Mountain](https://wikirby.com/wiki/Category:Rooms_in_Mustard_Mountain),
   [Carrot Castle](https://wikirby.com/wiki/Category:Rooms_in_Carrot_Castle),
   [Olive Ocean](https://wikirby.com/wiki/Category:Rooms_in_Olive_Ocean),
   [Peppermint Palace](https://wikirby.com/wiki/Category:Rooms_in_Peppermint_Palace),
   [Radish Ruins](https://wikirby.com/wiki/Category:Rooms_in_Radish_Ruins),
   [Candy Constellation](https://wikirby.com/wiki/Category:Rooms_in_Candy_Constellation).
5. Special-room interpretation uses the pinned source's
   [tutorial/world-map lists](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/pause_world_map.c#L185),
   native object-list types and
   [object constants](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/include/constants/object_types.h).
   Native 909 contains Dark Meta Knight; 910/912/914/916 contain Dark Mind form 1;
   918 contains form 2; 919 contains the form-3 trigger. The intervening rooms
   and order correspond to the shared
   [Dimension Mirror level article](https://wikirby.com/wiki/Dimension_Mirror_(level)).
   Its nine-area list does not count the final chase as an additional numbered
   room page. Tutorial 803–805 corresponds to the three rooms described together
   in [Labyrinth Entrance Stage](https://wikirby.com/wiki/Labyrinth_Entrance_Stage).

`page` means the individual target page was retrieved (163 rows); `category`
means the exact title and URL were verified through the area category (100 rows).
`shared` means a verified article describes multiple native rooms or a general
mode (22 rows). `internal` identifies the source-backed nonparticipant holding room
(1 row); no individual wiki counterpart has been verified. No populated room
identity remains unresolved in this inventory. Category verification is not a visual audit of every room's terrain.

### Special rooms: shared targets and internal holding room

The initial seven missing correspondences were research gaps, not evidence of
seven rooms without wiki coverage. Six now have shared article targets; the seventh is an internal holding room.
None of these seven is an unpopulated slot.

| Native IDs | Count | Classification and evidence |
| --- | ---: | --- |
| 950 | 1 | Boss Endurance starting ability chamber: statues plus Boss Challenge Door; the shared article describes the starting Copy Ability Room. |
| 951 | 1 | Boss Endurance rest chamber: random ability statues plus Boss Challenge Door; boss-clear code returns to 951. |
| 955, 956, 957 | 3 | Boss Endurance encounter rooms: Mr. Frosty, Batafire and Waddle Dee starts respectively; all three appear in the Boss Challenge Door destination table. |
| 970 | 1 | Copy Ability Room: ability statues and return door to Central Circle (native 801); the shared article describes this connection and the Boss Endurance reuse. |
| 969 | 1 | Internal Boss Endurance holding room for nonparticipating Kirby slots. Verified initializer tables and assignments establish its role. No separately verified wiki room target. |

The verified [Boss Endurance](https://wikirby.com/wiki/Boss_Endurance) article's
Amazing Mirror section covers the initial chamber, rest chamber and the three
mid-boss groups. Its group numbers are encounter labels, not native room IDs.
The [Copy Ability Room](https://wikirby.com/wiki/Copy_Ability_Room) article covers
the Central Circle connection and reuse as the starting area of Boss Endurance.
These are shared targets, not fabricated individual room-page URLs.

Native evidence beyond the object lists:
[Boss Challenge Door dispatch](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/boss_challenge_door.c#L125)
indexes `gUnk_08357B24`; its
[table extent](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/data/data_13.s#L9)
is 13 halfwords at ROM offset `0x357B24`. Decoding it in the verified USA ROM
includes native IDs 957, 956 and 955.
[Object destruction](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/object.c#L333)
handles the 955–957 range and returns to 951;
[boss-clear handling](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/code_0806F780.c#L9419)
also returns to 951 in that mode. This supports played mode rooms, not unused
slots. The native-to-wiki semantic join is an inference from this evidence;
WiKirby does not itself publish these native IDs.

Native 969 is not an ordinary adventure entrance or an unused slot; see the
initializer investigation below. Its missing individual wiki URL is an explicit
internal-room exception, not an unresolved native identity.

The three native Goal Game variants 980–982 share a
[general article](https://wikirby.com/wiki/Goal_Game), and are distinct from
the **16 goal entrance rooms** in the nine main areas. Neither the three
minigame variants nor their score tiers should replace those 16 entrances when
counting potential checks.

## Investigations: native 806 and 969

### Native 806: sentinel slot with a residual map-coordinate entry

This is not a decimal/hex mix-up: `0x326` is decimal 806. The pinned decompilation
[README](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/README.md)
targets the same USA SHA-1 used here; no cross-region comparison supports a
version-difference explanation. At `0x9331AC + 806 * 0x28 = 0x93AF9C`, the room
record is the exact sentinel. The independent per-room descriptor pointer at
`0xD6CD0C + 806 * 4` is null. Neighboring tutorial records 803–805 are populated.
This corroborates the table offset and distinguishes an unused slot from a
populated room whose purpose is unknown.

The source's [coordinate lookup](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/pause_world_map.c#L859)
uses the Dimension Mirror list to position Kirby's map icon; it is not a room
loader or an entrance list. The 806 entry has zero coordinates for every player.
The source search found no room-loading reference to 806; other `0x326` hits in
`ufo.c` are sprite animation IDs, not room IDs. The decoded tile-transition and
completion tables contain no inbound destination 806. Object/script-driven
transitions are not exhaustively proved absent by that decoder.

Conclusion: an unpopulated USA slot with a residual map-coordinate entry. A
stale/reserved entry is plausible, but its development history is unproved.
There is no evidence of a missing playable RoomSanity location or an AP gameplay
bug, and no justification to load this sentinel as a room.

### Native 969: Boss Endurance nonparticipant holding room

Native 969 is different: its record at `0x93C914` is populated and uses map,
solidity, object-list and completion index 285. Its descriptor pointer is valid
(`0x08B57F24`) and the area field is 10 (Dimension Mirror). Its foreground
metadata is at `0x9C2854`, and its solidity header is at `0x8B49C0`.
The existing [trace decoder](../tools/trace_hub_objects.py) reads a 16 by 13 grid
of 16-pixel collision cells: nine rows of attribute 0 followed by four rows of
attribute 13 (flags `0x200`). The object list, completion list and solidity
transition-record list are empty. This is a small 256 by 208 geometry, not a
copy of native 970's 29 by 32 collision-cell chamber.

No decoded tile/completion transition targets 969, because the verified inbound
path is an initializer rather than a door. The related
[#1002 research](https://github.com/hasherwi/Archipelago-kirbyam/issues/1002#issuecomment-6553935841)
provided that lead; it was independently checked against the pinned source and
USA ROM:

- [Subgame selection, case 3](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/subgame_menu.c#L820)
  calls `sub_08025650(gNumHumanPlayers)` for Boss Endurance.
- [The initializer](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/asm/code_08025650.s#L40)
  selects room IDs from `gUnk_082DEB10` for participant slots and
  `gUnk_082DEB48` for the others. All four USA halfwords at `0x2DEB10` are 950;
  all four at `0x2DEB48` are 969. Its later loop also writes literal `0x3C9`
  to the nonparticipant state entries (literal at ROM `0x257A4`).
- [sub_080332BC](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/code_080332BC.c#L26)
  passes those IDs into `CreateKirby`, then initializes the nonhuman slots.

Thus 969 is an internal holding room used by mode setup, not a normal playable
room reached through a door. The earlier literal-only search missed the
zero-padded assembly literal and room-ID tables. This resolves the native
identity statically; it is not a new emulator acceptance claim. No separately
verified WiKirby room page describes that internal slot, so the mapping keeps
its URL null. No ROM graphics or binary assets are included.

## RoomSanity inclusion policy

Keep Boss Endurance rooms 950, 951 and 955–957 excluded. The story-mode Copy
Ability Room, native 970 (completion index 286), also remains excluded from
RoomSanity by owner decision. Its mapping and identity remain documented here;
it is distinct from Boss Endurance's starting variant, native 950. Native 969
is an internal Boss Endurance holding room and remains excluded; native 806 is
a sentinel.

The current catalog stays at **263 RoomSanity checks**. RoomSanity OFF has 116
current checks; ON has 379. With the separate proposed 16 Goal Game completion
checks, those totals would be **132 OFF / 395 ON**. No additional location ID is
allocated for room 970. The unpublished RoomSanity-addition follow-up is dropped.

The Copy Ability Room access item in [#1002](https://github.com/hasherwi/Archipelago-kirbyam/issues/1002)
is a separate feature; granting access does not imply adding a RoomSanity check.
This documentation PR implements neither that item nor Goal Game checks.

## Reproduce and validate

The companion [JSON](native-room-wikirby-map.json) is the reviewable mapping
source. From the repository root:

```sh
python worlds/kirbyam/tools/check_native_room_mapping.py
python worlds/kirbyam/tools/check_native_room_mapping.py --rom /private/path/to/usa.gba
python -m unittest discover -s worlds/kirbyam/tools/tests -p test_native_room_mapping.py -v
```

The offline check rejects missing/duplicate IDs, overlapping sentinel ranges,
missing/duplicate AP keys, incorrect completion joins and stale Markdown.
`--rom` also verifies the revision, each populated identity and every sentinel
slot; it never writes ROM contents. Use `--write` to refresh the generated table
after a reviewed JSON change. The validator does not contact WiKirby or convert
an unresolved annotation into verified evidence. Further research can resolve
any future ambiguous records using room-specific evidence; retain honest unknowns
if no equivalent exists.

<!-- native-room-table:start -->

| Native ID (decimal / hex) | Completion index | WiKirby target | Evidence / exceptions | AP keys |
| --- | --- | --- | --- | --- |
| 101 / `0x065` | 21 | [Rainbow Route - Room 1](https://wikirby.com/wiki/Rainbow_Route_-_Room_1) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_01` |
| 102 / `0x066` | 245 | [Radish Ruins - Room 22](https://wikirby.com/wiki/Radish_Ruins_-_Room_22) | **category**: Completion-index join; AP compartments share this native room | `REGION_RADISH_RUINS/ROOM_8_22` |
| 103 / `0x067` | 22 | [Rainbow Route - Room 5](https://wikirby.com/wiki/Rainbow_Route_-_Room_5) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_05` |
| 104 / `0x068` | 23 | [Rainbow Route - Room 4](https://wikirby.com/wiki/Rainbow_Route_-_Room_4) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_04` |
| 106 / `0x06A` | 24 | [Rainbow Route - Room 2](https://wikirby.com/wiki/Rainbow_Route_-_Room_2) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_02` |
| 107 / `0x06B` | 25 | [Rainbow Route - Room 3](https://wikirby.com/wiki/Rainbow_Route_-_Room_3) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_03_UPPER`<br>`REGION_RAINBOW_ROUTE/ROOM_1_03_LOWER` |
| 108 / `0x06C` | 26 | [Rainbow Route - Room 6](https://wikirby.com/wiki/Rainbow_Route_-_Room_6) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_06_UPPER`<br>`REGION_RAINBOW_ROUTE/ROOM_1_06_LOWER_RIGHT`<br>`REGION_RAINBOW_ROUTE/ROOM_1_06_LOWER_MID`<br>`REGION_RAINBOW_ROUTE/ROOM_1_06_LOWER_CHEST` |
| 110 / `0x06E` | 27 | [Rainbow Route - Room 8](https://wikirby.com/wiki/Rainbow_Route_-_Room_8) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_08` |
| 113 / `0x071` | 246 | [Radish Ruins - Room 21](https://wikirby.com/wiki/Radish_Ruins_-_Room_21) | **category**: Completion-index join; AP compartments share this native room | `REGION_RADISH_RUINS/ROOM_8_21` |
| 114 / `0x072` | 247 | [Radish Ruins - Room 23](https://wikirby.com/wiki/Radish_Ruins_-_Room_23) | **category**: Completion-index join; AP compartments share this native room | `REGION_RADISH_RUINS/ROOM_8_23` |
| 115 / `0x073` | 45 | [Rainbow Route - Room 25](https://wikirby.com/wiki/Rainbow_Route_-_Room_25) | **category**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_25` |
| 117 / `0x075` | 46 | [Rainbow Route - Room 24](https://wikirby.com/wiki/Rainbow_Route_-_Room_24) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_24`<br>`REGION_RAINBOW_ROUTE/ROOM_1_24_UPPER` |
| 118 / `0x076` | 47 | [Rainbow Route - Room 23](https://wikirby.com/wiki/Rainbow_Route_-_Room_23) | **category**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_23` |
| 119 / `0x077` | 48 | [Rainbow Route - Room 22](https://wikirby.com/wiki/Rainbow_Route_-_Room_22) | **category**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_22` |
| 120 / `0x078` | 249 | [Carrot Castle - Room 2](https://wikirby.com/wiki/Carrot_Castle_-_Room_2) | **page**: Completion-index join; AP compartments share this native room | `REGION_CARROT_CASTLE/ROOM_5_02` |
| 121 / `0x079` | 250 | [Carrot Castle - Room 3](https://wikirby.com/wiki/Carrot_Castle_-_Room_3) | **category**: Completion-index join; AP compartments share this native room | `REGION_CARROT_CASTLE/ROOM_5_03` |
| 122 / `0x07A` | 251 | [Carrot Castle - Room 1](https://wikirby.com/wiki/Carrot_Castle_-_Room_1) | **page**: Completion-index join; AP compartments share this native room | `REGION_CARROT_CASTLE/ROOM_5_01` |
| 126 / `0x07E` | 44 | [Rainbow Route - Room 32](https://wikirby.com/wiki/Rainbow_Route_-_Room_32) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_32` |
| 127 / `0x07F` | 33 | [Rainbow Route - Room 15](https://wikirby.com/wiki/Rainbow_Route_-_Room_15) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_15`<br>`REGION_RAINBOW_ROUTE/ROOM_1_15_LOWER` |
| 129 / `0x081` | 248 | [Radish Ruins - Boss](https://wikirby.com/wiki/Radish_Ruins_-_Boss) | **page**: Completion-index join; AP compartments share this native room | `REGION_RADISH_RUINS/ROOM_8_BOSS` |
| 130 / `0x082` | 190 | [Olive Ocean - Room 1](https://wikirby.com/wiki/Olive_Ocean_-_Room_1) | **page**: Completion-index join; AP compartments share this native room | `REGION_OLIVE_OCEAN/ROOM_6_01` |
| 131 / `0x083` | 191 | [Olive Ocean - Room 2](https://wikirby.com/wiki/Olive_Ocean_-_Room_2) | **category**: Completion-index join; AP compartments share this native room | `REGION_OLIVE_OCEAN/ROOM_6_02` |
| 132 / `0x084` | 192 | [Olive Ocean - Room 4](https://wikirby.com/wiki/Olive_Ocean_-_Room_4) | **category**: Completion-index join; AP compartments share this native room | `REGION_OLIVE_OCEAN/ROOM_6_04` |
| 133 / `0x085` | 193 | [Olive Ocean - Room 5](https://wikirby.com/wiki/Olive_Ocean_-_Room_5) | **category**: Completion-index join; AP compartments share this native room | `REGION_OLIVE_OCEAN/ROOM_6_05`<br>`REGION_OLIVE_OCEAN/ROOM_6_05_SUBROOM`<br>`REGION_OLIVE_OCEAN/ROOM_6_05__LOGIC__ENTRY_FROM_6_04_OR_6_06`<br>`REGION_OLIVE_OCEAN/ROOM_6_05__LOGIC__ENTRY_FROM_6_23`<br>`REGION_OLIVE_OCEAN/ROOM_6_05__LOGIC__ENTRY_FROM_6_07` |
| 134 / `0x086` | 194 | [Olive Ocean - Room 6](https://wikirby.com/wiki/Olive_Ocean_-_Room_6) | **page**: Completion-index join; AP compartments share this native room | `REGION_OLIVE_OCEAN/ROOM_6_06` |
| 135 / `0x087` | 195 | [Olive Ocean - Goal 1](https://wikirby.com/wiki/Olive_Ocean_-_Goal_1) | **category**: Completion-index join; AP compartments share this native room | `REGION_OLIVE_OCEAN/ROOM_6_GOAL_1` |
| 136 / `0x088` | 34 | [Rainbow Route - Room 31](https://wikirby.com/wiki/Rainbow_Route_-_Room_31) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_31` |
| 137 / `0x089` | 35 | [Rainbow Route - Room 14](https://wikirby.com/wiki/Rainbow_Route_-_Room_14) | **category**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_14` |
| 138 / `0x08A` | 49 | [Rainbow Route - Room 28](https://wikirby.com/wiki/Rainbow_Route_-_Room_28) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_28` |
| 139 / `0x08B` | 50 | [Rainbow Route - Room 26](https://wikirby.com/wiki/Rainbow_Route_-_Room_26) | **category**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_26`<br>`REGION_RAINBOW_ROUTE/ROOM_1_26_UPPER_RIGHT` |
| 140 / `0x08C` | 28 | [Rainbow Route - Room 7](https://wikirby.com/wiki/Rainbow_Route_-_Room_7) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_07` |
| 141 / `0x08D` | 29 | [Rainbow Route - Room 41](https://wikirby.com/wiki/Rainbow_Route_-_Room_41) | **category**: Completion-index join; lower, inner/upper-left, top-right Mustard and east Moonlight compartments share this native room. Incoming native144/545 retain their separate physical sides. | `REGION_RAINBOW_ROUTE/ROOM_1_41`<br>`REGION_RAINBOW_ROUTE/ROOM_1_41_UPPER`<br>`REGION_RAINBOW_ROUTE/ROOM_1_41__LOGIC__TOP_MUSTARD`<br>`REGION_RAINBOW_ROUTE/ROOM_1_41__LOGIC__EAST_MOONLIGHT` |
| 142 / `0x08E` | 30 | [Rainbow Route - Warp](https://wikirby.com/wiki/Rainbow_Route_-_Warp) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_WARP` |
| 143 / `0x08F` | 31 | [Rainbow Route - Room 42](https://wikirby.com/wiki/Rainbow_Route_-_Room_42) | **category**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_42`<br>`REGION_RAINBOW_ROUTE/ROOM_1_42_CUT` |
| 144 / `0x090` | 60 | [Moonlight Mansion - Room 16](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_16) | **page**: Completion-index join; AP compartments share this native room | `REGION_MOONLIGHT_MANSION/ROOM_2_16` |
| 145 / `0x091` | 61 | [Moonlight Mansion - Room 17](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_17) | **category**: Completion-index join; AP compartments share this native room | `REGION_MOONLIGHT_MANSION/ROOM_2_17` |
| 146 / `0x092` | 62 | [Moonlight Mansion - Room 18](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_18) | **page**: Completion-index join; AP compartments share this native room | `REGION_MOONLIGHT_MANSION/ROOM_2_18`<br>`REGION_MOONLIGHT_MANSION/ROOM_2_18_BOTTOM_RIGHT`<br>`REGION_MOONLIGHT_MANSION/ROOM_2_18_UPPER_LEFT` |
| 147 / `0x093` | 63 | [Moonlight Mansion - Room 19](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_19) | **category**: Completion-index join; AP compartments share this native room | `REGION_MOONLIGHT_MANSION/ROOM_2_19` |
| 148 / `0x094` | 64 | [Moonlight Mansion - Goal 2](https://wikirby.com/wiki/Moonlight_Mansion_-_Goal_2) | **page**: Completion-index join; AP compartments share this native room | `REGION_MOONLIGHT_MANSION/ROOM_2_GOAL_2`<br>`REGION_MOONLIGHT_MANSION/ROOM_2_GOAL_2_UPPER_LEFT`<br>`REGION_MOONLIGHT_MANSION/ROOM_2_GOAL_2_UPPER_RIGHT`<br>`REGION_MOONLIGHT_MANSION/ROOM_2_GOAL_2_BOTTOM_RIGHT` |
| 149 / `0x095` | 65 | [Moonlight Mansion - Room 20](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_20) | **category**: Completion-index join; AP compartments share this native room | `REGION_MOONLIGHT_MANSION/ROOM_2_20` |
| 170 / `0x0AA` | 252 | [Carrot Castle - Room 5](https://wikirby.com/wiki/Carrot_Castle_-_Room_5) | **category**: Completion-index join; AP compartments share this native room | `REGION_CARROT_CASTLE/ROOM_5_05`<br>`REGION_CARROT_CASTLE/ROOM_5_05__LOGIC__CHUTE_SIDE` |
| 171 / `0x0AB` | 51 | [Rainbow Route - Room 21](https://wikirby.com/wiki/Rainbow_Route_-_Room_21) | **category**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_21` |
| 172 / `0x0AC` | 52 | [Rainbow Route - Room 20](https://wikirby.com/wiki/Rainbow_Route_-_Room_20) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_20` |
| 173 / `0x0AD` | 53 | [Rainbow Route - Room 18](https://wikirby.com/wiki/Rainbow_Route_-_Room_18) | **category**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_18`<br>`REGION_RAINBOW_ROUTE/ROOM_1_18_UPPER` |
| 174 / `0x0AE` | 54 | [Rainbow Route - Room 17](https://wikirby.com/wiki/Rainbow_Route_-_Room_17) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_17` |
| 175 / `0x0AF` | 55 | [Rainbow Route - Room 19](https://wikirby.com/wiki/Rainbow_Route_-_Room_19) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_19` |
| 176 / `0x0B0` | 56 | [Rainbow Route - Goal 2](https://wikirby.com/wiki/Rainbow_Route_-_Goal_2) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_GOAL_2` |
| 177 / `0x0B1` | 57 | [Rainbow Route - Goal 3](https://wikirby.com/wiki/Rainbow_Route_-_Goal_3) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_GOAL_3` |
| 178 / `0x0B2` | 58 | [Rainbow Route - Room 29](https://wikirby.com/wiki/Rainbow_Route_-_Room_29) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_29` |
| 180 / `0x0B4` | 8 | [Moonlight Mansion - Room 12](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_12) | **page**: Completion-index join; AP compartments share this native room | `REGION_MOONLIGHT_MANSION/ROOM_2_12_LEFT`<br>`REGION_MOONLIGHT_MANSION/ROOM_2_12_RIGHT` |
| 181 / `0x0B5` | 9 | [Carrot Castle - Room 6](https://wikirby.com/wiki/Carrot_Castle_-_Room_6) | **page**: Completion-index join; AP compartments share this native room | `REGION_CARROT_CASTLE/ROOM_5_06` |
| 190 / `0x0BE` | 32 | [Rainbow Route - Hub 1](https://wikirby.com/wiki/Rainbow_Route_-_Hub_1) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_HUB_1` |
| 191 / `0x0BF` | 189 | [Cabbage Cavern - Hub 1](https://wikirby.com/wiki/Cabbage_Cavern_-_Hub_1) | **page**: Completion-index join; AP compartments share this native room | `REGION_CABBAGE_CAVERN/ROOM_3_HUB_1` |
| 192 / `0x0C0` | 59 | [Rainbow Route - Hub 3](https://wikirby.com/wiki/Rainbow_Route_-_Hub_3) | **category**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_HUB_3` |
| 193 / `0x0C1` | 253 | [Carrot Castle - Hub](https://wikirby.com/wiki/Carrot_Castle_-_Hub) | **page**: Completion-index join; AP compartments share this native room | `REGION_CARROT_CASTLE/ROOM_5_HUB` |
| 194 / `0x0C2` | 36 | [Rainbow Route - Hub 2](https://wikirby.com/wiki/Rainbow_Route_-_Hub_2) | **category**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_HUB_2` |
| 195 / `0x0C3` | 66 | [Moonlight Mansion - Entry](https://wikirby.com/wiki/Moonlight_Mansion_-_Entry) | **page**: Completion-index join; AP compartments share this native room | `REGION_MOONLIGHT_MANSION/ROOM_2_ENTRY` |
| 200 / `0x0C8` | 85 | [Peppermint Palace - Room 24](https://wikirby.com/wiki/Peppermint_Palace_-_Room_24) | **category**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_24` |
| 202 / `0x0CA` | 86 | [Peppermint Palace - Room 2](https://wikirby.com/wiki/Peppermint_Palace_-_Room_2) | **category**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_02` |
| 203 / `0x0CB` | 87 | [Peppermint Palace - Room 11](https://wikirby.com/wiki/Peppermint_Palace_-_Room_11) | **page**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_11` |
| 204 / `0x0CC` | 88 | [Peppermint Palace - Room 12](https://wikirby.com/wiki/Peppermint_Palace_-_Room_12) | **category**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_12` |
| 205 / `0x0CD` | 89 | [Peppermint Palace - Room 7](https://wikirby.com/wiki/Peppermint_Palace_-_Room_7) | **page**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_07`<br>`REGION_PEPPERMINT_PALACE/ROOM_7_07__LOGIC__WATER_RETURN` |
| 206 / `0x0CE` | 90 | [Peppermint Palace - Room 8](https://wikirby.com/wiki/Peppermint_Palace_-_Room_8) | **page**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_08` |
| 208 / `0x0D0` | 91 | [Peppermint Palace - Room 3](https://wikirby.com/wiki/Peppermint_Palace_-_Room_3) | **page**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_03` |
| 209 / `0x0D1` | 92 | [Peppermint Palace - Chest](https://wikirby.com/wiki/Peppermint_Palace_-_Chest) | **page**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_CHEST`<br>`REGION_PEPPERMINT_PALACE/ROOM_7_CHEST__LOGIC__UPPER_ENTRY`<br>`REGION_PEPPERMINT_PALACE/ROOM_7_CHEST__LOGIC__LOWER_MAP`<br>`REGION_PEPPERMINT_PALACE/ROOM_7_CHEST__LOGIC__BOTTOM_MINOR` |
| 210 / `0x0D2` | 93 | [Peppermint Palace - Room 5](https://wikirby.com/wiki/Peppermint_Palace_-_Room_5) | **page**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_05`<br>`REGION_PEPPERMINT_PALACE/ROOM_7_05__LOGIC__SNOW_HALL` |
| 211 / `0x0D3` | 94 | [Peppermint Palace - Room 1](https://wikirby.com/wiki/Peppermint_Palace_-_Room_1) | **page**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_01` |
| 212 / `0x0D4` | 105 | [Peppermint Palace - Room 18](https://wikirby.com/wiki/Peppermint_Palace_-_Room_18) | **category**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_18` |
| 214 / `0x0D6` | 95 | [Peppermint Palace - Goal 1](https://wikirby.com/wiki/Peppermint_Palace_-_Goal_1) | **category**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_GOAL_1` |
| 215 / `0x0D7` | 106 | [Peppermint Palace - Room 17](https://wikirby.com/wiki/Peppermint_Palace_-_Room_17) | **category**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_17` |
| 216 / `0x0D8` | 107 | [Peppermint Palace - Room 19](https://wikirby.com/wiki/Peppermint_Palace_-_Room_19) | **page**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_19` |
| 217 / `0x0D9` | 108 | [Peppermint Palace - Room 20](https://wikirby.com/wiki/Peppermint_Palace_-_Room_20) | **page**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_20` |
| 218 / `0x0DA` | 109 | [Peppermint Palace - Room 23](https://wikirby.com/wiki/Peppermint_Palace_-_Room_23) | **category**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_23` |
| 219 / `0x0DB` | 110 | [Peppermint Palace - Boss](https://wikirby.com/wiki/Peppermint_Palace_-_Boss) | **page**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_BOSS` |
| 220 / `0x0DC` | 96 | [Peppermint Palace - Room 13](https://wikirby.com/wiki/Peppermint_Palace_-_Room_13) | **page**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_13` |
| 221 / `0x0DD` | 111 | [Peppermint Palace - Room 22](https://wikirby.com/wiki/Peppermint_Palace_-_Room_22) | **page**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_22` |
| 222 / `0x0DE` | 112 | [Peppermint Palace - Room 4](https://wikirby.com/wiki/Peppermint_Palace_-_Room_4) | **page**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_04` |
| 223 / `0x0DF` | 113 | [Peppermint Palace - Room 21](https://wikirby.com/wiki/Peppermint_Palace_-_Room_21) | **category**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_21` |
| 224 / `0x0E0` | 114 | [Peppermint Palace - Goal 2](https://wikirby.com/wiki/Peppermint_Palace_-_Goal_2) | **page**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_GOAL_2` |
| 225 / `0x0E1` | 115 | [Peppermint Palace - Room 15](https://wikirby.com/wiki/Peppermint_Palace_-_Room_15) | **category**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_15` |
| 226 / `0x0E2` | 97 | [Carrot Castle - Room 4](https://wikirby.com/wiki/Carrot_Castle_-_Room_4) | **category**: Completion-index join; AP compartments share this native room | `REGION_CARROT_CASTLE/ROOM_5_04` |
| 227 / `0x0E3` | 98 | [Peppermint Palace - Room 6](https://wikirby.com/wiki/Peppermint_Palace_-_Room_6) | **page**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_06`<br>`REGION_PEPPERMINT_PALACE/ROOM_7_06__LOGIC__HAPPY_NOTES_ENTRY` |
| 228 / `0x0E4` | 99 | [Peppermint Palace - Room 9](https://wikirby.com/wiki/Peppermint_Palace_-_Room_9) | **page**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_09` |
| 229 / `0x0E5` | 100 | [Peppermint Palace - Room 10](https://wikirby.com/wiki/Peppermint_Palace_-_Room_10) | **page**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_10` |
| 230 / `0x0E6` | 101 | [Peppermint Palace - Warp](https://wikirby.com/wiki/Peppermint_Palace_-_Warp) | **page**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_WARP` |
| 231 / `0x0E7` | 102 | [Peppermint Palace - Room 16](https://wikirby.com/wiki/Peppermint_Palace_-_Room_16) | **page**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_16` |
| 232 / `0x0E8` | 103 | [Peppermint Palace - Room 14](https://wikirby.com/wiki/Peppermint_Palace_-_Room_14) | **page**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_14` |
| 290 / `0x122` | 104 | [Peppermint Palace - Hub 1](https://wikirby.com/wiki/Peppermint_Palace_-_Hub_1) | **page**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_HUB_1` |
| 291 / `0x123` | 116 | [Peppermint Palace - Hub 2](https://wikirby.com/wiki/Peppermint_Palace_-_Hub_2) | **page**: Completion-index join; AP compartments share this native room | `REGION_PEPPERMINT_PALACE/ROOM_7_HUB_2` |
| 300 / `0x12C` | 125 | [Mustard Mountain - Room 14](https://wikirby.com/wiki/Mustard_Mountain_-_Room_14) | **category**: Completion-index join; AP compartments share this native room | `REGION_MUSTARD_MOUNTAIN/ROOM_4_14`<br>`REGION_MUSTARD_MOUNTAIN/ROOM_4_14__LOGIC__CANNON_LEFT` |
| 304 / `0x130` | 126 | [Mustard Mountain - Room 4](https://wikirby.com/wiki/Mustard_Mountain_-_Room_4) | **page**: Completion-index join; AP compartments share this native room | `REGION_MUSTARD_MOUNTAIN/ROOM_4_04` |
| 308 / `0x134` | 127 | [Mustard Mountain - Room 9](https://wikirby.com/wiki/Mustard_Mountain_-_Room_9) | **category**: Completion-index join; AP compartments share this native room | `REGION_MUSTARD_MOUNTAIN/ROOM_4_09` |
| 310 / `0x136` | 128 | [Mustard Mountain - Chest](https://wikirby.com/wiki/Mustard_Mountain_-_Chest) | **page**: Completion-index join; AP compartments share this native room | `REGION_MUSTARD_MOUNTAIN/ROOM_4_CHEST` |
| 312 / `0x138` | 129 | [Mustard Mountain - Room 18](https://wikirby.com/wiki/Mustard_Mountain_-_Room_18) | **category**: Completion-index join; AP compartments share this native room | `REGION_MUSTARD_MOUNTAIN/ROOM_4_18` |
| 313 / `0x139` | 130 | [Mustard Mountain - Room 19](https://wikirby.com/wiki/Mustard_Mountain_-_Room_19) | **category**: Completion-index join; AP compartments share this native room | `REGION_MUSTARD_MOUNTAIN/ROOM_4_19` |
| 315 / `0x13B` | 131 | [Mustard Mountain - Room 12](https://wikirby.com/wiki/Mustard_Mountain_-_Room_12) | **page**: Completion-index join; AP compartments share this native room | `REGION_MUSTARD_MOUNTAIN/ROOM_4_12` |
| 316 / `0x13C` | 132 | [Mustard Mountain - Room 10](https://wikirby.com/wiki/Mustard_Mountain_-_Room_10) | **category**: Completion-index join; AP compartments share this native room | `REGION_MUSTARD_MOUNTAIN/ROOM_4_10` |
| 317 / `0x13D` | 133 | [Mustard Mountain - Room 17](https://wikirby.com/wiki/Mustard_Mountain_-_Room_17) | **page**: Completion-index join; AP compartments share this native room | `REGION_MUSTARD_MOUNTAIN/ROOM_4_17`<br>`REGION_MUSTARD_MOUNTAIN/ROOM_4_17_LEFT` |
| 318 / `0x13E` | 134 | [Mustard Mountain - Warp](https://wikirby.com/wiki/Mustard_Mountain_-_Warp) | **category**: Completion-index join; AP compartments share this native room | `REGION_MUSTARD_MOUNTAIN/ROOM_4_WARP` |
| 321 / `0x141` | 135 | [Mustard Mountain - Room 5](https://wikirby.com/wiki/Mustard_Mountain_-_Room_5) | **page**: Completion-index join; AP compartments share this native room | `REGION_MUSTARD_MOUNTAIN/ROOM_4_05`<br>`REGION_MUSTARD_MOUNTAIN/ROOM_4_05__LOGIC__RIGHT_ENTRY` |
| 322 / `0x142` | 136 | [Mustard Mountain - Room 11](https://wikirby.com/wiki/Mustard_Mountain_-_Room_11) | **page**: Completion-index join; AP compartments share this native room | `REGION_MUSTARD_MOUNTAIN/ROOM_4_11` |
| 323 / `0x143` | 137 | [Mustard Mountain - Room 13](https://wikirby.com/wiki/Mustard_Mountain_-_Room_13) | **page**: Completion-index join; AP compartments share this native room | `REGION_MUSTARD_MOUNTAIN/ROOM_4_13`<br>`REGION_MUSTARD_MOUNTAIN/ROOM_4_13__LOGIC__CANNON_LEFT` |
| 324 / `0x144` | 138 | [Mustard Mountain - Boss](https://wikirby.com/wiki/Mustard_Mountain_-_Boss) | **page**: Completion-index join; AP compartments share this native room | `REGION_MUSTARD_MOUNTAIN/ROOM_4_BOSS` |
| 325 / `0x145` | 139 | [Mustard Mountain - Room 16](https://wikirby.com/wiki/Mustard_Mountain_-_Room_16) | **category**: Completion-index join; AP compartments share this native room | `REGION_MUSTARD_MOUNTAIN/ROOM_4_16` |
| 326 / `0x146` | 140 | [Mustard Mountain - Goal 2](https://wikirby.com/wiki/Mustard_Mountain_-_Goal_2) | **page**: Completion-index join; AP compartments share this native room | `REGION_MUSTARD_MOUNTAIN/ROOM_4_GOAL_2` |
| 390 / `0x186` | 141 | [Mustard Mountain - Hub](https://wikirby.com/wiki/Mustard_Mountain_-_Hub) | **page**: Completion-index join; AP compartments share this native room | `REGION_MUSTARD_MOUNTAIN/ROOM_4_HUB` |
| 400 / `0x190` | 142 | [Candy Constellation - Room 20](https://wikirby.com/wiki/Candy_Constellation_-_Room_20) | **page**: Completion-index join; AP compartments share this native room | `REGION_CANDY_CONSTELLATION/ROOM_9_20` |
| 401 / `0x191` | 143 | [Candy Constellation - Room 6](https://wikirby.com/wiki/Candy_Constellation_-_Room_6) | **page**: Completion-index join; AP compartments share this native room | `REGION_CANDY_CONSTELLATION/ROOM_9_06` |
| 402 / `0x192` | 144 | [Candy Constellation - Room 12](https://wikirby.com/wiki/Candy_Constellation_-_Room_12) | **page**: Completion-index join; AP compartments share this native room | `REGION_CANDY_CONSTELLATION/ROOM_9_12` |
| 403 / `0x193` | 145 | [Candy Constellation - Chest 2](https://wikirby.com/wiki/Candy_Constellation_-_Chest_2) | **category**: Completion-index join; AP compartments share this native room | `REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_2`<br>`REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_2__LOGIC__ENTRY_FROM_9_01`<br>`REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_2__LOGIC__ENTRY_FROM_9_09` |
| 404 / `0x194` | 146 | [Candy Constellation - Room 1](https://wikirby.com/wiki/Candy_Constellation_-_Room_1) | **page**: Completion-index join; AP compartments share this native room | `REGION_CANDY_CONSTELLATION/ROOM_9_01` |
| 405 / `0x195` | 147 | [Candy Constellation - Room 9](https://wikirby.com/wiki/Candy_Constellation_-_Room_9) | **page**: Completion-index join; AP compartments share this native room | `REGION_CANDY_CONSTELLATION/ROOM_9_09` |
| 406 / `0x196` | 148 | [Candy Constellation - Chest 1](https://wikirby.com/wiki/Candy_Constellation_-_Chest_1) | **page**: Completion-index join; AP compartments share this native room | `REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_1` |
| 407 / `0x197` | 149 | [Candy Constellation - Room 7](https://wikirby.com/wiki/Candy_Constellation_-_Room_7) | **category**: Completion-index join; AP compartments share this native room | `REGION_CANDY_CONSTELLATION/ROOM_9_07` |
| 408 / `0x198` | 150 | [Candy Constellation - Room 5](https://wikirby.com/wiki/Candy_Constellation_-_Room_5) | **category**: Completion-index join; AP compartments share this native room | `REGION_CANDY_CONSTELLATION/ROOM_9_05` |
| 409 / `0x199` | 151 | [Candy Constellation - Room 4](https://wikirby.com/wiki/Candy_Constellation_-_Room_4) | **page**: Completion-index join; AP compartments share this native room | `REGION_CANDY_CONSTELLATION/ROOM_9_04` |
| 411 / `0x19B` | 152 | [Candy Constellation - Room 8](https://wikirby.com/wiki/Candy_Constellation_-_Room_8) | **category**: Completion-index join; AP compartments share this native room | `REGION_CANDY_CONSTELLATION/ROOM_9_08` |
| 412 / `0x19C` | 153 | [Candy Constellation - Warp](https://wikirby.com/wiki/Candy_Constellation_-_Warp) | **page**: Completion-index join; AP compartments share this native room | `REGION_CANDY_CONSTELLATION/ROOM_9_WARP` |
| 413 / `0x19D` | 154 | [Candy Constellation - Goal 1](https://wikirby.com/wiki/Candy_Constellation_-_Goal_1) | **page**: Completion-index join; AP compartments share this native room | `REGION_CANDY_CONSTELLATION/ROOM_9_GOAL_1` |
| 414 / `0x19E` | 155 | [Candy Constellation - Room 11](https://wikirby.com/wiki/Candy_Constellation_-_Room_11) | **category**: Completion-index join; AP compartments share this native room | `REGION_CANDY_CONSTELLATION/ROOM_9_11` |
| 415 / `0x19F` | 156 | [Candy Constellation - Room 14](https://wikirby.com/wiki/Candy_Constellation_-_Room_14) | **page**: Completion-index join; AP compartments share this native room | `REGION_CANDY_CONSTELLATION/ROOM_9_14` |
| 416 / `0x1A0` | 157 | [Candy Constellation - Room 19](https://wikirby.com/wiki/Candy_Constellation_-_Room_19) | **category**: Completion-index join; AP compartments share this native room | `REGION_CANDY_CONSTELLATION/ROOM_9_19` |
| 417 / `0x1A1` | 158 | [Candy Constellation - Boss](https://wikirby.com/wiki/Candy_Constellation_-_Boss) | **page**: Completion-index join; AP compartments share this native room | `REGION_CANDY_CONSTELLATION/ROOM_9_BOSS` |
| 418 / `0x1A2` | 159 | [Candy Constellation - Room 10](https://wikirby.com/wiki/Candy_Constellation_-_Room_10) | **page**: Completion-index join; AP compartments share this native room | `REGION_CANDY_CONSTELLATION/ROOM_9_10` |
| 419 / `0x1A3` | 160 | [Candy Constellation - Room 13](https://wikirby.com/wiki/Candy_Constellation_-_Room_13) | **page**: Completion-index join; AP compartments share this native room | `REGION_CANDY_CONSTELLATION/ROOM_9_13` |
| 420 / `0x1A4` | 161 | [Candy Constellation - Goal 2](https://wikirby.com/wiki/Candy_Constellation_-_Goal_2) | **category**: Completion-index join; AP compartments share this native room | `REGION_CANDY_CONSTELLATION/ROOM_9_GOAL_2` |
| 421 / `0x1A5` | 162 | [Candy Constellation - Room 18](https://wikirby.com/wiki/Candy_Constellation_-_Room_18) | **category**: Completion-index join; AP compartments share this native room | `REGION_CANDY_CONSTELLATION/ROOM_9_18` |
| 422 / `0x1A6` | 163 | [Candy Constellation - Room 15](https://wikirby.com/wiki/Candy_Constellation_-_Room_15) | **category**: Completion-index join; AP compartments share this native room | `REGION_CANDY_CONSTELLATION/ROOM_9_15` |
| 423 / `0x1A7` | 164 | [Candy Constellation - Room 17](https://wikirby.com/wiki/Candy_Constellation_-_Room_17) | **page**: Completion-index join; AP compartments share this native room | `REGION_CANDY_CONSTELLATION/ROOM_9_17` |
| 424 / `0x1A8` | 165 | [Candy Constellation - Room 16](https://wikirby.com/wiki/Candy_Constellation_-_Room_16) | **category**: Completion-index join; AP compartments share this native room | `REGION_CANDY_CONSTELLATION/ROOM_9_16` |
| 425 / `0x1A9` | 166 | [Candy Constellation - Room 3](https://wikirby.com/wiki/Candy_Constellation_-_Room_3) | **page**: Completion-index join; AP compartments share this native room | `REGION_CANDY_CONSTELLATION/ROOM_9_03` |
| 426 / `0x1AA` | 167 | [Candy Constellation - Chest 3](https://wikirby.com/wiki/Candy_Constellation_-_Chest_3) | **page**: Completion-index join; AP compartments share this native room | `REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_3` |
| 427 / `0x1AB` | 168 | [Candy Constellation - Room 2](https://wikirby.com/wiki/Candy_Constellation_-_Room_2) | **page**: Completion-index join; AP compartments share this native room | `REGION_CANDY_CONSTELLATION/ROOM_9_02` |
| 490 / `0x1EA` | 169 | [Candy Constellation - Hub](https://wikirby.com/wiki/Candy_Constellation_-_Hub) | **page**: Completion-index join; AP compartments share this native room | `REGION_CANDY_CONSTELLATION/ROOM_9_HUB` |
| 500 / `0x1F4` | 170 | [Cabbage Cavern - Room 16](https://wikirby.com/wiki/Cabbage_Cavern_-_Room_16) | **page**: Completion-index join; AP compartments share this native room | `REGION_CABBAGE_CAVERN/ROOM_3_16` |
| 501 / `0x1F5` | 176 | [Cabbage Cavern - Room 8](https://wikirby.com/wiki/Cabbage_Cavern_-_Room_8) | **page**: Completion-index join; AP compartments share this native room | `REGION_CABBAGE_CAVERN/ROOM_3_08`<br>`REGION_CABBAGE_CAVERN/ROOM_3_08_RIGHT` |
| 502 / `0x1F6` | 241 | [Radish Ruins - Room 16](https://wikirby.com/wiki/Radish_Ruins_-_Room_16) | **page**: Completion-index join; AP compartments share this native room | `REGION_RADISH_RUINS/ROOM_8_16` |
| 503 / `0x1F7` | 41 | [Rainbow Route - Room 12](https://wikirby.com/wiki/Rainbow_Route_-_Room_12) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_12` |
| 504 / `0x1F8` | 37 | [Rainbow Route - Room 16](https://wikirby.com/wiki/Rainbow_Route_-_Room_16) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_16`<br>`REGION_RAINBOW_ROUTE/ROOM_1_16_MID`<br>`REGION_RAINBOW_ROUTE/ROOM_1_16_UPPER` |
| 507 / `0x1FB` | 38 | [Rainbow Route - Room 13](https://wikirby.com/wiki/Rainbow_Route_-_Room_13) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_13`<br>`REGION_RAINBOW_ROUTE/ROOM_1_13_LOWER` |
| 508 / `0x1FC` | 171 | [Cabbage Cavern - Room 11](https://wikirby.com/wiki/Cabbage_Cavern_-_Room_11) | **page**: Completion-index join; AP compartments share this native room | `REGION_CABBAGE_CAVERN/ROOM_3_11` |
| 509 / `0x1FD` | 172 | [Cabbage Cavern - Room 10](https://wikirby.com/wiki/Cabbage_Cavern_-_Room_10) | **category**: Completion-index join; AP compartments share this native room | `REGION_CABBAGE_CAVERN/ROOM_3_10`<br>`REGION_CABBAGE_CAVERN/ROOM_3_10_LEFT`<br>`REGION_CABBAGE_CAVERN/ROOM_3_10_RIGHT`<br>`REGION_CABBAGE_CAVERN/ROOM_3_10_LOWER_RIGHT` |
| 510 / `0x1FE` | 173 | [Cabbage Cavern - Room 9](https://wikirby.com/wiki/Cabbage_Cavern_-_Room_9) | **category**: Completion-index join; AP compartments share this native room | `REGION_CABBAGE_CAVERN/ROOM_3_09` |
| 511 / `0x1FF` | 177 | [Cabbage Cavern - Room 5](https://wikirby.com/wiki/Cabbage_Cavern_-_Room_5) | **category**: Completion-index join; AP compartments share this native room | `REGION_CABBAGE_CAVERN/ROOM_3_05` |
| 512 / `0x200` | 178 | [Cabbage Cavern - Room 4](https://wikirby.com/wiki/Cabbage_Cavern_-_Room_4) | **category**: Completion-index join; AP compartments share this native room | `REGION_CABBAGE_CAVERN/ROOM_3_04`<br>`REGION_CABBAGE_CAVERN/ROOM_3_04_SUB` |
| 513 / `0x201` | 179 | [Cabbage Cavern - Room 13](https://wikirby.com/wiki/Cabbage_Cavern_-_Room_13) | **category**: Completion-index join; AP compartments share this native room | `REGION_CABBAGE_CAVERN/ROOM_3_13`<br>`REGION_CABBAGE_CAVERN/ROOM_3_13_LOWER` |
| 514 / `0x202` | 180 | [Cabbage Cavern - Room 7](https://wikirby.com/wiki/Cabbage_Cavern_-_Room_7) | **page**: Completion-index join; AP compartments share this native room | `REGION_CABBAGE_CAVERN/ROOM_3_07` |
| 515 / `0x203` | 181 | [Cabbage Cavern - Room 15](https://wikirby.com/wiki/Cabbage_Cavern_-_Room_15) | **page**: Completion-index join; AP compartments share this native room | `REGION_CABBAGE_CAVERN/ROOM_3_15`<br>`REGION_CABBAGE_CAVERN/ROOM_3_15_UPPER_ENTRY`<br>`REGION_CABBAGE_CAVERN/ROOM_3_15_LOWER_ENTRY`<br>`REGION_CABBAGE_CAVERN/ROOM_3_15__LOGIC__LOWER_CHEST`<br>`REGION_CABBAGE_CAVERN/ROOM_3_15__LOGIC__FROM_3_13` |
| 516 / `0x204` | 174 | [Cabbage Cavern - Boss](https://wikirby.com/wiki/Cabbage_Cavern_-_Boss) | **page**: Completion-index join; AP compartments share this native room | `REGION_CABBAGE_CAVERN/ROOM_3_BOSS` |
| 517 / `0x205` | 182 | [Cabbage Cavern - Room 6](https://wikirby.com/wiki/Cabbage_Cavern_-_Room_6) | **page**: Completion-index join; AP compartments share this native room | `REGION_CABBAGE_CAVERN/ROOM_3_06` |
| 523 / `0x20B` | 183 | [Cabbage Cavern - Room 1](https://wikirby.com/wiki/Cabbage_Cavern_-_Room_1) | **page**: Completion-index join; AP compartments share this native room | `REGION_CABBAGE_CAVERN/ROOM_3_01` |
| 524 / `0x20C` | 242 | [Radish Ruins - Room 15](https://wikirby.com/wiki/Radish_Ruins_-_Room_15) | **category**: Completion-index join; AP compartments share this native room | `REGION_RADISH_RUINS/ROOM_8_15` |
| 525 / `0x20D` | 243 | [Radish Ruins - Room 17](https://wikirby.com/wiki/Radish_Ruins_-_Room_17) | **category**: Completion-index join; AP compartments share this native room | `REGION_RADISH_RUINS/ROOM_8_17` |
| 526 / `0x20E` | 244 | [Radish Ruins - Goal 2](https://wikirby.com/wiki/Radish_Ruins_-_Goal_2) | **page**: Completion-index join; AP compartments share this native room | `REGION_RADISH_RUINS/ROOM_8_GOAL_2` |
| 527 / `0x20F` | 184 | [Cabbage Cavern - Room 14](https://wikirby.com/wiki/Cabbage_Cavern_-_Room_14) | **page**: Completion-index join; AP compartments share this native room | `REGION_CABBAGE_CAVERN/ROOM_3_14` |
| 528 / `0x210` | 175 | [Cabbage Cavern - Room 12](https://wikirby.com/wiki/Cabbage_Cavern_-_Room_12) | **page**: Completion-index join; AP compartments share this native room | `REGION_CABBAGE_CAVERN/ROOM_3_12`<br>`REGION_CABBAGE_CAVERN/ROOM_3_12_UPPER`<br>`REGION_CABBAGE_CAVERN/ROOM_3_12_LOWER` |
| 529 / `0x211` | 185 | [Cabbage Cavern - Room 3](https://wikirby.com/wiki/Cabbage_Cavern_-_Room_3) | **page**: Directed Normal Bomb routes join lower/right approaches; fresh upper-left entry is separate and returns only to512SUB. One physical RoomSanity check. | `REGION_CABBAGE_CAVERN/ROOM_3_03`<br>`REGION_CABBAGE_CAVERN/ROOM_3_03__LOGIC__UPPER_LEFT` |
| 530 / `0x212` | 186 | [Cabbage Cavern - Room 2](https://wikirby.com/wiki/Cabbage_Cavern_-_Room_2) | **page**: Completion-index join; AP compartments share this native room | `REGION_CABBAGE_CAVERN/ROOM_3_02` |
| 531 / `0x213` | 187 | [Cabbage Cavern - Goal](https://wikirby.com/wiki/Cabbage_Cavern_-_Goal) | **page**: Completion-index join; AP compartments share this native room | `REGION_CABBAGE_CAVERN/ROOM_3_GOAL` |
| 532 / `0x214` | 10 | [Rainbow Route - Room 27](https://wikirby.com/wiki/Rainbow_Route_-_Room_27) | **category**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_27`<br>`REGION_RAINBOW_ROUTE/ROOM_1_27_UPPER_LEFT`<br>`REGION_RAINBOW_ROUTE/ROOM_1_27_UPPER_RIGHT` |
| 533 / `0x215` | 117 | [Mustard Mountain - Room 15](https://wikirby.com/wiki/Mustard_Mountain_-_Room_15) | **page**: Completion-index join; AP compartments share this native room | `REGION_MUSTARD_MOUNTAIN/ROOM_4_15` |
| 534 / `0x216` | 11 | [Rainbow Route - Room 34](https://wikirby.com/wiki/Rainbow_Route_-_Room_34) | **category**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_34` |
| 535 / `0x217` | 12 | [Rainbow Route - Room 35](https://wikirby.com/wiki/Rainbow_Route_-_Room_35) | **category**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_35` |
| 536 / `0x218` | 13 | [Rainbow Route - Room 38](https://wikirby.com/wiki/Rainbow_Route_-_Room_38) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_38` |
| 537 / `0x219` | 14 | [Rainbow Route - Room 39](https://wikirby.com/wiki/Rainbow_Route_-_Room_39) | **category**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_39` |
| 538 / `0x21A` | 15 | [Rainbow Route - Room 36](https://wikirby.com/wiki/Rainbow_Route_-_Room_36) | **category**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_36_VERTICAL`<br>`REGION_RAINBOW_ROUTE/ROOM_1_36_HORIZONTAL` |
| 539 / `0x21B` | 118 | [Mustard Mountain - Room 1](https://wikirby.com/wiki/Mustard_Mountain_-_Room_1) | **page**: Completion-index join; AP compartments share this native room | `REGION_MUSTARD_MOUNTAIN/ROOM_4_01` |
| 540 / `0x21C` | 119 | [Mustard Mountain - Room 2](https://wikirby.com/wiki/Mustard_Mountain_-_Room_2) | **category**: Completion-index join; AP compartments share this native room | `REGION_MUSTARD_MOUNTAIN/ROOM_4_02` |
| 541 / `0x21D` | 120 | [Mustard Mountain - Room 3](https://wikirby.com/wiki/Mustard_Mountain_-_Room_3) | **category**: Completion-index join; AP compartments share this native room | `REGION_MUSTARD_MOUNTAIN/ROOM_4_03` |
| 542 / `0x21E` | 16 | [Rainbow Route - Room 37](https://wikirby.com/wiki/Rainbow_Route_-_Room_37) | **category**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_37` |
| 543 / `0x21F` | 17 | [Rainbow Route - Room 40](https://wikirby.com/wiki/Rainbow_Route_-_Room_40) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_40` |
| 544 / `0x220` | 121 | [Mustard Mountain - Room 6](https://wikirby.com/wiki/Mustard_Mountain_-_Room_6) | **category**: Completion-index join; AP compartments share this native room | `REGION_MUSTARD_MOUNTAIN/ROOM_4_06` |
| 545 / `0x221` | 122 | [Mustard Mountain - Room 7](https://wikirby.com/wiki/Mustard_Mountain_-_Room_7) | **page**: Completion-index join; AP compartments share this native room | `REGION_MUSTARD_MOUNTAIN/ROOM_4_07` |
| 546 / `0x222` | 123 | [Mustard Mountain - Room 8](https://wikirby.com/wiki/Mustard_Mountain_-_Room_8) | **category**: Completion-index join; AP compartments share this native room | `REGION_MUSTARD_MOUNTAIN/ROOM_4_08` |
| 547 / `0x223` | 124 | [Mustard Mountain - Goal 1](https://wikirby.com/wiki/Mustard_Mountain_-_Goal_1) | **page**: Completion-index join; AP compartments share this native room | `REGION_MUSTARD_MOUNTAIN/ROOM_4_GOAL_1` |
| 551 / `0x227` | 196 | [Olive Ocean - Room 15](https://wikirby.com/wiki/Olive_Ocean_-_Room_15) | **category**: Completion-index join; AP compartments share this native room | `REGION_OLIVE_OCEAN/ROOM_6_15` |
| 553 / `0x229` | 197 | [Olive Ocean - Room 16](https://wikirby.com/wiki/Olive_Ocean_-_Room_16) | **category**: Completion-index join; AP compartments share this native room | `REGION_OLIVE_OCEAN/ROOM_6_16` |
| 554 / `0x22A` | 39 | [Rainbow Route - Room 9](https://wikirby.com/wiki/Rainbow_Route_-_Room_9) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_09` |
| 555 / `0x22B` | 40 | [Rainbow Route - Room 10](https://wikirby.com/wiki/Rainbow_Route_-_Room_10) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_10` |
| 556 / `0x22C` | 42 | [Rainbow Route - Room 11](https://wikirby.com/wiki/Rainbow_Route_-_Room_11) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_11` |
| 557 / `0x22D` | 43 | [Rainbow Route - Goal 1](https://wikirby.com/wiki/Rainbow_Route_-_Goal_1) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_GOAL_1` |
| 570 / `0x23A` | 18 | [Rainbow Route - Room 33](https://wikirby.com/wiki/Rainbow_Route_-_Room_33) | **category**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_33`<br>`REGION_RAINBOW_ROUTE/ROOM_1_33_LEFT` |
| 571 / `0x23B` | 19 | [Rainbow Route - Room 30](https://wikirby.com/wiki/Rainbow_Route_-_Room_30) | **category**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_30` |
| 590 / `0x24E` | 20 | [Rainbow Route - Hub 4](https://wikirby.com/wiki/Rainbow_Route_-_Hub_4) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_HUB_4` |
| 591 / `0x24F` | 188 | [Cabbage Cavern - Hub 2](https://wikirby.com/wiki/Cabbage_Cavern_-_Hub_2) | **page**: Completion-index join; AP compartments share this native room | `REGION_CABBAGE_CAVERN/ROOM_3_HUB_2` |
| 592 / `0x250` | 219 | [Cabbage Cavern - Hub 3](https://wikirby.com/wiki/Cabbage_Cavern_-_Hub_3) | **category**: Completion-index join; AP compartments share this native room | `REGION_CABBAGE_CAVERN/ROOM_3_HUB_3` |
| 600 / `0x258` | 254 | [Carrot Castle - Room 12](https://wikirby.com/wiki/Carrot_Castle_-_Room_12) | **page**: Completion-index join; AP compartments share this native room | `REGION_CARROT_CASTLE/ROOM_5_12` |
| 601 / `0x259` | 220 | [Radish Ruins - Room 4](https://wikirby.com/wiki/Radish_Ruins_-_Room_4) | **page**: Completion-index join; AP compartments share this native room | `REGION_RADISH_RUINS/ROOM_8_04` |
| 603 / `0x25B` | 221 | [Radish Ruins - Room 6](https://wikirby.com/wiki/Radish_Ruins_-_Room_6) | **category**: Completion-index join; AP compartments share this native room | `REGION_RADISH_RUINS/ROOM_8_06` |
| 604 / `0x25C` | 222 | [Radish Ruins - Room 9](https://wikirby.com/wiki/Radish_Ruins_-_Room_9) | **category**: Completion-index join; AP compartments share this native room | `REGION_RADISH_RUINS/ROOM_8_09`<br>`REGION_RADISH_RUINS/ROOM_8_09__LOGIC__ENTRY_FROM_8_06`<br>`REGION_RADISH_RUINS/ROOM_8_09__LOGIC__ENTRY_FROM_8_08` |
| 605 / `0x25D` | 223 | [Radish Ruins - Room 3](https://wikirby.com/wiki/Radish_Ruins_-_Room_3) | **page**: Completion-index join; AP compartments share this native room | `REGION_RADISH_RUINS/ROOM_8_03` |
| 606 / `0x25E` | 224 | [Radish Ruins - Room 8](https://wikirby.com/wiki/Radish_Ruins_-_Room_8) | **page**: Completion-index join; AP compartments share this native room | `REGION_RADISH_RUINS/ROOM_8_08` |
| 608 / `0x260` | 231 | [Radish Ruins - Room 11](https://wikirby.com/wiki/Radish_Ruins_-_Room_11) | **category**: Completion-index join; AP compartments share this native room | `REGION_RADISH_RUINS/ROOM_8_11` |
| 609 / `0x261` | 232 | [Radish Ruins - Room 18](https://wikirby.com/wiki/Radish_Ruins_-_Room_18) | **category**: Completion-index join; AP compartments share this native room | `REGION_RADISH_RUINS/ROOM_8_18` |
| 610 / `0x262` | 225 | [Radish Ruins - Chest 1](https://wikirby.com/wiki/Radish_Ruins_-_Chest_1) | **page**: Completion-index join; AP compartments share this native room | `REGION_RADISH_RUINS/ROOM_8_CHEST_1` |
| 611 / `0x263` | 226 | [Radish Ruins - Room 5](https://wikirby.com/wiki/Radish_Ruins_-_Room_5) | **category**: Completion-index join; AP compartments share this native room | `REGION_RADISH_RUINS/ROOM_8_05` |
| 612 / `0x264` | 233 | [Radish Ruins - Room 10](https://wikirby.com/wiki/Radish_Ruins_-_Room_10) | **category**: Completion-index join; AP compartments share this native room | `REGION_RADISH_RUINS/ROOM_8_10` |
| 613 / `0x265` | 234 | [Radish Ruins - Room 13](https://wikirby.com/wiki/Radish_Ruins_-_Room_13) | **page**: Completion-index join; AP compartments share this native room | `REGION_RADISH_RUINS/ROOM_8_13` |
| 614 / `0x266` | 235 | [Radish Ruins - Room 19](https://wikirby.com/wiki/Radish_Ruins_-_Room_19) | **category**: Completion-index join; AP compartments share this native room | `REGION_RADISH_RUINS/ROOM_8_19` |
| 616 / `0x268` | 236 | [Radish Ruins - Room 14](https://wikirby.com/wiki/Radish_Ruins_-_Room_14) | **category**: Completion-index join; AP compartments share this native room | `REGION_RADISH_RUINS/ROOM_8_14` |
| 617 / `0x269` | 237 | [Radish Ruins - Chest 2](https://wikirby.com/wiki/Radish_Ruins_-_Chest_2) | **page**: Completion-index join; AP compartments share this native room | `REGION_RADISH_RUINS/ROOM_8_CHEST_2` |
| 618 / `0x26A` | 238 | [Radish Ruins - Room 20](https://wikirby.com/wiki/Radish_Ruins_-_Room_20) | **page**: Completion-index join; AP compartments share this native room | `REGION_RADISH_RUINS/ROOM_8_20` |
| 619 / `0x26B` | 239 | [Radish Ruins - Room 12](https://wikirby.com/wiki/Radish_Ruins_-_Room_12) | **page**: Completion-index join; AP compartments share this native room | `REGION_RADISH_RUINS/ROOM_8_12`<br>`REGION_RADISH_RUINS/ROOM_8_12__LOGIC__CARROT_SIDE` |
| 620 / `0x26C` | 227 | [Radish Ruins - Room 1](https://wikirby.com/wiki/Radish_Ruins_-_Room_1) | **page**: Completion-index join; AP compartments share this native room | `REGION_RADISH_RUINS/ROOM_8_01` |
| 621 / `0x26D` | 228 | [Radish Ruins - Room 2](https://wikirby.com/wiki/Radish_Ruins_-_Room_2) | **page**: Completion-index join; AP compartments share this native room; individual page rechecked 2026-11-09 (wikirby-room-crosscheck-followup.md) | `REGION_RADISH_RUINS/ROOM_8_02` |
| 622 / `0x26E` | 229 | [Radish Ruins - Goal 1](https://wikirby.com/wiki/Radish_Ruins_-_Goal_1) | **page**: Completion-index join; AP compartments share this native room | `REGION_RADISH_RUINS/ROOM_8_GOAL_1` |
| 623 / `0x26F` | 230 | [Radish Ruins - Room 7](https://wikirby.com/wiki/Radish_Ruins_-_Room_7) | **page**: Completion-index join; AP compartments share this native room | `REGION_RADISH_RUINS/ROOM_8_07`<br>`REGION_RADISH_RUINS/ROOM_8_07__LOGIC__ENTRY_FROM_8_04`<br>`REGION_RADISH_RUINS/ROOM_8_07__LOGIC__ENTRY_FROM_8_09` |
| 690 / `0x2B2` | 240 | [Radish Ruins - Hub](https://wikirby.com/wiki/Radish_Ruins_-_Hub) | **page**: Completion-index join; AP compartments share this native room | `REGION_RADISH_RUINS/ROOM_8_HUB` |
| 700 / `0x2BC` | 67 | [Moonlight Mansion - Room 10](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_10) | **page**: Completion-index join; AP compartments share this native room | `REGION_MOONLIGHT_MANSION/ROOM_2_10` |
| 702 / `0x2BE` | 81 | [Moonlight Mansion - Room 5](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_5) | **page**: Completion-index join; AP compartments share this native room | `REGION_MOONLIGHT_MANSION/ROOM_2_05`<br>`REGION_MOONLIGHT_MANSION/ROOM_2_05_UPPER_LEDGE`<br>`REGION_MOONLIGHT_MANSION/ROOM_2_05_LOWER` |
| 704 / `0x2C0` | 68 | [Moonlight Mansion - Room 8](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_8) | **page**: Completion-index join; AP compartments share this native room | `REGION_MOONLIGHT_MANSION/ROOM_2_08`<br>`REGION_MOONLIGHT_MANSION/ROOM_2_08_BOMB_ROOM` |
| 705 / `0x2C1` | 69 | [Moonlight Mansion - Warp](https://wikirby.com/wiki/Moonlight_Mansion_-_Warp) | **page**: Completion-index join; AP compartments share this native room | `REGION_MOONLIGHT_MANSION/ROOM_2_WARP` |
| 706 / `0x2C2` | 70 | [Moonlight Mansion - Room 3](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_3) | **page**: Completion-index join; AP compartments share this native room | `REGION_MOONLIGHT_MANSION/ROOM_2_03`<br>`REGION_MOONLIGHT_MANSION/ROOM_2_03_LOWER` |
| 707 / `0x2C3` | 71 | [Moonlight Mansion - Room 4](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_4) | **category**: Completion-index join; AP compartments share this native room | `REGION_MOONLIGHT_MANSION/ROOM_2_04`<br>`REGION_MOONLIGHT_MANSION/ROOM_2_04_PAST_SWITCH_WALL`<br>`REGION_MOONLIGHT_MANSION/ROOM_2_04_FROM_2_07` |
| 708 / `0x2C4` | 72 | [Moonlight Mansion - Room 1](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_1) | **page**: Completion-index join; AP compartments share this native room | `REGION_MOONLIGHT_MANSION/ROOM_2_01`<br>`REGION_MOONLIGHT_MANSION/ROOM_2_01_BOTTOM_LEFT`<br>`REGION_MOONLIGHT_MANSION/ROOM_2_01_BOTTOM_RIGHT`<br>`REGION_MOONLIGHT_MANSION/ROOM_2_01_PAST_METAL_BLOCKS`<br>`REGION_MOONLIGHT_MANSION/ROOM_2_01_UPPER_PLATFORM`<br>`REGION_MOONLIGHT_MANSION/ROOM_2_01__LOGIC__RIGHT_TOP` |
| 709 / `0x2C5` | 73 | [Moonlight Mansion - Room 7](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_7) | **page**: Completion-index join; AP compartments share this native room | `REGION_MOONLIGHT_MANSION/ROOM_2_07_UPPER_LEFT`<br>`REGION_MOONLIGHT_MANSION/ROOM_2_07_UPPER_RIGHT`<br>`REGION_MOONLIGHT_MANSION/ROOM_2_07_LOWER` |
| 710 / `0x2C6` | 74 | [Moonlight Mansion - Boss](https://wikirby.com/wiki/Moonlight_Mansion_-_Boss) | **page**: Completion-index join; AP compartments share this native room | `REGION_MOONLIGHT_MANSION/ROOM_2_BOSS` |
| 711 / `0x2C7` | 75 | [Moonlight Mansion - Room 9](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_9) | **page**: Completion-index join; AP compartments share this native room | `REGION_MOONLIGHT_MANSION/ROOM_2_09` |
| 712 / `0x2C8` | 76 | [Moonlight Mansion - Room 13](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_13) | **page**: Completion-index join; AP compartments share this native room | `REGION_MOONLIGHT_MANSION/ROOM_2_13` |
| 714 / `0x2CA` | 255 | [Carrot Castle - Room 8](https://wikirby.com/wiki/Carrot_Castle_-_Room_8) | **page**: Completion-index join; AP compartments share this native room | `REGION_CARROT_CASTLE/ROOM_5_08` |
| 716 / `0x2CC` | 256 | [Carrot Castle - Room 18](https://wikirby.com/wiki/Carrot_Castle_-_Room_18) | **page**: Completion-index join; AP compartments share this native room | `REGION_CARROT_CASTLE/ROOM_5_18` |
| 717 / `0x2CD` | 257 | [Carrot Castle - Room 17](https://wikirby.com/wiki/Carrot_Castle_-_Room_17) | **category**: Completion-index join; AP compartments share this native room | `REGION_CARROT_CASTLE/ROOM_5_17` |
| 719 / `0x2CF` | 258 | [Carrot Castle - Room 7](https://wikirby.com/wiki/Carrot_Castle_-_Room_7) | **category**: Completion-index join; AP compartments share this native room | `REGION_CARROT_CASTLE/ROOM_5_07` |
| 720 / `0x2D0` | 267 | [Carrot Castle - Room 14](https://wikirby.com/wiki/Carrot_Castle_-_Room_14) | **page**: Completion-index join; AP compartments share this native room | `REGION_CARROT_CASTLE/ROOM_5_14` |
| 730 / `0x2DA` | 268 | [Carrot Castle - Room 15](https://wikirby.com/wiki/Carrot_Castle_-_Room_15) | **page**: Completion-index join; AP compartments share this native room | `REGION_CARROT_CASTLE/ROOM_5_15` |
| 731 / `0x2DB` | 269 | [Carrot Castle - Warp](https://wikirby.com/wiki/Carrot_Castle_-_Warp) | **page**: Completion-index join; AP compartments share this native room | `REGION_CARROT_CASTLE/ROOM_5_WARP` |
| 732 / `0x2DC` | 259 | [Carrot Castle - Chest 2](https://wikirby.com/wiki/Carrot_Castle_-_Chest_2) | **page**: Completion-index join; AP compartments share this native room | `REGION_CARROT_CASTLE/ROOM_5_CHEST_2` |
| 733 / `0x2DD` | 260 | [Carrot Castle - Room 16](https://wikirby.com/wiki/Carrot_Castle_-_Room_16) | **page**: Completion-index join; AP compartments share this native room | `REGION_CARROT_CASTLE/ROOM_5_16` |
| 734 / `0x2DE` | 261 | [Carrot Castle - Room 13](https://wikirby.com/wiki/Carrot_Castle_-_Room_13) | **category**: Completion-index join; AP compartments share this native room | `REGION_CARROT_CASTLE/ROOM_5_13`<br>`REGION_CARROT_CASTLE/ROOM_5_13_UPPER`<br>`REGION_CARROT_CASTLE/ROOM_5_13__LOGIC__ENTRY_FROM_5_07`<br>`REGION_CARROT_CASTLE/ROOM_5_13__LOGIC__ENTRY_FROM_5_14`<br>`REGION_CARROT_CASTLE/ROOM_5_13__LOGIC__ENTRY_FROM_5_12`<br>`REGION_CARROT_CASTLE/ROOM_5_13__LOGIC__ENTRY_FROM_5_18_OR_5_WARP` |
| 735 / `0x2DF` | 262 | [Carrot Castle - Room 9](https://wikirby.com/wiki/Carrot_Castle_-_Room_9) | **page**: Completion-index join; AP compartments share this native room | `REGION_CARROT_CASTLE/ROOM_5_09` |
| 736 / `0x2E0` | 263 | [Carrot Castle - Room 10](https://wikirby.com/wiki/Carrot_Castle_-_Room_10) | **page**: Completion-index join; AP compartments share this native room | `REGION_CARROT_CASTLE/ROOM_5_10` |
| 737 / `0x2E1` | 264 | [Carrot Castle - Room 11](https://wikirby.com/wiki/Carrot_Castle_-_Room_11) | **page**: Completion-index join; AP compartments share this native room | `REGION_CARROT_CASTLE/ROOM_5_11` |
| 738 / `0x2E2` | 265 | [Carrot Castle - Boss](https://wikirby.com/wiki/Carrot_Castle_-_Boss) | **page**: Completion-index join; AP compartments share this native room | `REGION_CARROT_CASTLE/ROOM_5_BOSS` |
| 739 / `0x2E3` | 266 | [Carrot Castle - Chest 1](https://wikirby.com/wiki/Carrot_Castle_-_Chest_1) | **page**: Completion-index join; AP compartments share this native room | `REGION_CARROT_CASTLE/ROOM_5_CHEST_1` |
| 740 / `0x2E4` | 77 | [Moonlight Mansion - Room 2](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_2) | **page**: Completion-index join; AP compartments share this native room | `REGION_MOONLIGHT_MANSION/ROOM_2_02`<br>`REGION_MOONLIGHT_MANSION/ROOM_2_02_ENTRY`<br>`REGION_MOONLIGHT_MANSION/ROOM_2_02_RIGHT` |
| 741 / `0x2E5` | 78 | [Moonlight Mansion - Room 14](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_14) | **page**: Completion-index join; AP compartments share this native room | `REGION_MOONLIGHT_MANSION/ROOM_2_14`<br>`REGION_MOONLIGHT_MANSION/ROOM_2_14_UPPER` |
| 742 / `0x2E6` | 79 | [Moonlight Mansion - Room 15](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_15) | **category**: Completion-index join; AP compartments share this native room. Native 741 lower door enters canonical lower 742; its upper return door enters a distinct logical compartment with unknown prior outer-Bomb state. One generated room-check sink does not merge these arrivals. | `REGION_MOONLIGHT_MANSION/ROOM_2_15`<br>`REGION_MOONLIGHT_MANSION/ROOM_2_15__LOGIC__UPPER_RETURN` |
| 743 / `0x2E7` | 82 | [Moonlight Mansion - Room 11](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_11) | **page**: Completion-index join; AP compartments share this native room | `REGION_MOONLIGHT_MANSION/ROOM_2_11`<br>`REGION_MOONLIGHT_MANSION/ROOM_2_11_DEAD_END`<br>`REGION_MOONLIGHT_MANSION/ROOM_2_11_AFTER_LEVER` |
| 744 / `0x2E8` | 83 | [Moonlight Mansion - Room 6](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_6) | **page**: Completion-index join; AP compartments share this native room | `REGION_MOONLIGHT_MANSION/ROOM_2_06` |
| 745 / `0x2E9` | 84 | [Moonlight Mansion - Goal 1](https://wikirby.com/wiki/Moonlight_Mansion_-_Goal_1) | **category**: Completion-index join; AP compartments share this native room | `REGION_MOONLIGHT_MANSION/ROOM_2_GOAL_1` |
| 790 / `0x316` | 80 | [Moonlight Mansion - Hub](https://wikirby.com/wiki/Moonlight_Mansion_-_Hub) | **page**: Completion-index join; AP compartments share this native room | `REGION_MOONLIGHT_MANSION/ROOM_2_HUB` |
| 800 / `0x320` | 212 | [Olive Ocean - Room 23](https://wikirby.com/wiki/Olive_Ocean_-_Room_23) | **category**: Completion-index join; AP compartments share this native room | `REGION_OLIVE_OCEAN/ROOM_6_23` |
| 801 / `0x321` | 0 | [Rainbow Route - Central Circle](https://wikirby.com/wiki/Rainbow_Route_-_Central_Circle) | **page**: Completion-index join; AP compartments share this native room | `REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE`<br>`REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE_UPPER_PLATFORMS` |
| 802 / `0x322` | 213 | [Olive Ocean - Room 20](https://wikirby.com/wiki/Olive_Ocean_-_Room_20) | **page**: Completion-index join; AP compartments share this native room | `REGION_OLIVE_OCEAN/ROOM_6_20` |
| 803 / `0x323` | 1 | [Labyrinth Entrance Stage](https://wikirby.com/wiki/Labyrinth_Entrance_Stage) | **shared**: Tutorial room 1; shared article | `REGION_TUTORIAL/ROOM_0_01` |
| 804 / `0x324` | 2 | [Labyrinth Entrance Stage](https://wikirby.com/wiki/Labyrinth_Entrance_Stage) | **shared**: Tutorial room 2; shared article | `REGION_TUTORIAL/ROOM_0_02` |
| 805 / `0x325` | 3 | [Labyrinth Entrance Stage](https://wikirby.com/wiki/Labyrinth_Entrance_Stage) | **shared**: Tutorial room 3; shared article | `REGION_TUTORIAL/ROOM_0_03` |
| 810 / `0x32A` | 214 | [Olive Ocean - Room 19](https://wikirby.com/wiki/Olive_Ocean_-_Room_19) | **category**: Completion-index join; AP compartments share this native room | `REGION_OLIVE_OCEAN/ROOM_6_19` |
| 811 / `0x32B` | 198 | [Olive Ocean - Room 10](https://wikirby.com/wiki/Olive_Ocean_-_Room_10) | **category**: Completion-index join; AP compartments share this native room | `REGION_OLIVE_OCEAN/ROOM_6_10` |
| 814 / `0x32E` | 199 | [Olive Ocean - Room 12](https://wikirby.com/wiki/Olive_Ocean_-_Room_12) | **category**: Completion-index join; AP compartments share this native room | `REGION_OLIVE_OCEAN/ROOM_6_12`<br>`REGION_OLIVE_OCEAN/ROOM_6_12__LOGIC__UPPER_LEFT` |
| 815 / `0x32F` | 200 | [Olive Ocean - Chest 1](https://wikirby.com/wiki/Olive_Ocean_-_Chest_1) | **page**: Completion-index join; AP compartments share this native room | `REGION_OLIVE_OCEAN/ROOM_6_CHEST_1` |
| 816 / `0x330` | 215 | [Olive Ocean - Chest 2](https://wikirby.com/wiki/Olive_Ocean_-_Chest_2) | **page**: Completion-index join; AP compartments share this native room | `REGION_OLIVE_OCEAN/ROOM_6_CHEST_2` |
| 819 / `0x333` | 216 | [Olive Ocean - Room 21](https://wikirby.com/wiki/Olive_Ocean_-_Room_21) | **page**: Completion-index join; AP compartments share this native room; individual page rechecked 2026-11-09 (wikirby-room-crosscheck-followup.md) | `REGION_OLIVE_OCEAN/ROOM_6_21` |
| 821 / `0x335` | 217 | [Olive Ocean - Room 22](https://wikirby.com/wiki/Olive_Ocean_-_Room_22) | **page**: Completion-index join; AP compartments share this native room; individual page rechecked 2026-11-09 (wikirby-room-crosscheck-followup.md) | `REGION_OLIVE_OCEAN/ROOM_6_22` |
| 822 / `0x336` | 218 | [Olive Ocean - Boss](https://wikirby.com/wiki/Olive_Ocean_-_Boss) | **page**: Completion-index join; AP compartments share this native room | `REGION_OLIVE_OCEAN/ROOM_6_BOSS` |
| 823 / `0x337` | 201 | [Olive Ocean - Room 9](https://wikirby.com/wiki/Olive_Ocean_-_Room_9) | **category**: Completion-index join; AP compartments share this native room | `REGION_OLIVE_OCEAN/ROOM_6_09` |
| 824 / `0x338` | 202 | [Olive Ocean - Room 13](https://wikirby.com/wiki/Olive_Ocean_-_Room_13) | **category**: Completion-index join; AP compartments share this native room | `REGION_OLIVE_OCEAN/ROOM_6_13`<br>`REGION_OLIVE_OCEAN/ROOM_6_13__LOGIC__ENTRY_FROM_MOONLIGHT` |
| 825 / `0x339` | 203 | [Olive Ocean - Goal 2](https://wikirby.com/wiki/Olive_Ocean_-_Goal_2) | **page**: Completion-index join; AP compartments share this native room | `REGION_OLIVE_OCEAN/ROOM_6_GOAL_2` |
| 826 / `0x33A` | 204 | [Olive Ocean - Room 3](https://wikirby.com/wiki/Olive_Ocean_-_Room_3) | **category**: Completion-index join; AP compartments share this native room | `REGION_OLIVE_OCEAN/ROOM_6_03` |
| 827 / `0x33B` | 205 | [Olive Ocean - Room 7](https://wikirby.com/wiki/Olive_Ocean_-_Room_7) | **page**: Completion-index join; AP compartments share this native room | `REGION_OLIVE_OCEAN/ROOM_6_07` |
| 828 / `0x33C` | 206 | [Olive Ocean - Room 8](https://wikirby.com/wiki/Olive_Ocean_-_Room_8) | **category**: Completion-index join; AP compartments share this native room | `REGION_OLIVE_OCEAN/ROOM_6_08` |
| 829 / `0x33D` | 207 | [Olive Ocean - Room 11](https://wikirby.com/wiki/Olive_Ocean_-_Room_11) | **category**: Completion-index join; AP compartments share this native room | `REGION_OLIVE_OCEAN/ROOM_6_11` |
| 830 / `0x33E` | 208 | [Olive Ocean - Room 18](https://wikirby.com/wiki/Olive_Ocean_-_Room_18) | **page**: Completion-index join; AP compartments share this native room | `REGION_OLIVE_OCEAN/ROOM_6_18` |
| 831 / `0x33F` | 209 | [Olive Ocean - Room 14](https://wikirby.com/wiki/Olive_Ocean_-_Room_14) | **page**: Completion-index join; AP compartments share this native room | `REGION_OLIVE_OCEAN/ROOM_6_14` |
| 832 / `0x340` | 210 | [Olive Ocean - Room 17](https://wikirby.com/wiki/Olive_Ocean_-_Room_17) | **category**: Completion-index join; AP compartments share this native room | `REGION_OLIVE_OCEAN/ROOM_6_17` |
| 890 / `0x37A` | 211 | [Olive Ocean - Hub](https://wikirby.com/wiki/Olive_Ocean_-_Hub) | **category**: Completion-index join; AP compartments share this native room | `REGION_OLIVE_OCEAN/ROOM_6_HUB` |
| 909 / `0x38D` | 270 | [Dimension Mirror (level)](https://wikirby.com/wiki/Dimension_Mirror_(level)) | **shared**: Dark Meta Knight arena (area 1); shared level article, not a numbered room page | — |
| 910 / `0x38E` | 271 | [Dimension Mirror (level)](https://wikirby.com/wiki/Dimension_Mirror_(level)) | **shared**: Dark Mind first encounter (area 2); shared level article, not a numbered room page | — |
| 911 / `0x38F` | 272 | [Dimension Mirror (level)](https://wikirby.com/wiki/Dimension_Mirror_(level)) | **shared**: Intermediate puzzle room (area 3); shared level article, not a numbered room page | — |
| 912 / `0x390` | 273 | [Dimension Mirror (level)](https://wikirby.com/wiki/Dimension_Mirror_(level)) | **shared**: Dark Mind second encounter (area 4); shared level article, not a numbered room page | — |
| 913 / `0x391` | 274 | [Dimension Mirror (level)](https://wikirby.com/wiki/Dimension_Mirror_(level)) | **shared**: Intermediate puzzle room (area 5); shared level article, not a numbered room page | — |
| 914 / `0x392` | 275 | [Dimension Mirror (level)](https://wikirby.com/wiki/Dimension_Mirror_(level)) | **shared**: Dark Mind third encounter (area 6); shared level article, not a numbered room page | — |
| 915 / `0x393` | 276 | [Dimension Mirror (level)](https://wikirby.com/wiki/Dimension_Mirror_(level)) | **shared**: Intermediate puzzle room (area 7); shared level article, not a numbered room page | — |
| 916 / `0x394` | 277 | [Dimension Mirror (level)](https://wikirby.com/wiki/Dimension_Mirror_(level)) | **shared**: Dark Mind fourth encounter (area 8); shared level article, not a numbered room page | — |
| 918 / `0x396` | 278 | [Dimension Mirror (level)](https://wikirby.com/wiki/Dimension_Mirror_(level)) | **shared**: Dark Mind second form (area 9); shared level article, not a numbered room page | — |
| 919 / `0x397` | 279 | [Dimension Mirror (level)](https://wikirby.com/wiki/Dimension_Mirror_(level)) | **shared**: Dark Mind third-form chase; outside nine-room list; shared level article, not a numbered room page | — |
| 950 / `0x3B6` | 280 | [Boss Endurance](https://wikirby.com/wiki/Boss_Endurance) | **shared**: Boss Endurance starting ability chamber: ability statues and Boss Challenge Door; shared article, no invented numbered room page | — |
| 951 / `0x3B7` | 281 | [Boss Endurance](https://wikirby.com/wiki/Boss_Endurance) | **shared**: Boss Endurance rest chamber: random ability statues and Boss Challenge Door; boss-clear code returns to native 951 | — |
| 955 / `0x3BB` | 282 | [Boss Endurance](https://wikirby.com/wiki/Boss_Endurance) | **shared**: Boss Endurance Mid-Bosses 1 encounter: Mr. Frosty and object spawner; native 955 is an explicit Boss Challenge Door destination | — |
| 956 / `0x3BC` | 283 | [Boss Endurance](https://wikirby.com/wiki/Boss_Endurance) | **shared**: Boss Endurance Mid-Bosses 3 encounter: Batafire and object spawner; native 956 is an explicit Boss Challenge Door destination | — |
| 957 / `0x3BD` | 284 | [Boss Endurance](https://wikirby.com/wiki/Boss_Endurance) | **shared**: Boss Endurance Mid-Bosses 2 encounter: Waddle Dee and object spawner; native 957 is an explicit Boss Challenge Door destination | — |
| 969 / `0x3C9` | 285 | No established wiki equivalent | **internal**: Boss Endurance nonparticipant holding room: initializer assigns native 969 to nonhuman slots; no separately verified WiKirby room target, not an unused table slot | — |
| 970 / `0x3CA` | 286 | [Copy Ability Room](https://wikirby.com/wiki/Copy_Ability_Room) | **shared**: Copy Ability Room linked to Central Circle: ability statues and return transition to native 801; shared article, distinct from native 950 Boss Endurance variant | `REGION_COPY_ABILITY_ROOM/MAIN` |
| 980 / `0x3D4` | 5 | [Goal Game](https://wikirby.com/wiki/Goal_Game) | **shared**: Goal Game variant; shared general article, no individual room page established | — |
| 981 / `0x3D5` | 6 | [Goal Game](https://wikirby.com/wiki/Goal_Game) | **shared**: Goal Game variant; shared general article, no individual room page established | — |
| 982 / `0x3D6` | 7 | [Goal Game](https://wikirby.com/wiki/Goal_Game) | **shared**: Goal Game variant; shared general article, no individual room page established | — |

### Unpopulated native slots

Every inclusive range below consists solely of the verified sentinel record. There is no wiki room mapping; these are slots, not 697 playable rooms.

| Decimal range | Hex range | Count |
| --- | --- | --- |
| 0–100 | `0x000`–`0x064` | 101 |
| 105–105 | `0x069`–`0x069` | 1 |
| 109–109 | `0x06D`–`0x06D` | 1 |
| 111–112 | `0x06F`–`0x070` | 2 |
| 116–116 | `0x074`–`0x074` | 1 |
| 123–125 | `0x07B`–`0x07D` | 3 |
| 128–128 | `0x080`–`0x080` | 1 |
| 150–169 | `0x096`–`0x0A9` | 20 |
| 179–179 | `0x0B3`–`0x0B3` | 1 |
| 182–189 | `0x0B6`–`0x0BD` | 8 |
| 196–199 | `0x0C4`–`0x0C7` | 4 |
| 201–201 | `0x0C9`–`0x0C9` | 1 |
| 207–207 | `0x0CF`–`0x0CF` | 1 |
| 213–213 | `0x0D5`–`0x0D5` | 1 |
| 233–289 | `0x0E9`–`0x121` | 57 |
| 292–299 | `0x124`–`0x12B` | 8 |
| 301–303 | `0x12D`–`0x12F` | 3 |
| 305–307 | `0x131`–`0x133` | 3 |
| 309–309 | `0x135`–`0x135` | 1 |
| 311–311 | `0x137`–`0x137` | 1 |
| 314–314 | `0x13A`–`0x13A` | 1 |
| 319–320 | `0x13F`–`0x140` | 2 |
| 327–389 | `0x147`–`0x185` | 63 |
| 391–399 | `0x187`–`0x18F` | 9 |
| 410–410 | `0x19A`–`0x19A` | 1 |
| 428–489 | `0x1AC`–`0x1E9` | 62 |
| 491–499 | `0x1EB`–`0x1F3` | 9 |
| 505–506 | `0x1F9`–`0x1FA` | 2 |
| 518–522 | `0x206`–`0x20A` | 5 |
| 548–550 | `0x224`–`0x226` | 3 |
| 552–552 | `0x228`–`0x228` | 1 |
| 558–569 | `0x22E`–`0x239` | 12 |
| 572–589 | `0x23C`–`0x24D` | 18 |
| 593–599 | `0x251`–`0x257` | 7 |
| 602–602 | `0x25A`–`0x25A` | 1 |
| 607–607 | `0x25F`–`0x25F` | 1 |
| 615–615 | `0x267`–`0x267` | 1 |
| 624–689 | `0x270`–`0x2B1` | 66 |
| 691–699 | `0x2B3`–`0x2BB` | 9 |
| 701–701 | `0x2BD`–`0x2BD` | 1 |
| 703–703 | `0x2BF`–`0x2BF` | 1 |
| 713–713 | `0x2C9`–`0x2C9` | 1 |
| 715–715 | `0x2CB`–`0x2CB` | 1 |
| 718–718 | `0x2CE`–`0x2CE` | 1 |
| 721–729 | `0x2D1`–`0x2D9` | 9 |
| 746–789 | `0x2EA`–`0x315` | 44 |
| 791–799 | `0x317`–`0x31F` | 9 |
| 806–809 | `0x326`–`0x329` | 4 |
| 812–813 | `0x32C`–`0x32D` | 2 |
| 817–818 | `0x331`–`0x332` | 2 |
| 820–820 | `0x334`–`0x334` | 1 |
| 833–889 | `0x341`–`0x379` | 57 |
| 891–908 | `0x37B`–`0x38C` | 18 |
| 917–917 | `0x395`–`0x395` | 1 |
| 920–949 | `0x398`–`0x3B5` | 30 |
| 952–954 | `0x3B8`–`0x3BA` | 3 |
| 958–968 | `0x3BE`–`0x3C8` | 11 |
| 971–979 | `0x3CB`–`0x3D3` | 9 |

<!-- native-room-table:end -->
