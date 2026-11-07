# Copy Ability Room on native saves: acceptance

This updates draft PR #1025 onto main `744b1a5708ecaafd80313b7836a9197a25f5db0e`
without restoring the removed single-file selector bypass or expanded save format.
PR #1041 traversal work is separate.

## Tested build

- USA retail input SHA-1: `274b102b6d940f46861a92b4e65f89a51815c12c`.
- Rebuilt `base_patch.bsdiff4` SHA-256:
  `a5c91a06b9676d84132e3be053f007dff0289232f8ebaa85c6f7ae9d255d924d`.
- Emulator: mGBA 0.10.5 on ARM64 Linux.
- Production protocol 2 and the real Kirby client `ReceivedItems` callback were
  exercised through an in-process BizHawk-compatible transport with simulated
  complete server histories. This is not an external-server or BizHawk Lua test.

The gate fixture changes only the initial room/spawn to Central Circle and the
ROM's seed identity to synthetic test bytes. Its SHA-256 is
`513d3fd3a082a16de74a409523e99adfcd7b0df37c1f536b98783d224f249945`.
The gated statue variant additionally uses the normal ability-gating config.
The menu Back case uses the production tutorial origin. The all-hubs negative
case starts with a checksummed legacy save containing all 15 hub words and the
old native word-18 unlock, rather than playing a 15-switch campaign.

After initial setup, movement and entry use controller input. Read-only telemetry
and save inspection record the results. Across 12 final runtime cases, the only
30 client writes were the four-byte ownership and epoch requests at
`0x0203B164` and `0x0203B160`. No native ownership, position, ability, equipment,
WORLD word-18 or save bytes were injected during the proof.

## Native results

- All three files can be selected normally. Fresh item-absent Up attempts remain
  in 801; receipt opens the mirror and the same aligned Up enters 970.
- Each file's authenticated grant survives an offline cold reload. Both native
  WORLD copies for all three files retain valid checksums. Other files remain
  unowned, and the native descriptors, file selector, Back target and save-copy
  offsets retain their original bytes.
- File 3 mode menu → Back → three-file selector → Adventure works. Back does not
  modify any saved WORLD bytes.
- Disconnect and a new socket before complete history preserve offline ownership.
  Complete empty current-socket history revokes, and later receipt regrants.
- Revocation at the doorway does not move Kirby, and Up is immediately denied.
  The already-open native graphic can remain blue. Cold reload restores a closed
  mirror; regrant opens it and permits entry again.
- All 15 saved physical-hub states, legacy word 18, and complete Hub Connection
  receipt history alone do not grant the Copy Room item.
- Explicit precollection grants room access. Access leaves the ability-unlock
  mask at zero. An ordinary statue touch equips Bomb (ID 9) when gating is off;
  the identical touch remains Normal (ID 0) with gating on and no ability items.
- Pause/map return preserves authenticated ownership and the active epoch.

## Other regression coverage

Host tests cover all three slots, seed changes, previews, invalid slots, inactive
or replaced tasks, failed native saves and retries, stale epochs, async history
and session changes, capability mismatches, item/region logic and RoomSanity's
unchanged 263 checks. Protected native patch sites and saved-layout byte ranges
are checked against the retail source. All 287 native object lists were examined
for WORLD-word consumers; the reserved Copy Room words 22–26 do not overlap the
existing Hub record in words 27–31.

Installed-APWorld generation exercises the ordinary default and actual YAML
`start_inventory` in single-player and AP multiworld seeds, with RoomSanity on
and off. The existing world does not expose optional `start_inventory_from_pool`;
this feature does not add that unrelated option.

## Limits

- No randomized full campaign, actual death/continue, Dark Mind sequence or full
  Boss Endurance gauntlet was completed. Damage and pause/map checks do not stand
  in for death/continue acceptance.
- Native linked-GBA multiplayer remains unsupported. AP multiworld is separate.
- Arbitrary save-state rollback is not a durability guarantee. Native save
  failures retry only while the same authenticated Adventure context stays live.
- Prototype expanded-format saves are not migrated. Preserve originals and use
  matching generated seed, ROM patch and client versions.
- Immediate entry denial is authoritative on revocation. Cosmetic closure waits
  for a full Central Circle reload; ordinary leave/reentry may reuse its room
  buffer while an AI Kirby remains there.

Full ROMs, saves, emulator states and screenshots are not included in the PR.
