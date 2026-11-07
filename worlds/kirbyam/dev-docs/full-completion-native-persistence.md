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
