# Generic block labels: door and check inventory

One row per compiled solver surface using a generic or floating block token.
The arrow is directional; room keys omit `REGION_`. The exact compact expression is preserved.
A matching overlay may enforce a different obstacle or be conditional. A missing direct
overlay does not rule out an upstream gate, a verified Normal route, or a bypass.

| Classification | Entrances | Checks |
| --- | ---: | ---: |
| Exact catalog overlay | 5 | 1 |
| Declared Normal alternative (not physical proof) | 5 | 0 |
| No direct overlay or declared Normal alternative | 134 | 9 |

## Exact catalog overlay

| Door / check | Compact expression | Exact overlay |
| --- | --- | --- |
| `MUSTARD_MOUNTAIN/ROOM_4_CHEST` → Mustard Mountain Map - Big Chest (3960205) | `{"all": ["can_fly","can_hit_far_switch","can_break_block"]}` | `switch_310_mustard_map` |
| `MOONLIGHT_MANSION/ROOM_2_15` → `MOONLIGHT_MANSION/ROOM_2_WARP` | `{"all": ["can_fly","can_break_floating_block","can_break_metal"]}` | `metal_742_lower_to_warp` |
| `RAINBOW_ROUTE/ROOM_1_08` → `RAINBOW_ROUTE/ROOM_1_09` | `{"all": ["can_break_block","can_fly"]}` | `bomb_110_room9` |
| `RAINBOW_ROUTE/ROOM_1_32` → `RAINBOW_ROUTE/ROOM_1_33_LEFT` | `{"all": ["can_fly","can_break_floating_block","can_light_fuses"]}` | `fuse_126` |
| `RAINBOW_ROUTE/ROOM_1_41_UPPER` → `RAINBOW_ROUTE/ROOM_1_41` | `{"all": ["can_break_block","can_break_metal"]}` | `metal_141_left_reverse` |
| `RAINBOW_ROUTE/ROOM_1_41_UPPER` → `RAINBOW_ROUTE/ROOM_1_41__LOGIC__EAST_MOONLIGHT` | `{"all": ["can_break_block","can_break_metal"]}` | `metal_141_right_forward` |

## Declared Normal alternative (not physical proof)

| Door / check | Compact expression | Exact overlay |
| --- | --- | --- |
| `OLIVE_OCEAN/ROOM_6_CHEST_1` → `OLIVE_OCEAN/ROOM_6_16` | `{"any": ["can_break_block","can_swim"]}` | — |
| `PEPPERMINT_PALACE/ROOM_7_02` → `PEPPERMINT_PALACE/ROOM_7_01` | `{"any": ["can_swim","can_break_block"]}` | — |
| `PEPPERMINT_PALACE/ROOM_7_02` → `PEPPERMINT_PALACE/ROOM_7_03` | `{"any": ["can_swim","can_break_block"]}` | — |
| `RAINBOW_ROUTE/ROOM_1_23` → `RAINBOW_ROUTE/ROOM_1_22` | `{"any": ["can_climb","can_break_block"]}` | — |
| `RAINBOW_ROUTE/ROOM_1_24_UPPER` → `RAINBOW_ROUTE/ROOM_1_24` | `{"any": ["can_climb","can_break_block"]}` | — |

## No direct overlay or declared Normal alternative

