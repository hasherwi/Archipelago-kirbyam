"""Real hub sources, retained equipment and OR alternatives for native 141/742."""

from dataclasses import replace
from types import SimpleNamespace
from typing import Any

import pytest

from .. import traversal_rules as rules
from ..traversal import METAL_BREAKING_ABILITIES, Position, SourcePolicy
from ..traversal_data import graph_items, room_traversal_graph, room_traversal_targets
from .test_metal_goal2 import simulate_burning_gating
from .test_traversal import policy


CENTRAL = "REGION_RAINBOW_ROUTE/ROOM_1_CENTRAL_CIRCLE"
RAINBOW = "REGION_RAINBOW_ROUTE/ROOM_1_HUB_1"
CABBAGE = "REGION_CABBAGE_CAVERN/ROOM_3_HUB_3"
PERMISSION = frozenset({"Burning Ability"})
TARGETS = {
    "metal_141_left_forward": ("rainbow190_statues", RAINBOW, "metal_141:inner"),
    "metal_141_right_forward": ("rainbow190_statues", RAINBOW, "metal_141:east"),
    "metal_141_left_reverse": ("rainbow190_statues", RAINBOW, "metal_141:lower_return"),
    "metal_742_sparerib": ("cabbage592_statues", CABBAGE, "metal_742:clean_chest"),
    "metal_742_lower_to_warp": ("cabbage592_statues", CABBAGE, "metal_742:clean_warp"),
}
CASES = [(target, witness) for target, (other, _, _) in TARGETS.items()
         for witness in ("central_statues", other)]


def row_for(target: str) -> dict[str, Any]:
    return next(row for row in room_traversal_targets("metal") if row["id"] == target)


@pytest.mark.parametrize("target,witness", CASES)
@pytest.mark.parametrize("area_keys", [False, True])
def test_exact_native_source_guards_and_no_extra_requirements(
    monkeypatch: pytest.MonkeyPatch, target: str, witness: str, area_keys: bool,
) -> None:
    simulate_burning_gating(monkeypatch)
    graph = room_traversal_graph(target, witness, area_keys)
    rainbow = "141" in target
    required = PERMISSION | {"Cabbage Cavern West - Hub Connection",
                             ("Rainbow Route East" if rainbow else "Moonlight Mansion") + " - Hub Connection"}
    if area_keys:
        if rainbow or witness == "central_statues":
            required |= {"Cabbage Cavern - Area Key"}
        if not rainbow:
            required |= {"Moonlight Mansion - Area Key"}
    endpoint = TARGETS[target][2]
    resolver = SourcePolicy({"mode": 0})
    assert graph.evaluate(resolver, required, True).reaches(endpoint)
    for missing in required:
        assert not graph.evaluate(resolver, required - {missing}, True).reaches(endpoint), missing
    assert graph.access_region == (CENTRAL if witness == "central_statues" else TARGETS[target][1])
    assert not graph.requires_all_hub_switches
    assert all(p.equipped == "Normal" for p in graph.starts)
    assert graph.placements == room_traversal_graph("metal_707_to_712", "central_statues").placements
    source190 = next(p for p in graph.placements if p.identity == "0x088B7CEC")
    source790 = next(p for p in graph.placements if p.identity == "0x088BDDF0")
    assert resolver.grant(source190.source_key, lambda _: True).guaranteed == {"Stone"}
    assert resolver.grant(source790.source_key, lambda _: True).guaranteed == {"Bomb"}
    assert all(p.source_key.startswith("STATUE:") for p in graph.placements)


