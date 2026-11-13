# Finite original-source Ice witness for Chocolate

This bounded witness supports only `bomb_517_chocolate`, graph `hub2_ice_entry`,
and `MINOR_CHEST_SPRAY_PAINT_12` (local location 3960511). The original Waddle
Doo template `0x088CA04C` at (528, 264), native type 18 and copy field 7, is a
finite source. Generation seed 149 uses the full 25-ability pool and raw policy
seed 13204005821666718668, guaranteeing Doo to Ice (2).

## Recorded route and mechanism

Independent Hub2 access is assumed. Normal crosses the real 591 to 517 door at
1109, ingests Doo at 1833, and actually acquires Ice at 1939. That original source
remains absent thereafter. Ice clears its own corridor F1 at 2016 and is retained
without player damage. Helpers remain in native room 101. Fresh saves and startup
room/coordinate fixtures are used; the only eight configuration writes are at
1085. There are no later gameplay writes or restored states.

Ordinary traveling breath is launched at frame 3326 from
(185.99609375, 120.99609375), facing right. The traveling child callback is
`0x080737D9`, parent player `0x02020EE0`, scanner bounds (-3, -3, 3, 3), mask
`0xA0000203`. HP1 first clears target F1 (14, 7) at 3341; HP6 at 3342, at both
enemy-health endpoints. Scanner rectangles are (219, 116, 225, 122) and
(219, 114, 225, 120), respectively. The mouth object's bounds do not reach the
target's x224 edge. Chain callback `0x0800E27D` identifies the traveling packet
as parent. Native creation/update is in `src/code_0806F780.c:5632-5697,2378-2421`.
This is sampled/source-reconciled attribution, not instruction-breakpoint tracing.

Each of the four HP1/6 by enemy100/500 positives finishes seven linked cells
30 frames after its target hit and physically opens chest 57 at 4252. All eight
endpoint runs have 3406 samples, 1085 through 4490 inclusive. Four full-length
controls omit only B during [3326, 3356), match states through 3326, and preserve
the earlier corridor attack. They retain HP and Ice while target, linked cells,
chest and client event stay sealed. Preserve the distinct HP1/HP6 hit timings.

The gated Ice-only permission run completes the full route. Empty permission
stays Normal through 2067 (983 samples), an acquisition-only negative. Inventory
permission is not equipped Ice. Chest event source `0x088CA0B8` maps through the
unchanged local client to exactly 3960511; there is no server receipt claim.

## No frozen payload dependency; bounded acceptance

Independent stable-instance audits distinguish recycled slots from enemy damage.
Doo ingestion is the only original-enemy non-removal HP reduction. Other original
enemy reductions end at HP1 with flag `0x1000`, matching the native removal path
in `src/object.c:180-212`. No room517 object in the ten traces has frozen-enemy
callback `0x0809D655` or generic task `0x08070581`. This recorded route has no
non-source combat, frozen platform or frozen payload dependency. Per-frame
observations do not instrument every intra-frame state or prove universal health
independence. Intermediate health and all-RNG behavior remain untested.

No generic Ice breakability, global range, arbitrary arrival, game-start access,
other target, exit, helper route, RoomSanity guarantee or source renewal follows.
Independent source access and non-circular raw-source permission checks remain
host requirements. Native spray-bit status was not separately instrumented.

`cabbage-ice-acceptance.json` contains scalars recomputed from frozen states,
controller-command comparisons, tile changes and local client results, with
private-packet and independent accepted-review hashes. No raw trace, input stream,
ROM, save or private path is included. Repository tests validate the bounded
contract and exact target ownership, not an emulator rerun.
