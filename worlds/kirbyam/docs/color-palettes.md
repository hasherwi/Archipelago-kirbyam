# Kirby color palettes

Browse **65 starting colors**: 14 from the original game and 51 custom KirbyAM colors. Each preview shows the same normal Kirby pose alongside its swatches, so you can compare colors directly. Copy abilities and effects can look different in-game.

## Choose your color

Set `starting_kirby_color` in your Kirby YAML. Use the exact value in the generated YAML for your build. For example:

```yaml
Kirby & The Amazing Mirror:
  starting_kirby_color: cotton_candy
```

**Pink** is the in-game default. Use `random` to pick a color when the seed is generated, or `random_color_per_room` to change color between rooms while connected through the KirbyAM client for BizHawk or mGBA. Without a connected client, the patched ROM applies only the initial color. These are modes, not separate palettes.

## Original colors

![Kirby sprites and swatches for the 14 original palettes, with Pink first, then Carbon through Yellow. The YAML keys are listed below.](color-palettes-native.png)

<details>
<summary>Original color names and YAML values</summary>

| Color | YAML value |
| --- | --- |
| Pink | `pink` |
| Carbon | `carbon` |
| Chalk | `chalk` |
| Cherry | `cherry` |
| Chocolate | `chocolate` |
| Emerald | `emerald` |
| Grape | `grape` |
| Green | `green` |
| Ocean | `ocean` |
| Orange | `orange` |
| Red | `red` |
| Sapphire | `sapphire` |
| Snow | `snow` |
| Yellow | `yellow` |

</details>

## Custom Palettes

![Kirby sprite previews and swatches for 18 custom palettes, Advance Ice through Lemon.](color-palettes-custom-1.png)

![Kirby sprite previews and swatches for 18 custom palettes, Link through Royal.](color-palettes-custom-2.png)

![Kirby sprite previews and swatches for 15 custom palettes, Shadow through White.](color-palettes-custom-3.png)

<details>
<summary>All 51 custom color names</summary>

- Advance Ice
- Advance Stone
- Beautiful Sunset
- Bright
- Calie
- Candy Corn
- Carrot Cake
- Citrus
- Cotton Candy
- Daisy
- Dedede
- Edgey
- Galacta Knight
- Ivory
- KDL3 Pink
- Lalala
- Lavender
- Lemon
- Link
- Lololo
- Marie
- Marina
- Marx
- Meconopsis / Blue Poppy
- Mint Chip
- Mogeko
- Morpho Knight
- Negative
- Pearl
- Pineapple
- Pumpkin
- Purple
- Rainbow
- Ramia’s Scale & Star Stone
- Rose
- Royal
- Shadow
- Snow Cone
- Spicy
- Strawberry Peach
- Superstar Ice
- Superstar Meta Knight
- Toad
- Ultra Beam
- Ultra Fire
- Ultra Mirror
- Ultra Ninja
- Ultra Plasma
- Ultra Stone
- Waddle Dee
- White

</details>

## Preview sources

The original sprite previews and the swatches for the reference-sheet palettes come from the reference images in [GitHub issue #1035](https://github.com/hasherwi/Archipelago-kirbyam/issues/1035). The main sheet is credited to Drschnaps; the issue credits the palettes from Daisy through Blue Poppy to SapphireGemNetwork. For some custom colors, previews apply normal-gameplay RGB555 values from the [color registry](../data/colors.json) to that same sprite’s indexed pixels. Previews based on the reference sheets illustrate the normal pose only; they do not show other forms or effects. Kirby sprite artwork © Nintendo / HAL Laboratory.
