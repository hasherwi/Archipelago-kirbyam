# Kirby color palettes

See the colors you can use now and the palettes under consideration for a future release. Each entry shows the same normal Kirby sprite alongside its swatches. These are previews, not gameplay screenshots; abilities and effects can change how some colors appear in-game.

## Available now

Pick any of these **27 colors** with `starting_kirby_color` in your Kirby YAML. For example:

```yaml
Kirby & The Amazing Mirror:
  starting_kirby_color: cotton_candy
```

**Pink** is the in-game default. Use `random` to pick a color when the seed is generated, or `random_color_per_room` to change color between rooms with the connected BizHawk client. These are modes, not separate palettes.

### Original colors

![Kirby sprites and swatches for the 14 original palettes, from Pink to Chalk. The YAML keys are listed below.](color-palettes-native.png)

### Additional starting colors

![Kirby sprites and swatches for the 13 additional selectable palettes, from Shadow to Mint Chip. The YAML keys are listed below.](color-palettes-curated.png)

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

These **41 reference palettes** are not in the game and cannot be selected in YAML. The sprite mockups show how the reference swatches look on normal Kirby; they have not been implemented or checked in gameplay. Names and colors may change.

![Kirby mockups and swatches for the first 21 proposals, Rose through Samus. The names are listed below.](color-palettes-proposals-1.png)

![Kirby mockups and swatches for the remaining 20 proposals, Marx through Ultra Stone. The names are listed below.](color-palettes-proposals-2.png)

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
- Ultra Ninja
- Ultra Plasma
- Ultra Stone

</details>

## Preview sources

The original sprite previews and the swatches used for the proposed sprites come from the reference images in [GitHub issue #1035](https://github.com/hasherwi/Archipelago-kirbyam/issues/1035). The main sheet is credited to Drschnaps; the issue credits the palettes from Daisy through Blue Poppy to SapphireGemNetwork. The additional available colors apply the exact normal-gameplay RGB555 values from the [current color registry](../data/colors.json) to that same sprite’s indexed pixels. The proposal mockups use only the reference colors for the visible slots of that pose; they do not specify colors for other forms or effects. Kirby sprite artwork © Nintendo / HAL Laboratory.
