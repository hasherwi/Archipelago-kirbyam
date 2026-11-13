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

### Additional file and network coverage

The same genuine route was then replayed continuously from blank SRAM in native
files 1 and 2. Only legitimate menu file-selection inputs changed; the total
41,104 input frames and all 115 room/position/health/ability checkpoints matched
the original route. Both physical pulls and separate-process cold boots passed.
Independent review verified full authentication, selected-file isolation, all
six checksums, unchanged other files and actual zero process exits. Thus the
Moonlight Mansion physical-first save/cold-load case now covers all three files.

A separate file-0 test used the shipping AP server on localhost and the shipping
Kirby client with an mGBA-backed BizHawk transport adapter. The initially empty
server acknowledged the actual lever location 3960415. An actual disconnect and
second connection preserved the same four checks and six-item received history,
with no duplicate location reports. The full authenticated physical record
survived. The 217 shipping-client memory writes reported no guard failures; these are
legitimate client delivery/configuration writes, not a zero-write experiment.
Both server and client/native processes exited zero, and independent review
verified the packet history and native evidence. No administrative item grants
or manually fabricated location checks were used.

This adds real AP synchronization/reconnect coverage for the Moonlight file-0
case, not actual BizHawk-emulator, receipt-first, other-lever or full-goal
acceptance. Earlier checkpoint exclusions describe their original scope; this
section records the later extensions without rewriting that provenance.

### Receipt-first Carrot Castle and Radish Ruins coverage

A separate ordinary generated seed (101614) used the supported `start_inventory`
option for all 15 Hub Connections and four Lever Walls, alongside the normal
Beam/Ice starting items. These are additional precollected copies, not an item-pool
removal option. The actual localhost AP server delivered the inventory through
the shipping client. All 21 precollected items matched the generated list, all
four native wall bits were set, and the live hub ownership mask was `0xfffe`.
No physical lever latch, physical lever record bit, outgoing lever check or
server-acknowledged lever check was created by those receipts.

Controller-only gameplay then reached and pulled the Carrot Castle lever in
room 170. Only the actual Up interaction set activation bit 2 and authenticated
record bit 17. Both native file-0 save copies contained the record, all six
checksums were valid, and a separate cold boot restored the exact record and
latch. The cold-load battery was byte-identical to its input.

Continuing through the genuine Carrot exit and wind shaft reached Radish Ruins
room 619. Its actual Up interaction added activation bit 3 and authenticated
record bit 18, preserving the earlier Carrot bit. Both file-0 save copies and
all six checksums passed independent review. A separate cold process restored
the combined Carrot/Radish record and activation latches. These cases show that receiving a
wall first neither grants physical credit nor prevents a later genuine pull.

The runs use their own same-ROM checkpoints, with every owning process exit
recorded and no route memory writes. The delivery phase uses legitimate
shipping-client writes; it is not described as a zero-write experiment. The
first delivery trial preserved a failed harness assertion: the live hub mask
uses indices 1–15 (`0xfffe`), unlike the zero-based physical switch record. The
corrected assertion passed on a fresh second trial. No production defect was
inferred from that harness error.

Full-goal/credits acceptance and the remaining native interruption matrix are
still outstanding. These narrow additional cases do not remove the known
limitation or establish universal multiplayer/BizHawk-emulator acceptance.

### Olive Ocean receipt-first coverage

For the remaining source, seed 101614 was restarted from a new blank native
battery. A continuous replay of the previously verified controller inputs
matched all 115 room/position/health/ability checkpoints on this new ROM,
including the genuine Moonlight lever pull. Only inputs were reused, not a
foreign savestate or battery. The new seed's full authentication matched.

The real AP server then delivered the generated starting inventory. It
acknowledged the genuine Moonlight check, while the other three lever checks
remained absent. Ordinary gameplay passed through the newly owned Moonlight
wall and wind shaft into Olive Ocean room 824. Only its actual Up interaction
changed activation flags from 1 to 3 and the authenticated physical record from
`0x48408000` to `0x48418000`. Both file-0 save copies contained the new record,
all six native checksums remained valid, and other files were unchanged. A
separate cold boot restored the exact authentication, record and latches; its
output battery was byte-identical to its input.

These captures establish genuine pull evidence for all four distinct lever
sources, with physical-first Moonlight and receipt-first Carrot, Radish and
Olive cases. They do not establish every source/order/file combination or
full-goal/credits acceptance. The known limitation remains until the outstanding
acceptance matrix is verified. See [Olive evidence](full-completion-olive-20261113.json).

