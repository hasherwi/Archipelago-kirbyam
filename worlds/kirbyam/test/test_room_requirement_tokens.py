"""Dispatch coverage for every capability and item token in the room graph."""
from copy import copy
from functools import lru_cache
from unittest.mock import patch
from typing import Any, Iterator, cast

from BaseClasses import CollectionState

import pytest

from .. import KirbyAmWorld
from ..data import data
from ..rules import evaluate_room_logic_requirement
from .test_rules import _FakeState


LEVER_ITEMS = {
    "mm_lever": (3860037, "Moonlight Mansion 2-11 - Lever Wall"),
    "oo_lever": (3860038, "Olive Ocean 6-13 - Lever Wall"),
    "cc_lever": (3860039, "Carrot Castle 5-05 - Lever Wall"),
    "rr_lever": (3860040, "Radish Ruins 8-12 - Lever Wall"),
}


def _tokens(requirement: Any) -> Iterator[str]:
    if isinstance(requirement, str):
        yield requirement
    elif isinstance(requirement, dict):
        for operator, operands in requirement.items():
            if operator in ("all", "any"):
                for operand in operands:
                    yield from _tokens(operand)


ROOM_TOKENS = sorted({
    token for region in data.regions.values()
    for requirement in (*region.exit_requirements.values(), *region.location_requirements.values())
    for token in _tokens(requirement)
})


@pytest.mark.parametrize("token", ROOM_TOKENS)
def test_every_room_token_is_evaluable_with_and_without_owned_items(token: str) -> None:
    assert evaluate_room_logic_requirement(token, cast(CollectionState, _FakeState()), 1) is (token not in LEVER_ITEMS)
    state = _FakeState({label for _, label in LEVER_ITEMS.values()})
    assert evaluate_room_logic_requirement(token, cast(CollectionState, state), 1)


@pytest.mark.parametrize("token", sorted(set(ROOM_TOKENS) - LEVER_ITEMS.keys()))
def test_capabilities_use_explicit_pending_policy(token: str) -> None:
    # Preserve the existing policy rather than invent new AP ownership gates.
    with patch("worlds.kirbyam.rules._allow_pending_ability_gate", return_value=False) as gate:
        assert not evaluate_room_logic_requirement(token, cast(CollectionState, _FakeState()), 1)
        gate.assert_called_once()


@pytest.mark.parametrize("token", LEVER_ITEMS)
def test_lever_tokens_require_their_own_item_not_events_or_other_levers(token: str) -> None:
    item_id, label = LEVER_ITEMS[token]
    assert data.items[item_id].label == label
    other_items = {name for _, name in LEVER_ITEMS.values()} - {label}
    events = {"Activate Lever - " + name.removesuffix(" - Lever Wall")
              for _, name in LEVER_ITEMS.values()}
    assert not evaluate_room_logic_requirement(token, cast(CollectionState, _FakeState(other_items | events)), 1)
    assert evaluate_room_logic_requirement(token, cast(CollectionState, _FakeState({label})), 1)
    assert evaluate_room_logic_requirement(
        {"all": ["can_cut_ropes", token]}, cast(CollectionState, _FakeState({label})), 1)
    assert not evaluate_room_logic_requirement(
        {"all": ["can_cut_ropes", token]}, cast(CollectionState, _FakeState()), 1)
    assert evaluate_room_logic_requirement({"any": [token, "can_use_mini"]}, cast(CollectionState, _FakeState()), 1)


@pytest.mark.parametrize("token", LEVER_ITEMS)
def test_lever_lookup_uses_requested_player(token: str) -> None:
    label = LEVER_ITEMS[token][1]

    class State:
        def has(self, name: str, player: int) -> bool:
            return (name, player) == (label, 2)

    assert not evaluate_room_logic_requirement(token, cast(CollectionState, State()), 1)
    assert evaluate_room_logic_requirement(token, cast(CollectionState, State()), 2)


def test_unknown_tokens_still_fail_closed() -> None:
    with pytest.raises(ValueError, match="Unknown KirbyAM room logic requirement"):
        evaluate_room_logic_requirement("can_cutt_ropes", cast(CollectionState, _FakeState()), 1)


@pytest.fixture(params=[(False, False), (False, True), (True, False), (True, True)],
                ids=['both-cold', 'mirror-warm', 'area-warm', 'both-warm'])
def isolated_graph_caches(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    from .. import area_keys, rules

    # Exercise real graph discovery with private caches, preserving the shared
    # caches for other tests regardless of collection order or assertion failures.
    helpers = ('area_key_entrance_area_ids', 'dimension_mirror_entrance_names')
    checks = []
    for name, warm in zip(helpers, request.param):
        discover = getattr(area_keys, name).__wrapped__
        expected = discover()
        cached = lru_cache(maxsize=1)(discover)
        if warm:
            cached()
        monkeypatch.setattr(rules, name, cached)
        checks.append((cached, expected))
    yield
    for cached, expected in checks:
        assert cached() == expected


@pytest.mark.parametrize('token', ['CanPoundPegs', 'can_pound_pegs'])
@pytest.mark.parametrize('operator', ['all', 'any'])
def test_stake_discovery_preserves_complete_compact_rule(
    token: str, operator: str, isolated_graph_caches: None,
) -> None:
    from types import SimpleNamespace
    from .. import rules
    from .test_rules import _FakeWorld
    from ..options import Goal

    requirement = {operator: [token, 'mm_lever']}
    regions = {'SOURCE': SimpleNamespace(
        exit_requirements={'DESTINATION': requirement}, location_requirements={})}
    raw = {'SOURCE': {'exits': {'DESTINATION': requirement}}}
    world = _FakeWorld(Goal.option_dark_mind)
    # Replace only the rules module's view; Area Key/Dimension Mirror helpers
    # must keep the canonical graph even when their caches are cold.
    rule_data = copy(data)
    rule_data.regions = cast(Any, regions)
    with patch.object(rules, 'data', rule_data), \
            patch.object(rules, 'load_json_data', return_value=raw):
        assert rules.get_stake_gated_transition_entrance_names() == ('SOURCE -> DESTINATION',)
        rules.set_rules(cast(KirbyAmWorld, world))
    entrance = world.multiworld.get_entrance('SOURCE -> DESTINATION', 1)
    lever = LEVER_ITEMS['mm_lever'][1]
    for capability in (False, True):
        for owns_lever in (False, True):
            state = _FakeState({lever} if owns_lever else set())
            with patch.object(rules, '_allow_pending_ability_gate', return_value=capability):
                expected = (capability and owns_lever) if operator == 'all' else (capability or owns_lever)
                assert entrance.access_rule(state) == expected


def test_exported_stake_entrances_exist_in_generated_world() -> None:
    from test.general import setup_solo_multiworld
    from .. import KirbyAmWorld
    from ..rules import get_stake_gated_transition_entrance_names

    world = setup_solo_multiworld(KirbyAmWorld, seed=914)
    names = get_stake_gated_transition_entrance_names()
    assert len(names) == 5
    for name in names:
        entrance = world.get_entrance(name, 1)
        assert entrance.connected_region is not None


def test_explicit_hub_item_requirements_require_ownership() -> None:
    # Item labels are operands of an item expression, not capability tokens.
    hubs = [item.label for item in data.items.values() if "HubConnections" in item.tags]
    assert len(hubs) == 15
    for label in hubs:
        requirement = {"item": label}
        assert not evaluate_room_logic_requirement(requirement, cast(CollectionState, _FakeState()), 1)
        assert evaluate_room_logic_requirement(requirement, cast(CollectionState, _FakeState({label})), 1)
