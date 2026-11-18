# Radish map: bounded Normal witness

The standard traversal target `bomb_617_radish_map` replaces the pending
`can_get_rr_map_chest` token. Its independent prerequisite is reaching
`REGION_RADISH_RUINS/ROOM_8_CHEST_2`. It proves only the map chest from the native
617 lower entrance; it grants no ability, permanent switch or reverse route.

Four fresh headless native runs entered from the original 502 door at tile
(49,16), arriving at (56,136.996). Normal Kirby approached the left boundary,
floated and released an air puff below the upper platform to hit the upper bomb
at (11,3), landed below the platform, jumped onto the resulting bridge, crossed
the wind corridor, then slid into the lower bomb at (22,8). Walking into the
opened compartment and pressing Up opened chest template `0x088D1114`.

The runs covered 1 and 6 HP with ability gating both on and off. All had zero
ability permissions, actual Normal equipment throughout, no damage, and all
three helpers remaining in room 101. Each run began with a blank battery save;
no state restoration or runtime RAM writes were used. Startup ROM edits selected
the initial room/position, HP, gating and Area Keys settings and synthetic local
client authentication. These are bounded room proofs, not whole-seed playthroughs.
The existing Normal-only playthrough was not resumed.

Native chest 73 and AP major-check bit 8 changed together at frame 2340; native
map-ownership bit 8 stayed clear. The unchanged client poll emitted exactly
`LocationChecks: [3960207]` to an in-process capture, with no server connection.
Omitting the upper puff or lower slide prevented the check in matched bounded
runs. The lower-slide omission took damage (minimum 4 HP); controls establish
these input-sequence dependencies, not universal impossibility of other routes.

`radish617-normal-acceptance.json` retains scalar results and SHA-256 hashes of
private traces. ROMs, saves, screenshots and replay inputs are not distributed.
The pinned USA original has SHA-1 `274b102b6d940f46861a92b4e65f89a51815c12c`.
The native runs used vanilla assignments. Host tests also exercise shuffled and
live policies: this route has no acquisition, source, pool or retry dependency.
It therefore does not turn a random possible grant into guaranteed equipment.

This closes this one pending gate. It does not certify the remaining physical
placement access, encounter output acquisition or policy-scoped gate fallbacks
tracked by issue #1114.
