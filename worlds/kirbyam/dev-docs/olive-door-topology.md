# Olive Ocean 6-04 / 6-05 directed door crosswalk

Match the US retail [tile-door inventory](native-tile-door-inventory.json)
to the extracted [6-05 room image](https://wikirby.com/wiki/File:KaTAM_6-5_Map.png).
The image spans the full native room (736 × 336 pixels); coordinates below are
zero-based 16-pixel tiles. The two arrivals in native 133 occupy separate
corridors. The upper corridor runs over the left slope into the enclosed
mirror chamber. The lower corridor enters below that barrier and follows
the tunnel to the right-side passages and surface exit. Both outgoing
mirrors also match inspected positions in the native object inventory.

| Directed transition | Native rooms | Trigger tile | Arrival tile | Landing/exit identification |
| --- | --- | --- | --- | --- |
| 6-04 → 6-05 Subroom | 132 → 133 | (73,6) | (2,6) | Upper corridor; reaches the enclosed mirror |
| 6-04 → 6-05 main approach | 132 → 133 | (73,18) | (3,18) | Lower tunnel; leads toward the surface exit |
| 6-05 Subroom → 6-07 | 133 → 827 | (14,14) | (3,4) | Enclosed chamber; mirror template 0x088CBA20 at (232,232) pixels |
| 6-05 main approach → 6-06 | 133 → 134 | (43,2) | (2,7) | Far-right surface exit; mirror template 0x088CBAF8 at (696,40) pixels |

The main approach AP key is `ROOM_6_05__LOGIC__ENTRY_FROM_6_04_OR_6_06`.
Its name is a legacy solver label, not proof that 6-06 has a reciprocal
door. The pins apply only to the exact four directed edges in the table.
Static topology does not prove all traversal states or validate the
current ability requirement on access to either trigger.

## Unmatched directions to investigate next

There is no 133 → 132 or 134 → 133 retail tile record. Do not infer either
return from the verified forward doors. The existing 133 ↔ 800 (6-23)
edges also have no matching tile record. The object at (184,24) in 133 is
a consumable (table-1 type 0x63), not an Area Door (0x99).

6-07 → 6-05 uses a distinct fuse-cannon template. The native object inventory
places a table-1 type 0x8A cannon at (656,272) and a type 0x78 fuse at
(568,88) in 827. The [native cannon callback](https://github.com/jiangzhengwenjz/katam/blob/89a012c0d2e46a0ae87d9133c7a0435d95e348e8/src/kirby_cannon.c#L157-L184)
launches Kirby, rather than serving as a freely reversible mirror. Its
[initialization](https://github.com/jiangzhengwenjz/katam/blob/89a012c0d2e46a0ae87d9133c7a0435d95e348e8/src/kirby_cannon.c#L45-L59)
reads the room halfword at template +0x12 and the high byte of the +0x18
halfword for horizontal spawn; the launch passes a nonzero flag from the
+0x18 halfword as the vertical spawn argument.
[The receiver](https://github.com/jiangzhengwenjz/katam/blob/89a012c0d2e46a0ae87d9133c7a0435d95e348e8/src/kirby.c#L11242-L11265)
stores those values in the destination state. The
[retail room description](https://wikirby.com/wiki/Olive_Ocean_-_Room_7)
agrees with the pinned retail decode: template 0x088CD65C targets room 133
with configured spawn arguments (27,1). The
[ordinary loader](https://github.com/jiangzhengwenjz/katam/blob/89a012c0d2e46a0ae87d9133c7a0435d95e348e8/src/kirby.c#L12855-L12915)
maps those to (424, 8.996) pixels, above the surface path to 6-06.
These are initial coordinates for that loader branch, not zero-based
room tile coordinates or a live final landing. Rainbow's witnessed 126 →
570 cannon independently matches decoded arguments (6,1). Verify the
actual Olive landing, fuse/occupancy requirements and retained ability
before trusting this legacy entrance for physical carry.
The solver graph and all its current requirements are unchanged by this audit.
