#!/usr/bin/env python3
"""Exercise a hypothetical 742 state-expanded design against the existing kernel.

The movement edges below are ASSUMPTIONS FOR A LOGIC TEST, not native acceptance.
No graph is serialized as reviewed and no production catalog is modified.
Requires the repository's installed Python dependencies. --repo selects it.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import importlib
import os
from pathlib import Path
import random
import sys
from unittest.mock import patch


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    args = parser.parse_args()
    os.environ.setdefault("AP_TEST_WORLDS", "kirbyam")
    sys.path.insert(0, str(args.repo))
    importlib.import_module("pytest")  # Activate the repository's scoped test-world imports.
    from worlds.kirbyam import traversal as t
    from worlds.kirbyam.ability_randomization import build_enemy_copy_ability_policy
    from worlds.kirbyam.enemy_ability_data import GATEABLE_ENEMY_COPY_ABILITIES, VALID_ENEMY_COPY_ABILITIES
    from worlds.kirbyam.traversal_rules import target_applies

    def policy(mode: int = 0, *, pool: list[str] | None = None, weight: int = 0) -> t.SourcePolicy:
        raw = build_enemy_copy_ability_policy(
            random.Random(427), mode, True, True, True,
            whitelist=VALID_ENEMY_COPY_ABILITIES if pool is None else pool,
            include_passive_enemies=True, no_ability_weight=weight,
        )
        return t.SourcePolicy(raw)

    node_rooms = {
        "741_main_source": 741,
        "742_clean_lower": 742,
        "742_clean_roof": 742,
        "742_clean_tower": 742,
        "742_clean_chest": 742,
        "742_warp": 742,
        "742_outer_changed": 742,
        "742_inner_door_revealed": 742,
        "741_upper_return_source": 741,
        "742_return_roof_unknown": 742,
        "742_return_tower_unknown": 742,
    }
    nodes = tuple(t.Node(key, room) for key, room in node_rooms.items())
    routes = (
        t.Route("741_main_source", "742_clean_lower", room_transition=True),
        t.Route("742_clean_lower", "742_clean_roof"),
        t.Route("742_clean_roof", "742_clean_tower", capability="metal", allowed_abilities=frozenset({"Burning"})),
        t.Route("742_clean_tower", "742_clean_chest"),
        t.Route("742_clean_tower", "742_warp"),
        # Outer and inner Bomb actions are separate directed phase changes.
        t.Route("742_clean_roof", "742_outer_changed"),
        t.Route("742_outer_changed", "742_inner_door_revealed"),
        t.Route("742_inner_door_revealed", "741_upper_return_source", room_transition=True),
        # Unknown room lifetime does not take this return to a clean node.
        t.Route("741_upper_return_source", "742_return_roof_unknown", room_transition=True),
        t.Route(
            "742_return_roof_unknown", "742_return_tower_unknown",
            capability="metal", allowed_abilities=frozenset({"Burning"}),
        ),
        t.Route("742_return_tower_unknown", "742_warp"),
    )
    placements = (
        t.Placement("741_main_source", "FLAMER", identity="0x088BD8AC"),
        t.Placement("741_upper_return_source", "FLAMER", identity="0x088BDA38"),
    )
    check_count = 0
    gateable = tuple(set(GATEABLE_ENEMY_COPY_ABILITIES) | {"Burning"})
    with patch.object(t, "GATEABLE_ENEMY_COPY_ABILITIES", gateable):
        def run(
            start: str = "741_main_source", *, source_policy: t.SourcePolicy | None = None,
            owned: frozenset[str] = frozenset({"Burning Ability"}),
            sources: tuple[t.Placement, ...] = placements, edges: tuple[t.Route, ...] = routes,
            equipped: str = "Normal", consumed: frozenset[str] = frozenset(),
        ) -> t.TraversalResult:
            return t.reachable_positions(
                nodes, edges, sources, [t.Position(start, equipped, consumed=consumed)],
                source_policy or policy(), owned, True,
            )

        def check(value: bool, description: str) -> None:
            nonlocal check_count
            if not value:
                raise AssertionError(description)
            check_count += 1

        clean = run()
        check(
            clean.reaches("742_clean_chest") and clean.reaches("742_warp"),
            "Hypothetical clean path must reach both distinct targets",
        )
        dirty = run("741_upper_return_source")
        check(dirty.reaches("742_warp"), "Hypothetical dirty return still has the Warp route")
        check(not dirty.reaches("742_clean_chest"), "Dirty return must not acquire the clean chest route")
        check(
            not any(position.node.startswith("742_clean_") for position in dirty.positions),
            "Dirty states must never rejoin clean states",
        )
        check(not run("742_outer_changed").reaches("742_clean_chest"), "Outer Bomb cannot return to clean chest")
        check(not run(sources=()).reaches("742_clean_chest"), "Permission alone cannot equip Burning")
        check(not run(owned=frozenset()).reaches("742_clean_chest"), "Burning permission is required at acquisition")
        wrong_source = (replace(placements[0], node="742_clean_chest"),)
        check(not run(sources=wrong_source).reaches("742_clean_chest"), "A source cannot bootstrap its own gate")
        spent = frozenset({"0x088BD8AC"})
        check(
            not run(sources=placements[:1], consumed=spent).reaches("742_clean_chest"),
            "A consumed finite Flamer is not renewable",
        )
        for lifetime in [None, "preserve", "reset"]:
            changed = tuple(
                replace(route, preserves_room_instance=lifetime == "preserve", resets_room_instance=lifetime == "reset")
                if route.source == "741_upper_return_source" else route for route in routes
            )
            check(
                not run("741_upper_return_source", edges=changed).reaches("742_clean_chest"),
                "Kernel instance flags must not silently create a phase edge to clean chest",
            )
        condition = {"requires_guaranteed_source": {"source_key": "FLAMER", "ability": "Burning"}}
        cases: list[tuple[int, list[str] | None, int, bool]] = [
            (0, None, 0, True), (1, ["Burning"], 0, True), (1, ["Hammer"], 0, False),
            (2, ["Burning"], 0, True), (2, ["Burning", "Hammer"], 0, False),
            (2, ["Burning"], 50, False), (2, ["Burning"], 100, False),
        ]
        full_permissions = frozenset(f"{name} Ability" for name in gateable)
        for mode, pool, weight, applies in cases:
            resolver = policy(mode, pool=pool, weight=weight)
            check(target_applies(condition, resolver) is applies, "Conditional policy applicability mismatch")
            result = run(source_policy=resolver, owned=full_permissions)
            check(result.reaches("742_clean_chest") is applies, "Finite source outcome guarantee mismatch")
        for ability in t.METAL_BREAKING_ABILITIES:
            isolated = run("742_clean_roof", sources=(), equipped=ability)
            check(
                isolated.reaches("742_clean_chest") is (ability == "Burning"),
                "Unaccepted provider entered the narrow draft move",
            )
        # AP monotonic union is valid: the clean witness is an alternative plan,
        # not a mutation reversal in the dirty witness.
        check(
            clean.reaches("742_clean_chest") or dirty.reaches("742_clean_chest"),
            "Union of alternatives lost a valid clean plan",
        )
        print(
            f"PASS: {check_count} design-semantic assertions; "
            f"clean states={len(clean.positions)}, dirty states={len(dirty.positions)}"
        )
        print(
            "Movement, capture, Bomb timing, metal contact, chest collection "
            "and native room reset behavior were NOT tested."
        )


if __name__ == "__main__":
    main()
