# Carrot Room7 bounded Fighter alternative

This is an OR alternative on `bomb_719_room13`, not a general ranged class.
Only guaranteed singleton WADDLE_DOO → Beam or Fighter enables the target.
The existing Beam graph and its independent Room5/native170 access stay intact.
Fighter inventory is acquisition permission, never equipment. With gating on,
Fighter becomes progression only for this enforced source assignment. Gating off
leaves it useful. Mixed finite random draws cannot guarantee this route.

Full25pool seed39 naturally assigns the finite lower original Doo0x088D3BF4
at568,456 to Fighter20. Continuous controller ingress170→719 occurs at1188,
natural acquisition at1420, and intact carry reaches86,232.996 at2971.
The final one-frame B tap enters ordinary first-combo state0x08065C5C at2973.
Its object0x0807E820 (sprite0x1FA/0) triggers F1(1,14); fifteen F2 cells
clear by3009. Actual door ingress reaches734 lower at3133 and remains there
at3242. The single differing no-final-B control retains F1 and all F2 cells
and stays719. This establishes only ENTRY_FROM_5_07, not general734 access,
Secret Notes, other exits, RoomSanity, rewards, or AP delivery.

Eight positive/control runs cover HP1/6 × enemy100/500, with four matching
positive tile-audit replays. All retain initial HP and acquired Fighter.
The carry includes held B2650–2700 and release: HP1 uses the special wave,
while HP6 uses the ordinary charged large wave. Neither changes any observed
719 tile during2650–2760. At500%, Big Waddle survives the carry hit atHP5/7;
its HP later restores on scrolling. The no-damage carry remains successful.
Do not replace the tested carry timing or call the whole route HP-independent.
Only the final ordinary combo is HP-independent. HP2–5 and intermediate enemy
multipliers are supported by native branches, not independently replayed.

Native source commit7d969fbce14fdc838d2c1ea01389717fb96c3189:
`src/kirby.c:19475–19493,19569–19600` selects the ordinary combo independently
of HP. `src/code_0806F780.c:6023–6105` creates the first combo, follows Kirby,
and sets scan bounds. `asm/code_08032E98.s:6946–7072,8630–8636` mirrors bounds
for the left-facing scan. At floor86,232 the scan spansx26..86,y213..243,
columns1..5/rows13..15, including F1(1,14). Do not double-mirror the sprite
bounds. `src/kirby.c:19519–19544` selects HP-dependent carry waves;
`src/code_0806F780.c:6207–6247` identifies the ordinary large wave.

Startup only places Normal near the native170 predecessor door, then eight
real client configuration writes finish at1085. No gameplay RAM/ROM writes,
state restores, source replacements, equipment edits, helpers or Phone inputs
occur. Helpers are observed in101 through1085–3242 with AI0/humans1.
Global game-start reachability to the startup pose is not a native claim.
Raw ROMs, traces and controller recordings remain private; the compact
`carrot-room7-fighter-acceptance.json` records audited outcomes and trace hashes.
Runtime patch and base patch are unchanged.
