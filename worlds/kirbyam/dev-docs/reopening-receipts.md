# Reopening and receipt recovery (#952)

The client keeps a local SQLite journal at
`Utils.user_path("kirbyam", "receipts.sqlite3")`. It records individual AP receipts,
not a delivery high-water counter. Scope is a digest of the server seed name,
validated ROM authentication bytes, team and slot; authentication bytes are not
stored. Receipt identity is item ID, source location, sender and occurrence of
that tuple in the complete history. This distinguishes duplicate starting items
and survives insertion of a different starting-inventory prefix.

After an observed mailbox ACK:
- Food, lives, battery, invincibility and traps are confirmed one-shot receipts.
  They are skipped on subsequent replay, including after a full client restart.
- Persistent items remain eligible for native-save restoration. An old save may
  lack their ownership, so a journal receipt never suppresses their delivery.
- Receive notices are claimed once in the journal, independently of restoration.
  A newly received copy at a different location still delivers and notifies.
  Disabling receive notices also records that decision for the acknowledged receipt.

Delivery semantics use an explicit transient item-ID set, independent of AP
filler/progression classification. Changing Sound Player to filler must not stop
its restoration. New transient item types must be added deliberately.

## Interrupted effects

Before offering a transient effect, the client commits a pending receipt. If the
client stops before recording the native ACK, that pending receipt has an unknown
outcome. A physical counter alone cannot prove what happened after a reset or
savestate restore. The client pauses new mailbox delivery instead of automatically
repeating or discarding the effect. Location polling/ownership reconciliation are
not disabled by this pause.

For a live pending request, a cleared mailbox confirms a receipt only when the
physical application counter is exactly one greater than its value at offer time.
An unchanged counter (including the first request at zero), a jump, or missing
counter evidence leaves the transient receipt unresolved. A wrap to zero also
pauses because it cannot be distinguished from a reset. If an effect was consumed
but a reset erased that evidence before the ACK poll, explicit resolution is still
required. Failed journal commits retain the offer-time baseline for safe retry.
Permanent ownership requests without ACK evidence remain eligible for restoration.

The console identifies the pending receipt (item ID, location, sender, occurrence).
Restart the ROM from its native save to empty the mailbox, then choose:

- `/receipt received`: the effect already happened; do not apply it again.
- `/receipt retry`: explicitly request delivery again. This can duplicate an effect
  if it actually happened before the interruption.

Only the currently blocked receipt in the current scope can be resolved. A queued
choice cannot override a nonempty mailbox. Multiple unresolved receipts are handled
one at a time. Do not run competing clients for the same game session.

Journal creation/read/write failures pause delivery; they never silently fall back
to replay. Restore access to the journal and reconnect. Do not delete the journal
as a routine recovery step: deleting it removes evidence of prior consumable effects.
Keep this file when moving a play session to another computer. Different computers
without the same journal do not share receipt protection.

## Migration and limits

The client waits for complete index-zero authenticated history before opening a
journal. It does not infer old acknowledgements from a server location check,
item classification, or arbitrary local/native counter. Existing sessions created
before this feature may have no durable evidence of already-consumed effects.
Protection begins when the updated client records receipts; a cold first upgrade
cannot retroactively guarantee suppression of unknown historical effects. Run the
updated client and allow pending deliveries to finish before closing it.

The ROM/mailbox/native-save formats are unchanged. No rebuilt ROM is required.
SQLite transactions protect local receipt writes, but native application and the
journal are not a shared atomic transaction. The explicit interrupted-effect pause
is intentional; this is not an exactly-once guarantee across arbitrary process loss.
Notification claiming precedes display, so a crash/display failure may lose a notice
rather than repeatedly show it. Lost/deleted journals and unsupported cross-seed
native-save imports cannot be repaired from this journal.

## Validation

Tests exercise actual client delivery/notification functions with simulated bridge
IO and physical +1 ACK counters. Coverage includes every current transient ID,
persistent restoration, new copies, duplicate identities, reinitialization, network
reconnect, RAM reset, seed/team/slot/ROM isolation, precollect-prefix identity,
concurrent reservation, missing full history, corrupt/storage-failing journals,
changed in-flight history, and explicit interrupted-effect resolution.
These are protocol regressions, not live-emulator/native-save gameplay acceptance.
