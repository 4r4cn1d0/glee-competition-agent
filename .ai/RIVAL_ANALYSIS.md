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
