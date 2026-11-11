# Phone a Friend: traversal audit and implementation boundary

Status: **implementation in progress; production activation and helper-route grants remain disabled.** The initial audit below was checked 2026-11-09. See [the native gate and ownership milestone](phone-implementation.md) for current code, tests, and remaining acceptance work. AI-assisted source review. This is a separate follow-up to [#490](https://github.com/hasherwi/Archipelago-kirbyam/issues/490), not a change to the through-wall evidence work in [#1052](https://github.com/hasherwi/Archipelago-kirbyam/pull/1052).

## Current design

Future Phone progression may assume helper participation only at **small switches and Heave-Ho blocks**, never helper copy abilities, ability attacks, Bomb Block/chest attacks or discarded ability sources. This is a logic restriction, not a change to native AI behavior. Room-specific arrival, positioning, useful cooperation and full traversal still require acceptance; these two permitted categories are not universal Phone grants.

The initial source audit also found documented cooperative Bomb Block behavior in Carrot Castle Room 16. Retain that discovery and the later native-733 observations as historical evidence, but exclude the helper attack from future progression witnesses under the current design. Independently reviewed human solo/source alternatives remain eligible and must be OR alternatives within each target, not separate AND requirements.

Only Beam is automatically precollected after PR #1051. Historical Phone evidence keeps its original starts and masks and does not certify this new baseline. Phone remains inactive with no catalog item, pool entry, option, slot capability or traversal binding.

## Historical audit scope and baseline

- Active feature tracker: [#490, Gate Kirby Actions](https://github.com/hasherwi/Archipelago-kirbyam/issues/490). Its initial action set includes Phone a Friend alongside Swallow, Slide, and Swim.
- [#1039](https://github.com/hasherwi/Archipelago-kirbyam/issues/1039) is closed as a duplicate, not as implemented. Its corrected scope withdraws the proposal to gate both phone actions: **only calling allies is eligible for gating**. Holding L to return to Central Circle must remain available under its normal native restrictions, independently of Phone ownership.
- AP baseline: [`7a198f4ff09a0b3a279dc61bc420bc57a0d62c10`](https://github.com/hasherwi/Archipelago-kirbyam/commit/7a198f4ff09a0b3a279dc61bc420bc57a0d62c10). Its [item catalog](https://github.com/hasherwi/Archipelago-kirbyam/blob/7a198f4ff09a0b3a279dc61bc420bc57a0d62c10/worlds/kirbyam/data/items.json) has no Phone summon-unlock item. It does already define `BATTERY`, labeled **Cell Phone Battery**, as filler (`3860027`); a consumable refill is not action ownership. `can_hit_far_switch` remains a permissive pending token in [rules.py](https://github.com/hasherwi/Archipelago-kirbyam/blob/7a198f4ff09a0b3a279dc61bc420bc57a0d62c10/worlds/kirbyam/rules.py), not an implemented Phone or ranged-ability contract.
- Native source reviewed: USA decompilation [`1197474f80e5de282fbedcd0025ebfa61f61a764`](https://github.com/jiangzhengwenjz/katam/tree/1197474f80e5de282fbedcd0025ebfa61f61a764). The repository targets ROM SHA-1 `274b102b6d940f46861a92b4e65f89a51815c12c`. This review did not build or execute that ROM.
- Native IDs below come from the checked-in [native/AP/WiKirby mapping](https://github.com/hasherwi/Archipelago-kirbyam/blob/7a198f4ff09a0b3a279dc61bc420bc57a0d62c10/worlds/kirbyam/dev-docs/native-room-wikirby-map.json). Native room IDs, completion indices, and AP logical compartments are different identifiers.

## Candidate routes and excluded historical observation

Small-switch and Heave-Ho rows are review targets, not newly accepted logic witnesses. The Carrot row is an excluded historical observation. An optional chest can still hold progression in an AP seed. Conversely, helping with an optional chest does not justify gating every exit from its room.

| Native room | Route or target | What the sources support | What remains to establish |
| --- | --- | --- | --- |
| **733**, Carrot Castle Room 16 | `REGION_CARROT_CASTLE/ROOM_5_16`, `MINOR_CHEST_SPRAY_PAINT_02` | Remote **Bomb Block** activation opens the lower Yellow Spray Paint route; friends and long-range abilities are documented alternatives. This historical observation is outside the current helper-progression scope. | Excluded as a Phone witness, regardless of repeatability. Preserve independent human solo alternatives and the ordinary exit to Room 9. |
| **146**, Moonlight Mansion Room 18 | Door toward Goal 2's Room-18 entrance; inspect `ROOM_2_18_BOTTOM_RIGHT -> ROOM_2_GOAL_2_UPPER_LEFT` | A large stone block obstructs the goal-room door. Cooperative inhaling and repeated Final Cutter nudges are both documented. | Exact object/template variant, helper count and positioning, reliable solo alternative, and alignment of native doorway/treasure compartment with the existing AP splits. Other Room 18 doors are not automatically Phone-dependent. |
| **315**, Mustard Mountain Room 12 | Upper secret doorway toward a different part of Room 13; compare ordinary `ROOM_4_13` and `ROOM_4_13__LOGIC__CANNON_LEFT` entries | Helpers can move a Heave-Ho Block to plug the volcano and expose the upper route. An ordinary lower route to Room 13 is also described. | Exact destination spawn/compartment, object variant, solo movement alternatives and full traversal. Do not turn the whole Room 12-to-13 connection into a Phone gate. |
| **310**, Mustard Mountain Chest | `MAJOR_CHEST_MUSTARD_MOUNTAIN` | A nearly immediate small-switch gate has an explicitly suggested helper solution. | CPU switch holding, arrival side, gate timing, enemy interference and collection. The static switch-height obstruction in #1052 prevents assuming any flat projectile is a substitute. |
| **426**, Candy Constellation Chest 3 | `MAJOR_CHEST_CANDY_CONSTELLATION` | Three small switches form the map puzzle. Swift movement and breath attacks, or friends, are described; a lower path bypasses the puzzle. | Reproducible solo and helper sequences for the chest. Preserve the bypass to Goal 2 independently. |
| **511**, Cabbage Cavern Room 5 | `MINOR_CHEST_MUSIC_NOTE_09` | The Secret Sounds chest can be reached by a switch-and-rush sequence, with friends as an alternative. | Measured route execution, helper positioning and control cases. This is not evidence that Phone is mandatory. |
| **804**, Labyrinth Entrance Stage, room 2 | `REGION_TUTORIAL/ROOM_0_02 -> REGION_TUTORIAL/ROOM_0_03` | The tutorial describes friends holding a small switch while another Kirby reaches a Bomb Block. It then teaches ordinary super-inhale movement of a Heave-Ho Block. | Fresh-start safety if Phone is locked before the tutorial is cleared; ambient helpers, any independent solo solution, and the actual AP startup path. Do not assume an item placed beyond the tutorial can solve its own entrance requirement. |

Room sources: [Carrot 16](https://wikirby.com/wiki/Carrot_Castle_-_Room_16), [treasure reference](https://wikirby.com/wiki/Treasure), [Moonlight 18](https://wikirby.com/wiki/Moonlight_Mansion_-_Room_18), [Moonlight Goal 2 compartments](https://wikirby.com/wiki/Moonlight_Mansion_-_Goal_2), [Mustard 12](https://wikirby.com/wiki/Mustard_Mountain_-_Room_12), [Mustard Chest](https://wikirby.com/wiki/Mustard_Mountain_-_Chest), [Candy Chest 3](https://wikirby.com/wiki/Candy_Constellation_-_Chest_3), [Cabbage 5](https://wikirby.com/wiki/Cabbage_Cavern_-_Room_5), and [Labyrinth Entrance Stage](https://wikirby.com/wiki/Labyrinth_Entrance_Stage). These are descriptive gameplay references, not substitutes for native/runtime acceptance.

### Existing graph annotations are not proof of a solution

At the pinned AP baseline, [rooms.json](https://github.com/hasherwi/Archipelago-kirbyam/blob/7a198f4ff09a0b3a279dc61bc420bc57a0d62c10/worlds/kirbyam/data/regions/rooms.json) leaves the Carrot 16 Yellow, Cabbage 5 Secret Sounds, and Candy Chest 3 map requirements null. The Mustard map includes the pending `can_hit_far_switch` token. The two Mustard Room 12 exits carry `can_break_block`; Moonlight Room 18's bottom-right/Goal 2 upper-left connection is null. These were the historical annotations to reconcile, not source evidence that Phone is unnecessary or that all alternatives work.

The Moonlight Goal 2 physical room is split into AP compartments. The wiki places the Chalk chest in the chamber reached from Room 18; the current JSON lists its chest key under `ROOM_2_GOAL_2`. The later [native acceptance review](phone-heave-ho-acceptance.md) resolves this mapping to the upper-left compartment and its bottom-right return. That correction does not activate a Phone-dependent rule.

## Small-switch coverage

The existing [#1052 inventory at `3828e3f2`](https://github.com/hasherwi/Archipelago-kirbyam/blob/3828e3f2cdb6b7297ac5817a10a76491ab483c39/worlds/kirbyam/dev-docs/small-switch-inventory.md) reports **35 instances in 24 native rooms**, from all 983 room slots and 287 object lists, with all 37 native Object Spawners checked and none spawning a small switch. Its [JSON manifest](https://github.com/hasherwi/Archipelago-kirbyam/blob/3828e3f2cdb6b7297ac5817a10a76491ab483c39/worlds/kirbyam/dev-docs/small-switch-inventory.json) is reused as evidence rather than copied or modified here. This review checked its counts, native room/AP joins and the absence of native room 733; it did **not** rerun that ROM extraction.

The complete native-room queue is: `147, 177, 209, 228, 310, 404, 426, 427, 511, 527, 533, 608, 610, 707, 708, 712, 720, 742, 804, 815, 825, 831, 911, 915`. Keep all of them in scope for a future helper audit, not just those that already have a `can_hit_far_switch` token. The Dimension Mirror rooms `911` and `915` have no AP room key in that inventory and must not disappear from gameplay review for that reason.

The inventory distinguishes contact/race puzzles, remote alternatives, cooperative candidates and separated targets. For example, Moonlight 19 has an ordinary timing solution and a clear initial ranged lane; Olive Goal 2 has a separated switch; Olive Chest 1 has a staged inhale/spit puzzle. None implies that summoned CPU Kirbys can reliably stand on the required side of every gate. The proposed Phone item is not a blanket grant for all 35 switches.

## What the native source establishes

### Small switches and Big Switches are different

[big_small_switch.c](https://github.com/jiangzhengwenjz/katam/blob/1197474f80e5de282fbedcd0025ebfa61f61a764/src/big_small_switch.c) sets `unkB8 = FALSE` in `CreateSmallSwitch` and `TRUE` in `CreateBigSwitch`. In `sub_081194DC`, eligible block overlap, Kirby overlap and interaction flags are separate activation paths. Its final `0x40000` branch accepts a small switch directly, while a Big Switch takes an additional human-player check. This supports investigating companion activation of small switches; it does not establish pathfinding, attack compatibility, or arrival positions.

Do not confuse the small-switch candidates with the permanent Big Switch hub unlocks or the independently itemized Lever Walls. This review does not add a Phone dependency to either system.

### Heave-Ho movement is not simply a Phone check

[star_stone_block.c](https://github.com/jiangzhengwenjz/katam/blob/1197474f80e5de282fbedcd0025ebfa61f61a764/src/star_stone_block.c) provides stronger evidence than visual size alone:

- `sub_0811EA60` accumulates signed contributions from each Kirby's two-bit interaction field, with up to two units per Kirby; opposite-side contributions can cancel.
- `sub_0811EC80` calls this for all four Kirby slots and compares the absolute total with `unkE1`. Ordinary constructors select thresholds 2 or 3 according to template bit 0.
- The [0x7D constructor](https://github.com/jiangzhengwenjz/katam/blob/1197474f80e5de282fbedcd0025ebfa61f61a764/src/large_stone_block_7D.c) and specialized [0x7E](https://github.com/jiangzhengwenjz/katam/blob/1197474f80e5de282fbedcd0025ebfa61f61a764/src/large_star_stone_block.c), [0x88](https://github.com/jiangzhengwenjz/katam/blob/1197474f80e5de282fbedcd0025ebfa61f61a764/src/large_star_stone_block_88.c) and [0x89](https://github.com/jiangzhengwenjz/katam/blob/1197474f80e5de282fbedcd0025ebfa61f61a764/src/large_star_stone_block_89.c) constructors use thresholds 4 or 5. One Kirby's maximum two-unit contribution cannot satisfy those thresholds by itself through this branch.
- A separate zero-contribution branch responds to `sub_08070504`, a same-room event flag queried in [code_0806F780.c](https://github.com/jiangzhengwenjz/katam/blob/1197474f80e5de282fbedcd0025ebfa61f61a764/src/code_0806F780.c), and can set block horizontal speed without passing the collective-inhale threshold. Direction, obstruction and event transitions still matter. The gameplay reference's ground-shaking alternatives and Moonlight 18's Final Cutter alternative are consistent with this distinct path; this is not an exhaustive verified move list.

The actual template variant and geometry must be matched to each physical block. This review did not enumerate all native Heave-Ho templates, dynamically spawned instances, or their room usage. Therefore it does not claim the two highlighted room routes are an exhaustive native inventory, nor that every smaller-looking block is solo-movable.

### Calling allies has native preconditions and separate input paths

The [Cell Phone reference](https://wikirby.com/wiki/Cell_Phone) distinguishes R to summon allies, which consumes battery, from holding L to return to Central Circle without battery consumption. It also describes health recovery from summoned friends and distinct native link-multiplayer behavior. Those effects matter to regression testing even though they are not additional proven traversal requirements.

In [kirby.c](https://github.com/jiangzhengwenjz/katam/blob/1197474f80e5de282fbedcd0025ebfa61f61a764/src/kirby.c), `Macro_0803FF64_7` checks the `0x100` input branch, battery, room priority flags, existing call state and player eligibility; `sub_080572A0` decrements battery on the ordinary initiating-call path. Other state-specific call entry paths also exist. A gate must cover the intended player-initiated summon action without indiscriminately suppressing L, altering native restrictions, or modifying already-active calls.

[cpu_kirby_trigger.c](https://github.com/jiangzhengwenjz/katam/blob/1197474f80e5de282fbedcd0025ebfa61f61a764/src/cpu_kirby_trigger.c) contains room/template-dependent triggers for Kirby positions and block positions. Their presence reinforces that helper behavior is contextual; it is not proof that Phone ownership yields any requested action on demand. This review has not fully traced the CPU state machines or all room trigger templates.

## Future implementation contract

1. Gate only the approved summon action. Preserve the ordinary L return-to-hub action before and after receipt, including zero battery and native disallowed states.
2. Model a verified **small-switch or Heave-Ho helper-assisted route**, not `has(Phone)` as a universal substitute for attacks, switch contact or inhaling. Record caller location, reachable helper landing/approach, required battery/retry assumptions, helper behavior and complete traversal or collection.
3. Keep independent solo witnesses as alternatives. Do not require Phone where a reviewed ordinary timing, breath, source-backed attack or bypass route succeeds.
4. Distinguish ownership of an action from a summoned companion's ability, ability source, and AI behavior. Never credit a helper's ability attack or discarded ability. Review source randomization only for interference with eligible cooperation, not as permission to use helpers as ability providers.
5. Decide and document the behavior of already-present or naturally arriving CPU allies, answering another Kirby's call, canceled calls, and native link play. A player-summon gate is not automatically a global ban on companions. AP multiworld synchronization is not native four-player link multiplayer.
6. Prove fresh-start safety, particularly the tutorial cooperation puzzle. Verify the actual startup/skip configuration rather than assuming all games begin after the tutorial.
7. Add item classification, item-pool balance, slot-data/protocol, receipt persistence and seed/slot isolation only in the implementation PR. Phone must be classified for any progression routes that actually depend on it. Preserve the existing save and transport contracts.

## Required acceptance evidence before enabling routes

- Locked/unlocked R behavior in normal, underwater and relevant ability-specific states; zero/full battery; repeated presses, canceled calls and interruption. Show that a rejected locked attempt has no unintended battery, call-state or control side effect.
- L return-to-Central-Circle regression before receipt, after receipt and at zero battery, respecting native restrictions rather than inventing unrestricted escape behavior.
- For each accepted route: a fresh-start or explicitly qualified fixture, exact native room and AP target, helper setup, uninterrupted successful traversal/collection, and a matching no-helper/no-Phone control. Record independent solo successes too.
- Carrot 16 helper Bomb Block/Yellow chest observations stay historical and excluded from progression. Human solo/source-backed alternatives are separate; no additional helper-attack proof can make this an eligible Phone witness under the current design.
- Moonlight 18 and Mustard 12 specifically: actual block variant, required cooperative interaction, alternate solo nudges, exact exit spawn and downstream collectible access. Do not replace a directional route with whole-room gating.
- Coverage review of all 24 small-switch rooms plus a fresh Heave-Ho object/template/spawner inventory, followed by room-specific CPU/runtime checks. Keep future helper progression limited to small switches and Heave-Ho blocks; other observed cooperative behavior is not an eligible witness.
- AP generation and reachability tests with Phone absent/present and solo alternatives absent/present; no self-locking placement; source-randomization/action-gate combinations; repeat receipt, reconnect, offline delivery, restart and cross-seed/slot isolation.

## Validation and limitations of this document

Checked the pinned AP item catalog, room requirements, native-room mapping, existing small-switch JSON inventory, native switch/block/call code, and the linked gameplay references. Mechanical checks verify the seven candidate room IDs against the mapping, the named AP room/location targets against the baseline JSON, the 35/24 inventory totals, and Carrot 16's absence from that switch inventory. Markdown syntax, whitespace and the documentation-only diff were checked separately.

The original documentation-only revision did not perform native replay, full-ROM object extraction, ROM rebuild, Python world tests or generation tests. The later implementation milestone and its separately scoped evidence are described in [phone-implementation.md](phone-implementation.md). No runtime acceptance or exhaustive Phone route coverage is claimed. #1052's existing replays test particular attacks; they are not Phone helper witnesses. Existing source/page coverage gaps remain gaps, and no inaccessible page was retrieved through an alternative route. Human review and the remaining acceptance work are necessary before production activation.
