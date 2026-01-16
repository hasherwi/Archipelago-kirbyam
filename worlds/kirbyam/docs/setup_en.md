# Kirby & The Amazing Mirror (GBA) — Archipelago Setup (Work-in-Progress)

This integration is currently implemented as a **BizHawk client + ROM patch memory contract**.

- The **Python world** is stable for seed generation.
- The **ROM patch** is responsible for implementing the RAM protocol described below.
- No seed-specific ROM patching is required yet; all randomization is mediated via RAM.

This document describes the **minimum contract required for a playable game**.

---

## BizHawk requirements

- BizHawk 2.x
- `connector_bizhawk_generic.lua` (standard Archipelago BizHawk connector)

All memory access uses the **System Bus** domain.

---

## Memory contract (EWRAM, System Bus)

All Archipelago-related RAM is located in **EWRAM starting at `0x0202C000`**.

Addresses are defined in: `worlds/kirbyam/data/addresses.json`

The ROM patch must treat this region as **reserved and owned by Archipelago**.

### AP EWRAM layout

Base address: **`0x0202C000`**

| Address | Size | Name | Description |
|------|------|------|-------------|
| `0x0202C000` | u32 | `shard_bitfield` | Location check bitfield |
| `0x0202C004` | u32 | `incoming_item_flag` | Incoming item mailbox flag |
| `0x0202C008` | u32 | `incoming_item_id` | Incoming AP item id |
| `0x0202C00C` | u32 | `incoming_item_player` | Sender slot id |

All values are **little-endian 32-bit integers**.

---

## Location checks

### `shard_bitfield` (u32)

- Each bit represents whether a location has been checked.
- Bits are **monotonic** (once set, never cleared).

Current proof-of-concept mapping:

- bit 0 → `SHARD_1` location checked
- bit 1 → `SHARD_2` location checked
- …
- bit 7 → `SHARD_8` location checked

**Client behavior:**
- Polls `shard_bitfield` each tick.
- When a new bit transitions from `0 → 1`, sends a `LocationChecks` message to the server.

**ROM behavior:**
- When the player completes a shard location, set the corresponding bit.
- Bits should only ever be set, never cleared.

---

## Incoming item mailbox

This is a **single-slot mailbox** used to deliver AP items from the client to the ROM.

### Fields

- `incoming_item_flag` (u32)
  - `0` = mailbox empty (client may write)
  - `1` = mailbox full (ROM must consume)
- `incoming_item_id` (u32)
  - AP item id (world-defined; opaque to the ROM except for effect mapping)
- `incoming_item_player` (u32)
  - Slot id of the sending player (informational; optional to use)

### Client behavior

- Maintains a local queue of newly received AP items.
- When `incoming_item_flag == 0`:
  1. Writes `incoming_item_id`
  2. Writes `incoming_item_player`
  3. Sets `incoming_item_flag = 1`
- Does not overwrite the mailbox while the flag is `1`.

### ROM behavior (implemented in the base patch)

- Poll `incoming_item_flag` periodically (e.g., once per frame).
- When `incoming_item_flag == 1`:
  1. Read `incoming_item_id` (and optionally `incoming_item_player`)
  2. Grant the item’s in-game effect
  3. Clear `incoming_item_flag` back to `0`

For initial playability, item effects may be implemented in a minimal or placeholder manner (e.g., shard items directly advancing shard progress).

---

## Notes

- This RAM contract is intentionally minimal and designed for early playability.
- Future revisions may replace the single-slot mailbox with a ring buffer or add save persistence.
- All addresses may be relocated if conflicts with game memory are discovered, but must remain consistent between ROM patch and client.
