# Cabbage Chocolate chest: finite Missile detonation alternative

The single `bomb_517_chocolate` row OR-composes Beam, Smash, Fire and the
separate `hub2_missile_entry` graph. This Missile route gates only
`MINOR_CHEST_SPRAY_PAINT_12` (3960511) in Cabbage Room 6 / native 517.
Unrelated exits, Area-Key entry and RoomSanity checks keep their existing rules.

## Source and permission

Complete normal generation seed 5 uses all 25 allowed abilities and policy
seed 2089474284528698192. The original finite Waddle Doo, template
`0x088CA04C` at nominal position (528,264), receives guaranteed Missile 25.
The generated table byte at `0x3517FE` is 25 and source bitmap bit 18 is set.
The actual native source has type 18 and copy field 7 before swallowing;
its health is 4 at 100% enemy health and 20 at 500%.

The graph starts Normal at independently reachable Cabbage Hub2, traverses
the actual native 591 to 517 entry, approaches that Doo and acquires Missile
through the production swallow path at frame 1939. It then follows its own
Missile-specific carry, detonation and physical chest route. Merely reaching
Room 6, owning an item or using another ability's carry does not supply it.
The exact source is finite, with no retry, respawn or renewal guarantee.

The graph's raw guaranteed-source guard precedes permission filtering. Mixed
random pools and no-ability outcomes do not become a Missile guarantee when
only Missile permission is owned. Fixed mode 1 is the native-tested policy;
host tests separately exercise guaranteed singleton modes and reject uncertain
policies. Existing Beam, Smash and Fire graphs remain alternatives, not AND gates.

Missile is gateable but its baseline item is `USEFUL`. The implementation
promotes it to progression only when ability gating is enabled, the actual
Chocolate chest location exists, and the raw Doo policy guarantees Missile.
There is no promotion for other policies or disabled minor chests. Explicit
`start_inventory` items are created before regions; once the actual chest exists,
early Missile instances are promoted and collected exactly once into the existing
state. Fresh states read the updated precollected items. Ownership
permits acquisition of the original source; it never supplies equipped Missile.

## Four continuous positives and bounded controls

The accepted positives cover actual HP 1 and 6 with enemy health 100% and 500%.
Each fresh boot uses the documented room/coordinate predecessor fixture in
native 591, with helpers in native 101. Fifteen changed bytes in the startup
arrays are retained in `cabbage-missile-acceptance.json`. This is not evidence
of reaching Hub2 from game start. A blank battery save is loaded only before
frame 0; there are no state restores, injected abilities or source remappings.

The genuine production client makes eight four-byte configuration writes at
frame 1085. The harness fences their frame, address and size, then permits no
later harness writes. This is not a compare-and-write GUARD claim. Native
runs have gating and Area Keys off; their enabled variants are host rule tests.
Helpers remain in room 101 throughout accepted samples.

All four positives maintain configured HP on every frame from 1085 through
5123, retain Missile after acquisition and physically open chest 57 at frame
4885. The production minor-chest poll captures exactly
`LocationChecks [3960511]` locally. There is no server submission or
acknowledgment. Missile is retained after detonation; it is not spent like Crash.

Four matched no-attack controls remove only the B press at frame 3742 and
otherwise use the same inputs through frame 3813, including later down-right.
Their complete state history agrees through frame 3742. Each preserves HP and
Missile, leaves F1 and all F2 cells intact, and produces no chest event/check.
These controls stop 1,072 frames before the positive chest collection. They
prove the attack-window dependency, not a full-length no-damage route while
the wall is shut. Later full-length control continuations die and are explicitly
excluded from the accepted no-damage matrix.

## Local blast, not piercing flight

At frame 3742, the upper dry standing pose is (201.9961,88.9961). B is pressed
alone for one frame, followed by down-right for 70 frames. Starting with down+B
instead crouches, so the ordering is part of the witness. Native movement and
collision lead to a stopped local detonation; no piercing flight is inferred.

The blast callback `0x08074745` appears at frame 3771 with fixed origin
(201.9961,88.9961), while Kirby recoils away. Its tile scanner bounds are
(-24,-24,24,24). Truncated integer scan extremes (225,112) touch the intended
F1 corner at tile (14,7). Later damage bounds grow to ±30, but the tile scanner
remains ±24; damage bounds are not used to claim reach.

On that frame, the F1 chain callback `0x0800E27D` at center (232,120) names the
observed blast object as its parent. That blast names player Kirby
`0x02020EE0` as parent. F1 clears at frame 3771 and all seven linked F2 cells
finish clearing by 3801. The per-run parent chain and observed scan bounds
are retained in the compact metadata.

A separate 1 HP / 100% neutral-direction control uses the same standing pose
but detonates at y 77.6055. Its lower scan edge reaches only y 101, and the
target remains closed at frame 3813 with HP and Missile retained. This excludes
that tested input variant, not all other Missile routes.

## Provenance and limits

Native acceptance used AP commit `3304eb7cd4d83f8e09f18cfb737fc67e798a7b1e`
and native source commit `7d969fbce14fdc838d2c1ea01389717fb96c3189`. Public
metadata includes hashes of the frozen private acceptance and review manifest,
source policy, bounded setup, observed blast attribution and outcomes. ROMs,
saves, generated patches/archives and complete traces remain private.

The independently reviewed evidence supports only the exact finite-source
carry and dry detonation. It does not prove global Missile range, intermediate
health interpolation, other targets/exits, arbitrary arrivals, RoomSanity,
helper/Phone alternatives or source renewal. Repository tests check the graph,
policy, promotion, options, fills and retained metadata; they do not replay a ROM.
