# Enemy health scaling (Issue #880)

`enemy_health_multiplier` is a generation-time percentage option. `100` is
vanilla HP; values below or above 100 reduce or increase health respectively.
The supported range is 50–500 and normal Archipelago `Range` weighting works,
for example:

```yaml
enemy_health_multiplier:
  150: 50
  200: 30
  300: 20
```

## Why this is a patch-procedure step

KirbyAM's ordinary per-seed ROM changes use token writes, but token operations
cannot multiply an existing signed 16-bit ROM value. Hard-coding a second copy
of every vanilla HP value would be brittle and unnecessary.

Instead, each `.apkirbyam` contains the resolved percentage as a two-byte file.
The procedure is:

1. apply the shared `base_patch.bsdiff4`;
2. scale enemy-health tables using the actual resulting ROM bytes;
3. apply ordinary per-seed token writes.

This keeps the shared payload/base patch independent of the option and means
`100` leaves every HP byte unchanged.

## Native tables

The supported North American ROM uses three native sources:

| Table | File offset | Shape / usage |
| --- | ---: | --- |
| `gUnk_08351530` | `0x351530` | 27 object-type rows × 4 human-player difficulty columns for `ObjType38To52` |
| `gUnk_08351608` | `0x351608` | 4 subtype rows × 4 difficulty columns for Dark Mind form 1 |
| `gUnk_08351648` | `0x351648` | regular Object2 metadata; HP is signed 16-bit at record `+0x04`, record size `0x18` |

The HUD converts current HP into meter fill in `sub_08034E14` using three
additional Q8.8 coefficient tables. Each coefficient is scaled using its
corresponding original HP divided by the actual rounded/clamped HP, so the
meter continues to show the fraction of the scaled maximum HP:

| Table | File offset | Shape / usage |
| --- | ---: | --- |
| `gUnk_083513E8` | `0x3513E8` | one regular-enemy coefficient for each type `0x00..0x37` |
| `gUnk_08351458` | `0x351458` | 27 miniboss/boss rows × 4 human-player difficulty columns |
| `gUnk_08351628` | `0x351628` | 4 Dark Mind form-1 rows × 4 human-player difficulty columns |

Only regular object types `0x00..0x37` are scaled in `gUnk_08351648`; native
type `0x38` (`OBJ_MR_FROSTY`) begins the miniboss/boss range and reads the
dedicated boss table.

All positive signed-16-bit values in the health slots are scaled with integer
half-up rounding. Zero and negative values are preserved as sentinel/non-health
data. Results clamp to `0x7FFF`.

## Rounded HP and native meter limits (Issue #1028)

The native meter truncates `current_hp * coefficient` to signed 16-bit,
shifts right by eight, rounds up for a nonzero fractional byte, and stores
the result as a signed byte. A positive result therefore requires a product
no greater than `127 * 256`, not merely `0x7FFF`.

Scarfy, falling Scarfy, and Bomber have 1 HP. At 50%, HP still rounds to 1;
dividing their coefficient by 50% produced `0x8000`, interpreted by the meter
as -128. When the target becomes zero after damage, the meter animates upward
and repeatedly requests the same sound as Kirby's healing.

Coefficients now use the nearest integer to
`native_coefficient * native_hp / scaled_hp`. The result is capped so its
rounded full-health fill cannot exceed the original fill or 127. This also
prevents a nearest-coefficient rounding step from overfilling the native
64-pixel meter. A Q8.8 coefficient cannot always represent the original fill
exactly at large scaled HP; its remaining error is bounded by one coefficient
step. Zero coefficients and coefficients paired with sentinel HP are preserved.
The 100% option remains byte-identical. For synthetic HP too large for any
positive safe coefficient, zero suppresses the meter rather than wrapping.

Tests cover every integer percentage from 50 through 500, every slot and
difficulty column in all three table layouts, the one-HP enemies, sentinel
values, both signed boundaries, and native signed-meter monotonicity.

An optional probe checks all actual table entries and executes the native
Thumb meter routines for Scarfy, falling Scarfy, and Bomber at all 451 settings:

```sh
python worlds/kirbyam/test/native/run_enemy_meter_probe.py --rom /private/clean-USA.gba
```

This requires `bsdiff4` and Unicorn. It verifies the clean USA hash, applies the
committed base patch in memory, and emits only a JSON summary. It checks every
current-HP value in each scaled entry. Rendering and sound playback are
intercepted; the probe counts sound requests and does not certify audible
playback or a full gameplay encounter.

## Native-consumer consistency

Scaling the source tables rather than only live `Object2::unk80` values means
any native code that reads those health tables sees the same per-seed values.
All four human-player difficulty columns are changed together, and the inverse
meter-coefficient scaling keeps each meter proportional to its enemy's scaled
maximum HP.

## Runtime impact

None. This feature does not add mailbox state, payload hooks, or per-frame work.
The generated GBA already contains the scaled HP and meter-coefficient tables
when play begins.
