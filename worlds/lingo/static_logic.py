import os
import pickle
import pkgutil
from io import BytesIO
from typing import Dict, List, Set

from .datatypes import Door, Painting, Panel, PanelDoor, Progression, Room

ALL_ROOMS: list[Room] = []
DOORS_BY_ROOM: dict[str, dict[str, Door]] = {}
PANELS_BY_ROOM: dict[str, dict[str, Panel]] = {}
PANEL_DOORS_BY_ROOM: dict[str, dict[str, PanelDoor]] = {}
PAINTINGS: dict[str, Painting] = {}

PROGRESSIVE_ITEMS: set[str] = set()
PROGRESSIVE_DOORS_BY_ROOM: dict[str, dict[str, Progression]] = {}
PROGRESSIVE_PANELS_BY_ROOM: dict[str, dict[str, Progression]] = {}

PAINTING_ENTRANCES: int = 0
PAINTING_EXIT_ROOMS: set[str] = set()
PAINTING_EXITS: int = 0
REQUIRED_PAINTING_ROOMS: list[str] = []
REQUIRED_PAINTING_WHEN_NO_DOORS_ROOMS: list[str] = []

SUNWARP_ENTRANCES: list[str] = []
SUNWARP_EXITS: list[str] = []

SPECIAL_ITEM_IDS: dict[str, int] = {}
PANEL_LOCATION_IDS: dict[str, dict[str, int]] = {}
DOOR_LOCATION_IDS: dict[str, dict[str, int]] = {}
DOOR_ITEM_IDS: dict[str, dict[str, int]] = {}
DOOR_GROUP_ITEM_IDS: dict[str, int] = {}
PANEL_DOOR_ITEM_IDS: dict[str, dict[str, int]] = {}
PANEL_GROUP_ITEM_IDS: dict[str, int] = {}
PROGRESSIVE_ITEM_IDS: dict[str, int] = {}

HASHES: dict[str, str] = {}


def get_special_item_id(name: str):
    if name not in SPECIAL_ITEM_IDS:
        raise Exception(f"Item ID for special item {name} not found in ids.yaml.")

    return SPECIAL_ITEM_IDS[name]


def get_panel_location_id(room: str, name: str):
    if room not in PANEL_LOCATION_IDS or name not in PANEL_LOCATION_IDS[room]:
        raise Exception(f"Location ID for panel {room} - {name} not found in ids.yaml.")

    return PANEL_LOCATION_IDS[room][name]


def get_door_location_id(room: str, name: str):
    if room not in DOOR_LOCATION_IDS or name not in DOOR_LOCATION_IDS[room]:
        raise Exception(f"Location ID for door {room} - {name} not found in ids.yaml.")

    return DOOR_LOCATION_IDS[room][name]


def get_door_item_id(room: str, name: str):
    if room not in DOOR_ITEM_IDS or name not in DOOR_ITEM_IDS[room]:
        raise Exception(f"Item ID for door {room} - {name} not found in ids.yaml.")

    return DOOR_ITEM_IDS[room][name]


def get_door_group_item_id(name: str):
    if name not in DOOR_GROUP_ITEM_IDS:
        raise Exception(f"Item ID for door group {name} not found in ids.yaml.")

    return DOOR_GROUP_ITEM_IDS[name]


def get_panel_door_item_id(room: str, name: str):
    if room not in PANEL_DOOR_ITEM_IDS or name not in PANEL_DOOR_ITEM_IDS[room]:
        raise Exception(f"Item ID for panel door {room} - {name} not found in ids.yaml.")

    return PANEL_DOOR_ITEM_IDS[room][name]


def get_panel_group_item_id(name: str):
    if name not in PANEL_GROUP_ITEM_IDS:
        raise Exception(f"Item ID for panel group {name} not found in ids.yaml.")

    return PANEL_GROUP_ITEM_IDS[name]


def get_progressive_item_id(name: str):
    if name not in PROGRESSIVE_ITEM_IDS:
        raise Exception(f"Item ID for progressive item {name} not found in ids.yaml.")

    return PROGRESSIVE_ITEM_IDS[name]


def load_static_data_from_file():
    global PAINTING_ENTRANCES, PAINTING_EXITS

    from Utils import safe_builtins

    from . import datatypes

    class RenameUnpickler(pickle.Unpickler):
        def find_class(self, module, name):
            if module in ("worlds.lingo.datatypes", "datatypes"):
                return getattr(datatypes, name)
            elif module == "builtins" and name in safe_builtins:
                return getattr(safe_builtins, name)
            raise pickle.UnpicklingError(f"global '{module}.{name}' is forbidden")

    file = pkgutil.get_data(__name__, "data/generated.dat")
    pickdata = RenameUnpickler(BytesIO(file)).load()

    HASHES.update(pickdata["HASHES"])
    PAINTINGS.update(pickdata["PAINTINGS"])
    ALL_ROOMS.extend(pickdata["ALL_ROOMS"])
    DOORS_BY_ROOM.update(pickdata["DOORS_BY_ROOM"])
    PANELS_BY_ROOM.update(pickdata["PANELS_BY_ROOM"])
    PANEL_DOORS_BY_ROOM.update(pickdata["PANEL_DOORS_BY_ROOM"])
    PROGRESSIVE_ITEMS.update(pickdata["PROGRESSIVE_ITEMS"])
    PROGRESSIVE_DOORS_BY_ROOM.update(pickdata["PROGRESSIVE_DOORS_BY_ROOM"])
    PROGRESSIVE_PANELS_BY_ROOM.update(pickdata["PROGRESSIVE_PANELS_BY_ROOM"])
    PAINTING_ENTRANCES = pickdata["PAINTING_ENTRANCES"]
    PAINTING_EXIT_ROOMS.update(pickdata["PAINTING_EXIT_ROOMS"])
    PAINTING_EXITS = pickdata["PAINTING_EXITS"]
    REQUIRED_PAINTING_ROOMS.extend(pickdata["REQUIRED_PAINTING_ROOMS"])
    REQUIRED_PAINTING_WHEN_NO_DOORS_ROOMS.extend(pickdata["REQUIRED_PAINTING_WHEN_NO_DOORS_ROOMS"])
    SUNWARP_ENTRANCES.extend(pickdata["SUNWARP_ENTRANCES"])
    SUNWARP_EXITS.extend(pickdata["SUNWARP_EXITS"])
    SPECIAL_ITEM_IDS.update(pickdata["SPECIAL_ITEM_IDS"])
    PANEL_LOCATION_IDS.update(pickdata["PANEL_LOCATION_IDS"])
    DOOR_LOCATION_IDS.update(pickdata["DOOR_LOCATION_IDS"])
    DOOR_ITEM_IDS.update(pickdata["DOOR_ITEM_IDS"])
    DOOR_GROUP_ITEM_IDS.update(pickdata["DOOR_GROUP_ITEM_IDS"])
    PANEL_DOOR_ITEM_IDS.update(pickdata["PANEL_DOOR_ITEM_IDS"])
    PANEL_GROUP_ITEM_IDS.update(pickdata["PANEL_GROUP_ITEM_IDS"])
    PROGRESSIVE_ITEM_IDS.update(pickdata["PROGRESSIVE_ITEM_IDS"])


# Initialize the static data at module scope.
load_static_data_from_file()
