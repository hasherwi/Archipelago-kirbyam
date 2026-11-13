# Rainbow Room8: original-source upper-arrival witness

Fresh-boot continuous replay, reviewed 2026-11-09: **native110 →554 in5799
frames, retaining Spark and6HP**, with original enemy templates and no runtime
writes, state reloads or substituted essence. This closes the acquisition/carry
missing from the earlier lower-startup attack fixture.

The startup-only fixture reproduces the decoded108→110 arrival: door record
0x0087847A at trigger tile(34,18) selects spawn tile(7,8), resulting in Kirby
(104,120.99609375). The incoming transition itself was not replayed. The verified
AP source is `REGION_RAINBOW_ROUTE/ROOM_1_06_LOWER_MID`, whose existing outgoing
edge to Room8 has no extra requirement. The logic requires independent access to
that compartment, not merely generic Room8 reachability.

Normal Kirby descends and inhales native Sparky template0x008B743C at(72,520),
then swallows to acquire Spark. The source is finite; no respawn or retry is
assumed. The replay carries Spark intact through the central descent, uses the
ordinary left bomb chain to reach the lower chamber, and protects the descent
with Spark before entering water. It swims to the close right-hand pose and
activates Spark above the waterline against the wall-separated bomb at(13,57).
The remaining right-shaft and lower-bomb sequence enters Room9/native554.

[Compact acceptance manifest](rainbow-route-8-source-acceptance.json) records
fixture changes, identity hashes, source and entry coordinates, replay hash and
checkpoints. The full controller trace and private images remain local. The
previous matched attack/control fixture continues to establish the specific
wall-hit effect; this new record adds the original-source acquisition/carry.

## Installed scope

`bomb_110_room9` binds only Room8's outgoing Room9 edge when the actual source
policy guarantees SPARKY→Spark. This includes native Spark, deterministic Spark
assignment and a no-failure singleton live pool. Mixed/failable live outputs and
other assignments remain outside the installed subset, with their prior access
behavior unchanged. They are **not** claimed solved or impossible.

The graph begins with Normal, explicitly acquires from the native source, and
keeps the complete carried-Spark route in one witness. Spark permission is
required when ability gating is enabled and becomes progression for this installed
subset. Gating disabled does not waive the physical source or entry prerequisite.
No permanent room-open event, arbitrary incoming-side access, or optional bypass
is inferred. RoomSanity and other exits remain unchanged.
