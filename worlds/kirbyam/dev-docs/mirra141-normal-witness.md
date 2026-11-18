# Room141 top Mirra: bounded Normal clearance

The TOP_MUSTARD compartment has a source-free Normal route through Mirra
`0x088B7780` to the native room545 door. The four positive records in
`mirra141-normal-acceptance.json` retain one HP and Normal throughout, kill the
actual two-HP Mirra, and enter room545. They cover vanilla, 500% enemy health
with gating enabled and zero unlocks, shuffled Beam, and live randomization
with gating enabled and zero unlocks. No random grant is required.

Each fresh blank-save fixture configures room141 spawn `(552,64)`, producing
native arrival `(536,56.99609375)` at frame1085. This matches the top arrival
pose independently recorded after actual 545→141 travel in
`ordinary-141-directed-burning-acceptance.json`; it is a coordinate join, not
an additional global-entry proof. The accepted local action retreats left,
inflates and settles, faces right, then fires an air puff and walks to the
cleared door. The native damage callbacks and disappearance distinguish a
kill from merely scaring Mirra. The wrong-facing control changes only the
launch facing: Mirra remains alive and Kirby stays in room141 with one HP.

The graph is scoped to TOP_MUSTARD, requires Normal, contains no ability
sources or retries, and models local clearance only. The ordinary entrance
retains its existing area-key rule. Other room141 metal barriers, the east
Mirra and the lower-to-top access requirements are unchanged. This does not
provide a generic Normal Mirra action or certify every arrival phase.
Two additional warmup attempts failed to cross (one lost HP); neither
established the scared callback, so neither proves scared-Mirra behavior.

Manifest provenance includes private trace/runtime hashes, fixture and
production ROM hashes, bridge and script hashes, native snapshots, damage
landmarks, and all guarded production-client configuration writes. Writes
occur only at frame1085; subsequent observations are read-only. ROMs, saves,
full traces and input replay packets remain private. The paused Normal-only
playthrough was not used or resumed.
