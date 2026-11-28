"""Explicit Completely Random room patch; historical slots keep native timing."""
from . import conditional_routes
from .traversal import SourcePolicy

CONTRACT = "mustard_room_4_16_timer"
_TARGET, _AUTHORED = conditional_routes.contract(CONTRACT)
TARGET = _TARGET["id"]
POLICY_KEY = "room16_switch_timer_frames"
TIMER_FRAMES = _AUTHORED["activation"]["source_policy_values"][POLICY_KEY]
ROM_OFFSET = 0x008C2708  # native533 switch0x088C26F0, template+0x18


def configure_policy(raw: dict) -> dict:
    return conditional_routes.policy_with_contract(CONTRACT, raw, runtime_key=POLICY_KEY)


def enabled(policy: SourcePolicy) -> bool:
    return conditional_routes.policy_has_contract(CONTRACT, policy)


def timer_bytes(raw: dict) -> bytes:
    policy = SourcePolicy(raw)
    if POLICY_KEY in raw and not enabled(policy):
        raise ValueError("Invalid Room16 switch timer patch contract")
    return (TIMER_FRAMES if enabled(policy) else 0).to_bytes(2, "little")


def graph():
    return conditional_routes.graph(CONTRACT)


def target_graphs(row: dict, policy: SourcePolicy) -> tuple:
    return conditional_routes.active_graphs(row, frozenset({CONTRACT}) if enabled(policy) else frozenset(), policy)
