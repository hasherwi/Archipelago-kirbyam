"""Minimal preserves AP option semantics but cannot bypass Kirby all-check validation."""

from argparse import Namespace
from collections.abc import Iterable
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import random
import shutil
from types import SimpleNamespace
from typing import Any, cast

import pytest
from Options import Accessibility
from BaseClasses import MultiWorld

from .. import KirbyAmWorld, peg_traversal, traversal_rules, wheel_traversal
from ..ability_randomization import build_enemy_copy_ability_policy
from ..data import data
from ..traversal import Node, Placement, Position, Route, SourcePolicy, TraversalGraph
from ..traversal_data import has_graph_access, requires_all_traversal_witnesses
from .test_mini_traversal import make_world


FIXTURES = Path(__file__).with_name("data") / "traversal_accessibility"
FUZZ_CASES = {
    1: (271418054, "4d450086f2e39d6056ccc5fc5bf7bc9290e616a555ac915d39941f4ef3d2cf1d"),
    69: (108836542, "0a25d61c00d636bd9c02c0a4dcb74ee6a7447d4d0686ed71be9a802a25e62b36"),
    95: (321375454, "f9a2bc967e178e691cc53095c96c6fb9dc3c326a5cdd611d231d90d4530ae90e"),
}


@pytest.mark.parametrize("option,required", [
    (Accessibility.from_any("full"), True), (Accessibility.from_any("minimal"), False),
    (Accessibility.from_any("none"), False), (None, True), (2, True), ("minimal", True),
    (SimpleNamespace(value=2), True), (Accessibility(cast(Any, 2.0)), True),
])
def test_only_typed_minimal_option_defers_all_check_validation(option: object, required: bool) -> None:
    world = SimpleNamespace(options=SimpleNamespace(accessibility=option))
    assert requires_all_traversal_witnesses(world) is required


def test_missing_options_keep_full_validation() -> None:
    assert requires_all_traversal_witnesses(SimpleNamespace())
    assert requires_all_traversal_witnesses(SimpleNamespace(options=SimpleNamespace()))


@pytest.mark.parametrize("mode", [0, 1, 2])
def test_explicit_source_filter_opt_out_preserves_assignment(mode: int) -> None:
    initial = build_enemy_copy_ability_policy(random.Random(73), mode, True, True,
                                              whitelist=("Stone",), no_ability_weight=100)
    before = deepcopy(initial)
    selected = peg_traversal.validate_peg_assignment(
        initial, lambda: pytest.fail("Explicit filter opt-out must not resample a source policy"), True,
        require_all_witnesses=False,
    )
    assert selected is initial and initial == before


@pytest.mark.parametrize("required", [False, True])
def test_explicit_invalid_budget_remains_an_error(required: bool) -> None:
    with pytest.raises(ValueError, match="budget must be positive"):
        peg_traversal.validate_peg_assignment(
            {"mode": 1}, lambda: {}, False, 0, require_all_witnesses=required,
        )


@pytest.mark.parametrize("invalid", [None, 0, 1, "minimal"])
def test_assignment_validation_flag_requires_boolean(invalid: Any) -> None:
    with pytest.raises(TypeError, match="must be a boolean"):
        peg_traversal.validate_peg_assignment(
            {"mode": 1}, lambda: {}, False, require_all_witnesses=invalid,
        )


@pytest.mark.parametrize("budget", [1, 3, None])
def test_all_check_filter_keeps_explicit_and_default_bounded_search(
    monkeypatch: pytest.MonkeyPatch, budget: int | None,
) -> None:
    initial = {"mode": 1}
    calls: list[int] = []

    def factory() -> dict[str, Any]:
        calls.append(1)
        return initial

    monkeypatch.setattr(peg_traversal, "SourcePolicy", lambda *_: SimpleNamespace(mode=1))
    monkeypatch.setattr(wheel_traversal, "static_wheel_witness", lambda _: False)
    kwargs: dict[str, Any] = {} if budget is None else {"max_attempts": budget}
    expected = 8192 if budget is None else budget
    with pytest.raises(ValueError, match=f"Wheel-source search budget exhausted after {expected} attempts"):
        peg_traversal.validate_peg_assignment(initial, factory, False, **kwargs)
    assert len(calls) == expected - 1
    assert initial == {"mode": 1}


