# KirbyAM generation fuzzing

KirbyAM uses the pinned
[Archipelago-fuzzer](https://github.com/ionium-ap/Archipelago-fuzzer) to search
for failures caused by random option combinations. This complements, but does
not replace, `worlds/kirbyam/test/fuzzer.py`: that helper checks malformed
client/protocol inputs, while this tool runs Archipelago world generation.

The third-party source is vendored under
`tools/third_party/archipelago_fuzzer/`. Its exact upstream commit, original
checksum, one documented compatibility field, vendored checksum, and MIT
license are recorded beside it. The launcher verifies the vendored checksum
before executing the source.

## Local run

Install the normal CI dependencies and initialize settings as described for
the unit-test suite, then run from the repository root:

```shell
python tools/run_kirbyam_generation_fuzz.py --runs 100
```

The launcher defaults to at most four workers, a 60-second per-generation
timeout, KirbyAM only, and `--skip-output`. The existing deterministic
generation integration test covers patch/archive output. Note that upstream's
`--skip-output` skips upstream's final accessibility assertion. KirbyAM's
all-check audit runs in `stage_pre_output` before that early return, so it still
rejects unreachable enabled Kirby checks in fuzzer runs, including minimal
accessibility. To include archive output and upstream's accessibility assertion
in a deeper local fuzz run, pass `--with-output`.

The launcher is intentionally not part of the default pytest or pre-commit
commands. It is stochastic and substantially more expensive than a focused
unit test.

## Results and failure policy

Archipelago-fuzzer writes `fuzz_output/report.json` and stores the YAML and log
for failures, timeouts, and ignored option errors below `fuzz_output/`. The
launcher also writes `fuzz_output/metadata.json` with the Archipelago commit,
pinned fuzzer revision, Python/platform details, arguments, and subprocess exit
code.

By default, the launcher fails when any generation fails or times out. It also
fails when an `OptionError` is reported as ignored. `--allow-ignored` exists for
deliberate investigation only and is not enabled in CI.

CI explicitly passes `--classify-minimal-rejections`. This adds a distinct
**unsafe rejected** outcome; it never changes the pinned fuzzer's raw report,
counts a rejection as successful generation, or relaxes the production guard.
Each classified rejection must have all of the following evidence:

- A unique case ID with its saved YAML and log, matched to the report.
- Exactly one terminal `KirbyAmCheckAccessibilityError` traceback through the
  final `stage_pre_output` guard, without chained or grouped exceptions.
- Logged, actually rolled options for one Kirby player selecting minimal.
- No unfilled checks and no checks unreachable with all inventory.
- A nonempty exact list of checks stranded by the actual placed progression.

Missing/malformed evidence, other exception types, full accessibility,
multiworld cases, theoretical source/route closures, timeouts, and ignored
option errors remain failures. The classifier is intentionally narrow, so a
future logging or guard-message format change requires review. It writes
`classified_outcomes.json` alongside the unchanged raw artifacts, with case
IDs, seeds, actual options, stranded checks, artifact hashes, and reasons for
unclassified failures.

At least **50% of all attempts must still succeed** when this policy accepts
rejections. This is a generation-success regression tripwire, not a universal
seed guarantee. An all-rejected batch stays red. Before random fuzzing, CI also
runs the deterministic 36-case output/rejection matrix: three randomization
modes, two gating settings, full/minimal, and three source/option profiles.
All full cases and at least one known safe minimal archive for each mode/gating
pair must actually generate and pass independent fresh-state all-check audits.
Rejected cases must stop before archive output. This preserves both playable
output coverage and deliberate safety-rejection coverage.

Archipelago-fuzzer 0.6.2 does not expose a master RNG seed. A failing YAML and
log are therefore the primary reproducer. Copy only the `.yaml` files from one
finding into an otherwise empty directory, then run:

```shell
python tools/run_kirbyam_generation_fuzz.py --sample-from path/to/replay-yamls --runs 20
```

Do not point `--sample-from` directly at a finding directory that also contains
the `.log` file; the upstream tool treats every file in that directory as a
sample. When a bug is confirmed, reduce it to a deterministic regression test
rather than relying on an automated fuzz run to rediscover it.

## CI

`.github/workflows/kirbyam-generation-fuzz.yml` runs separately from the unit
test matrix. It runs for every pull request and is also manually dispatchable
on one Ubuntu / Python 3.13 runner. The workflow always uploads `fuzz_output/`,
including when the launcher fails. Repository branch-protection settings decide
whether this workflow is a required pull-request check.

## Health-pair constraints

The default launcher passes `tools/kirbyam_generation_fuzz_meta.yaml` to the
unchanged pinned fuzzer. Its triggers preserve the randomly chosen minimum HP
and draw maximum HP from the supported `[minimum, min(minimum + 4, 10)]`
interval. Thus it exercises all supported pairs without treating intentionally
invalid combinations as generation bugs. Deterministic tests separately cover
every supported pair and invalid-pair rejection. `--sample-from` bypasses this
metadata so saved reproductions, including invalid user YAML, are not rewritten.


## Reviewed safety rejections on PR #1051

[Run 42519129270](https://github.com/hasherwi/Archipelago-kirbyam/actions/runs/42519129270)
tested merge `ca7aee9097cf574878af1e589fb3bd604313f507` for published head
`5a01bb955db1cf8d781491979922605364eedf1e`. It reported 395 successful
generations, 105 failures, no timeouts, and no ignored cases. Review of every
saved YAML/log pair found that all 105 were minimal placed-progression
rejections with no unfilled or all-inventory-unreachable checks. These were
unsafe seeds correctly rejected, not 105 playable outputs or source failures.
`generation-fuzz-42519129270-audit.json` retains per-case seeds, counts, hashes,
and original artifact provenance. The exact original case 1 YAML and seed
271418054 are pinned in regression tests; an independent sweep reproduces its
44 stranded checks while the selected goal remains beatable.

The default strict launcher still returns failure on those raw artifacts.
Only the explicit, evidence-checked CI classification accepts the batch as a
successful safeguard test. Starting Stone/Burning, source filtering, final
all-check validation, and native traversal rules remain unchanged.
