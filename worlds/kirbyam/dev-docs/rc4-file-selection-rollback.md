# RC4 file-selection rollback

RC4 defers the File 1/menu bypass and coupled save foundation merged in
[#1024](https://github.com/hasherwi/Archipelago-kirbyam/pull/1024).
[#1037](https://github.com/hasherwi/Archipelago-kirbyam/issues/1037) tracks the
reported extra/title-screen-like Kirbys and corrupted sprites after RC3 startup.
The report establishes the symptom, not a reproduced root cause.

The rollback restores the pre-feature native three-file selector, mode-menu Back
route, startup validation, WORLD descriptor layout and client behavior. Reverting
only the menu branch is unsafe: the merged foundation also requires slot 0 and
changes WORLD checksums and backup offsets. The deferred feature's source and
validation history remain in #1024. Copy Room (#1025) and Goal Games (#1026) must
be reconciled and rebuilt before future integration; neither is part of RC4.

The independent Rainbow Route 1-06 lower-cave chest correction (#1033/#1032),
its starting-Area-Key lifecycle fix and subsequent release-workflow changes are
preserved. No merge, release tag or publication is performed by this rollback.

## Save compatibility

Back up an RC3 save before switching builds. RC3's APSHR02 layout has 4,884-byte
WORLD copies at SRAM offsets 24 and 4,908, including the 4 KiB extension. The
restored native layout has 788-byte copies, different checksum coverage and a
different backup offset. An RC3 save is not directly compatible with this
rollback, and opening the only copy may cause native invalid-save recovery to
clear or replace it. Repatching a ROM does not convert its save.

Use a fresh save or a preserved pre-#1024 native-layout save for the same seed.
No RC3 save migration is implemented or claimed. Preserve the original RC3 ROM
and save separately if progress must be recovered later.

## Verification boundary

The patch-tool regression checks that the native title-to-selector call,
mode-menu Back pointer, three-file validation bounds and all nine WORLD
descriptor references remain unchanged. The release review must also verify the
rebuilt patch and retained chest/Area-Key tests. Record actual emulator coverage
and any remaining limitations in the rollback PR; prior #1024 acceptance is not
evidence that the reported RC3 failure has been reproduced.
