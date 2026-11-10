"""Unaccepted helper routes cannot accidentally enable the experimental gate."""
from pathlib import Path

from test.general import setup_multiworld
from .. import KirbyAmWorld
from ..data import data
from ..phone_protocol import PHONE_ITEM_ID


def test_production_generation_does_not_enable_phone_without_route_acceptance() -> None:
    multiworld = setup_multiworld(KirbyAmWorld, seed=1086, options={
        "ability_gating": 1, "area_keys": 1, "room_sanity": 1,
    })
    world = multiworld.worlds[1]
    assert PHONE_ITEM_ID not in data.items
    assert all(item.code != PHONE_ITEM_ID for item in multiworld.itempool)
    assert not world.fill_slot_data().get("phone_protocol_version", 0)
    assert len(multiworld.itempool) == len(multiworld.get_unfilled_locations())
    source = Path(__file__).resolve().parents[1] / "kirby_ap_payload" / "phone.c"
    assert 'gApPhoneConfig = {"APPHN01", 0u}' in source.read_text()
