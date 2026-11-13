# Cabbage Chocolate chest: finite Fire breath alternative

The single `bomb_517_chocolate` row OR-composes its existing Beam and Smash
witnesses with the separate Fire-only `hub2_fire_entry` graph. Only
`MINOR_CHEST_SPRAY_PAINT_12` (3960511) in Cabbage Room 6 / native 517 is gated.
No other exit, RoomSanity check or global attack range changes.

## Source, policy and permission

Normal generation seed 18 uses the full 25-ability pool and policy seed
2395008880317811979. Its guaranteed WADDLE_DOO result is Fire, runtime ID 1;
table byte `0x3517FE` is 1 and source bitmap bit 18 is enabled. The finite
original source is template `0x088CA04C` at native coordinates (528,264).
Kirby enters from native 591, reaches that source as Normal and acquires Fire
through the production swallow hook at frame 1939. No substitute source,
post-generation mapping or injected equipment is used.

The graph requires independently reachable Cabbage Hub2, not merely Room 6.
Its raw guaranteed-source guard checks the policy before permission filtering.
This prevents a mixed random pool from becoming a false Fire guarantee when
only the Fire item is owned. The finite source has no retry or renewal proof.
Fixed mode 1 is the native-tested policy. Host tests separately cover static,
shuffled and random singleton policy semantics and reject uncertain grants.

Fire is already gateable in `abilities.json` and its item is already
`PROGRESSION` in `items.json`; no promotion or gateability change is needed.
When gating is enabled, Fire Ability is permission to acquire this source,
not equipped Fire. Removing the source or putting it behind the chest fails
regardless of inventory. Native replays use gating and Area Keys off; host
rule tests separately verify gating, Area Keys and fill behavior.

## Continuous native acceptance

Four positive runs and four matched controls cover actual HP 1 and 6 with
100% and 500% enemy health. Every run is a cold boot with a narrowly declared
predecessor fixture: four startup room words at ROM `0x2D8CB8` and eight
coordinate words at `0x2D8CD0`. The resulting 15 changed bytes are retained in
`cabbage-fire-acceptance.json`. This is not proof of reaching Hub2 from game
start. The actual 591 to 517 door is crossed at frame 1109, after which the
source-to-chest route is continuous, with no state restores or gameplay writes.

At frame 1085, the genuine production client makes exactly eight four-byte
configuration writes. The harness fences their frame, address and size; these
are not compare-and-write GUARD requests. No later harness writes occur.
All three helpers stay in native 101. Every one of the 3,406 sampled frames
from 1085 through 4490 retains configured maximum HP. Fire remains equipped
from acquisition through the final sample.

At frame 3326, Kirby faces right at (185.9961,120.9961). Only B is held for
30 frames, with no directional boost or payload. The traveling Fire packet
(callback `0x080737D9`, bounds ±3) opens F1 at tile (14,7) at frame 3341.
The seven linked F2 cells finish clearing by 3371. The packet has attack word
`0xA0000103`, category `0x100`, strength 3. Its flags change from pre-contact
`0xA0004100` to hit `0xA0084100`.

At its seventh observed movement, the HP 1 packet center is
(223.0117,117.8242) and the HP 6 center is (221.3711,118.6992). Native integer
scanner rectangles are respectively x 220–226 / y 114–120 and x 218–224 /
y 115–121. Both first reach tile (14,7) on that movement. The concurrent
mouth-only callback `0x08073B65` stays anchored to Kirby with bounds
(0,-4,16,4), reaching only x 201.9961. The recorded player parent, helper
rooms, packet movement, scanner source and matched controls attribute the
hit to the traveling packet. Scanner coverage is derived from observations
and source, not a CPU breakpoint trace. Neither endpoint establishes a global
Fire range or an intermediate-health interpolation.

The physical chest at (320,136) opens at frame 4252. Chest index 57 records
event source `0x088CA0B8`, and the initialized production client's real minor
chest poll captures exactly `LocationChecks [3960511]`. The callback is local;
no server transmission or acknowledgment is claimed. Native spray 11 remains
false because AP owns the reward.

Each 4,490-frame control removes only B during frames 3326–3355. Acquisition,
carry and all later inputs stay unchanged. F1 and all seven F2 cells remain
closed, the chest stays unopened, and no event or client check appears.

## Provenance and limits

The frozen native acceptance used AP commit
`3304eb7cd4d83f8e09f18cfb737fc67e798a7b1e` and native source commit
`7d969fbce14fdc838d2c1ea01389717fb96c3189`. The compact public metadata records
the private manifest SHA-256 and each run's ROM/input hash, not ROMs, saves,
patch archives, screenshots or raw traces. The native packet and mouth paths
are `src/code_0806F780.c:2319–2465`; scanner/filter anchors are
`asm/code_08032E98.s:6946–7333,8630–8636`.

Independent review verified all eight runs, exact matched input differences,
all four fixture byte comparisons and all seven movement recurrences for both
HP classes. The source x-coordinate observed at frame 1826 differs by HP:
530.9961 at HP 1 and 531.9961 at HP 6. These are observations of the same
original source, not different source placements.

Unproved scope remains excluded: game-start Hub2 access, arbitrary arrivals,
respawn, renewal, multiplayer/helper or Phone routes, other targets, global
Fire equivalence and intermediate enemy-health settings. Repository tests
validate the graph, policy, AP binding and retained metadata; they do not
replay a ROM.
