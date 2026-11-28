# Step 4B: Phone return to Central Circle

The native L action is a one-way return to the **Central Circle floor**
(native 801). It needs neither the AP Phone item nor a battery charge.
It does not summon allies, make a Goal Game reachable, or grant a Hub
Connection or Area Key. Leaving Central Circle still uses the existing
exit requirements, including the random starting mirror.

[Runtime data](../data/phone_return.json) joins the
[retail L-return flag inventory](phone-return-native-rooms.json) to the
[audited room compartments](native-room-wikirby-map.json). The solver
installs this route for 340 physical compartments in 254 native rooms.
The 24 native rooms without the flag are excluded, including the hub,
tutorial, Copy Ability Room and several final-area and minigame rooms.
The eight other flagged rooms with encounter-session slots are also
excluded from this pass: their active/cleared state is not tracked by
ordinary region reachability. This does not assert that L is impossible
after those fights. Menu, area summaries and Room Sanity sinks do not
provide routes.

The edge represents movement after Kirby can settle into an eligible
**Normal** state. It does not assert that L interrupts a cutscene,
attacking, or a blocked live state, or that any equipped ability can be
carried through the teleport. In the
[native controller notes](phone-implementation.md), native 190 returns at
zero charge, a native 108 Normal return works underwater, Mini cannot
return in the tested idle state, and UFO is lost on arrival. Ability
retention and state-specific carry are separate from this movement graph.

Generation and Universal Tracker use the same region constructor. The
return is a separate named edge, not a new native mirror or an entry in
the static room-to-room mirror data sent to the client. A normal seed
already starts in Central Circle. The return becomes observable in a
reachability probe that starts in an eligible compartment with the
original start path disabled; it still cannot open a locked hub exit.
