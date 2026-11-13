# Physical lever persistence for full completion

The full-completion payload carries `APFULL01` (eight bytes, no terminator) at ROM
file offset `0x1000010`. Clients must validate this marker before relying on the
new native physical-check record or restoring lever acknowledgements into it.
The existing color and Hub markers remain at their original offsets.

The five native world-state words at `0x02028C7C` keep the existing allocation:
words 27–30 contain the complete 16-byte ROM authentication token and word 31
contains a tagged physical-check mask. The new tag is `0x48400000`, with bits
0–14 holding the existing physical Hub switches and bits 15–18 holding the four
physical lever pulls. All bits above bit 18 must match the tag. An old
`0x48530000 | hub_mask` record remains readable, supplies no lever evidence, and
migrates on the first newly recorded physical check. Foreign-auth and unknown
records supply no physical checks. This changes neither the native save section
size nor its checksum or backup scheme.

The physical lever hook records a pull before returning to the original chest
callback. The native callback performs its existing save-disable, link-owner and
save-slot checks and then serializes the native world state. The new hook does
not invoke another saver and does not set the item-owned native lever chest bit.
Frame polling assigns both transport masks from the current native save record,
so switching files cannot retain the previous file's volatile lever mask.
Authenticated server acknowledgement recovery must update this same record
with guarded writes; writing only the volatile lever mailbox is insufficient
for marker-bearing ROMs. Legacy ROM clients retain their existing mailbox path.

## Evidence and limits

`test_hub_save_logic.py` executes the shared shipping header across all 32,768
Hub masks and 16 lever subsets, checking legacy migration, both update orders,
duplicates, invalid indices and unrelated native world words. The shipping
payload host harness exercises all four actual source/treasure-ID pairs across
three simulated save slots, save/reload, changed authentication and an empty-file
switch. It checks that pulls do not set native wall-ownership flags or call an
extra saver. The extracted lever lifecycle harness retains its popup/counter and
ability-gate regression coverage.

The host save spy copies RAM buffers; it does not execute the original ARM native
serializer, establish save-call timing on BizHawk, or prove a cold-boot cartridge
save roundtrip. Real-game acceptance still requires disconnected physical pulls,
a native save, cold reload and later AP reconnect, with all four lever locations,
all native save slots, receipt-before-pull and pull-before-receipt cases. Power
loss before the native save completes is not guaranteed. Loading a newer save
in an older payload is unsupported: the older payload does not understand the
new tagged record. Regenerate patches with the updated client for this goal.

## Native cold-load checkpoint (2026-11-13)

The current patched ROM was exercised in mGBA 0.10.5, starting from new blank
battery files rather than imported saves or savestates. All three native files
were created and cold-reloaded. In three additional runs, the shipping client's
`_reconcile_lever_activations` method restored all four acknowledged lever bits
through its real guarded transport against the running emulator. The server
acknowledgements were a **simulated context**, not a real server or physical pull.
No native chest, room, ownership or final-clear flags were injected.

Ordinary tutorial frames then let the original ARM code serialize the record.
New-process cold loads retained the full authentication token and `0x48478000`
record in the correct file, with all six native world-record checksums valid.
All twelve subprocesses completed with exit code zero. This establishes actual
native save/cold-load persistence of **client-restored** lever records in those
three files; it replaces no offline physical-pull or goal-completion acceptance.
The input/output hashes and explicit exclusions are recorded in
[the bounded checkpoint](full-completion-native-cold-20261113.json).

Still required: genuine disconnected pulls at the four physical lever sources,
both receipt/pull orders, and the full-completion/credits, health and interruption
matrix in [the completion contract](full-completion.md). The feature's native
policy remains candidate; neither this checkpoint nor the passing host suites
justify removing the full-completion known limitation.

## Genuine offline lever checkpoint (2026-11-13)

An ordinary generated `full_completion` seed (101613) was started from blank
SRAM on the unchanged shipping patch. Input-only gameplay reached room 743,
including genuine acquisition of Burning from a Flamer and traversal of the
room 708 metal barrier and room 743 maze. The run used its own hashed native
checkpoints for branches; it was not an uninterrupted full-game playthrough.
No received-item, chest, room or completion flags were injected.

The physical Moonlight Mansion lever interaction changed activation flags from
zero to one and the seed-bound physical record from zero to `0x48408000`
(physical lever bit 15). Native wall ownership remained zero, as required: a
physical pull is not receipt of the AP Lever Wall item. Ordinary native frames
saved this record. A separate cold-start process loaded that battery into file
0 and restored the complete authentication and physical lever latch in hub 801.

Independent review verified the 115-run input-only ancestry, actual zero exits,
ROM/state/runtime hashes, all six native world checksums and unchanged files
1/2. The cold-load battery was byte-identical to its input. The narrow evidence
is recorded in [the physical-pull checkpoint](full-completion-physical-lever-20261113.json).
Full ROMs, battery saves and savestates remain private and are not published.

This establishes **one genuine physical-first offline lever save/cold-load
roundtrip, in native file 0, on mGBA**. The other three lever sources, files 1/2,
receipt-first ordering, real server reconnect and the full goal/credits and
interruption matrix remain unverified. The candidate status and known limitation
remain in place.
