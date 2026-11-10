# Mustard Room15: bounded Magic Meta Knight alternative

A separate `hub4_magic_entry` graph OR-composes with the unchanged Bomb, UFO
and Crash graphs on `switch_533_room16`, Room15/native 533 to Room16/native 325.
It requires raw guaranteed FOLEY → Magic, independent Rainbow Hub4 access,
actual finite acquisition and carried Magic. Owning the permission is not
being equipped. Native Magic remains `safe_to_gate`; the item becomes
progression only when the actual target entrance exists, the raw source is
guaranteed Magic and ability gating is enabled. Early explicit `start_inventory`
items are reconciled once after regions exist, without collecting an already
progression item twice. No base item classification or gateability is changed.

## Complete source, selection and timed crossing

Normal generation seed 12 uses shuffled mode 1 with the full 25-ability pool
and no-ability weight 0. Policy seed 16990593358183723736 assigns Magic/21 to
Foley at source table offset 0x35197E. The original finite Foley template
0x088C2714, native type 34, is at (224, 64) in 533. The graph checks the raw
source before permission filtering, so a mixed or failable live-random grant
cannot become a guaranteed route merely because only Magic is unlocked.

The accepted continuous inputs independently enter 534 from native 590 at
frame 1157, clear its lower obstacle with real inhaled/spat payloads and its
upper obstacle with air puffs, then enter 533 at 2697. The lower/right/up
approach and source viewport reset are retained. The original Foley is observed
alive at 4162 with copy field 21 and HP 2/10. Inhaling and swallowing its finite
payload gives Magic at 4377. Generic 533 or 534 reachability is not this ingress.

At 4404, Kirby carries Magic at (245.51953125, 72.99609375). Seventy Left frames
reach the dry v4 casting pose (170.21875, 135.80859375). B at 4474 begins casting;
the settled camera is (50.21875, 55.80859375). The player watches the rendered
roulette sword icon in the upper-right sector and presses A. This is an enacted
visible selection strategy, not permission to receive a lucky outcome. The
accepted controller reads only rendered RGB pixels for its stop decision.
Layout, angle, RNG, outcome and equipment are not selection inputs.

In the baseline, the visible cue and A input occur at 4534, Meta Knight outcome
4 resolves at 4660, and native task 0x08083B05 creates the local effect at 4723.
Its parent and `kirby2` both identify player 0 at 0x02020EE0, room 533, with
category 0x2000 and without conversion category 0x8000. First switch contact
occurs only on the third sweep, at 4862, effect counter 140 and center x
306.21875. The actual switch contact pointer resolves to this player-owned
Meta Knight task. Switch template 0x088C26F0 is linked slot 1, parameter 0;
the solid x 240 to 287 structure still separates caster and switch.

Gate template 0x088C26CC starts opening at 4864. Magic is consumed to Normal
at 4894. The gate finishes opening at 4907, starts closing at 4908, and is
closed by 4951. Normal fully crosses left of it at 4941, x 138, y 101.00390625.
The fixed recovery schedule is 320 neutral frames after A, then 120 Up+Left
frames with fresh A presses on alternating frames. No hidden recovery-state
trigger is used. Normal then flies directly up the clear x 80 to 95 column,
right and down to the actual 325 ledge, entering at 5221 and settling to 5269.
The graph spends Magic on this exact operation and requires Normal throughout
the tail and terminal transition. It never grants a persistent opened event.

## Roulette and native coverage boundary

[The sanitized acceptance manifest](mustard-room15-magic-acceptance.json)
records the frozen v4 packet, exact raw hashes and 44 independently validated
cold runs: 36 positives and eight controls. The 12 endpoint/control cases cover
actual HP 1/6 × enemy health 100%/500%, each with a positive, no-cast control
and non-Meta conversion control. All use the baseline layout 3 timing. The
other 32 ordinary-wait positives use actual 1 HP and 100% enemy health and
cover all ordinary layouts 0 to 4. This is not the Cartesian product of every
layout and health setting, and not a health continuum. All sampled HP values
remain equal to the configured endpoint, including the controls.

With `gUnk_0203AD10 & 4` clear, the native selector's 16 entries select only
layouts 0 to 4. With it set, the four entries are 5, 6, 7, 5. Source recurrence
shows a controllable Meta Knight stop in all eight layouts, but only the
ordinary branch has native cast/recovery/traversal acceptance. Alternate-mode
layouts 5 to 7 are source-only and are not promoted to native or multiplayer
proof. The successful after-press icon angles are 960, 964 and 972, inside the
source-derived interval 886 to 1013. Diagnostic angle reads verify the visible
strategy; the player does not select by those hidden values. Waiting variations
are separate cold tests, never repeated draws from the finite Foley.

No-cast controls replace only the B input at 4474 with neutral. They retain
Magic and never activate the switch, open the gate or leave 533. Conversion
controls move the roulette A input from 4534 to 4541, a two-frame input-file
difference. They consume Magic and create outcome 1's category 0x8000 effect,
but never activate this switch or leave 533. These controls do not exclude
every other conceivable Magic outcome, pose or body route.

## Fixture and integration limits

Each fixture is built through normal production generation and patching, with
only startup room/position bytes changed: player 0 begins in 590, other Kirbys
in 101. This isolates the independently required Hub4 ingress, not a full
new-game route to Hub4. Every run cold-starts with a blank 32 KiB battery. The
actual client performs eight guarded configuration writes at frame 1085, before
movement, then the write fence closes. No gameplay RAM/ROM writes, equipment
injection, RNG manipulation, nonblank save import or emulator-state load occurs.
Other Kirbys remain in 101. Remote spell broadcasts do not contribute an actor
or attack in 533; every accepted local Meta effect is player0-parented.

Native fixtures use ability gating and area keys off. Host regressions cover
permission, progression, source policy, area-key/statue/RoomSanity options,
starting-inventory lifecycle, fill and accessibility separately. They are not
a native gate-on replay. Raw ROMs, saves, screenshots, sprite samples and trace
files remain private; this checked-in packet contains metadata and hashes only.

Only frozen v4 is accepted. Earlier Crash-pose and slow-recovery attempts,
v1/v2 air-puff tails and v3's gate-margin failure remain superseded. The v4
pose and direct upward tail are not silently replaced with those failed inputs.
No general Magic small-switch, Bomb Block, F1/F6, rope or fuse provider, other
exit, renewable source, helper route or general RoomSanity gate is added.

Source revision 7d969fbce14fdc838d2c1ea01389717fb96c3189:
[roulette layouts and update](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/code_0806F780.c#L14956-L15149),
[casting and consumption](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/kirby.c#L20951-L21182),
[Meta Knight object](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/code_0806F780.c#L7960-L8076),
[small-switch branch](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/asm/big_small_switch.s#L729-L1013),
and [door animation](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/vert_sliding_door.c).
