"""Shared room-authored route guards keep their exact scope and physical weld."""
from copy import deepcopy

import pytest

from .. import conditional_routes as rules
from ..traversal_data import _validate_conditional_routes


@pytest.mark.parametrize("name, count", [
    ("candy_9_12_linked_fuse", 2),
    ("mustard_room_4_16_timer", 1),
    ("carrot_yellow_cupid", 1),
])
def test_route_contracts_attached_and_validate_once(name, count):
    row, profile = rules.contract(name)
    assert len(profile["witnesses"]) == count
    seen: set[str] = set()
    _validate_conditional_routes(row, seen)
    with pytest.raises(ValueError, match="duplicate"):
        _validate_conditional_routes(row, seen)
    transplant = {**row, "native_room": row["native_room"] + 1}
    assert not rules.matches_target(name, transplant)
    with pytest.raises(ValueError, match="Detached"):
        _validate_conditional_routes(transplant, set())


def test_unknown_condition_ability_cannot_be_silently_ignored():
    row, _ = rules.contract(rules.CANDY_FUSE.CONTRACT)
    bad = deepcopy(row)
    bad["conditional_routes"][0]["witnesses"][1]["guaranteed_source"]["ability"] = "PossiblyFire"
    with pytest.raises(ValueError, match="grant"):
        _validate_conditional_routes(bad, set())
