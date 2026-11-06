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

- Native paint IDs remain `0..13`; curated logical IDs `14..26` use native Pink as a safe renderer fallback. IDs absent from the generated registry are ignored.
- ROM default `0xFFFFFFFF` keeps older procedure patches safe.
- Pink is the fallback and a valid requested palette. Runtime Pink refresh is no longer skipped.
- The owned-paint A-button handler at `0x0814406C` records a genuine choice, including choosing a paint matching the AP default. Saved preference uses native treasure padding and the native serializer, not raw SRAM writes. See PROTOCOL.md for the marker and priority order.
- The patcher verifies both callsites still target `0x080332BC` before replacing them, refusing unknown ROM revisions.
- Demo and multiplayer calls to `sub_080332BC` are not patched.


## Curated colors (Issue #599)

`data/colors.json` is the shared registry. `color_registry.py` validates stable native
IDs, contiguous logical IDs, three 16-word RGB555 rows per curated color, transparent
index zero, the safe native fallback, and context-specific provenance. The world
builds YAML options and seeded random choices from it. `generate_colors.py` generates
`color_tables.h` for the native build; `--check` and the unit suite reject stale tables.
Add future colors through validated registry data, then regenerate and rebuild the patch.

Shadow, Ivory, Citrus, White and Lavender use verified named Squeak Squad USA normal
and UFO palette rows. The HUD rows are **derived adaptations**, not extracted native
Squeak Squad HUD art: Amazing Mirror HUD indices 1..6 use normal indices 3,4,5,10,6,7;
other Pink HUD colors, including the cyan UI accent, remain unchanged. Transparent
index zero is normalized to zero; ignored bit15 is stripped. These bounded tables
were approved for publication in [Issue #599](https://github.com/hasherwi/Archipelago-kirbyam/issues/599).
No sprite graphics or bulk source assets are included. Native Chalk remains unchanged.

Logical IDs never enter native paint ownership, menu indices, saves, player-color
arrays or Kirby's native color field. Curated colors write native fallback zero there.
The priority remains per-room AP color, explicitly selected owned native paint,
AP static color, then Pink. Every saved-paint nibble still validates against only
0..13, including malformed markers that encode 14 or 15.

The small main payload remains in its original window. `color_payload.bin` is appended
at file offset `0x1000000` (bus `0x09000000`), bounded to 64 KiB. No presumed internal
padding is reused. The patcher validates the original 16 MiB size, extension marker,
target alignment/range, native OBJ dispatch pointer at `0xD60820`, and eight original
HUD entry bytes at `0x3D21C` before changing those sites. The dispatch pointer and
three-argument HUD tail jump can reach the extension without a short Thumb BL.

OBJ substitution occurs only on native normal/UFO fallback variant zero, bank zero,
16-color loads at offset zero. Native animation cursor advancement, load-suppression
flag, transform function, sync flag and temporary variant14 semantics remain intact.
Native refresh helpers still compose ability/effect-owned indices 12..15 or 1/10..15
and update their backups. UFO's alternate form may compose its own custom UFO tail
with the normal custom body, exactly following that native order. This is not a
per-frame blanket palette write.

The HUD hook replaces only the exact Pink HUD source and bank/count, preserving both
working and backup copies and native argument widths. Substitution requires local
single-player gameplay, excluding demos and multiplayer. During synchronous scene
construction, the existing applied latch temporarily holds `AP_COLOR_STARTUP` so
Kirby can load its custom palette before HUD creation; the startup wrapper clears
it on return. Otherwise a bounded live HUD task is required. The existing per-frame
recovery still waits for fades before updating palettes.

New slot data declares `kirby_color_catalog_version: 3`. The client verifies
`APCOL03\0` at the appended ROM start before sending these color IDs. Earlier seed
metadata retains the native-only 14-color per-room pool. Regenerate a patch and update
the client for the expanded catalog; existing saves and owned paint choices keep their
format. No color items, menu swatches, ownership bits or save layout were added.

## Validation boundary

The optional `test/native/run_color_probe.py` applies the distributable diff to an
owner-supplied USA ROM in memory and executes the patched instructions in mGBA. Its
checks cover all 27 ability IDs in two form states for each curated color, HUD working
and backup rows, native damage/interaction composition, special variant14, partner
banks, transform parity, the load gate, and pre-HUD startup palette loads. Existing
native-color transitions and real native save serializers/checksums across three slots
remain covered. Scene construction is an explicit IO stand-in; this is instruction
and serializer evidence, not a full gameplay or visual-acceptance claim. No ROM or
save file is written by the probe. Interactive BizHawk and whole-game visual review
remain manual acceptance steps.

## Original static multicolor palettes

Rainbow (19) and Candy Corn (20) are original designs, with explicit normal, UFO,
and HUD rows. Choose `starting_kirby_color: rainbow` or `candy_corn`. These are
static colors; multiple hues appear simultaneously, following existing sprite
shading regions. Candy Corn uses white highlights, orange body shading and yellow
feet, approximating white/top, orange/middle, yellow/bottom without changing art.
Neither palette promises geometric stripes or color cycling.

Normal Pink outline and effect tail slots are retained. UFO retains its
native canopy slot 4 and tail slots 12..15; its body/saucer receives the theme.
HUD indices 1..6 follow the existing adaptation, preserving shared UI accents,
outline, eyes/white detail and all other HUD slots. Native abilities and damage
still compose their own colors. Menus, paint swatches, demo/multiplayer and partner
colors remain native under the existing gameplay-only contract. Explicit owned
spray paint continues to override a static AP color.

Catalog 3 requires APCOL03 and regenerated patches. The updated client still
accepts catalog 2 only with APCOL02, limiting its static and per-room choices to
0..18. Legacy metadata retains 0..13. This prevents new IDs reaching old payloads.

Negative (21) complements each RGB555 channel of native Pink body/feet slots 2..11;
its dark green highlights and pale teal shadows intentionally reverse the shading.
Its UFO row inverts the native UFO body/saucer slots separately, retaining canopy
slot 4. It retains black outlines, eye/white details, native effect tails and shared
HUD accents; only the six existing Kirby HUD slots adopt the theme. Choose
`starting_kirby_color: negative`.

Additional original themes use descending brightness for readable body/foot shading:

| ID | YAML option | Body and highlight | Feet / UFO saucer accent |
| --- | --- | --- | --- |
| 22 | `pineapple` | Warm gold/amber, cream highlight | Dark leaf green |
| 23 | `cotton_candy` | Pale sky blue | Bubblegum pink |
| 24 | `royal` | Deep violet, lilac highlight | Rich gold |
| 25 | `pumpkin` | Pumpkin orange, apricot highlight | Dark plum |
| 26 | `mint_chip` | Pale mint | Dark cocoa |

Each includes its own normal, UFO and six-slot HUD adaptation with the same native
outline/eyes, UFO canopy/effect-tail and shared UI preservation rules. Palette-only
Mint Chip has cocoa feet, not chocolate-chip texture; Pineapple has green feet, not
new leaf geometry. No sprite art or animation is added. Game Boy is not included.

Catalog 3 remains unreleased within this draft PR. Released IDs 0..18 and draft
Rainbow/Candy Corn IDs 19/20 are unchanged. The remaining draft entries are
contiguous at 21..26; their palette colors are unchanged. Earlier draft seeds and
ROM patches must be regenerated together after removal of a draft entry: APCOL03
cannot distinguish those draft layouts and mixing them can select the wrong color.
Native paint saves and released catalog-2 seeds remain compatible.
