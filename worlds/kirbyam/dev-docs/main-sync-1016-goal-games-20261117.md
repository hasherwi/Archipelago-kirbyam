# Goal Game integration into full completion

Main `63e87438b` merges Goal Games and the Docker manifest fix. The combined
source retains APGOAL3 at ROM offset `0x1000010` and moves the unreleased
APFULL01 marker to `0x1000018`. Both markers are linker-asserted and the
packaged patch is checked for their distinct bytes. Regenerate full-completion
patches after updating the client: older full-completion patches fail the
marker guard rather than being accepted as compatible.

Goal Game flags remain in the Copy Room record, independent of physical
lever/chest/room completion. Goal Games are not added to the full-completion
contract. Historical evidence retains its original source and patch hashes;
the live `bbeb161ce` checkpoint is not acceptance of this combined patch.

Historical source/surface projections preserve the same original hashes,
reversing the exact sixteen Goal Game surfaces before the previously pinned
feature delta. No physical evidence or source-qualified traversal is rebased.

Validation: combined lawful-ROM ARM rebuild and APWorld packaging passed.
880 focused feature, generation and historical-evidence tests passed, followed
by 64 projection, native save, Goal Game runtime and patch tests. Final aggregate
and exact-head hosted CI remain pending. Positive full-completion gameplay
acceptance is still incomplete.

The follow-up integration includes main `b4bb477f2` (Universal Tracker).
Both physical-save and tracker slot fields are retained. Full-completion goal
reconstruction is exercised with and without RoomSanity/Area Keys. Native
source and patch bytes are unchanged by this follow-up. The prior aggregate
was intentionally stopped after 1,832 passes when main advanced; it is not a
complete aggregate result.

Follow-up validation: 42 UT/slot/snapshot/projection tests passed with four
upstream/live skips; 680 full-completion and source-monotonicity tests passed.
The expanded UT cases passed (18 tests, three upstream dependency skips).
APWorld packaging passed. Native patch SHA-256 remains
`068f5b56df0d48bd8fabd4cba918c1a1bf0492cb2f3f126c325a1e8148aeec82`.
