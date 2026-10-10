"""Format-2 Vitality policy (#946/#947).

The generator, client and native payload share this identity contract.
These helpers never infer ownership from physical chest flags.
"""

from dataclasses import dataclass
from typing import Iterable


VITALITY_ITEM_IDS = (3860018, 3860019, 3860020, 3860021,
                     3860224, 3860225, 3860226, 3860227, 3860228)
VITALITY_ITEM_BITS = {item: 1 << index for index, item in enumerate(VITALITY_ITEM_IDS)}
VITALITY_MASK = 0x1FF
HEALTH_PROTOCOL_VERSION = 2
HEALTH_CONFIG_MAGIC = 0xA9020000
HEALTH_CONFIG_OFFSET = 0x15F690
HEALTH_ROM_TITLE = b"KIRBYAM APV2"
LEGACY_ROM_TITLE = b"AGB KIRBY AM"


@dataclass(frozen=True)
class VitalityPlan:
    minimum: int
    maximum: int

    def __post_init__(self) -> None:
        if any(type(value) is not int or not 1 <= value <= 10
               for value in (self.minimum, self.maximum)):
            raise ValueError("health bounds must be whole numbers within 1..10")
        if self.minimum > self.maximum:
            raise ValueError("maximum_health must be at least minimum_health")

    @property
    def count(self) -> int:
        return self.maximum - self.minimum

    @property
    def item_ids(self) -> tuple[int, ...]:
        return VITALITY_ITEM_IDS[:self.count]

    @property
    def config_word(self) -> int:
        return HEALTH_CONFIG_MAGIC | self.maximum << 8 | self.minimum

    def earned(self, mask: int) -> int:
        return min((mask & VITALITY_MASK).bit_count(), self.count)

    def capacity(self, saved_count: int) -> int:
        return self.minimum + min(max(saved_count, 0), self.count)


def resolve_vitality_plan(minimum: int = 6, maximum: int = 10,
                         one_hit_mode: int = 0) -> VitalityPlan:
    # Keep existing preset precedence, including ignored custom bounds.
    if one_hit_mode == 1:
        return VitalityPlan(1, 1)
    if one_hit_mode == 2:
        return VitalityPlan(1, 5)
    if one_hit_mode != 0:
        raise ValueError(f"unsupported one_hit_mode: {one_hit_mode}")
    return VitalityPlan(minimum, maximum)


def decode_health_config(word: int) -> VitalityPlan:
    if type(word) is not int or word >> 16 != HEALTH_CONFIG_MAGIC >> 16:
        raise ValueError("unsupported health ROM config; regenerate/update")
    return VitalityPlan(word & 0xFF, (word >> 8) & 0xFF)


def validate_health_protocol(title: bytes, config: int, slot_version: int,
                             plan: VitalityPlan) -> None:
    """Fail closed before writes; callers select legacy handling separately."""
    if title != HEALTH_ROM_TITLE or type(slot_version) is not int or slot_version != 2:
        raise ValueError("health ROM/client protocol mismatch; regenerate/update")
    if decode_health_config(config) != plan:
        raise ValueError("health ROM/slot bounds mismatch; regenerate/update")


def history_mask(item_ids: Iterable[int]) -> int:
    """Only call with authenticated complete history, including precollects."""
    mask = 0
    for item_id in item_ids:
        mask |= VITALITY_ITEM_BITS.get(item_id, 0)
    return mask


def replace_owned_bits(previous: int, owned: int) -> int:
    """Preserve the prefixed-history marker and reserved high bits."""
    return (previous & ~VITALITY_MASK) | (owned & VITALITY_MASK)


def partial_receipt(plan: VitalityPlan, previous_mask: int, saved_count: int,
                    item_id: int) -> tuple[int, int, bool]:
    """No shrinking a loaded count during replay; full history does that later.

    A new volatile bit already represented by a saved count must not heal again.
    Return whether earned capacity actually increased, not whether a bit changed.
    """
    bit = VITALITY_ITEM_BITS.get(item_id, 0)
    retained = min(max(saved_count, 0), plan.count)
    mask = previous_mask | bit
    count = max(retained, plan.earned(mask))
    return mask, count, count > retained


def authoritative_health(plan: VitalityPlan, owned_mask: int, hp: int,
                         previous_capacity: int, previous_count: int) -> tuple[int, int, int]:
    """Reconcile complete ownership without repeat healing or death revival."""
    count = plan.earned(owned_mask)
    capacity = plan.minimum + count
    if hp > 0:
        if count > previous_count:
            hp = capacity
        elif 0 < previous_capacity < capacity:
            hp += capacity - previous_capacity
        hp = min(hp, capacity)
    return count, hp, capacity


def remaining_pool(plan: VitalityPlan, locations: int, other_items: int,
                   trap_percent: int = 0) -> tuple[int, int]:
    """Filler/trap arithmetic after selecting non-filler items, not precollect removal."""
    if any(type(value) is not int for value in (locations, other_items, trap_percent)):
        raise ValueError("pool sizes and trap percentage must be integers")
    if min(locations, other_items) < 0 or not 0 <= trap_percent <= 100:
        raise ValueError("invalid pool size or trap percentage")
    disposable = locations - other_items - plan.count
    if disposable < 0:
        raise ValueError("Vitality upgrades exceed unfilled location capacity")
    traps = disposable * trap_percent // 100
    return disposable - traps, traps
