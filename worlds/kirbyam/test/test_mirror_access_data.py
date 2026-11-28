"""Keep JSON migration aligned with existing item, topology, and native IDs."""
from copy import deepcopy

import pytest

from .. import mirror_access_data
from ..area_keys import (
    AREA_KEY_BITFIELD_MASK, FALLBACK_STARTING_AREA_ID, RAINBOW_ROUTE_AREA_KEY_ID,
    area_key_entrance_area_ids, dimension_mirror_entrance_names,
)
from ..starting_mirror import (
    STARTING_MIRROR_ENTRANCE, STARTING_MIRROR_ITEM_ID, STARTING_MIRROR_MASK_BIT, starting_mirror_candidates,
)


def test_mirror_access_contract_preserves_existing_direction_and_native_ids() -> None:
    assert AREA_KEY_BITFIELD_MASK == 0x3FE
    assert RAINBOW_ROUTE_AREA_KEY_ID == 3860056
    assert FALLBACK_STARTING_AREA_ID == 2
    assert STARTING_MIRROR_ITEM_ID == 3860416
    assert STARTING_MIRROR_MASK_BIT == 16
    expected = ("REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE -> REGION_RAINBOW_ROUTE/ROOM_1_01")
    assert STARTING_MIRROR_ENTRANCE == expected
    for keys in (False, True):
        assert starting_mirror_candidates(keys)["Room 1-01 Mirror - Hub Connection"] == expected
    gates = area_key_entrance_area_ids()
    assert gates["REGION_MOONLIGHT_MANSION/ROOM_2_11_AFTER_LEVER -> "
                 "REGION_MOONLIGHT_MANSION/ROOM_2_12_LEFT"] == 6
    assert gates["REGION_CARROT_CASTLE/ROOM_5_05 -> REGION_CARROT_CASTLE/ROOM_5_05__LOGIC__CHUTE_SIDE"] == 8
    assert not set(gates).intersection(dimension_mirror_entrance_names())


@pytest.mark.parametrize(("section", "field", "value", "message"), [
    ("starting_mirror", "from_region", "REGION_WRONG", "Unknown directed"),
    ("starting_mirror", "unlock_item", "AREA_KEY_1", "HubConnections catalog item"),
    ("starting_mirror", "tutorial_reward_location", "NO_SUCH_CHEST", "map chest"),
    ("starting_mirror", "native_unlock_bit", True, "unlock bit"),
    ("area_keys", "fallback_key_region", "TUTORIAL", "must have Area Keys"),
    ("area_keys", "minimum_early_reachable_checks", 0, "threshold"),
])
def test_mirror_access_rejects_invalid_data(monkeypatch, section, field, value, message) -> None:
    payload = deepcopy(mirror_access_data.load_json_data("mirror_access.json"))
    payload[section][field] = value
    monkeypatch.setattr(mirror_access_data, "load_json_data", lambda _: payload)
    with pytest.raises(ValueError, match=message):
        mirror_access_data._load_mirror_access()
