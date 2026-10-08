"""Shared generation/client policy for Kirby's configurable HP range."""

from dataclasses import dataclass


MINIMUM_HEALTH_DEFAULT = 6
MAXIMUM_HEALTH_DEFAULT = 10
HEALTH_MIN = 1
HEALTH_MAX = 10
VITALITY_COUNTER_COUNT = 4


@dataclass(frozen=True)
class HealthRange:
    minimum: int
    maximum: int

    @property
    def vitality_count(self) -> int:
        return self.maximum - self.minimum


def resolve_health_range(
    minimum: int = MINIMUM_HEALTH_DEFAULT,
    maximum: int = MAXIMUM_HEALTH_DEFAULT,
    one_hit_mode: int = 0,
) -> HealthRange:
    """Resolve legacy One-Hit presets first, then validate the custom range.

    The four existing unique vitality items each add one HP. Reject unsupported
    ranges rather than silently changing the requested cap or duplicating items
    that the payload's replay guard would ignore.
    """
    if one_hit_mode == 1:
        return HealthRange(1, 1)
    if one_hit_mode == 2:
        return HealthRange(1, 5)
    if one_hit_mode != 0:
        raise ValueError(f"unsupported one_hit_mode: {one_hit_mode}")
    if any(type(value) is not int or not HEALTH_MIN <= value <= HEALTH_MAX for value in (minimum, maximum)):
        raise ValueError("minimum_health and maximum_health must be whole numbers within 1..10")
    if maximum < minimum:
        raise ValueError("maximum_health must be at least minimum_health")
    if maximum - minimum > VITALITY_COUNTER_COUNT:
        raise ValueError(
            "maximum_health may be at most 4 HP above minimum_health "
            "because KirbyAM has four unique Vitality Counters"
        )
    return HealthRange(minimum, maximum)


def reconcile_health(range_: HealthRange, vitality: int, hp: int, max_hp: int) -> tuple[int, int, int]:
    """Return bounded vitality, HP, and capacity without reviving dead Kirby.

    Native room/respawn and vitality-grant paths use a six-HP base. If raising
    that native capacity, retain the existing damage deficit; repeated calls
    with an already-correct cap cannot heal. Lowering capacity only clamps HP.
    """
    vitality = min(max(vitality, 0), range_.vitality_count)
    desired_max = range_.minimum + vitality
    if hp > 0:
        if 0 < max_hp < desired_max:
            hp += desired_max - max_hp
        hp = min(hp, desired_max)
    return vitality, hp, desired_max
