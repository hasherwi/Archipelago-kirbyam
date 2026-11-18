"""Reverse only reviewed phase-cache, finite-grant and destination-reset extensions.

The remaining search bytes retain the pre-1114 hash; source expansion stays
unoptimized. Exact replacements also reject mutations inside these extensions.
"""

REVIEWED_TRANSFERS = (
    (
        """            unrestricted = (policy.grant(source.source_key, lambda _: True, source.native_grants)
                            if source.native_grants else policy.grant(source.source_key, lambda _: True))
            bounded = not unrestricted.can_fail and unrestricted.abilities == grant.abilities
            abilities = grant.guaranteed if bounded else frozenset()
""",
        """            abilities = grant.guaranteed
""",
    ),
    ("            if bounded and not grant.can_fail and grant.abilities and not abilities:\n",
     "            if not grant.can_fail and grant.abilities and not abilities:\n"),
    (
        """    grants: dict[tuple[str, tuple[str, ...]], Grant] = {}

    def permitted(ability: str) -> bool:
        return ability_permission(ability, owned, gating)

    def source_grant(key: str, native_grants: tuple[str, ...]) -> Grant:
        # Grants describe deterministic possibilities, not individual RNG draws.
        # Policy, owned permissions and gating are fixed for this evaluation.
        cache_key = (key, native_grants)
        if cache_key not in grants:
            grants[cache_key] = (policy.grant(key, permitted, native_grants) if native_grants
                                 else policy.grant(key, permitted))
        return grants[cache_key]

""",
        """    grants: dict[str, Grant] = {}

    def permitted(ability: str) -> bool:
        return ability_permission(ability, owned, gating)

    def source_grant(key: str) -> Grant:
        # Grants describe deterministic possibilities, not individual RNG draws.
        # Policy, owned permissions and gating are fixed for this evaluation.
        if key not in grants:
            grants[key] = policy.grant(key, permitted)
        return grants[key]

""",
    ),
    (
        """            grant = source_grant(source.source_key, source.native_grants)
""",
        """            grant = source_grant(source.source_key)
""",
    ),
    (
        """                if route.resets_room_instance:
                    # Recreate only aliases in the destination's resettable bank.
                    # Unknown, remote and persistent identities remain spent.
                    resettable = set()
                    for identity, aliases in objects.items():
                        if all(node_by_key[source.node].room == node_by_key[route.target].room
                               and source.room_reset_respawns
                               and (source.lifetime is None or source.lifetime in route.revives_lifetimes)
                               for source in aliases):
                            resettable.add(identity)
                    consumed = consumed - resettable
""",
        """                if route.resets_room_instance:
                    consumed = frozenset()
""",
    ),
)


def before_1114_reference_transfers(tail: bytes) -> bytes:
    for current, historical in REVIEWED_TRANSFERS:
        current_bytes = current.encode()
        assert tail.count(current_bytes) == 1, "Reviewed reference transfer changed"
        tail = tail.replace(current_bytes, historical.encode(), 1)
    return tail
