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
`--skip-output` also skips the final accessibility assertion. To include output
and that assertion in a deeper local fuzz run, pass `--with-output`.

The launcher is intentionally not part of the default pytest or pre-commit
commands. It is stochastic and substantially more expensive than a focused
unit test.

## Results and failure policy

Archipelago-fuzzer writes `fuzz_output/report.json` and stores the YAML and log
for failures, timeouts, and ignored option errors below `fuzz_output/`. The
launcher also writes `fuzz_output/metadata.json` with the Archipelago commit,
pinned fuzzer revision, Python/platform details, arguments, and subprocess exit
code.

The launcher fails when any generation fails or times out. It is stricter than
the upstream script and also fails when an `OptionError` is reported as
ignored. `--allow-ignored` exists for deliberate investigation only; it must
not be used by CI without reviewing and documenting the ignored cases.

Archipelago-fuzzer 0.6.2 does not expose a master RNG seed. A failing YAML and
log are therefore the primary reproducer. Copy only the `.yaml` files from one
finding into an otherwise empty directory, then run:

```shell
python tools/run_kirbyam_generation_fuzz.py --sample-from path/to/replay-yamls --runs 20
```

Do not point `--sample-from` directly at a finding directory that also contains
the `.log` file; the upstream tool treats every file in that directory as a
sample. When a bug is confirmed, reduce it to a deterministic regression test
rather than relying on the scheduled fuzzer to rediscover it.

## CI

`.github/workflows/kirbyam-generation-fuzz.yml` runs separately from the unit
test matrix. It is manually dispatchable and scheduled weekly on one Ubuntu /
Python 3.13 runner. The workflow always uploads `fuzz_output/`, including when
the launcher fails. It is intentionally not a required pull-request check
while upstream lacks master-seed support and the scheduled job is establishing
its stability.
