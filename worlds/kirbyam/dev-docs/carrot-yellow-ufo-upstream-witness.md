# Separate Normal approach through native719

## Result and boundary

A separate ordinary route is now verified from beside native170's original
upper-plateau door, through its real lower-right entry into719, through719's
maze and directed self-door, and into720 at the actual far-right arrival.
Four positive runs and four matched controls cover actual HP1/6 and enemy
health100%/500%. Every run stays Normal, solo and no-hit.

This does **not** change `bomb_733_yellow` or its independent AP access at
`REGION_CARROT_CASTLE/ROOM_5_14` / native720. The new prefix has not been
concatenated with the accepted source-to-Yellow route. Its different enemy
phases need testing before claiming continuous170-to-Yellow completion.
The fixture also does not prove all entrances into170 reach its upper plateau.
The native170/719/720 AP names are respectively Room5/Room7/Room14 in Carrot
Castle. Existing AP edges and their requirements remain unchanged.

## Directed ordinary route

- Start beside170 door tiles(12/13,5). The private fixture changes only startup
  room/coordinates to170 at(200,80); normal startup settles at(184,73.441).
  At1198, the real door enters719 at spawn(43,29), pixel(680,456.996).
- Float above the original lower Waddle Doo and Blockin. Ascend through the
  right-hand corridor after timing the stationary Waddle Doo's volley.
- Ordinary air puff and inhalation clear the five upper checkerboard F0 cells
  at(27,11),(25,11),(23,11),(21,11),(19,11), all clear by2417. Descend only a
  short section of the ladder, jump left and float above the lower enemies.
  Move right on emerging from the upper-left ladder to avoid Chip.
- At2944, the directed719 self-door at(19,8) places Kirby at spawn(26,9),
  pixel(408,136.996). This is a real native transition that reloads the room
  and restores the cleared checkerboard. It is not a save-state restore.
- Jump and inflate above the two upper Big Waddle Dees. Rise into the top
  chamber. At3322, hold B for60 frames facing left. Ordinary inhale clears
  lower F0(31,3) at3329; upper F0(31,2) stays intact. Walk beneath the upper
  tile to door(14,3), arriving in720 at3646 at pixel(1896,120.996).

The separate719 Bomb Block F1(1,14), which controls the734 exit, remains intact
on every719 frame. No copy ability is acquired from any enemy. The controls
omit only the final60-frame inhale, retain both final F0 tiles and remain in719.
They are finite route controls, not an exhaustive claim that no other ordinary
strategy works.

## Recorded evidence and replay boundary

`carrot-yellow-ufo-upstream-runtime.json` is a separate compact record. It
retains all eight result/trace hashes, four fixture and production hashes,
21,064 validated gameplay samples, exact transition and self-door timing,
checkerboard reload observations, input schedules and final outcomes. Tests
check these retained records, not a fresh emulator replay. The original
`carrot-yellow-ufo-source-runtime.json` is preserved byte-for-byte. All37
private prior-packet files checked by the original preservation manifest also
remain unchanged.

The four fixtures come from normal full-production seed8, mode1 with the
full25-ability shuffled pool and policy seed5662892934360856578. Each differs
from its production ROM in exactly15 startup bytes; sources, geometry and
ordinary enemy behavior are untouched. Actual enemy health is observed at
100% and500%, not inferred from the setting. These discrete runs do not claim
all50–500% values. Original Doos have HP4/20, and Chip/Big Waddle Dees HP2/10.

For an independent replay, use a lawful USA ROM with SHA1
`274b102b6d940f46861a92b4e65f89a51815c12c`, generate those production settings
with actual HP1 or6 and enemy health100% or500%, and record all fixture
startup differences. Cold-boot a blank battery and replay the recorded inputs.
At1085, before directional movement, invoke the real client's configuration
synchronization once, record its eight writes and seal subsequent external
writes. Measure every frame1085–3717 inclusive. Check Normal ability, unchanged
actual HP/maxHP, AI0/humans1, the real self-door reload, the untouched upper F0
and734 Bomb Block, and the final native720 transition. Repeat with only the
3322 inhale window changed to idle. No chest/check, server submission,
gameplay RAM write, state restore or helper is part of this segment.

Native source reference `7d969fbce14fdc838d2c1ea01389717fb96c3189` supports the
ordinary collision classes and enemy timing: `code_080023A4.c` collision
attributes, `waddle_doo.c` stationary firing, `big_waddle_dee.c` movement and
bounds, and `chip.c` pursuit. ROMs, traces, saves, screenshots and private
scripts are not included. Hashes identify retained evidence, not a new replay.