@pytest.mark.parametrize("target,witness", CASES)
@pytest.mark.parametrize("mode,statues,pool,weight,finite,retry", [
    (0, False, None, 0, True, True),
    (1, False, ["Hammer"], 0, True, True),
    (1, True, ["Burning"], 0, True, True),
    (1, True, ["Hammer"], 0, False, False),
    (2, False, ["Hammer"], 100, True, True),
    (2, True, ["Burning", "Hammer"], 100, False, True),
    (2, True, ["Hammer"], 0, False, False),
])
def test_actual_policy_retains_statue_fairness_without_finite_enemy_retry(
    target: str, witness: str, mode: int, statues: bool, pool: list[str] | None,
    weight: int, finite: bool, retry: bool,
) -> None:
    graph = room_traversal_graph(target, witness)
    resolver = policy(mode, statues=statues, pool=pool, weight=weight)  # type: ignore[no-untyped-call]
    owned = graph_items(graph) | PERMISSION | {"Hammer Ability"}
    endpoint = TARGETS[target][2]
    assert graph.evaluate(resolver, owned, True).reaches(endpoint) is finite
    result = graph.evaluate(resolver, owned, True, allow_documented_retries=True)
    assert result.reaches(endpoint) is retry
    if retry and not finite:
        assert result.retry_assumptions
    assert rules.target_applies(row_for(target), resolver)
    assert "requires_guaranteed_source" not in row_for(target)


@pytest.mark.parametrize("target,witness", CASES)
def test_no_source_behind_barrier_or_permission_as_equipment(target: str, witness: str) -> None:
    graph = room_traversal_graph(target, witness)
    endpoint = TARGETS[target][2]
    native = SourcePolicy({"mode": 0})
    source = next(p for p in graph.placements if p.identity == "0x088CEFC8")
    final = next(r for r in graph.routes if r.target == endpoint)
    for broken in (replace(graph, placements=()),
                   replace(graph, placements=(replace(source, node=endpoint),)),
                   replace(graph, starts=(Position(final.source),))):
        assert not broken.evaluate(native, graph_items(graph) | PERMISSION, True).reaches(endpoint)
    assert not any(r.source == endpoint for r in graph.routes)
    suffix = [r for r in graph.routes if r.target.startswith(("metal_141:", "metal_742:", "metal_707:"))]
    assert all(r.opens is None and r.uses_object is None and not r.recover_dropped_ability
               and not r.preserves_room_instance and not r.resets_room_instance for r in suffix)


@pytest.mark.parametrize("target", TARGETS)
@pytest.mark.parametrize("ability", sorted(METAL_BREAKING_ABILITIES | {"Normal"}))
def test_source_free_full_carrier_needs_retained_burning(target: str, ability: str) -> None:
    graph = room_traversal_graph(target, "central_statues")
    start = "hub_190" if "141" in target else "hub_790"
    suffix = tuple(r for r in graph.routes if r.target.startswith(("metal_141:", "metal_742:", "metal_707:")))
    isolated = replace(graph, placements=(), routes=suffix, starts=(Position(start, ability),))
    assert isolated.evaluate(SourcePolicy({"mode": 0}), frozenset(), True).reaches(
        TARGETS[target][2]) is (ability == "Burning")
    if "742" in target:
        assert any(r.source == "metal_707:712_door" for r in suffix)
        original707 = room_traversal_graph("metal_707_to_712", "central_statues")
        assert not any(r.source == "metal_707:712_door" for r in original707.routes)
        assert not any(p.node.startswith("metal_742:") for p in graph.placements)


