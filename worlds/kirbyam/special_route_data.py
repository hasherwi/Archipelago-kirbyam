"""Named evidence-backed profiles and source scope contracts."""
from .data import load_json_data

SOURCE_SCOPE_CATALOG = load_json_data("traversal_source_scopes.json")
if (not isinstance(SOURCE_SCOPE_CATALOG, dict)
        or type(SOURCE_SCOPE_CATALOG.get("schema")) is not int or SOURCE_SCOPE_CATALOG["schema"] != 1):
    raise ValueError("Unsupported Kirby traversal source scopes schema")

SPECIAL_ROUTE_PROFILES = SOURCE_SCOPE_CATALOG["special_route_profiles"]
