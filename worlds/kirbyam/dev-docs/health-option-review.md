# Custom health option review

PR #934 is synchronized with main after #930. This review does **not** establish
that every supported option combination works. The health delta passes focused
checks, but the wider review reproduces inherited compatibility defects below.
No live emulator session, owner save, ROM or connector was changed by this review.

## Consolidated v0.4 candidate update

The findings below describe the earlier #934 review against its then-current
main baseline. The consolidated #931 candidate includes #940's full starting
history (`items_handling=0b111`), guarded Vitality authority reconciliation, and
native dead-HP preservation. Actual stock-server history tests now include
starting Vitality, and the compiled native grant preserves HP zero. These close
the specific source/protocol reproductions recorded for #943 and #944 within
the tested scope; they do not establish every DeathLink interleaving or native
save/load behavior. The room-sanity defect #945 remains unchanged. Issue state
and release acceptance are separate from this local integration evidence.

## Executable coverage

`test_health_option_matrix.py` covers:

- Every minimum/maximum pair in 1..10 crossed with all three One-Hit modes:
  300 inputs, 240 accepted and 60 rejected. Off accepts 40 pairs with minimum <=
  maximum <= minimum + 4. The two presets override the pair to 1/1 or 1/5.
- Every effective range crossed with both shard modes (0 and 2), no-extra-lives,
  start-with-all-maps and ability-gating toggles. For each combination it builds
  the pool with traps disabled, then with traps enabled at every percentage
  0..100: 65,280 pool builds. Disabled-trap percentages are factored out because
  that branch never reads the percentage. Assertions cover pool size, exact
  unique Vitality IDs, trap rounding, allowed filler/traps and health filters.
  These use the existing synthetic location fixture, not actual room traversal.
- 480 actual archive-generation attempts: all 40 health pairs crossed with 12
  mixed scenarios covering all three goals and ability-randomization modes,
  room sanity, DeathLink, maps, gating, trap and life settings, ability-source
  toggles, enemy health 50/100/500 and no-ability weight 0/50/100.
  240 room-sanity-off cases passed; all 240 room-sanity-on cases reproduced the
  same five inaccessible checks. Those precise failures are marked strict
  expected failures; an unexpected generation error still fails the test, and
  a repaired scenario becomes an unexpected pass requiring marker removal.

The existing health tests additionally generate archives for all 40 effective
ranges and both One-Hit overrides. Focused client tests cover guarded writes,
rejected snapshots, death values, legacy slot data and the main-branch counter
regressions. Independent review passed 481 focused tests and 40 lifecycle
sequence cases, one per effective range. Those sequences use mocked native RAM:
initial cap, damage, repeated polls, new-client reconnect, each allowed grant,
native file/respawn reconstruction and HP 0/-1/-128.

The health helper has no goal, region, ability, color or enemy-HP inputs. Those
options do not alter its numeric transformation. That factorization is not a
proof of native gameplay reachability or arbitrary common AP options. Common
`start_inventory`, item links, plando, arbitrary excluded locations and ability
customizations cannot be reduced to a claimed finite global Cartesian test.
The 12 mixed scenarios are examples, not pairwise-complete coverage.

## Blocking broader compatibility findings

1. **Room sanity ([#945](https://github.com/hasherwi/Archipelago-kirbyam/issues/945)):** split rooms 5-13, 6-05, 8-09 and 9-CHEST_2 attach their one
   room check to a canonical region while entrances target logical subregions.
   A separate archive generation on the unchanged main-equivalent tree
   reproduced the same five missing checks without custom health. Room 2-06
   has a different defect: its sole predecessor, 2-05_LOWER, has no
   incoming edge. All five checks fail the generator's accessibility check.
   A repair must preserve one check per physical room and must not join isolated
   compartments by adding traversable parent edges. The missing Moonlight
   entrance requires source evidence; this PR does not invent a route.
2. **Starting Vitality ([#943](https://github.com/hasherwi/Archipelago-kirbyam/issues/943)):** a real generated 3/5 seed with `start_inventory`
   containing `Carrot Castle - Vitality Counter: 1` correctly places item 3860018
   in precollected items. The current client requests `items_handling=0b011`;
   stock MultiServer Sync omits that starting item. This is an observed protocol
   defect, inherited from main, not merely an untested case. The precollect and
   history-migration work in #940 is relevant and must be integrated and checked
   before claiming compatibility with starting Vitality.
3. **DeathLink and native Vitality ([#944](https://github.com/hasherwi/Archipelago-kirbyam/issues/944)):** the watcher applies an incoming DeathLink
   (HP zero), then can offer a fresh Vitality. An independent host execution of
   the actual native grant/sync functions changes HP 0 to 7 and vitality 0 to 1.
   The custom 3/5 reconciler then clamps HP to 4; it cannot recover the lost death
   intent. Native engine timing and death-animation cancellation were not tested.
   The definite HP overwrite is inherited from main. Death-safe grant ordering
   needs its own regression and implementation review.

The reconciler's promise to preserve dead HP applies to that helper, not every
native item path. Native grants, respawn, HP-meter rendering, save/load and
DeathLink interleavings still need actual emulator acceptance. The ROM payload
and packaged base patch are unchanged by this PR.
