\# Kirby \& The Amazing Mirror (GBA) — Archipelago Setup (Work-in-Progress)



This integration is currently implemented as a \*\*BizHawk client + ROM patch memory contract\*\*.



\- The \*\*Python world\*\* is stable for seed generation.

\- The \*\*ROM patch\*\* is responsible for implementing the RAM protocol described below.

\- No seed-specific ROM patching is required yet; all randomization is mediated via RAM.



This document describes the \*\*minimum contract required for a playable game\*\*.



---



\## BizHawk requirements



\- BizHawk 2.x

\- `connector\_bizhawk\_generic.lua` (standard Archipelago BizHawk connector)



All memory access uses the \*\*System Bus\*\* domain.



---



\## Memory contract (EWRAM, System Bus)



All Archipelago-related RAM is located in \*\*EWRAM starting at `0x0202C000`\*\*.



Addresses are defined in: `worlds/kirbyam/data/addresses.json`



The ROM patch must treat this region as \*\*reserved and owned by Archipelago\*\*.



\### AP EWRAM layout



Base address: \*\*`0x0202C000`\*\*



| Address | Size | Name | Description |

|------|------|------|-------------|

| `0x0202C000` | u32 | `shard\_bitfield` | Location check bitfield |

| `0x0202C004` | u32 | `incoming\_item\_flag` | Incoming item mailbox flag |

| `0x0202C008` | u32 | `incoming\_item\_id` | Incoming AP item id |

| `0x0202C00C` | u32 | `incoming\_item\_player` | Sender slot id |



All values are \*\*little-endian 32-bit integers\*\*.



---



\## Location checks



\### `shard\_bitfield` (u32)



\- Each bit represents whether a location has been checked.

\- Bits are \*\*monotonic\*\* (once set, never cleared).



Current proof-of-concept mapping:



\- bit 0 → `SHARD\_1` location checked

# Kirby & The Amazing Mirror (GBA) - Address Policy Notes

## POC baseline

- Baseline ROM for the POC is `Kirby & The Amazing Mirror (USA).gba` only.
- Multi-ROM parity (EU/JP/VC) is out of scope for this phase.
- Non-USA testing issues remain tracked separately (`#99`, `#100`, `#101`, `#102`).

## Address domain separation (locked policy)

Do not mix these two domains:

1. AP transport/mailbox addresses
- Purpose: client/ROM communication contract.
- Source of truth: `worlds/kirbyam/data/addresses.json` under `ram.transport`.
- Examples: `incoming_item_flag`, `incoming_item_id`, `delivered_item_index`.

2. Native game-state addresses
- Purpose: actual in-game progression/check/goal state.
- Source of truth: `worlds/kirbyam/data/native_address_policy.json` and `ram.native` entries in `worlds/kirbyam/data/addresses.json`.
- Current verified native signal: `shard_bitfield_native` at `0x02038970`.

Rule: AP transport fields must never be treated as native gameplay truth.

## Candidate vs verified statuses

- `candidate`: Derived from workbook/cheat/reverse-engineering source and needs live confirmation in BizHawk.
- `verified`: Confirmed by repeatable live memory observation on USA ROM.

Current high-level status:

| Signal type | Candidate exists | Verified exists |
| --- | --- | --- |
| Shard progression | Yes | Yes |
| Dungeon boss defeat | Yes | Not yet |
| Final boss defeat | Yes | Not yet |

Detailed signal registry lives in `worlds/kirbyam/data/native_address_policy.json`.

## Promotion criteria: candidate -> verified

All criteria below must be met before a signal can be marked `verified`:

1. Observed on USA ROM in BizHawk memory viewer during real gameplay action.
2. Before/after transition recorded with exact address, width, and expected semantic meaning.
3. Reproduced in at least 3 independent attempts with consistent transition behavior.
4. Persistence checked across room transitions and save/reload as applicable.
5. Cross-domain sanity check confirms no AP mailbox field is being used as native source.
6. Registry and matrix updated together:
- `worlds/kirbyam/data/native_address_policy.json`
- `worlds/kirbyam/ADDRESS_VERIFICATION_MATRIX.md`

## Implementation notes

- Transport contract details remain documented in `worlds/kirbyam/PROTOCOL.md`.
- Verification workflow remains documented in `worlds/kirbyam/docs/BIZHAWK_TESTING_GUIDE.md`.
\### Client behavior






