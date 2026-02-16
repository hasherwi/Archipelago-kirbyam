from __future__ import annotations

import typing
from typing import Dict
from collections.abc import Collection

from ..content.game_content import StardewContent
from ..options import StardewValleyOptions
from ..stardew_rule import StardewRule

if typing.TYPE_CHECKING:
    from .logic import StardewLogic


class LogicRegistry:

    def __init__(self):
        self.item_rules: dict[str, StardewRule] = {}
        self.seed_rules: dict[str, StardewRule] = {}
        self.cooking_rules: dict[str, StardewRule] = {}
        self.crafting_rules: dict[str, StardewRule] = {}
        self.crop_rules: dict[str, StardewRule] = {}
        self.artisan_good_rules: dict[str, StardewRule] = {}
        self.fish_rules: dict[str, StardewRule] = {}
        self.museum_rules: dict[str, StardewRule] = {}
        self.festival_rules: dict[str, StardewRule] = {}
        self.quest_rules: dict[str, StardewRule] = {}
        self.special_order_rules: dict[str, StardewRule] = {}

        self.sve_location_rules: dict[str, StardewRule] = {}


class BaseLogicMixin:
    def __init__(self, *args, **kwargs):
        pass


class BaseLogic(BaseLogicMixin):
    player: int
    registry: LogicRegistry
    options: StardewValleyOptions
    content: StardewContent
    regions: Collection[str]
    logic: StardewLogic

    def __init__(self, player: int, registry: LogicRegistry, options: StardewValleyOptions, content: StardewContent, regions: Collection[str],
                 logic: StardewLogic):
        super().__init__(player, registry, options, content, regions, logic)
        self.player = player
        self.registry = registry
        self.options = options
        self.content = content
        self.regions = regions
        self.logic = logic
