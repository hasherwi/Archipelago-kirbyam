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

The 63 active sources are exact matches in the same AP-owned source table. The generic
chest hook records the source and preserves native chest flags. It marks only
ordinary rewards 0..5 for delayed popup suppression. New Spray Paint interception
uses the already-validated callsite 0xB1D0. Music Sheets use the existing 0xB264
Sound Player/Sheets wrapper. Unknown sources retain bounded native collection
behavior. Collection reward fields remain unchanged, preserving their popups.

Mailbox delivery uses the same tested C helpers as native-host contract tests.
All 24 item IDs can OR their ownership bit and ACK normally, but only the 22
items with active locations enter the generated pool. Replay is
idempotent and leaves unrelated bits untouched. A sheet never implicitly unlocks
Sound Player; delivering any collection item never consumes a physical check.
Existing one-shot chest persistence and all six ordinary consumable effects stay
unchanged. Cherry uses the existing Small Food item/effect.

The popup bridge preserves r1, r2, r3, and LR around its C call with a four-register
stack frame. It then replays `ldr r4, [r2, #0x4C]; adds r0, r4, #0`, including the
original flag effects. It no longer assumes caller-live scratch registers can be
clobbered or reconstructs r2 from a different register.

## Two sources deliberately deferred

- Spray Paint #6: location 3960505, item 3860205, exact source 0x008C5EA0,
  native room 403, `REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_2`.
- Music Sheet #6: location 3960519, item 3860219, exact source 0x008D3E64,
  native room 734, `REGION_CARROT_CASTLE/ROOM_5_13`.

These physical room parents have no reachable incoming edges: existing topology
routes every entrance into separate logical compartments. Assigning either chest
to its physical parent fails the real generation accessibility test. Assigning a
compartment by guess would introduce incorrect logic. Their historical rows remain
dormant, absent from the AP-owned source table and generated item pool. The native
grant wrappers preserve their rewards. All 24 mailbox IDs remain supported for
future activation; no existing transition or compartment logic changes here.

The checked-in states `9 - 8 Small Chest Spray Paint.State` and
`5 - 9 Small Chest Music Sheet.State` independently confirm the exact live source,
reward, and room, but do not prove which modeled compartment reaches the chest.
The former has chest reward 25 at pixel (144, 88), the latter reward 46 at
(128, 120). State history is insufficient: their neighboring collection snapshots
share the same prior native rooms. Resolve access with a lawful ROM-backed room
layout/door trace or a direct gameplay route before enabling these two checks.

## Validation and release gate

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
