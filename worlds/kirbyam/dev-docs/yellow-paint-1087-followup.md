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

## Bounded Cupid source-to-chest replay; admission pending

A later cold-start replay and matched controls are retained in
`carrot-yellow-cupid-candidate.json`. On the current combined Phone/main ROM,
production world setup seed 14 assigns Cupid to both original Sparky sources.
Room Sanity is on, ability gating and Area Keys are off, actual initial/max HP
is 6, and enemy health is 100%. This is a controlled startup beside the real
719 door, not a filled seed or proof of every upstream compartment.

The human acquires upper Cupid at frame 5450, loses it to damage, reaches the
lower original source and reacquires Cupid at 7578. The route reaches native
733 at 8240 with Cupid retained. An upward charged shot opens the upper trigger
while Kirby remains below the one-way ledge; the opened lower corridor then
permits a second upward shot at the lower trigger. The human flies around the
remaining central obstacle and physically collects the chest at frame 9547.
Native chest flag 80 and exact-source event counter 1 are observed, and the real
client produces `LocationChecks [3960501]`. Minimum observed HP is 3; a native
healing pickup restores HP 4. No health, equipment, source or geometry RAM edits,
state restores, Phone calls or helpers occur in this cold replay.

Removing the upper-shot input window leaves both triggers closed. Removing both
lower-shot windows leaves only the upper trigger open. Neither matched control
sets the chest flag or produces a client check. These finite controls do not
prove that all other methods are impossible. The earlier unchanged UFO input
schedule failed with Cupid; restored-state exploration found the revised inputs,
then the entire successful sequence was replayed from a blank native battery.

This is a bounded physical candidate, **not an installed Cupid access rule**.
Health/source-profile coverage, independent entry qualifications and source-
sensitive graph integration still require review. It does not qualify Phone,
Normal + Phone, all Cupid sources, every health setting or arbitrary retries.
The existing UFO witness remains intact. The unsupported-policy fallback and
Phone/helper restriction above remain blockers to closing #1087; no progression
rule changed here, and #490's broader action gates remain outside this scope.
