import asyncio
from typing import TYPE_CHECKING, Set

import Utils
import worlds._bizhawk as bizhawk
from worlds._bizhawk.client import BizHawkClient

from .data import data

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext


EXPECTED_ROM_NAME_PREFIX = "kirby amazing mirror"  # loosen while you iterate


class KirbyAmazingMirrorClient(BizHawkClient):
    game = "Kirby & The Amazing Mirror"
    system = "GBA"
    patch_suffix = ".apkirbyam"

    def initialize_client(self):
        self._checked_location_bits: Set[int] = set()
        self._delivered_item_index: int = 0

    async def validate_rom(self, ctx: "BizHawkClientContext") -> bool:
        from CommonClient import logger

        try:
            rom_name_bytes = (await bizhawk.read(ctx.bizhawk_ctx, [(0x108, 32, "ROM")]))[0]
            rom_name = bytes([b for b in rom_name_bytes if b != 0]).decode("ascii", errors="ignore").lower()
            if not rom_name.startswith(EXPECTED_ROM_NAME_PREFIX):
                return False
        except Exception:
            return False

        # minimal AP settings
        ctx.game = self.game
        ctx.items_handling = 0b001
        ctx.want_slot_data = False
        ctx.watcher_timeout = 0.125

        self.initialize_client()
        logger.info("Kirby client validated ROM.")
        return True

    async def game_watcher(self, ctx: "BizHawkClientContext") -> None:
        if ctx.server is None or ctx.server.socket.closed:
            return

        await self._poll_locations(ctx)
        await self._deliver_items(ctx)

    async def _poll_locations(self, ctx: "BizHawkClientContext") -> None:
        shard_addr = data.ram_addresses["shard_bitfield"]
        raw = (await bizhawk.read(ctx.bizhawk_ctx, [(shard_addr, 4, "System Bus")]))[0]
        shard_bits = int.from_bytes(raw, "little")

        newly_checked = []
        for bit in range(32):
            if (shard_bits >> bit) & 1:
                if bit not in self._checked_location_bits:
                    self._checked_location_bits.add(bit)
                    # For now, map bit 0..7 to the corresponding location IDs in your world.
                    # Your python world should already define shard locations with bit_index 0..7.
                    for loc in data.locations.values():
                        if loc.bit_index == bit:
                            newly_checked.append(loc.location_id)

        if newly_checked:
            await ctx.send_msgs([{"cmd": "LocationChecks", "locations": newly_checked}])

    async def _deliver_items(self, ctx: "BizHawkClientContext") -> None:
        flag_addr = data.ram_addresses["incoming_item_flag"]
        id_addr = data.ram_addresses["incoming_item_id"]
        player_addr = data.ram_addresses["incoming_item_player"]

        # mailbox empty?
        raw_flag = (await bizhawk.read(ctx.bizhawk_ctx, [(flag_addr, 4, "System Bus")]))[0]
        flag = int.from_bytes(raw_flag, "little")
        if flag != 0:
            return

        # deliver next undelivered received item
        if self._delivered_item_index >= len(ctx.items_received):
            return

        itm = ctx.items_received[self._delivered_item_index]

        # Write full AP item id (u32) + sender slot (u32), then set flag to 1.
        await bizhawk.write(ctx.bizhawk_ctx, [
            (id_addr, int(itm.item).to_bytes(4, "little"), "System Bus"),
            (player_addr, int(itm.player).to_bytes(4, "little"), "System Bus"),
            (flag_addr, (1).to_bytes(4, "little"), "System Bus"),
        ])
        self._delivered_item_index += 1
