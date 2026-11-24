# Kirby color palettes

See the colors you can use now and the palettes under consideration for a future release. Each row shows a palette as a strip of color swatches. These are previews, not gameplay screenshots; abilities and effects can change how some colors appear in-game.

## Available now

Pick any of these **27 colors** with `starting_kirby_color` in your Kirby YAML. For example:

```yaml
Kirby & The Amazing Mirror:
  starting_kirby_color: cotton_candy
```

**Pink** is the in-game default. Use `random` to pick a color when the seed is generated, or `random_color_per_room` to change color between rooms with the connected BizHawk client. These are modes, not separate palettes.

### Original colors

![Swatches for the 14 original palettes, from Pink to Chalk. The YAML keys are listed below.](color-palettes-native.svg)

### Additional starting colors

![Swatches for the 13 additional selectable palettes, from Shadow to Mint Chip. The YAML keys are listed below.](color-palettes-curated.svg)

<details>
<summary>All 27 color names and YAML values</summary>

| Color | YAML value |
| --- | --- |
| Pink | `pink` |
| Yellow | `yellow` |
| Red | `red` |
| Green | `green` |
| Snow | `snow` |
| Carbon | `carbon` |
| Ocean | `ocean` |
| Sapphire | `sapphire` |
| Grape | `grape` |
| Emerald | `emerald` |
| Orange | `orange` |
| Chocolate | `chocolate` |
| Cherry | `cherry` |
| Chalk | `chalk` |
| Shadow | `shadow` |
| Ivory | `ivory` |
| Citrus | `citrus` |
| White | `white` |
| Lavender | `lavender` |
| Rainbow | `rainbow` |
| Candy Corn | `candy_corn` |
| Negative | `negative` |
| Pineapple | `pineapple` |
| Cotton Candy | `cotton_candy` |
| Royal | `royal` |
| Pumpkin | `pumpkin` |
| Mint Chip | `mint_chip` |

</details>

## Proposed colors

These **41 reference palettes** are not in the game and cannot be selected in YAML. Names and colors may change before implementation.

![Swatches for the first 21 proposals, Rose through Samus. The names are listed below.](color-palettes-proposals-1.svg)

![Swatches for the remaining 20 proposals, Marx through Invincible. The names are listed below.](color-palettes-proposals-2.svg)

<details>
<summary>All 41 proposed color names</summary>

- Rose
- Daisy
- Lemon
- Beautiful Sunset
- Carrot Cake
- Snow Cone
- Strawberry Peach
- Halloween
- Ramia’s Scale & Star Stone
- Meconopsis / Blue Poppy
- Superstar Ice
- KDL3 Pink
- Advance Ice
- Advance Stone
- Superstar Meta Knight
- Advance Meta Knight
- Galacta Knight
- Morpho Knight
- Dedede
- Link
- Samus
- Marx
- Purple
- Bright
- Spicy
- Toad
- Edgey
- Mogeko
- Waddle Dee
- Lololo
- Lalala
- Calie
- Marie
- Pearl
- Marina
- Ultra Beam
- Ultra Fire
- Ultra Mirror
- Ultra Plasma
- Ultra Stone
- Invincible

</details>

## Preview sources

The original and proposed swatches use colors from the reference images in [GitHub issue #1035](https://github.com/hasherwi/Archipelago-kirbyam/issues/1035). The main sheet is credited to Drschnaps; the issue credits the palettes from Daisy through Blue Poppy to SapphireGemNetwork. The available additional colors use the normal gameplay values in the [current color registry](../data/colors.json). No reference sprites are included here.
