# Mustard Room15: camera-scoped Crash alternative

This complete graph is OR-composed with Bomb and UFO inside `switch_533_room16`. Only guaranteed singleton FOLEY→Crash enables this alternative. Native Foley grants Bomb, not Crash. Finite mixed/failable random grants are not retries. Crash permission becomes progression only when this source condition applies and ability gating is enabled; inventory never supplies equipment.

## Native source and pose

Normal generation seed 29, full 25-ability pool, shuffled mode1, policy seed 14642711172500888381 assigns original Foley template 0x088C2714 at(224,64) to Crash. Source table 0x35197E contains 24. Normal enters through actual Rainbow Hub4/native 590→534→533, clears 534 using real payload/spit-star and air-puff actions, and acquires the finite Foley at 4377. Generic 533 access cannot replace independent Hub4 access.

Carry Crash to(208.75,145.6836), viewport(88.75,65.6836)..(328.75,225.6836), and begin the attack at 4455. Its screen object overlaps the actual small-switch rectangle x 305..319,y 135.996..143.996 at 4525. Crash pauses the room during startup. At 4610 it is consumed to Normal and the room resumes; the gate opens, then closes. Normal crosses left of the gate at 4681, uses the observed air-puff/flight sequence past the left obstruction, and enters actual 325 at 4906. The graph spends Crash explicitly, requires Normal for the remaining movement and actual 325 transition, and grants no persistent switch event.

This is a camera-valid target witness, not a whole-room range claim. The offscreen control uses Crash at(166,152.996), viewport x 46..286, short of the switch's left edge 305. Crash is consumed but the switch remains inactive and the gate closed. No other camera pose, switch template, room, Bomb Block, environmental Foley explosion or Phone helper inherits this capability.

## Validation boundary

The compact [acceptance manifest](mustard-room15-crash-acceptance.json) records four continuous positive runs: actual 1 HP and 6 HP, each at 100% and 500% enemy health. All reach 325 as Normal with unchanged HP. 6 HP event timings/coordinates match 1 HP. Matched no-trigger controls at 100%/500% and the offscreen100% control are **1 HP only**, not 6 HP controls. Only these discrete health settings were exercised. Removing the initial trigger frame leaves Crash equipped and never activates the switch; subsequent air-puff inputs remain unchanged.

Fixtures are normal production AP patches applied to the verified USA ROM; only startup room/positions differ. Eight guarded actual-client runtime configuration writes occur before movement. There are no gameplay RAM/ROM writes, nonblank save imports, injected equipment, restores or helpers. Native fixtures use ability_gating=0 and area_keys=0. Host-side regressions separately test permissions, conditional classification, area keys, source applicability and world wiring. Raw ROMs and traces remain private.

Native source revision 7d969fbce14fdc838d2c1ea01389717fb96c3189: [screen attack creation/update](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/code_0806F780.c#L7678-L7745) registers viewport-centered bounds±120×±80 without a Bomb Block tile-scan bit; [switch contact branch](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/asm/big_small_switch.s#L729-L1013) accepts this interaction before damage immunity; [Crash completion](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/kirby.c#L20752-L20958) releases pause and assigns Normal. Runtime observations qualify the exact timer/crossing, not a generic timer inference.

Broad PR 1052 coverage remains unfinished. Existing Bomb/UFO alternatives, unrelated targets and options are unchanged.

Continuous HP observations cover gameplay from frame 1085. Full per-frame coordinate/state traces begin at frame 4374; earlier approach evidence comprises input, transition and checkpoint records.
