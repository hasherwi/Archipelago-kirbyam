# Mustard map: finite Twister-to-Cupid alternative

`hub4_cupid_entry` is a third OR graph on `switch_310_mustard_map`, the physical
Mustard map chest39 / AP location3960205. The UFO and Crash graphs are unchanged.
It requires independent Rainbow Hub4 access, a Normal590 start, the actual finite
original534 Twister (template0x088B59B4 at144,280), a raw guaranteed Cupid outcome,
and Cupid ownership when gating is enabled. Permission never supplies equipment.
The precise dry310 capability is not general Cupid range, triple/max-charge,
wall piercing, another switch/check, or a persistent open event.

## Acquisition, carry and timed crossing

Normal production full-pool seed63, policy seed7582041893722069666, assigns Cupid19
to Twister (table0x3518EE, source bit28). After actual590-to-534 door entry, native
inhale/swallow acquires Cupid at1320. Cupid flight, a slide and a neutral arrow
clear the534 obstructions. Lower flight avoids Bronto, and the actual upper-right
door reaches310 at2368 without damage or equipment loss. Startup-only fixture
records set player590(248,104) and helpers101(48,80); this is not a whole-game
playthrough from the ordinary spawn.

In310 the route flies over initial enemies, drops under the hanging wall and
rises before crossing Chip's platform. The first UP/left weak arrow is intercepted
by Chip at2848, doing3 damage. At100% Chip2→−1; at500% Chip10→7 is knocked away,
not killed. This first arrow is not mislabeled as switch contact.

The second UP/left q0 release occurs2896 at Kirby's after-update pose
(425.99609375,85.16796875). Creation uses pre-movement Y85.10546875. The first
linked arrow update is(417.5234375,82.40625), vx−633/vy691. After73 movements,
mutual live collision pointers link the same player-parent arrow at
(301.0859375,134.4375), vx−201/vy−1037, to switch0x088C3F14 at2968. The arrow
embeds2969, but slot1 is high only2969–2980 and low2981. Visual arrow retention
never grants a continuously held switch. Gate opening starts2970.

Kirby hovers until3000 to avoid Knight's initial attack, then down/right32 and
right16 cross during gate closing: x455.296875/y136.99609375 at3045, x459.1875
at3048. Actual gate bounds and physical crossing were traced. After crossing,
eight weak arrows precede further movement. At100% two hits defeat Knight4HP;
at163–174% a third is needed. At500% Knight20HP dashes left while Kirby hovers and
remains behind the reclosed gate; no500% kill is claimed. The fixed sequence also
handles changed bomb-obstruction timing and opens chest39 at3452, ending3549
with Cupid retained and no damage. The graph keeps this enemy-aware sequence
atomic and requires carried Cupid for the final continuation.

## Coverage, controls and limits

The accepted eight-arrow input hash is
`0c68359e85cde0ac8a515dd3b5cbd72cec3f68fc4504ef1d78a6d1a2b22b596f`.
There are34 fresh positives and13 fresh negative controls:

- Four endpoint positives: HP1/6 × enemy100/500%, all damage-free.
- Four matched full endpoint omissions remove only B from the second launch
  at2881. They never trigger, cross or collect, but later take damage or respawn.
- Four matched clean prefix omissions stop3000, after positive contact2968 and
  opening2970. They retain HP and Cupid, with no switch/gate/check effect.
- Five fresh1HP positive/full-omission pairs at50,162,163,174,175% cover minimum
  scaling and the actual lethal-hit thresholds. Full controls retain the damage
  qualification.
- One normally generated positive per each of28 distinct Chip/Knight HP pairs
  over50–500%. Shared50/163/175 representatives are the same fresh threshold
  cases, not duplicated or relabeled runs. There are32 distinct sampled health
  percentages, not exhaustive coverage of every integer or other enemy/RNG state.

The older two-arrow sequence actually fails at163%: Knight7HP retains1 after
six damage, and Kirby is hit at3126. Its raw evidence is retained separately.
The accepted record repairs that failure with eight post-gate arrows. Endpoint
interpolation, arbitrary arrival timing and all-seed invariance are not claimed.
Helpers stay in101 and have attacks there; they are not described as inert.
No helper-parent attack occurs in310 in the accepted traces.

## Gating and collection boundaries

The full-route matrix is ungated. A separate normally generated100%/1HP gated
acquisition pair receives either Cupid permission item3860119 or no items.
The eight startup configuration writes differ only at unlock mask0x0203B0B4:
524288 versus0. The gate mask includes Cupid in both. Actual ingestion yields
Cupid at1320 with permission and Normal through1335 without it, with unchanged
HP. This is source-acquisition evidence only, not a completed gated chest route
or proof that other routes are impossible. Initial AP inventory is not an
injected equipped-ability grant.

Exactly eight production client configuration writes occur at1085; no later
harness RAM/ROM writes or state restores occur. Physical chest39 and transport
0x0203B028 bit4 are true in positives. The unchanged production client's read-only
poll locally captures LocationChecks([3960205]), with no server transmission.
Native map ownership remains false: check collection is not randomized delivery.

Cupid is already gateable and unconditionally PROGRESSION in the item catalog.
This change adds no classification promotion or late starting-inventory repair.
Tests retain existing pre-region collection/multiplicity, fresh-state ownership,
removal and normal full-generation fill/accessibility behavior. Area-key ingress,
statues, RoomSanity, start-with-all-maps and unrelated entrances remain unchanged.

## Evidence identity

`mustard-map-cupid-acceptance.json` contains sanitized scalar outcomes, exact
private hashes and the separate gating pair. Raw ROMs, saves, traces and local
paths stay private and immutable. Original native source is7d969fbc; fixtures
were produced from frozen6e189f5. The integration base is2fc41e3. No earlier
UFO/Crash packet or held payload is changed. Private hashes are exact bytes;
tracked client-source comparison normalizes UTF-8 line endings to LF for Windows
checkouts without normalizing any private artifact.
