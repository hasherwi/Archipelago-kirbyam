"""One qualified Phone cooperation witness, not a generic helper capability.

All seeds require Phone and a charge source on the 146 lower-pocket edge.
Only the qualified profile adds the reviewed cooperation witness. This does not
assert Phone necessity: unqualified solo/ambient-helper histories remain
unmodeled, not physically impossible. Generation requires a repeatable Goal
Game before the Phone gate; battery consumables do not replace that route.
Helpers do not supply attacks, equipment or discarded-star sources to this
rule.
"""
from __future__ import annotations

from functools import cache
from typing import Any

from BaseClasses import ItemClassification

from .data import LocationCategory, data, load_json_data

SOURCE_REGION = "REGION_RAINBOW_ROUTE/ROOM_1_42"


@cache
def _charge_data() -> tuple[str, str, str, str, LocationCategory, str, str, str]:
    raw = load_json_data("phone_logic.json")
    if not isinstance(raw, dict) or type(raw.get("schema")) is not int or raw["schema"] != 1:
        raise ValueError("Unsupported Phone charge logic data")
    rows = raw.get("phone_required_checks")
    # This version binds the single currently modeled Phone route.
    if not isinstance(rows, list) or len(rows) != 1:
        raise ValueError("Phone charge schema 1 requires exactly one check")
    row = rows[0]
    if not isinstance(row, dict) or row.keys() != {"from_region", "to_region", "check", "check_route"}:
        raise ValueError("Invalid Phone check and entrance declaration")
    def item_label(key: object, tag: str, classification: ItemClassification) -> str:
        code = data.item_key_to_id.get(key) if isinstance(key, str) else None
        item = data.items.get(code) if code is not None else None
        if item is None or tag not in item.tags or item.classification != classification:
            raise ValueError(f"Phone logic item {key!r} must resolve to a {tag} {classification.name} item")
        return item.label

    phone = item_label(raw.get("phone_item"), "Phone", ItemClassification.progression)
    battery = item_label(raw.get("battery_item"), "Battery", ItemClassification.useful)
    witness = raw.get("cooperation_witness_items")
    if not isinstance(witness, dict) or witness.keys() != {"hub_connection", "area_key"}:
        raise ValueError("Phone cooperation witness must declare hub connection and area key item keys")
    hub = item_label(witness["hub_connection"], "HubConnections", ItemClassification.progression)
    area_key = item_label(witness["area_key"], "AreaKeys", ItemClassification.progression)
    if raw.get("repeatable_refill_category") != "GOAL_GAME":
        raise ValueError("Phone refill category must be GOAL_GAME")
    main, pocket, check = row["from_region"], row["to_region"], row["check"]
    if main not in data.regions or pocket not in data.regions[main].exits:
        raise ValueError("Phone charge data refers to an unknown entrance")
    route = row["check_route"]
    if not isinstance(route, list) or any(not isinstance(region, str) for region in route):
        raise ValueError("Phone-required check route must list region keys")
    # The Phone is needed at the gate, not when opening the downstream chest.
    # Verify its directed exit sequence without moving the gate onto the award.
    owner = pocket
    visited = {main, pocket}
    for region in route:
        if region in visited or region not in data.regions[owner].exits:
            raise ValueError("Phone-required check route must follow directed exits from the gate")
        visited.add(region)
        owner = region
    location = data.locations.get(check)
    if location is None or location.parent_region != owner or check not in data.regions[owner].locations:
        raise ValueError("Phone-required check must belong to the end of its declared route")
    return phone, battery, hub, area_key, LocationCategory.GOAL_GAME, main, pocket, check


PHONE, BATTERY, EAST_HUB, MOONLIGHT_KEY, _REFILL_CATEGORY, MAIN, POCKET, PHONE_CHECK = _charge_data()
ENTRANCE = f"{MAIN} -> {POCKET}"


def _value(world: Any, name: str, default: Any = None) -> Any:
    option = getattr(world.options, name, default)
    return getattr(option, "value", option)


# Player damage in a replay is execution history, not an acquisition prerequisite.
_PROFILE = {"ability_randomization_mode": 0, "ability_gating": 0,
            "enemy_health_multiplier": 100}


def validate_phone_profile(world: Any, *, require_policy: bool = False) -> bool:
    """Return witness eligibility, not permission to generate the Phone item.

    Valid other profiles remain supported. Malformed or changed installed
    profiles cannot publish a stale qualified rule.
    """
    import json
    values = {name: _value(world, name)
              for name in (*_PROFILE, "room_sanity")}
    for name, value in values.items():
        if type(value) is not int:
            raise ValueError(f"Phone route profile requires canonical {name}")
    for name in ("ability_gating", "room_sanity"):
        if values[name] not in (0, 1):
            raise ValueError(f"Phone route profile requires canonical {name}")
    if values["ability_randomization_mode"] not in (0, 1, 2):
        raise ValueError("Phone route profile requires canonical ability_randomization_mode")
    raw = getattr(world, "_enemy_copy_ability_policy", None)
    if raw is None:
        if require_policy:
            raise ValueError("Phone route requires resolved source policy before publication")
        return False
    from .traversal import SourcePolicy
    if (not isinstance(raw, dict) or type(raw.get("mode")) is not int
            or raw["mode"] != values["ability_randomization_mode"]):
        raise ValueError("Phone route source policy differs from selected mode")
    source = SourcePolicy(raw)
    signature = (tuple(values.items()), json.dumps(raw, sort_keys=True, separators=(",", ":")))
    installed = getattr(world, "_phone_route_signature", None)
    if installed is not None and signature != installed:
        raise ValueError("Phone route profile changed after rule installation")
    return (all(values[name] == value for name, value in _PROFILE.items())
            and source.grant("SIR_KIBBLE", lambda _: True).guaranteed == frozenset({"Cutter"}))


def install_phone_rules(world: Any) -> None:
    import json
    from worlds.generic.Rules import add_rule
    qualified = validate_phone_profile(world, require_policy=True)
    values = {name: _value(world, name)
              for name in (*_PROFILE, "room_sanity")}
    world._phone_route_signature = (tuple(values.items()), json.dumps(
        world._enemy_copy_ability_policy, sort_keys=True, separators=(",", ":")))
    mw, player = world.multiworld, world.player
    entrance = mw.get_entrance(ENTRANCE, player)
    # Ask whether the actually instantiated Goal Game location is reachable,
    # not merely its room. The AP region search computes a least fixed point
    # and retries this gate when a relevant parent region becomes reachable.
    locations = getattr(mw, "get_locations", None)
    goal_games = tuple(
        location for location in (locations(player) if callable(locations) else ())
        if (meta := data.locations.get(getattr(location, "key", None))) is not None
        and meta.category == _REFILL_CATEGORY
    )

    def rule(state: Any) -> bool:
        if not state.has(PHONE, player):
            return False
        if qualified and not (
                state.has(EAST_HUB, player)
                and (not world._area_keys_enabled() or state.has(MOONLIGHT_KEY, player))
                and state.can_reach_region(SOURCE_REGION, player)):
            return False
        return any(game.can_reach(state) for game in goal_games)

    add_rule(entrance, rule)
    dependencies = {game.parent_region for game in goal_games}
    for region in sorted(dependencies, key=lambda region: region.name):
        mw.register_indirect_condition(region, entrance)
    if qualified:
        source = mw.get_region(SOURCE_REGION, player)
        if source not in dependencies:
            mw.register_indirect_condition(source, entrance)
