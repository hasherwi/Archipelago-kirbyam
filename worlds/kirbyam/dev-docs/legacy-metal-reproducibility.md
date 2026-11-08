# Reproducing the legacy metal audit

This is a historical research audit of nine directed legacy exits at `bee5a93`, integrated as derived documentation at `5a01bb9`. New route implementations may legitimately change those AP edges. The native data interpretation is pinned to `jiangzhengwenjz/katam` revision `7d969fbce14fdc838d2c1ea01389717fb96c3189` and the unmodified 16 MiB USA ROM SHA-1 `274b102b6d940f46861a92b4e65f89a51815c12c`.

## Bundled derived files

- `legacy-metal-exit-audit.json`: exact historical AP edge keys, source candidates, six F5 banks, door facts, limits and corrected source identifications.
- `legacy-metal-public-map-references.json`: all ten inspected composite maps, article URLs pinned to revision IDs, original CDN URLs, byte count and SHA-256 of the inspected image bytes. Map art is not bundled. A hash detects CDN drift; it does not guarantee the CDN retains old bytes.
- `legacy-metal-public-source-references.json`: exact native repository/revision/file/symbol/line URLs and hashes of inspected source files. These explain object grants, room loading, mutation application, Bomb propagation and Throw restrictions. They do not establish room-specific controller success.
- `../tools/validate_legacy_metal_audit.py`: standard-library Python 3.10+ validator. It does not depend on the three nonbundled native extracts or on a network connection.

## Portable consistency check

From a checkout containing these files in `worlds/kirbyam/dev-docs`:

```sh
python worlds/kirbyam/tools/validate_legacy_metal_audit.py \
  --world worlds/kirbyam
```

For artifacts kept outside the checkout:

```sh
python /path/to/artifacts/validate_legacy_metal_audit.py \
  --world /path/to/checkout/worlds/kirbyam \
  --audit /path/to/artifacts/legacy-metal-exit-audit.json \
  --map-references /path/to/artifacts/legacy-metal-public-map-references.json
```

This checks the nine historical edge records, native edge counts, six F5 banks against the published tile inventory, named source registry grants, and ten map references. It deliberately prints that native re-extraction was NOT RUN. It does not independently verify object offsets, door endpoints, collision replacements, movement or controller acceptance.

Add `--check-current-bindings` only when checking the historical AP baseline. This optional check should fail after a legitimate implementation replaces an old rule or redirects an arrival. Without it, historical research remains validatable against a newer checkout's unchanged data tables.

## Optional independent scalar re-extraction

An owner of the unchanged USA ROM may run the new bounded reader locally:

```sh
python worlds/kirbyam/tools/validate_legacy_metal_audit.py \
  --world worlds/kirbyam \
  --rom /private/path/to/owned-original-usa.gba
```

The reader checks the ROM size and SHA-1, then imports the published `tools/scan_metal_tiles.py` primitives. It decodes only rooms needed by the assertions, checks source template coordinates/native grant values, incoming/exit records, F5 coordinates, the separate 742 Bomb components and the selected 742 mutation values. It prints a small result summary and writes no ROM bytes, graphics, complete collision grid or extraction file. It does not download a ROM and does not require an emulator or the decomp checkout.

The optional native path was subsequently run successfully on the pinned original USA ROM with validator and scanner files from `a062278eea84ce3c2a6a7bbc601262cda0f3fab2`. The exact Git blob hashes and output are recorded in `legacy-metal-native-reextraction-result.json`: 19 native rooms, 14 incoming-record assertions, and disjoint 742 Bomb components passed. This is independent scalar re-extraction, not source capture, attack clearance, room reset, collection or passage safety. The default no-ROM mode still prints NOT RUN correctly for that invocation.

The original independent extraction programs and exact commands that produced the supplemental blobs were not supplied. This new validator is a separate bounded reader, not a claim to recreate those files byte for byte.

## Supplemental independent extracts, not bundled dependencies

These content-addressed GitHub REST endpoints identify the exact blob objects read during the audit:

- `legacy-exit-native-evidence.json`: https://api.github.com/repos/hasherwi/Archipelago-kirbyam/git/blobs/406a1af7589ae4633420348acc10552341e9a54f
- `moonlight-native-evidence.json`: https://api.github.com/repos/hasherwi/Archipelago-kirbyam/git/blobs/c737e3d49b340984bf39376ab323e8f40f064bae
- `742-708-bounded-mutations.json`: https://api.github.com/repos/hasherwi/Archipelago-kirbyam/git/blobs/560323b5f1cfbf36770937535300d79bf459bc04

All three were retrieved successfully through the authorized GitHub connector on 2026-11-08. They are blob-only objects rather than branch/ref artifacts, may require repository access, and are not guaranteed to be retained indefinitely. The audit JSON records the extracted content SHA-256 values. No claim is made that the blobs are public, permanently hosted, or required for the portable check. They contain scalar native excerpts intentionally omitted from the derived publication; do not copy full collision grids into the public deliverable merely to satisfy a reproducibility label.

An older scratch `validate_report.py` used those files and is not bundled. Use `validate_legacy_metal_audit.py` instead. Its narrower scope is explicit.

## Separate design-semantic check

With the repository's normal test dependencies installed:

```sh
AP_TEST_WORLDS=kirbyam python /path/to/artifacts/check_742_design_semantics.py \
  --repo /path/to/checkout
```

At `32d1c44`: PASS, 35 assertions. This exercises a hypothetical phase-expanded 742 graph against the real kernel. It is neither a reviewed production graph nor native physical evidence. See `moonlight-742-implementation-design.md` for the planned acceptance and integration tests.

The executable helpers now live in `worlds/kirbyam/tools`, following repository package policy. The pinned successful native run above used their historical `dev-docs` location at `a062278`; its recorded blob hashes remain the exact evidence. Moving the validator changes only its default map-reference lookup to the supplied world directory.
