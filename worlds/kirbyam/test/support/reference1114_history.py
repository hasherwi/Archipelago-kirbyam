"""Reverse only reviewed phase-cache, finite-grant, encounter and destination-reset extensions.

The remaining search bytes retain the pre-1114 hash; source expansion stays
unoptimized. Exact replacements also reject mutations inside these extensions.
"""

REVIEWED_TRANSFERS = (
    (
        """            if route.loses_equipment:
                ability = "Normal"
            expired = position.expired.union(route.ends_lifetimes).difference(route.revives_lifetimes)
            active = set(position.active)
            crosses_room = route.room_transition or node_by_key[position.node].room != node_by_key[route.target].room
            if crosses_room and (not route.preserves_room_instance or route.resets_room_instance):
                active.clear()
            active.difference_update(route.ends_lifetimes, route.revives_lifetimes)
            active.update(lifetime for lifetime in route.activates_lifetimes if lifetime not in expired)
            queue.append(Position(route.target, ability, opened, consumed, expired, frozenset(active)))""",
        """            queue.append(Position(route.target, ability, opened, consumed))""",
    ),
    (
        """                        or not objects[route.uses_object][0].requirements <= owned
                        or (objects[route.uses_object][0].lifetime is not None
                            and objects[route.uses_object][0].lifetime not in position.active)):""",
        """                        or not objects[route.uses_object][0].requirements <= owned):""",
    ),
    (
        """queue.append(Position(position.node, grant.abilities, position.opened, consumed,
                                      position.expired, position.active))""",
        """queue.append(Position(position.node, grant.abilities, position.opened, consumed))""",
    ),
    (
        """queue.append(Position(position.node, granted_ability, position.opened, consumed,
                                      position.expired, position.active))""",
        """queue.append(Position(position.node, granted_ability, position.opened, consumed))""",
    ),
    (
        """            grant = source_grant(source.source_key, source.native_grants)
            unrestricted = (policy.grant(source.source_key, lambda _: True, source.native_grants)
                            if source.native_grants else policy.grant(source.source_key, lambda _: True))
            if source.source_choices:
                grant = policy.grant_choice(source.source_choices, permitted)
                unrestricted = policy.grant_choice(source.source_choices, lambda _: True)""",
        """            grant = source_grant(source.source_key, source.native_grants)
            unrestricted = (policy.grant(source.source_key, lambda _: True, source.native_grants)
                            if source.native_grants else policy.grant(source.source_key, lambda _: True))""",
    ),
    (
        """            if not source.requirements <= owned:
                continue
            if source.lifetime is not None and source.lifetime not in position.active:
                continue
            identity""",
        """            if not source.requirements <= owned:
                continue
            identity""",
    ),
    (
        """queue.append(Position(position.node, "Normal", position.opened, position.consumed,
                                      position.expired, position.active))""",
        """queue.append(Position(position.node, "Normal", position.opened, position.consumed))""",
    ),

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
