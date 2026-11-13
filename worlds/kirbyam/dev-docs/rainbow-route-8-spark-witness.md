# Rainbow Route Room 8: Spark route witness

The vanilla USA engine completed native **110 → 554** (Rainbow Route Room 8 → Room 9) with Spark. A continuous fresh-boot replay reached native 554 at frame 2268, with 6 HP and Spark still held. An otherwise identical replay replacing attack-only B inputs with neutral inputs remained in native 110. This is one positive route witness and a bounded negative control, not proof that every non-piercing move fails or that Spark solves every Beam gate.

## Fixture qualifications

- Vanilla USA base SHA-1: `274b102b6d940f46861a92b4e65f89a51815c12c`.
- Startup room and coordinates were redirected to the lower part of native 110. One enemy template at ROM offset `0x008B73F4` was replaced with a Spark essence (object type `0x93`, subtype 2) at (168,872). The original enemy is therefore absent in this fixture.
- No attack code, terrain/collision tiles, Bomb Block records, door records, enemy HP, or camera code was changed. No runtime memory writes or state reloads occurred in either continuous replay. Initial SRAM was blank.
- The fixture establishes physical attack/route feasibility after obtaining Spark, **not** a natural room-entry or randomized source-availability proof. Separate exploratory play acquired Spark from a native Sparky higher in Room 8, but that source sequence was not concatenated into the accepted lower-route replay.

## Target and result

The intended wall-separated trigger is the Bomb Block at tile **(13,57)**, pixel rectangle x=208..223, y=912..927. A permanent solid column at x=192..207 separates it from Kirby's left-side approach. Kirby was at x=185.996 with Spark, jumped out of the water, and activated Spark while above the waterline. The right-hand chain cleared. The route then crossed above the permanent column, descended the cleared right shaft, activated the lower Bomb Block at tile (14,63), and entered the right door at tile (12,68), arriving in native 554.

This distinction matters: the upper Bomb Blocks around y=520, and the exposed lower Bomb Block at (14,63), are not the wall-separated trigger at (13,57). Clearing an unrelated chain alone does not prove the Room 9 route.

The accepted replay used the source-derived short Spark envelope by approaching closely. It does not establish a maximum-range target hit, left-facing symmetry, all starting positions, or equivalence to Beam. The negative control changes attack inputs, so differences in animation/movement are expected; it is not a proof of exclusive necessity.

[Sanitized replay inputs, checkpoints and identity hashes](rainbow-route-8-spark-runtime.json) record both continuous runs. Local screenshots and full private fixtures are retained; full ROMs and save states are not published.
