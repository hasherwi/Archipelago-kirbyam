# Olive Vitality Normal traversal binding

The installed location target requires independent access to
`REGION_OLIVE_OCEAN/ROOM_6_CHEST_1` and the bounded Normal sequence from its
room815 arrival to `VITALITY_CHEST_OLIVE_OCEAN`. The current AP graph has only
one incoming entrance, from Room15/native551 with its existing flight condition.
The native551 door at tile(73,18) enters815 at spawn tile(5,9); fresh fixtures
observe the actual arrival at (72,136.99609375). The native815 underwater
connection goes out to553. Neither the incoming AP condition nor that separate
exit is changed. This binding does not establish unqualified upstream551 access.

The original silver block `room:815/template:0x088CCCFC` remains physical and
unconsumed. Normal inhale moves it into maintained lower-switch contact. An
intrinsic air puff then activates the upper switch briefly; the bounded timing
crosses the lower gate and reaches chest0x088CCC90. The graph models that complete
recipe as one room-scoped action, with no persistent opening, Copy Ability,
consumed enemy payload, or retry. It does not generalize to another block,
arbitrary displaced-block state, arrival compartment, or switch latch.

[Five current-patch fixtures](normal815-current-acceptance.json) preserve Normal
and one HP. Vanilla100/500% and gated shuffled/live Stone policies with no owned
copy permission collect the chest; the production client's read-only poll emits
only location3960301. Omitting the final puff leaves Kirby alive before the gate
and emits no check. That control matches observations through frame3525. Helpers
remain in101 and configuration writes, where needed, occur only at startup.
The historical four positives and control in
[the original review](olive-normal815-source-witness.md) remain unchanged.

The new local rule requires the independent room access even when ability gating
is off. Owning an ability cannot replace it. It preserves the existing RoomSanity
check, incoming flight condition and outgoing swimming alternative. No ROM,
save or private replay packet is published; the paused playthrough is untouched.
