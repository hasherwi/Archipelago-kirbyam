# Mustard map: local finite Sir Kibble acquisition

`hub4_kibble_cutter_entry` is a fifth OR witness for `switch_310_mustard_map`,
chest 39 / AP 3960205. It binds original room 310 Sir Kibble `0x088C3FEC` at (176, 88)
to `room:310/template:0x088C3FEC` in the common inventory. The four reviewed
Twister graphs remain byte-for-byte unchanged. The new witness is standard
logic: it uses a static enemy, not an encounter-generated source.

Independent Rainbow Hub 4 access starts the witness at Normal in room 590. Actual door
entry reaches room 534 at frame 1157; Normal flight, air puffs and slides reach room 310 at frame 2515.
The approach reaches Sir Kibble before the map barrier. Native inhale/swallow
acquires Cutter at frame 2753, without damage. Owning Cutter is only permission;
the graph requires a guaranteed raw runtime grant, actual source access and
finite acquisition. Wrong grants, mixed live pools and no-ability outcomes
cannot be turned into guaranteed Cutter by filtering to owned abilities.

Cutter is carried to the dry roof. Three left-facing UP-steered throws clear
the interfering Chip. After an idle timing adjustment, five DOWN-steered roof
returns cycle the switch, positioning live Sword Knight out of the crossing.
The final return contacts the switch and the player crosses with center x>454,
y=136.996 while the gate bounds are[-8,-32,8,-20]. Knight remains alive on the
left. This is a timed full-body crossing, not a permanent switch event. Retained
Cutter breaks the later obstruction and opens chest 39. The unchanged production
client locally reports only LocationChecks 3960205; native map ownership remains
false without randomized item delivery. Nothing is submitted to a server.

The compact acceptance manifest selects 66 fresh successful cold boots: the
28 distinct Chip/Knight health pairs at 1 HP in both gating settings, four 6 HP
100/500% endpoints, four singleton randomized-policy runs, and two full-pool
shuffled runs. The full-pool fixture uses generator RNG seed 51, policy seed
15467416924712283663: Sir Kibble grants Cutter while Twister grants Missile.
All retain starting HP and acquired Cutter; helpers remain in room 101. The sampled
percentages include 224/225 and 424/425 boundaries. This is not every integer
percentage, all seeds, arbitrary arrivals or a complete playthrough.

There is a timing family, not one universally robust replay. The selected
runs record their idle delay explicitly. Middle health settings need different
Knight timing from the low/high endpoints. Earlier failed timings, including
switch activation followed by a Knight collision, remain in the private
packets and are not presented as successes. Separate acquisition, permission,
final-shot, wrong-Beam and no-ability controls all prevent collection. Some
controls take damage; none establishes universal no-route impossibility.

Each accepted run starts with a blank battery and only startup/configuration
ROM fields adjusted. The only runtime writes are the production client's
initial guarded configuration writes at frame 1085, when applicable. There are no
subsequent gameplay writes, equipment injection, state restores or runtime ROM
edits. This does not resume the paused #1059 playthrough. The manifest contains
sanitized scalar results and hashes, not controller replays, ROMs, saves or
private paths. Helper presence in room 101 is not a claim of global helper inactivity.

The existing traversal engine models the source as one finite instance. Tests
reject missing/wrong sources, placement behind its own barrier, equipment loss,
consumed-instance reuse and permission-only access. Loss before first acquisition
still permits the live source; loss afterward does not recreate it. The template reappears later after camera
movement in the native traces. That
observation does not establish a safe reacquisition/retry loop; this graph uses
only the first acquisition and does not admit respawn or repeated random draws. Old witnesses are preserved, and historical catalog comparisons strictly reverse only this added
graph and its target-level OR condition rather than replacing historical hashes.

This resolves the bounded route investigated in #1117. Other source-policy
fallbacks and dynamic-source evidence remain tracked separately in #1118/#1119.
