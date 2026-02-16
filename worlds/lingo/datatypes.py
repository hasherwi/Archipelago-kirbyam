from enum import Enum, Flag, auto
from typing import List, NamedTuple, Optional


class RoomAndDoor(NamedTuple):
    room: str | None
    door: str


class RoomAndPanel(NamedTuple):
    room: str | None
    panel: str


class RoomAndPanelDoor(NamedTuple):
    room: str | None
    panel_door: str


class EntranceType(Flag):
    NORMAL = auto()
    PAINTING = auto()
    SUNWARP = auto()
    WARP = auto()
    CROSSROADS_ROOF_ACCESS = auto()
    STATIC_PAINTING = auto()


class RoomEntrance(NamedTuple):
    room: str  # source room
    door: RoomAndDoor | None
    type: EntranceType


class Room(NamedTuple):
    name: str
    entrances: list[RoomEntrance]


class DoorType(Enum):
    NORMAL = 1
    SUNWARP = 2
    SUN_PAINTING = 3


class Door(NamedTuple):
    name: str
    item_name: str
    location_name: str | None
    panels: list[RoomAndPanel] | None
    skip_location: bool
    skip_item: bool
    has_doors: bool
    painting_ids: list[str]
    event: bool
    door_group: str | None
    include_reduce: bool
    type: DoorType
    item_group: str | None


class Panel(NamedTuple):
    required_rooms: list[str]
    required_doors: list[RoomAndDoor]
    required_panels: list[RoomAndPanel]
    colors: list[str]
    check: bool
    event: bool
    exclude_reduce: bool
    achievement: bool
    non_counting: bool
    panel_door: RoomAndPanelDoor | None  # This will always be fully specified.
    location_name: str | None


class PanelDoor(NamedTuple):
    item_name: str
    panel_group: str | None


class Painting(NamedTuple):
    id: str
    room: str
    enter_only: bool
    exit_only: bool
    required: bool
    required_when_no_doors: bool
    required_door: RoomAndDoor | None
    disable: bool
    req_blocked: bool
    req_blocked_when_no_doors: bool


class Progression(NamedTuple):
    item_name: str
    index: int
