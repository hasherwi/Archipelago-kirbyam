# Phone helper acceptance: native room 146

Status: **qualified fixture success, not an accepted production traversal**. AI-assisted research, 2026-11-10. See the [implementation boundary](phone-implementation.md) and [sanitized input/checkpoint ledger](phone-heave-ho-evidence.json).

## Positive and negative controls

Two identical runs enter native room 146 through its real room-145 doorway, summon three native CPU Kirbys, displace the large `0x7D` block, and cross the bottom-right door into room 148. A matched unowned control uses the same inputs and frame schedule, spends no battery and remains blocked in room 146. The only runtime writes in the successful runs are the real client's guarded Phone grant and epoch publication. No pose, ability, enemy, switch or CPU state is injected.

The preboot fixture sets initial rooms to 145, 148, 148, 148; local position to `(1170,144)`; CPU positions to `(96,112)`; a synthetic seed identity; and experimental Phone activation. It starts with a blank native save and disabled ability-gate/source-randomization settings. All Kirbys remain Normal at the successful runs' recorded checkpoints. This is not a route from the real restart hub.

After native entry and the real grant, the successful sequence is Right 25 frames, R 60, neutral 600, B 240, Right 120, A 30, Right 83, Up 1, neutral 120. It consumes one of three initial batteries and ends in room 148 at `(40,88.996)`. The same unowned sequence ends in room 146 at `(153.996,105.996)`.

The exact AP surface is `ROOM_2_18_BOTTOM_RIGHT` to `ROOM_2_GOAL_2_UPPER_LEFT`. It does not certify every room-146 exit or every room-148 compartment. The documented Final Cutter solo alternative is preserved, but was not replayed in this investigation. A later screenshot supports chest collection visually; there is no independently decoded AP chest-flag claim.

## Native ability disposal is real, but not sufficient

In native source commit `7d969fbce14fdc838d2c1ea01389717fb96c3189`, room 146's helper program requests Normal: opcode 3 with operand `0xFFFF` sets desired ability to `0xFF`, then navigation and timed B input continue. `sub_080152B0` schedules `sub_080186DC` to discard a held non-Normal ability with Select. The timed-B chain ultimately emits B input. The large block still requires collective inhale; it does not test Phone ownership.

Neutral delays in room 145 allowed helpers to acquire abilities naturally. A 9,000-frame contrast produced Missile; a 24,000-frame contrast produced Fire, Fire and Beam. These were not ability fixtures or runtime injections. After summoning, the helpers eventually became Normal, and read-only checkpoints show native timed-B behavior. Nevertheless, the baseline crossing and longer reposition/inhale attempts failed. The public ledger contains the baseline natural-ability contrasts; the separate exploratory reposition/retry ledgers are not included. Different arrival positions and timing remain unresolved. Normalization alone therefore does not justify a universal Phone rule.

The pinned source files are `src/code_0800ECAC.c` and `src/code_0800ECAC_2.c`. This is the local source revision used for runtime analysis, distinct from the newer revision pinned in the original prose audit.

## Native reload restores charges and ownership

A successful qualified run saved native battery RAM with two charges and Phone ownership. A fresh emulator instance loaded that save before its first frame and followed the ordinary menus, with no new client writes. It started with three charges, Phone still owned and all Kirbys Normal. A corrected doorway-alignment replay then repeated the 145-to-146-to-148 crossing without runtime writes.

This establishes native refill and persistent ownership for the configured startup. It does not establish an open, progression-safe route from the actual hub back to this barrier, or reliable CPU state after an arbitrary approach. The native `CreateKirby` initializer sets Normal and three charges independently of saved Phone ownership.

## Acceptance decision

Do not install a `has(Phone)` witness yet. A reproducible real-start approach and a reliable positioning/retry procedure are still required. Naturally present helpers remain a separate non-Phone case. Other small switches and the large blocks in rooms 315 and 322 require their own proofs; room-146 results do not transfer to them.
