# Supplemental actual Room6 lower-mid entry to the Sword route

This supplements, rather than replaces, the original five-run
[decoded-arrival witness](rainbow-route-8-sword-witness.md) and its unchanged
runtime packet. The additional [compact record](rainbow-route-8-sword-entry-runtime.json)
proves the actual native108 lower-mid door, original Sword acquisition, exact
underwater target and native554 exit continuously at **100% enemy health and
actual1HP only**. It adds evidence, not a new rule or source-policy grant.

## Production identity and exact door

The fixture uses the same already-generated100%/1HP native-policy production ROM
from `8dbf941f30f88f8d0f151e2a556d31ca19aa6ac5`, with its original hash. This is
not a new production build. Exactly17 bytes change, solely in the standard
startup room/position arrays at0x2D8CB8/0x2D8CD0. Source, door and terrain data
are unchanged. The eight real-client configuration writes occur at1085 before
movement, with no later gameplay writes or state restores.

At1085, Normal Kirby starts on the dry lower-mid slope in108 at(504,277).
Controller movement settles at(551.546875,296.99609375); Up starts at1206 and
produces the door animation at1207. Actual110 entry occurs at1218, arriving at
(104,120.99609375). Door record0x0087847A selects tile(34,18), destination110,
spawn(7,8), matching the original decoded-door evidence.

This does not establish access to the startup pose from arbitrary108 entrances.
The independent prerequisite remains exactly
`REGION_RAINBOW_ROUTE/ROOM_1_06_LOWER_MID`, not generic108 or110 access.

## Source, exact attack and completed exit

At1238, original Sword Knight0x088B74CC is observed at(120,215.99609375), type26,
copy18 and HP4. Normal inhale and Down acquire Sword at1512. Every later positive
sample retains Sword. The accepted route is independently replayed, including
enemy phase: an earlier exploratory90-frame door wait caused later acquisition
damage, and is not acceptance evidence. The accepted31-frame wait resumes from
the settled arrival, without assuming the old trace's phase is interchangeable.

At3039, the exact F1(13,57) opens while Kirby is underwater at
(185.99609375,926.71484375), state0x69. The parent-linked attached Sword weapon
uses animation0x6F/1 and bounds(0,-26,25,-3), scanning columns11–13 and rows56–57
through solid column12. This is the underwater Sword spin, not landing wave.
The other F1(12,50) remains sealed.

The controller crosses into native554 at3541 and finishes3620 with Sword and1HP.
The transient water flag clears3551, so no underwater554 landing is asserted.
There are2536 positive HP samples, all1HP.

## Matched control and limits

A separate cold control omits only the30-frame target B press starting3035.
Every sampled state through3035 matches. It finishes3620 in110, never enters554,
and keeps F1(13,57) sealed throughout every110 sample. Its2536 samples also
retain1HP. Both runs use only the eight initial configuration writes.

This closes the incoming-door replay gap for this specific100%/1HP case. It does
not broaden the original discrete health coverage, prove arbitrary108 arrivals,
or add randomized-source/gating-on native acceptance. Original packet and
artifact hashes are preserved separately; the supplement records its own input,
result, frame, effect and fixture hashes without changing those original records.
