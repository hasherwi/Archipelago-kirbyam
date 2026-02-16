from typing import NamedTuple, Optional, Union

from BaseClasses import Item, ItemClassification


class SongData(NamedTuple):
    """Special data container to contain the metadata of each song to make filtering work."""

    code: int | None
    uid: str
    album: str
    streamer_mode: bool
    easy: int | None
    hard: int | None
    master: int | None


class AlbumData(NamedTuple):
    """Special data container to contain the metadata of each album to make filtering work. Currently not used."""

    code: int | None


class MuseDashSongItem(Item):
    game: str = "Muse Dash"

    def __init__(self, name: str, player: int, data: SongData | AlbumData) -> None:
        super().__init__(name, ItemClassification.progression, data.code, player)


class MuseDashFixedItem(Item):
    game: str = "Muse Dash"

    def __init__(self, name: str, classification: ItemClassification, code: int | None, player: int) -> None:
        super().__init__(name, classification, code, player)
