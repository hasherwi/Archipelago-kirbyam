"""One qualified Phone cooperation witness, not a generic helper capability.

All seeds require Phone ownership on the 146 lower-pocket edge; only the
qualified profile adds the reviewed cooperation witness. This does not assert Phone necessity: unqualified solo/ambient-helper
histories remain unmodeled, not physically impossible. The witness uses a
post-tutorial same-file reset (three batteries), two calls, native Sir Kibble
Cutter for the approach, then human Normal and collective inhale. Helpers do
not supply attacks, equipment or discarded-star sources to this rule.
"""
from __future__ import annotations

from typing import Any

PHONE = "Phone a Friend"
EAST_HUB = "Rainbow Route East - Hub Connection"
MOONLIGHT_KEY = "Moonlight Mansion - Area Key"
SOURCE_REGION = "REGION_RAINBOW_ROUTE/ROOM_1_42"
MAIN = "REGION_MOONLIGHT_MANSION/ROOM_2_18"
POCKET = "REGION_MOONLIGHT_MANSION/ROOM_2_18_BOTTOM_RIGHT"
ENTRANCE = f"{MAIN} -> {POCKET}"


def _value(world: Any, name: str, default: Any = None) -> Any:
    option = getattr(world.options, name, default)
    return getattr(option, "value", option)


_PROFILE = {"ability_randomization_mode": 0, "ability_gating": 0,
            "minimum_health": 6, "maximum_health": 10,
            "enemy_health_multiplier": 100, "one_hit_mode": 0}


def validate_phone_profile(world: Any, *, require_policy: bool = False) -> bool:
    """Return witness eligibility, not permission to generate the Phone item.

    Valid other profiles remain supported. Malformed or changed installed
    profiles cannot publish a stale qualified rule.
    """
    import json
    values = {name: _value(world, name, 0 if name == "one_hit_mode" else None)
              for name in (*_PROFILE, "room_sanity")}
    for name, value in values.items():
        if type(value) is not int:
            raise ValueError(f"Phone route profile requires canonical {name}")
    for name in ("ability_gating", "room_sanity"):
        if values[name] not in (0, 1):
            raise ValueError(f"Phone route profile requires canonical {name}")
    if values["one_hit_mode"] not in (0, 1, 2):
        raise ValueError("Phone route profile requires canonical one_hit_mode")
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
    values = {name: _value(world, name, 0 if name == "one_hit_mode" else None)
              for name in (*_PROFILE, "room_sanity")}
    world._phone_route_signature = (tuple(values.items()), json.dumps(
        world._enemy_copy_ability_policy, sort_keys=True, separators=(",", ":")))
    entrance = world.multiworld.get_entrance(ENTRANCE, world.player)

    if not qualified:
        # Ownership-only conservative constraint, not a physical helper witness.
        add_rule(entrance, lambda state: state.has(PHONE, world.player))
        return

    def rule(state: Any) -> bool:
        return (state.has(PHONE, world.player)
                and state.has(EAST_HUB, world.player)
                and (not world._area_keys_enabled() or state.has(MOONLIGHT_KEY, world.player))
                and state.can_reach_region(SOURCE_REGION, world.player))

    add_rule(entrance, rule)
    world.multiworld.register_indirect_condition(
        world.multiworld.get_region(SOURCE_REGION, world.player), entrance)
