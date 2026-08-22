# Test 4 negotiation experiment — deployed 2026-08-22 23:19 IST

**Treatment:** Test 4 (`randomized` slot) only. The other four agents are the
control and remain byte-identical to each other.

| knob | control | Test 4 |
|---|---|---|
| GLEE_NEGO_ACCEPT_SPAN | 0.48 | 0.70 |
| GLEE_NEGO_ZOPA_SHARE | 0.39 (default) | 0.20 |
| GLEE_NEGO_MARGIN_WEIGHT | 0.40 | 0.16 |
| GLEE_NEGO_MIN_MARGIN | 0.02 | 0.070 |
| GLEE_NEGO_FINAL_OPTION | 0.60 | 0.68 |

All five are read through `runtime_flags`, so this took effect on the 3s poll.
No restart, nothing stranded.

## Where the numbers came from

`sim/nego_search.py`, two independent 30-config searches with hold-out validation.
They reached similar gains through DIFFERENT values, so the specific numbers are
noise and only the agreed DIRECTIONS were taken. BOULWARE, ULTIMATUM_SHARE and
SPAN_INVARIANT are deliberately untouched — the two searches disagreed on them.

Consensus config on a third game set neither search selected on:
**+0.0102 percentile = +82 rating-equivalent, close rate +0.001.**

## PRE-REGISTERED PREDICTION

Negotiation percentile on Test 4 minus the mean of the other four rises by
**+0.0102** (about +82 rating). Close rate moves less than 1pp. Written down
before the fact so it can be scored rather than rationalised.

## BASELINE, 2026-08-22 23:19 IST

Server ratings:

| agent | barg | nego | pers | games |
|---|---|---|---|---|
| Test 1 | 2228 | 1992 | 2298 | 21,342 |
| Test 2 | 2169 | 1950 | 2215 | 22,959 |
| Test 3 | 2173 | 1987 | 2254 | 18,705 |
| **Test 4** | 2236 | **1730** | 1962 | **2,087** |
| Agent 5 | 2192 | 2018 | 2266 | 19,986 |

Negotiation percentile since 19:41 (play resumed):

| agent | n | pct |
|---|---|---|
| Test 1 | 85 | 0.5392 |
| Test 2 | 92 | 0.4784 |
| Test 3 | 112 | 0.4454 |
| **Test 4** | **245** | **0.5169** |
| Agent 5 | 84 | 0.5100 |

control mean (excl. Test 4): **0.4933**;  Test 4 minus control: **+0.0236**
Test 4 already sits above control before the change, so the morning read must be
a DIFFERENCE IN DIFFERENCES against this +0.0236, not against zero.

## HOW TO READ IT IN THE MORNING

**Do not use Test 4's rating.** It has 2,087 games against ~20,000 on the others
and is still converging up from 1000, so its rating will rise overnight whatever
we do. Attributing that climb to this change would be wrong.

Use PERCENTILE, which is per-game and immune to convergence:

    python scripts/live_percentile.py --hours <hours since 23:19>

Then: (Test 4 pct − mean of other four) now, minus the same quantity at baseline
(+0.0236). That difference is the effect. The prediction is +0.0102.

Known confound to state rather than hide: Test 4 is a new agent with a low
rating, and if matchmaking is rating-sensitive it may face a different opponent
pool than the others. That would bias the comparison in an unknown direction.
The clean version is a WITHIN-agent randomised arm; this between-agent design was
chosen for speed and its result should be treated as a screen, not a verdict.
