# Lever and late ability runtime regressions (v0.4.0)

## Evidence for #911 and #912

The four AP levers are **Chest objects with reward 0x63**, not the small-switch
effect dispatcher previously intercepted at `0x08119B98`. Consequently, physical
activation never reached that old hook, did not set `lever_activation_flags`, and
continued through the native chest wall-opening path.

The repository's four pre-lever BizHawk savestates independently identify the
following live objects. These are observations of existing RAM snapshots, not a
new emulator test or an acquired ROM:

| Repository state | Native room | Source pointer | Object type | Reward | Chest ID | AP bit |
|---|---:|---|---|---|---:|---:|
| `2 - Moonlight Mansion/2 - 3 Lever.State` | 743 | `0x088BE07C` | `0x81` | `0x63` | 18 | 0 |
| `6 - Olive Ocean/6 - 26 Lever.State` | 824 | `0x088CD240` | `0x81` | `0x63` | 65 | 1 |
| `5 - Carrot Castle/5 - 6 Lever.State` | 170 | `0x088D2E68` | `0x81` | `0x63` | 77 | 2 |
| `8 - Radish Ruins/8 - 15 Lever.State` | 619 | `0x088D1454` | `0x81` | `0x63` | 74 | 3 |

These historical state filenames use an older room numbering convention; AP
location names and IDs remain Moonlight 2-11, Olive 6-13, Carrot 5-12, Radish 8-12.
The payload matches exact source pointer, reward, and chest ID together instead
of interpreting a current-room label as proof of an activation.

### Source provenance

US decomp revision `7d969fbce14fdc838d2c1ea01389717fb96c3189`:

- [chest.c](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/chest.c): `sub_0800AFC8` collects the chest; `sub_0800B97C` grants the delayed room-counter increment for reward 0x63; `sub_0800BD4C` applies the same counter on later loads if `HasChest` is true.
- [lever_wall.c](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/lever_wall.c): the wall tests the room counter, rather than directly polling a chest bit.
- [code_080023A4.c](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/code_080023A4.c): `sub_080029F4` adds to `gUnk_02023510[roomSlot]`.
- [data.h](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/include/data.h): Chest/Object/LevelInfo field layout, including Object callback fields and `LevelInfo::unk65E`.
- [object.c](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/object.c): `ObjectMain` invokes the auxiliary `unk7C` callback before the object's normal update, then updates its sprite variant from `unk83`.
- [mGBA serialized layout](https://github.com/mgba-emu/mgba/blob/master/include/mgba/internal/gba/serialize.h): IWRAM starts at serialized offset `0x19000`; EWRAM at `0x21000`. The checked-in BizHawk archives use zstd-compressed Core.bin with a four-byte length prefix before the mGBA state. The four states contain native waiting-chest callback `0x0800AEB1`, reward `+0xE0`, chest ID `+0xE2`, source pointer `+0xB0`, and room `+0x60`.

## Corrected lifecycle

1. The existing verified `CollectChest` hook recognizes the four exact lever
   sources, latches the physical AP check, and returns without setting the
   native wall-ownership bit or reporting an ordinary chest event.
2. Only native `sub_080029F4` calls discovered within the chest-popup function
   (`0x0800B97C..0x0800BD4B`) are redirected. The wrapper suppresses the lever's
   delayed wall counter increment; every other chest retains native behavior.
3. The big-chest object table initializer pointer is validated against
   `sub_0800BD4C` before replacement. The lever-aware wrapper preserves native
   initialization, but uses the physical AP latch for the lever's open/closed
   appearance and interaction callback. Receiving a wall item first therefore
   does not consume its lever check.
4. A lever-only auxiliary object callback observes the AP-owned native chest
   bit and contributes exactly once to that object's room counter. It handles
   receipt before activation, after activation, while the popup runs, and on
   room reload. Native initialization applies an already-owned wall once; the
   per-object `Chest::unkDC` latch prevents a duplicate contribution.
5. The old small-switch wrapper becomes transparent. No ordinary small switch
   is gated just because it happens to be in an AP lever room.

The mailbox layout, item IDs, and location IDs do not change. Physical activation
is an EWRAM-session latch, while native chest bits persist AP wall ownership.
A reset can make a previously pulled lever interactable again; AP server check
deduplication still prevents a second reward.

## #892: gate the final native ability commit

The US [Kirby source](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/kirby.c)
shows that the existing request/start hooks run before all pending-ability
changes are finished. Native roulette `sub_0805C3B8` rewrites
`Kirby::transitioningAbility` after those entry hooks. Both ordinary and roulette
transitions install `sub_0805C618` as their final state callback, where it copies
the pending low five bits to `Kirby::ability` and dispatches that ability.

The patch validates the two aligned callback-pointer literals in the bounded
installer functions and redirects them to a wrapper that reapplies the existing
unlock mask immediately before calling the native final state. This closes the
verified late-write bypass without guessing a collision instruction offset or
rerolling any native state. It preserves all upper transition flags and normal
animation behavior. It does **not** establish which native path caused the
original damage/Waddle Doo report; that exact reproduction remains necessary.

## Validation and remaining release gates

- Native-C tests execute the actual lever collection, initialization, auxiliary
  update, popup-counter wrapper, and final ability gate with platform IO stubbed.
  Both receipt orders, all four levers, duplicate updates, room reloads,
  nonlever behavior, and all 31 ability IDs/eight upper-flag combinations are
  covered.
- Synthetic patch tests validate target scope, Thumb pointer bits, BL targets,
  and refusal on missing/changed original targets before mutating a ROM.
- The ARM payload builds within the existing reserved code/config window.
- The committed shared base patch still needs regeneration from the maintainer's
  clean USA ROM before generated games contain these source changes. Synthetic
  fixtures are never a release base patch.
- BizHawk acceptance: for each lever, test physical-first and item-first order,
  delayed popup receipt, leaving/reentering, reconnect and reset. Physical pull
  must send one check and leave the wall closed without the item; item receipt
  must open the wall without consuming the lever. Confirm ordinary small
  switches, ordinary/minor and collection chests, and other room counters.
- Reproduce #892 with its original damage/contact sequence, locked and unlocked
  Tornado, every randomization mode, dropped stars, mix roulette, and gating off.
  Inspect pending/active ability fields and live gate masks. Until reproduced,
  describe the code change as final-commit hardening rather than a verified
  resolution of every collision path.
