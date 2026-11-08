#!/usr/bin/env python3
"""Paired source-expansion benchmark; imports and compilation are not timed.

Run from the repository with its test Python environment. Prints JSON. The
reference is the frozen 181c6e9 evaluator; this proves no native gameplay route.
"""

from __future__ import annotations

import argparse
from collections import deque
import json
import os
from pathlib import Path
import statistics
import sys
import time
from typing import Any, Callable


def timings(operation: Callable[[], Any], number: int) -> float:
    start = time.perf_counter_ns()
    for _ in range(number):
        operation()
    return (time.perf_counter_ns() - start) / number / 1_000_000


def queue_counts(module: Any, operation: Callable[[], Any]) -> dict[str, int]:
    counts = {"pops": 0, "appends": 0}

    class CountedDeque(deque[Any]):
        def append(self, value: Any) -> None:
            counts["appends"] += 1
            super().append(value)

        def popleft(self) -> Any:
            counts["pops"] += 1
            return super().popleft()

    original = module.deque
    module.deque = CountedDeque
    try:
        operation()
    finally:
        module.deque = original
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--number", type=int, default=50)
    parser.add_argument("--samples", type=int, default=7)
    args = parser.parse_args()
    if args.number < 1 or args.samples < 1:
        parser.error("number and samples must be positive")
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    os.environ["AP_TEST_WORLDS"] = "kirbyam"
    import pytest  # noqa: F401 - activate supported scoped world imports
    from worlds.kirbyam import traversal as current
    from worlds.kirbyam.enemy_ability_data import ABILITY_NAME_TO_ID
    from worlds.kirbyam.test import traversal_reference as reference
    from worlds.kirbyam.test.test_traversal import policy
    from worlds.kirbyam.traversal_data import graph_items, room_traversal_graph

    permissions = frozenset(f"{name} Ability" for name in ABILITY_NAME_TO_ID)
    cases = (
        ("707_native", "metal_707_to_712", "central_statues", 0, False),
        ("707_live_finite", "metal_707_to_712", "central_statues", 2, False),
        ("707_live_retries", "metal_707_to_712", "central_statues", 2, True),
        ("216_native", "metal_216_chest", "central_statues", 0, False),
        ("216_live_finite", "metal_216_chest", "central_statues", 2, False),
        ("216_live_retries", "metal_216_chest", "central_statues", 2, True),
        ("742_native", "metal_742_sparerib", "clean_carry", 0, False),
        ("557_native", "metal_557_goal1_tomato", "local", 0, False),
        ("peg605_native", "peg_605_12_24", "carry", 0, False),
        ("mini134_native", "mini_134_ocean_spray", "local", 0, False),
    )
    result: dict[str, Any] = {
        "python": sys.version.split()[0], "reference": "181c6e9faeb97040723d0786d4b6f1fc31156441",
        "scope": "Paired full-result evaluations; same graph, policy and owned items; compilation/imports excluded",
        "samples": args.samples, "evaluations_per_sample": args.number, "cases": {},
    }
    for name, target, witness, mode, retries in cases:
        graph = room_traversal_graph(target, witness, True)
        resolver = policy(mode, statues=True)  # type: ignore[no-untyped-call]
        owned = graph_items(graph) | permissions

        def operation(module: Any) -> Any:
            return module.reachable_positions(graph.nodes, graph.routes, graph.placements, graph.starts,
                                              resolver, owned, True, retries)

        def before() -> Any:
            return operation(reference)

        def after() -> Any:
            return operation(current)
        expected, actual = before(), after()
        assert actual == expected
        for _ in range(3):
            before()
            after()
        old_samples: list[float] = []
        new_samples: list[float] = []
        for sample in range(args.samples):
            pair = ((before, old_samples), (after, new_samples))
            for run, measurements in pair if sample % 2 == 0 else reversed(pair):
                measurements.append(timings(run, args.number))
        result["cases"][name] = {
            "target": target, "witness": witness, "nodes": len(graph.nodes), "routes": len(graph.routes),
            "sources": len(graph.placements), "positions": len(actual.positions),
            "retry_assumptions": len(actual.retry_assumptions),
            "reference_queue": queue_counts(reference, before), "optimized_queue": queue_counts(current, after),
            "reference_samples_ms": old_samples, "optimized_samples_ms": new_samples,
            "reference_median_ms": statistics.median(old_samples),
            "optimized_median_ms": statistics.median(new_samples),
        }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
