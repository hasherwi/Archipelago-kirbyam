# Title-screen reference assets for #1031

Reference only; this branch does not modify the game or ship a ROM. English North American retail, clean boot, 240×160.

| Preview | Native source |
| --- | --- |
| [Settled retail title screen](title-retail-mgba.png) | mGBA frame 960, no inputs or state edits |
| [BG1 logo, ribbon and legal text](title-bg1-logo-and-ribbon.png) | English background entry 0xCF, descriptor 0x081FC118, 4bpp LZ77 tiles 0x081FA0EC, tilemap 0x081FBC68 and shared BGR555 palette 0x081F9EEC |
| [BG0 logo fade overlay](title-bg0-fade-overlay.png) | English entry 0xCE, descriptor 0x081F9ED0, 4bpp LZ77 tiles 0x081F92E0 and tilemap 0x081F9A20. It blends over BG1 and BG2; the isolated image looks dark by itself. |
| [Press Start sprite row](title-press-start-obj.png) | Actual frame-960 OBJ tiles, OAM and palette. Animation 0x3A9 variants 0–6, stock table 0x08D62720. Visible bounds x=16–223, y=119–134. |

The ribbon is background art, not an OBJ sprite. The requested addition could be a new overlay sprite placed beneath it, without replacing the retail ribbon, fading overlay, scenery or legal text. Avoid overlapping the late Press Start sprites or triggering any change to native menu/attract transitions. If there is insufficient clearance, adjust the prompt placement rather than replacing retail artwork.

Pinned source: https://github.com/jiangzhengwenjz/katam/blob/89a012c0d2e46a0ae87d9133c7a0435d95e348e8/src/title_screen.c
