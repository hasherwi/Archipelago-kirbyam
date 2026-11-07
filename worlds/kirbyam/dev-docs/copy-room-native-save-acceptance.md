# Copy Ability Room on native saves: acceptance

This updates draft PR #1025 onto main `744b1a5708ecaafd80313b7836a9197a25f5db0e`
without restoring the removed single-file selector bypass or expanded save format.
PR #1041 traversal work is separate. Room access is a permanent grant within the
authenticated seed and native save file; it is never reconciled downward.

## Tested build

- USA retail input SHA-1: `274b102b6d940f46861a92b4e65f89a51815c12c`.
- Rebuilt `base_patch.bsdiff4` SHA-256:
  `1635d972f40f0b843b326cf0a8ab44033591713df1258ee74b4073e27a0e5fcd`.
- Emulator: mGBA 0.10.5 on ARM64 Linux.
- Production protocol 2, the real Kirby client `ReceivedItems` callback and Copy
  Room sync function were exercised through an in-process BizHawk-compatible
  transport with simulated histories and sockets. This is not an external-server,
  complete game-watcher pipeline or BizHawk Lua test.

The gate fixture changes only the initial room/spawn to Central Circle and the
ROM's seed identity to synthetic test bytes. Its SHA-256 is
`79a533a95eaa6a30897cca347f626ad32889bb3a778660575f7d96b4dbaad0ee`.
The gated statue variant additionally uses the normal ability-gating config.
The menu Back case uses the production tutorial origin. The all-hubs negative
case starts with a checksummed legacy save containing all 15 hub words and the
old native word-18 unlock, rather than playing a 15-switch campaign.

After initial setup, movement and entry use controller input. Read-only telemetry
and save inspection record results. The final 13-case matrix contains 24 four-byte
mailbox writes at `0x0203B164` and `0x0203B160`: 12 production grant writes and 12
separately labeled adversarial zero-request writes. Empty histories and redundant
grants produce no client writes. No native ownership, position, ability,
equipment, WORLD word-18 or save bytes are injected during the proof.

## Native results

- All three files can be selected normally. Fresh item-absent Up attempts remain
  in 801; receipt opens the mirror and the same aligned Up enters 970.
- Each file's authenticated grant survives an offline cold reload. Both native
  WORLD copies for all three files retain valid checksums. Other files remain
  unowned, and native descriptors, file-selector bounds and save-copy offsets
  retain their original bytes.
- File 3 mode menu → Back → three-file selector → Adventure works on the final
  patch with the production start tables. Back leaves all 32 KiB of saved bytes
  unchanged, and normal reentry restores the selected file's ownership.
- Complete empty history after a grant leaves ownership, gate access and all
  32 KiB of saved bytes unchanged in every file. Current-epoch and noncurrent-
  epoch zero requests also cannot take the item away. Ordinary Up still enters
  970. The noncurrent test uses an adversarial mismatched epoch, not a captured
  old-session packet.
- Disconnect, an incomplete replacement-socket history and its eventual complete
  empty replay preserve the saved grant. Replaying an already-owned grant causes
  no redundant writes.
- A fresh File 2 remains locked when File 1 owns access, with File 1's WORLD
  copies unchanged. Loading an owned save with a different seed identity starts
  unowned for that new seed and denies entry. These are separate file/seed
  identities, not revocation of an item in its matching saved file.
- All 15 saved physical-hub states, legacy word 18, and complete Hub Connection
  receipt history alone do not grant the item. An aligned Up remains in 801.
- Explicit precollection grants access. Access leaves the ability-unlock mask at
  zero. An ordinary statue touch equips Bomb (ID 9) when gating is off; the
  identical touch remains Normal (ID 0) with gating on and no ability items.
- Start opens pause help, Select visibly switches to the Rainbow Route map, and
  B returns to gameplay with epoch and ownership intact. Gate entry still works.

## Other regression coverage

Host tests cover all three slots, seed changes, previews, invalid slots, inactive
or replaced tasks, failed native saves and retries, zero-request rejection, stale
positive grants across cleared/changed files, async history and session changes,
capability mismatches, item/region logic and RoomSanity's unchanged 263 checks.
Protected native patch sites and saved-layout byte ranges are checked against the
retail source. All 287 native object lists were examined for WORLD-word consumers;
reserved Copy Room words 22–26 do not overlap Hub words 27–31.

Installed-APWorld generation exercises the ordinary default and actual YAML
`start_inventory` in single-player and AP multiworld seeds, with RoomSanity on
and off. The existing world does not expose optional `start_inventory_from_pool`;
this feature does not add that unrelated option.

## Limits

- No randomized full campaign, actual death/continue, Dark Mind sequence, full
  Boss Endurance gauntlet, all-statue sweep or physical 15-switch campaign was
  completed. Damage and pause/map checks do not stand in for death acceptance.
- Native linked-GBA multiplayer remains unsupported. AP multiworld is separate.
- Arbitrary save-state rollback is not a durability guarantee. Native save
  failures retry only while the same authenticated Adventure context stays live.
- Prototype expanded-format saves are not migrated. Preserve originals and use
  matching generated seed, ROM patch and client versions.
- Earlier revocation/cosmetic-closing tests belong to a superseded candidate.
  The current grant-only contract has no item-revocation or mirror-closing path.

Full ROMs, saves, emulator states and screenshots are not included in the PR.