def installer_setup(
    monkeypatch: pytest.MonkeyPatch, kind: str, mode: int, accessibility: str, gating: bool, *, sources: bool,
) -> tuple[Any, ...]:
    capability, source, ability = {
        "peg": ("peg", "BONKERS", "Hammer"), "wheel": ("wheel_race", "WHEELIE", "Wheel"),
        "fuse": ("fuse", "HOT_HEAD", "Fire"), "rope": ("rope", "SWORD_KNIGHT", "Sword"),
    }[kind]
    end = "chest" if kind == "wheel" else "target"
    graph = TraversalGraph(
        (Node("source", 126), Node(end, 126)),
        (Route("source", end, capability, items=frozenset({"Route item"})),),
        (Placement("source", source),) if sources else (),
        (Position("source"),), frozenset({end}), access_region="Independent source",
    )
    row = {"id": "test-" + kind, "region": "Owner", "exit": "Exit", "graphs": {"local": {}}}
    target = SimpleNamespace(access_rule=lambda state: state.base_rule)
    dependencies = []
    world = SimpleNamespace(
        player=1, _enemy_copy_ability_policy=build_enemy_copy_ability_policy(random.Random(73), mode, True, True),
        options=SimpleNamespace(ability_randomization_statues=SimpleNamespace(value=False),
                                accessibility=Accessibility.from_any(accessibility)),
        _ability_gating_enabled=lambda: gating, _area_keys_enabled=lambda: False,
        multiworld=SimpleNamespace(
            get_entrance=lambda *_: target, get_region=lambda name, _: name,
            register_indirect_condition=lambda region, entrance: dependencies.append((region, entrance)),
        ),
    )
    if kind == "peg":
        monkeypatch.setattr(peg_traversal, "PEG_ROUTES", (row,))
        monkeypatch.setattr(peg_traversal, "peg_graph", lambda _: replace(graph, placements=(), access_region=None))
        monkeypatch.setattr(peg_traversal, "carry_graphs", lambda *_: (graph,))
        install = peg_traversal.install_peg_rules
    elif kind == "wheel":
        monkeypatch.setattr(wheel_traversal, "RACE", row)
        monkeypatch.setattr(wheel_traversal, "room_traversal_graph", lambda *_: graph)
        install = wheel_traversal.install_wheel_rules
    else:
        monkeypatch.setattr(traversal_rules, "extra_traversal_targets", lambda: (row,))
        monkeypatch.setattr(traversal_rules, "target_graphs", lambda *_: (graph,))
        install = traversal_rules.install_extra_traversal_rules
    items = {"Route item", ability + " Ability"}
    state = SimpleNamespace(base_rule=True, accessible=True, has=lambda name, _: name in items)
    state.can_reach_region = lambda *_: state.accessible
    return world, install, target, state, items, ability, dependencies


@pytest.mark.parametrize("kind", ["peg", "wheel", "fuse", "rope"])
@pytest.mark.parametrize("mode", [0, 1, 2])
@pytest.mark.parametrize("accessibility", ["full", "minimal"])
@pytest.mark.parametrize("gating", [False, True])
def test_absent_sources_reject_full_but_stay_closed_in_minimal(
    monkeypatch: pytest.MonkeyPatch, kind: str, mode: int, accessibility: str, gating: bool,
) -> None:
    world, install, target, state, _, _, dependencies = installer_setup(
        monkeypatch, kind, mode, accessibility, gating, sources=False,
    )
    if accessibility == "full":
        with pytest.raises(ValueError, match="No reviewed"):
            install(world)
    else:
        install(world)
        assert not target.access_rule(state)  # Owning all needed items is not equipment.
        assert dependencies == [("Independent source", target)]


@pytest.mark.parametrize("kind", ["peg", "wheel", "fuse", "rope"])
@pytest.mark.parametrize("accessibility", ["full", "minimal"])
def test_accessibility_never_relaxes_source_permission_dependencies_or_existing_rules(
    monkeypatch: pytest.MonkeyPatch, kind: str, accessibility: str,
) -> None:
    world, install, target, state, items, ability, _ = installer_setup(
        monkeypatch, kind, 0, accessibility, True, sources=True,
    )
    install(world)
    assert target.access_rule(state)
    for item in (ability + " Ability", "Route item"):
        items.remove(item)
        assert not target.access_rule(state)
        items.add(item)
    state.accessible = False
    assert not target.access_rule(state)
    state.accessible = True
    state.base_rule = False
    assert not target.access_rule(state)


