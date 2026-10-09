# Pi USA-ROM evidence checkpoint

The owner-provided 16 MiB USA ROM was downloaded privately from the existing
Drive file on 2026-10-09. Its SHA-1 is
`274b102b6d940f46861a92b4e65f89a51815c12c`; SHA-256 is
`cfb194cd0cb373787094a962852e3e564fb2ecdb0609fe065afdd8de3f4e11f1`.
The ROM remains outside Git, and its Drive sharing was unchanged.

## Actual build and manifest validation

The local overlay combines PRs 930, 931, 934, 935 and 936 at the exact heads
recorded in the Pi handoff. Its index tree before evidence-tool additions is
`e51100d4f8d58ea0e00912921b92b0e8b095c4eb`. No PR was merged.

- All 65 chest records regenerated from the USA ROM match the existing manifest.
  There are zero ambiguous records. The exact pinned AMR items source SHA-256
  matches `df1aa7bcdfaee028a0f15f2e53c220071cfd147cbe5dbe9417eb89a1c8d96286`.
  Manifest metadata differs for local filenames and the current rooms file hash.
- ARM GCC 14.2.1 rebuilt the combined payload and the real-ROM patcher validated
  its retail hook sites. Four ability-request and ten transition-start calls
  were patched, along with the source-specific chest and runtime hooks.
- The 5,792-byte payload SHA-256 is
  `19ddbda3fda9a481650d265fc707d69c35406cbfa250769736faaa967d4397c5`.
- Generated bsdiff SHA-256:
  `037b7704b1a0404d3b6bcee7a29c8458b087f7c20b3fcf80d0f70a3a9760e4e4`.
  Applying it to the clean ROM reproduces the payload bytes at `0x15E000`,
  preserves the cartridge header and yields a 16 MiB baseline with SHA-256
  `9275b6be03ce6be7c49d6f228783efaa998aca9ab6229c3f1ee3d6019c123d23`.
- APWorld packaging passed; its embedded patch exactly matches the rebuilt
  patch, and the archive contains no `.gba` files.

These outputs are in the private local `real-rom-validation` directory. The
checked-in base patch has not been replaced. A patched baseline is not a tested
playable seed: BizHawk gameplay, save/reload, reconnect and other runtime
acceptance remain unrun.

## Carrot identity and transition evidence

Reproduce with a lawful clean ROM and the current rooms database:

```sh
python worlds/kirbyam/tools/extract_room_evidence.py --rom /private/kirby-usa.gba \
  --room 719 --room 720 --room 730 --room 732 --room 734 \
  --output carrot-room-evidence.json
```

The [derived evidence](carrot-room-evidence.json) contains interpreted fields,
addresses and provenance, with no raw ROM byte dump. The extractor rejects the
wrong ROM, invalid pointers, unknown record layouts and unterminated lists.

| Native room | objectListIdx / doorsIdx | Current AP room-sanity key |
| --- | --- | --- |
| 719 | 258 / 258 | 5-07 |
| 720 | 267 / 267 | 5-14 |
| 730 | 268 / 268 | 5-15 |
| 732 | 259 / 259 | 5-Chest 2 |
| 734 | 261 / 261 | 5-13 |

Native 720 has transition records at source tiles `(17..27, 11)` into native
734 at `(14, 5)`, matching the music-sheet compartment's saved-state spawn.
Native 734 returns from `(2, 4)` to 720 at `(11, 8)`. Its lower exit at `(13, 13)`
goes to native 719 at `(6, 15)`; 719 returns from `(1, 14)` to 734 at `(13, 14)`.
Thus the lower compartment's old `ENTRY_FROM_5_12` claim conflicts with the
current ROM-backed 5-07 identity. These facts require a focused topology
reconciliation, not merely activation of the Music Sheet #6 location.

The misleadingly named `doorsIdx` does **not** enumerate outgoing transitions.
Its table at `0x08D640A4` contains room-completion records, including chest pixel
coordinates. For native 734, its two entries are `(128, 120)` and `(72, 264)`.
Native 720/730 have zero such entries despite having real transitions. Route
records instead come from `gSolidityMaps` at `0x08D63330`, using the room's
solidity-map index and the map descriptor's `+4` pointer.

Layouts and interpretation are pinned to KatAM commit
`7d969fbce14fdc838d2c1ea01389717fb96c3189`:
[data structures](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/include/data.h),
[table addresses](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/data/data_2.s),
[record traversal and completion tracking](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/code_080023A4.c),
and [native transition use](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/code_0800ECAC_2.c).
The subsequent [scoped reconciliation](carrot-topology-reconciliation.md)
corrects the lower 1-UP parent without changing progression edges or active counts. Music Sheet #6 remains dormant and the active minor-check count is 64.

## Pi compatibility

Archipelago's [source guide](https://github.com/ArchipelagoMW/Archipelago/blob/main/docs/running%20from%20source.md)
supports Linux with Python 3.11.9 through 3.13, pip and a matching compiler.
This Pi runs Python 3.13.5. The combined 960-test suite passed with an ARM64
native `_speedups` extension, including generated archives, local MultiServer
hosting and simulated BizHawk transport. `BizHawkClient.py --help` also runs.
The headless Kirby path is verified; the graphical launcher and every other
world's optional dependencies were not installed or certified. The CLI reports
unavailable optional worlds in this deliberately limited environment.

BizHawk itself is a separate emulator. Official
[2.11.1 release assets](https://github.com/TASEmulators/BizHawk/releases/tag/2.11.1)
are Linux x64 and Windows x64. Its [README](https://github.com/TASEmulators/BizHawk#unix)
describes x86-64 releases and partial AArch64 support. Upstream
[ARM discussion](https://github.com/TASEmulators/BizHawk/issues/4052) and
[merged ARM libraries](https://github.com/TASEmulators/BizHawk/pull/4526)
document experimental frontend/SMSHawk progress, including a reported Pi run.
That does not prove GBA emulation or the Archipelago Lua connector on this Pi.

The official master `Assets/dll/libmgba.dll.so` was downloaded for architecture
inspection only: it is an x86-64 ELF, not ARM64. Its SHA-256 is
`26d67d3b904103cf2ecf716f246137ed24bf3c0cc33e03a23c3e74f9c2e4183e`.
The current `Dist/arm64` directory contains SDL2, blip_buf and cimgui libraries,
but no replacement mGBA core. Mono, .NET SDK and EmuHawk are absent on this Pi.
No emulator or system dependencies were installed. Use a supported x86-64
BizHawk host for dependable acceptance testing; native Pi GBA support would
require a separate build/port investigation and runtime verification.
