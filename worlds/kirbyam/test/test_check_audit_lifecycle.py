"""Exercise the real Main lifecycle, including the skip-output fuzzer path."""

from pathlib import Path
from collections.abc import Iterable

import pytest
from BaseClasses import MultiWorld

from .. import KirbyAmWorld, check_accessibility
from .test_cutter_progression import _generate
from .test_traversal_accessibility import replay_fuzz_case


@pytest.mark.parametrize("skip_output", [False, True])
def test_audit_runs_once_after_balance_and_every_finalizer(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, skip_output: bool,
) -> None:
    import Main

    events: list[tuple[str, int | None]] = []
    from Fill import balance_multiworld_progression as original_balance
    original_validate = check_accessibility.validate_all_checks

    def balance(multiworld: MultiWorld) -> None:
        original_balance(multiworld)
        events.append(("balance", None))

    def finalize(world: KirbyAmWorld) -> None:
        events.append(("finalize", world.player))

    def validate(multiworld: MultiWorld, players: Iterable[int]) -> None:
        assert events == [("balance", None), ("finalize", 1), ("finalize", 2)]
        assert set(players) == {1, 2}
        original_validate(multiworld, (1, 2))
        events.append(("audit", None))

    monkeypatch.setattr(Main, "balance_multiworld_progression", balance)
    monkeypatch.setattr(KirbyAmWorld, "finalize_multiworld", finalize)
    monkeypatch.setattr(check_accessibility, "validate_all_checks", validate)
    if skip_output:
        replay_fuzz_case(monkeypatch, tmp_path, 95, companion="default")
        assert not tuple((tmp_path / "output").glob("*.zip"))
    else:
        _generate(  # type: ignore[no-untyped-call]
            monkeypatch, tmp_path, 105100, [{"accessibility": "full"}, {"accessibility": "full"}],
        )
        assert len(tuple((tmp_path / "output").glob("*.zip"))) == 1
    assert events[-1] == ("audit", None)


@pytest.mark.parametrize("accessibility", ["full", "minimal"])
@pytest.mark.parametrize("mode", [0, 1, 2])
def test_generation_requests_all_source_witnesses_without_changing_accessibility(
    monkeypatch: pytest.MonkeyPatch, accessibility: str, mode: int,
) -> None:
    import worlds.kirbyam as kirby
    from .test_mini_traversal import make_world

    from ..peg_traversal import validate_peg_assignment as original
    requested: list[bool] = []

    def validate(*args: object, **kwargs: object) -> object:
        requested.append(kwargs.get("require_all_witnesses") is True)
        return original(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(kirby, "validate_peg_assignment", validate)
    world = make_world(mode, True, accessibility=accessibility)  # type: ignore[no-untyped-call]
    assert requested == [True]
    assert world.options.accessibility.current_key == accessibility
