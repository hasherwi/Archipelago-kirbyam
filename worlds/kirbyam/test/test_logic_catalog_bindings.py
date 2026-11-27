"""Reject invalid declarative progression and client goal bindings."""
from copy import deepcopy

import pytest

from .. import goal_reporting_data, traversal_rules
from ..data import data, load_json_data
from ..options import Goal


def test_client_goal_bindings_keep_current_and_legacy_locations() -> None:
    ids = goal_reporting_data.goal_location_ids_by_option()
    assert ids == {
        Goal.option_dark_mind: data.locations["GOAL_DARK_MIND"].location_id,
        Goal.option_defeat_any_area_boss: data.locations["GOAL_ANY_AREA_BOSS"].location_id,
        Goal.option_defeat_area_boss: data.locations["GOAL_CONFIGURED_AREA_BOSS"].location_id,
        Goal.option_defeat_area_boss_count: data.locations["GOAL_AREA_BOSS_COUNT"].location_id,
        Goal.option_full_completion: data.locations["GOAL_100_PERCENT"].location_id,
        3: data.locations["GOAL_HIDDEN_AREA_BOSS"].location_id,
    }


def test_reporting_only_goal_cannot_override_current_slot_mode() -> None:
    payload = deepcopy(load_json_data("goal_logic.json"))
    assert isinstance(payload, dict)
    payload["legacy_reporting_only_goals"][0]["slot_option"] = Goal.option_dark_mind
    with pytest.raises(ValueError, match="goal reporting binding"):
        goal_reporting_data._goal_locations(payload)


@pytest.mark.parametrize("clause", [
    {"route": "olive_goal_2_ice"},
    {"guaranteed_source": "not_an_enemy"},
    {"entrance_exists": {"from_region": "REGION_GAME_START", "to_region": "REGION_WRONG"}},
    {"reviewed_graph_sources": {"target": "bomb_517_chocolate", "witnesses": ["not_a_witness"]}},
])
def test_invalid_permission_route_fails_validation(clause) -> None:
    payload = deepcopy(load_json_data("progression_permissions.json"))
    assert isinstance(payload, dict)
    payload["routes"]["olive_goal_2_ice"] = clause
    with pytest.MonkeyPatch.context() as patch, pytest.raises(ValueError, match="Invalid Kirby permission predicate"):
        patch.setattr(traversal_rules, "load_json_data", lambda _: payload)
        traversal_rules._progression_permissions.__wrapped__()
