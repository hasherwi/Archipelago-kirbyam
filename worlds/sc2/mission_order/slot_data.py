"""
Houses the data structures representing a mission order in slot data.
Creating these is handled by the nodes they represent in .nodes.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Protocol

from .entry_rules import SubRuleRuleData


class MissionOrderObjectSlotData(Protocol):
    entry_rule: SubRuleRuleData


@dataclass
class CampaignSlotData:
    name: str
    entry_rule: SubRuleRuleData
    exits: list[int]
    layouts: list[LayoutSlotData]

    @staticmethod
    def legacy(name: str, layouts: list[LayoutSlotData]) -> CampaignSlotData:
        return CampaignSlotData(name, SubRuleRuleData.empty(), [], layouts)


@dataclass
class LayoutSlotData:
    name: str
    entry_rule: SubRuleRuleData
    exits: list[int]
    missions: list[list[MissionSlotData]]

    @staticmethod
    def legacy(name: str, missions: list[list[MissionSlotData]]) -> LayoutSlotData:
        return LayoutSlotData(name, SubRuleRuleData.empty(), [], missions)


@dataclass
class MissionSlotData:
    mission_id: int
    prev_mission_ids: list[int]
    entry_rule: SubRuleRuleData
    victory_cache_size: int = 0

    @staticmethod
    def empty() -> MissionSlotData:
        return MissionSlotData(-1, [], SubRuleRuleData.empty())

    @staticmethod
    def legacy(mission_id: int, prev_mission_ids: list[int], entry_rule: SubRuleRuleData) -> MissionSlotData:
        return MissionSlotData(mission_id, prev_mission_ids, entry_rule)
