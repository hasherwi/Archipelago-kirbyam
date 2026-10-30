# Carrot Castle lever placement (#972)

The physical Carrot lever belongs to room 5-05, not room 5-12. Move its AP
location and activation event together, and display 5-05 in the lever and wall
item names. Keep the legacy internal keys ending in `5_12`, item ID 3860039,
location ID 3960417 and transport bit 2. Existing seeds retain their generated
placement and labels; generate a new seed to use this correction.

## Source evidence

The bounded metadata fixture `test/data/carrot-lever-native.json` is extracted
from `test/data/native-room-topology.json` in preserved progression commit
`abf60952fdf79d15bb07607c4977bce7d68f1be7`. It records USA ROM SHA1
`274b102b6d940f46861a92b4e65f89a51815c12c`: native room 170 uses object/door
list 252 and maps to `REGION_CARROT_CASTLE/ROOM_5_05`. The lever object at
ROM offset `0x008D2E68` has type `0x81`, reward `0x63` and chest/save flag 77.
Only decoded metadata is included, not ROM bytes.

The [existing runtime evidence](lever-runtime-regressions.md) independently
records native room 170, source pointer `0x088D2E68`, flag 77 and AP bit 2 in
the historical pre-lever state. Its filename uses older room numbering.
The native payload already recognizes that exact object source; this correction
needs no payload, patch, receipt or wall-ownership changes.

## Regression and acceptance scope

Tests require stable numeric identity, unique ownership by room 5-05, and an
actual generated check and locked activation event in that room. Room 5-12
must contain neither lever check nor event. Existing lever/rules and strict
slot-data snapshot tests cover the corrected labels. The refresh onto main `785a97317db8e28e51b03a656ca4518f226a25f8` preserves
all #914 room exits, requirements and logical exit overrides, including the
`cc_lever` gate from 5-05 to 5-06. A generated-world regression verifies that
physical activation alone does not unlock that gate; receiving the AP wall
item does. Both explicit room location ownership and the activation event move
together. Stable IDs, native bits and the committed ROM patch are unchanged.

This is static evidence and AP generation coverage. Emulator playthrough,
wall opening and save/load acceptance for a newly generated seed remain manual
checks. No new emulator acceptance is claimed.