@pytest.mark.parametrize("target", TARGETS)
def test_one_installed_row_ors_independent_hub_access_and_preserves_base_rule(
    monkeypatch: pytest.MonkeyPatch, target: str,
) -> None:
    simulate_burning_gating(monkeypatch)
    row = row_for(target)
    assert len(row["graphs"]) == 3
    monkeypatch.setattr(rules, "extra_traversal_targets", lambda: (row,))
    resolver = policy(1, statues=False, pool=["Hammer"])  # type: ignore[no-untyped-call]
    # Local Flamer cannot supply Burning, while excluded statues retain native Burning.
    assert resolver.grant("FLAMER", lambda _: True).guaranteed == {"Hammer"}
    assert rules.static_extra_witness(resolver)
    installed = SimpleNamespace(access_rule=lambda state: state.base)
    indirect: list[str] = []
    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy=resolver.policy,
        _ability_gating_enabled=lambda: True, _area_keys_enabled=lambda: True,
        options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=False)),
        multiworld=SimpleNamespace(get_location=lambda *args: installed, get_entrance=lambda *args: installed,
                                   get_region=lambda name, player: name,
                                   register_indirect_condition=lambda name, entrance: indirect.append(name)),
    )
    rules.install_extra_traversal_rules(world)
    owned = set(graph_items(room_traversal_graph(target, "central_statues", True)) | PERMISSION)
    access: set[str] = set()
    state = SimpleNamespace(base=True, has=lambda name, player: name in owned,
                            can_reach_region=lambda name, player: name in access)
    assert not installed.access_rule(state)
    for region in (CENTRAL, TARGETS[target][1]):
        access.add(region)
        assert installed.access_rule(state)
        access.clear()
    access.add(CENTRAL)
    owned.remove("Burning Ability")
    assert not installed.access_rule(state)
    owned.add("Burning Ability")
    state.base = False
    assert not installed.access_rule(state)
    if "exit" in row:
        assert {CENTRAL, TARGETS[target][1]} <= set(indirect)
    else:
        assert not indirect


def test_reverse_alternative_is_a_pre_bank_destination_bypass_not_a_reverse_attack() -> None:
    for witness in ("central_statues", "rainbow190_statues"):
        graph = room_traversal_graph("metal_141_left_reverse", witness)
        assert all(p.node.startswith("hub_") and p.equipped == "Normal" for p in graph.starts)
        assert not any(route.capability == "metal" for route in graph.routes)
        ordinary, = (route for route in graph.routes if route.capability)
        assert ordinary.capability == "ordinary_block_hit" and ordinary.allowed_abilities == frozenset({"Burning"})
        assert ordinary.target == "metal_141:lower_return" and ordinary.water_state == "dry"
        assert "metal_141:inner" not in {node.key for node in graph.nodes}
        for node in ("metal_141:143_carried_arrival", "metal_141:lower_carried_arrival"):
            assert not replace(graph, starts=(Position(node),)).evaluate(
                SourcePolicy({"mode": 0}), graph_items(graph) | PERMISSION, True).reaches(ordinary.target)


@pytest.mark.parametrize("ability", sorted(METAL_BREAKING_ABILITIES | {"Normal"}))
@pytest.mark.parametrize("water", ["dry", "swimming"])
def test_ordinary_block_carrier_is_a_dry_attack_without_equipment_or_open_state_effects(
    ability: str, water: str,
) -> None:
    graph = room_traversal_graph("metal_141_left_reverse", "central_statues")
    action, = (route for route in graph.routes if route.capability)
    action = replace(action, water_state=water)
    initial = Position(action.source, ability, frozenset({"already_open"}), frozenset({"used_source"}))
    isolated = replace(graph, placements=(), routes=(action,), starts=(initial,))
    result = isolated.evaluate(SourcePolicy({"mode": 0}), PERMISSION, True)
    assert result.reaches(action.target) is (water == "dry" and ability == "Burning")
    if result.reaches(action.target):
        assert Position(action.target, "Burning", initial.opened, initial.consumed) in result.positions
    with pytest.raises(ValueError, match="persistent opens"):
        replace(isolated, routes=(replace(action, opens="already_open"),)).evaluate(
            SourcePolicy({"mode": 0}), PERMISSION, True)
    with pytest.raises(ValueError, match="native room"):
        replace(isolated, routes=(replace(action, room_transition=True),)).evaluate(
            SourcePolicy({"mode": 0}), PERMISSION, True)
    with pytest.raises(ValueError, match="narrow"):
        replace(isolated, routes=(replace(action, allowed_abilities=frozenset({"Hammer"})),)).evaluate(
            SourcePolicy({"mode": 0}), PERMISSION, True)


