# Native receipt/display verification (#953, #971)

Original verification baseline: main `99c63e3a505131d5ab16db60350a4c9c9daae54d`.
These reports are not closed by this verification work. No cheat-free emulator
reproduction or collection-menu acceptance was performed.

## Refresh against main

The PR was refreshed against main `ac4c30217aa726149de951aa5b21fed9a2840a26`.
All 176 focused mailbox, collection/wrapper, Vitality-history and HUD-hook tests
passed again on Linux. The changelog conflict was resolved by preserving every
entry under one Unreleased Internal Changes section. Native source, client,
payload and distributable files are unchanged by this PR; the original build
evidence below is historical and was not repeated for this documentation/test refresh.

## Executable evidence

`test_native_received_collections.py` compiles the shipping payload C with mapped
host EWRAM and executes its mailbox consumption/ACK path. ARM register captures
and two unrelated per-frame ROM callbacks are replaced; item dispatch, ownership
fields, Vitality writes and ACK logic remain the actual source.

- All 14 Spray Paint and 10 Music Sheet IDs write their native ownership bits.
  Sheets preserve the separate Sound Player bit, with and without that item.
  Reserved bits and physical chest flags are preserved. Repeated receipts are
  idempotent and each successful mailbox receipt ACKs exactly once.
- Vitality updates the active player's HP/max-HP fields immediately, for each of
  the four native player structures. Other players stay unchanged. Dead players
  remain dead, and duplicate receipts preserve subsequent damage.
- Existing wrapper, catalog, native Vitality history and HUD-hook tests remain
  unchanged. The focused suite passed 176 tests.

The native collection room reads `HasSprayPaint(j - 1)` and
`HasMusicPlayerOrSheet(j + 1)` in `sub_08143730`; these correspond to the fields
exercised above. That correspondence does not prove rendered menu refresh timing.

## Distributable/source agreement

The existing local clean USA input was SHA-1 validated before an in-memory build.
An ARM rebuild produced a 5,792-byte payload with SHA-256
`d27ceae383c113686655299b1532745bb47ab0188f554ced0c933fa3c11528a2`.
The shipped patch SHA-256 is
`a1fdbdf1f1b5379bd75f7670f2f2ef1bc3e0ae9e1f6b9c19aef54066fc8a5766`.
The complete result of applying that distributable matches the ROM reconstructed
from current source, including native hooks and color extension. No full ROM was
written or published. No source/payload change is justified by these passing cases.

## Remaining acceptance

For #953, reproduce without the HP-lock and invincibility cheats mentioned in the
report, as requested by the maintainer. Receive a new unique Vitality while damaged
and alive; inspect immediate HP and HUD capacity, then duplicate/reconnect behavior.
Record health configuration, ROM patch version and client version.

For #971, receive one Spray Paint and Music Sheet through a live multiworld,
inspect the collection room, leave/re-enter it, and perform normal save/load.
Record whether ownership RAM is set even when the icons are absent, whether the
menu was already open at delivery, and the exact client/patch versions. Test with
and without Sound Player. A failure with correct RAM would isolate menu refresh
or rendering rather than receipt dispatch.
