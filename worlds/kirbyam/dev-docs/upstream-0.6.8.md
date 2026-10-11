# Archipelago 0.6.8 integration (Issue #933)

## Reproducible revisions

- Released KirbyAM v0.4.0: `kirbyam-v0.4.0`, commit `cbf69ef05c6803dab6d973584c93dc9253d8200c`.
- Fork main at start: `6eba088d9f1f99ad205a8d90ee1ec17265442195` (includes PR #959).
- Upstream target: **stable 0.6.8**, commit `54803be064fc7e80c4628777ed0b46a9390f255f`.
- Common ancestor: `fb45a2f87e392a7ea69daa33905b8aee3e83e19d`.
- Upstream range: `fb45a2f8..54803be0`, 214 commits. Some were previously copied into this fork without shared ancestry.

The integration uses the released upstream tag instead of its moving main branch.
It is post-v0.4.0 work. At the owner's request, the changelog entry is under
v0.4.1 Internal Changes; the issue's v0.5.0 milestone is unchanged. Existing
v0.4.1 entries and all released changelog sections are retained.

## Compatibility and conflict decisions

- Framework: accept upstream's batched fill, option-counter validation, rule-builder
  updates, server data-package cache, manifest loading and launcher component API.
- Client: accept CommonClient's session-identity reset and malformed DeathLink guard;
  BizHawk now ignores empty patch-server metadata instead of overriding `--connect`.
  Retain the fork's opt-in mGBA connector staging and launch arguments.
- Lua: accept upstream's Lua 5.5-compatible connector/base64 changes.
- Dependencies: retain bounded core ranges and the validated Cython `<3.3` ceiling;
  raise platformdirs' lower bound to upstream's 4.10.1. Accept upstream web-host
  requirements, including mistune 3.3.0 and psutil 7.2.2. Keep pytest-asyncio for
  Kirby's asynchronous tests. ModuleUpdate now constrains world installs against
  core requirements, as upstream does.
- Preserve the fork's prerelease-aware version parser and explicit source-test
  requirement-update override. Neither changes the Kirby network protocol.
- Conflicting non-Kirby world implementations and tests use the stable upstream
  versions. Preserve Kirby's MIT license despite the upstream delete conflict.
- Preserve all Kirby item/location IDs, room logic, option migration, receipts,
  native hooks and packaged base patch. No ROM or save-format migration is added.
- The standalone APWorld minimum stays **0.6.7**: this sync does not add a new
  framework API dependency to the world. Source users use the integrated 0.6.8
  framework. Do not confuse the framework version with Kirby's world version.

## Compatibility repairs exposed by restored coverage

- Scope Kirby test DEBUG logging to its test protocol, restoring the root level
  after all fixture finalizers. Collection must not enable global DEBUG: pytest
  capture retains log arguments and caused false MultiWorld leak failures in
  other games. Keep the upstream memory checks unchanged.
- Give the dynamic starting-color option its real module identity so WebHost can pickle it.
- Add missing package initializers in Kirby tooling and test helpers.
- Keep container version fields out of source `archipelago.json`; the builder
  writes them into the archive without mutating source metadata.
- Make the single-player generation helper explicitly choose one player and no
  global weights/meta/race settings, so repository test order cannot change it.
- Make the generic collect/remove test honor the existing `collect_item` hook for
  useful items; retain its symmetry assertion and the unchanged non-tracked-item check.
  This preserves the six useful precollected abilities introduced by #957.
- Register the exact 32 empty/dormant default Kirby regions in the upstream test
  exception table. The test asserts they remain unreachable and still requires
  every active location and the completion condition to be reachable. No graph
  edges are invented; #945 and its strict room-sanity failures remain explicit.

## Test and CI scope (Issue #156)

The previous `unittests.yml` ran only `worlds/kirbyam/test`. Restore the upstream
`pytest` baseline on all six Python/OS combinations and keep the hosting job.
No `AP_TEST_WORLDS` filter is set for baseline jobs. Preserve the fork's main-only
push trigger and stale-PR cancellation. The separate **Focused KirbyAM tests**
job uses upstream's explicit `AP_TEST_WORLDS=kirbyam` filter; it is additive.
The ROM-patch, APWorld, scheduled fuzz and private Windows BizHawk workflows remain.
`pytest.ini` keeps repository-wide discovery and async support, and gains the
upstream `world` marker. The removed upstream PR-label automation stays removed.

Useful commands from the repository root:

```sh
python -m pytest -n auto --dist worksteal
AP_TEST_WORLDS=kirbyam python -m pytest worlds/kirbyam/test -n auto --dist worksteal
python test/hosting/__main__.py
python worlds/kirbyam/build.py --skip-patch --skip-install --non-interactive
```

Full Kirby tests include generated archives for all 55 health bounds, 89,760 pool
builds and strict expected failures for the pre-existing five room-sanity ingress
checks (#945). Those expected failures are not evidence that room-sanity is fixed.
The PR records terminal test/CI results and the distinction between protocol smoke
tests and fresh emulator acceptance. Private ROM validation must remain local;
only source, metadata and distributable patches may be published.

## Owner-requested Overcooked! 2 quarantine

The restored macOS baseline exposed a default-option Overcooked! 2 fill failure
at seed `51633506502411458318`: 25 items remain unplaceable. The same seed fails
in a clean upstream `54803be0` snapshot. At the owner's request, the slot-data
test now uses the verified fillable seed `0` for OC2 only; other games retain
their existing randomized coverage. OC2 serialization, other OC2 tests and all
memory assertions remain enabled.

`test/general/test_overcooked_slot_data_regression.py` separately runs the exact
bad seed with a strict expected failure. Only its specific 25-item `FillError`
is accepted; setup errors, other fill errors and serialization failures remain
failures. A repaired seed becomes strict XPASS, requiring removal of this
quarantine. This does not fix OC2 generation or claim arbitrary-seed coverage.