@pytest.mark.parametrize("target", ["metal_141_left_reverse", "metal_742_sparerib"])
@pytest.mark.parametrize("missing_kind", ["permission", "connection", "source_access"])
def test_actual_ap_destination_cannot_bootstrap_its_own_source_path(
    monkeypatch: pytest.MonkeyPatch, target: str, missing_kind: str,
) -> None:
    from BaseClasses import CollectionState, ItemClassification
    from ..data import data
    from .test_mini_traversal import make_world

    simulate_burning_gating(monkeypatch)
    world = make_world(2, 1, room_sanity=1, ability_randomization_statues=0,
                       ability_randomization_no_ability_weight=100)  # type: ignore[no-untyped-call]
    mw = world.multiworld
    row = row_for(target)
    if row.get("exit"):
        entrance = mw.get_entrance(f"{row['region']} -> {row['exit']}", 1)
        destination = row["exit"]
        check = next(loc for loc in mw.get_locations(1) if loc.address == 3961020)
    else:
        entrance = None
        destination = row["region"]
        check = mw.get_location(data.locations[row["location"]].label, 1)
    for region in mw.get_regions(1):
        region.exits.clear()
    menu = mw.get_region("Menu", 1)
    menu.connect(mw.get_region(row["region"], 1))
    if entrance is not None:
        mw.get_region(row["region"], 1).exits.append(entrance)
        mw.get_region(destination, 1).connect(check.parent_region)
    missing = "Burning Ability" if missing_kind == "permission" else (
        "Rainbow Route East - Hub Connection" if "141" in target else "Moonlight Mansion - Hub Connection")
    if missing_kind == "source_access":
        # The source region is only reachable after the gated destination.
        locked_source = check.parent_region.connect(mw.get_region(CENTRAL, 1))
        if entrance is None:
            locked_source.access_rule = check.access_rule
    else:
        menu.connect(mw.get_region(CENTRAL, 1))
    state = CollectionState(mw)
    owned = graph_items(room_traversal_graph(target, "central_statues", True)) | PERMISSION
    for name in owned - ({missing} if missing_kind != "source_access" else set()):
        state.collect(world.create_item(name), prevent_sweep=True)
    if missing_kind != "source_access":
        while state.has(missing, 1):
            state.remove(world.create_item(missing))
        item = world.create_item(missing)
        item.classification = ItemClassification.progression
        check.place_locked_item(item)
        state.sweep_for_advancements(locations=[check])
        assert check not in state.advancements and not state.has(missing, 1)
    assert not check.can_reach(state)
    if missing_kind == "source_access":
        menu.connect(mw.get_region(CENTRAL, 1))
        replacement = CollectionState(mw)
        for name in owned:
            replacement.collect(world.create_item(name), prevent_sweep=True)
        state = replacement
    else:
        state.collect(world.create_item(missing), prevent_sweep=True)
    assert check.can_reach(state)


@pytest.mark.parametrize("area_keys", [False, True])
def test_all_preexisting_compiled_witnesses_remain_identical(area_keys: bool) -> None:
    from dataclasses import asdict
    import hashlib
    import json
    from pathlib import Path

    root = Path(__file__).parents[1]
    baseline = json.loads((root / "dev-docs/carried-burning-prefix-equivalence.json").read_text(encoding="utf-8"))
    records = []
    for kind in ("mini", "peg", "wheel", "fuse", "rope", "block", "reinforced", "metal"):
        for row in room_traversal_targets(kind):
            for witness in row["graphs"]:
                if (row["id"], witness) in CASES:
                    continue
                graph = room_traversal_graph(row["id"], witness, area_keys)
                normalized = json.loads(json.dumps(asdict(graph), default=sorted, sort_keys=True))
                records.append([row["id"], witness, normalized])
    assert len(records) == baseline["unchanged_witnesses"] == 92
    encoded = json.dumps(sorted(records), sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(encoded).hexdigest() == baseline["area_key_hashes"][str(area_keys).lower()]
