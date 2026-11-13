# Candy map: ordinary Normal route through native 426

## Result and ownership

Independent review accepts three bounded controller-only witnesses: actual 1 HP
at 100% and 500% enemy health, and 6 HP at 100%. Each physically collects chest
`0x088C87FC` and the unchanged production client's read-only local poll reports
exactly `LocationChecks [3960208]`. `MAJOR_CHEST_CANDY_CONSTELLATION` belongs to
`REGION_CANDY_CONSTELLATION/ROOM_9_CHEST_3`. Preserve its existing null rule.
Normal is ordinary equipment, not a Copy Ability item or a new generic power.
The separate RoomSanity check and outgoing Goal 2 edge remain unchanged.

`candy-normal426-acceptance.json` retains compact scalars and private artifact
hashes. Review independently reconstructed the three production ROMs and checked
native source, telemetry, exact ownership and the production client. It did not
perform a fresh emulator replay. No ROM, save, raw frame stream or private path
is published here. Source d04d4d0 and integration base a1c2cff have identical
production gameplay code; their differences are documentation and tests only.

## Qualified boundary and setup

Each run cold boots a blank battery save. Only 17 startup room/position bytes
differ from its normally generated production ROM. The fixture stores native
419 at (1184,256); Kirby is observed at (1176,248.99609375) beside the actual
(73,15) door. Up at frame 1086 enters 426 at frame 1098, at
(72,56.99609375), with clear tracked slots and map flag. This proves a real
transition from a qualified near-door 419 fixture, not access to that doorway
from arbitrary 419 arrivals or a new game.

All 3,070 consecutive recorded samples, frames 1085 through 4154 inclusive,
retain exact starting HP and ability 0. “All-frame” does not mean boot frame 0.
Eight guarded four-byte production-client configuration writes occur at 1085.
There are no gameplay RAM writes, runtime ROM writes, state restores, imported
abilities or helper Kirbys in 426. Local polling sends nothing to a server.
The seed 2 recipe uses enemy-copy mode 1, all 25 allowed abilities, ability gating
off, area keys off, and minimum/maximum HP equal to the tested actual endpoint.

## Retained timing and physical completion

The full finite input sequence retains preliminary movement, unsuccessful puffs
and repeated first-switch body contacts. Its active intervals are 2009–2020,
2194–2205, 2635–2704 and 2723–2764. The first switch is momentary. At frame 2782,
Kirby is (231.0234375,56.99609375), the first gate is still opening with bounds
[-8,-32,8,-20], and a one-frame A input makes the decisive late jump. This is
not an arbitrary fresh single-press dash. Complete crossing occurs at 2807,
x=279.3671875, while the gate is closing with bottom bound -20.

The middle switch activates at 2820. The route reaches the lower switch through
the narrow shaft near x344; it does not establish that crossing the middle
switch's lower gate is required. The lower switch activates at 3218. Native
mode bit 0x4 makes switches 5/6 latch while loaded, not permanently or across reset.
Narrow-shaft positioning, jumping and inflation return above the upper platform.
The final gate is completely crossed at 3788, x=390.484375, bottom bound -28.
An ordinary down+B slide breaks the F1 chain at (25,3), then the physical chest
event at 3976 names 0x088C87FC and the major-chest transport flag becomes 0x200.

The matched 6 HP / 100% omission changes only frame 2782 keys 17 to 16, removing
A. Its entire recorded state prefix through 2782 is identical. It stays alive
and Normal but reaches at most x=250.375 in 426, never completely crosses the
first gate, never activates the middle/lower switches, and produces no chest
event or client check through 4154. This supports the recorded timing, not a
claim that jumping is the only solution.

## Limits and other alternatives

There are no local enemies in 426. These runs neither attack nor consume an
enemy in 419, so no finite enemy, copied ability or spit-star source is needed.
Separate lower-bypass exploration reached the upper-right corridor but neither
collected the map nor entered 420. Preserve ordinary alternatives without
assigning map or outgoing-door credit to that exploration.

No arbitrary 419 access, new-game route, 426 to 420 exit, RoomSanity, room-reset
persistence, multiplayer, copied ability matrix, gated runtime matrix, arbitrary
RNG, health continuum or 6 HP / 500% endpoint is certified. This is a sufficient
ordinary alternative, not a minimal or unique route and not a health restriction.
