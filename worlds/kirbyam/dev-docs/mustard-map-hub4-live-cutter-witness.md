# Mustard Map from the randomized east Hub 4 statue

The seed 1259 controller proof is recorded as sheet Ability Trials row 180.
The map witness SHA-256 is
`6934af1ecabeccbc3052e1f8677ddfec97042a4f365492ba825bd1f4fc8ad876`.
The separate permanent-statue retouch trace SHA-256 is
`c7405f9b6702cca98d7312fcd3645ebdf7c8f05d2ee3dc42023b811df47eee7a`.

On that playthrough, enemy no-ability weight was 100, Completely Random
and world-statue randomization were on, and Area Keys, ability gating and
Room Sanity were off. The reviewed alternative is limited to that option
profile with stock enemy health and 6 HP starting capacity. It also requires the real
statue runtime pool to include Cutter. The branch does not special-case
the seed number, extend the switch timer, or promise a bounded draw.

From independently reached Rainbow Route Hub 4, the east statue in native
590 is `0x088B6908` at (200,48), source key `STATUE:353903`. Select-drop
and recontact the same live statue without a reset: Sword, Parasol, Burning
and Cutter were observed. Its stock output is Tornado. The permanent retouch
lets the logic use its existing explicit eventual-draw assumption for eligible
Cutter, independent of the ordinary enemy no-ability weight. The other n590
statue, a dropped copy star, and finite enemies are not substitute sources.

Carry Cutter through 590 to 534 and through 534 to 310. The witnessed Cutter
return triggers the stock switch, and the dash clears the closing gate. The
no-shot control stays blocked. The original Map chest `0x088C3FA4` opens
and the native event ring changes 0 to 1 at 6 HP. The client identifies local
AP check 3960205; no AP packet was sent. This is not an independent proof of
reaching Hub 4 from start. Keep the guaranteed Twister and Sir Kibble routes,
timings, and out-of-profile fallback unchanged.
