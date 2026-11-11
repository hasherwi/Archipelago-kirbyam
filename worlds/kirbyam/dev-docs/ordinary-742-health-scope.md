# Native742 health and enemy-durability evidence

The original clean-route record took damage. It is retained as historical
acceptance, not used to justify a low-health route. The replacement records
separate evidence levels rather than equate a Python generation pass with
native gameplay.

## No-loss native route

[Native no-loss acceptance](ordinary-742-no-loss-source-acceptance.json) contains
27 linked controller segments from actual712 entry, through741 main Flamer
acquisition and the first742 lower entry, to separate chest and Warp outcomes.
All26 post-entry segments were audited every frame:5,205 frames, minimum HP6,
zero HP decreases. This rules out a damage-and-healing event hidden between
sampled checkpoints. Source, attack and collision data were unchanged.

## One-HP source reasoning, not a direct one-HP replay

The supported health surface includes `minimum_health = maximum_health = 1`
and legacy One-Hit presets. The AP configuration and reconciliation code changes
HP, maximum HP and Vitality ownership, not movement, enemy AI, attack or room
collision parameters. Relevant implementation: `health.py:resolve_health_range`,
`health.py:reconcile_health`, payload `ap_initial_health_capacity`, and client
`_enforce_health_range` health reconciliation.

The pinned native
[`kirby.c`](https://github.com/jiangzhengwenjz/katam/blob/7d969fbce14fdc838d2c1ea01389717fb96c3189/src/kirby.c)
has two explicit `hp == 1` branches. `sub_0803FBB4` (lines6794-6803) plays the
low-health sound and sets/clears its flag. `sub_08065A0C` (lines19519-19549) changes
Fighter's charged projectile; that state is reached through the ability dispatch
index20, not Normal or Burning. The accepted route uses only Normal and Burning.
Burning dispatch index3 and `sub_0805DBA4`, `sub_0805DC70`, `sub_0805DE18` use
fixed speed/timing and no HP predicate. Native `object.c` acquisition has no
Normal/Burning HP-dependent grant branch.

This bounded source review plus the continuous zero-loss route supports the
same movement at any positive Kirby HP. It does **not** claim an AP-patched
one-HP controller replay, all other abilities, all hazards or arbitrary native
multiplayer timing. No healing, damage boost or hit invulnerability is required.

## Maximum supported enemy durability

A Waddle Doo has native4HP; the supported500% setting raises this to20. Replaying
the original post-F5 wait with only DooHP changed failed: the surviving roof
Doo damaged Kirby. That failure was not treated as proof the route is impossible.

[The full500% acceptance](ordinary-742-all500-acceptance.json) instead applies the
**production** `scale_enemy_health_tables` once to a cold-boot native fixture.
It scales all regular enemies, minibosses, bosses and meter coefficients, not
just Waddle Doo. The exact module blob is pinned in the record and matched by a
regression test. Startup placement and this HP transformation are the only ROM
changes; no terrain, attack, source mapping or runtime writes are introduced.

The successful variant uses prompt movement/repeated Burning and avoids the
surviving roof enemy for Warp. For the chest, it deliberately drops Burning
**after** the last metal action and uses Normal inhale/spit to remove the roof
and chest-platform Doos without assuming a damage-based kill. All30 post-entry
segments have minimum HP6 and zero HP decreases across5,463 audited frames.
The chest flag changes0 to2, ending Normal; the separate Warp branch reaches705
with Burning. Enemy HP does not add a static gate to the Normal inhalation and
avoidance mechanisms; no route predicate assumes an enemy dies to one Burning hit.

These are native fixtures with the same production HP transform, not full AP
patch/server or direct one-HP acceptance. The endpoint durability cases are not
an exhaustive replay of every percentage, source assignment or controller timing.

## Both targets with one finite source

[The same-visit continuation](ordinary-742-all500-combined-checks.json) resumes
the collected chest's actual500% checkpoint as Normal, ascends to the roof,
handles a Doo that reappears when the camera returns, avoids native spike26,4,
and enters705 as Normal with the chest flag still set. All eight segments have
minimum HP6 and zero decreases across1,058 audited frames. There is no room
reset, reentry or ability reacquisition. This proves both outcomes can be
completed together, rather than merely unioning mutually exclusive plans.

The production target graphs keep their separate terminal outcomes. The
durable-enemy chest sequence can end Normal; its abstract result is not a
Burning-equipped postcondition. Regression tests prohibit outgoing endpoint
edges. Any later carry extension needs its own actual equipment/geometry proof.
