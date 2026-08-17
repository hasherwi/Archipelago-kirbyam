# Archipelago-fuzzer provenance

- Upstream: <https://github.com/ionium-ap/Archipelago-fuzzer>
- Imported commit: `ebe01d5523f04a2a0a1de5eb7229d10ef12b8fc2`
- Upstream version: `0.6.2`
- Upstream `fuzz.py` SHA-256: `4f65c12813b06e19046d9aa2397083cb14977592acee1cf8d40544307e405694`
- Vendored `fuzz.py` SHA-256: `fbb3c0f19e1dc5a85c6e7f561a4f2cdc2d18c773f48238b4df0923b3c68ea35b`
- Imported: 2026-08-17
- Local modifications: one compatibility field, `allow_quantity=False`, in the
  synthetic `Generate` namespace. This checkout requires that argument.

The source is vendored so local fuzzing works offline and CI never executes a
mutable upstream branch. The launcher verifies the checksum before every run.

To update it, review an exact upstream commit, replace `fuzz.py`, reapply (or
remove if no longer necessary) the documented compatibility field, update both
checksums and the commit above, update the vendored checksum and commit in
`tools/run_kirbyam_generation_fuzz.py`, then run the launcher tests and at least
one generation-fuzz smoke run.
