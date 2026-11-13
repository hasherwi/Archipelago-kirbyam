# Cabbage Cavern Room 6: Chocolate Spray Paint wall gate

## Verified result

**Beam, Spark, Ice breath, and Smash Up+B each open the intended Chocolate gate and permit collecting the native chest.** All four positive witnesses are fresh-boot, continuous controller-input runs. Matched controls omit the tested attack's B input and retain the target and linked blocks. Beam, Spark, and Ice controls also repeat the collection-route inputs and do not obtain the chest or paint. The Smash control ends after the gate test.

This is native physical feasibility evidence, not proof of an available randomized ability source, AP item delivery, or every other use of these abilities. No global equivalence or maximum-distance claim follows.

## Exact target and receipt

- Native room 517, Cabbage Cavern Room 6.
- Intended Bomb Block: collision tile (14,7), code **F1**, covering x224–239, y112–127.
- Linked **F2** cells: (15,7), (15,8), (16,8), (17,8), (15,9), (16,9), (17,9).
- Native Chocolate chest: template ROM offset 0x8ca0b8, object type 0x80, reward subtype 0x1f, position (320,136), chest index 57. Source `chest.c` maps reward 0x1f to spray index 11.
- All four positives change F1 and all seven F2 cells to zero, then set both native chest57 and spray11 receipt bits. Controls keep F1/F2 and leave both receipt bits false.
- Receipt reads: chest57 is bit1 at 0x02038967; spray11 is bit11 in u32 at 0x02038974. These are original-game treasure bits, not randomizer receipt addresses.

## Reproduced approaches

| Ability | Controller attack and legal approach | First observed F1 clear |
|---|---|---|
| Beam | Face right at (185.9961,120.9961), jump for 3 frames, then B. Attack begins at y109.4414. | Frame1238, Kirby (185.9961,108.7617). |
| Spark | Jump onto the small upper-left step, then walk into its right wall. Hold B at **(201.9961,88.9961)**. | Frame1344, same coordinate, 6 frames after starting B. |
| Ice | Stand facing right at **(185.9961,120.9961)** and hold ordinary B breath. No enemy is frozen or kicked. | Frame1222, same coordinate, 16 frames after starting B. |
| Smash | Stand facing right at (185.9961,120.9961), use Up+B Final Cutter. | Frame1216, Kirby (185.9961,111.3711), animation107. |

**Smash attribution limit:** the target clears during the rising part of the move, before landing. This witnesses the complete Up+B move, not specifically the landing shockwave or its maximum range.

**Spark approach matters:** the ordinary left-wall position is too far in the tested direct hold, while the higher, closer step succeeds. Exploratory state-restored probes gave inconsistent corner outcomes and are superseded by the continuous fresh-boot positive/control pairs. Do not cite those probes as impossibility evidence. The initial draft filename containing “bounded-negative” predates the successful continuous replay and is not an accepted result.

Damage hitboxes and terrain-destruction scanning bounds differ. These measured room witnesses do not replace source-derived range analysis. Frozen-enemy Ice projectiles and other attacks remain untested here.

## Fixture and integrity limits

- Private authorized USA source ROM SHA1: 274b102b6d940f46861a92b4e65f89a51815c12c.
- Original ROM remains unchanged. Each private test ROM changes only the four startup-room entries, the startup coordinates, and one native Bronto Burt template into a nearby ability essence.
- Fixture starts the player in room517 at (176,112). The essence is at (168,104), substituted for the Bronto Burt template at 0x8ca0dc. Beam uses type0x92/subtype0; Spark type0x93/subtype2; Ice type0x93/subtype1; Smash type0x93/subtype4.
- No attack code, terrain, enemy HP, rewards, or chest fields are modified. No runtime memory writes, save-state loading, or state rewinds occur in accepted runs. Each begins with a fresh 32-KiB FF battery save.
- After gate activation, the route returns through the lower-left passage, flies into the opened chamber, and opens the chest with Up. One native enemy collision later lowers HP to5 and loses the ability; this occurs after the intended gate is opened. All positive receipts are still obtained by controller inputs.
- Essence/start substitution isolates physical feasibility. It does not establish a natural or randomized source path to the tested ability.

## Reviewed evidence

[Sanitized runtime manifest](cabbage-room6-runtime.json) includes all eight runs, ROM/bridge hashes, fixture byte differences, run-length-compressed controller inputs, checkpoints, native target/receipt outcomes and first-clear frames. Detailed per-frame traces and screenshots are retained privately. The fixture driver validates the original ROM, allowlisted setup changes, zero initial receipts, target changes and final receipts.

No full ROMs, battery saves or save states are published. Source-derived envelopes and these finite room witnesses remain distinct.
