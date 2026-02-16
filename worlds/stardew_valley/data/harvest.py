from dataclasses import dataclass
from typing import Tuple
from collections.abc import Mapping, Sequence

from ..strings.season_names import Season
from .game_item import ItemTag, Source


@dataclass(frozen=True, kw_only=True)
class ForagingSource(Source):
    regions: tuple[str, ...]
    seasons: tuple[str, ...] = Season.all


@dataclass(frozen=True, kw_only=True)
class SeasonalForagingSource(Source):
    season: str
    days: Sequence[int]
    regions: tuple[str, ...]

    def as_foraging_source(self) -> ForagingSource:
        return ForagingSource(seasons=(self.season,), regions=self.regions)


@dataclass(frozen=True, kw_only=True)
class FruitBatsSource(Source):
    ...


@dataclass(frozen=True, kw_only=True)
class MushroomCaveSource(Source):
    ...


@dataclass(frozen=True, kw_only=True)
class HarvestFruitTreeSource(Source):
    add_tags = (ItemTag.CROPSANITY,)

    sapling: str
    seasons: tuple[str, ...] = Season.all

    @property
    def requirement_tags(self) -> Mapping[str, tuple[ItemTag, ...]]:
        return {
            self.sapling: (ItemTag.CROPSANITY_SEED,)
        }


@dataclass(frozen=True, kw_only=True)
class HarvestCropSource(Source):
    add_tags = (ItemTag.CROPSANITY,)

    seed: str
    seasons: tuple[str, ...] = Season.all
    """Empty means it can't be grown on the farm."""

    @property
    def requirement_tags(self) -> Mapping[str, tuple[ItemTag, ...]]:
        return {
            self.seed: (ItemTag.CROPSANITY_SEED,)
        }


@dataclass(frozen=True, kw_only=True)
class ArtifactSpotSource(Source):
    amount: int
