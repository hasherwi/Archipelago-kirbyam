# Step 4A: Normal-only evidence baseline

[Playthrough #1059](https://github.com/hasherwi/Archipelago-kirbyam/issues/1059)
and its follow-up stock-timing replays classify 336 addressed checks as
positive and 59 as **No** for Normal-only in the reviewed layouts, across
395 current AP locations. The
[versioned baseline](normal-baseline-1059.json) partitions those IDs and
requires separate patch qualifications for Candy 9-12 (linked west fuse)
and Mustard 4-16 (the 600-frame timer). It does not make runtime rules from
workbook statuses. A positive entry on a single native profile is not
an unconditional rule.

The workbook's five goal rows refer to combat feasibility and exemptions,
including one legacy reporting binding. They do not establish AP goal
completion. Current 100% completion remains independently constrained by
its item, room, check, and final encounter requirements. Addressless region
events keep their exact prerequisite actions and ownership.

Run the comparison from the repository checkout:

```sh
AP_TEST_WORLDS=kirbyam python -m worlds.kirbyam.tools.audit_normal_baseline
```

The probe supplies progression items except copy unlocks, Phone, and Copy
Ability Room access. It is **not** a held-Normal simulation, a fresh seed's
progression order, or in-game proof. In particular, ungated native ability
sources (such as Beam) and post-clear Master can still satisfy a legitimate
rule when no AP copy item was collected.

## First reconciliation (seed 1197 probe)

- Four proven Moonlight checks still disagree in both Off and Completely
  Random probes: the 2-05, 2-06, and Goal Room 1 visits, plus Goal Game 1.
  The workbook route uses a precise climb from the post-lever side of 2-11,
  the lower-right arrival in 2-01 and its high east mirror, then the isolated
  lower-west of 2-03. Reconcile those directed sides rather than opening
  the entire room or granting its other mirrors.
- Mustard 4-16 matches its patched timer profile; don't infer a Normal
  route on the original zero timer.
- Carrot Yellow (3960501) can open through the permissive legacy fallback
  when the reviewed grant-specific route does not install. This is not new
  Normal evidence; a replacement must preserve supported seeds.
- Cabbage Chocolate (3960511) opens in the fixed native profile through
  ungated local Beam. The lower Carrot 5-13 chest (3960606) has ungated Beam
  and post-clear Master routes in this probe. These ability paths do not
  contradict the restricted playthrough's negative results.
- Mustard Map can appear reachable in the Completely Random solver probe.
  This probe is not a held-Normal run and does not override the stock-timing
  baseline classification below.

## Stock-timing Normal follow-up

No copy abilities or helpers were used. All three checks are classified
**No** for the reviewed Normal-only setup; none awarded the target chest
or produced an AP check report. These are baseline decisions, not claims
that every conceivable setup is impossible.

- Mustard Mountain Map (3960205): held the switch 62 frames, then used the
  dry jump and hover; the gate closed before Kirby arrived. The stock
  Chip-shot timing and reversal were also tried.
- Rainbow Route 1-06 Lower (3960567): the dry-shelf slide was about 84
  pixels short on the last frame the gate was open.
- Peppermint Palace Chest #1 (3960587): trying the secondary fuse first
  with a spat Sparky star did not light either fuse or open the roof.

## Moonlight correction

The restricted keyless run (seed 1197, Normal, no Phone or helpers) rode the
2-12 right current into 2-11. AP accepted the 2-11 lever check (3960415) at
frame 368968. Kirby slid into the right-side fuse, used the upper mirror
(743 tile 10,2; retail record 0x885CB6), entered 708 at x472/y456.996
(frame 369347), and climbed the right shaft without breaking its metal.
The high east mirror (tile 43,2; record 0x883C72) reached lower 706 at
frame 370857. The directed suffix uses 706 tile 25,18 to 702, 702 tile
43,17 to 744, and 744 tile 3,58 to Goal Room 1. AP acknowledged all three
room visit IDs. Native Goal Game entry and play were observed; the Goal
Game server receipt was not.

The two new same-room edges join the post-lever side to the existing right
door only with the lever-wall item, and join the bottom-right arrival in
708 to its high east exit by flight. They do not grant either reverse edge,
the canonical left side, or passage through the metal divider. All eligible
positive IDs are reachable in the four audit profiles after this correction.
