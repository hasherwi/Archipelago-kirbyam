# Olive Vitality: ordinary Normal route through native 815

## Result and ownership

Four reviewed cold controller replays cover actual 1/6 HP crossed with 100/500%
enemy health. Each physically collects chest `0x088CCC90`, and the unchanged
production client's local vitality poll reads register `0x0203B02C = 2` and emits
only `LocationChecks [3960301]`. These are captured messages, not server sends.
`VITALITY_CHEST_OLIVE_OCEAN` belongs to `REGION_OLIVE_OCEAN/ROOM_6_CHEST_1`.
Keep its existing `can_break_block` rule, separate RoomSanity check and outgoing
`ROOM_6_16` rule (`can_break_block` or `can_swim`). No Copy Ability or helper gate
is justified, and no production logic changes here.

The compact `olive-normal815-acceptance.json` pins private artifacts and scalars.
Source a1c2cff and integration base 7a417dc differ only in documentation/tests.
Independent review reconstructed all four production ROMs, inspected the used
harness and native source, compared relevant native function/object bytes, and
repolled the production client. It did not rerun the emulator or independently
reconstruct every collision-map tile. No ROMs, saves, raw frames or private paths
are included here.

## Boundary and clean setup

Seed 2 uses enemy-copy mode 1, all 25 allowed abilities, no-ability weight 0,
ability gating 0 and area keys 0. Only 17 startup room/position bytes differ
from each normally generated production ROM. Normal starts at the qualified
late 551 approach stored at (1168,288), then enters the actual door and loads
815 at (72,136.99609375), frame 1288. This is not new-game access, arbitrary
551 arrival, every incoming source, or an arbitrary door-shuffle proof.

All 2,861 consecutive gameplay samples, frames 1085–3945, retain ability 0 and
exactly the configured 1 or 6 HP, without damage. Helpers remain in 101. Eight
fenced four-byte client configuration writes occur at frame 1085, then writes
are sealed. Blank battery boot, no state restores, runtime ROM writes, gameplay
RAM writes, injected items, Phone or helper contributions are retained. Local
Blipper ordinary HP is 2 or 10 respectively (constructor HP 1 also occurs).
The route neither defeats nor copies it. This is not an all-policy/RNG claim.

## Moved block, intrinsic puff and timed crossing

Sustained Normal inhale moves silver star-stone block `0x088CCCFC` from x184 to
183.75 at frame 2336 and 182.75 at 2388. It remains solid and loaded, never
swallowed or spat. Its maintained contact holds lower switch (168,144), slot 1,
after Kirby leaves. Native `sub_081194DC` explicitly handles type 0x79/0x7D,
arithmetic-shifts coordinates by 8 and tests inclusive integer bounds. At 2388
the block rectangle [175,127,189,143] touches switch [161,135,175,143] at x175,
despite a superficial fractional-coordinate gap of 0.75. This is not a latch,
generic consumable payload or helper-count requirement.

The upper gate is crossed by frame 2562. Earlier body/puff attempts and an upper
F1 activation are part of the retained continuous exploration, not a shortest
route. Final Right+B at 3525 releases an intrinsic air puff from inflated Normal
at (265.99609375,72.84765625). The native airshot constructor creates a local
projectile at (277.62109375,72.84765625), frame 3526, with bounds [-5,-5,5,5].
At 3535 it reaches x304.62109375 and activates upper-switch slot 2 through 3546;
the slot releases at 3547. The lower gate continues its opening/closing animation,
not a permanent latch. Kirby drops around the platform's left edge, turns right,
and reaches (279.93359375,136.99609375) at 3600 with gate bounds [-8,-32,8,-16].
By 3610 x299.1875 is beyond the gate. An ordinary slide is observed at 3666;
the retained witness reports the lower F1/barrier continuation. At 3807 physical
chest contact at (432.63671875,136.99609375) changes event counter 0→1 with ring
entry `0x088CCC90`. The distinct underwater 553 exit is never used.

## Matched control and limits

The 6 HP / 100% control differs by exactly one input bit, frame 3525 keys 18→16,
omitting B. Every recorded state through 3525 is identical, including earlier
attempts. It never reaches x272 afterward, fails the lower-gate crossing and
ends at (242.734375,136.99609375), event counter 0 and no client check. This
supports the final puff's role in this sequence, not failure of every other
ordinary solution. The earlier mistaken major-chest poll is excluded.

No global Normal/silver-block/puff equivalence, reset persistence, health gate,
new AP edge, RoomSanity gate or coverage of other 815 exits follows. Preserve
other abilities' source/equipment requirements and unrelated room assessments.
