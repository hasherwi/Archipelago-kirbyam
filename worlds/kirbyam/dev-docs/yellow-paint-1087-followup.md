# Yellow Paint alternatives follow-up (#1087)

Target: `MINOR_CHEST_SPRAY_PAINT_02`, AP 3960501, native room 733,
`REGION_CARROT_CASTLE/ROOM_5_16`, chest template `0x088D3DD0`.
This audit does not close #1087 or add an unverified access alternative.

## Source-backed access currently installed

`bomb_733_yellow` / `room14_entry` is the qualified UFO alternative. It requires
independent access to native 720 and two distinct finite original Sparky
sources in 730 (`0x088D4FC0` and `0x088D4F9C`) with guaranteed UFO outcomes.
The upper acquisition, intentional discard for the ladder, lower acquisition,
real 730-to-733 transition, top-charge lower Bomb Block shot and physical chest
receipt are recorded in `carrot-yellow-ufo-source-witness.md` and its runtime
packet. Ability-gated profiles additionally require UFO permission. Ownership
alone is not an equipment source; mixed/failable outcomes do not qualify.

The existing target is policy-scoped. Outside its guaranteed-UFO applicability,
the legacy location rule remains in effect, currently unrestricted beyond its
owner region. That is an unresolved partial-coverage gap, not evidence that
Normal, Phone or Cupid suffices. Closing it requires a qualified alternative
or an explicitly reviewed unsupported-profile policy. This follow-up preserves
the existing safety boundary instead of converting an untested candidate into
a source capability.

## Phone remains unqualified here

`phone-carrot-helper-evidence.json` records a helper-associated upper-chain
activation and a human Normal lower-chain action. The precise helper attack
and full helper equipment history were not established. The Phone admission
in `phone-progression-admission.md` covers small switches and Heave-Ho, not
helper Bomb Block attacks, ability attacks, copy sources or discarded stars.
Consequently Phone inventory must not become a speculative OR branch here.
The Chalk witness does not qualify this separate chest.

## Cupid acquisition observed; complete route still missing

An isolated mGBA 0.10.5 experiment on the combined Phone/main source used an
actual production mode-1 policy from world seed 14, Room Sanity on, ability
gating and Area Keys off, enemy health 100%, actual starting HP 6. It used the
lawful USA base and combined patch SHA256
`c3fca0d4b550130d6ff65e7679aca4950a88ae8d36a036d9371be918f79cd630`.
Only player-zero startup was moved to the documented 719 door fixture at
(232,56). Eight production client source-configuration writes occurred at
frame 1085; no source objects, equipment, health or target geometry were edited.
This world setup was not a filled seed or restricted-run beatability test.

A cold-start replay of the retained UFO input schedule reached the same
719→720→734→720→730 ingress and acquired Cupid (native ability 19) from the
upper original Sparky at frame 5450, HP 6. Reusing UFO movement timings then
lost Cupid at frame 6004 and died before reaching 733. Separate restored-state
controller exploration carried Cupid farther through the maze, but did not
reach the chest. These are finite unsuccessful schedules, not an impossibility
claim, and restored-state exploration is not accepted source-to-chest evidence.
No Cupid attack, lower-chain activation or physical/AP chest receipt is admitted.

Next: establish a continuous cold-start Cupid source-to-chest route with exact
entry and compartment coverage, target-order observations, matched controls,
health qualifications and physical plus AP receipt. Then represent it as an OR
alternative on this same target with its actual finite source requirements.
Phone needs an independently qualifying permitted helper action; another
human ability's success cannot qualify Phone. No progression rule changed in
this follow-up, and #490's broader action-gate work remains outside scope.
