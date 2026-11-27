"""Project the exact new stock carriers out of frozen historical evidence."""
from copy import deepcopy

from .kibble310_history import digest

_PEP = {
    "metal_228_chest": "949e5e576c58aae85b6b2fd279c0f6b863a8d0b45ea9478cb8063259b418e19f",
    "metal_229_left1up": "b5a52ef7ee74e0decb0180313444993d483aeabb92f79e4c9d2d7a5a5b42cc19",
}
_MOON = {
    "bomb_708_right_c_main": "8ac0d56cad6bdfc902af1988811d4e9c99a6c8011c443a98ccfb8c4be68a14d3",
    "bomb_708_right_c_dead_end": "e2e3a0eb28180c32ef32585964937e262371bd95c97826098964f109d30217ca",
}
_MOON_OWNER = "REGION_MOONLIGHT_MANSION/ROOM_2_01__LOGIC__RIGHT_TOP"
_MOON_EXITS = {"REGION_MOONLIGHT_MANSION/ROOM_2_11", "REGION_MOONLIGHT_MANSION/ROOM_2_11_DEAD_END"}


def before_stock_short_target(row):
    target = row["id"]
    if target in _MOON:
        assert digest(row) == _MOON[target]
        return None
    if target in _PEP:
        row = deepcopy(row)
        assert digest(row["graphs"].pop("bonkers_stock_short")) == _PEP[target]
    return row


def before_stock_short_targets(rows):
    projected = []
    for row in rows:
        target = before_stock_short_target(row["target"])
        if target is not None:
            projected.append({**row, "target": target})
    return projected


def before_stock_short_surfaces(rows):
    extra = [row for row in rows if row["owner"] == _MOON_OWNER and row["target"] in _MOON_EXITS]
    assert len(extra) == 2
    assert all(row["kind"] == "exit" and row["requirement"] is None and not row["room_sanity"] for row in extra)
    return [row for row in rows if row not in extra]


def before_stock_short_catalog(catalog):
    projected = deepcopy(catalog)
    assert (projected["witnesses"], projected["variants"]) == (169, 338)
    extra = [row for row in projected["graphs"]
             if row["target"] in _MOON or row["witness"] == "bonkers_stock_short"]
    assert digest(extra) == "03fc233163c0076914c383f259cfb1852d6b8b899659945a9c0728a9dbd1375b"
    projected["graphs"] = [row for row in projected["graphs"] if row not in extra]
    assert projected["capability_providers"].pop("bomb_708_right_c_burning") == ["Burning"]
    assert projected["sources"].pop("FLAMER@0x088BDE80") == [{
        "source_key": "FLAMER", "identity": "0x088BDE80", "renewable": False, "documented_retry": False,
    }]
    projected["witnesses"], projected["variants"] = 165, 330
    return projected
