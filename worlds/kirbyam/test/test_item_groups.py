"""
Tests for KirbyAM item groups.

Validates that:
- Canonical item groups are defined and properly populated.
- Group aliases work as expected.
- All grouped items exist in the item data.
- No empty groups are exposed (AP requirement).
"""

import pytest

from .. import KirbyAmWorld
from ..data import data
from ..groups import ITEM_GROUPS


# Canonical item group names that must exist and be non-empty.
# These form the stable API contract for users working with groups.
CANONICAL_ITEM_GROUPS = {
    "Shard",      # Mirror shard items (one per area)
    "Unique",     # Unique progression items (e.g., maps, shards)
    "Map",        # Area map items
    "Vitality",   # Vitality counter items
    "Useful",     # Useful but non-critical progression items
    "Filler",     # Filler items (1-Up, 2-Up, 3-Up)
}

# Aliases that should map to canonical group names.
EXPECTED_ALIASES = {
    "Shards": "Shard",  # plural form
}

# Expected members in canonical groups (representative samples for validation).
EXPECTED_GROUP_MEMBERS = {
    "Shard": {
        "Mustard Mountain - Mirror Shard",
        "Moonlight Mansion - Mirror Shard",
        "Candy Constellation - Mirror Shard",
    },
    "Map": {
        "Map - Rainbow Route",
        "Map - Mustard Mountain",
        "Map - Moonlight Mansion",
    },
    "Vitality": {
        "Vitality Counter I",
        "Vitality Counter II",
        "Vitality Counter III",
    },
    "Filler": {
        "1 Up",
        "2 Up",
        "3 Up",
    },
}


class TestItemGroupsExist:
    """Test that canonical item groups are defined and accessible."""

    def test_canonical_groups_exist(self):
        """Canonical groups must be defined in ITEM_GROUPS."""
        missing = CANONICAL_ITEM_GROUPS - set(ITEM_GROUPS.keys())
        assert not missing, f"Missing canonical item groups: {missing}"

    def test_canonical_groups_non_empty(self):
        """Canonical groups must not be empty."""
        empty_groups = {name for name in CANONICAL_ITEM_GROUPS if not ITEM_GROUPS.get(name)}
        assert not empty_groups, f"Empty canonical item groups: {empty_groups}"

    def test_aliases_are_resolvable(self):
        """Aliases must resolve to non-empty canonical groups."""
        for alias, canonical in EXPECTED_ALIASES.items():
            assert alias in ITEM_GROUPS, f"Alias '{alias}' not found in ITEM_GROUPS"
            assert canonical in ITEM_GROUPS, f"Canonical group '{canonical}' not found"
            # Aliases should reference the same set object
            assert ITEM_GROUPS[alias] is ITEM_GROUPS[canonical], \
                f"Alias '{alias}' does not reference the same set as canonical '{canonical}'"


class TestItemGroupMembership:
    """Test that expected items are present in groups."""

    @pytest.mark.parametrize("group_name,expected_members", [
        (group_name, members) for group_name, members in EXPECTED_GROUP_MEMBERS.items()
    ])
    def test_group_contains_expected_members(self, group_name: str, expected_members: set):
        """Each group must contain expected representative members."""
        group_items = ITEM_GROUPS.get(group_name, set())
        missing = expected_members - group_items
        assert not missing, f"Group '{group_name}' missing expected items: {missing}"

    def test_all_grouped_items_exist_in_data(self):
        """All items in groups must exist in item data."""
        data_item_labels = {item.label for item in data.items.values()}
        for group_name, group_items in ITEM_GROUPS.items():
            invalid_items = group_items - data_item_labels
            assert not invalid_items, \
                f"Group '{group_name}' contains items not in data: {invalid_items}"

    def test_canonical_groups_have_expected_item_count(self):
        """Canonical groups should have reasonable item counts."""
        # Shard: 8 items (one per area)
        assert len(ITEM_GROUPS.get("Shard", set())) == 8, \
            "Shard group should have 8 items (one per area)"
        # Map: 9 items (one per area map in areas.json)
        assert len(ITEM_GROUPS.get("Map", set())) == 9, \
            "Map group should have 9 items"
        # Vitality: 4 items (I, II, III, and possibly IV)
        assert len(ITEM_GROUPS.get("Vitality", set())) >= 3, \
            "Vitality group should have at least 3 items"
        # Filler: 3 items (1-Up, 2-Up, 3-Up)
        assert len(ITEM_GROUPS.get("Filler", set())) == 3, \
            "Filler group should have 3 items (1-Up, 2-Up, 3-Up)"


class TestItemGroupsInWorldContext:
    """Test that item groups are accessible from the world object."""

    def test_world_exposes_item_name_groups(self):
        """KirbyAmWorld must expose item_name_groups."""
        assert hasattr(KirbyAmWorld, 'item_name_groups'), \
            "KirbyAmWorld must define item_name_groups"
        # The class attribute should be a dict-like structure with group names
        groups = KirbyAmWorld.item_name_groups
        assert isinstance(groups, dict), "item_name_groups must be a dict"
        # Verify canonical groups are present (may be transformed to frozensets by AP)
        for canonical_group in CANONICAL_ITEM_GROUPS:
            assert canonical_group in groups, \
                f"Canonical group '{canonical_group}' not found in world.item_name_groups"

    def test_no_empty_groups_exposed(self):
        """AP requirement: no empty groups should be exposed."""
        empty_groups = {name for name, members in ITEM_GROUPS.items() if not members}
        assert not empty_groups, f"Empty groups exposed: {empty_groups}"


class TestItemGroupContracts:
    """Test stability of item group contracts for users."""

    def test_shard_group_remains_stable(self):
        """The 'Shard' group is used by world logic and must not break."""
        # The world uses item_name_groups.get("Shard", set()) for pool accounting
        shard_items = ITEM_GROUPS.get("Shard", set())
        assert shard_items, "Shard group must exist and be non-empty for world logic"

    def test_no_life_group_in_canonical(self):
        """The 'Life' group should not be in canonical (was removed from contract)."""
        # 'Life' can exist as a tag-derived group, but it's not a documented canonical group
        # This is a regression test to catch if someone accidentally re-documents it.
        assert "Life" not in CANONICAL_ITEM_GROUPS, \
            "'Life' was removed from canonical groups but appears in test expectations"

    def test_all_canonical_groups_have_use_case(self):
        """Each canonical group should have a documented use case."""
        use_cases = {
            "Shard": "Boss-defeat progression items",
            "Unique": "One-of-a-kind progression items (maps, shards)",
            "Map": "Area map items",
            "Vitality": "Vitality counter increase items",
            "Useful": "Non-critical progression enhancers (e.g., copy ability upgrades)",
            "Filler": "Generic filler items (1-Up, 2-Up, 3-Up)",
        }
        # Verify all canonical groups are documented
        for group_name in CANONICAL_ITEM_GROUPS:
            assert group_name in use_cases, f"No use case documented for '{group_name}'"
