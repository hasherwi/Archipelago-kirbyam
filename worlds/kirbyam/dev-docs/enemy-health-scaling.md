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

Only regular object types `0x00..0x37` are scaled in `gUnk_08351648`; native
type `0x38` (`OBJ_MR_FROSTY`) begins the miniboss/boss range and reads the
dedicated boss table.

All positive signed-16-bit values in the health slots are scaled with integer
half-up rounding. Zero and negative values are preserved as sentinel/non-health
data. Results clamp to `0x7FFF`.

## Native-consumer consistency

Scaling the source tables rather than only live `Object2::unk80` values means
any native code that reads those health tables sees the same per-seed values.
All four human-player difficulty columns are changed together.

## Runtime impact

None. This feature does not add mailbox state, payload hooks, or per-frame work.
The generated GBA already contains the scaled tables when play begins.
