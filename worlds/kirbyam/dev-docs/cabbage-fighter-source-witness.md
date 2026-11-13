# Finite original-source Fighter witness for Chocolate

This witness supports the existing `bomb_517_chocolate` target's
`hub2_fighter_entry` graph and room 517 capability
`bomb_517_fighter_first_combo`. It owns only `MINOR_CHEST_SPRAY_PAINT_12`,
client location 3960511. The original Waddle Doo template `0x088CA04C` at
(528, 264), native type 18 and copy field 7, is finite. Ordinary full-pool
seed 39 yields policy 6282654274669279257 and Doo to Fighter (20).

## Source and complete carry

Independent Hub2 access is assumed. Fresh Normal crosses the real 591 to 517
entrance at frame 1109. Doo enters inhale/HP0 state at 1833, mouth-full begins
at 1850, the original source task disappears at 1851, and swallowing grants
Fighter at 1939. It remains equipped through the route. Helpers stay in room
101. The startup-only room/coordinate fixture and fresh blank 32 KiB save are
declared. The only eight real-client configuration writes occur at 1085;
there are no gameplay writes or restored states.

A short B tap at 2007, released the next frame, opens the separate source
corridor F1 at 2009 with the first combo. Its chain finishes at 2033. The
accepted Fighter carry pauses during frames 2067-2074, then walks left for
82 frames during 2075-2156. Another short punch at 2356 opens ordinary block (19, 17) at
2358. Immediate Up input at 2357 prevents the punch's movement from causing
a fall. At 2561, Kirby is at (312.640625, 197.00390625); continued flight
through 2588 avoids an unnecessary air attack/drop. Block (17, 14) is never
changed. The complete carry reaches the dry lower target pose at 3326.

Copied long-hold inputs and intermediate carry attempts failed and are not
acceptance. Every accepted endpoint was freshly executed using the corrected
Fighter-specific inputs. No source or ability is supplied by the fixture.

## First combo and exact target attribution

At frame 3326, right-facing Kirby is settled at
(185.99609375, 120.99609375), with F1 (14, 7) still sealed. A single B tap
selects the ordinary first combo. At 3328, Kirby animation 53/header 1, the
attached task `0x0807E821` has player parent `0x02020EE0`, animation 506
(`0x1FA`), variant 0, bounds (0, -19, 60, 11), flags `0xA0080100` and mask
`0xB1000043`. Its integer rectangle (185, 101, 245, 131) intersects the target
rectangle (224, 112, 239, 127) behind solid columns 12 and 13. The new chain
callback `0x0800E27D` names that exact scanner as parent.

Native `kirby.c:19475-19493,19569-19600` selects and initializes the ordinary
combo independently of HP. `code_0806F780.c:6023-6105` creates and follows the
attached scanner and uses its active animation bounds. The distinct regular,
charged and HP1 wave constructors at lines 6164-6290 use generic task
`0x08070581`; that task is absent throughout every accepted room 517 trace.
Neither the source corridor nor the target uses the HP1 piercing projectile.
Ordinary F1 scanning is in `asm/code_08032E98.s:6946-7333`. This is sampled,
source-reconciled attribution, not instruction-breakpoint tracing.

## Endpoints and separate controls

Four HP 1/6 by enemy-health 100%/500% positives open F1 at 3328, finish all
seven F2 cells at 3358 and physically open chest 57 at 4252. Each records
3,406 frames, from 1085 through 4490. The unchanged local client captures
exactly location 3960511 from chest source `0x088CA0B8`; no server receipt
is claimed.

Four full-length negatives remove only B in [3326, 3327), match states
through 3326, and retain every other carry and collection input. They keep
maximum configured HP and Fighter, with F1=241, all seven F2=242, unopened
chest, event count 0 and no check through frame 4490. A separate gated
positive receives only Fighter Ability 3860120 as permission, unlock mask
1048576, then still acquires actual Fighter from Doo. The no-permission
counterpart stays Normal through 2067, a bounded acquisition negative rather
than a full target omission.

Stable original-object identities show no non-source combat HP reduction.
Other observed reductions end at HP1 with removal flag `0x1000`, matching
`object.c:180-212` culling. No frozen platform or payload is used. The four
positive player coordinate/room/ability/animation histories match across
endpoints. Intermediate health and arbitrary RNG or arrival states remain
untested.

## Host scope and provenance

Generation source tree `b9aa0f9b3a0898d0ccba1b253104dd960b6f1064` matches public
commit `0db01bdd5c91bd971993e59dc92f38572a33c908`. Native source is
`7d969fbce14fdc838d2c1ea01389717fb96c3189`. The host preservation baseline is
the later Sword checkpoint, `a4b3c31c4b4546a767ad38de4636819f22a7a8e1`, with
eight existing graphs. Compact scalars and review hashes are retained in
`cabbage-fighter-acceptance.json`; full ROMs, saves and raw memory stay private.

The new OR graph requires raw guaranteed Doo to Fighter before permission
filtering, independent Hub2 access, finite original acquisition and retained
equipment. The existing Carrot lower-entry reason already promotes Fighter
under the same raw assignment when gating is on, including before regions
exist and when minor chests are disabled. That reason and starting-item
multiplicity remain unchanged; no new factory or reconciliation is added.
No exit, RoomSanity rule, other target or global Fighter range changes.
