"""Audit all local checks without treating inventory feasibility as a valid fill.

This is test support, not an enabled generation guard. Removing the remaining
starting permissions still requires native room/source coverage.
"""

from __future__ import annotations

from dataclasses import dataclass

from BaseClasses import CollectionState, MultiWorld


@dataclass(frozen=True)
class LocalCheckAudit:
    inventory_unreachable: tuple[str, ...]
    progression_unreachable: tuple[str, ...]
    unfilled: tuple[str, ...]


def audit_local_checks(multiworld: MultiWorld, player: int) -> LocalCheckAudit:
    """Compare theoretical inventory with the actual reachable progression sweep.

    Never collect the item pool into ``progression``: it may contain the very
    permission locked behind its own location. Sweep the entire multiworld so
    genuinely reachable deliveries from other players are credited. The normal
    collection implementation remains authoritative; useful items must not be
    promoted to logical permissions by the test itself.
    """
    checks = tuple(location for location in multiworld.get_locations(player) if location.address is not None)
    inventory = multiworld.get_all_state()
    progression = CollectionState(multiworld)
    progression.sweep_for_advancements()
    return LocalCheckAudit(
        tuple(sorted(location.name for location in checks if not location.can_reach(inventory))),
        tuple(sorted(location.name for location in checks if not location.can_reach(progression))),
        tuple(sorted(location.name for location in checks if location.item is None)),
    )
