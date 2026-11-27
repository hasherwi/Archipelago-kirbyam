"""Explicit Completely Random room patch; historical slots keep native timing."""
from functools import lru_cache
from .data import load_json_data
from .special_route_data import SPECIAL_ROUTE_PROFILES
from .traversal import SourcePolicy, compile_traversal_graph

_PROFILE = SPECIAL_ROUTE_PROFILES["mustard_room_4_16_timer"]
TARGET = _PROFILE["target"]
POLICY_KEY = "room16_switch_timer_frames"
TIMER_FRAMES = _PROFILE["switch_timer_frames"]
ROM_OFFSET = 0x008C2708  # native533 switch0x088C26F0, template+0x18


def configure_policy(raw: dict) -> dict:
    if raw.get("mode") == _PROFILE["ability_randomization_mode"]:
        return {**raw, POLICY_KEY: TIMER_FRAMES}
    return raw


def enabled(policy: SourcePolicy) -> bool:
    return (policy.mode == _PROFILE["ability_randomization_mode"] and type(policy.policy.get(POLICY_KEY)) is int
            and policy.policy[POLICY_KEY] == TIMER_FRAMES)


def timer_bytes(raw: dict) -> bytes:
    policy = SourcePolicy(raw)
    if POLICY_KEY in raw and not enabled(policy):
        raise ValueError("Invalid Room16 switch timer patch contract")
    return (TIMER_FRAMES if enabled(policy) else 0).to_bytes(2, "little")


@lru_cache(maxsize=1)
def graph():
    return compile_traversal_graph(load_json_data(_PROFILE["normal_witness"]))


def target_graphs(row: dict, policy: SourcePolicy) -> tuple:
    if row.get("id") == TARGET and enabled(policy):
        return (graph(),)
    return ()
