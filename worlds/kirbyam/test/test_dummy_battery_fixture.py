"""The complete smoke fixture must satisfy, not bypass, battery byte guards."""
import pytest
from ..tools.create_dummy_rom import build_dummy_rom
from ..kirby_ap_payload.patch_rom import BATTERY_SITES, build_battery_writes


def test_smoke_fixture_seeds_every_battery_guard():
    rom = build_dummy_rom()
    targets = {name: 0x0815F600 for name in BATTERY_SITES}
    assert len(build_battery_writes(rom, targets)) == 13
    for offset, original in BATTERY_SITES.values():
        assert rom[offset:offset + 4] == bytes.fromhex(original)
        for byte in range(4):
            rom[offset + byte] ^= 1
            with pytest.raises(SystemExit):
                build_battery_writes(rom, targets)
            rom[offset + byte] ^= 1
