"""Stable item-art variants shared by the generator and KirbyAM client."""
from enum import IntEnum

from BaseClasses import Item, ItemClassification


class RewardArt(IntEnum):
    GEM = 0
    TRAP = 1
    ONE_UP = 2
    FOOD = 3
    DRINK = 4
    MEAT = 5
    TOMATO = 6
    CANDY = 7
    BATTERY = 8


KIRBY_CONSUMABLE_ART_BY_ITEM_CODE = {
    3860001: RewardArt.ONE_UP,
    3860026: RewardArt.FOOD,
    3860030: RewardArt.DRINK,
    3860031: RewardArt.MEAT,
    3860028: RewardArt.TOMATO,
    3860029: RewardArt.CANDY,
    3860027: RewardArt.BATTERY,
}


def reward_art_for_item(item: Item | None, location_player: int) -> RewardArt:
    """Choose art for the item placed at a check in the current world."""
    if item is None or item.code is None:
        return RewardArt.GEM
    # A trap stays a trap even when another slot receives it, and takes
    # precedence over an item-code match if a classification is combined.
    if item.classification & ItemClassification.trap:
        return RewardArt.TRAP
    if item.game == "Kirby & The Amazing Mirror" and item.player == location_player:
        return KIRBY_CONSUMABLE_ART_BY_ITEM_CODE.get(item.code, RewardArt.GEM)
    return RewardArt.GEM
