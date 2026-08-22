# Why we are last in negotiation — 2026-08-22

Live leaderboard: our account is 4th, placed by Test 1 at 2204.5. Per family
Test 1 is 3rd of 10 in bargaining and 4th in persuasion, and **10th of 10 in
negotiation** at 1994.5. The gap to #1 is +597.7 negotiation, +201.8 persuasion,
and we BEAT them by 69.3 in bargaining. Negotiation is the whole deficit.

## What the top negotiators actually do

Share of the ZOPA the proposer claims for itself, complete-information games,
by round block, from our own logs of games we played against them:

| who | r1-3 | r4-6 | r7-9 | r10+ |
|---|---|---|---|---|
| **US** | 0.681 | 0.810 | 0.720 | **0.581** |
| **opus 5\*** (nego 2550) | **0.970** | **0.970** | 0.933 | **0.935** |
| gamma (2118) | 0.912 | 0.920 | 0.912 | -- |
| Zeus (2018) | 0.947 | 0.888 | 0.625 | **0.504** |

The 2550-rated agent claims 97% of the zone and NEVER CONCEDES. gamma holds 91%
flat. Zeus concedes to 0.50 — and Zeus is rated 2018, essentially our 1994.

**The agents that stonewall win. The agents that concede are us and Zeus, at the
bottom of the top ten.**

## What it costs us

| opponent | games | close rate | their ZOPA share | our share | our percentile |
|---|---|---|---|---|---|
| opus 5\* | 49 | 40.8% | **0.757** | 0.166 | **0.3655** |
| gamma | 84 | 60.7% | **0.753** | 0.178 | 0.4629 |
| Zeus | 50 | 52.0% | 0.473 | 0.527 | 0.5283 |

Our average negotiation percentile is 0.4905. Against opus 5 it is 0.3655 — our
worst result against any opponent. Against Zeus, who plays like us, we split the
zone evenly and score 0.5283.

Their close rate is LOWER than ours and it does not matter: they take 4.5x more
per close, and the deals they forgo were heading to the $0 atom anyway. With 45%
of the grid structurally infeasible, most games pay zero regardless — which makes
holding out nearly free and paying hugely when the opponent caves.

## Why our own local search pointed the wrong way

`sim/nego_search.py` found "concede faster" worth +0.0026 and a consensus config
worth +82 rating. That search is not wrong, it is LOCAL: the clone's acceptance
curve is fitted from our own historical behaviour, and we have only ever played
the conceding regime. So the search found the best point INSIDE that regime and
structurally cannot see that a different regime dominates.

This is the coverage limit again, in a form worse than the one already recorded
in sim/clone_fidelity.py: it does not only hide unexplored PRICES, it hides
unexplored STRATEGIES. No amount of local search on our logs can find a policy we
have never played, and the honest reading is that tonight's +82 is an improvement
within the losing regime.

## What has NOT been established

* n is thin: 49 games against the opus family, 12 against opus 5(4) itself.
  Enough to characterise their BEHAVIOUR (49 games is ~540 observed offers) but
  NOT to estimate what stonewalling would earn US -- that needs ~130 games/arm.
* Their edge is measured in games against US. We cannot see how they fare against
  the rest of the field, so "stonewalling wins" is inferred from their rating plus
  their behaviour, not directly observed across their whole schedule.
* If we stonewall and the opponent also stonewalls, both take zero. Whether that
  is cheap depends on the feasible-game mix and is UNMEASURED for a policy we
  have never run.

The next step is a live randomised arm that holds a high share and does not
concede, measured against the current policy. That is a regime change, not a
parameter tweak, and it must not go on the agent that carries our rank.


---

## CORRECTION, same night: it is the LEVEL, not the stonewalling

The section above generalised from opus 5 alone. With the negotiation-only
leaderboard we could check every ranked opponent we have played. Seven of them,
157 complete-information games, share of the ZOPA the proposer claims:

| opponent | nego rating | opens | ends | our pct vs them |
|---|---|---|---|---|
| opus 5(4) | 2555.8 | 0.970 | 0.884 | 0.3641 |
| Clod | 2355.4 | 0.958 | 0.816 | 0.4140 |
| MACH2 | 2278.3 | 1.050 | 0.816 | 0.4696 |
| Fortuna | 2258.1 | 0.970 | 0.929 | 0.3691 |
| NegoMind-B | 2195.4 | 0.925 | 0.925 | 0.3994 |
| velocity | 2148.8 | 0.701 | 0.777 | 0.3840 |
| Neo | 2135.4 | 0.774 | 0.674 | 0.5010 |
| **US** | **1994.5** | **0.681** | **0.581** | |

**Correlation between negotiation rating and opening claim: +0.60.**

Everyone above 2195 opens at 0.92-1.05. We open at 0.681, lowest in the group.
MACH2 opens at 1.050 -- above the whole zone -- and is rated 2278.

The sharpest way to say it: **their FINAL position (0.82-0.93) is above our
OPENING position (0.68).**

CONCESSION AMOUNT DOES NOT TRACK RATING. It ranges 0.000 (NegoMind-B) to 0.234
(MACH2) among agents rated 2195-2278. So "never concede", inferred above from
opus 5 alone, was the wrong lesson from a sample of one. What tracks rating is
the LEVEL: where you open and what floor you concede to.

Field context, 1,612 complete-info games: the median opponent opens at 0.900 and
walks to 0.657, and 58% concede more than 5 points. We concede into a field that
opens high and settles near 0.65-0.80.

## Why waiting for gill bates / Mythos01 data is not a plan

