# Read-only native BizHawk Phone probe

Status: **prepared, not run on native BizHawk**. This harness does not close the
outstanding native Lua transport acceptance item. Its unit tests use a stub and
are only harness contract checks. The existing mGBA evidence remains separate.

## Isolated operator setup

Use an already installed supported BizHawk (2.7 or later; follow
[setup](../docs/setup_en.md) for the appropriate Lua engine). Record its actual
version and selected GBA core. Do not install software or alter a user's active
emulator session merely to run this test. Use a dedicated instance and isolated
copies of lawful existing ROMs with a separate save directory. Do not copy or
publish private saves. Never connect the probe to an instance already owned by
an Archipelago client.

Load one test ROM, then start this checkout's unmodified
`data/lua/connector_bizhawk_generic.lua`. Its dependencies must remain alongside
it. The stock connector binds and increments its port but does **not** print the
chosen port. Identify the dedicated EmuHawk process ID, then inspect its listening
sockets with read-only OS tools. On Windows PowerShell, first identify the exact
instance with `Get-Process EmuHawk | Select-Object Id,Path,StartTime`, then use:

```
Get-NetTCPConnection -State Listen | Where-Object { $_.OwningProcess -eq VERIFIED_PID -and $_.LocalPort -ge 43055 -and $_.LocalPort -le 43059 } | Select-Object LocalAddress,LocalPort,OwningProcess
```

Replace `VERIFIED_PID` with the independently verified dedicated process ID. On
Linux, use `ps -eo pid,args` to identify the dedicated EmuHawk process and
`ss -ltnp` to match its PID to a listener in 43055–43059. Check that exactly one
matching listener belongs to the intended test instance. Do not guess, scan by
connecting, or choose another instance's port. If process ownership cannot be
verified with available read-only inspection, stop before connecting.

Record the actual executable,
version, core and loaded ROM locally; the script's operator-supplied version/core
fields are not independent proof that a server is native BizHawk. Restart the
connector after loading each ROM. Do not switch ROMs during a probe: the stock
connector caches the ROM hash at startup.

From the repository root, with an existing Python 3.10+ interpreter:

```
python tools/phone_bizhawk_readonly_probe.py --rom /private/path/retail.gba --port 43055 --expected legacy --bizhawk-version ACTUAL_VERSION --core ACTUAL_CORE --output retail-bizhawk.json
```

On Windows use the actual Windows ROM path. Select the actual connector port,
not necessarily 43055. The tool never rotates through other ports. It sends only
VERSION, PING, SYSTEM, HASH, MEMORY_SIZE and READ. It reads 12 bytes at System Bus
`0x0900FFC8` three times, requires stable data and the specified configuration,
and compares the connector's ROM identity with the local file before and after.
The operation has a 30-second overall transport bound and a 5-second connection
bound. It does not write memory, lock emulation, load a ROM, advance frames,
modify saves or run the game watcher. Evidence output is exclusively created,
never overwritten, and contains hashes and lengths rather than ROM bytes or
private file paths. An error produces no successful evidence file.

## Required cases

1. Original USA 16 MiB ROM: SHA-1
   `274b102b6d940f46861a92b4e65f89a51815c12c`, SHA-256
   `cfb194cd0cb373787094a962852e3e564fb2ecdb0609fe065afdd8de3f4e11f1`.
   Use `--expected legacy` and a fresh output file.
2. Existing pre-Phone patch built at
   `7a198f4ff09a0b3a279dc61bc420bc57a0d62c10`: 16,842,752 bytes, SHA-256
   `edd6c31aa19f77c411a587aaa67fc7ecd795220adc5686f6408b5ac03bc1d71e`.
   Use `--expected legacy`. Verify these local hashes before accepting the case.
   This harness does not build, alter, obtain or distribute a ROM.
3. Current shipping disabled ROM, if available: `--expected disabled` requires
   the exact `APPHN01\0` marker and little-endian enable word 0.
4. Existing authorized experimental enabled fixture, if available:
   `--expected enabled` requires the exact marker and enable word 1. Do not
   enable production generation or modify the original ROM to make this case.

The legacy cases require marker-free data, but do not require the returned hash
to equal mGBA's hash. Different emulator cores can map out-of-image bus reads
differently; compare and investigate rather than treating mGBA as authoritative.
Any result beginning `APPHN` but not the exact supported disabled/enabled
configuration is rejected.

## Pairing and acceptance boundaries

These reads exercise the production Python transport and the native stock Lua
READ handler only when the operator has independently verified that endpoint.
They are not an end-to-end Phone grant, persistence, gameplay or watcher-side
pairing test. No AP server connection is made. Existing protocol tests still own
the pairing matrix: legacy/disabled plus capability-free slot accepted; enabled
plus compatible Phone-v1/Copy-v2 slot accepted; both mismatch directions refused
before watcher side effects. Actual native watcher pairing remains a separate
future test and should use isolated fixtures and explicit write authorization.

Retain the sanitized output, observed native emulator provenance and exact
checkout commit together. Do not promote a synthetic/fake connector result into
native acceptance. Never include complete ROMs or saves in a commit.
