# Cabbage Room 6: finite Doo-to-Smash source witness

## Accepted result

A normally generated shuffled seed assigns the actual Cabbage Room 6 Waddle Doo to Smash. Continuous controller inputs acquire it, carry it to the Chocolate Spray Paint barrier, open the intended Bomb Block with rising Up+B, and open the physical chest without damage or losing Smash.

The same inputs pass four complete production AP-ROM runs: player HP **1 and 6**, each at **100% and 500% enemy health**. These are actual generated health configurations, not inferred one-hit safety or harness HP changes. Every frame from 1085 through 4900 was sampled, with constant HP and no ability loss after acquisition.

## Source, arrival, target, and event

- The startup fixture starts in native591, Cabbage Hub2. Controller input triggers the native591→517 door transition at frame1109. At frame1158, Normal Kirby is at (696,296.9961).
- Actual native Waddle Doo: template **0x088CA04C**, type18, original position (528,264). Read-only source scans confirm that exact template. Its walking copy field is still native Beam7, but the complete production swallow-restoration path grants shuffled **Smash22 at frame1939**. The ROM table byte at0x3517FE is22 and source bitmap bit18 is enabled.
- The relevant target is **MINOR_CHEST_SPRAY_PAINT_12 /3960511** only. Intended F1 is tile(14,7); linked F2 cells are (15,7), (15,8), (16,8), (17,8), (15,9), (16,9), (17,9).
- At frame3129 the F1 clears during the **rising** Up+B attack, animation107, at (185.9961,111.3711). All seven F2 cells then clear by frame3179; they have not yet cleared on frame3129. This does not attribute success to the landing shockwave.
- At frame4421, chest57 opens and the production payload records exact chest source **0x088CA0B8** in its minor-chest event ring, counter1.
- The real initialized KirbyAmClient reads that ring and produces **LocationChecks [3960511]**. The test captures this message locally; it does not submit to an AP server and does not claim server acknowledgment.
- Native spray11 stays false intentionally: the production AP-owned chest hook suppresses its native reward until AP item delivery. Physical chest opening plus exact location/event identity is the acceptance criterion, unlike the vanilla Beam witness's native spray receipt.

## Production recipe and write accounting

The checkout used was **a110c96260b52205fb1b7013c7ac95b1d41fc6b9**. The companion manifest records base-patch, original-USA-ROM, generated-patch, production-ROM, fixture-ROM and emulator-bridge hashes.

Full `Generate.main` / `Main.main` generation uses seed173 and the normal 25-ability pool. The generated policy seed is2904965844187189627. YAML sets shuffled mode1, ability gating0, no-ability weight0, Area Keys0, the tested enemy-health percentage, and equal minimum/maximum player health. No singleton whitelist is supplied. Other source-policy fields remain their normal generated defaults.

`KirbyAmWorld.generate_output`, `rom.write_tokens`, and `KirbyAmProcedurePatch.patch` supply the complete base patch, tokens, source-policy bitmap, enemy-health scaling and health configuration. Only afterward does the startup fixture change the four room words at0x2D8CB8 to591/101/101/101 and coordinates at0x2D8CD0 to(40,136) plus(48,80) for each AI. The manifest includes every changed byte. Each replay cold-boots from a blank battery.

The production payload begins in mode0. At frame1085, before route movement, the real client's `_sync_enemy_copy_ability_runtime_config` synchronizes the actual generated slot data with an empty received-item list. There are **eight logged four-byte configuration writes**, not zero writes:

| Address | Little-endian data | Purpose |
|---|---|---|
| 0x0203B064 | 01000000 | Mode1 |
| 0x0203B068 | 7b916b4b | Policy seed low |
| 0x0203B06C | 0b835028 | Policy seed high |
| 0x0203B070 | 00000000 | No-ability weight |
| 0x0203B074 | feffff03 | Normal allowed-ability mask |
| 0x0203B0B0 | 00000000 | Gate mask |
| 0x0203B0B4 | 00000000 | Empty-item unlock mask |
| 0x0203B078 | 00000000 | Runtime counter reset |

All writes have guard_failed=false and the production client method as origin. There are **no subsequent harness writes**, no equipment/HP/position/terrain/source injection, and no save-state restoration. The portable replay rejects any other write or any write after synchronization.

## Controls and attribution

1. **Exact attack-window negative:** identical inputs through frame3119, then Up-only64 instead of Up+B66 for60 frames. It ends at3179 with F1=241, all seven F2=242, no chest/event/check, HP6 and Smash retained.
2. **Full-route no-target-attack negative:** removes B from the target attack and settling inputs at starts3119,3179,3220; all later movement/collection inputs are unchanged. At4900 the barrier remains intact, no chest/event/check exists, and HP6 and Smash remain.

A diagnostic run that omitted only the initial Up+B but continued every later B opened the target with a later **grounded B** at frame3221. It is not a negative. The accepted exact-window negative isolates rising Up+B; the accepted full negative removes every later target-opening B as well. It does not imply Up+B is the only Smash move capable of opening this target.

## Reproduction and publication boundary

Retained compact review evidence:
- `cabbage-smash-source-witness.md`: this qualified report.
- `cabbage-smash-source-runtime.json`: sanitized metadata, full compressed inputs, six accepted run outcomes, configuration-write records, source excerpts, hashes, controls and event-to-check mapping.
Portable production builder and controller replay scripts are reviewed separately. They are not part of this bounded rule change.

Private only: original/generated ROMs, generated archives and AP patches, battery files, full source scans/raw runtime traces, exploratory failed attempts, auth-bearing raw logs, and screenshots. Only this report and the sanitized manifest are retained with the rule change; none of those private artifacts is included.

## Scope limits

This is one finite actual-source route, not proof of reaching Hub2 from game start. No reset/respawn guarantee, renewable source, random eventual draw, RoomSanity reachability, other exit, global Smash equivalence, or untested enemy-health interpolation follows. Gating is off in executed ROMs; gated ownership logic is covered separately by `test_cabbage_smash_gate.py`, not by a gating-on native replay. Existing Beam evidence remains unchanged.

## Installed rule boundary

The Chocolate chest target has a separate Smash-only carry graph alongside the existing Beam graph. Applicability requires a guaranteed singleton WADDLE_DOO grant of Beam or Smash. Both start Normal and require independent Cabbage Hub2 access. The Smash graph requires its real finite source, and gating-on additionally requires Smash permission; inventory alone is not equipment. No source renewal, RoomSanity, Area-Key or unrelated-exit rule changes are implied.
