"""Bind client goal reporting to the same locations used by generation."""
from .data import LocationCategory, data, load_json_data
from .options import Goal


def _goal_locations(payload) -> dict[int, int]:
    if not isinstance(payload, dict) or type(payload.get("schema")) is not int or payload["schema"] != 1:
        raise ValueError("Unsupported Kirby goal reporting schema")
    goals = payload["goals"]
    if goals.keys() != set(Goal.name_lookup.values()):
        raise ValueError("Kirby goal reporting must bind each current goal mode")
    rows = [(mode, goals[key]["goal_location"]) for mode, key in Goal.name_lookup.items()]
    for legacy in payload["legacy_reporting_only_goals"]:
        rows.append((legacy["slot_option"], legacy["goal_location"]))
    ids: dict[int, int] = {}
    for mode, key in rows:
        loc = data.locations.get(key)
        if (type(mode) is not int or mode in ids or loc is None
                or loc.category != LocationCategory.GOAL or loc.location_id in ids.values()):
            raise ValueError(f"Invalid Kirby goal reporting binding: {mode!r} → {key!r}")
        ids[mode] = loc.location_id
    return ids


_GOAL_DECLARATION = load_json_data("goal_logic.json")
_GOAL_LOCATION_IDS = _goal_locations(_GOAL_DECLARATION)
assert isinstance(_GOAL_DECLARATION, dict)
_LEGACY_GOAL, = _GOAL_DECLARATION["legacy_reporting_only_goals"]
LEGACY_HIDDEN_BOSS_GOAL_OPTION = _LEGACY_GOAL["slot_option"]


def goal_location_ids_by_option() -> dict[int, int]:
    """Return a separate copy for each client instance."""
    return dict(_GOAL_LOCATION_IDS)
