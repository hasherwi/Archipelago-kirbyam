"""One qualified Phone cooperation witness, not a generic helper capability.

Enabled seeds conservatively replace the legacy permissive 146 lower-pocket
edge. This does not assert Phone necessity: unqualified solo/ambient-helper
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


def phone_progression_enabled(world: Any) -> bool:
    value = _value(world, "phone_progression", 0)
    if type(value) is not int or value not in (0, 1):
        raise ValueError("phone_progression must be a canonical toggle value")
    return value == 1


def validate_phone_profile(world: Any, *, require_policy: bool = False) -> None:
    """Validate early options, and resolved source policy whenever available."""
    if not phone_progression_enabled(world):
        return
    expected = {"ability_randomization_mode": 0, "ability_gating": 0,
                "minimum_health": 6, "maximum_health": 10,
                "enemy_health_multiplier": 100, "room_sanity": 0,
                "one_hit_mode": 0}
    mismatches = [f"{name}={value}" for name, value in expected.items()
                  if (type(_value(world, name, 0 if name == "one_hit_mode" else None)) is not int
                      or _value(world, name, 0 if name == "one_hit_mode" else None) != value)]
    if mismatches:
        raise ValueError("Phone progression requires the reviewed profile: " + ", ".join(mismatches))
    raw = getattr(world, "_enemy_copy_ability_policy", None)
    if raw is None and require_policy:
        raise ValueError("Phone progression requires resolved source policy before publication")
    if raw is not None:
        from .traversal import SourcePolicy
        if (not isinstance(raw, dict) or type(raw.get("mode")) is not int or raw.get("mode") != 0
                or SourcePolicy(raw).grant("SIR_KIBBLE", lambda _: True).guaranteed
                != frozenset({"Cutter"})):
            raise ValueError("Phone progression requires native Sir Kibble -> Cutter")


def install_phone_rules(world: Any) -> None:
    if not phone_progression_enabled(world):
        return
    from worlds.generic.Rules import add_rule
    validate_phone_profile(world, require_policy=True)
    entrance = world.multiworld.get_entrance(ENTRANCE, world.player)

    def rule(state: Any) -> bool:
        return (state.has(PHONE, world.player)
                and state.has(EAST_HUB, world.player)
                and (not world._area_keys_enabled() or state.has(MOONLIGHT_KEY, world.player))
                and state.can_reach_region(SOURCE_REGION, world.player))

    add_rule(entrance, rule)
    world.multiworld.register_indirect_condition(
        world.multiworld.get_region(SOURCE_REGION, world.player), entrance)
