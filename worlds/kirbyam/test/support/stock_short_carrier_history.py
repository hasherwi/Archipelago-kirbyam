"""Project the exact new stock carriers out of frozen historical evidence."""
from copy import deepcopy

from .kibble310_history import digest
from .conditional_route_history import before_conditional_routes_target

_PEP = {
    "metal_228_chest": "949e5e576c58aae85b6b2fd279c0f6b863a8d0b45ea9478cb8063259b418e19f",
    "metal_229_left1up": "b5a52ef7ee74e0decb0180313444993d483aeabb92f79e4c9d2d7a5a5b42cc19",
}
_MOON = {
    "bomb_708_right_c_main": "8ac0d56cad6bdfc902af1988811d4e9c99a6c8011c443a98ccfb8c4be68a14d3",
    "bomb_708_right_c_dead_end": "e2e3a0eb28180c32ef32585964937e262371bd95c97826098964f109d30217ca",
}

_NEW_ROUTES = {
    ('metal_537_beginning_notes', 'stock_bombar_short_missile'): '9627113ad2df3a7c0671ab25433dbcd9c9575d387bcf5589aa6b6e7df8385b65',
    ('bomb_708_right_c_dead_end', 'normal_from_right_top'): 'e0e48258a721babc54ab9497c574e5c5f5ebd1e8a5554de055878d52182e8430',
    ('metal_708_forward', 'short_golem_missile'): '4ce7fe4bae6ada9fca6370d6124dc5b09d1c98768e69e5c9952f8f57979e8f9d',
    ('metal_708_743_main', 'short_golem_missile'): '0ec266d3a5e7ef277b6260eaceba5d634edf42d9e5d0e6ca815a77c5c9d9e6f0',
    ('metal_708_743_dead_end', 'short_golem_missile'): '5066f0c7b02813badffe004ea869864f6078e928db32171b2a6bb5ee9ef72efd',
    ('metal_707_to_712', 'local_doo_missile'): 'cc02410eb78e4ca9503396505b87b5b02339db8eba7e9d1ae437b4fbe0b06733',
    ('peg_513_4_7', 'short_rocky_stone'): 'd6b8e49ac5872eff0b0a6e926bfb76b0f7065055c8747914b2b23133494b642f',
    ('peg_513_4_7', 'local_foley_stone'): '21e3beff6022cffbcdc3dca995d6eeb60b894a4d584b977c90c1272b6c6bc9fa',
    ('peg_527_56_16', 'local_giant_rocky_stone'): '2d8edbd3358818d7276a1f1756157a4ca709519a4246aa3987429f39622197bb',
    ('peg_527_56_16', 'short_bonkers_hammer'): 'ea03e381e5b690a9e31a0db4124cc2c372798c3cd69d0b88033b9584b66d7e66',
    ('peg_527_18_13', 'local_giant_rocky_stone'): '65d463316d44dd532255a75561d3efd75eb293c564bd1271311c71ac2ec6f250',
    ('peg_527_18_13', 'short_bonkers_hammer'): '5dccf00e44202bc11db6ae9a8422a372112fbf2bca41c6a68e46a20a64059fbf',
    ('peg_411_4_3', 'short_401_rocky'): 'b874e05a48f4cb97b517e8e12a116f6de7a0bed5bd3fc220f75a8942836bd08a',
    ('peg_510_7_7', 'short_bonkers_hammer'): 'be70fa057dff0925e51e7c3d7dfde30a8a26755c63b32614eab1b2e6595cc7db',
    ('rope_217_6_5', 'short_225_sword_knight'): '8c23a9ccd2ea61a911c952fe6d43c0a2bbbdc9413fa9177a7c76e8d5ca31c999',
    ('rope_228_11_21', 'short_sword_knight'): 'cb744a97a42b72bcc522b6645f529c680c3228829c3421bef970d704d339322d',
    ('rope_316_35_5', 'short_308_cupie'): 'f81d7f121366d0e8ab956179fa9e8972330e4083f0c4005fec44d1bbd630b455',
}
_NEW_CATALOG_SHA = '306e238ebf200a0a866cd4a80949336abd19b84cde64928b16201d930365ea5c'
_NEW_SOURCES = ('BOMBAR@0x088C2914', 'GOLEM@0x088BC580', 'WADDLE_DOO@0x088BCCDC')


def before_stock_short_target(row):
    row = before_conditional_routes_target(row)
    target = row["id"]
    for (owner, witness), expected in _NEW_ROUTES.items():
        if target == owner:
            row = deepcopy(row)
            assert digest(row["graphs"].pop(witness)) == expected
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


def before_stock_short_catalog(catalog):
    projected = deepcopy(catalog)
    count = len(_NEW_ROUTES)
    assert (projected["witnesses"], projected["variants"]) == (169 + count, 338 + 2 * count)
    new_rows = [row for row in projected["graphs"] if (row["target"], row["witness"]) in _NEW_ROUTES]
    assert len(new_rows) == 2 * count and digest(new_rows) == _NEW_CATALOG_SHA
    projected["graphs"] = [row for row in projected["graphs"] if row not in new_rows]
    for key in _NEW_SOURCES:
        source, identity = key.split("@")
        assert projected["sources"].pop(key) == [{
            "source_key": source, "identity": identity, "renewable": False, "documented_retry": False,
            **({"native_grants": ["Stone"]} if source == "GOLEM" else {}),
        }]
    assert projected['sources'].pop('ROCKY@room:528/template:0x088C93A0') == [{'source_key': 'ROCKY', 'identity': 'room:528/template:0x088C93A0', 'renewable': False, 'documented_retry': False}]
    assert projected['sources'].pop('FOLEY@room:513/template:0x088C9B50') == [{'source_key': 'FOLEY', 'identity': 'room:513/template:0x088C9B50', 'renewable': False, 'documented_retry': False}]
    assert projected['sources'].pop('GIANT_ROCKY@room:527/template:0x088CA568') == [{'source_key': 'GIANT_ROCKY', 'identity': 'room:527/template:0x088CA568', 'renewable': False, 'documented_retry': False}]
    assert projected['sources'].pop('BONKERS@room:515/template:0x088C9FB4') == [{'source_key': 'BONKERS', 'identity': 'room:515/template:0x088C9FB4', 'renewable': False, 'documented_retry': False}]
    assert projected['sources'].pop('CUPIE@0x088C3DEC') == [{'source_key': 'CUPIE', 'identity': '0x088C3DEC', 'renewable': False, 'documented_retry': False}]
    assert projected['sources'].pop('ROCKY@room:401/template:0x088C5864') == [{'source_key': 'ROCKY', 'identity': 'room:401/template:0x088C5864', 'renewable': False, 'documented_retry': False}]
    assert projected['sources'].pop('SWORD_KNIGHT@0x088C2514') == [{'source_key': 'SWORD_KNIGHT', 'identity': '0x088C2514', 'renewable': False, 'documented_retry': False}]
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
