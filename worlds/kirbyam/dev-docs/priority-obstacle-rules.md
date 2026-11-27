# Metal, peg, fuse, and rope solver targets

Generated from the compiled room and traversal catalogs. Region names below omit the common
`REGION_` prefix; the arrow is directional. A check row includes its AP location ID.
An exact match uses the same obstacle family, AP owner, and exit or location—not merely the same native room.

| Family | Explicit compact sites | Same-family exact matches | Catalog targets |
| --- | ---: | ---: | ---: |
| Metal | 6 | 6 | 16 (9 exits, 7 checks) |
| Peg | 7 | 7 | 11 (6 exits, 5 checks) |
| Fuse | 2 | 2 | 5 (4 exits, 1 check) |
| Rope | 2 | 2 | 6 (2 exits, 4 checks) |

## Metal

| Door / check | Catalog target and witness notes | Compact token |
| --- | --- | --- |
| `RAINBOW_ROUTE/ROOM_1_41` → `RAINBOW_ROUTE/ROOM_1_41_UPPER` | `metal_141_left_forward` | `can_break_metal` |
| `RAINBOW_ROUTE/ROOM_1_41_UPPER` → `RAINBOW_ROUTE/ROOM_1_41` | `metal_141_left_reverse` | `can_break_metal` |
| `RAINBOW_ROUTE/ROOM_1_41_UPPER` → `RAINBOW_ROUTE/ROOM_1_41__LOGIC__EAST_MOONLIGHT` | `metal_141_right_forward` | `can_break_metal` |
| `RAINBOW_ROUTE/ROOM_1_GOAL_2` → Rainbow Route Goal 2 - Small Chest #1 (3960583) | `metal_176_goal2_drink` | — |
| `PEPPERMINT_PALACE/ROOM_7_07` → `PEPPERMINT_PALACE/ROOM_7_CHEST` | `metal_205_to_209_top` | `can_break_metal` |
| `PEPPERMINT_PALACE/ROOM_7_19` → Peppermint Palace 7-19 - Small Chest (3960572) | `metal_216_chest` | — |
| `PEPPERMINT_PALACE/ROOM_7_09` → Peppermint Palace 7-09 - Small Chest (3960571) | `metal_228_chest` | — |
| `PEPPERMINT_PALACE/ROOM_7_10` → Peppermint Palace 7-10 - Small Chest #2 (3960593) | `metal_229_left1up` | — |
| `RAINBOW_ROUTE/ROOM_1_39` → Rainbow Route 1-39 - Music Sheet #1 Chest (3960514) | `metal_537_beginning_notes` | — |
| `RAINBOW_ROUTE/ROOM_1_GOAL_1` → Rainbow Route Goal 1 - Small Chest #1 (3960581) | `metal_557_goal1_tomato` | — |
| `MOONLIGHT_MANSION/ROOM_2_04_PAST_SWITCH_WALL` → `MOONLIGHT_MANSION/ROOM_2_13` | `metal_707_to_712` | `can_break_metal` |
| `MOONLIGHT_MANSION/ROOM_2_01_PAST_METAL_BLOCKS` → `MOONLIGHT_MANSION/ROOM_2_01_BOTTOM_RIGHT` | `metal_708_743_dead_end` | — |
| `MOONLIGHT_MANSION/ROOM_2_01_PAST_METAL_BLOCKS` → `MOONLIGHT_MANSION/ROOM_2_01_BOTTOM_LEFT` | `metal_708_743_main` | — |
| `MOONLIGHT_MANSION/ROOM_2_01` → `MOONLIGHT_MANSION/ROOM_2_01_PAST_METAL_BLOCKS` | `metal_708_forward` | — |
| `MOONLIGHT_MANSION/ROOM_2_15` → `MOONLIGHT_MANSION/ROOM_2_WARP` | `metal_742_lower_to_warp` | `can_break_metal` |
| `MOONLIGHT_MANSION/ROOM_2_15` → Moonlight Mansion 2-15 - Small Chest #1 (3960585) | `metal_742_sparerib` | — |

## Peg

| Door / check | Catalog target and witness notes | Compact token |
| --- | --- | --- |
| `MOONLIGHT_MANSION/ROOM_2_20` → Moonlight Mansion 2-20 - Small Chest (3960569) | `peg_149_35_18` | — |
| `PEPPERMINT_PALACE/ROOM_7_12` → `PEPPERMINT_PALACE/ROOM_7_06__LOGIC__HAPPY_NOTES_ENTRY` | `peg_204_62_4` | `can_pound_pegs` |
| `PEPPERMINT_PALACE/ROOM_7_22` → Peppermint Palace 7-22 - Spray Paint #1 Chest (3960500) | `peg_221_41_12` | — |
| `CANDY_CONSTELLATION/ROOM_9_06` → `CANDY_CONSTELLATION/ROOM_9_CHEST_1` | `peg_401_28_30` | `can_pound_pegs` |
| `CANDY_CONSTELLATION/ROOM_9_08` → `CANDY_CONSTELLATION/ROOM_9_09` | `peg_411_4_3` | `can_pound_pegs` |
| `CABBAGE_CAVERN/ROOM_3_09` → Cabbage Cavern 3-09 - Small Chest (3960576) | `peg_510_7_7` | — |
| `CABBAGE_CAVERN/ROOM_3_13` → `CABBAGE_CAVERN/ROOM_3_13_LOWER` | `peg_513_4_7` | `can_pound_pegs` |
| `CABBAGE_CAVERN/ROOM_3_14` → Cabbage Cavern 3-14 - Spray Paint #8 Chest (3960507) | `peg_527_18_13` | — |
| `CABBAGE_CAVERN/ROOM_3_14` → `CABBAGE_CAVERN/ROOM_3_15_LOWER_ENTRY` | `peg_527_56_16` | `can_pound_pegs` |
| `RADISH_RUINS/ROOM_8_03` → `RADISH_RUINS/ROOM_8_CHEST_1` | `peg_605_12_24` | `can_pound_pegs` |
| `OLIVE_OCEAN/ROOM_6_CHEST_2` → Olive Ocean Map - Big Chest (3960201) | `peg_816_26_3` | `can_pound_pegs` |

