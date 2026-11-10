# Phone helper acceptance: native room 146

Status: **qualified fixture success, not an accepted production traversal**. AI-assisted research, 2026-11-10. See the [implementation boundary](phone-implementation.md) and [sanitized input/checkpoint ledger](phone-heave-ho-evidence.json).

## Positive and negative controls

Two identical runs enter native room 146 through its real room-145 doorway, summon three native CPU Kirbys, displace the large `0x7D` block, and cross the bottom-right door into room 148. A matched unowned control uses the same inputs and frame schedule, spends no battery and remains blocked in room 146. The only runtime writes in the successful runs are the real client's guarded Phone grant and epoch publication. No pose, ability, enemy, switch or CPU state is injected.

The preboot fixture sets initial rooms to 145, 148, 148, 148; local position to `(1170,144)`; CPU positions to `(96,112)`; a synthetic seed identity; and experimental Phone activation. It starts with a blank native save and disabled ability-gate/source-randomization settings. All Kirbys remain Normal at the successful runs' recorded checkpoints. This is not a route from the real restart hub.

After native entry and the real grant, the successful sequence is Right 25 frames, R 60, neutral 600, B 240, Right 120, A 30, Right 83, Up 1, neutral 120. It consumes one of three initial batteries and ends in room 148 at `(40,88.996)`. The same unowned sequence ends in room 146 at `(153.996,105.996)`.

The observed physical doorway maps `ROOM_2_18_BOTTOM_RIGHT` to `ROOM_2_GOAL_2_UPPER_LEFT`; this identifies the endpoint, not where a future Phone requirement belongs. The current graph first has an internal `ROOM_2_18` to `ROOM_2_18_BOTTOM_RIGHT` edge. That approach is the candidate barrier surface, followed by the doorway. The native door at source tile `(13,8)` enters room 148 at spawn tile `(3,6)`, matching the recorded arrival. Native return from 148 enters room 146 at tile `(13,9)`, but the current return edge targets `ROOM_2_18` directly, so that compartment mapping also needs review before a binding is installed. These observations do not certify every room-146 exit or room-148 compartment. The documented Final Cutter solo alternative is preserved, but was not replayed in this investigation. The goal-room upper-left region has no check and no edge to its main region in the current graph; a later screenshot is not an independently decoded AP chest-flag or chest-access proof.

## Native ability disposal is real, but not sufficient

In native source commit `7d969fbce14fdc838d2c1ea01389717fb96c3189`, room 146's helper program requests Normal: opcode 3 with operand `0xFFFF` sets desired ability to `0xFF`, then navigation and timed B input continue. `sub_080152B0` schedules `sub_080186DC` to discard a held non-Normal ability with Select. The timed-B chain ultimately emits B input. The large block still requires collective inhale; it does not test Phone ownership.

Neutral delays in room 145 allowed helpers to acquire abilities naturally. A 9,000-frame contrast produced Missile; a 24,000-frame contrast produced Fire, Fire and Beam. These were not ability fixtures or runtime injections. After summoning, the helpers eventually became Normal, and read-only checkpoints show native timed-B behavior. Nevertheless, the baseline crossing and longer reposition/inhale attempts failed. The public ledger contains the baseline natural-ability contrasts; the separate exploratory reposition/retry ledgers are not included. Different arrival positions and timing remain unresolved. Normalization alone therefore does not justify a universal Phone rule.

The pinned source files are `src/code_0800ECAC.c` and `src/code_0800ECAC_2.c`. This is the local source revision used for runtime analysis, distinct from the newer revision pinned in the original prose audit.

## Native reload restores charges and ownership

A successful qualified run saved native battery RAM with two charges and Phone ownership. A fresh emulator instance loaded that save before its first frame and followed the ordinary menus, with no new client writes. It started with three charges, Phone still owned and all Kirbys Normal. A corrected doorway-alignment replay then repeated the 145-to-146-to-148 crossing without runtime writes.

This establishes native refill and persistent ownership for the configured startup. It does not establish an open, progression-safe route from the actual hub back to this barrier, or reliable CPU state after an arbitrary approach. The native `CreateKirby` initializer sets Normal and three charges independently of saved Phone ownership.

