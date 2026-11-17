# Native wood overlay for themed hub mirrors (#1027)

The Area Key lock now draws only the four wooden pieces from the game's own
boarded mirror. The themed hub frame remains visible underneath. This is reused
in-game art, not original artwork by Mateo; his contribution was extraction and
reference context. No extracted tile sheet or replacement art asset is shipped.

## Runtime and patch contract

Only `ap_area_hub_mirror_main` uses new animation `0x294`, variant 11, frame 56.
`SpecialHubMirror` (`0x8C`) retains its existing anchor `(x, y + 16)`;
`DoorToHub` (`0x97`) retains `(x, y)` and its separate native base effect.
The gate, collision, initialization, destructor and Warp Star code are unchanged.
Ordinary mirror/AreaDoor boards retain retail variant 6, including its full frame.

USA animation 0x294's native variant table is at `0x0841E494` (11 pointers),
frame attributes at `0x0846A744` (56 twelve-byte records), and variant 6's script
at `0x0841E348`. Frame 32 uses OAM entries 137–142 from `0x084A108C`.
Entries 137–140 are the wood; entries 141–142 are the unwanted gold mirror.
The patch copies the metadata tables into a reserved 776-byte extension,
preserves all old entries, adds a script selecting frame 56, and appends a frame
with OAM start 137/count 4. Two native table pointers select the extended tables.
The builder validates the source pointers, script, frame and all six OAM records
before writing. Drift fails closed. The synthetic CI ROM contains metadata only.

The original 4bpp tiles and palette 0xAF stay in place. Index 0 is transparent;
the wood occupies 24×24 pixels at x=-12..11, y=-23..0 relative to its anchor
(canvas anchor 12,23). It uses palette indices 2,3,6,7,10,14. This is derived
from native OAM and pixels, not inferred from hardware sprite limits. There is
no scaling, palette conversion, new graphics allocation or frame/glass layer.
Native definitions were cross-checked against KatAM decomp commit
`7d969fbce14fdc838d2c1ea01389717fb96c3189`, `include/sprite.h` and
`src/sprite.c` (`DisplaySprite`).

## Native evidence

[Evidence matrix](hub-board-native-evidence.json) records implementation commit
`ae51c4d1d659c0d2138fc236d635de67576e9603` and the rebuilt patch SHA-256.
Tests used an isolated mGBA 0.10.5 core and the lawful USA ROM, SHA-1
`274b102b6d940f46861a92b4e65f89a51815c12c`. All ROMs and saves remained private.
Each cold fixture changes only player 0's startup room/coordinates (plus immutable
Area Keys configuration for the disabled runs). Hub Connections and Area Keys
are delivered via the actual payload mailbox. Camera placement holds player
coordinates for 35 frames per mirror; it is a rendering fixture, not route proof.
Relock explicitly clears the key mask. Private savestate reload is also exercised.

All 32 native templates across rooms 190, 191, 192, 193, 194, 290, 291, 390,
490, 590, 591, 592, 690, 790, 801, 805 and 890 were inspected with keys enabled
and disabled. Twelve keyed overlays (five SpecialHubMirror, seven DoorToHub)
show variant 11/frame 56 while locked, disappear after key delivery and return
on controlled rollback. Other templates retain their native indicator or absence.
Disabled-key runs never create variant 11. This covers the template inventory;
it is not every shuffled route assignment or native prerequisite combination.

Actual unscaled 240×160 screenshots from the rebuilt emulator:

- [Before: room 801 → 592 locked](hub-board-images/before-801-592-locked.png)
- [After: room 801 → 592 locked](hub-board-images/after-801-592-locked.png)
- [After: same mirror unlocked](hub-board-images/after-801-592-unlocked.png)
- [After: DoorToHub in room 191 locked](hub-board-images/after-191-locked.png)

The first comparison preserves the blue themed frame while removing the extra
gold frame/glass. Room 592 is the Cabbage Cavern destination. Connections are
present; Area Keys are absent for locked images. Images are native emulator
output, not a mockup or composited sprite sheet.

## Regression checks and limits

`test_hub_board_sprite.py` verifies metadata preservation, unchanged tile/palette
references, the four-piece frame and rejection of drift/invalid reservations.
`verify_area_key_objects.py` executes the compiled ARM hooks for both families,
repeated lock/unlock cycles, missing native initialization, disabled keys,
base-effect preservation, anchors and duplicate prevention. Existing ordinary
mirror and Warp Star lifecycle checks remain active.

The full KirbyAM aggregate, packaging and exact-head CI results are recorded in
the PR. Linked multiplayer, every route assignment and a complete playthrough
are not claimed. Historical evidence in `area-key-object-reconciliation.md`
predates this change; its gold-frame appearance limitation is superseded here.

## In-flight Warp Star follow-up

[Paired native evidence](hub-board-warp-star-flight-evidence.json) closes the
previously unrun in-flight case for one Warp Star in native room 142, template
`0x088B7A10`, on the merged boards implementation. The existing disclosed
startup/mailbox fixture supplies the correct key. Controller input (70 frames
Up, then 26 Up+Right) boards the star; native passenger mask becomes 1.

An unedited boarded snapshot supplies two 1,200-frame continuations: ordinary
control and controlled key-mask rollback immediately after boarding. Both
retain the passenger for 513 frames, enter native room 195 at frame 503, and remove the
original transport at frame 514. Recorded player position, room, star object fields
and cleanup timing are identical when excluding the deliberately different
key mask. This does not claim equality of every byte of emulator state.
The rollback case finishes with keys absent and the human safely in native room 195;
it verifies preservation of an already boarded transport, not permission for
a new locked boarding attempt.

The existing idle-star tests still cover suppression, receipt-driven respawn,
duplicate prevention, relock and savestate reload. No production code or ROM
patch changed for this follow-up. It remains a controlled lifecycle fixture,
not natural route proof, Normal-only baseline evidence, every shuffled route
or linked multiplayer coverage. ROMs, savestates and full native traces remain
private; the committed record contains derived observations and hashes only.
