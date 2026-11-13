# Carrot Castle 733 Yellow Paint: entry-bound UFO witness

## Scope and graph boundary

`bomb_733_yellow` applies only to `MINOR_CHEST_SPRAY_PAINT_02` / 3960501,
owned by `REGION_CARROT_CASTLE/ROOM_5_16` (native733). Independent AP access
is `REGION_CARROT_CASTLE/ROOM_5_14` (native720), **not native719**. The
physical fixture starts beside719's actual720-bound door; it does not prove
that every upstream719 compartment reaches that door. Preserve the existing
719→720 `can_climb && can_break_block` qualification. Those permissive labels
are existing assumptions within this core witness. A separate later Normal
170→719→720 segment is recorded in `carrot-yellow-ufo-upstream-witness.md`.
It neither moves this graph boundary nor proves continuous170-to-Yellow
completion; all170 arrivals and timing composition remain unverified.

The installed witness is `room14_entry`; its scoped attack capability is
`bomb_733_yellow_ufo_top_charge`. Carry-only route requirements preserve the
upper UFO → Normal ladder → lower UFO sequence without treating every carry
edge as an attack.

The finite source model requires a guaranteed `SPARKY -> UFO` grant and
permission to acquire it when ability gating is enabled. Inventory permission
is not equipped UFO. The accepted native configuration is mode1, production
seed8, full25-ability pool, policy seed5662892934360856578, no-ability weight0,
ability gating off and Area Keys off. This is not a proof for arbitrary mixed
or failure-weighted outcomes, retries, or another ability. A future qualified
Phone alternative belongs as an OR alternative to this same target, not a
room-wide unlock or a second independently required gate.

## Resolved ingress and two original sources

The later packet contains four independent Normal ingress runs and twelve
complete runs: actual HP1/6 × enemy health100%/500% × positive/no-shot/medium
charge. The identical complete controller schedule succeeds at all four
health settings. Its directed route is:

1.719 door(14,3) →720 far-right spawn(119,8), frame1172.
2.720 floor transition(26,11) →734 upper spawn(14,5), frame3844.
3.734 door(2,4) →720 left spawn(11,8), frame4136.
4.720 door(2,7) →730 top spawn(29,4), frame4313.

Normal avoids the original Foley drops and Bronto Burt swoops, passes above
Shotzos, lands on the original small switch at(600,96), walks through its
sliding door, then falls through the narrow floor-star gap. Neither720-left
bomb-chain tile activates.734 access is reached physically, not assumed in
advance. Inhaling and spitting a bird is not swallowing a copy ability.

Inside730, original upper Sparky `0x088D4FC0` at(344,296) supplies UFO at
frame5450. UFO traverses the directed maze and moving Gordo to the hidden
selfdoor. A180-frame wait at the upper-right ladder compartment lures the
lower enemy away before descending. Intentional Select discard makes Kirby
Normal at6830 because UFO cannot use the ladder. Original lower Sparky
`0x088D4F9C` at(344,664) supplies UFO at6994. This second UFO is retained
intact through733 arrival and chest collection. Both original sources have
type25, copy field14 and HP4/20 at the two tested enemy-health settings.
It is not uninterrupted carry from the upper source. Template scans are
observations, not proof that stale references remain live objects.

## Selective lower trigger and physical receipt

At the legal attack pose(217.99609375,102.99609375), hold B for160 frames
starting8071 and release. The top-charge shot clears only lowerF1(21,6) at8257.
UpperF1(18,2) remains241 on every733 frame. Lower's chain removes the chest
cap and right wall. Kirby flies through the one-way ledge, crosses above the
intact upper trigger, descends through the cap and presses Up at the chest.
Physical chest `0x088D3DD0` at(344,56) sets chest bit80 and event counter1 at
8613. Final frame8671 has the exact captured real-client message
`LocationChecks [3960501]`; native spray bit1 remains suppressed. The object's
list index5 is not its native chest flag.

Matched controls replace only the8071 target window:160 idle frames, or90 B
frames plus70 idle. Both preserve HP and lower UFO but leave both F1s intact,
chest bit80 false, event counter0 and no client check at all four settings.
Charge level and legal attack geometry matter; generic ranged possession is
not sufficient evidence.

## Earlier packet and limitations

The retained earlier twelve cases are separately labeled in the JSON. They
start at decoded734→720 **left-arrival coordinates**, not at719 or generic720
access. Normal boot settles at(152,105.44); the actual720→730 transition occurs
at1200. Upper UFO acquisition2337, intentional discard3734, lower acquisition
3938, lower trigger5200 and chest5556 belong to that earlier schedule only.
Its6HP schedule aligns the hidden selfdoor by moving Up one frame earlier and
adding one idle frame. Blindly reusing earlier timing with the longer ingress
caused a hit; rejected schedules are not accepted evidence.

Native Normal air-puff/slide lower-first probes left both triggers intact.
Upper-first air-puff activates the upper chain, but tested Down, jump+Down and
slide did not return through the one-way ledge to the lower corridor. These
are finite failed probes, **not exhaustive impossibility**. No helper, Phone,
Beam or Spark source-to-chest alternative is established here. Only discrete
100% and500% enemy health were replayed.50–99% and101–499% were not replayed
and cannot be inferred by interpolation.

## Retained evidence and portable replay recipe

`carrot-yellow-ufo-source-runtime.json` retains sanitized observed final
outcomes, all28 case ROM/per-frame hashes, both packet hashes, the complete
new positive input schedule and its matched control replacements. It is a
compact evidence contract, not raw frame traces or an executable replay.
Contract tests validate the retained records; they do not cold-boot an emulator.

For an independent replay, obtain a lawful USA base ROM with SHA1
`274b102b6d940f46861a92b4e65f89a51815c12c`, generate the normal production seed8
configuration above, and apply the production procedure patch. Record its
hash and every fixture difference. Change only startup room/coordinates to
719 at(232,56); do not edit sources, target geometry, policy or enemy objects.
Cold-boot a blank battery. At1085, before directional movement, allow exactly
eight configuration words from the real
`KirbyAmClient._sync_enemy_copy_ability_runtime_config`, then seal external
writes. Replay the retained input tuples; keys use GBA bitmasks (A1, B2,
Select4, Start8, Right16, Left32, Up64, Down128). Repeat at HP1/6 and enemy
health100%/500%, with both target-window replacements and standalone ingress
ending4357. Record actual HP/maxHP each gameplay frame, ability phases,
AI0/humans1, source fields, transitions, target order and physical chest/event
receipt. Capture the real client output locally without server transmission.
No gameplay RAM writes, state restores or helpers are allowed.

Native source reference: `7d969fbce14fdc838d2c1ea01389717fb96c3189`.
Relevant native implementation: chain propagation `src/code_0800E0E4.c`,
collision/replacement and ladder exclusion `src/code_080023A4.c`, UFO charge
and physical chest interaction `src/kirby.c`, chest flag indexing `src/chest.c`.
ROMs, saves, screenshots, raw traces, private scripts and filesystem paths are
not distributed in this witness. Hashes identify retained evidence; hashes
alone are not a fresh independent replay.
