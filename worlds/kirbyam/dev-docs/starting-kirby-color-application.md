# Starting Kirby Color application contract

## Root cause of Issue #852

The previous payload treated `0x02020FBF` as a deferred transition-color variable. The KATAM decomp identifies it as `gKirbys[0].color` (`struct Kirby` offset `0xDF`). Updating that byte changes Kirby's logical color but does not rebuild the OBJ palette already loaded in palette RAM. Native damage and room-transition paths eventually call `sub_0803E558`, which explains why the requested color appeared only after those events.

The other previous symbol, `0x0203ADE0`, is `gUnk_0203ADE0`, a signed 16-bit selected-color value used before single-player startup. It must not be written as an 8-bit active-palette field.

## Generation-time startup path

`rom.write_tokens()` writes the resolved color ID to payload ROM word `0x0815F694` (file offset `0x15F694`). Existing ability-gate and statue-pool words remain at `0x15F698` and `0x15F69C`.

`patch_rom.py` validates and redirects the two North American retail calls to `sub_080332BC` at file offsets `0x123EF2` and `0x124022`. Both are inside the single-player startup module `code_08123950.c`. The wrapper writes:

- `gUnk_0203ADE0` as `s16`;
- `gUnk_0203AD1C[0]`, the player-one color initialization entry;
- then calls the original `sub_080332BC` with all five arguments unchanged.

Because `CreateKirby` consumes that table during the original call, the first visible gameplay palette is generated from the configured color.

## Runtime recovery path

The existing client mailbox at `0x0203B050` remains for reconnect, savestate, and compatibility recovery. Once player one has a valid IWRAM task and a valid ability ID, the payload keeps selected/table/live color state coherent and calls native `sub_0803E558(0)` to rebuild and upload the OBJ palette immediately.

The one-shot latch lives at `0x0203B0B8`. Payload code executes from ROM, so a writable C `static`/`.bss` variable is not a valid place for session state.

## Compatibility and safety

- Color IDs outside `0..13` are ignored.
- ROM default `0xFFFFFFFF` keeps older procedure patches safe.
- Pink remains the default/no-runtime-refresh option, while the startup wrapper still writes Pink before `CreateKirby`.
- The patcher verifies both callsites still target `0x080332BC` before replacing them, refusing unknown ROM revisions.
- Demo and multiplayer calls to `sub_080332BC` are not patched.
