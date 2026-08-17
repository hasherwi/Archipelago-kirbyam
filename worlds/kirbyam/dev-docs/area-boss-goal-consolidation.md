# Area-boss goal consolidation (Issue #872)

## Canonical option model

KirbyAM now exposes three canonical goal values:

- `dark_mind` (`0`)
- `defeat_any_area_boss` (`1`)
- `defeat_area_boss` (`2`)

`defeat_configured_area_boss` is retained as a safe YAML alias for value `2` because its semantics are unchanged. The former `defeat_random_hidden_area_boss` YAML value is intentionally removed rather than aliased: silently mapping it to value `2` would select the default configured boss instead of preserving the old random-target semantics. Its explicit replacement is:

```yaml
goal: defeat_area_boss
configured_area_boss: random
```

The BizHawk client still understands legacy generated slot data with goal value `3` and `goal_hidden_area_boss_key`, so already-generated worlds remain finishable.

## Random selection contract

Both `configured_area_boss` and `starting_kirby_color` use Archipelago's built-in `Choice.from_text("random")` behavior. `Choice` reserves the literal `random`, so KirbyAM must not add a custom `option_random`, `alias_random`, or sentinel ID. The framework resolves `random` to a concrete choice before world generation; slot data and ROM configuration therefore contain only concrete values.

Generated weighted YAML templates enumerate only concrete `Choice` members, so the literal `random` will not appear as a weight-map key. The option docstrings intentionally include the scalar examples `configured_area_boss: random` and `starting_kirby_color: random`, and explain that users should replace the whole generated mapping with the scalar shorthand. Tests protect those comments so the framework feature stays discoverable.

## Area-boss mapping

The option values are intentionally independent of area/location numbering. Keep this explicit mapping synchronized with the actual game layout:

| Configured boss | Area | Boss-defeat key |
|---|---|---|
| King Golem | Moonlight Mansion | `BOSS_DEFEAT_2` |
| Moley | Cabbage Cavern | `BOSS_DEFEAT_6` |
| Kracko | Mustard Mountain | `BOSS_DEFEAT_1` |
| Mega Titan | Carrot Castle | `BOSS_DEFEAT_7` |
| Gobbler | Olive Ocean | `BOSS_DEFEAT_4` |
| Wiz | Peppermint Palace | `BOSS_DEFEAT_5` |
| Dark Meta Knight | Radish Ruins | `BOSS_DEFEAT_8` |
| Master Hand + Crazy Hand | Candy Constellation | `BOSS_DEFEAT_3` |

## Goal event model

Current generated worlds materialize these goal events:

- `GOAL_DARK_MIND`
- `GOAL_ANY_AREA_BOSS`
- `GOAL_CONFIGURED_AREA_BOSS` (player-facing label: `Defeat Area Boss`)

The legacy `GOAL_HIDDEN_AREA_BOSS` data record is retained only so a new client can understand old generated worlds; it is not materialized in the current Rainbow Route region and is omitted from new tracker-facing slot-data location metadata.

All current completion conditions consistently require the corresponding locked goal event item. Goal-event access rules determine when that event becomes reachable:

- Dark Mind requires all Mirror Shards plus the Dimension Mirror Dark Meta Knight event.
- Any Area Boss becomes reachable when any of the eight boss-defeat locations is reachable.
- Area Boss becomes reachable only when the configured target boss-defeat location is reachable.

The client independently reports runtime completion from acknowledged boss-defeat checks, using `goal_configured_area_boss_key` for the canonical area-boss goal. The historical field name is kept to avoid unnecessary slot-data churn.
