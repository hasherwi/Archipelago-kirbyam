"""The single post-clear Central stand contract, not a general fixed-source API.

Availability inherits the world's reached-boss completion model. It is not a
native clear receipt, selected objective, equipment item, or helper provider.
"""

from .special_route_data import SPECIAL_ROUTE_PROFILES

_PROFILE = SPECIAL_ROUTE_PROFILES["central_master_carrot_5_13"]

CENTRAL_RETURN_EVENT = _PROFILE["prerequisite_event"]
CENTRAL_MASTER_SOURCE = _PROFILE["source_key"]
CENTRAL_MASTER_IDENTITY = _PROFILE["stand_identity"]
CENTRAL_REGION = _PROFILE["central_region"]
MASTER719_CAPABILITY = _PROFILE["charged_wave_capability"]
MASTER719_PREFIX = _PROFILE["node_prefix"]
MASTER719_NODES = tuple((row["name"], row["native_room"]) for row in _PROFILE["ordered_compartments"])
RAINBOW_WEST_HUB = _PROFILE["west_hub_item"]
CARROT_HUB = _PROFILE["carrot_hub_item"]
CARROT_KEY = _PROFILE["carrot_area_key"]
