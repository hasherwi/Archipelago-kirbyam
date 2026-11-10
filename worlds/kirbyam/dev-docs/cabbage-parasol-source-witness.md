# Cabbage Chocolate chest: finite Parasol forward-swing alternative

The single `bomb_517_chocolate` row OR-composes its unchanged Beam, Smash,
Fire and Missile graphs with a separate `hub2_parasol_entry` graph. This route
owns only `MINOR_CHEST_SPRAY_PAINT_12` (3960511) in Cabbage Room 6 / native
517. Both exits, the Area-Key entry and RoomSanity checks retain their rules.

## Original finite source and permission

Normal generation seed 29 uses all 25 allowed abilities and policy seed
14642711172500888381. The original Waddle Doo template `0x088CA04C` at nominal
(528,264) receives guaranteed Parasol 5: ROM table byte `0x3517FE` is 5 and
source bitmap bit 18 is enabled. Before swallowing, the actual source is type
18 with native copy field 7 and HP 4 or 20 at enemy health 100% or 500%.

The graph starts Normal at independently reachable Cabbage Hub2, takes the
actual native 591 to 517 entry at frame 1109, and approaches and swallows
that Doo. Parasol is acquired at frame 1939 and retained throughout the
subsequent carry. Owning an item does not supply equipment or Hub2 access.
The original source is finite; there is no respawn, renewal or retry premise.

A raw guaranteed-source guard precedes permission filtering, so owning only
Parasol cannot turn a mixed random pool or no-ability outcome into certainty.
The production target condition admits exactly the five independently
witnessed Doo assignments. Native acceptance uses fixed mode 1; guaranteed
singleton and uncertain policies have separate host rule coverage.

Parasol is already gateable, but its baseline item is `USEFUL`. It becomes
progression only when gating is enabled, the actual Chocolate chest location
exists, and the raw Doo policy guarantees Parasol. Explicit `start_inventory`
is created before regions. The existing scoped reconciliation now also checks
early Parasol instances after regions exist, promotes qualifying instances and
collects each once. Already-progression instances are not recollected. Duplicate
counts, fresh states, removal, disabled targets and uncertain policies are
covered separately from the native route. No runtime permission format changes.

## Continuous native endpoint matrix

Four positives and four matched controls cover actual HP 1 and 6 with enemy
health 100% and 500%. Every run is a fresh cold boot with a 32 KiB all-0xFF
battery save loaded before frame 0, no initial state and no later restoration.
The fixture changes only the documented 15 startup room/coordinate bytes:
player native 591 at (40,136), helpers native 101 at (48,80). It establishes
an independent predecessor fixture, not reaching Hub2 from game start.

The real production client makes eight four-byte configuration writes at
frame 1085. The harness fences frame, address and size and permits no later
harness writes. This is not a compare-and-write memory GUARD. No source,
position, ability or health is injected during gameplay. Native gating and
Area Keys are off; enabled variants are host rule tests, not native replays.

All eight runs retain configured HP on all 3,133 sampled frames from 1085
through 4217. Helpers remain in native 101. The source-corridor Parasol swing
opens a separate F1 at (34,18) on frame 2015 and its chain by 2039. That swing
and all other carry inputs remain in the controls. The accepted carry crosses
below the falling enemy near x 336, rises between the enemies, travels under
the central structure and reaches the left dry alcove without damage.

The target controls remove only B on frames 3069 through 3098. They continue
for the same full duration, including the attempted chest approach, retaining
HP and Parasol while the target F1, seven F2 cells and chest stay sealed. They
produce no event or check. Earlier exploratory routes that died are not part
of the accepted matrix, and no state from them is reused.

## Exact active swing, not a general range claim

Kirby stands right-facing at (185.99609375,120.99609375). B at frame 3069 starts
animation `0x35` at frame 3070. At frame 3078, the attached Parasol callback
`0x08077575` has parent player `0x02020EE0`, room 517, flags `0xA00C0100` and
attack word `0x30000043`. Its actual ObjectSetBounds rectangle at +0x3C is
(16,-11,48,11), matching the active animation box at +0x34. Integer scanning
covers x 201..233 and y 109..131: columns 12..14 and rows 6..8. It reaches
F1 (14,7) through the static solid columns 12 and 13. The preceding frame's
(7,-11,31,11) rectangle does not reach F1.

This is the only active scanner-enabled kind-2 object in the room when F1
clears. The chain callback `0x0800E27D` names that Parasol object as parent.
The seven F2 cells clear at frames 3084, 3090, 3096, 3102 and 3108. The
physical chest 57 opens at frame 3979 after the lower-passage continuation.
Its event ring names `0x088CA0B8`; the actual production minor-chest poll
captures exactly `LocationChecks [3960511]` locally, with no server submission
or acknowledgment claim.

These are post-frame read-only object, task and tile observations, not CPU
instruction breakpoint observations. The held umbrella at frame 3069 is not
scanner-enabled. Neither held Parasol, animation `0x42`, other attacks nor
other targets inherit this dry forward-swing proof.

At the frozen native commit, `src/code_0806F780.c:3440-3585` creates and
updates the attached object and copies the active animation hitbox into
ObjectSetBounds. `src/kirby.c:5831-5837` writes those bounds.
`asm/code_08032E98.s:8630-8636` is scanner dispatch, **not** the F1/F6 filter.
Rectangle scanning is at lines 6946-7237; tile-category filters and chain
creation are at lines 7238-7333. This corrects the frozen report's wording
without editing the original packet.

## Provenance and limits

Native acceptance used AP commit `db9d09d539afac3c8dab1a03390d505830d5b7c2`
and native source commit `7d969fbce14fdc838d2c1ea01389717fb96c3189`.
`cabbage-parasol-acceptance.json` retains the frozen manifest/report hashes,
full source policy, bounded setup, observed effect attribution and eight
outcomes. Private artifact hashes stay raw. Preserved tracked-text checks use
UTF-8 LF content, and prior graph checks use sorted parsed JSON, so Windows
checkout line endings do not change those contracts. ROMs, saves, generated
patches/archives and raw traces remain private.

This supports only the exact source, carry, dry swing and Chocolate chest.
It does not prove game-start Hub2 access, source renewal, arbitrary arrivals,
other targets/exits, RoomSanity, helper/Phone alternatives, general Parasol
range or intermediate health interpolation. Repository tests validate host
logic and retained evidence; they do not replay a ROM.
