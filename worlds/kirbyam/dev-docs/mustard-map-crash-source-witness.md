# Mustard map: finite Twister-to-Crash alternative

The separate `hub4_crash_entry` OR graph belongs only to `switch_310_mustard_map`,
`MAJOR_CHEST_MUSTARD_MOUNTAIN` in `REGION_MUSTARD_MOUNTAIN/ROOM_4_CHEST` (3960205).
The existing UFO graph is unchanged. This is not a whole-room range rule, another 310
exit, the separate F1 (35, 8), inventory equipment, or a mixed-pool/retry guarantee.

## Source and complete route

Production full 25-ability pool generation seed 15, policy seed 816280806725934461, maps the
actual 534 Twister template 0x088B59B4 at (144, 280) to Crash. Executed source ABI:
bitmap index 28, table 0x3518EE. The graph requires that raw singleton assignment,
independent Rainbow Hub4 access and, when gating is enabled, Crash permission.
Normal enters 534 from 590 and inhales/swallows the finite Twister at 1320. Air puffs
and slides clear 534 barriers without spending Crash; the independently played
aerial carry reaches 310 at 2344. No UFO combat or carry sequence is borrowed.

The exact dry pose is (425.996, 136.996), camera (305.996, 8). B at 2804 produces a
player-owned Crash task (callback 0x08082EBD, parent 0x02020EE0, category 0x10003).
The live attack contacts SwordKnight at 2875 and switch 0x088C3F14 at 2879; activation
is at 2881. Raw attack damage 29 is separate from the observed Knight 20→−9 delta.
Crash consumes to Normal at 2960. Gate 0x088C3F38 opens at 2961; Normal passes center 440
at 3005 and clears x = 454 at 3016 before closure at 3048. Normal slides through later
bomb blocks and opens chest 0x088C3FA4/native 39 at 3297. This atomic timed crossing
grants no persistent switch event. Chip can remain alive: movement avoids it.

## Positives and qualified controls

Four continuous positives cover actual 1HP/6HP × enemy 100%/500%, all without damage.
Four full omission controls skip only B at 2804 and never activate or collect, but
SwordKnight damage starts at 2847, **before** the positive's contact at 2875. They are
not damage-free controls. Two clean 1HP prefix controls stop at 2846, too early to
compare the later switch-contact frame. Two clean 1HP offscreen Crash controls
at entry (56, 136.996), camera (8, 8), consume Crash but exclude switch x = 312 from
coverage x = 8..248. They establish separate camera evidence, not global impossibility.
Direct live object/parent attribution ties the positive contact to the player;
helpers remain in 101, with no helper-parent attack in 310.

Exactly eight guarded production client configuration writes occur at startup 1085.
There are no gameplay writes, restores, helper use, runtime ROM writes or server
transmission. A startup-only fixture sets the entry; this is a native route witness,
not an end-to-end playthrough from the game's ordinary spawn.

## Location collection is not item delivery

Physical chest 39 opens and transport 0x0203B028 bit 4 is set. A separately reviewed
actual production client poll locally captures `LocationChecks[3960205]` using a
read-only adapter. Vanilla map ownership remains intentionally suppressed in the
AP fixture. Local check emission is not server receipt or randomized item delivery.
The no-trigger poll control has the same admitted damage qualification.

## Reproduction identity and limits

`mustard-map-crash-acceptance.json` contains compact outcomes and exact hashes.
The frozen native manifest hash is
`4f620650a0a67621b70365eac6bbc8155565beb30fed223445feeb5f693675d4`;
the separate client-poll manifest hash is
`6a3abe9137dee807921648495f97532ad7143bcc813588118ccd9b27789b39eb`.
Private ROMs, saves, raw traces and local paths are not distributed.

Initial 100%/1HP generation used f739e859; later generation and the regenerated 100%/1HP
build used 3304eb7. Retained old/new production ROM, fixture ROM, basepatch and
slot bytes are identical; archive hashes differ. Final 100%/1HP outputs were fresh
reruns on reused paths, not relabeled old traces; the initial twelve-run manifest
was not separately archived. The earlier build and positive raw trace remain
retained privately. Current results are pinned to exact build/input hashes.

Crash permission becomes progression for the enforced guaranteed Twister route,
alongside existing Foley/HotHead conditions. `start_with_all_maps` removes map
items but retains this check; a missing location does not promote this alternative.
Area-key entrances, statues, RoomSanity and unrelated exits retain their rules.
