# worlds/kirbyam/bizhawk_client/kirbyam_bizhawk.py
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple

# This module is written to be “drop-in friendly” with the typical Archipelago BizHawk pattern:
# - A Python client talks to the AP server.
# - It also talks to BizHawk via a Lua socket script that can read/write memory.
#
# The exact base class/AP client wiring varies by Archipelago version and your repo layout.
# So: keep KirbyAM-specific logic encapsulated, and call these functions from your existing BizHawk client loop.


from worlds.kirbyam.ram_config import KirbyAMRAMConfig, load_ram_config


class KirbyAMPlayablePOC:
    """
    KirbyAM POC runtime:
    - Tracks room-based location checks
    - Applies item effects via memory writes

    Integrate by calling:
    - poc.configure(slot_data, ram_yaml_path)
    - poc.on_frame(mem) periodically
    - poc.on_item(item_id, mem) on item receipt

    'mem' is expected to be a tiny adapter around your BizHawk Lua bridge, with:
    - read_u8(addr), read_u16_le(addr)
    - write_u8(addr, value), write_u16_le(addr, value)
    """

    def __init__(self) -> None:
        self._slot_data: Dict[str, Any] = {}
        self._ram: Optional[KirbyAMRAMConfig] = None
        self._checked_locations: Set[int] = set()

    def configure(self, slot_data: Dict[str, Any], ram_yaml_path: Path) -> None:
        if int(slot_data.get("schema_version", 0)) != 1:
            raise ValueError(f"Unsupported slot_data schema_version: {slot_data.get('schema_version')!r}")
        self._slot_data = slot_data
        self._ram = load_ram_config(ram_yaml_path)

        if slot_data.get("region") != "na":
            raise ValueError("POC client currently supports NA only (slot_data['region'] must be 'na').")

        # Ensure mappings exist
        if "room_triggers" not in slot_data or "item_effects" not in slot_data:
            raise ValueError("slot_data missing required keys: room_triggers/item_effects")

    def _read_room_id(self, mem: Any) -> int:
        assert self._ram is not None
        addr = self._ram.na.room_id_addr
        width = self._ram.na.room_id_width
        if width == 1:
            return int(mem.read_u8(addr))
        if width == 2:
            return int(mem.read_u16_le(addr))
        raise ValueError(f"Unsupported room_id_width={width}")

    def on_frame(self, mem: Any, *, send_location_check: Any) -> None:
        """
        Call every frame or on a short interval.

        send_location_check(location_id: int) should send the check to the AP server.
        """
        if self._ram is None:
            raise RuntimeError("POC client not configured. Call configure() first.")

        room = self._read_room_id(mem)

        # slot_data maps str(location_id)->room_value
        triggers: Dict[str, Any] = self._slot_data["room_triggers"]
        for loc_id_str, expected in triggers.items():
            loc_id = int(loc_id_str)
            expected_room = int(expected)
            if loc_id in self._checked_locations:
                continue
            if room == expected_room:
                send_location_check(loc_id)
                self._checked_locations.add(loc_id)

    def on_item(self, item_id: int, mem: Any) -> None:
        """
        Apply a received item. Call this from your AP client item-receive handler.
        """
        if self._ram is None:
            raise RuntimeError("POC client not configured. Call configure() first.")

        effects: Dict[str, Any] = self._slot_data["item_effects"]
        effect = effects.get(str(item_id))
        if not isinstance(effect, dict):
            return  # unknown item: ignore

        eff_type = str(effect.get("type"))
        amount = int(effect.get("amount", 1))

        if eff_type == "max_hp_up":
            self._apply_max_hp_up(mem, amount)
        elif eff_type == "phone_charge":
            self._apply_phone_charge(mem, amount)

    def _apply_max_hp_up(self, mem: Any, amount: int) -> None:
        assert self._ram is not None
        addr = self._ram.na.max_hp_addr
        width = self._ram.na.hp_width

        if width == 1:
            old = int(mem.read_u8(addr))
            new = max(0, old + amount) & 0xFF
            mem.write_u8(addr, new)
        elif width == 2:
            old = int(mem.read_u16_le(addr))
            new = max(0, old + amount) & 0xFFFF
            mem.write_u16_le(addr, new)
        else:
            raise ValueError(f"Unsupported hp_width={width}")

        # optional: heal-to-full
        cur = self._ram.na.cur_hp_addr
        if cur is not None:
            if width == 1:
                mem.write_u8(cur, new if width == 1 else (new & 0xFF))
            else:
                mem.write_u16_le(cur, new)

    def _apply_phone_charge(self, mem: Any, amount: int) -> None:
        assert self._ram is not None
        addr = self._ram.na.phone_charge_addr
        width = self._ram.na.phone_width
        cap = int(self._ram.na.phone_charge_cap)

        if width == 1:
            old = int(mem.read_u8(addr))
            new = min(cap, max(0, old + amount)) & 0xFF
            mem.write_u8(addr, new)
        elif width == 2:
            old = int(mem.read_u16_le(addr))
            new = min(cap, max(0, old + amount)) & 0xFFFF
            mem.write_u16_le(addr, new)
        else:
            raise ValueError(f"Unsupported phone_width={width}")