## Fuse

| Door / check | Catalog target and witness notes | Compact token |
| --- | --- | --- |
| `CANDY_CONSTELLATION/ROOM_9_12` → Candy Constellation 9-12 - Small Chest (3960575) | `bomb_402_candy_chest`; conditional on source policy; block-family target with a profile-specific linked-fuse fallback | — |
| `RAINBOW_ROUTE/ROOM_1_32` → `RAINBOW_ROUTE/ROOM_1_33_LEFT` | `fuse_126`; has Advanced-only variants | `can_light_fuses` |
| `MUSTARD_MOUNTAIN/ROOM_4_13__LOGIC__CANNON_LEFT` → `MUSTARD_MOUNTAIN/ROOM_4_14__LOGIC__CANNON_LEFT` | `fuse_323` | `can_light_fuses` |
| `RADISH_RUINS/ROOM_8_16` → `RADISH_RUINS/ROOM_8_17` | `fuse_502` | — |
| `OLIVE_OCEAN/ROOM_6_07` → `OLIVE_OCEAN/ROOM_6_05__LOGIC__ENTRY_FROM_6_07` | `fuse_827` | — |

## Rope

| Door / check | Catalog target and witness notes | Compact token |
| --- | --- | --- |
| `RAINBOW_ROUTE/ROOM_1_42` → `RAINBOW_ROUTE/ROOM_1_42_CUT` | `rope_143_23_14` | `can_cut_ropes` |
| `PEPPERMINT_PALACE/ROOM_7_20` → `PEPPERMINT_PALACE/ROOM_7_21` | `rope_217_6_5` | `can_cut_ropes` |
| `PEPPERMINT_PALACE/ROOM_7_06` → Peppermint Palace 7-06 - Small Chest #3 (3960591) | `rope_227_20_12` | — |
| `PEPPERMINT_PALACE/ROOM_7_09` → Peppermint Palace 7-09 - Small Chest #2 (3960592) | `rope_228_11_21` | — |
| `MUSTARD_MOUNTAIN/ROOM_4_10` → Mustard Mountain 4-10 - Small Chest #1 (3960597) | `rope_316_35_5` | — |
| `OLIVE_OCEAN/ROOM_6_16` → Olive Ocean 6-16 - Small Chest (3960578) | `rope_553_26_7` | — |

### Standard and Advanced route classification (#1170)


A reviewed route can be evaluated under Standard rules from the shared
traversal capability catalog. Count directed native room transitions since
the equipment was acquired, not screen sections or same-room mirrors. A
fresh physical acquisition restarts the count. Standard allows a copy
action after at most three transitions and never requires Crash or Magic.
Advanced removes those two restrictions; named exceptions still require
their own reviewed graph and actual source.

The generator does not opt all targets into the new carry limit yet. A
stock-assignment comparison found these targets with at least one reviewed
Advanced route and no reviewed Standard route:

| Target | Reviewed Standard evidence needed |
| --- | --- |
| Cabbage 3-09 chest | Verify original n528 Rocky and the three-transition suffix |
| Peppermint 7-06 Happy Notes entry | Verify n210 Bonkers across two transitions, or closer n203 Rocky |
| Radish Chest 1 | Verify n623 Bonkers across two doors or n592 Stone across three |
| Beginning Music Notes (`metal_537_beginning_notes`) | Local or shorter metal-breaking route |
| Moonlight past-metal and both 2-01 entries (`metal_708_*`) | Local or shorter metal-breaking routes for each landing |
| Moonlight 2-13 (`metal_707_to_712`) | Local or shorter metal-breaking route |
| Peppermint 7-09 chest and 7-10 left 1-Up | Alternatives to the reviewed long metal-breaking carriers |

The three peg leads above come from the native inventory and directed doors,
not yet verified individual acquisition or arrival on the correct side.
These are gaps in reviewed data, not proof of impossibility in the game.
Do not make a long route Standard solely to satisfy seed validation, and do
not enable a hard gate before the affected Standard generation profiles can
still succeed. The Missile Wheel Race exception separately needs a verified
directed source path connected to the race and exact chest.

### Standard Shuffled source assignment (#1170)

With Advanced Logic **off**, check the initial deterministic enemy and world
statue assignment against the existing required acquisition graphs. If a
source cannot supply a legal action, try bounded swaps of existing grants in
the same enabled pool, preferring assignments that leave the other verified
targets satisfied. Do not consume another world RNG draw. Off, Completely
Random and Advanced Shuffled continue using their previous assignment path.

For Standard Shuffled with randomized world statues and enemy No Ability
Weight 100 only, a needed ability can be absent from the initial world
statue roster: there are more eligible abilities than slots. If swaps alone
fail, reserve the missing grant in an existing statue slot before applying the
swap plan. Do not add slots, add starting items, change enemy grants, or
randomize the Copy Ability Room. Preserve all counts in the resulting roster
when moving grants. Other settings do not reserve an absent grant; a bounded
failure with the available multiset is diagnostic, not a claim no other seed
or route can work.

The persisted plan drives ROM tokens, tracker reconstruction and the
spoiler; the same underlying witness predicates and final all-check audit
still run. The separate world-wide three-transition migration remains gated
on the Standard evidence gaps above.