@pytest.mark.parametrize("mode", [0, 1, 2])
def test_generate_early_preserves_already_feasible_policy_under_minimal(
    monkeypatch: pytest.MonkeyPatch, mode: int,
) -> None:
    import worlds.kirbyam as world_module

    original = build_enemy_copy_ability_policy
    drawn = []

    def build(*args: Any, **kwargs: Any) -> dict[str, Any]:
        candidate = original(*args, **kwargs)
        drawn.append(deepcopy(candidate))
        return candidate

    monkeypatch.setattr(world_module, "build_enemy_copy_ability_policy", build)
    world = make_world(  # type: ignore[no-untyped-call]
        mode, True, accessibility="minimal", ability_randomization_statues=False,
        ability_randomization_no_ability_weight=100,
    )
    assert drawn == [world._enemy_copy_ability_policy]
    if mode:
        state = world.multiworld.get_all_state(False)
        for name in world.item_name_to_id:
            if name != "Copy Ability Room Access":
                state.collect(world.create_item(name), prevent_sweep=True)
        assert not world.multiworld.get_entrance(wheel_traversal.RACE_ENTRANCE, 1).access_rule(state)
        peg = world.multiworld.get_location(data.locations["MINOR_CHEST_MOONLIGHT_MANSION_2_20"].label, 1)
        assert not peg.access_rule(state)


@pytest.mark.parametrize("accessibility", ["full", "minimal"])
def test_room_970_requires_independent_access_in_every_accessibility(accessibility: str) -> None:
    graph = wheel_traversal.wheel_graph(True)
    assert graph.unavailable_reason is None
    world = SimpleNamespace(player=1, options=SimpleNamespace(accessibility=Accessibility.from_any(accessibility)))
    state = SimpleNamespace(can_reach_region=lambda *_: False, has=lambda *_: True)
    assert not has_graph_access(world, state, graph)
    state.can_reach_region = lambda region, player: region == "REGION_COPY_ABILITY_ROOM/MAIN"
    assert has_graph_access(world, state, graph)
    assert not graph.evaluate(SourcePolicy({"mode": 0}), frozenset({"Wheel Ability"}), False,
                              allow_documented_retries=True).reaches("chest")


def replay_fuzz_case(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, case: int, *, companion: str | int | None = None,
) -> MultiWorld:
    """Use the unmodified artifact and the pinned fuzzer's normal generation entrypoints."""
    import Generate
    import Main
    import settings
    import Utils
    from BaseClasses import PlandoOptions

    seed, digest = FUZZ_CASES[case]
    fixture = FIXTURES / f"{case}-0.yaml"
    # Normalize only line endings for Git checkouts on Windows and Linux.
    assert sha256(fixture.read_bytes().replace(b"\r\n", b"\n")).hexdigest() == digest
    players = tmp_path / "players"
    players.mkdir()
    shutil.copy2(fixture, players / fixture.name)
    if companion == "default":
        (players / "companion.yaml").write_text(
            "name: Companion\ngame: Kirby & The Amazing Mirror\nKirby & The Amazing Mirror:\n"
            "  accessibility: full\n  ability_randomization_mode: off\n", encoding="utf-8",
        )
    elif companion is not None:
        shutil.copy2(FIXTURES / f"{companion}-0.yaml", players / f"{companion}-0.yaml")
    output = tmp_path / "output"
    output.mkdir()
    monkeypatch.setattr(settings, "no_gui", True)
    monkeypatch.setattr(settings, "skip_autosave", True)
    monkeypatch.setattr(Utils, "init_logging", lambda *args, **kwargs: None)
    args = Namespace(
        weights_file_path=settings.get_settings().generator.weights_file_path,
        sameoptions=False, player_files_path=str(players), seed=seed, multi=1 if companion is None else 2, spoiler=1,
        outputpath=str(output), allow_quantity=False, race=False, meta_file_path="meta-doesnt-exist.yaml",
        log_level="info", yaml_output=1,
        plando=PlandoOptions.items | PlandoOptions.connections | PlandoOptions.texts | PlandoOptions.bosses,
        skip_prog_balancing=False, skip_output=True, csv_output=False, log_time=False, spoiler_only=False,
    )
    generated_args, actual_seed = Generate.main(args)
    assert actual_seed == seed
    return cast(MultiWorld, Main.main(generated_args, actual_seed))


def replay_rejected_fuzz_case(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, case: int, *, companion: str | int | None = None,
) -> MultiWorld:
    """Retain source diagnostics on the final world, but never suppress rejection."""
    from .. import check_accessibility

    captured: list[MultiWorld] = []
    original = check_accessibility.validate_all_checks

    def validate(multiworld: MultiWorld, players: Iterable[int]) -> None:
        captured.append(multiworld)
        original(multiworld, players)

    monkeypatch.setattr(check_accessibility, "validate_all_checks", validate)
    with pytest.raises(check_accessibility.KirbyAmCheckAccessibilityError,
                       match="unreachable from placed progression") as error:
        replay_fuzz_case(
            monkeypatch, tmp_path, case, companion=companion,
        )
    assert "unavailable even with all inventory=[]" in str(error.value)
    assert not tuple((tmp_path / "output").glob("*.zip"))
    multiworld, = captured
    return multiworld