### Starting-item health and physical-completion separation

A supported full-completion fixture (seed 101615, health 6–10, enemy health 50%, no traps) delivered 33 official starting items through the shipping local AP server and client, plus two rewards from actual tutorial checks. Native health capacity increased from 6 to 10, current HP from 5 to 10, and received Vitality count from 0 to 4. All four physical Vitality chest flags remained clear; their transport register remained zero. All eight mirror shards, hub connections and lever-wall ownership arrived without physical lever credit, Vitality/lever check packets, or a goal notification.

The input-template attempts did not pass: all three exited with assertions. The third included a native death; 300 neutral frames then produced an ordinary respawn, and subsequent input-only checkpoints reached the hub. These failures are retained as observed timing/route divergence, not treated as product defects or an identical-replay success. No foreign states or fabricated physical flags were used. The successful route and delivery processes exited zero, as did the server.

Delivery used the mGBA bridge adapter with the shipping client, not the BizHawk emulator. It performed 473 shipping-client memory writes; this is neither a zero-write nor an all-writes-guarded claim. Native ownership-derived counts (5 chests, 15 switches, 8 shards) did not establish physical completion: visited-room count was zero, physical lever credit was zero, final-clear was false, and the full-completion goal remained incomplete. Credits, positive full-goal acceptance and offline persistence after a verified native save are not established by this fixture.

A separate offline boot of the immediate post-delivery battery export returned capacity 6 and received count 0. The original capacity-10 test expectation failed and is retained. Exporting SRAM immediately after item delivery did not prove that the native game had saved those received upgrades; the volatile receipt mask also correctly reset to zero.

A subsequent ordinary cold boot connected to a byte-identical copy of the existing AP server save. Its 35 ordered item-history entries and two checked locations matched exactly before and after reconciliation; the original server save remained unchanged. The shipping client restored capacity 10 and received count 4 while physical Vitality chests and lever credit stayed zero, with no goal notification. Both processes exited zero. This verifies authoritative connected recovery, not offline persistence.

See [health receipt evidence](full-completion-health-receipts-20261113.json) for sanitized checkpoints, hashes, exit results and network observations.

### Later HP-assisted ending and completed-save validation

At the owner's explicit request, final-boss testing used a current-HP freeze. The actual ending branch contains 34 logged writes, all to the human player's current-HP byte (`0x02020fe0 = 10`). Boss HP, capacity, abilities, item receipts, physical checks and completion flags were not directly changed. Own same-ROM checkpoint branches and failed attempts were preserved. This is assisted testing, not an uninterrupted or unassisted playthrough.

Controller inputs defeated the final eye and shooting stage. The freeze was then disabled: the native ending reached the visually verified **The End** screen, transitioned to AI state 9999, and returned to the title. A new process cold-loaded that earned battery into hub 801 with final-clear state 9999 and no boss refight or memory writes.

The shipping client then reconnected to a byte-identical copy of the original real server save. All 35 ordered items and two physical acknowledgements remained identical; the original save was unchanged. Native final-clear was true, but only 5 chest bits and 10 visited rooms were present. The 15 native switches and 8 shards include ownership-derived state and are not claims of physical AP checks. No `CLIENT_GOAL` was reported, as required. The client performed 470 real reconciliation writes. Native and server processes exited zero; the retained log also contains a websocket keepalive/closure warning.

A separate actual guarded-read test accepted an unchanged native snapshot, then rejected that same snapshot after loading an earlier own same-ROM state. It made no manual memory writes or server/goal requests. This verifies the shipping guarded-read mechanism through the mGBA adapter, **not** the whole pending full-completion-report race with all positive preconditions satisfied.

Independent file review verified state/runtime hashes, parent links, exit results, write inventories, ending/title images, cold loading and the reconnect evidence. Historical executed script hashes were not pre-pinned, so this is not a tamper-proof execution attestation. See [assisted ending and cold-load evidence](full-completion-assisted-ending-20261113.json).

### Configured health-range receipt cases

Fresh ordinary full-completion seeds now cover these native capacity transitions with the real local AP server and shipping client:

| Configured minimum/maximum | Capacity before/after | Received Vitality count | Physical Vitality bits | Goal |
| --- | --- | --- | --- | --- |
| 6/6 | 6 → 6 | 0 | all zero | not reported |
| 3/5 | 3 → 5 | 2 | all zero | not reported |
| 1/10 | 1 → 10 | 9 | all zero | not reported |

