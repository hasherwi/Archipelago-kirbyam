"""Check that AP item identity is explicit, stable and validated at load time."""
from copy import deepcopy

import pytest

from ..data import _parse_item_catalog, data, load_json_data


def test_every_catalog_item_has_stable_explicit_identity():
    raw = load_json_data("items.json")
    assert isinstance(raw, dict)
    assert len(raw) == len(data.item_key_to_id) == len(data.items)
    assert data.item_key_to_id == {key: entry["item_id"] for key, entry in raw.items()}
    assert [data.item_key_to_id[f"SHARD_{n}"] for n in range(1, 9)] == list(range(3860002, 3860010))
    _, reversed_ids, _ = _parse_item_catalog(dict(reversed(tuple(raw.items()))))
    assert reversed_ids == data.item_key_to_id


@pytest.mark.parametrize(("field", "value", "error"), [
    ("item_id", None, "explicit item_id"),
    ("item_id", True, "explicit item_id"),
    ("item_id", 0, "explicit item_id"),
    ("item_id", 3860001, "Duplicate KirbyAM item_id"),
    ("label", "1 Up", "Duplicate KirbyAM item label"),
    ("label", "", "Invalid label"),
    ("classification", None, "invalid classification"),
    ("classification", "unknown", "Unknown classification"),
    ("tags", "Shards", "Invalid tags"),
    ("tags", ["Shards", "Shards"], "Duplicate tags"),
])
def test_malformed_item_catalog_fails_loudly(field, value, error):
    raw = load_json_data("items.json")
    assert isinstance(raw, dict)
    sample = {key: deepcopy(raw[key]) for key in ("1_UP", "SHARD_1")}
    sample["SHARD_1"][field] = value
    with pytest.raises(ValueError, match=error):
        _parse_item_catalog(sample)
