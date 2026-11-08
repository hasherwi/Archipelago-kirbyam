# Shuffled enemy state overwrites (#1049)

Shuffled generation patches each included source's native ability table byte.
`InitObject` copies that byte to the live object's `kirbyAbility`, but enemy AI
can subsequently replace it. Native Waddle Doo `sub_080B6AD8` writes Beam;
`sub_080B73D8` and `sub_080B7460` write Parasol. Waddle Dee also has Normal and
Parasol resets. Changing only object initialization would miss later resets.

The request hook now restores the assigned table byte immediately before an
ordinary enemy's ability request. It does not change the live object's ability
field, which native AI also uses for behavior. Resolution requires all of:

- Shuffled mode (1).
- Verified ordinary swallow callsite `0x0809C6AA` and a readable, aligned EWRAM
  or IWRAM source object.
- Version-one source config magic and an enabled bit for the source type.

The table pointer is the GBA ROM address `0x0835164E`, not file offset
`0x35164E`; entries have a 24-byte stride. The result replaces only the low
five ability bits. The normal ownership gate then acts on that restored ID,
including conversion of a locked result to Normal. A table assignment of
Normal is a real assignment and must also override native Beam/Parasol.

Off/completely-random modes, excluded sources, Minny, unknown callers, ability
stars (including Mini recovery), and statues keep their existing behavior.
Legacy patches with no source bitmap are not remapped: inferring their source
eligibility from current defaults would silently change their options. Generate
a new patch to receive the fix. No seed/data format or fixed config address is
changed. Two existing RNG helpers are placed in the existing ROM extension to
keep the fixed payload window within its linker assertions.

## Evidence and tests

Native source revision: `1197474f80e5de282fbedcd0025ebfa61f61a764` in
[jiangzhengwenjz/katam](https://github.com/jiangzhengwenjz/katam).
See `src/waddle_doo.c` lines 43–100, 357–392 and `src/object.c` lines 1244–1250,
2042–2051. The ordinary swallow calls the transition even for ability zero.

- `test/native/shuffled_enemy_host.c` exercises production resolution across
  all 256 source indices, 32 ability IDs, upper flags, mode/legacy boundaries,
  disabled sources, invalid pointers, and repeated native-reset inputs.
- `test_minny_runtime.py` executes the actual extracted request hook with a
  source object and ROM table mapped at GBA addresses. It checks native Beam
  and Parasol inputs, a locked/unlocked Sword assignment, Normal assignment,
  exclusions and unchanged RNG state.
- Existing Mini recovery, Minny, source policy and randomization tests cover
  protected paths. These host tests are not an emulator playthrough.

## Gameplay regression checklist

Use a newly generated Shuffled seed whose spoiler assigns WADDLE_DOO something
other than Beam, with that ability unlocked. Record build/seed/options.

1. Swallow the first Waddle Doo in room 1-01. Compare the result to the spoiler.
2. Repeat after attack/landing state changes and for stationary/parasol variants.
3. Repeat while the assigned ability is locked, then after receiving it.
4. Check a Normal assignment and, with passive enemies enabled, Waddle Dee.
5. Check excluded sources, vanilla and completely-random controls, recovery
   stars and statues. Avoid treating controlled host fixtures as game evidence.

## Native room 1-01 result

A controlled native-emulator replay now reproduces the report and verifies the
fix: the first Waddle Doo grants Beam (7) on baseline main and Sword (18) on the
rebuilt candidate, with the same Sword table assignment and controller inputs.
Both runs finish in native room 101 at full health. Initial room/position and
seed data are explicit test fixtures; gameplay uses controller inputs and the
production client's runtime-config writes, with no direct gameplay RAM edits.
This is not a complete generated-seed playthrough.

See [the sanitized evidence record](shuffled-enemy-native-evidence.json) for
patch/ROM hashes, fixture setup, inputs, config writes and resulting snapshots.
Full ROMs and private save files are not included.