| Door / check | Compact expression | Exact overlay |
| --- | --- | --- |
| `CABBAGE_CAVERN/ROOM_3_GOAL` → Cabbage Cavern - Goal Game (3960705) | `{"all": ["can_break_block","can_fly"]}` | — |
| `CABBAGE_CAVERN/ROOM_3_GOAL` → Cabbage Cavern Map - Big Chest (3960200) | `{"all": ["can_fly","can_break_block"]}` | — |
| `MOONLIGHT_MANSION/ROOM_2_GOAL_2` → Moonlight Mansion - Goal Game 2 (3960704) | `{"all": ["can_fly","can_break_floating_block"]}` | — |
| `MUSTARD_MOUNTAIN/ROOM_4_GOAL_2` → Mustard Mountain - Goal Game 2 (3960707) | `"can_break_block"` | — |
| `OLIVE_OCEAN/ROOM_6_GOAL_2` → Olive Ocean - Goal Game 2 (3960709) | `{"all": ["can_fly","can_break_block"]}` | — |
| `PEPPERMINT_PALACE/ROOM_7_GOAL_1` → Peppermint Palace - Goal Game 1 (3960710) | `{"all": ["can_break_block","can_fly"]}` | — |
| `RAINBOW_ROUTE/ROOM_1_GOAL_1` → Rainbow Route - Goal Game 1 (3960700) | `"can_break_block"` | — |
| `RAINBOW_ROUTE/ROOM_1_GOAL_2` → Rainbow Route - Goal Game 2 (3960701) | `"can_break_floating_block"` | — |
| `RAINBOW_ROUTE/ROOM_1_GOAL_3` → Rainbow Route - Goal Game 3 (3960702) | `"can_break_block"` | — |
| `CABBAGE_CAVERN/ROOM_3_02` → `CABBAGE_CAVERN/ROOM_3_01` | `{"all": ["can_fly","can_break_block"]}` | — |
| `CABBAGE_CAVERN/ROOM_3_02` → `CABBAGE_CAVERN/ROOM_3_HUB_2` | `{"all": ["can_fly","can_break_block"]}` | — |
| `CABBAGE_CAVERN/ROOM_3_04` → `CABBAGE_CAVERN/ROOM_3_03` | `"can_break_block"` | — |
| `CABBAGE_CAVERN/ROOM_3_04` → `RAINBOW_ROUTE/ROOM_1_13` | `"can_break_block"` | — |
| `CABBAGE_CAVERN/ROOM_3_06` → `CABBAGE_CAVERN/ROOM_3_07` | `{"all": ["can_fly","can_break_block"]}` | — |
| `CABBAGE_CAVERN/ROOM_3_06` → `CABBAGE_CAVERN/ROOM_3_HUB_2` | `"can_break_block"` | — |
| `CABBAGE_CAVERN/ROOM_3_08` → `CABBAGE_CAVERN/ROOM_3_13` | `"can_break_block"` | — |
| `CABBAGE_CAVERN/ROOM_3_09` → `CABBAGE_CAVERN/ROOM_3_08` | `"can_break_block"` | — |
| `CABBAGE_CAVERN/ROOM_3_09` → `CABBAGE_CAVERN/ROOM_3_10_RIGHT` | `{"all": ["can_fly","can_break_block"]}` | — |
| `CABBAGE_CAVERN/ROOM_3_10_LEFT` → `CABBAGE_CAVERN/ROOM_3_10` | `{"all": ["can_fly","can_swim","can_break_block"]}` | — |
| `CABBAGE_CAVERN/ROOM_3_11` → `CABBAGE_CAVERN/ROOM_3_10_LEFT` | `{"all": ["can_swim","can_break_block"]}` | — |
| `CABBAGE_CAVERN/ROOM_3_11` → `CABBAGE_CAVERN/ROOM_3_12_UPPER` | `{"all": ["can_swim","can_break_block"]}` | — |
| `CABBAGE_CAVERN/ROOM_3_12` → `CABBAGE_CAVERN/ROOM_3_13` | `"can_break_block"` | — |
| `CABBAGE_CAVERN/ROOM_3_15` → `CABBAGE_CAVERN/ROOM_3_13_LOWER` | `{"all": ["can_fly","can_break_block"]}` | — |
| `CABBAGE_CAVERN/ROOM_3_15` → `CABBAGE_CAVERN/ROOM_3_16` | `"can_break_block"` | — |
| `CABBAGE_CAVERN/ROOM_3_15_LOWER_ENTRY` → `CABBAGE_CAVERN/ROOM_3_15` | `{"all": ["can_fly","can_break_block"]}` | — |
| `CABBAGE_CAVERN/ROOM_3_15_LOWER_ENTRY` → `CABBAGE_CAVERN/ROOM_3_15__LOGIC__LOWER_CHEST` | `{"all": ["can_fly","can_break_block"]}` | — |
| `CABBAGE_CAVERN/ROOM_3_15_UPPER_ENTRY` → `CABBAGE_CAVERN/ROOM_3_15` | `"can_break_block"` | — |
| `CABBAGE_CAVERN/ROOM_3_GOAL` → `RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE` | `{"all": ["can_break_block","can_fly"]}` | — |
| `CARROT_CASTLE/ROOM_5_01` → `CARROT_CASTLE/ROOM_5_03` | `{"all": ["can_fly","can_break_block"]}` | — |
| `CARROT_CASTLE/ROOM_5_01` → `CARROT_CASTLE/ROOM_5_HUB` | `"can_break_block"` | — |
| `CARROT_CASTLE/ROOM_5_01` → `RAINBOW_ROUTE/ROOM_1_21` | `"can_break_block"` | — |
| `CARROT_CASTLE/ROOM_5_03` → `CARROT_CASTLE/ROOM_5_01` | `{"all": ["can_fly","can_break_block"]}` | — |
| `CARROT_CASTLE/ROOM_5_03` → `CARROT_CASTLE/ROOM_5_04` | `{"all": ["can_fly","can_break_block"]}` | — |
| `CARROT_CASTLE/ROOM_5_07` → `CARROT_CASTLE/ROOM_5_08` | `{"all": ["can_climb","can_break_block"]}` | — |
| `CARROT_CASTLE/ROOM_5_07` → `CARROT_CASTLE/ROOM_5_14` | `{"all": ["can_climb","can_break_block"]}` | — |
| `CARROT_CASTLE/ROOM_5_15` → `CARROT_CASTLE/ROOM_5_16` | `"can_break_block"` | — |
| `CARROT_CASTLE/ROOM_5_15` → `CARROT_CASTLE/ROOM_5_17` | `"can_break_block"` | — |
| `CARROT_CASTLE/ROOM_5_17` → `CARROT_CASTLE/ROOM_5_18` | `"can_break_block"` | — |
| `CARROT_CASTLE/ROOM_5_18` → `CARROT_CASTLE/ROOM_5_WARP` | `{"all": ["can_break_block",{"any": ["can_fly","can_climb"]}]}` | — |
| `MOONLIGHT_MANSION/ROOM_2_01` → `MOONLIGHT_MANSION/ROOM_2_01_UPPER_PLATFORM` | `"can_break_block"` | — |
| `MOONLIGHT_MANSION/ROOM_2_01_BOTTOM_LEFT` → `MOONLIGHT_MANSION/ROOM_2_11` | `"can_break_block"` | — |
| `MOONLIGHT_MANSION/ROOM_2_02` → `MOONLIGHT_MANSION/ROOM_2_02_RIGHT` | `"can_break_block"` | — |
| `MOONLIGHT_MANSION/ROOM_2_02_RIGHT` → `MOONLIGHT_MANSION/ROOM_2_02` | `{"all": ["can_fly","can_break_floating_block"]}` | — |
| `MOONLIGHT_MANSION/ROOM_2_02_RIGHT` → `MOONLIGHT_MANSION/ROOM_2_HUB` | `"can_break_block"` | — |
| `MOONLIGHT_MANSION/ROOM_2_03` → `MOONLIGHT_MANSION/ROOM_2_04` | `{"all": ["can_climb","can_break_block"]}` | — |
| `MOONLIGHT_MANSION/ROOM_2_04` → `MOONLIGHT_MANSION/ROOM_2_04_PAST_SWITCH_WALL` | `"can_break_block"` | — |
| `MOONLIGHT_MANSION/ROOM_2_04` → `MOONLIGHT_MANSION/ROOM_2_07_UPPER_LEFT` | `"can_break_block"` | — |
| `MOONLIGHT_MANSION/ROOM_2_04_PAST_SWITCH_WALL` → `MOONLIGHT_MANSION/ROOM_2_08` | `"can_break_block"` | — |
| `MOONLIGHT_MANSION/ROOM_2_05` → `MOONLIGHT_MANSION/ROOM_2_05_UPPER_LEDGE` | `{"all": ["can_fly","can_break_floating_block"]}` | — |
| `MOONLIGHT_MANSION/ROOM_2_05_UPPER_LEDGE` → `MOONLIGHT_MANSION/ROOM_2_05` | `"can_break_block"` | — |
| `MOONLIGHT_MANSION/ROOM_2_06` → `MOONLIGHT_MANSION/ROOM_2_GOAL_1` | `"can_break_block"` | — |
| `MOONLIGHT_MANSION/ROOM_2_08` → `MOONLIGHT_MANSION/ROOM_2_07_UPPER_RIGHT` | `"can_break_floating_block"` | — |
| `MOONLIGHT_MANSION/ROOM_2_08` → `MOONLIGHT_MANSION/ROOM_2_09` | `"can_break_block"` | — |
| `MOONLIGHT_MANSION/ROOM_2_08_BOMB_ROOM` → `MOONLIGHT_MANSION/ROOM_2_08` | `"can_break_block"` | — |
| `MOONLIGHT_MANSION/ROOM_2_09` → `MOONLIGHT_MANSION/ROOM_2_10` | `"can_break_block"` | — |
| `MOONLIGHT_MANSION/ROOM_2_11` → `MOONLIGHT_MANSION/ROOM_2_11_AFTER_LEVER` | `{"all": ["can_climb","can_fly","can_break_block","mm_lever"]}` | — |
| `MOONLIGHT_MANSION/ROOM_2_14` → `MOONLIGHT_MANSION/ROOM_2_15` | `"can_break_block"` | — |
| `MOONLIGHT_MANSION/ROOM_2_14_UPPER` → `MOONLIGHT_MANSION/ROOM_2_15__LOGIC__UPPER_RETURN` | `{"all": ["can_break_block","can_fly"]}` | — |
| `MOONLIGHT_MANSION/ROOM_2_15` → `MOONLIGHT_MANSION/ROOM_2_14_UPPER` | `{"all": ["can_fly","can_break_floating_block"]}` | — |
| `MOONLIGHT_MANSION/ROOM_2_19` → `MOONLIGHT_MANSION/ROOM_2_GOAL_2_UPPER_RIGHT` | `{"all": ["can_climb","can_break_block"]}` | — |
| `MOONLIGHT_MANSION/ROOM_2_20` → `MOONLIGHT_MANSION/ROOM_2_GOAL_2` | `{"all": ["can_break_block","can_swim"]}` | — |
| `MOONLIGHT_MANSION/ROOM_2_20` → `MOONLIGHT_MANSION/ROOM_2_GOAL_2_BOTTOM_RIGHT` | `{"all": ["can_break_block","can_swim"]}` | — |
| `MOONLIGHT_MANSION/ROOM_2_GOAL_2` → `RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE` | `{"all": ["can_fly","can_break_floating_block"]}` | — |
| `MOONLIGHT_MANSION/ROOM_2_WARP` → `CANDY_CONSTELLATION/ROOM_9_04` | `{"all": ["can_fly","can_break_block"]}` | — |
| `MUSTARD_MOUNTAIN/ROOM_4_02` → `MUSTARD_MOUNTAIN/ROOM_4_01` | `"can_break_block"` | — |
| `MUSTARD_MOUNTAIN/ROOM_4_02` → `MUSTARD_MOUNTAIN/ROOM_4_03` | `{"all": ["can_fly","can_break_floating_block"]}` | — |
| `MUSTARD_MOUNTAIN/ROOM_4_03` → `MUSTARD_MOUNTAIN/ROOM_4_02` | `{"all": ["can_fly","can_break_floating_block"]}` | — |
| `MUSTARD_MOUNTAIN/ROOM_4_03` → `MUSTARD_MOUNTAIN/ROOM_4_HUB` | `"can_break_floating_block"` | — |
| `MUSTARD_MOUNTAIN/ROOM_4_06` → `RAINBOW_ROUTE/ROOM_1_40` | `"can_break_block"` | — |
| `MUSTARD_MOUNTAIN/ROOM_4_07` → `MUSTARD_MOUNTAIN/ROOM_4_08` | `"can_break_block"` | — |
| `MUSTARD_MOUNTAIN/ROOM_4_08` → `MUSTARD_MOUNTAIN/ROOM_4_05__LOGIC__RIGHT_ENTRY` | `{"all": ["can_fly","can_break_block"]}` | — |
| `MUSTARD_MOUNTAIN/ROOM_4_08` → `MUSTARD_MOUNTAIN/ROOM_4_GOAL_1` | `{"all": ["can_fly","can_break_block"]}` | — |
| `MUSTARD_MOUNTAIN/ROOM_4_09` → `MUSTARD_MOUNTAIN/ROOM_4_10` | `"can_break_block"` | — |
| `MUSTARD_MOUNTAIN/ROOM_4_10` → `MUSTARD_MOUNTAIN/ROOM_4_11` | `"can_break_block"` | — |
| `MUSTARD_MOUNTAIN/ROOM_4_11` → `MUSTARD_MOUNTAIN/ROOM_4_12` | `"can_break_block"` | — |
| `MUSTARD_MOUNTAIN/ROOM_4_12` → `MUSTARD_MOUNTAIN/ROOM_4_13` | `"can_break_block"` | — |
| `MUSTARD_MOUNTAIN/ROOM_4_12` → `MUSTARD_MOUNTAIN/ROOM_4_13__LOGIC__CANNON_LEFT` | `"can_break_block"` | — |
| `MUSTARD_MOUNTAIN/ROOM_4_15` → `MUSTARD_MOUNTAIN/ROOM_4_17` | `{"all": ["can_fly","can_break_block"]}` | — |
| `MUSTARD_MOUNTAIN/ROOM_4_16` → `MUSTARD_MOUNTAIN/ROOM_4_17_LEFT` | `"can_break_block"` | — |
| `MUSTARD_MOUNTAIN/ROOM_4_17` → `MUSTARD_MOUNTAIN/ROOM_4_18` | `{"all": ["can_fly","can_break_block"]}` | — |
| `MUSTARD_MOUNTAIN/ROOM_4_17_LEFT` → `MUSTARD_MOUNTAIN/ROOM_4_18` | `"can_break_block"` | — |
| `MUSTARD_MOUNTAIN/ROOM_4_19` → `MUSTARD_MOUNTAIN/ROOM_4_GOAL_2` | `"can_break_block"` | — |
| `MUSTARD_MOUNTAIN/ROOM_4_GOAL_2` → `RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE` | `"can_break_block"` | — |
| `OLIVE_OCEAN/ROOM_6_02` → `OLIVE_OCEAN/ROOM_6_03` | `"can_break_block"` | — |
| `OLIVE_OCEAN/ROOM_6_06` → `OLIVE_OCEAN/ROOM_6_GOAL_1` | `{"all": ["can_break_block","can_fly"]}` | — |
| `OLIVE_OCEAN/ROOM_6_07` → `OLIVE_OCEAN/ROOM_6_08` | `{"all": ["can_break_block","can_swim","can_fly"]}` | — |
| `OLIVE_OCEAN/ROOM_6_08` → `OLIVE_OCEAN/ROOM_6_07` | `{"all": ["can_swim","can_break_block"]}` | — |
| `OLIVE_OCEAN/ROOM_6_08` → `OLIVE_OCEAN/ROOM_6_09` | `{"all": ["can_swim","can_fly","can_break_block"]}` | — |
| `OLIVE_OCEAN/ROOM_6_09` → `OLIVE_OCEAN/ROOM_6_08` | `{"all": ["can_swim","can_fly","can_break_block"]}` | — |
| `OLIVE_OCEAN/ROOM_6_09` → `OLIVE_OCEAN/ROOM_6_HUB` | `{"all": ["can_swim","can_fly","can_break_block"]}` | — |
| `OLIVE_OCEAN/ROOM_6_10` → `OLIVE_OCEAN/ROOM_6_11` | `{"all": ["can_swim","can_break_block"]}` | — |
| `OLIVE_OCEAN/ROOM_6_10` → `OLIVE_OCEAN/ROOM_6_18` | `{"all": ["can_swim","can_break_block"]}` | — |
| `OLIVE_OCEAN/ROOM_6_10` → `OLIVE_OCEAN/ROOM_6_HUB` | `{"all": ["can_swim","can_break_block"]}` | — |
| `OLIVE_OCEAN/ROOM_6_11` → `OLIVE_OCEAN/ROOM_6_10` | `"can_break_block"` | — |
| `OLIVE_OCEAN/ROOM_6_11` → `OLIVE_OCEAN/ROOM_6_12` | `"can_break_block"` | — |
| `OLIVE_OCEAN/ROOM_6_12` → `OLIVE_OCEAN/ROOM_6_11` | `"can_break_block"` | — |
| `OLIVE_OCEAN/ROOM_6_16` → `OLIVE_OCEAN/ROOM_6_17` | `"can_break_block"` | — |
| `OLIVE_OCEAN/ROOM_6_17` → `OLIVE_OCEAN/ROOM_6_12` | `"can_break_block"` | — |
| `OLIVE_OCEAN/ROOM_6_17` → `OLIVE_OCEAN/ROOM_6_22` | `{"all": ["can_break_block","can_swim"]}` | — |
| `OLIVE_OCEAN/ROOM_6_GOAL_2` → `RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE` | `{"all": ["can_fly","can_break_block"]}` | — |
| `PEPPERMINT_PALACE/ROOM_7_08` → `PEPPERMINT_PALACE/ROOM_7_GOAL_1` | `"can_break_block"` | — |
| `PEPPERMINT_PALACE/ROOM_7_09` → `PEPPERMINT_PALACE/ROOM_7_10` | `{"all": ["can_break_block",{"any": ["can_fly","can_climb"]}]}` | — |
| `PEPPERMINT_PALACE/ROOM_7_GOAL_1` → `RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE` | `{"all": ["can_break_block","can_fly"]}` | — |
| `RAINBOW_ROUTE/ROOM_1_03_LOWER` → `RAINBOW_ROUTE/ROOM_1_06_UPPER` | `"can_break_block"` | — |
| `RAINBOW_ROUTE/ROOM_1_03_UPPER` → `RAINBOW_ROUTE/ROOM_1_04` | `"can_break_block"` | — |
| `RAINBOW_ROUTE/ROOM_1_04` → `RAINBOW_ROUTE/ROOM_1_05` | `"can_break_block"` | — |
| `RAINBOW_ROUTE/ROOM_1_06_LOWER_MID` → `RAINBOW_ROUTE/ROOM_1_06_LOWER_RIGHT` | `"can_break_block"` | — |
| `RAINBOW_ROUTE/ROOM_1_06_LOWER_RIGHT` → `RAINBOW_ROUTE/ROOM_1_06_LOWER_MID` | `"can_break_block"` | — |
| `RAINBOW_ROUTE/ROOM_1_08` → `RAINBOW_ROUTE/ROOM_1_12` | `{"all": ["can_break_block","can_fly"]}` | — |
| `RAINBOW_ROUTE/ROOM_1_10` → `RAINBOW_ROUTE/ROOM_1_11` | `{"all": ["can_break_block","can_swim"]}` | — |
| `RAINBOW_ROUTE/ROOM_1_12` → `RAINBOW_ROUTE/ROOM_1_08` | `"can_break_block"` | — |
| `RAINBOW_ROUTE/ROOM_1_12` → `RAINBOW_ROUTE/ROOM_1_13` | `"can_break_block"` | — |
| `RAINBOW_ROUTE/ROOM_1_14` → `RAINBOW_ROUTE/ROOM_1_13` | `{"all": ["can_fly","can_break_floating_block"]}` | — |
| `RAINBOW_ROUTE/ROOM_1_14` → `RAINBOW_ROUTE/ROOM_1_31` | `{"all": ["can_fly","can_break_floating_block"]}` | — |
| `RAINBOW_ROUTE/ROOM_1_14` → `RAINBOW_ROUTE/ROOM_1_HUB_2` | `{"all": ["can_fly","can_break_floating_block"]}` | — |
| `RAINBOW_ROUTE/ROOM_1_15` → `RAINBOW_ROUTE/ROOM_1_15_LOWER` | `"can_break_floating_block"` | — |
| `RAINBOW_ROUTE/ROOM_1_15_LOWER` → `RAINBOW_ROUTE/ROOM_1_15` | `{"all": ["can_break_block","can_fly"]}` | — |
| `RAINBOW_ROUTE/ROOM_1_16` → `RAINBOW_ROUTE/ROOM_1_16_MID` | `{"all": ["can_fly","can_break_block"]}` | — |
| `RAINBOW_ROUTE/ROOM_1_16_MID` → `RAINBOW_ROUTE/ROOM_1_16` | `{"all": ["can_climb","can_break_block"]}` | — |
| `RAINBOW_ROUTE/ROOM_1_16_MID` → `RAINBOW_ROUTE/ROOM_1_16_UPPER` | `{"all": ["can_fly","can_break_block"]}` | — |
| `RAINBOW_ROUTE/ROOM_1_16_MID` → `RAINBOW_ROUTE/ROOM_1_17` | `"can_break_block"` | — |
| `RAINBOW_ROUTE/ROOM_1_18_UPPER` → `RAINBOW_ROUTE/ROOM_1_18` | `"can_break_block"` | — |
| `RAINBOW_ROUTE/ROOM_1_21` → `CARROT_CASTLE/ROOM_5_01` | `"can_break_block"` | — |
| `RAINBOW_ROUTE/ROOM_1_21` → `RAINBOW_ROUTE/ROOM_1_20` | `"can_break_block"` | — |
| `RAINBOW_ROUTE/ROOM_1_24_UPPER` → `CARROT_CASTLE/ROOM_5_02` | `"can_break_block"` | — |
| `RAINBOW_ROUTE/ROOM_1_27` → `RAINBOW_ROUTE/ROOM_1_27_UPPER_LEFT` | `{"all": ["can_break_floating_block",{"any": ["can_fly","can_climb"]}]}` | — |
| `RAINBOW_ROUTE/ROOM_1_27_UPPER_LEFT` → `RAINBOW_ROUTE/ROOM_1_27` | `"can_break_block"` | — |
| `RAINBOW_ROUTE/ROOM_1_28` → `RAINBOW_ROUTE/ROOM_1_29` | `"can_break_block"` | — |
| `RAINBOW_ROUTE/ROOM_1_34` → `RAINBOW_ROUTE/ROOM_1_35` | `"can_break_block"` | — |
| `RAINBOW_ROUTE/ROOM_1_34` → `RAINBOW_ROUTE/ROOM_1_HUB_4` | `"can_break_block"` | — |
| `RAINBOW_ROUTE/ROOM_1_35` → `RAINBOW_ROUTE/ROOM_1_34` | `{"all": ["can_fly","can_break_floating_block"]}` | — |
| `RAINBOW_ROUTE/ROOM_1_35` → `RAINBOW_ROUTE/ROOM_1_36_VERTICAL` | `"can_break_block"` | — |
| `RAINBOW_ROUTE/ROOM_1_36_HORIZONTAL` → `MUSTARD_MOUNTAIN/ROOM_4_01` | `"can_break_block"` | — |
| `RAINBOW_ROUTE/ROOM_1_36_HORIZONTAL` → `RAINBOW_ROUTE/ROOM_1_39` | `"can_break_block"` | — |
| `RAINBOW_ROUTE/ROOM_1_37` → `RAINBOW_ROUTE/ROOM_1_36_VERTICAL` | `{"all": ["can_fly","can_break_block"]}` | — |
| `RAINBOW_ROUTE/ROOM_1_37` → `RAINBOW_ROUTE/ROOM_1_38` | `{"all": ["can_fly","can_break_block"]}` | — |
| `RAINBOW_ROUTE/ROOM_1_37` → `RAINBOW_ROUTE/ROOM_1_40` | `"can_break_block"` | — |
| `RAINBOW_ROUTE/ROOM_1_41_UPPER` → `RAINBOW_ROUTE/ROOM_1_41__LOGIC__TOP_MUSTARD` | `"can_break_floating_block"` | — |
| `RAINBOW_ROUTE/ROOM_1_42_CUT` → `MOONLIGHT_MANSION/ROOM_2_17` | `{"all": ["can_break_block",{"any": ["can_fly","can_climb"]}]}` | — |
| `RAINBOW_ROUTE/ROOM_1_42_CUT` → `RAINBOW_ROUTE/ROOM_1_42` | `{"all": ["can_climb","can_break_block"]}` | — |
| `RAINBOW_ROUTE/ROOM_1_GOAL_1` → `RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE` | `"can_break_block"` | — |
| `RAINBOW_ROUTE/ROOM_1_GOAL_2` → `RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE` | `"can_break_floating_block"` | — |
| `RAINBOW_ROUTE/ROOM_1_GOAL_3` → `RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE` | `"can_break_block"` | — |