def test_exact_fuzz_69_minimal_rejects_stranded_fill_but_preserves_source_policy(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    from ..rules import _BOSS_DEFEAT_LOCATION_LABELS

    multiworld = replay_rejected_fuzz_case(monkeypatch, tmp_path, 69)
    world = cast(KirbyAmWorld, multiworld.worlds[1])
    assert world.options.accessibility.value == Accessibility.option_minimal
    assert multiworld.can_beat_game() and multiworld.fulfills_accessibility()
    assert world._enemy_copy_ability_policy["seed"] == 4994526115634732429
    assert world._enemy_copy_ability_policy["mode"] == 2
    assert world._enemy_copy_ability_policy["ability_randomization_no_ability_weight"] == 100
    assert not world.options.ability_randomization_statues.value
    state = multiworld.get_all_state(False)
    unreachable = {location.name for location in multiworld.get_locations() if not location.can_reach(state)}
    assert unreachable == set()
    assert all(state.can_reach_location(name, 1) for name in _BOSS_DEFEAT_LOCATION_LABELS)
    assert multiworld.get_entrance(wheel_traversal.RACE_ENTRANCE, 1).access_rule(state)
    assert multiworld.get_location("Moonlight Mansion 2-20 - Small Chest", 1).access_rule(state)
    assert has_graph_access(world, state, wheel_traversal.wheel_graph(True))
    # get_all_state collects both the item pool and filled-location sweep.
    while state.has("Copy Ability Room Access", world.player):
        state.remove(world.create_item("Copy Ability Room Access"))
    assert not multiworld.get_entrance(wheel_traversal.RACE_ENTRANCE, 1).access_rule(state)
    assert not multiworld.get_location("Moonlight Mansion 2-20 - Small Chest", 1).access_rule(state)


def test_exact_fuzz_95_full_generates_with_proved_copy_room_route(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    multiworld = replay_fuzz_case(monkeypatch, tmp_path, 95)
    world = multiworld.worlds[1]
    assert world.options.accessibility.value == Accessibility.option_full
    assert multiworld.can_beat_game() and multiworld.fulfills_accessibility()
    state = multiworld.get_all_state(False)
    assert all(location.can_reach(state) for location in multiworld.get_locations())
    assert has_graph_access(world, state, wheel_traversal.wheel_graph(True))
    # get_all_state collects both the item pool and filled-location sweep.
    while state.has("Copy Ability Room Access", world.player):
        state.remove(world.create_item("Copy Ability Room Access"))
    assert not multiworld.get_location("Moonlight Mansion 2-20 - Small Chest", 1).access_rule(state)


@pytest.mark.parametrize("companion", ["default", 95])
def test_mixed_accessibility_rejects_stranded_fill_and_keeps_copy_room_per_player(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, companion: str | int,
) -> None:
    multiworld = replay_rejected_fuzz_case(monkeypatch, tmp_path, 69, companion=companion)
    minimal, full = multiworld.worlds[1], multiworld.worlds[2]
    assert minimal.options.accessibility.value == Accessibility.option_minimal
    assert full.options.accessibility.value == Accessibility.option_full
    assert multiworld.can_beat_game() and multiworld.fulfills_accessibility()
    state = multiworld.get_all_state(False)
    assert all(location.can_reach(state) for location in multiworld.get_locations())
    while state.has("Copy Ability Room Access", minimal.player):
        state.remove(minimal.create_item("Copy Ability Room Access"))
    graph = wheel_traversal.wheel_graph(True)
    assert not has_graph_access(minimal, state, graph)
    assert has_graph_access(full, state, graph)
    assert not multiworld.get_entrance(wheel_traversal.RACE_ENTRANCE, 1).access_rule(state)
    assert multiworld.get_entrance(wheel_traversal.RACE_ENTRANCE, 2).access_rule(state)


def test_exact_ci_fuzz_1_rejects_only_actual_placement_strands(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    import json
    from .support.check_accessibility import audit_local_checks

    expected = json.loads((FIXTURES / "1-expected.json").read_text())
    multiworld = replay_rejected_fuzz_case(monkeypatch, tmp_path, 1)
    assert multiworld.worlds[1].options.accessibility.value == Accessibility.option_minimal
    assert multiworld.can_beat_game() and multiworld.fulfills_accessibility()
    audit = audit_local_checks(multiworld, 1)
    assert audit.unfilled == audit.inventory_unreachable == ()
    assert list(audit.progression_unreachable) == expected["stranded_checks"]
