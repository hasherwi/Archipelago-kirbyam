"""Explicit Completely Random room patch; historical slots keep native timing."""
from functools import lru_cache
from .data import load_json_data
from .traversal import SourcePolicy, compile_traversal_graph

TARGET = "switch_533_room16"
POLICY_KEY = "room16_switch_timer_frames"
TIMER_FRAMES = 600
ROM_OFFSET = 0x008C2708  # native533 switch0x088C26F0, template+0x18


def configure_policy(raw: dict) -> dict:
    if raw.get("mode") == 2:
        return {**raw, POLICY_KEY: TIMER_FRAMES}
    return raw


def enabled(policy: SourcePolicy) -> bool:
    return (policy.mode == 2 and type(policy.policy.get(POLICY_KEY)) is int
            and policy.policy[POLICY_KEY] == TIMER_FRAMES)


def timer_bytes(raw: dict) -> bytes:
    policy = SourcePolicy(raw)
    if POLICY_KEY in raw and not enabled(policy):
        raise ValueError("Invalid Room16 switch timer patch contract")
    return (TIMER_FRAMES if enabled(policy) else 0).to_bytes(2, "little")


@lru_cache(maxsize=1)
def graph():
    return compile_traversal_graph(load_json_data("room16_normal_timer_witness.json"))


def target_graphs(row: dict, policy: SourcePolicy) -> tuple:
    if row.get("id") == TARGET and enabled(policy):
        return (graph(),)
    return ()
