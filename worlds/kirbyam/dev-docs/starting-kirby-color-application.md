# Starting Kirby Color application contract

## Root cause of Issue #852

The previous payload treated `0x02020FBF` as a deferred transition-color variable. The KATAM decomp identifies it as `gKirbys[0].color` (`struct Kirby` offset `0xDF`). Updating that byte changes Kirby's logical color but does not rebuild the OBJ palette already loaded in palette RAM. Native damage and room-transition paths eventually call `sub_0803E558`, which explains why the requested color appeared only after those events.

The other previous symbol, `0x0203ADE0`, is `gUnk_0203ADE0`, a signed 16-bit selected-color value used before single-player startup. It must not be written as an 8-bit active-palette field.

## Generation-time startup path

`rom.write_tokens()` writes the versioned color/mode configuration to payload ROM word `0x0815F694` (file offset `0x15F694`). Existing ability-gate and statue-pool words remain at `0x15F698` and `0x15F69C`.

`patch_rom.py` validates and redirects the two North American retail calls to `sub_080332BC` at file offsets `0x123EF2` and `0x124022`. Both are inside the single-player startup module `code_08123950.c`. The wrapper resolves the current per-room color, saved owned paint choice, AP static choice or Pink, then writes:

- `gUnk_0203ADE0` as `s16`;
- `gUnk_0203AD1C[0]`, the player-one color initialization entry;
- then calls the original `sub_080332BC` with all five arguments unchanged.

Because `CreateKirby` consumes that table during the original call, the first visible gameplay palette is generated from the resolved color.

## Runtime recovery path

The existing client mailbox at `0x0203B050` remains for reconnect, savestate, and compatibility recovery. Once player one and the normal gameplay HUD have valid IWRAM tasks and fades are finished, the payload keeps selected/table/live color state coherent. It calls native `sub_0803E558(0)` for OBJ and `sub_0803D21C(table + color*16, 0xF0, 16)` for the HUD palette and backup, then requests BG upload. Pink is a real runtime color.

The one-shot latch lives at `0x0203B0B8`. Payload code executes from ROM, so a writable C `static`/`.bss` variable is not a valid place for session state.

## Compatibility and safety

- Color IDs outside `0..13` are ignored.
- ROM default `0xFFFFFFFF` keeps older procedure patches safe.
- Pink is the fallback and a valid requested palette. Runtime Pink refresh is no longer skipped.
- The owned-paint A-button handler at `0x0814406C` records a genuine choice, including choosing a paint matching the AP default. Saved preference uses native treasure padding and the native serializer, not raw SRAM writes. See PROTOCOL.md for the marker and priority order.
- The patcher verifies both callsites still target `0x080332BC` before replacing them, refusing unknown ROM revisions.
- Demo and multiplayer calls to `sub_080332BC` are not patched.
