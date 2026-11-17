# Docker manifest inputs

Each architecture build publishes its ordinary architecture tags and a
`run-<GitHub run ID>-<architecture>` tag. The manifest job reads only the two
run-specific tags. Public output tags, platforms and image contents are unchanged.
Run IDs stay stable for partial retries, allowing a failed manifest job to reuse
successful builds. Retain these tags while a workflow may still be retried.

This prevents a confirmed overlap between main publication runs. On November 17,
2026, run `44053149744` completed its manifest job, but the resulting `nightly`
index `sha256:4ce179e27ab9924aa7ab79f505ff06dc9fe66f2b443882a9a64aa32f458d2115`
referenced amd64 revision `73760a672d8d10fe457eaa1ec98d6b2df5988ee2` and arm64
revision `cb356f8bc1f9ec14e1ef865d27d74a2c44466935`. Another run had advanced
the shared arm64 tag before manifest creation. Both child manifests and their
layers were readable; this was a mixed-revision index, not a missing-layer claim.

The earlier `unknown blob` failure in run `44019644570` is distinct. Both of
that run's architecture manifests and all layers were readable during inspection.
Its original failure cause remains unproven. This change fixes the demonstrated
mutable-input race and does not claim to repair every registry availability error.

The regression test executes the workflow's tag and manifest shell scripts with
a fake Docker command. Interleaved runs deliberately overwrite one convenience
tag; manifest inputs must still resolve to two images from the intended run.
It exercises both nightly and multiple release output tags without publishing.
The shell regression runs on Linux, matching the publication runners; other
test platforms skip it because their default shells need not support `readarray`.

This is repository CI maintenance; the existing Kirby v0.5.2 player changelog
is preserved. No native ROM source, patch, gameplay or progression rules change.
