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

The HUD fix was subsequently launched with the same seed and a copy of the
current native save after a read-only guard found all saved fields matched both
native copies. While the AP client was disconnected, a read-only probe showed
HP7/MAX7, native Vitality1 and fresh transport count/mask0. After reconnection,
HP4/MAX4, Vitality1, transport count3 and ownership mask1 were observed; the HUD
showed four units. The restarted client replayed the three prior history entries,
so this does not establish exactly-once transient effects across process loss.

## Native reload initialization

The seven-unit disconnected reload was an actual capacity defect, not stale
HUD tiles. The USA initializer calls NumVitalitiesCollected at0x3EB0E and adds6
at0x3EB12. A separate fix replaces that call with configured capacity and only
NOPs the add, retaining native HP/max stores. It reads a per-seed v1 ROM word at
0x15F690 (magic0xA901, maximum then minimum bytes). Existing color/gate/statue
words remain atF694/F698/F69C. Invalid configuration falls back to6..10;
valid ranges are1..10 with at most four upgrades, including resolved One-Hit
presets. Saved counts are capped for capacity calculation without modifying
save data. Native fresh Vitality grants use the same capacity and preserve
HP<=0; living fresh grants retain their existing full-heal policy.

Newly generated procedure patches include the health word. Older procedure
patches need regeneration or an explicit same-seed metadata-preserving rebuild
to embed custom bounds; changing only their base patch leaves default6..10
before client reconciliation. This does not enable PR947's extra Vitality items.

Independent packaged-ROM instruction checks passed1,536 initializer cases across
all40 ranges, eight saved counts and four Kirby pointers, plus malformed config
cases. Native stores, adjacent bytes, saved count and callee registers were
checked. These probes use synthetic RAM in an isolated real core; they are not
full gameplay/save-load acceptance. Live offline reload acceptance of this
additional initializer fix remains pending.
