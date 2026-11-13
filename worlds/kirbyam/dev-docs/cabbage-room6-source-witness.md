# Cabbage Room6: original-source Hub2 witness

Fresh-boot continuous replay, reviewed 2026-11-09: **native591→517, original
Waddle Doo→Beam, Chocolate gate opening, chest57 and spray11 collected**. No
essence substitution, runtime writes, state restores or reward manipulation.

The startup-only fixture begins in native591, the existing Cabbage Hub2 AP
region. Controller input performs the actual door transition into517 at frame1158,
arriving (696,296.99609375), matching decoded spawn tiles(44,19). Normal Kirby
approaches from the right and inhales native Waddle Doo template0x008CA04C at
(528,264) above the sealed ordinary chain, then swallows it. Beam is acquired at
frame2007. This is a finite source instance, not a respawn/retry assumption.

The route carries Beam through the lower corridor, avoids the central fire lane
with ground movement, then climbs the left passage to the tested gate pose
(185.99609375,120.99609375), still6HP at frame3085. Beam opens the intended F1 and
all seven F2 cells by frame3148. The player returns through the lower passage,
flies into the opened chamber and collects the chest. Native chest57 and spray11
are true at frame4325, with Beam still held. A separate fresh replay samples HP
every frame from actual arrival1158 through collection4325 and confirms minimum
6HP throughout. This no-damage variant supersedes the exploratory route that
took a collision after opening the gate; no minimum-health requirement is inferred.

[Compact acceptance manifest](cabbage-room6-source-acceptance.json) contains
startup-only differences, identity/replay hashes, source/arrival records,
checkpoints and receipt assertions. Full inputs, validation script and private
screenshots remain local. This is native physical acceptance, not an AP-delivery
or global-game-reachability test.

## Installed scope

Bind only `MINOR_CHEST_SPRAY_PAINT_12` when the actual source policy guarantees
WADDLE_DOO→Beam. Require independent access to
`REGION_CABBAGE_CAVERN/ROOM_3_HUB_2`, and model its actual transition, Normal
acquisition and complete Beam carry. Merely reaching Room6 or owning an ability
item cannot establish this source path. Disabled optional chest categories do
not receive the rule. RoomSanity and exits to Room7/Hub2 are unchanged.

Beam is not gateable in the existing ROM, so it remains useful and no Beam item
permission is invented. The target's other physical providers (Spark, Ice, Smash)
do not inherit this Beam-specific carry proof. Unsupported source policies retain
prior behavior and remain unresolved rather than being labelled impossible.
