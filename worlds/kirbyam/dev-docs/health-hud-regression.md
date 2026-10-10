# Custom-capacity health HUD regression

A live PR931 build at `384e52b3` showed a detached health segment after one
Vitality Counter with a 3..7 HP plan. A read-only snapshot confirmed HP4/MAX4
and one owned counter. The native grant can temporarily use 6+count before
client reconciliation restores the custom capacity. This transient ordering
was inferred from source, not captured in a live frame trace.

The original USA renderer at `0x0803518C` writes only the current HP pairs and
endcap. Running its actual instructions at7/7 then4/4 leaves the previous
seventh-HP tile at `0x0600E4A0`, including on repeated4/4 draws. The routine
is byte-identical in the clean USA ROM and the observed package.

The fix wraps all three callers (`0x339B2`, `0x33BF2`, `0x35A62`). After the
original renderer, it clears unused paired cells to tile `0x184`, the blank
used by native HUD initialization at `0x080338B4`. The cleanup starts at
`floor(maxHP/2)+1`, preserving odd half-caps and even endcaps. Six cells cover
the supported1..10HP range. Demo flag0x10 and unsupported capacities preserve
the original behavior. The hook does not change health, rewards or saves.

## Reproduce instruction-level validation

Use an existing mGBA0.10.5 development library and a private clean USA ROM.
The optional probe applies the committed distributable patch in memory, executes
all three patched call instructions in a separate core, and never opens a save
or writes a ROM. It does not attach to a running game.

```sh
python worlds/kirbyam/test/native/run_health_hud_probe.py \
  --rom /private/path/usa.gba \
  --mgba-prefix /existing/mgba/usr \
  --library-dir /existing/mgba/usr/lib/aarch64-linux-gnu
```

Observed:2,850 instruction-level cases passed (all three sites, old and new
capacities1..10, signed dead/zero/damaged/fullHP, repeat redraw). Each case
compares the nearby tilemap with a clean native redraw and checks HP/MAX,
callee-saved registers and SP. Three demo-mode no-write cases also passed.
The unmodified prior patch fails this same probe as a negative control.

This is native-instruction validation with synthetic RAM, not gameplay or
save/load acceptance. The live game remains on the old ROM until an explicit
safe replacement. Recheck the HUD after a real receipt and normal door/save
transition on the fixed build; do not treat the old build's receipt as fixed
build acceptance. Global custom-capacity policy and PR947 remain separate.
