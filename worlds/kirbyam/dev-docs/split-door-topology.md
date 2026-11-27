# Split-room native door crosswalk

These matches combine the SHA-1-pinned retail tile records with named
compartments. They identify ports, not every ability or approach allowed
by generation.

## Rainbow and Moonlight

- Rainbow 1-02 (106) has two right-edge doors. The upper trigger (76,3)
  lands at (4,4) in 1-03 upper, whose exit heads to 1-04. The lower
  trigger (76,7) lands at (4,9) in 1-03 lower, whose exit heads to 1-06.
  The [room layout](https://wikirby.com/wiki/Rainbow_Route_-_Room_3)
  distinguishes the two one-way corridors. Neither port creates a return.
- Moonlight 2-20 (149) enters Goal Room 2 (148) through either the ordinary
  mirror (2,18) to (59,13), or the bottom current at x=0–1 and y=26–29 to
  (60,19). Keep all eight current cells, not just one representative tile.
  The [room layout](https://wikirby.com/wiki/Moonlight_Mansion_-_Goal_2)
  places the bottom arrival in a different pocket. Neither of these
  records is the upper-left arrival from 2-18, and arriving in this room
  doesn't itself prove the Goal Game check.

## Mustard cannon and Batafire

- From 4-12, the [ordinary controller witness](phone-mustard12-lower-evidence.json)
  enters native 323 at (472,616.996) pixels. This agrees with configured
  arguments (30,39) from trigger (6,15). The other door (1,8) lands at
  (13,36), the left corridor to the fuse and its cannon. The
  [room layout](https://wikirby.com/wiki/Mustard_Mountain_-_Room_13)
  distinguishes it from the ordinary route through Batafire. This
  identification does not impose the Phone on either route.
- Native room 300 is split left/right. Its two boss doors at (3,2) and
  (12,2) match the left and right corridors and preserve two distinct
  spawns in the boss room. The
  [room layout](https://wikirby.com/wiki/Mustard_Mountain_-_Room_14)
  independently describes the two sides and distinct doors.
- The previous room's cannon route is not the ordinary 323→300 mirror
  just because the native IDs match. The production CANNON_LEFT graph
  identifies the cannon as a separate, fuse-gated approach; this audit
  does not use the ordinary mirror as evidence for carrying an ability
  along the cannon route.

## Candy Constellation Room 13

Two 9-12 (402) doors reached a single AP region for native 419, so either
arrival could appear to grant the other route. The
[room layout](https://wikirby.com/wiki/Candy_Constellation_-_Room_13)
separates the upper corridor to Warp from the lower corridor to Chest 3.
The native upper trigger (40,3) arrives at (3,4), with the Warp door
at (73,2). The lower trigger (40,28) arrives at (3,15), with the Chest 3
door at (73,15). The solver now has one AP region per corridor with no
link between them. Both can award the same Room Sanity bit via a
terminal shared check; neither gains the other's exit. The separate
9-12 chest rule is unchanged. No new native transition is installed.
