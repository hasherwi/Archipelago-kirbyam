"""Stable item-art variants shared by the generator and KirbyAM client."""
from enum import IntEnum

from BaseClasses import Item, ItemClassification

from .area_keys import RAINBOW_ROUTE_AREA_KEY_ID
from .data import data
from .vitality import VITALITY_ITEM_IDS


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
    MAP_RAINBOW = 9
    MAP_MOONLIGHT = 10
    MAP_CABBAGE = 11
    MAP_MUSTARD = 12
    MAP_CARROT = 13
    MAP_OLIVE = 14
    MAP_PEPPERMINT = 15
    MAP_RADISH = 16
    MAP_CANDY = 17
    VITALITY = 18
    SOUND_PLAYER = 19
    PAINT_01 = 20
    PAINT_02 = 21
    PAINT_03 = 22
    PAINT_04 = 23
    PAINT_05 = 24
    PAINT_06 = 25
    PAINT_07 = 26
    PAINT_08 = 27
    PAINT_09 = 28
    PAINT_10 = 29
    PAINT_11 = 30
    PAINT_12 = 31
    PAINT_13 = 32
    PAINT_14 = 33
    SHEET_01 = 34
    SHEET_02 = 35
    SHEET_03 = 36
    SHEET_04 = 37
    SHEET_05 = 38
    SHEET_06 = 39
    SHEET_07 = 40
    SHEET_08 = 41
    SHEET_09 = 42
    SHEET_10 = 43
    SHARD = 44
    PHONE = 45
    HUB_SWITCH = 46
    LEVER_WALL = 47
    ABILITY_BEAM = 48
    ABILITY_BURNING = 49
    ABILITY_LASER = 50
    ABILITY_FIRE = 51
    ABILITY_STONE = 52
    ABILITY_FIGHTER = 53
    ABILITY_BOMB = 54
    ABILITY_TORNADO = 55
    ABILITY_WHEEL = 56
    ABILITY_ICE = 57
    ABILITY_SPARK = 58
    ABILITY_MISSILE = 59
    ABILITY_SMASH = 60
    ABILITY_THROW = 61
    ABILITY_HAMMER = 62
    ABILITY_SWORD = 63
    ABILITY_CUTTER = 64
    ABILITY_CUPID = 65
    ABILITY_PARASOL = 66
    KEY_RAINBOW = 67
    KEY_MOONLIGHT = 68
    KEY_CABBAGE = 69
    KEY_MUSTARD = 70
    KEY_CARROT = 71
    KEY_OLIVE = 72
    KEY_PEPPERMINT = 73
    KEY_RADISH = 74
    KEY_CANDY = 75
    KEY_COPY_ROOM = 76


KIRBY_CONSUMABLE_ART_BY_ITEM_CODE = {
    3860001: RewardArt.ONE_UP,
    3860026: RewardArt.FOOD,
    3860030: RewardArt.DRINK,
    3860031: RewardArt.MEAT,
    3860028: RewardArt.TOMATO,
    3860029: RewardArt.CANDY,
    3860027: RewardArt.BATTERY,
}


# Native statue subtype order: CopyAbilityObject1 (0x92), then 2/3/4.
# Baseline ROM inventory for room 970 contains each of these 19 variants.
KIRBY_STATUE_ART_BY_ITEM_CODE = {
    3860107: RewardArt.ABILITY_BEAM,
    3860103: RewardArt.ABILITY_BURNING,
    3860113: RewardArt.ABILITY_LASER,
    3860101: RewardArt.ABILITY_FIRE,
    3860108: RewardArt.ABILITY_STONE,
    3860120: RewardArt.ABILITY_FIGHTER,
    3860109: RewardArt.ABILITY_BOMB,
    3860116: RewardArt.ABILITY_TORNADO,
    3860104: RewardArt.ABILITY_WHEEL,
    3860102: RewardArt.ABILITY_ICE,
    3860115: RewardArt.ABILITY_SPARK,
    3860125: RewardArt.ABILITY_MISSILE,
    3860122: RewardArt.ABILITY_SMASH,
    3860110: RewardArt.ABILITY_THROW,
    3860117: RewardArt.ABILITY_HAMMER,
    3860118: RewardArt.ABILITY_SWORD,
    3860106: RewardArt.ABILITY_CUTTER,
    3860119: RewardArt.ABILITY_CUPID,
    3860105: RewardArt.ABILITY_PARASOL,
}



KIRBY_AREA_KEY_ART_BY_ITEM_CODE = {
    RAINBOW_ROUTE_AREA_KEY_ID: RewardArt.KEY_RAINBOW,
    **{3860041 + n: RewardArt(RewardArt.KEY_MOONLIGHT + n) for n in range(8)},
}


KIRBY_NATIVE_ART_BY_ITEM_CODE = {
    **KIRBY_CONSUMABLE_ART_BY_ITEM_CODE,
    **KIRBY_STATUE_ART_BY_ITEM_CODE,
    **KIRBY_AREA_KEY_ART_BY_ITEM_CODE,
    3860500: RewardArt.KEY_COPY_ROOM,
    3860024: RewardArt.MAP_RAINBOW,
    3860011: RewardArt.MAP_MOONLIGHT,
    3860015: RewardArt.MAP_CABBAGE,
    3860010: RewardArt.MAP_MUSTARD,
    3860016: RewardArt.MAP_CARROT,
    3860013: RewardArt.MAP_OLIVE,
    3860014: RewardArt.MAP_PEPPERMINT,
    3860017: RewardArt.MAP_RADISH,
    3860012: RewardArt.MAP_CANDY,
    3860025: RewardArt.SOUND_PLAYER,
    **dict.fromkeys(VITALITY_ITEM_IDS, RewardArt.VITALITY),
    **{3860200 + index: RewardArt(RewardArt.PAINT_01 + index) for index in range(14)},
    **{3860214 + index: RewardArt(RewardArt.SHEET_01 + index) for index in range(10)},
    **dict.fromkeys(range(3860002, 3860010), RewardArt.SHARD),
    3860501: RewardArt.PHONE,
    # Hub Connections all share the native Big Switch asset, including optional connections.
    **{code: RewardArt.HUB_SWITCH for code, item in data.items.items() if "HubConnections" in item.tags},
    **dict.fromkeys(range(3860037, 3860041), RewardArt.LEVER_WALL),
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
        return KIRBY_NATIVE_ART_BY_ITEM_CODE.get(item.code, RewardArt.GEM)
    return RewardArt.GEM
