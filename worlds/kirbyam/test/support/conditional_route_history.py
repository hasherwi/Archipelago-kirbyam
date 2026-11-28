"""Remove only the exact migrated profiles from frozen historical target pins."""
from copy import deepcopy

from .kibble310_history import digest

_AUTHORED = {'switch_533_room16': '84f89152f578286ea8976706cae7b5f7d8fa3a85c83c67b625f0c897587e98a9', 'bomb_733_yellow': '99c9e1aed71ea20a3c8f83d137b41b67ba01dc64664f2641401fc31c71af2424', 'bomb_402_candy_chest': 'bf9fb7fe9dc305529c1e85cfc03a6e8f6de4b17fb55dce8b2fbf18b4c052ed77'}


def before_conditional_routes_target(row):
    if row["id"] not in _AUTHORED:
        assert "conditional_routes" not in row
        return row
    projected = deepcopy(row)
    assert digest(projected.pop("conditional_routes")) == _AUTHORED[row["id"]]
    return projected
