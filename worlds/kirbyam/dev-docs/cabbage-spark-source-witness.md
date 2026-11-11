# Finite original-source Spark witness for Chocolate

This bounded witness supports only `bomb_517_chocolate`, graph
`hub2_spark_entry`, and `MINOR_CHEST_SPRAY_PAINT_12` (local location 3960511).
The original Waddle Doo template `0x088CA04C` at (528, 264), native type 18
and copy field 7, is a finite source, not a renewable Spark supply.
Generation seed 22 uses the full 25-ability pool and raw policy seed
14282527318440564224. Its guaranteed Doo assignment is Spark (15).

## Recorded route and mechanism

Independent Hub2 access is assumed. Normal crosses the real 591 to 517 door
at frame 1109, consumes the original Doo, and actually acquires Spark at 1939.
The source remains absent afterward. Spark clears its own corridor F1 at
2013 and is retained without player damage through the full route. Helpers
remain in native room 101. Fresh saves and startup room/coordinate fixtures
are used; the only eight configuration writes occur at 1085, before gameplay.
There are no later gameplay writes or restored states.

The attached Spark field strikes from the upper step at
(201.99609375, 88.99609375). Its callback is `0x08074C1D`, parent player is
`0x02020EE0`, scanner bounds are (-26, -22, 26, 30), and mask is
`0xA0000403`. Integer scanner rectangle (175, 66, 227, 118) overlaps target
F1 tile (14, 7), pixel rectangle (224, 112, 239, 127). Native creation and
update are in `src/code_0806F780.c:2781-2825`; scanner bounds differ from
its damage bounds. The chain callback `0x0800E27D` identifies the field as
parent. This is frame-sampled/source-reconciled attribution, not CPU tracing.

All four HP1/6 by enemy100/500 positives clear target F1 at 3510, finish the
seven linked F2 cells at 3540, and physically open chest 57 at 4334. Each has
3488 samples covering 1085 through 4572 inclusive. Four equally long controls
omit only B during [3504, 3534), match the positive state through 3504, preserve
source acquisition and corridor action, and retain HP and Spark while leaving
the target, linked cells, chest and event sealed. This is not arrival-only proof.

The gated Spark-only permission run completes the full route. Empty permission
stays Normal through 2007 (923 samples); it is only an acquisition negative.
Spark inventory is permission, not equipment. The exact chest event source is
`0x088CA0B8`; the unchanged client's local poll emits only location 3960511.
No remote submission or receipt is claimed.

## Review and limits

The independent review audits stable enemy identities, including slot replacement.
Except for consumed Doo, observed health reductions end at HP1 with removal flag
`0x1000`, consistent with `src/object.c:180-212`, not non-source combat damage.
These endpoint observations do not prove intermediate-health or all-RNG behavior.
No global range, wall-piercing, arbitrary arrival, other target, helper route,
exit, or RoomSanity guarantee follows. Host access must remain independent and
raw-source permission filtering must not create circular source availability.

`cabbage-spark-acceptance.json` contains sanitized scalars recomputed from frozen
states, controller-command comparisons, tile changes and local client results.
Its hashes pin the retained private packet and independent accepted review;
no ROM, save, raw trace, controller stream or private filesystem path is included.
Repository tests check this bounded contract and current target ownership; they
do not rerun the emulator or establish new runtime evidence.
