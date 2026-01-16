"""BizHawk client for Kirby & The Amazing Mirror.

This is a minimal scaffold so the world can be loaded and a seed can be
generated while ROM integration is still under construction.

To progress this into a functional client you will need to:
  - Define ROM validation (ROM name/version string check)
  - Read the per-seed auth token from a ROM address (see data/addresses.json)
  - Read location-check state from RAM (e.g., a bitfield)
  - Write received items into RAM (or a queue consumed by injected code)
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Optional

import worlds._bizhawk as bizhawk
from worlds._bizhawk.client import BizHawkClient

from .data import data

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext


class KirbyAmClient(BizHawkClient):
    game = "Kirby & The Amazing Mirror"
    patch_suffix = ".apkirbyam"

    def __init__(self) -> None:
        super().__init__()
        # Local cache of what we've already reported to the server.
        self._local_checked_locations: set[int] = set()
        # Last observed value of the shard/location bitfield.
        self._last_check_bitfield: Optional[int] = None
        # Cached mapping from bit index -> AP location id.
        self._bit_to_location_id: Optional[dict[int, int]] = None

        # Received-item delivery state.
        # The client will deliver items through a single-slot RAM "mailbox".
        # See `data/addresses.json` keys: incoming_item_flag/incoming_item_id/incoming_item_player.
        self._delivered_items_count: int = 0
        self._pending_items: list[tuple[int, int]] = []  # (item_id, from_player)

    @staticmethod
    def _u32(value: int) -> bytes:
        return int(value).to_bytes(4, "little", signed=False)

    async def _read_u32(self, ctx: "BizHawkClientContext", address: int, domain: str = "System Bus") -> Optional[int]:
        try:
            raw = (await bizhawk.read(ctx.bizhawk_ctx, [(address, 4, domain)]))[0]
            return int.from_bytes(raw, "little", signed=False)
        except Exception:
            return None

    async def _try_deliver_received_items(self, ctx: "BizHawkClientContext") -> None:
        """Deliver received items through a single-slot mailbox in RAM.

        Contract (all addresses in `data/addresses.json`, System Bus domain):

          - incoming_item_flag (u32): 0 = empty/ready; 1 = full/pending
          - incoming_item_id   (u32): AP item id to deliver (world-defined encoding)
          - incoming_item_player (u32): sending player slot id

        The patched ROM is expected to:
          - consume the mailbox when flag==1
          - clear flag back to 0 after consuming
        """
        flag_addr_raw = data.ram_addresses.get("incoming_item_flag")
        item_addr_raw = data.ram_addresses.get("incoming_item_id")
        player_addr_raw = data.ram_addresses.get("incoming_item_player")

        if flag_addr_raw is None or item_addr_raw is None or player_addr_raw is None:
            return

        flag_addr = int(flag_addr_raw)
        item_addr = int(item_addr_raw)
        player_addr = int(player_addr_raw)

        # Queue any newly received items.
        while self._delivered_items_count < len(ctx.items_received):
            ni = ctx.items_received[self._delivered_items_count]
            # `ni.item` is the AP item id.
            self._pending_items.append((int(ni.item), int(ni.player)))
            self._delivered_items_count += 1

        if not self._pending_items:
            return

        # Only write if mailbox is empty.
        flag_val = await self._read_u32(ctx, flag_addr)
        if flag_val is None or flag_val != 0:
            return

        item_id, from_player = self._pending_items[0]
        try:
            await bizhawk.write(ctx.bizhawk_ctx, [
                (item_addr, self._u32(item_id), "System Bus"),
                (player_addr, self._u32(from_player), "System Bus"),
                (flag_addr, self._u32(1), "System Bus"),
            ])
            # Pop only after a successful write.
            self._pending_items.pop(0)
        except Exception:
            # Connector failure or domain issue; try again next loop.
            return

    async def validate_rom(self, ctx: "BizHawkClientContext") -> bool:
        """Return True if the currently loaded ROM appears to be Kirby AM.

        Until a Kirby-specific base patch is in place, we only check that we can
        talk to BizHawk; no robust ROM identification is performed.
        """
        _ = ctx
        return True

    async def get_payload(self, ctx: "BizHawkClientContext") -> Optional[dict]:
        """Provide additional payload data for the server connection.

        Once ROM integration is ready, read an auth token from ROM and return:
            {"auth": <base64 string>}
        """
        _ = ctx
        return None

    async def game_watcher(self, ctx: "BizHawkClientContext") -> None:
        """Main polling loop.

        This is where you'll later:
          - detect newly checked locations and call ctx.send_msgs([...])
          - deliver received items by writing to game memory
        """
        # NOTE:
        # This implementation assumes the patched ROM (or a temporary RAM hack) exposes a 32-bit little-endian
        # bitfield at `addresses.json -> ram -> shard_bitfield` where each set bit corresponds to a checked
        # location. For the current shard proof-of-concept, locations define `bit_index` 0..7 in locations.json.

        # Build mapping once (lazy) so we can translate RAM bits -> AP location IDs.
        if self._bit_to_location_id is None:
            mapping: dict[int, int] = {}
            for loc in data.locations.values():
                if loc.bit_index is None:
                    continue
                # Prefer first-wins behavior; duplicate bit indices are a data error.
                if loc.bit_index not in mapping:
                    mapping[loc.bit_index] = loc.location_id
            self._bit_to_location_id = mapping

        shard_bitfield_addr_raw = data.ram_addresses.get("shard_bitfield")
        shard_bitfield_addr = int(shard_bitfield_addr_raw) if shard_bitfield_addr_raw is not None else None

        while not ctx.exit_event.is_set():
            await asyncio.sleep(getattr(ctx, "watcher_timeout", 0.5) or 0.5)

            # Attempt item delivery first; it is independent of location checks.
            await self._try_deliver_received_items(ctx)

            # If we don't have a known address yet, nothing to do.
            if shard_bitfield_addr is None:
                continue

            try:
                raw = (await bizhawk.read(ctx.bizhawk_ctx, [(shard_bitfield_addr, 4, "System Bus")]))[0]
            except Exception:
                # Most commonly: BizHawk disconnected or request failed; let the outer loop continue.
                continue

            bitfield = int.from_bytes(raw, "little")

            # If we haven't seen the bitfield before, initialize state but do not spam checks.
            if self._last_check_bitfield is None:
                self._last_check_bitfield = bitfield

            # Compute newly set bits since last poll.
            new_bits = bitfield & ~int(self._last_check_bitfield or 0)
            self._last_check_bitfield = bitfield

            if new_bits == 0:
                continue

            newly_checked: set[int] = set()
            for bit_index, location_id in (self._bit_to_location_id or {}).items():
                if new_bits & (1 << bit_index):
                    # Only report locations that exist in this slot's location set.
                    if location_id in ctx.server_locations:
                        newly_checked.add(location_id)

            if newly_checked:
                self._local_checked_locations |= newly_checked
                await ctx.check_locations(self._local_checked_locations)


# Registration helper for BizHawk integration
bizhawk.register_client(KirbyAmClient)
