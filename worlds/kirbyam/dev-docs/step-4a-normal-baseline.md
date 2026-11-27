# Step 4A: Normal-only evidence baseline

[Playthrough #1059](https://github.com/hasherwi/Archipelago-kirbyam/issues/1059)
recorded 336 positive addressed checks, 56 ruled out in the reviewed layouts,
and three **No, Unproven** across 395 current AP locations. The
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
  It, Rainbow 1-06 Lower, and Peppermint Chest #1 stay **No, Unproven** in
  this evidence set; no rules or publication status change based on the
  probe alone.
