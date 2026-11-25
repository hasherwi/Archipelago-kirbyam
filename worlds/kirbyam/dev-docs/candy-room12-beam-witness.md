# Candy Constellation 9-12: Beam to Small Chest #1

This is a bounded same-room route for AP location **3960575**, object
`0x088C5BA4`, native room 402. It does not change the RoomSanity check or
either native exit to 9-13.

- The stock North American ROM and the reproduced keyless 1197 seed have
  identical room-402 collision data (SHA-256
  `43d464d6b6a3c82b90d2087b3b98ddde26692e84214d1defff147868b4df44ae`).
  Scanning all 287 native transition tables finds only the upper 9-10
  entrance, room 418 tile (133,3) to room 402 spawn (4,4).
- The chest is at (392,424) and the linked Bomb fuse at tile (25,25).
  The three linked east seal cells (28,25–27) are initially `0xF2`.
  There is no chain from the separately reachable Bomb fuse and the tested
  Normal puff from the east does not trigger the interior fuse. The
  uninterrupted Normal route can still visit the room and reach its exit.
- In a private controller-only mGBA replay of the keyless seed, Normal
  Kirby took the native lower gallery and inhaled/swallowed the original
  Waddle Doo (`0x088C5BC8`, type 18) from the approach at about (301,457).
  Kirby retained Beam through the central one-way floor. A left-facing
  Beam sweep at (442,376.996) hit the Bomb fuse through the roof. The fuse
  and all three seal cells changed to zero.
- Without leaving the room or resetting the seal, Kirby came around the
  east gallery, passed through the opened east seal and opened the chest.
  The native exact-event counter increased from 0 to 1 and reported
  `0x088C5BA4`; no helper or gameplay writes were used. This was a private
  emulator replay, not an AP server acknowledgment. The recorded route
  survived native damage; it does not prove a damage-free or 1-HP route.
- This Standard witness has zero ability-carry room transitions and
  installs only for assignments that guarantee Beam from Waddle Doo.
  Beam is not an AP permission item. No alternative carrier, live RNG
  retry, or unsupported randomization assignment is asserted; those
  profiles keep the old location rule pending a separate native witness.