## Acceptance decision

Do not install a `has(Phone)` witness yet. A reproducible real-start approach and a reliable positioning/retry procedure are still required. Naturally present helpers remain a separate non-Phone case. Other small switches and the large blocks in rooms 315 and 322 require their own proofs; room-146 results do not transfer to them.

## Contact and freeze diagnostics

Later two-call regroup trials gathered all three helpers in room 145, entered 146 through the real doorway, and normalized a naturally acquired Missile ability. They still did not certify a crossing. Helpers stayed left of the block; neither opposing contributions nor the room-state completion trigger explained these failures.

The [native block source](https://github.com/jiangzhengwenjz/katam/blob/1197474f80e5de282fbedcd0025ebfa61f61a764/src/star_stone_block.c) checks contact separately from inhale strength. A contributing Kirby on the left can also set obstruction bit `0x20` when its collision bounds overlap the block's horizontally expanded rectangle. Positive summed inhale cannot move the block while that bit is set. In the configured trial, caller x139 had actual Normal bounds `[-6,-5,+6,+7]` and overlapped the block's expanded x141–179 rectangle. Obstruction was observed; moving close enough to inhale is not by itself a valid pulling arrangement.

Source analysis also found a distinct timing problem. Native copy acquisition freezes other Kirbys in the same room. The acquiring Kirby bypasses the freeze to complete its transition, then releases it. A helper may therefore cause a room-wide pause while its sampled ability is still Normal, before the new ability is assigned. Repeated ability disposal/reacquisition can interrupt short controller batches.

A [read-only freeze diagnostic](phone-room-freeze-evidence.json) held Left continuously. Over 69 video frames, 49 samples were frozen and 20 were eligible under the sampled input/update checks. The caller moved from x139 to x119.281; during the freeze it stayed at x138.75. The observed freeze mask was `0x0F` with owners `[2,2,2,2]`. This confirms that elapsed video frames and movement-update opportunities must be distinguished. It proves steering under those conditions, not a pull or crossing.

These findings narrow the investigation without accepting a Phone witness. A source-derived initial pull position still needs a reproducible controller route and native movement/completion proof. The original successful fixture and all later failed controls remain distinct.

The native gate ledger's schema 2 also corrects a historical field label: `kirby_unkC` reads base+0x0C. It was previously named `kirby_flags`, but is not the true flags field at base+0x08. Values and prior movement/receipt/tutorial observations are unchanged; no flag-bit interpretation was used to establish those observations.

## Bounded inhale controls

A later [continuous-B control](phone-inhale-retry-evidence.json) observed 1,200 pre-frame block-eligibility samples across 1,734 video frames. The caller started stationary, Normal and right-facing at `(88.930,136.996)`. The block stayed at `(160,127.996)` and room state 15 stayed zero, including after obstruction bit `0x20` cleared. End-frame aggregate inhale values were only 0, 1 or 2, never the threshold of 4. These are sampled fields, not instruction breakpoints or individual Kirby contribution measurements.

The caller's first recorded inhale state lasted 243 samples, then changed to ordinary movement at frame 13,510 for the remaining 1,491 samples while controller B and decoded held input both stayed 2. Native `sub_08054950` has a finite empty-inhale path, but animation and the inhaling byte were not separately captured, so this observation does not identify the exact branch taken. Continuous B did not restart the inhale in this trial. The bounded procedure failed to move the block; it does not establish that Phone traversal is impossible.

A release/re-press variant then restarted the human inhale eight times, producing nine recorded inhale starts across 1,735 video frames and 1,200 pre-frame block-eligibility samples. The caller remained Normal and spent 1,719 samples in the inhale state. However, all 69 end-frame samples with aggregate strength 4 coincided with obstruction (`E3=0x21`, terrain field `0x62=0x06`) and a helper at x139. Native contact also shifted the caller from x88.930 toward x78.930, out of the conservative horizontal reach. The block never moved and room state 15 stayed zero. Re-pressing fixes the sustained-input problem in this trial, but not collective positioning. The ledger records all restart frames and inhale-start positions; horizontal range candidates are not attributed contributions. No crossing was attempted after either failed control.