Routing through the ordinary tutorial was HP-assisted. Current HP alone was frozen at 10, then explicitly restored to the configured minimum before recording the controlled baseline and disabling assistance. Capacity, items and physical/completion flags were never manually changed. The later capacity/receipt changes came from real AP delivery. These cases do not claim unassisted survival at minimum health or physical opening of every Vitality chest.

Earlier harness failures remain documented: a nullable tutorial-progress assertion, a local-server startup timeout, and receipt polling before leaving the tutorial. The last is the expected non-gameplay delivery gate, not a reason to relax receipt checks. All final native/client and server processes exited zero. The separately documented 6/10 authoritative recovery case remains applicable. See [configured health-range evidence](full-completion-health-ranges-20261113.json).

The outstanding limitation is now narrower, but remains: positive full-goal acceptance with all 99 physical acknowledgements, all 84 native chest bits and 272 visited rooms has not been demonstrated. Remaining physical order/file combinations, the full end-to-end pending-goal reset/rewind case, and universal BizHawk/multiplayer behavior are not established by these bounded tests. No merge or release is implied.


### Real-server reconnect in native files 1 and 2

The genuine Moonlight Mansion physical-first case now has real AP synchronization
and reconnect coverage in all three native files. The additional file-1 and
file-2 runs cold-loaded the previously reviewed, input-only physical-pull
batteries from ordinary seed 101613. Their source inputs and native bridge were
pinned before execution, and the shipping client/server source was verified
against commit `a7f2ca105afe4a517f000d920abca1a16b01880d`, tree
`0b3f648470ac8a55c4b2b02ef59baf531468e9eb`.

Each run used a fresh, initially empty local AP server. It acknowledged the
actual Moonlight lever location `3960415`; after an actual second connection,
the same four checked locations and six-item history remained, with no duplicate
location reports or goal notification. Both native files retained the complete
authenticated physical record and mask `0x48408000`. Each run performed 211
shipping-client guarded writes, with zero guard failures and no manual gameplay
or completion writes. Both native/client and server owning waits exited zero.
The output batteries were byte-identical to their respective inputs.

This is mGBA-backed shipping-client transport coverage, not native BizHawk
validation. It does not establish positive full-goal acceptance with all 99
physical acknowledgements, 84 native chest bits and 272 rooms, an end-to-end
pending-positive-goal race, or the remaining receipt/pull ordering and other-lever
file combinations. See [the bounded network-file evidence](full-completion-network-files-20261113.json).


### Receipt-first Carrot Castle in native file 1

A fresh native file-1 run on ordinary seed 101614 replayed the accepted tutorial
from blank SRAM, then received 21 official starting items from the real local AP
server through the shipping client. The total received history contained 23 items:
21 precollected entries plus two earned tutorial checks. Physical lever activation
was still zero before gameplay pulled the Carrot Castle lever.

The accepted Carrot controller route matched its initial and final checkpoints at
every segment. The genuine pull was saved by the original native code; a separate
process cold-loaded the earned file-1 battery and retained activation `4` and the
authenticated record mask `0x48420020`. Tutorial, pull and cold-load stages made no
manual memory writes. Receipt delivery made 207 shipping guarded writes with zero
guard failures. All four stages, the wrapper and the server exited zero, with no
remaining live owned processes. The immutable source/input pins stayed unchanged.

This packet did not reconnect after the physical pull or establish a new server
acknowledgement for it. File 2, other ordering/file combinations, positive full-goal
acceptance and the pending-positive-goal race remain outside this result. See
[the bounded Carrot file-1 evidence](full-completion-carrot-file1-20261113.json),
including the retained non-fatal sqlite connection warning.


### Receipt-first Carrot Castle in native file 2

The same bounded receipt-first sequence also passed in a fresh native file 2:
blank-SRAM tutorial, real delivery of 21 precollected items (23 total history
entries including two earned tutorial checks), actual Carrot lever pull, native
save and separate-process cold reload. The cold file retained activation `4` and
record mask `0x48420020`; its battery was byte-identical to the pull-stage output.

All four stages, wrapper and server exited zero, with no remaining live owned
processes. The 2,596 pinned inputs were unchanged. Receipt delivery made 207
shipping guarded writes with zero guard failures; the other stages made no manual
writes. Thus the existing file-0 case and these file-1/2 extensions cover Carrot's
receipt-first physical save/cold-load case in all three native files, not the
other lever permutations. No post-pull server reconnect or positive full-goal
acceptance is claimed. See [file-2 evidence](full-completion-carrot-file2-20261113.json).
