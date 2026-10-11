# Chest rewards and native save acceptance

The USA inventory has 84 chest objects: 65 small rewards, 15 major rewards
(10 maps including tutorial, four Vitality counters, one Sound Player), and four
lever objects. The small rewards comprise 41 consumables and 24 fixed collections
(14 paints and 10 sheets). There are no native battery or ability chest rewards;
those can still be AP placements. One sheet, Carrot Music Sheet 6, stays dormant.
The recovery map covers 79 physical reward checks, excluding that sheet and the
four item-owned lever bits.

## Save corruption fix and evidence

The old shard helper wrote candidate offsets 0x12/0x18/0x1A/0x1C. The pinned USA
save metadata proves these overlap save headers, not saved shard fields:

- FILE_INFO: four data bytes plus eight checksum bytes, two 12-byte records.
- WORLD_PROPS: 780 data bytes plus eight checksum bytes, six 788-byte records.
- Shard bytes: 0x30E/0x622, 0x936/0xC4A, 0xF5E/0x1272 for the three slots.

Native checksums sum all data halfwords and store sum/complement/negation/zero.
Independent synthetic valid-save fixtures demonstrated the old helper invalidates
backup FILE_INFO and slot-zero primary WORLD_PROPS without updating any shard byte.
This damages redundancy; it does not prove total save loss because fallback copies
can remain valid. The fix removes the helper and every caller, retaining EWRAM
shard grants, AP authority, boss transition state and mailbox ACK semantics.
It does not invoke a native saver from an unproven frame-hook context.

`test_shard_save_integrity.py` executes payload C on a host with mapped memory,
covering 256 prior masks × eight shard IDs through grant/replay/boss/scrub paths.
It checks all 32 KiB of SRAM remain unchanged. ARM registers and unrelated callbacks
are substituted. This is not a native serializer roundtrip or emulator test.

Source: pinned [save.c](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/save.c),
[chest.c](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/chest.c), and
[kirby.c](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/kirby.c).

## Native save timing

Chest opening calls CollectChest, dispatches the physical reward, and conditionally
saves the whole world before creating the delayed popup. Saving is guarded by game
mode, local-player ownership and selected save slot. A human-player door transition
also provides a guarded native save. The AP reward may arrive after the chest save;
its owned state then needs a later native save or authenticated history replay.
Immediate reset/power loss before that save is not guaranteed. Consumable effects
have no durable transaction journal across arbitrary process loss.

## Remaining runtime checks — all unrun

Use the rebuilt candidate, owner ROM and a fresh same-seed native save. Keep backups.

- Test each native save slot: receive a shard, trigger a native save, cold boot and
  inspect both record checksums and retained shard ownership. Compare unrelated slots.
- Open representative minor and major chests while disconnected; reconnect and verify
  exactly their physical checks recover. Never use lever ownership bits as fallback.
- Place remote non-health items at Vitality chests; verify no native heal/cap reset,
  then verify AP Vitality delivery, damage, death, save, reload and replay separately.
- Verify paints, sheets, maps and Sound Player in the native UI after receipt and after
  a later native save. Check 1UP, cherry, meat, drink, tomato and candy suppression and
  mailbox effects separately from durable ownership.
- For Music Sheet 6, record a continuous partner-isolated 719 → 720 → upper 734 route,
  switch timing, ability and timeout failures. Lower 734's 1UP is a different compartment.
  Do not enable the sheet until route and requirements are observed.

No usable emulator was found among the installed ARM64 tools during this audit.
The saved BizHawk core is x86-64; Docker daemon access was denied. No emulator was
installed and no new permission was requested. Host tests do not satisfy this checklist.
