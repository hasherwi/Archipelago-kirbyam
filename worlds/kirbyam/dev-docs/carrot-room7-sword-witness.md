# Carrot Room7 bounded Sword repeated slash

`bomb_719_room13` has a separate Sword OR graph alongside unchanged Beam and
Fighter graphs. The graph requires the raw guaranteed singleton lower
WADDLE_DOO → Sword assignment before inventory filtering, independent AP
Room5/native170 access, and actual natural Sword acquisition. Inventory grants
permission, never equipment. Sword is already gateable and progression; no
classification change or starting-inventory promotion is added. Mixed finite
random draws, no-ability weight and source renewal do not prove this route.

Full 25-ability pool seed4, policy seed14749067020901597923, naturally maps the
original finite lower Doo0x088D3BF4 at568,456 to Sword18. Actual170→719 ingress
at1188 is Normal. The source appears at1198 and is swallowed at1420. Separate
Sword-specific combat, ladder flight, crouch slides and repositioning retain
Sword and starting HP through the legal dry left-facing stop86,232.996 at3093.
Earlier attacks clear eight ordinary F0 cells; F1(1,14) and all fifteen F2 cells
remain intact. This is not inherited Fighter combat or a general Sword range.

Three one-frame B taps at3093,3102,3106 enter repeated-slash animation111 at3110.
At3114/header5, attached local-player Sword task0x080753CC (Thumb0x080753CD),
object0x03003D18, sprite0x98/0 has active flags0xA2084101 and category0xB3002003.
Stored scan bounds(14,-12,55,1), mirrored once and integer-quantized at the tested
pose, scan x31..72,y220..233 and hit F1(1,14). The first bomb-chain task0x0800E27C
is parented to this same Sword object. All fifteen F2 clear by3150. The final
window has only animations0,52,53,111, never finisher112 or landing-wave110.
No landing-wave task0x08080130 appears anywhere in any accepted positive trace.
The first decoded55px contact suffices; later or maximum bounds are not needed.

Ordinary left movement at3212 and Up at3272 physically enter734 lower at3284.
The final3393 frame retains Sword and initial HP. This establishes only the
normalized `ROOM_5_13__LOGIC__ENTRY_FROM_5_07` edge. No reward collection, Secret
Notes, RoomSanity, other exit, AP delivery or general734 access is established.

Eight cold positive/control runs cover HP1/6 × enemy100/500. Each control
changes only the three final B taps to neutral, matches every state through3093,
retains F1/all15F2 and stays719 with full HP and Sword. Earlier carry attacks are
unchanged. At2786, ordinary Sword animation52 deals5 to lower Big Waddle:
HP2→-3 at100%, HP10→5 at500%. At500%, it survives through2962 while Kirby passes;
2963 offscreen cleanup is not another hit. The carry needs no kill threshold.
All four positive player trajectories match. HP2–5 and intermediate enemy
multipliers were not independently replayed and are not extra native tests.

Native source commit7d969fbce14fdc838d2c1ea01389717fb96c3189:
- `src/kirby.c:17510–17631,17675–17771`: repeated-slash111 and fresh-B edges.
- `src/code_0806F780.c:2884–3064`: attached Sword, parent, flags and bounds.
- `src/kirby.c:5831–5837`, `asm/code_08032E98.s:6946–7072,8630–8636`: scanner.
- `src/code_0806F780.c:6590–6657`: separate, absent landing-wave update.

Source fixtures use normal Generate/Main packaging and the shipped base patch
from commit2fc41e31e99ba612777c9916a0b7f6eaf867555d. Only startup room/position
ROM ranges0x2D8CB8..0x2D8CBF and0x2D8CD0..0x2D8CEF differ. Actual client sync makes
eight fenced configuration writes at1085. There are no gameplay RAM/ROM writes,
state restores, equipment edits, source replacement, helpers or Phone inputs.
Helpers remain101, AI0/humans1 throughout1085–3393. Native170 is startup-directed
near its real door, so independent access is an assumption, not game-start proof.
Native gating is off; gating-on permission, source-policy, option and fill
coverage is host testing, not a full native gated replay.

`carrot-room7-sword-acceptance.json` contains sanitized selected outcomes and
exact raw SHA256 identities for the frozen private inputs, traces, builds and
native sources. Private ROMs, full recordings, absolute paths and failed
exploratory runs are not published. Runtime and base patches are unchanged.
