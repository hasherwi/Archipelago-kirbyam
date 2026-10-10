"""Dispatch coverage for every capability and item token in the room graph."""
from unittest.mock import patch

import pytest

from ..data import data
from ..rules import evaluate_room_logic_requirement
from .test_rules import _FakeState


LEVER_ITEMS = {
    "mm_lever": (3860037, "Moonlight Mansion 2-11 - Lever Wall"),
    "oo_lever": (3860038, "Olive Ocean 6-13 - Lever Wall"),
    "cc_lever": (3860039, "Carrot Castle 5-12 - Lever Wall"),
    "rr_lever": (3860040, "Radish Ruins 8-12 - Lever Wall"),
}


def _tokens(requirement):
    if isinstance(requirement, str):
        yield requirement
    elif isinstance(requirement, dict):
        for operands in requirement.values():
            for operand in operands:
                yield from _tokens(operand)


ROOM_TOKENS = sorted({
    token for region in data.regions.values()
    for requirement in (*region.exit_requirements.values(), *region.location_requirements.values())
    for token in _tokens(requirement)
})


@pytest.mark.parametrize("token", ROOM_TOKENS)
def test_every_room_token_is_evaluable_with_and_without_owned_items(token):
    assert evaluate_room_logic_requirement(token, _FakeState(), 1) is (token not in LEVER_ITEMS)
    state = _FakeState({label for _, label in LEVER_ITEMS.values()})
    assert evaluate_room_logic_requirement(token, state, 1)


@pytest.mark.parametrize("token", sorted(set(ROOM_TOKENS) - LEVER_ITEMS.keys()))
def test_capabilities_use_explicit_pending_policy(token):
    # Preserve the existing policy rather than invent new AP ownership gates.
    with patch("worlds.kirbyam.rules._allow_pending_ability_gate", return_value=False) as gate:
        assert not evaluate_room_logic_requirement(token, _FakeState(), 1)
        gate.assert_called_once()


@pytest.mark.parametrize("token", LEVER_ITEMS)
def test_lever_tokens_require_their_own_item_not_events_or_other_levers(token):
    item_id, label = LEVER_ITEMS[token]
    assert data.items[item_id].label == label
    other_items = {name for _, name in LEVER_ITEMS.values()} - {label}
    events = {"Activate Lever - " + name.removesuffix(" - Lever Wall")
              for _, name in LEVER_ITEMS.values()}
    assert not evaluate_room_logic_requirement(token, _FakeState(other_items | events), 1)
    assert evaluate_room_logic_requirement(token, _FakeState({label}), 1)
    assert evaluate_room_logic_requirement({"all": ["can_cut_ropes", token]}, _FakeState({label}), 1)
    assert not evaluate_room_logic_requirement({"all": ["can_cut_ropes", token]}, _FakeState(), 1)
    assert evaluate_room_logic_requirement({"any": [token, "can_use_mini"]}, _FakeState(), 1)


@pytest.mark.parametrize("token", LEVER_ITEMS)
def test_lever_lookup_uses_requested_player(token):
    label = LEVER_ITEMS[token][1]

    class State:
        def has(self, name, player):
            return (name, player) == (label, 2)

    assert not evaluate_room_logic_requirement(token, State(), 1)
    assert evaluate_room_logic_requirement(token, State(), 2)


def test_unknown_tokens_still_fail_closed():
    with pytest.raises(ValueError, match="Unknown KirbyAM room logic requirement"):
        evaluate_room_logic_requirement("can_cutt_ropes", _FakeState(), 1)
