"""Reject invalid declarative progression and client goal bindings."""
from copy import deepcopy
import hashlib
import json

import pytest

from .. import goal_reporting_data, rules, traversal_rules
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


def test_flag_has_a_seed_selected_event_not_a_static_goal_location(monkeypatch) -> None:
    payload = deepcopy(load_json_data("goal_logic.json"))
    assert isinstance(payload, dict)
    flag = Goal.option_capture_the_flag
    assert rules._GOAL_LOCATION_LABELS[flag] == "Capture the Flag"
    assert flag not in goal_reporting_data.goal_location_ids_by_option()
    payload["goals"]["capture_the_flag"] = payload["goals"]["full_completion"]
    monkeypatch.setattr(rules, "load_json_data", lambda _: payload)
    with pytest.raises(ValueError, match="Capture the Flag goal event"):
        rules._load_goal_logic()
    with pytest.raises(ValueError, match="Capture the Flag goal reporting binding"):
        goal_reporting_data._goal_locations(payload)


def _permission_catalogs():
    return deepcopy(load_json_data("regions/rooms.json")), deepcopy(load_json_data("abilities.json"))


def test_migrated_permissions_match_the_previous_semantic_projection() -> None:
    routes, items = traversal_rules._progression_permissions()
    # Canonical semantic projection of the deleted standalone catalog.
    normalized = json.dumps([routes, items], sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(normalized).hexdigest() == (
        "d8927448d3662dcc2ad9117a0d0524dfa0e866fd560195387a339e3dbafe5ceb"
    )


@pytest.mark.parametrize("clause", [
    {"route": "olive_goal_2_ice"},
    {"guaranteed_source": "not_an_enemy"},
    {"entrance_exists": {"from_region": "REGION_GAME_START", "to_region": "REGION_WRONG"}},
    {"reviewed_graph_sources": {"target": "bomb_517_chocolate", "witnesses": ["not_a_witness"]}},
])
def test_invalid_permission_route_fails_validation(clause) -> None:
    rooms, abilities = _permission_catalogs()
    rooms["REGION_OLIVE_OCEAN/ROOM_6_GOAL_2"]["permission_progression_routes"]["olive_goal_2_ice"] = clause
    with pytest.raises(ValueError, match="Invalid Kirby permission predicate"):
        traversal_rules._compile_progression_permissions(rooms, abilities)


def test_duplicate_permission_route_across_rooms_fails_validation() -> None:
    rooms, abilities = _permission_catalogs()
    rooms["REGION_MUSTARD_MOUNTAIN/ROOM_4_16"]["permission_progression_routes"]["olive_goal_2_ice"] = (
        "advanced_logic"
    )
    with pytest.raises(ValueError, match="Duplicate or invalid Kirby permission route"):
        traversal_rules._compile_progression_permissions(rooms, abilities)


@pytest.mark.parametrize("replacement", [
    {"item": "BATTERY", "routes": ["olive_goal_2_ice"]},
    {"item": "ABILITY_UNLOCK_SPARK", "routes": ["olive_goal_2_ice"]},
    {"item": "ABILITY_UNLOCK_ICE", "routes": ["does_not_exist"]},
    {"item": "ABILITY_UNLOCK_ICE", "routes": ["olive_goal_2_ice", "olive_goal_2_ice"]},
    {"item": ["ABILITY_UNLOCK_ICE"], "routes": ["olive_goal_2_ice"]},
    {"item": "ABILITY_UNLOCK_ICE", "routes": "olive_goal_2_ice"},
    {"item": "ABILITY_UNLOCK_ICE", "routes": []},
    {},
    None,
])
def test_invalid_permission_binding_fails_validation(replacement) -> None:
    rooms, abilities = _permission_catalogs()
    abilities["Ice"]["progression_permission"] = replacement
    with pytest.raises(ValueError, match="Invalid Kirby permission promotion"):
        traversal_rules._compile_progression_permissions(rooms, abilities)