In negotiation we hold 1 game against gill bates and 2 against Mythos01, and none
of them has a final game_state. Over a 3.3-day log window that is 0.30 gill bates
negotiation games per day: about 2 more before the competition closes on Aug 29.
The data will not arrive. opus 5(4) at 2555.8 is 45 points off the top and we have
real data on it, so that is the window we use.

---

## The other two families, same method (2026-08-23)

### Bargaining — we are #3 (2306.6), 145 behind #1. NO lever found.

Share of the pot the opponent demands, from our games against ranked agents:

| opponent | barg | opens | ends | our pct vs them |
|---|---|---|---|---|
| opus 5(4) | 2451.6 | 0.731 | 0.790 (hardens) | **0.6172** |
| jeff zeboss | 2302.8 | 0.658 | 0.635 | 0.4615 |
| Priori | 2292.3 | 0.570 | 0.587 | 0.4812 |
| Morphling | 2235.4 | 0.617 | 0.535 | 0.4801 |
| P-agent | 2219.9 | 0.609 | 0.554 | 0.4827 |
| the field | -- | 0.608 | 0.573 | 0.4986 |

Opening demand does NOT track rating here (the #1 opens 0.731, the #5 opens
0.570), and we score our BEST result of any matchup against the top bargainer.
Nothing to copy.

### Persuasion — we are #4 (2293.1), 216 behind #1. Our difference is an EDGE.

Lie rate on low-quality units, measured from 8,369 games where we were the BUYER
so the true quality is visible:

    median seller across 70 opponents   96.0%
    Zeus (persuasion 2400.7, #2)        91.7%
    Mythos01 (2308.2, #3)              100.0%
    US                                  59.9%

Only 4 of 70 sellers lie less than we do. That looked like a deficiency until it
was split by whether lying is punished:

| cell | our lie rate | field | our percentile | rating-equiv |
|---|---|---|---|---|
| p*r < 1 (lying punished) | **17.6%** | ~96% | **0.6485** [.6354,.6615] | **3188** |
| p*r >= 1 (lying free) | 96.2% | ~96% | 0.5097 [.4986,.5208] | 2078 |

**Our restraint in the costly cells is the single biggest edge we have in any
family.** We score the 65th percentile there precisely BECAUSE we do not do what
the other 66 sellers do. Copying the field would have destroyed it. This is also
consistent with our own randomised evidence (Agent 5's never-lie beat Test 1's
shading by +0.0457, CI [+0.0030,+0.0883], in exactly those cells) and with the
theory: when p*r < 1 a caught lie costs every remaining round.

The persuasion opportunity is therefore in the FREE cells, where we already lie
96.2% and score only 0.5097 -- dead average. Whatever separates gill bates from us
there is NOT lie rate; both are at ceiling. Unexplained and worth a look.

### Priority

| family | rank | gap to #1 | lever |
|---|---|---|---|
| negotiation | last of 15 | -606 | YES: we open 0.681, winners 0.92-1.05, r=+0.60 over 7 agents |
| persuasion | #4 | -216 | partly: free cells average and unexplained |
| bargaining | #3 | -145 | none found |

Negotiation has the largest gap, the clearest mechanism and the strongest
evidence. It is the only one worth a regime change.

---

## RECENCY: the field is moving, and pooled history hides it (2026-08-23)

Prompted by the operator asking whether the logs hold opponents' UPDATED
strategies. They do, and pooling 3.3 days of them was hiding it.

**Negotiation — the field is HARDENING.** Claimed ZOPA share in opponents' offers:

| window | mean claim | n |
|---|---|---|
| older than 24h | 0.776 | 7,222 |
| 24h-6h ago | 0.813 | 2,636 |
| last 6h | **0.830** | 985 |

Individual agents visibly updating: Zeus 0.726 -> 0.856, opus 5(2) 0.908 -> 0.965,
gamma flat at ~0.91. Our 0.681 is now far below the AVERAGE opponent, not just the
leaders, and the gap is widening while we sit still. This strengthens the
GLEE_NEGO_OPEN_CLAIM=0.95 change already on Test 4.

**Persuasion — this INVALIDATES the knife-edge recommendation.** Sellers' lie
rates on low-quality units, same windows:

| cell | >24h ago | 24h-6h | last 6h |
|---|---|---|---|
| knife | 88.8% | 93.5% | **97.0%** |
| free | 86.4% | 93.2% | 95.1% |
| costly | 87.0% | 92.7% | 96.2% |

The inverted-U reported earlier -- 40-80% lying appearing optimal at the knife
edge, versus 38% for near-honest and 55% for near-always -- was POOLED ACROSS
TIME. Those low-lie bands are almost entirely OLD games. The current field lies
97% there. "Moderate lying wins" may be nothing more than "older opponents lied
less", and a flag built on it would have been built on a time artifact.

A second defect in that same table: its "units sold" column comes from games where
WE were the buyer, so it reflects our own buying policy as much as the seller's
skill. It is not a clean read of their strategy in either direction.

**The knife-edge persuasion flag is therefore NOT justified and was not built.**

What survives is our own randomised evidence: our costly-cell lie rate went
20.8% -> 8.1% -> 0.0% across the unification, and Test 3's percentile there went
0.6243 -> 0.7235. Own agents, own change, holding.

**Method note.** This is the third distinct way a comparison fooled us in one day:
realised-q instead of assigned arm (persuasion), clone support instead of policy
space (the local search), and now pooled time instead of current behaviour. All
three produced a confident number pointing the wrong way. Any cross-sectional
comparison against the field must be cut by time window before it is believed.
